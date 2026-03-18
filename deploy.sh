#!/bin/bash
# =============================================================================
# deploy.sh — Actualizacion del sitio en produccion
# Ejecutar desde el servidor:
#   cd /var/www/app-vp && bash deploy.sh
# =============================================================================

set -e

APP_DIR="/var/www/app-vp"
APP_USER="appvp"
PYTHON="$APP_DIR/.venv/bin/python"
PIP="$APP_DIR/.venv/bin/pip"
MANAGE="DJANGO_SETTINGS_MODULE=config.settings.prod $PYTHON $APP_DIR/manage.py"

echo "========================================"
echo "  Desplegando App VP — $(date '+%d/%m/%Y %H:%M')"
echo "========================================"

cd "$APP_DIR"

echo "[1/5] Actualizando codigo desde GitHub..."
sudo -u "$APP_USER" git pull origin main

echo "[2/5] Instalando dependencias..."
sudo -u "$APP_USER" "$PIP" install -r requirements/prod.txt -q

echo "[3/5] Ejecutando migraciones..."
sudo -u "$APP_USER" bash -c "$MANAGE migrate --noinput"

echo "[4/5] Recopilando archivos estaticos..."
sudo -u "$APP_USER" bash -c "$MANAGE collectstatic --noinput"

echo "[5/5] Reiniciando servicio..."
systemctl restart app-vp
systemctl is-active --quiet app-vp && \
    echo "Servicio reiniciado correctamente." || \
    { echo "ERROR: el servicio no levanto."; journalctl -u app-vp -n 20 --no-pager; exit 1; }

echo ""
echo "Despliegue completado — https://app.patioviejo.click"
