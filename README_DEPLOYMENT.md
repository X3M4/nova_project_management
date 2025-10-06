# Nova Kanban Board - Despliegue en Producción

## 📋 Resumen

Este documento describe cómo desplegar correctamente Nova Kanban Board en producción con Ubuntu 24.04, Nginx, Gunicorn y Tailwind CSS compilado.

## 🚀 Configuración Completada

### Archivos de Configuración

1. **tailwind.config.js** - Configuración de Tailwind CSS con clases personalizadas
2. **package.json** - Dependencias de Node.js y scripts de compilación
3. **static/css/input.css** - Archivo de entrada para Tailwind CSS
4. **static/css/output.css** - CSS compilado y minificado para producción
5. **gunicorn.conf.py** - Configuración optimizada de Gunicorn
6. **gunicorn-nova-kanban.service** - Servicio systemd para Gunicorn
7. **.env** - Variables de entorno actualizadas para producción

### Cambios en Django

- **settings.py**: Configurado WhiteNoise para servir archivos estáticos
- **base.html**: Actualizado para usar CSS compilado en producción
- **requirements.txt**: Añadido WhiteNoise para servir archivos estáticos

## 🛠️ Scripts de Despliegue

### Script Completo de Despliegue
```bash
./deploy.sh
```
- Instala dependencias
- Compila Tailwind CSS
- Ejecuta migraciones
- Recolecta archivos estáticos
- Reinicia servicios

### Script de Actualización Rápida
```bash
./update.sh
```
- Compila CSS
- Recolecta archivos estáticos
- Reinicia Gunicorn
- Verifica funcionamiento

## 🔧 Configuración de Nginx

Tu configuración actual de Nginx está bien. Los archivos estáticos se sirven desde:
```
/srv/nova_project_management/static/
```

## 📝 Comandos Manuales

### Compilar Tailwind CSS
```bash
cd /srv/nova_project_management/nova_project_management
npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --minify
```

### Recolectar Archivos Estáticos
```bash
/srv/nova_project_management/venv/bin/python manage.py collectstatic --noinput
```

### Gestionar Servicio Gunicorn
```bash
sudo systemctl status gunicorn-nova-kanban
sudo systemctl restart gunicorn-nova-kanban
sudo systemctl reload gunicorn-nova-kanban
```

## 🐛 Resolución de Problemas

### 1. CSS no se carga correctamente
```bash
# Verificar que el archivo CSS existe
ls -la /srv/nova_project_management/static/css/output.css

# Recompilar CSS
npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --minify

# Copiar al directorio estático
cp ./static/css/output.css /srv/nova_project_management/static/css/output.css

# Verificar permisos
sudo chown -R www-data:www-data /srv/nova_project_management/static
```

### 2. Kanban no funciona (solo plano)
- **Causa**: CSS de Tailwind no compilado o no cargado
- **Solución**: Ejecutar `./update.sh`

### 3. No se ven proyectos, solo obras
- **Causa**: JavaScript no carga o problemas con el template
- **Solución**: Verificar logs del navegador y del servidor

### 4. Gunicorn no arranca
```bash
# Ver logs detallados
sudo journalctl -u gunicorn-nova-kanban -f

# Verificar configuración
/srv/nova_project_management/venv/bin/gunicorn --check-config nova_workers_management.wsgi:application

# Reiniciar servicio
sudo systemctl restart gunicorn-nova-kanban
```

## 📊 Logs

### Gunicorn
```bash
sudo journalctl -u gunicorn-nova-kanban -f
tail -f /var/log/gunicorn/nova_kanban_error.log
tail -f /var/log/gunicorn/nova_kanban_access.log
```

### Nginx
```bash
tail -f /var/log/nginx/kanban_error.log
tail -f /var/log/nginx/kanban_access.log
```

### Django
```bash
cd /srv/nova_project_management/nova_project_management
/srv/nova_project_management/venv/bin/python manage.py runserver --settings=nova_workers_management.settings
```

## 🔍 Verificación del Estado

### Servicios
```bash
systemctl status gunicorn-nova-kanban
systemctl status nginx
```

### Conectividad
```bash
curl -I http://localhost:8000
curl -I https://kanban.novacartografia.com
```

### Archivos CSS
```bash
# Verificar tamaño del archivo CSS compilado
wc -l /srv/nova_project_management/static/css/output.css

# Debe mostrar alrededor de 1000+ líneas si está compilado correctamente
```

## 📋 Checklist de Despliegue

- [ ] Node.js y npm instalados
- [ ] Tailwind CSS compilado (`output.css` existe y tiene contenido)
- [ ] Archivos estáticos recolectados
- [ ] Permisos correctos en `/srv/nova_project_management/static`
- [ ] Servicio Gunicorn corriendo
- [ ] Nginx configurado y corriendo
- [ ] HTTPS funcionando
- [ ] CSS cargando correctamente en el navegador
- [ ] Kanban board funcional (drag & drop)
- [ ] Ambas secciones visibles (Obras y Proyectos)

## 🚨 Problemas Conocidos

1. **CSS no aplica**: Asegúrate de que `DEBUG=False` en producción
2. **Archivos estáticos 404**: Verifica que Nginx apunta al directorio correcto
3. **Permisos**: www-data debe tener acceso de lectura a todos los archivos estáticos

## 🔄 Flujo de Actualización Futuro

1. Hacer cambios en el código
2. Si cambias CSS: Ejecutar `./update.sh`
3. Si cambias modelos: Hacer migraciones + `./update.sh`
4. Si solo cambias Python: `sudo systemctl restart gunicorn-nova-kanban`

## 📞 Soporte

Si hay problemas:
1. Verificar logs de Gunicorn y Nginx
2. Comprobar que todos los servicios están corriendo
3. Verificar permisos de archivos
4. Probar en modo desarrollo para aislar el problema
