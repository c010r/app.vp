#!/bin/bash
# =============================================================================
# Script de despliegue — App VP
# Uso: ./deploy.sh [staging|production]
# =============================================================================

set -e  # Salir si cualquier comando falla

ENV=${1:-production}
APP_DIR="/var/www/app-vp"
VENV="$APP_DIR/.venv"
PYTHON="$VENV/bin/python"
PIP="$VENV/bin/pip"
MANAGE="$PYTHON $APP_DIR/manage.py"

echo "========================================"
echo "  Desplegando App VP — entorno: $ENV"
echo "========================================"

# 1. Actualizar codigo
echo "[1/7] Actualizando codigo..."
cd "$APP_DIR"
git pull origin main

# 2. Activar/crear entorno virtual
echo "[2/7] Entorno virtual..."
if [ ! -d "$VENV" ]; then
    python3 -m venv "$VENV"
fi

# 3. Instalar dependencias
echo "[3/7] Instalando dependencias..."
$PIP install --upgrade pip -q
$PIP install -r requirements/prod.txt -q

# 4. Variables de entorno
echo "[4/7] Verificando .env..."
if [ ! -f "$APP_DIR/.env" ]; then
    echo "ERROR: Falta el archivo .env"
    echo "Copialo desde .env.example y completalo."
    exit 1
fi

# 5. Migraciones
echo "[5/7] Ejecutando migraciones..."
DJANGO_SETTINGS_MODULE=config.settings.prod $MANAGE migrate --noinput

# 6. Archivos estáticos
echo "[6/7] Recopilando archivos estaticos..."
DJANGO_SETTINGS_MODULE=config.settings.prod $MANAGE collectstatic --noinput

# 7. Reiniciar servicio
echo "[7/7] Reiniciando servicio..."
if command -v systemctl &> /dev/null; then
    sudo systemctl restart app-vp
    sudo systemctl status app-vp --no-pager
else
    echo "Reinicia el proceso manualmente (gunicorn, supervisor, etc.)"
fi

echo ""
echo "Despliegue completado exitosamente."
