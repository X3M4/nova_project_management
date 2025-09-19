from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import ProjectLocation, BigProjectLocation

@admin.register(ProjectLocation)
class ProjectLocationAdmin(admin.ModelAdmin):
    # Campos a mostrar en la lista
    list_display = [
        'project_name_link',
        'latitude', 
        'longitude',
        'address_short',
        'city',
        'province',
        'country',
        'coordinates_link',
        'created_at',
        'updated_at'
    ]
    
    # Campos editables directamente en la lista
    list_editable = [
        'city',
        'province',
        'country'
    ]
    
    # Campos por los que se puede buscar
    search_fields = [
        'project__name',
        'address',
        'city',
        'province',
        'country'
    ]
    
    # Filtros laterales
    list_filter = [
        'province',
        'country',
        'created_at',
        'updated_at'
    ]
    
    # Campos de solo lectura en el formulario de detalle
    readonly_fields = [
        'created_at',
        'updated_at',
        'coordinates_map_link'
    ]
    
    # Organización de campos en el formulario de detalle
    fieldsets = (
        ('Proyecto', {
            'fields': ('project',)
        }),
        ('Coordenadas', {
            'fields': ('latitude', 'longitude', 'coordinates_map_link'),
            'description': 'Coordenadas geográficas del proyecto'
        }),
        ('Dirección', {
            'fields': ('address', 'city', 'province', 'country'),
            'description': 'Información de la dirección'
        }),
        ('Información del Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Ordenamiento por defecto
    ordering = ['project__name']
    
    # Número de elementos por página
    list_per_page = 25
    
    # Acciones personalizadas
    actions = ['update_provinces_from_coordinates', 'clear_coordinates']
    
    def project_name_link(self, obj):
        """Enlace al proyecto en el admin"""
        if obj.project:
            url = reverse('admin:novacartografia_employee_management_project_change', args=[obj.project.pk])
            return format_html('<a href="{}" target="_blank">{}</a>', url, obj.project.name)
        return '-'
    project_name_link.short_description = 'Proyecto'
    project_name_link.admin_order_field = 'project__name'
    
    def address_short(self, obj):
        """Versión corta de la dirección para la lista"""
        if obj.address:
            return obj.address[:50] + '...' if len(obj.address) > 50 else obj.address
        return '-'
    address_short.short_description = 'Dirección'
    address_short.admin_order_field = 'address'
    
    def coordinates_link(self, obj):
        """Enlace a Google Maps con las coordenadas"""
        if obj.latitude and obj.longitude:
            url = f"https://www.google.com/maps?q={obj.latitude},{obj.longitude}"
            return format_html(
                '<a href="{}" target="_blank" title="Ver en Google Maps">'
                '<span style="color: #0066cc;">📍 Ver Mapa</span></a>', 
                url
            )
        return '-'
    coordinates_link.short_description = 'Mapa'
    
    def coordinates_map_link(self, obj):
        """Enlace a Google Maps en el formulario de detalle"""
        if obj.latitude and obj.longitude:
            url = f"https://www.google.com/maps?q={obj.latitude},{obj.longitude}"
            return format_html(
                '<a href="{}" target="_blank" class="button">'
                'Ver ubicación en Google Maps</a><br><br>'
                '<iframe src="https://www.google.com/maps/embed/v1/place?key=YOUR_API_KEY&q={},{}" '
                'width="100%" height="200" frameborder="0" style="border:0;" allowfullscreen="" '
                'aria-hidden="false" tabindex="0"></iframe>', 
                url, obj.latitude, obj.longitude
            )
        return 'No hay coordenadas disponibles'
    coordinates_map_link.short_description = 'Mapa de Ubicación'
    
    def update_provinces_from_coordinates(self, request, queryset):
        """Acción para actualizar provincias basándose en las coordenadas"""
        updated_count = 0
        for location in queryset:
            if location.latitude and location.longitude:
                if location.geocode_address():  # Requiere el método del modelo actualizado
                    location.save()
                    updated_count += 1
        
        self.message_user(
            request,
            f'{updated_count} ubicaciones actualizadas con información de provincia.'
        )
    update_provinces_from_coordinates.short_description = "Actualizar provincias desde coordenadas"
    
    def clear_coordinates(self, request, queryset):
        """Acción para limpiar coordenadas"""
        count = queryset.update(latitude=None, longitude=None, address='', city='', province='')
        self.message_user(
            request,
            f'{count} ubicaciones han sido limpiadas.'
        )
    clear_coordinates.short_description = "Limpiar coordenadas y direcciones"
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        return super().get_queryset(request).select_related('project')
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)  # CSS personalizado opcional
        }
        js = ('admin/js/custom_admin.js',)  # JavaScript personalizado opcional

# Si no quieres usar el decorador @admin.register, puedes usar:
# admin.site.register(ProjectLocation, ProjectLocationAdmin)

@admin.register(BigProjectLocation)
class BigProjectLocationAdmin(admin.ModelAdmin):
    # Lista simple sin métodos personalizados complejos
    list_display = [
        'name',
        'amount',
        'developer',
        'city',
        'province',
        'start_date',
        'created_at'
    ]
    
    search_fields = [
        'name',
        'developer',
        'city',
        'province'
    ]
    
    list_filter = [
        'developer',
        'province',
        'start_date',
        'created_at'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Información del Proyecto', {
            'fields': ('name', 'amount', 'developer', 'start_date')
        }),
        ('Ubicación', {
            'fields': ('latitude', 'longitude', 'city', 'province', 'country', 'address')
        }),
        ('Descripción', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    ordering = ['-amount', 'name']
    list_per_page = 25