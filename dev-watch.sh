#!/bin/bash

# Script de desarrollo con auto-reload para CSS
# Uso: ./dev-watch.sh

echo "🔄 Iniciando modo desarrollo con auto-reload de CSS..."
echo "📁 Directorio de trabajo: $(pwd)"
echo "⚠️  Presiona Ctrl+C para detener"
echo "---"

# Función para compilar CSS y actualizar versión
compile_and_update() {
    echo "🎨 Detectado cambio en CSS - Compilando..."
    
    # Compilar CSS
    npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --minify
    
    # Generar nueva versión
    TIMESTAMP=$(date +%Y%m%d%H%M%S)
    
    # Actualizar versión en base.html
    sed -i "s/css\/output\.css?v=[^\"']*/css\/output.css?v=${TIMESTAMP}/g" templates/base.html
    
    # Copiar al directorio estático
    sudo cp ./static/css/output.css /srv/nova_project_management/static/css/output.css
    
    # Collectstatic silencioso
    sudo /srv/nova_project_management/venv/bin/python manage.py collectstatic --noinput > /dev/null 2>&1
    
    echo "✅ CSS actualizado con versión: ${TIMESTAMP}"
    echo "🔄 Esperando próximos cambios..."
}

# Compilación inicial
compile_and_update

# Monitoring de archivos
if command -v inotifywait &> /dev/null; then
    echo "📡 Usando inotifywait para monitoreo de archivos"
    
    # Monitorear archivos CSS y templates
    inotifywait -m -r -e modify,create,delete \
        --include='\.(css|html|js)$' \
        ./static/css/ ./templates/ 2>/dev/null | \
    while read path action file; do
        if [[ "$file" == *".css" ]] || [[ "$file" == *".html" ]] || [[ "$file" == *".js" ]]; then
            compile_and_update
        fi
    done
else
    echo "⚠️  inotifywait no está instalado. Instalando..."
    sudo apt-get update && sudo apt-get install -y inotify-tools
    echo "✅ inotify-tools instalado. Reinicia el script."
fi