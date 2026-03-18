#!/bin/bash
# =============================================================================
# setup.sh — Instalacion inicial en servidor Ubuntu/Debian
# Ejecutar como root la primera vez:
#   bash setup.sh
# =============================================================================

set -e

DOMAIN="app.patioviejo.click"
APP_DIR="/var/www/app-vp"
REPO="https://github.com/c010r/app.vp.git"
APP_USER="appvp"
PYTHON_VERSION="3.12"

echo "========================================"
echo "  Setup inicial — $DOMAIN"
echo "========================================"

# 1. Actualizar sistema e instalar dependencias del SO
echo ""
echo "[1/9] Instalando dependencias del sistema..."
apt-get update -q
apt-get install -y -q \
    python3 python3-pip python3-venv python3-dev \
    postgresql postgresql-contrib libpq-dev \
    nginx \
    certbot python3-certbot-nginx \
    git curl build-essential

# 2. Crear usuario del sistema
echo ""
echo "[2/9] Creando usuario '$APP_USER'..."
if ! id "$APP_USER" &>/dev/null; then
    useradd --system --create-home --shell /bin/bash "$APP_USER"
    echo "Usuario $APP_USER creado."
else
    echo "Usuario $APP_USER ya existe."
fi

# 3. Configurar PostgreSQL
echo ""
echo "[3/9] Configurando PostgreSQL..."
DB_PASSWORD=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 20)
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='appvp'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE USER appvp WITH PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='appvp_db'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE DATABASE appvp_db OWNER appvp;"
echo "DB creada. Contrasena PostgreSQL: $DB_PASSWORD"
echo "(guardala, la necesitas en el .env)"

# 4. Clonar repositorio
echo ""
echo "[4/9] Clonando repositorio..."
if [ -d "$APP_DIR" ]; then
    echo "El directorio ya existe, haciendo pull..."
    cd "$APP_DIR" && git pull origin main
else
    git clone "$REPO" "$APP_DIR"
fi
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"

# 5. Entorno virtual y dependencias Python
echo ""
echo "[5/9] Configurando entorno virtual Python..."
sudo -u "$APP_USER" python3 -m venv "$APP_DIR/.venv"
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install --upgrade pip -q
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements/prod.txt" -q

# 6. Crear .env de produccion
echo ""
echo "[6/9] Creando archivo .env..."
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")

if [ ! -f "$APP_DIR/.env" ]; then
cat > "$APP_DIR/.env" <<EOF
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN

DB_NAME=appvp_db
DB_USER=appvp
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=5432
EOF
    chown "$APP_USER":"$APP_USER" "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"
    echo ".env creado en $APP_DIR/.env"
else
    echo ".env ya existe, no se sobreescribe."
fi

# 7. Migraciones, static files, superusuario
echo ""
echo "[7/9] Migraciones y archivos estaticos..."
cd "$APP_DIR"
sudo -u "$APP_USER" DJANGO_SETTINGS_MODULE=config.settings.prod \
    "$APP_DIR/.venv/bin/python" manage.py migrate --noinput
sudo -u "$APP_USER" DJANGO_SETTINGS_MODULE=config.settings.prod \
    "$APP_DIR/.venv/bin/python" manage.py collectstatic --noinput

mkdir -p /var/log/app-vp
chown "$APP_USER":"$APP_USER" /var/log/app-vp

# 8. Configurar systemd
echo ""
echo "[8/9] Configurando servicio systemd..."
cp "$APP_DIR/app-vp.service" /etc/systemd/system/app-vp.service
systemctl daemon-reload
systemctl enable app-vp
systemctl restart app-vp
systemctl is-active --quiet app-vp && echo "Servicio OK" || echo "ERROR en el servicio — revisa: journalctl -u app-vp"

# 9. Configurar Nginx + SSL
echo ""
echo "[9/9] Configurando Nginx..."
cp "$APP_DIR/nginx.conf" /etc/nginx/sites-available/app-vp
ln -sf /etc/nginx/sites-available/app-vp /etc/nginx/sites-enabled/app-vp
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo ""
echo "Obteniendo certificado SSL con Certbot..."
certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m admin@patioviejo.click || \
    echo "Certbot fallo. Podes ejecutarlo despues: certbot --nginx -d $DOMAIN"

echo ""
echo "========================================"
echo "  Instalacion completada"
echo "  Sitio: https://$DOMAIN"
echo "========================================"
echo ""
echo "IMPORTANTE — Crear superusuario admin:"
echo "  cd $APP_DIR"
echo "  sudo -u $APP_USER DJANGO_SETTINGS_MODULE=config.settings.prod .venv/bin/python manage.py createsuperuser"
