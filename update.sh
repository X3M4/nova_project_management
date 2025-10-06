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

# 2. Copiar CSS compilado al directorio estático
echo "📁 Copiando archivos estáticos..."
cp ./static/css/output.css /srv/nova_project_management/static/css/output.css

# 3. Recolectar archivos estáticos
echo "📦 Recolectando archivos estáticos..."
/srv/nova_project_management/venv/bin/python manage.py collectstatic --noinput

# 4. Ejecutar migraciones si hay alguna pendiente
echo "🗄️ Verificando migraciones..."
/srv/nova_project_management/venv/bin/python manage.py migrate

# 5. Reiniciar Gunicorn
echo "🔄 Reiniciando Gunicorn..."
sudo systemctl restart gunicorn-npm

# 6. Verificar estado
echo "✅ Verificando estado..."
if systemctl is-active --quiet gunicorn-npm; then
    echo "✅ Gunicorn está corriendo"
else
    echo "❌ Error: Gunicorn no está corriendo"
    exit 1
fi

# 7. Verificar respuesta
echo "🧪 Probando aplicación..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 | grep -q "200\|302"; then
    echo "✅ Aplicación responde correctamente"
else
    echo "⚠️ La aplicación puede no estar respondiendo"
fi

echo "🎉 ¡Actualización completada!"
echo "🌐 Tu aplicación está disponible en: https://kanban.novacartografia.com"
