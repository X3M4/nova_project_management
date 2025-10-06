#!/bin/bash

# Script de despliegue para Nova Kanban Board
# Autor: GitHub Copilot
# Fecha: $(date)

set -e  # Salir en caso de error

echo "🚀 Iniciando despliegue de Nova Kanban Board..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
PROJECT_DIR="/srv/nova_project_management/nova_project_management"
NGINX_CONFIG="/etc/nginx/sites-available/kanban.novacartografia.com"
GUNICORN_SERVICE="gunicorn-nova-kanban"

# Función para logs
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "$PROJECT_DIR/manage.py" ]; then
    error "No se encontró manage.py en $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

log "📁 Trabajando en directorio: $(pwd)"

# 1. Actualizar el código (si usas git)
if [ -d ".git" ]; then
    log "🔄 Actualizando código desde repositorio..."
    git pull origin main || warning "No se pudo actualizar desde git"
else
    log "📝 No hay repositorio git, continuando..."
fi

# 2. Activar entorno virtual si existe
if [ -d "venv" ]; then
    log "🐍 Activando entorno virtual..."
    source venv/bin/activate
elif [ -d "../venv" ]; then
    log "🐍 Activando entorno virtual..."
    source ../venv/bin/activate
else
    warning "No se encontró entorno virtual"
fi

# 3. Instalar/actualizar dependencias Python
log "📦 Instalando dependencias Python..."
pip install -r requirements.txt

# 4. Verificar que Node.js y npm están instalados
if ! command -v node &> /dev/null; then
    error "Node.js no está instalado. Instalando..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

if ! command -v npm &> /dev/null; then
    error "npm no está instalado"
    exit 1
fi

# 5. Instalar dependencias de Node.js
log "📦 Instalando dependencias de Node.js..."
npm install

# 6. Compilar Tailwind CSS para producción
log "🎨 Compilando Tailwind CSS para producción..."
npm run build-css-prod

# 7. Verificar que el archivo CSS se generó correctamente
if [ ! -f "static/css/output.css" ]; then
    error "No se generó el archivo CSS compilado"
    exit 1
fi

log "✅ CSS compilado correctamente: $(wc -l < static/css/output.css) líneas"

# 8. Ejecutar migraciones de Django
log "🗄️ Ejecutando migraciones de Django..."
python manage.py migrate

# 9. Recolectar archivos estáticos
log "📁 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

# 10. Verificar archivos estáticos
STATIC_ROOT="/srv/nova_project_management/static"
if [ ! -d "$STATIC_ROOT" ]; then
    error "No se creó el directorio de archivos estáticos"
    exit 1
fi

if [ ! -f "$STATIC_ROOT/css/output.css" ]; then
    error "El archivo CSS compilado no se copió a archivos estáticos"
    exit 1
fi

log "✅ Archivos estáticos recolectados en: $STATIC_ROOT"

# 11. Verificar permisos
log "🔒 Verificando permisos..."
sudo chown -R www-data:www-data "$STATIC_ROOT"
sudo chmod -R 755 "$STATIC_ROOT"

# 12. Reiniciar Gunicorn
log "🔄 Reiniciando Gunicorn..."
if systemctl is-active --quiet "$GUNICORN_SERVICE"; then
    sudo systemctl restart "$GUNICORN_SERVICE"
    log "✅ Gunicorn reiniciado"
else
    warning "Servicio $GUNICORN_SERVICE no está corriendo"
    log "Iniciando Gunicorn..."
    sudo systemctl start "$GUNICORN_SERVICE"
fi

# 13. Reiniciar Nginx
log "🔄 Reiniciando Nginx..."
sudo nginx -t
if [ $? -eq 0 ]; then
    sudo systemctl reload nginx
    log "✅ Nginx reiniciado"
else
    error "Error en configuración de Nginx"
    exit 1
fi

# 14. Verificar estado de los servicios
log "🔍 Verificando estado de servicios..."

if systemctl is-active --quiet "$GUNICORN_SERVICE"; then
    log "✅ Gunicorn está corriendo"
else
    error "❌ Gunicorn no está corriendo"
fi

if systemctl is-active --quiet nginx; then
    log "✅ Nginx está corriendo"
else
    error "❌ Nginx no está corriendo"
fi

# 15. Mostrar resumen
log "📊 Resumen del despliegue:"
echo "  - Proyecto: $PROJECT_DIR"
echo "  - Archivos estáticos: $STATIC_ROOT"
echo "  - CSS compilado: $(wc -l < static/css/output.css) líneas"
echo "  - Última migración: $(python manage.py showmigrations --list | tail -1)"

# 16. Hacer una prueba básica
log "🧪 Probando conectividad..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 | grep -q "200\|302"; then
    log "✅ Aplicación responde correctamente"
else
    warning "⚠️ La aplicación puede no estar respondiendo correctamente"
fi

log "🎉 ¡Despliegue completado exitosamente!"
log "🌐 Tu aplicación debería estar disponible en: https://kanban.novacartografia.com"

echo ""
echo "🔧 Si hay problemas, revisa los logs:"
echo "  - Gunicorn: sudo journalctl -u $GUNICORN_SERVICE -f"
echo "  - Nginx: sudo tail -f /var/log/nginx/kanban_error.log"
echo "  - Django: python manage.py runserver --settings=nova_workers_management.settings"
