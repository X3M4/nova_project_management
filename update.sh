#!/bin/bash

# Script de actualización rápida para Nova Kanban Board
# Uso: ./update.sh

set -e

echo "🔄 Actualizando Nova Kanban Board..."

# Moverse al directorio del proyecto
cd /srv/nova_project_management/nova_project_management

# 1. Compilar Tailwind CSS
echo "🎨 Compilando CSS..."
npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --minify

# 2. Generar versión automática para cache-busting
TIMESTAMP=$(date +%Y%m%d%H%M%S)
echo "🔄 Actualizando versión CSS a: ${TIMESTAMP}"

# 3. Actualizar la versión en base.html
sed -i "s/?v=[0-9]*/?v=${TIMESTAMP}/g" templates/base.html

# 4. Copiar CSS compilado al directorio estático
echo "📁 Copiando archivos estáticos..."
sudo cp ./static/css/output.css /srv/nova_project_management/static/css/output.css

# 5. Recolectar archivos estáticos
echo "📦 Recolectando archivos estáticos..."
sudo /srv/nova_project_management/venv/bin/python manage.py collectstatic --noinput

# 6. Ejecutar migraciones si hay alguna pendiente
echo "🗄️ Verificando migraciones..."
/srv/nova_project_management/venv/bin/python manage.py migrate

# 7. Reiniciar Gunicorn (usando el servicio correcto)
echo "🔄 Reiniciando Gunicorn..."
sudo systemctl restart gunicorn-npm

# 8. Verificar estado
echo "✅ Verificando estado..."
if systemctl is-active --quiet gunicorn-npm; then
    echo "✅ Gunicorn está corriendo"
else
    echo "❌ Error: Gunicorn no está corriendo"
    exit 1
fi

# 9. Verificar respuesta
echo "🧪 Probando aplicación..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 | grep -q "200\|302"; then
    echo "✅ Aplicación responde correctamente"
else
    echo "⚠️ La aplicación puede no estar respondiendo"
fi

echo "🎉 ¡Actualización completada!"
echo "🔄 Versión CSS actualizada: ${TIMESTAMP}"
echo "🌐 Tu aplicación está disponible en: https://kanban.novacartografia.com"
echo "💡 Los estilos se actualizarán automáticamente sin problemas de cache"
