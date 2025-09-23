from datetime import datetime, timedelta
from decimal import Decimal
import math
import re
from bs4 import BeautifulSoup
from django.http import JsonResponse
import folium
from folium.plugins import MarkerCluster, Fullscreen
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse, NoReverseMatch
from django.core.cache import cache
from .models import ProjectLocation, BigProjectLocation
from novacartografia_employee_management.models import Employee, Project
import time
import random
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable, GeocoderRateLimited
from django.db.models import Q
from django.core.paginator import Paginator
from .forms import ProjectLocationForm, BigProjectLocationForm
from django.db.models import Sum, Avg, Count


@login_required
def project_map(request):
    # Crear un mapa centrado en España
    m = folium.Map(location=[38, -4.7038], zoom_start=7,
                   tiles='OpenStreetMap', min_zoom=6, max_zoom=14, prefer_canvas=True)
    
    # Crear clusters separados para diferentes tipos
    # Crear clusters separados para diferentes tipos con configuración para mostrar marcadores al hacer clic
    marker_cluster_projects = MarkerCluster(
        name='Proyectos', 
        overlay=True, 
        control=True,
        options={
            'disableClusteringAtZoom': 15,  # Desactiva clustering a zoom alto
            'maxClusterRadius': 50,  # Radio máximo del cluster
            'spiderfyOnMaxZoom': True,  # Muestra marcadores individuales al máximo zoom
            'showCoverageOnHover': True,  # Muestra área de cobertura al hover
            'zoomToBoundsOnClick': True,  # Hace zoom al área del cluster al hacer clic
            'spiderfyDistanceMultiplier': 1.5  # Distancia entre marcadores cuando se expanden
        }
    ).add_to(m)
    
    marker_cluster_external = MarkerCluster(
        name='Externos', 
        overlay=True, 
        control=True,
        options={
            'disableClusteringAtZoom': 15,
            'maxClusterRadius': 50,
            'spiderfyOnMaxZoom': True,
            'showCoverageOnHover': True,
            'zoomToBoundsOnClick': True,
            'spiderfyDistanceMultiplier': 1.5
        }
    ).add_to(m)
    
    marker_cluster_employees = MarkerCluster(
        name='Empleados', 
        overlay=True, 
        control=True,
        options={
            'disableClusteringAtZoom': 16,  # Para empleados, desactivar clustering un poco antes
            'maxClusterRadius': 40,  # Radio menor para empleados
            'spiderfyOnMaxZoom': True,
            'showCoverageOnHover': True,
            'zoomToBoundsOnClick': True,
            'spiderfyDistanceMultiplier': 2  # Mayor distancia para empleados
        }
    ).add_to(m)
    
    marker_cluster_big_projects = MarkerCluster(
        name='Interesantes', 
        overlay=True, 
        control=True,
        options={
            'disableClusteringAtZoom': 16,  # Para empleados, desactivar clustering un poco antes
            'maxClusterRadius': 40,  # Radio menor para empleados
            'spiderfyOnMaxZoom': True,
            'showCoverageOnHover': True,
            'zoomToBoundsOnClick': True,
            'spiderfyDistanceMultiplier': 2  # Mayor distancia para empleados
        }
    ).add_to(m)
    
    # Añadir controles de pantalla completa y capas
    Fullscreen(
        position='topleft',
        title='Ver pantalla completa',
        title_cancel='Salir de pantalla completa',
        force_separate_button=True
    ).add_to(m)
    
    # Añadir control de capas
    folium.LayerControl(position="topleft").add_to(m)
    
    # Verificar cuántos proyectos tienen coordenadas
    project_locations = ProjectLocation.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    ).select_related('project')
    
    print(f"Proyectos con coordenadas: {project_locations.count()}")

    
    # Variables para contar empleados desplazados
    displaced_employees = []
    total_red_markers = 0
    
    def calculate_employee_positions(center_lat, center_lng, employee_count):
        """
        Calcula posiciones en círculo alrededor del proyecto
        """
        positions = []
        if employee_count == 0:
            return positions
        
        # Radio base en grados (aproximadamente 100-200 metros)
        base_radius = 0.004
        
        # Si hay muchos empleados, usar múltiples círculos
        if employee_count <= 8:
            # Un solo círculo
            radius = base_radius
            for i in range(employee_count):
                angle = (2 * math.pi * i) / employee_count
                lat_offset = radius * math.cos(angle)
                lng_offset = radius * math.sin(angle)
                positions.append((
                    center_lat + lat_offset,
                    center_lng + lng_offset
                ))
        else:
            # Múltiples círculos concéntricos
            employees_per_circle = 8
            circle_count = math.ceil(employee_count / employees_per_circle)
            
            employee_index = 0
            for circle in range(circle_count):
                current_radius = base_radius * (1 + circle * 0.5)  # Círculos cada vez más grandes
                employees_in_this_circle = min(employees_per_circle, employee_count - employee_index)
                
                for i in range(employees_in_this_circle):
                    angle = (2 * math.pi * i) / employees_in_this_circle
                    # Añadir un pequeño offset angular para cada círculo
                    angle += (circle * math.pi / 8)
                    
                    lat_offset = current_radius * math.cos(angle)
                    lng_offset = current_radius * math.sin(angle)
                    positions.append((
                        center_lat + lat_offset,
                        center_lng + lng_offset
                    ))
                    employee_index += 1
        
        return positions
    
    # Añadir marcadores para cada proyecto
    for location in project_locations:
        project = location.project
        
        # Verificar y convertir coordenadas
        try:
            lat = float(location.latitude)
            lng = float(location.longitude)
            
            if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                print(f"Coordenadas inválidas para {project.name}: {lat}, {lng}")
                continue
                
        except (ValueError, TypeError):
            print(f"Error convirtiendo coordenadas para {project.name}")
            continue
        
        # Obtener empleados del proyecto
        employees = Employee.objects.filter(project_id=project)
        employee_count = employees.count()
        
        # Determinar el tipo de proyecto
        project_type = getattr(project, 'type', 'project').lower()
        is_external = 'external' in project_type or 'externo' in project_type
        
        # Determinar color del marcador del proyecto
        if employee_count == 0:
            project_marker_color = "orange"
        elif is_external:
            project_marker_color = "purple"
        else:
            project_marker_color = "green"
        
        # Determinar el icono según el tipo
        if is_external:
            project_icon = 'star'
            project_cluster = marker_cluster_external
        else:
            project_icon = 'building'
            project_cluster = marker_cluster_projects
        
        # Crear popup con información del proyecto
        employees_info = []
        displaced_count = 0
        local_count = 0
        
        for employee in employees:
            employee_province = getattr(employee, 'state', None) or 'Sin provincia'
            project_province = location.province or 'Sin provincia'
            
            if (employee_province != project_province and 
                employee_province != 'Sin provincia' and 
                project_province != 'Sin provincia'):
                displaced_count += 1
                employees_info.append(f"🔴 {employee.name} (de {employee_province})")
                
                # Agregar a la lista global de empleados desplazados
                displaced_employees.append({
                    'employee': employee,
                    'employee_province': employee_province,
                    'project_province': project_province,
                    'project_name': project.name,
                    'project_id': project.id
                })
                total_red_markers += 1
            else:
                local_count += 1
                employees_info.append(f"🔵 {employee.name}")
        
        employees_list = "<br>".join(employees_info) if employees_info else "Sin empleados asignados"
        
        popup_html = f"""
        <div style="width: 250px; font-family: Arial, sans-serif;">
            <h4 style="margin: 0 0 10px 0; color: #333;">
                {'🌟' if is_external else '🏢'} {project.name}
            </h4>
            <div style="margin-bottom: 8px;">
                <strong>Tipo:</strong> 
                {'<span style="background: #C827F5; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; margin-left: 5px;">OBRA</span>' if is_external else '<span style="background: #56B32B; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; margin-left: 5px;">PROYECTO</span>'}
            </div>
            <div style="margin-bottom: 8px;"><strong>Manager:</strong> {getattr(project, 'manager', 'No asignado')}</div>
            <div style="margin-bottom: 8px;"><strong>Provincia:</strong> {location.province or 'No especificada'}</div>
            <div style="margin-bottom: 8px;">
                <strong>Empleados:</strong> {employee_count} 
                ({local_count} locales, {displaced_count} desplazados)
            </div>
            <div style="margin-bottom: 8px;"><strong>Dirección:</strong> {location.address or 'No especificada'}</div>
            {f'<div style="margin-top: 10px; font-size: 0.9em;"><strong>Personal:</strong><br>{employees_list}</div>' if employees_info else ''}
        </div>
        """
        
        # Añadir marcador del proyecto
        folium.Marker(
            location=[lat, lng],
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=f"{'🌟' if is_external else '🏢'} {project.name} ({employee_count} empleados)",
            icon=folium.Icon(
            color=project_marker_color, 
            icon=project_icon,
            prefix='fa'  # Usar Font Awesome en lugar de glyphicon
            )
        ).add_to(project_cluster)
        
        # Calcular posiciones para los empleados en círculo
        employee_positions = calculate_employee_positions(lat, lng, employee_count)
        
        # Añadir marcadores individuales para cada empleado
        for i, employee in enumerate(employees):
            employee_province = getattr(employee, 'state', None) or 'Sin provincia'
            project_province = location.province or 'Sin provincia'
            
            # Determinar color del empleado
            if (employee_province != project_province and 
                employee_province != 'Sin provincia' and 
                project_province != 'Sin provincia'):
                employee_color = "red"
                employee_icon = "exclamation-sign"
                status_text = f"Desplazado de {employee_province}"
            elif employee_province in project_province and employee_province != 'Sin provincia':
                employee_color = "blue"
                employee_icon = "user"
                status_text = "Trabajando localmente"
            else:
                employee_color = "blue"
                employee_icon = "user"
                status_text = "Trabajando localmente"
            
            # Usar la posición calculada o posición por defecto si hay error
            if i < len(employee_positions):
                emp_lat, emp_lng = employee_positions[i]
            else:
                # Fallback: posición ligeramente desplazada
                emp_lat = lat + (random.uniform(-0.001, 0.001))
                emp_lng = lng + (random.uniform(-0.001, 0.001))
            
            # Popup del empleado
            employee_popup_html = f"""
            <div style="width: 200px; font-family: Arial, sans-serif;">
                <h4 style="margin: 0 0 10px 0; color: #333;">👤 {employee.name}</h4>
                <div style="margin-bottom: 6px;"><strong>Proyecto:</strong> {project.name}</div>
                <div style="margin-bottom: 6px;"><strong>Provincia origen:</strong> {employee_province}</div>
                <div style="margin-bottom: 6px;"><strong>Provincia trabajo:</strong> {project_province}</div>
                <div style="margin-bottom: 6px;">
                    <strong>Estado:</strong> 
                    <span style="color: {'#dc3545' if employee_color == 'red' else '#007bff'};">
                        {status_text}
                    </span>
                </div>
                {f'<div style="margin-bottom: 6px;"><strong>Teléfono:</strong> {employee.phone}</div>' if hasattr(employee, 'phone') and employee.phone else ''}
                {f'<div style="margin-bottom: 6px;"><strong>Email:</strong> {employee.email}</div>' if hasattr(employee, 'email') and employee.email else ''}
            </div>
            """
            
            # Añadir marcador del empleado con línea de conexión al proyecto
            folium.Marker(
                location=[emp_lat, emp_lng],
                popup=folium.Popup(employee_popup_html, max_width=300),
                tooltip=f"👤 {employee.name} ({'Desplazado' if employee_color == 'red' else 'Local'})",
                icon=folium.Icon(
                    color=employee_color, 
                    icon=employee_icon,
                    prefix='glyphicon'
                )
            ).add_to(marker_cluster_employees)
            
            # Opcional: Añadir línea de conexión entre empleado y proyecto (solo si no hay muchos)
            if employee_count <= 10:  # Solo mostrar líneas si no hay demasiados empleados
                folium.PolyLine(
                    locations=[[lat, lng], [emp_lat, emp_lng]],
                    color='gray',
                    weight=1,
                    opacity=0.5,
                    dash_array='5, 5'
                ).add_to(m)
                
    # Añadir marcadores para proyectos interesantes
    big_project_locations = BigProjectLocation.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    )
    
    for big_location in big_project_locations:
        try:
            lat = float(big_location.latitude)
            lng = float(big_location.longitude)
            
            if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                print(f"Coordenadas inválidas para proyecto interesante {big_location.name}: {lat}, {lng}")
                continue
                
        except (ValueError, TypeError):
            print(f"Error convirtiendo coordenadas para proyecto interesante {big_location.name}")
            continue
        
        popup_html = f"""
        <div style="width: 300px; font-family: Arial, sans-serif;">
            <h4 style="margin: 0 0 10px 0; color: #8B5CF6;">
                💎 {big_location.name}
            </h4>
            <div style="margin-bottom: 8px;">
                <strong>Monto:</strong> €{big_location.amount:,.2f}
            </div>
            <div style="margin-bottom: 8px;">
                <strong>Desarrollador:</strong> {big_location.developer or 'No especificado'}
            </div>
            {f'<div style="margin-bottom: 8px;"><strong>Inicio:</strong> {big_location.start_date.strftime("%d/%m/%Y")}</div>' if big_location.start_date else ''}
            <div style="margin-bottom: 8px;">
                <strong>Ubicación:</strong> {big_location.city or 'No especificada'}, {big_location.province or 'Sin provincia'}
            </div>
            <div style="margin-bottom: 8px;">
                <strong>Dirección:</strong> {big_location.address or 'No especificada'}
            </div>
            <div style="margin-bottom: 8px;">
                <strong>Desc:</strong> {big_location.description or ''}
            </div>
            <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #e2e8f0; font-size: 0.8em; color: #666;">
                Creado: {big_location.created_at.strftime("%d/%m/%Y")}
            </div>
        </div>
        """
        
        folium.Marker(
            location=[lat, lng],
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=f"🏗️ {big_location.name}",
            icon=folium.Icon(
                color="darkblue", 
                icon="euro",
                prefix='glyphicon'
            )
        ).add_to(marker_cluster_big_projects)
    
    # Continuar con el resto del código de estadísticas...
    # NUEVO: Obtener distribución de proyectos por provincias
    from django.db.models import Count
    
    projects_by_province = ProjectLocation.objects.values(
        'province'
    ).annotate(
        count=Count('id')
    ).filter(
        count__gt=0,
        province__isnull=False
    ).exclude(
        province=''
    ).order_by('-count', 'province')
    
    # Procesar datos de proyectos por provincia
    provinces_project_data = []
    total_projects_with_location = ProjectLocation.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False,
        province__isnull=False
    ).exclude(province='').count()
    
    for province_data in projects_by_province:
        province_name = province_data['province']
        count = province_data['count']
        
        # Calcular proyectos con coordenadas en esta provincia
        with_coords_in_province = ProjectLocation.objects.filter(
            province=province_name,
            latitude__isnull=False,
            longitude__isnull=False
        ).count()
        
        # Obtener proyectos de esta provincia
        projects_in_province = ProjectLocation.objects.filter(
            province=province_name
        ).select_related('project')
        
        # Contar empleados asignados a proyectos de esta provincia
        total_employees_in_province = 0
        for project_location in projects_in_province:
            employee_count = Employee.objects.filter(project_id=project_location.project).count()
            total_employees_in_province += employee_count
        
        provinces_project_data.append({
            'name': province_name,
            'project_count': count,
            'projects_with_coords': with_coords_in_province,
            'projects_without_coords': count - with_coords_in_province,
            'percentage': round((count / total_projects_with_location) * 100, 1) if total_projects_with_location > 0 else 0,
            'total_employees': total_employees_in_province,
            'projects': [pl.project for pl in projects_in_province]
        })
    
    # Top 5 provincias con más proyectos
    top_project_provinces = provinces_project_data[:5]
    remaining_project_provinces = provinces_project_data[5:] if len(provinces_project_data) > 5 else []
    
    # NUEVO: Distribución de empleados por provincia de PROYECTOS (no por su residencia)
    employees_by_project_province = {}
    total_employees_in_projects = 0
    
    # Obtener todos los empleados con proyecto asignado
    employees_with_projects = Employee.objects.filter(
        project_id__isnull=False
    ).select_related('project_id')
    
    for employee in employees_with_projects:
        project = employee.project_id
        
        # Buscar la ubicación del proyecto
        try:
            project_location = ProjectLocation.objects.get(project=project)
            project_province = project_location.province or 'Sin provincia'
        except ProjectLocation.DoesNotExist:
            project_province = 'Sin ubicación'
        
        # Contar empleados por provincia de proyecto
        if project_province not in employees_by_project_province:
            employees_by_project_province[project_province] = {
                'name': project_province,
                'employee_count': 0,
                'employees': []
            }
        
        employees_by_project_province[project_province]['employee_count'] += 1
        employees_by_project_province[project_province]['employees'].append(employee)
        total_employees_in_projects += 1
    
    # Convertir a lista y ordenar
    provinces_employee_by_projects_data = list(employees_by_project_province.values())
    provinces_employee_by_projects_data.sort(key=lambda x: x['employee_count'], reverse=True)
    
    # Calcular porcentajes
    for province_data in provinces_employee_by_projects_data:
        province_data['percentage'] = round(
            (province_data['employee_count'] / total_employees_in_projects) * 100, 1
        ) if total_employees_in_projects > 0 else 0
    
    # Top 5 provincias con más empleados trabajando
    top_employee_project_provinces = provinces_employee_by_projects_data[:5]
    remaining_employee_project_provinces = provinces_employee_by_projects_data[5:] if len(provinces_employee_by_projects_data) > 5 else []
    
    # NUEVO: Distribución de empleados por provincia de RESIDENCIA (para comparar)
    employees_by_residence_province = Employee.objects.values(
        'state'
    ).annotate(
        count=Count('id')
    ).filter(
        count__gt=0,
        state__isnull=False
    ).exclude(
        state=''
    ).order_by('-count', 'state')
    
    provinces_employee_residence_data = []
    total_employees_with_residence = Employee.objects.filter(
        state__isnull=False
    ).exclude(state='').count()
    
    for province_data in employees_by_residence_province:
        province_name = province_data['state']
        count = province_data['count']
        
        # Empleados con coordenadas en esta provincia
        try:
            with_coords_in_province = Employee.objects.filter(
                state=province_name,
                latitude__isnull=False,
                longitude__isnull=False
            ).count()
        except:
            with_coords_in_province = 0
        
        # Empleados de esta provincia que trabajan en proyectos de la misma provincia
        local_workers = 0
        displaced_from_here = 0
        
        for employee in Employee.objects.filter(state=province_name, project_id__isnull=False):
            try:
                project_location = ProjectLocation.objects.get(project=employee.project_id)
                if project_location.province == province_name:
                    local_workers += 1
                else:
                    displaced_from_here += 1
            except ProjectLocation.DoesNotExist:
                pass
        
        provinces_employee_residence_data.append({
            'name': province_name,
            'employee_count': count,
            'employees_with_coords': with_coords_in_province,
            'employees_without_coords': count - with_coords_in_province,
            'percentage': round((count / total_employees_with_residence) * 100, 1) if total_employees_with_residence > 0 else 0,
            'local_workers': local_workers,
            'displaced_from_here': displaced_from_here
        })
    
    # Top 5 provincias por residencia
    top_employee_residence_provinces = provinces_employee_residence_data[:5]
    remaining_employee_residence_provinces = provinces_employee_residence_data[5:] if len(provinces_employee_residence_data) > 5 else []
    
    # NUEVO: Proyectos sin empleados asignados
    projects_without_employees = []
    all_projects_with_location = ProjectLocation.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    ).select_related('project')
    
    for project_location in all_projects_with_location:
        project = project_location.project
        employee_count = Employee.objects.filter(project_id=project).count()
        
        if employee_count == 0:
            projects_without_employees.append({
                'project': project,
                'location': project_location,
                'province': project_location.province or 'Sin provincia'
            })
    
    # Proyectos sin ubicación definida
    projects_without_location = {}
    projects_without_coordinates = ProjectLocation.objects.filter(
        Q(latitude__isnull=True) | Q(longitude__isnull=True)
    ).select_related('project')
    
    for project_location in projects_without_coordinates:
        project = project_location.project
        employee_count = Employee.objects.filter(project_id=project).count()
        projects_without_location[project.id] = {
            'id': project.id,
            'name': project.name,
            'manager': project.manager if hasattr(project, 'manager') else "No asignado",
            'type': project.type if hasattr(project, 'type') else "No especificado",
            'province': project_location.province or "Sin provincia",
            'employee_count': employee_count
        }
    
    # También incluir proyectos que no tienen entrada en ProjectLocation
    projects_no_location_entry = Project.objects.exclude(
        id__in=ProjectLocation.objects.values_list('project_id', flat=True)
    )
    
    for project in projects_no_location_entry:
        employee_count = Employee.objects.filter(project_id=project).count()
        projects_without_location[project.id] = {
            'name': project.name,
            'manager': project.manager if hasattr(project, 'manager') else "No asignado",
            'type': project.type if hasattr(project, 'type') else "No especificado",
            'province': "Sin definir",
            'employee_count': employee_count
        }
    
    # Renderizar el mapa
    map_html = m._repr_html_()
    
    return render(request, 'project_maps/map.html', {
        'map': map_html,
        'projects_without_location': projects_without_location,
        'project_count': project_locations.count(),
        'provinces_project_data': provinces_project_data,
        'top_project_provinces': top_project_provinces,
        'remaining_project_provinces': remaining_project_provinces,
        'provinces_employee_project_data': provinces_employee_by_projects_data,
        'top_employee_project_provinces': top_employee_project_provinces,
        'remaining_employee_project_provinces': remaining_employee_project_provinces,
        'provinces_employee_residence_data': provinces_employee_residence_data,
        'top_employee_residence_provinces': top_employee_residence_provinces,
        'remaining_employee_residence_provinces': remaining_employee_residence_provinces,
        'projects_without_employees': projects_without_employees,
        'displaced_employees': displaced_employees,  # Lista de empleados desplazados
        'total_projects_with_location': total_projects_with_location,
        'total_projects_without_location': len(projects_without_location),
        'total_employees_with_residence': total_employees_with_residence,
        'total_employees_in_projects': total_employees_in_projects,
        'total_displaced_employees': len(displaced_employees),  # Número correcto de empleados desplazados
        'total_red_markers': total_red_markers,  # Número de marcadores rojos
        'big_projects_count': big_project_locations.count()
    })



def get_project_popup_html(project, num_employees, location, request=None):
    """
    Genera el HTML para el popup de un proyecto en el mapa
    """
    try:
        # Determinar las clases de tipo de proyecto
        if project.type.lower() == 'project':
            type_class = 'project-type-project'
        elif project.type.lower() == 'external':
            type_class = 'project-type-external'
        else:
            type_class = 'project-type-other'
        
        # Preparar la información de ubicación
        location_info = []
        if hasattr(location, 'address') and location.address:
            location_info.append(location.address)
        if hasattr(location, 'city') and location.city:
            location_info.append(location.city)
        if hasattr(location, 'province') and location.province:
            location_info.append(location.province)
        if hasattr(location, 'country') and location.country:
            location_info.append(location.country)
        
        location_text = ", ".join(filter(None, location_info))
        if not location_text:
            location_text = "Ubicación sin detalles"
        
        # URL para los detalles del proyecto
        detail_url = f"/projects/{project.id}/"
        
        # Intentar usar reverse si está disponible
        try:
            if request:
                detail_url = request.build_absolute_uri(f"/projects/{project.id}/")
        except:
            pass
        
        # Generar el HTML
        return f"""
        <style>
            .project-popup {{
                width: 280px;
                padding: 16px;
                background: white;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                border: 1px solid #e2e8f0;
                font-family: system-ui, -apple-system, sans-serif;
            }}
            .project-title {{
                font-size: 1.25rem;
                font-weight: 600;
                color: #4f46e5;
                margin-bottom: 8px;
            }}
            .project-info {{
                margin-bottom: 12px;
            }}
            .project-info p {{
                margin: 4px 0;
                color: #4b5563;
            }}
            .project-label {{
                font-weight: 500;
                margin-right: 4px;
            }}
            .project-type {{
                display: inline-block;
                padding: 2px 8px;
                font-size: 0.75rem;
                border-radius: 9999px;
            }}
            .project-type-project {{
                background-color: #dcfce7;
                color: #166534;
            }}
            .project-type-external {{
                background-color: #f3e8ff;
                color: #6b21a8;
            }}
            .project-type-other {{
                background-color: #dbeafe;
                color: #1e40af;
            }}
            .project-footer {{
                margin-top: 12px;
                padding-top: 8px;
                border-top: 1px solid #e2e8f0;
            }}
            .project-link {{
                display: inline-block;
                padding: 4px 12px;
                font-size: 0.875rem;
                color: white;
                background-color: #4f46e5;
                border-radius: 6px;
                text-decoration: none;
            }}
            .project-link:hover {{
                background-color: #4338ca;
            }}
            .project-location {{
                margin-top: 8px;
                font-size: 0.875rem;
                color: #6b7280;
                font-style: italic;
            }}
        </style>
        <div class="project-popup">
            <h4 class="project-title">{project.name}</h4>
            <div class="project-info">
                <p>
                    <span class="project-label">Tipo:</span> 
                    <span class="project-type {type_class}">{project.type}</span>
                </p>
                <p><span class="project-label">Manager:</span> {project.manager if hasattr(project, 'manager') else 'No asignado'}</p>
                <p><span class="project-label">Empleados:</span> {num_employees}</p>
                <p><span class="project-label">Estado:</span> {project.status if hasattr(project, 'status') else 'No definido'}</p>
                <p class="project-location">{location_text}</p>
            </div>
            <div class="project-footer">
                <a href="{detail_url}" target="_blank" class="project-link" onclick="window.parent.location='{detail_url}'; return false;">
                    Ver detalles
                </a>
            </div>
        </div>
        """
    except Exception as e:
        # En caso de error, mostrar un mensaje genérico
        print(f"Error generando popup para proyecto {project.id}: {str(e)}")
        return f"""
        <div style="padding: 10px; text-align: center;">
            <h4>{project.name}</h4>
            <p>Error al cargar detalles</p>
        </div>
        """


@login_required
def project_detail_redirect(request, project_id):
    """
    Vista auxiliar para redirigir desde el mapa a los detalles del proyecto
    """
    # Intentar diferentes nombres de URL para redirigir
    for url_name in ['project_detail', 'project_view', 'view_project', 'project']:
        try:
            return redirect(url_name, project_id=project_id)
        except NoReverseMatch:
            continue
    
    # Si no funciona, intentar una URL directa
    return redirect(f'/projects/{project_id}/')


@login_required
def add_project_location(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    
    # Verificar si ya existe una ubicación para este proyecto
    try:
        location = ProjectLocation.objects.get(project=project)
        # Si ya existe, redirigir a la edición
        return redirect('edit_project_location', location.id)
    except ProjectLocation.DoesNotExist:
        # Continuar con la creación
        pass
    
    if request.method == 'POST':
        # Procesar el formulario manualmente
        locality = request.POST.get('locality', '').strip()
        province = request.POST.get('province', '').strip()
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        
        if locality and (latitude and longitude):
            # Crear nueva ubicación
            location = ProjectLocation(
                project=project,
                city=locality,  # Usar el campo city para la localidad
                province=province,
                latitude=latitude,
                longitude=longitude
            )
            location.save()
            
            # Asegurarse de que el estado se actualiza correctamente
            project.state = province  # Actualizar el estado del proyecto
            project.save(update_fields=['state'])  # Solo actualizar el campo state
            
            messages.success(request, f'Ubicación añadida para {project.name}')
            return redirect('project_map')
    
    return render(request, 'project_maps/add_location.html', {
        'project': project,
        'title': 'Añadir ubicación'
    })


@login_required
def edit_project_location(request, location_id):
    location = get_object_or_404(ProjectLocation, pk=location_id)
    project = location.project
    
    if request.method == 'POST':
        # Procesar el formulario manualmente
        locality = request.POST.get('locality', '').strip()
        province = request.POST.get('province', '').strip()
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        
        if locality and (latitude and longitude):
            # Actualizar ubicación
            location.city = locality  # Usar el campo city para la localidad
            location.province = province
            location.latitude = latitude
            location.longitude = longitude
            
            project.state = province
            project.save(update_fields=['state'])
            
            location.save()
            
            messages.success(request, f'Ubicación actualizada para {project.name}')
            return redirect('project_map')
        else:
            messages.error(request, 'Por favor introduce la localidad y/o selecciona una ubicación en el mapa.')
    
    context = {
        'project': project,
        'title': 'Editar ubicación',
        'location': {
            'locality': location.city,  # Usar el campo city como localidad
            'province': location.province,
            'latitude': location.latitude,
            'longitude': location.longitude
        }
    }
    
    return render(request, 'project_maps/add_location.html', context)


from django.db.models import Count

@login_required
def employee_locations_list(request):
    """Vista para mostrar una lista de empleados y gestionar sus ubicaciones."""
    # Obtener todos los empleados
    employees = Employee.objects.all().order_by('name')
    
    # Contar empleados con y sin ubicación
    try:
        employees_with_coords = Employee.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False
        ).count()
    except:
        # Si los campos no existen aún en el modelo
        employees_with_coords = 0
    
    total_employees = employees.count()
    employees_without_coords = total_employees - employees_with_coords
    
    # NUEVO: Obtener resumen por provincias
    employees_by_province = Employee.objects.values(
        'state'
    ).annotate(
        count=Count('id')
    ).filter(
        count__gt=0  # Solo provincias con al menos 1 empleado
    ).order_by('-count', 'state')
    
    # Procesar datos para mejor visualización
    provinces_data = []
    total_with_province = 0
    
    for province_data in employees_by_province:
        province_name = province_data['state']
        count = province_data['count']
        
        # Si la provincia está vacía o es None
        if not province_name:
            province_name = "Sin provincia definida"
        else:
            total_with_province += count
        
        # Calcular empleados con coordenadas en esta provincia
        try:
            with_coords_in_province = Employee.objects.filter(
                state=province_data['state'],
                latitude__isnull=False,
                longitude__isnull=False
            ).count()
        except:
            with_coords_in_province = 0
        
        provinces_data.append({
            'name': province_name,
            'total_count': count,
            'with_coords': with_coords_in_province,
            'without_coords': count - with_coords_in_province,
            'percentage': round((count / total_employees) * 100, 1) if total_employees > 0 else 0
        })
    
    # Obtener top 5 provincias con más empleados
    top_provinces = provinces_data[:5]
    
    return render(request, 'project_maps/employee_locations_list.html', {
        'employees': employees,
        'employees_with_coords': employees_with_coords,
        'employees_without_coords': employees_without_coords,
        'total_employees': total_employees,
        'provinces_data': provinces_data,
        'top_provinces': top_provinces,
        'total_with_province': total_with_province
    })


@login_required
def edit_employee_location(request, employee_id):
    """Vista para editar la ubicación de un empleado específico."""
    employee = get_object_or_404(Employee, pk=employee_id)
    
    if request.method == 'POST':
        # Procesar el formulario manualmente
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        
        if latitude and longitude:
            # Verificar si el modelo Employee tiene los campos latitude y longitude
            if not hasattr(employee, 'latitude') or not hasattr(employee, 'longitude'):
                # Si los campos no existen, mostrar un mensaje de error
                messages.error(request, 'El modelo Employee no tiene campos de latitud y longitud definidos.')
                return redirect('employee_locations_list')
            
            # Actualizar ubicación
            employee.latitude = latitude
            employee.longitude = longitude
            employee.save()
            messages.success(request, f'Ubicación actualizada para {employee.name}')
            return redirect('employee_locations_list')
        else:
            messages.error(request, 'Por favor selecciona una ubicación en el mapa.')
    
    context = {
        'employee': employee,
        'title': 'Editar ubicación del empleado',
        'location': {
            'address': employee.street if hasattr(employee, 'street') else '',
            'locality': employee.city if hasattr(employee, 'city') else '',
            'province': employee.get_state_display() if hasattr(employee, 'get_state_display') else '',
            'latitude': employee.latitude if hasattr(employee, 'latitude') else None,
            'longitude': employee.longitude if hasattr(employee, 'longitude') else None
        }
    }
    
    return render(request, 'project_maps/add_employee_location.html', context)

# Añadir estas vistas al final del archivo

@login_required
def big_project_list(request):
    """Vista para listar todos los grandes proyectos con filtros y paginación"""
    
    # Obtener parámetros de búsqueda y filtros
    search_query = request.GET.get('search', '')
    city_filter = request.GET.get('city', '')
    province_filter = request.GET.get('province', '')
    developer_filter = request.GET.get('developer', '')
    min_amount = request.GET.get('min_amount', '')
    max_amount = request.GET.get('max_amount', '')
    
    # Consulta base
    queryset = BigProjectLocation.objects.all().order_by('-created_at')
    
    # Aplicar filtros
    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(developer__icontains=search_query)
        )
    
    if city_filter:
        queryset = queryset.filter(city__icontains=city_filter)
    
    if province_filter:
        queryset = queryset.filter(province__icontains=province_filter)
    
    if developer_filter:
        queryset = queryset.filter(developer__icontains=developer_filter)
    
    if min_amount:
        try:
            queryset = queryset.filter(amount__gte=float(min_amount))
        except ValueError:
            pass
    
    if max_amount:
        try:
            queryset = queryset.filter(amount__lte=float(max_amount))
        except ValueError:
            pass
    
    # Estadísticas
    stats = queryset.aggregate(
        total_projects=Count('id'),
        total_amount=Sum('amount'),
        avg_amount=Avg('amount'),
    )
    
    # Paginación
    paginator = Paginator(queryset, 12)  # 12 proyectos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener valores únicos para los filtros
    cities = BigProjectLocation.objects.values_list('city', flat=True).distinct().exclude(city__isnull=True).exclude(city='')
    provinces = BigProjectLocation.objects.values_list('province', flat=True).distinct().exclude(province__isnull=True).exclude(province='')
    developers = BigProjectLocation.objects.values_list('developer', flat=True).distinct().exclude(developer__isnull=True).exclude(developer='')
    
    context = {
        'big_projects': page_obj,
        'stats': stats,
        'search_query': search_query,
        'city_filter': city_filter,
        'province_filter': province_filter,
        'developer_filter': developer_filter,
        'min_amount': min_amount,
        'max_amount': max_amount,
        'cities': sorted([city for city in cities if city]),
        'provinces': sorted([province for province in provinces if province]),
        'developers': sorted([developer for developer in developers if developer]),
        'page_obj': page_obj,
    }
    
    return render(request, 'project_maps/big_project_list.html', context)


@login_required
def big_project_detail(request, pk):
    """Vista para ver detalles de un gran proyecto"""
    big_project = get_object_or_404(BigProjectLocation, pk=pk)
    
    context = {
        'big_project': big_project,
    }
    
    return render(request, 'project_maps/big_project_detail.html', context)


@login_required
def big_project_create(request):
    """Vista para crear un nuevo gran proyecto"""
    if request.method == 'POST':
        form = BigProjectLocationForm(request.POST)
        if form.is_valid():
            big_project = form.save()
            messages.success(request, f'Gran proyecto "{big_project.name}" creado exitosamente.')
            return redirect('big_project_detail', pk=big_project.pk)
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = BigProjectLocationForm()
    
    context = {
        'form': form,
        'title': 'Crear Gran Proyecto',
        'button_text': 'Crear Proyecto',
    }
    
    return render(request, 'project_maps/big_project_form.html', context)


@login_required
def big_project_edit(request, pk):
    """Vista para editar un gran proyecto existente"""
    big_project = get_object_or_404(BigProjectLocation, pk=pk)
    
    if request.method == 'POST':
        form = BigProjectLocationForm(request.POST, instance=big_project)
        if form.is_valid():
            big_project = form.save()
            messages.success(request, f'Gran proyecto "{big_project.name}" actualizado exitosamente.')
            return redirect('big_project_detail', pk=big_project.pk)
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = BigProjectLocationForm(instance=big_project)
    
    context = {
        'form': form,
        'big_project': big_project,
        'title': f'Editar - {big_project.name}',
        'button_text': 'Actualizar Proyecto',
    }
    
    return render(request, 'project_maps/big_project_form.html', context)


@login_required
def big_project_delete(request, pk):
    """Vista para eliminar un gran proyecto"""
    big_project = get_object_or_404(BigProjectLocation, pk=pk)
    
    if request.method == 'POST':
        project_name = big_project.name
        big_project.delete()
        messages.success(request, f'Gran proyecto "{project_name}" eliminado exitosamente.')
        return redirect('big_project_list')
    
    context = {
        'big_project': big_project,
    }
    
    return render(request, 'project_maps/big_project_confirm_delete.html', context)


@login_required
def geocode_address(request):
    """Vista AJAX para geocodificar una dirección"""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        address = data.get('address', '').strip()
        
        if not address:
            return JsonResponse({'error': 'Dirección no proporcionada'})
        
        try:
            # Usar el geocodificador con retry
            geolocator = Nominatim(
                user_agent="nova_workers_map",
                timeout=15  # Aumentar timeout
            )
            
            # Añadir país si no está incluido
            if 'españa' not in address.lower() and 'spain' not in address.lower():
                address += ', España'
            
            location = geolocator.geocode(address, exactly_one=True, limit=1)
            
            if location:
                # Validar que las coordenadas están en rangos válidos
                lat = float(location.latitude)
                lng = float(location.longitude)
                
                # Verificar rangos válidos
                if not (-90 <= lat <= 90):
                    return JsonResponse({'error': f'Latitud fuera de rango válido: {lat}'})
                
                if not (-180 <= lng <= 180):
                    return JsonResponse({'error': f'Longitud fuera de rango válido: {lng}'})
                
                # Redondear a 6 decimales para evitar problemas de precisión
                lat = round(lat, 6)
                lng = round(lng, 6)
                
                return JsonResponse({
                    'success': True,
                    'latitude': lat,
                    'longitude': lng,
                    'display_name': location.address,
                    'formatted_coords': f"{lat}, {lng}"
                })
            else:
                return JsonResponse({'error': 'No se pudo encontrar la ubicación. Intenta con una dirección más específica.'})
                
        except GeocoderTimedOut:
            return JsonResponse({'error': 'Tiempo de espera agotado. Inténtalo de nuevo.'})
        except GeocoderUnavailable:
            return JsonResponse({'error': 'Servicio de geocodificación no disponible.'})
        except Exception as e:
            return JsonResponse({'error': f'Error de geocodificación: {str(e)}'})
    
    return JsonResponse({'error': 'Método no permitido'})

@login_required
def import_adjudicaciones_html(request):
    """Vista para importar adjudicaciones desde archivo HTML de Gestboes"""
    if request.method == 'POST':
        uploaded_file = request.FILES.get('html_file')
        
        if not uploaded_file:
            messages.error(request, 'Por favor selecciona un archivo HTML.')
            return render(request, 'project_maps/import_adjudicaciones.html')
        
        if not uploaded_file.name.endswith(('.html', '.htm')):
            messages.error(request, 'Por favor selecciona un archivo HTML válido.')
            return render(request, 'project_maps/import_adjudicaciones.html')
        
        try:
            # Read file content
            file_content = uploaded_file.read()
            
            # Try different encodings
            content_str = None
            for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    content_str = file_content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if not content_str:
                messages.error(request, 'No se pudo leer el archivo. Encoding no soportado.')
                return render(request, 'project_maps/import_adjudicaciones.html')
            
            # Process the HTML file
            result = extract_from_gestboes_html(content_str)
            
            if result['success']:
                # Store details in session for summary page
                request.session['import_details'] = result['details']
                request.session['import_summary'] = {
                    'processed': result['processed'],
                    'imported': result['imported'],
                    'skipped': result['skipped'],
                    'duplicates': result['duplicates'],
                    'errors': result['errors']
                }
                
                # Show success message
                messages.success(request, f"""
                📊 Importación completada:
                • {result['processed']} registros procesados
                • {result['imported']} proyectos importados
                • {result['skipped']} omitidos por filtros
                • {result['duplicates']} duplicados encontrados
                • {result['errors']} errores
                """)
                
                return redirect('big_project_list')
            else:
                messages.error(request, f"Error en la importación: {result.get('error', 'Error desconocido')}")
                
        except Exception as e:
            messages.error(request, f"Error procesando el archivo: {str(e)}")
            import traceback
            print(f"Error details: {traceback.format_exc()}")
        
        # Return to form if there was an error
        return render(request, 'project_maps/import_adjudicaciones.html')
    
    # Show upload form for GET requests
    return render(request, 'project_maps/import_adjudicaciones.html')

@login_required
def import_summary(request):
    """Vista para mostrar resumen detallado de la importación"""
    details = request.session.get('import_details', [])
    summary = request.session.get('import_summary', {})
    
    # Clear session after showing
    if 'import_details' in request.session:
        del request.session['import_details']
    if 'import_summary' in request.session:
        del request.session['import_summary']
    
    return render(request, 'project_maps/import_summary.html', {
        'details': details,
        'summary': summary
    })


def extract_adjudication_data(table):
    """Extract data from main adjudication table"""
    data = {}
    rows = table.find_all('tr')[1:]  # Skip header row with ID and gestboes
    
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 2:
            field_name = clean_html_text(cells[0].get_text()).lower()
            field_value = clean_html_text(cells[1].get_text())
            
            # Map fields based on Gestboes structure
            if 'descripción' in field_name or 'descripcion' in field_name:
                data['descripcion'] = field_value
                # Extract amount from description
                data['importe_from_desc'] = extract_amount_from_text(field_value)
                
            elif 'expediente' in field_name:
                data['expediente'] = field_value
                
            elif 'clase' in field_name and 'contrato' in field_name:
                data['clase_contrato'] = field_value
                
            elif 'importe' in field_name:
                data['importe'] = field_value
                data['importe_display'] = field_value
                
            elif 'area geográfica' in field_name or 'area geografica' in field_name:
                data['area_geografica'] = field_value
                
            elif 'fecha' in field_name and ('adjudicación' in field_name or 'adjudicacion' in field_name):
                data['fecha_adjudicacion'] = field_value
                
            elif 'organismo' in field_name:
                data['organismo'] = field_value
    
    return data

def extract_empresa_data(table):
    """Extract empresa data from empresa table"""
    try:
        rows = table.find_all('tr')
        if len(rows) < 2:
            return None
            
        # Get data from first data row (skip header)
        data_row = rows[1]
        cells = data_row.find_all('td')
        
        if len(cells) >= 2:
            empresa = clean_html_text(cells[0].get_text())
            euros = clean_html_text(cells[1].get_text())
            
            return {
                'empresa': empresa,
                'euros_empresa': euros,
                'importe_display': euros + ' €'
            }
    except Exception as e:
        print(f"Error extracting empresa data: {e}")
    
    return None

def clean_html_text(text):
    """Clean HTML text from spaces, tags and special characters"""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Normalize spaces and line breaks
    text = re.sub(r'\s+', ' ', text)
    
    # Remove control characters except basic ones
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    return text.strip()

def extract_amount_from_text(text):
    """Extract amounts from text using multiple patterns"""
    if not text:
        return ""
    
    patterns = [
        r'Importe de licitación \(SIN IVA\):\s*([\d.,]+)\s*EUR',
        r'Valor estimado del contrato:\s*([\d.,]+)\s*EUR',
        r'Importe de licitación \(CON IVA\):\s*([\d.,]+)\s*EUR',
        r'([\d]{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*EUR',
        r'([\d]{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*€'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return ""

def parse_amount_string(amount_str):
    """Convert amount string to float"""
    if not amount_str:
        return None
    
    try:
        # Clean: keep only numbers, dots and commas
        clean_amount = re.sub(r'[^\d,.]', '', amount_str)
        
        # Spanish format: 1.234.567,89 -> 1234567.89
        if ',' in clean_amount:
            parts = clean_amount.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                # It's Spanish format
                integer_part = parts[0].replace('.', '')
                decimal_part = parts[1]
                clean_amount = f"{integer_part}.{decimal_part}"
        
        return float(clean_amount)
    except (ValueError, TypeError):
        return None

def extract_project_name(description):
    """Extract project name from description"""
    if not description:
        return "Proyecto sin descripción"
    
    # Take until first period, line break or 100 characters
    lines = description.split('\n')
    first_line = lines[0].strip()
    
    # Look for first period that ends sentence
    sentences = re.split(r'\.\s+[A-Z]', first_line)
    if sentences:
        name = sentences[0].strip()
        if name and len(name) > 10:
            return name
    
    # Fallback: first 100 characters of first line
    if len(first_line) > 10:
        return first_line[:100] if len(first_line) > 100 else first_line
    
    return "Proyecto de construcción"

def extract_city_from_area(area_geografica):
    """Extract city from geographic area"""
    if not area_geografica:
        return ""
    
    # Split by comma and take first part
    parts = area_geografica.split(',')
    if parts:
        city = parts[0].strip()
        return city.title()
    
    return area_geografica.strip()

def extract_province_from_area(area_geografica):
    """Extract province from geographic area"""
    if not area_geografica:
        return ""
    
    parts = area_geografica.split(',')
    if len(parts) >= 2:
        return parts[1].strip().title()
    
    return area_geografica.strip().title()

def parse_spanish_date(date_str):
    """Parse Spanish dates from Gestboes format"""
    if not date_str:
        return None
    
    try:
        from datetime import datetime
        
        # Clean weekday
        clean_date = re.sub(r'^(lunes|martes|miércoles|jueves|viernes|sábado|domingo),?\s*', '', date_str.lower())
        
        # Try different formats
        formats = [
            '%d/%m/%Y',
            '%d/%m/%y',
            '%Y-%m-%d'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(clean_date.strip(), fmt).date()
            except ValueError:
                continue
        
        # Extract numbers if standard format doesn't work
        numbers = re.findall(r'\d+', date_str)
        if len(numbers) >= 3:
            day, month, year = int(numbers[0]), int(numbers[1]), int(numbers[2])
            if year < 100:
                year += 2000
            return datetime(year, month, day).date()
            
    except Exception:
        pass
    
    return None

def truncate_text(text, max_length):
    """Truncate text keeping complete words"""
    if not text or len(text) <= max_length:
        return text
    
    truncated = text[:max_length]
    # Find last space to not cut words
    last_space = truncated.rfind(' ')
    if last_space > max_length * 0.8:
        truncated = truncated[:last_space]
    
    return truncated + '...'

@login_required
def import_summary(request):
    """View to show detailed import summary"""
    details = request.session.get('import_details', [])
    summary = request.session.get('import_summary', {})
    
    # Clear session after showing
    if 'import_details' in request.session:
        del request.session['import_details']
    if 'import_summary' in request.session:
        del request.session['import_summary']
    
    return render(request, 'project_maps/import_summary.html', {
        'details': details,
        'summary': summary
    })
    
# Add these functions to your views.py file

def extract_from_gestboes_html(html_content):
    """
    Extracts adjudications from Gestboes HTML using <P></P><P></P> separators
    """
    processed = 0
    imported = 0
    skipped = 0
    duplicates = 0
    errors = 0
    details = []
    
    try:
        print("Starting HTML extraction...")
        
        # Split content by record separators
        record_sections = html_content.split('<P></P><P></P>')
        
        print(f"Found {len(record_sections)} sections after splitting")
        
        for i, section in enumerate(record_sections):
            if i == 0:  # Skip header section
                continue
            
            if not section.strip():  # Skip empty sections
                continue
                
            try:
                # Parse section with BeautifulSoup
                soup = BeautifulSoup(section, 'html.parser')
                
                # Find all tables in this section
                tables = soup.find_all('table', {'border': '1', 'width': '100%'})
                
                if not tables:
                    continue
                
                # Look for main table (with gestboes header)
                main_table = None
                empresa_table = None
                
                for table in tables:
                    rows = table.find_all('tr')
                    if not rows:
                        continue
                        
                    first_row = rows[0]
                    cells = first_row.find_all('td')
                    
                    # Check if this is the main record table (ID + "gestboes")
                    if (len(cells) >= 2 and 
                        'gestboes' in cells[1].get_text().lower()):
                        main_table = table
                        processed += 1
                        
                        # Extract record ID
                        record_id = clean_html_text(cells[0].get_text())
                        print(f"Processing record {processed}: ID {record_id}")
                        break
                    
                    # Check if this is empresa table (has "Empresa" and "Euros" headers)
                    elif table.find('th'):
                        headers = [th.get_text().lower() for th in table.find_all('th')]
                        if 'empresa' in ' '.join(headers) and 'euros' in ' '.join(headers):
                            empresa_table = table
                
                if main_table:
                    # Extract data from main table
                    record_data = extract_adjudication_data(main_table)
                    record_data['record_id'] = record_id
                    
                    # Extract empresa data if available
                    if empresa_table:
                        empresa_data = extract_empresa_data(empresa_table)
                        if empresa_data:
                            record_data.update(empresa_data)
                    
                    # Process the record
                    result = process_adjudication_record(record_data)
                    
                    # Add to details
                    detail_entry = {
                        'numero': processed,
                        'expediente': record_data.get('expediente', 'Sin expediente'),
                        'descripcion': truncate_text(record_data.get('descripcion', ''), 60),
                        'importe': record_data.get('importe_display', 'No especificado'),
                        'empresa': record_data.get('empresa', 'No especificada'),
                        'status': result['status'],
                        'reason': result.get('reason', ''),
                        'area': record_data.get('area_geografica', 'No especificada')
                    }
                    details.append(detail_entry)
                    
                    # Count results
                    if result['status'] == 'imported':
                        imported += 1
                    elif result['status'] == 'duplicate':
                        duplicates += 1
                    elif result['status'] == 'error':
                        errors += 1
                    else:
                        skipped += 1
                        
            except Exception as e:
                print(f"Error processing section {i}: {str(e)}")
                if processed > 0:  # Only count as error if we were processing a record
                    errors += 1
                    details.append({
                        'numero': processed,
                        'expediente': 'Error',
                        'descripcion': 'Error en procesamiento',
                        'importe': 'N/A',
                        'empresa': 'N/A',
                        'status': 'error',
                        'reason': f'Error: {str(e)[:50]}...',
                        'area': 'N/A'
                    })
    
    except Exception as e:
        print(f"General error in extraction: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'processed': 0,
            'imported': 0,
            'skipped': 0,
            'duplicates': 0,
            'errors': 1,
            'details': []
        }
    
    return {
        'success': True,
        'processed': processed,
        'imported': imported,
        'skipped': skipped,
        'duplicates': duplicates,
        'errors': errors,
        'details': details
    }

def extract_adjudication_data(table):
    """Extract data from main adjudication table"""
    data = {}
    rows = table.find_all('tr')[1:]  # Skip header row with ID and gestboes
    
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 2:
            field_name = clean_html_text(cells[0].get_text()).lower()
            field_value = clean_html_text(cells[1].get_text())
            
            # Map fields based on Gestboes structure
            if 'descripción' in field_name or 'descripcion' in field_name:
                data['descripcion'] = field_value
                # Extract amount from description
                data['importe_from_desc'] = extract_amount_from_text(field_value)
                
            elif 'expediente' in field_name:
                data['expediente'] = field_value
                
            elif 'clase' in field_name and 'contrato' in field_name:
                data['clase_contrato'] = field_value
                
            elif 'importe' in field_name:
                data['importe'] = field_value
                data['importe_display'] = field_value
                
            elif 'area geográfica' in field_name or 'area geografica' in field_name:
                data['area_geografica'] = field_value
                
            elif 'fecha' in field_name and ('adjudicación' in field_name or 'adjudicacion' in field_name):
                data['fecha_adjudicacion'] = field_value
                
            elif 'organismo' in field_name:
                data['organismo'] = field_value
    
    return data

def extract_empresa_data(table):
    """Extract empresa data from empresa table"""
    try:
        rows = table.find_all('tr')
        if len(rows) < 2:
            return None
            
        # Get data from first data row (skip header)
        data_row = rows[1]
        cells = data_row.find_all('td')
        
        if len(cells) >= 2:
            empresa = clean_html_text(cells[0].get_text())
            euros = clean_html_text(cells[1].get_text())
            
            return {
                'empresa': empresa,
                'euros_empresa': euros,
                'importe_display': euros + ' €'
            }
    except Exception as e:
        print(f"Error extracting empresa data: {e}")
    
    return None

def process_adjudication_record(data):
    """Process individual adjudication record with filters"""
    try:
        # Get basic fields
        descripcion = data.get('descripcion', '')
        expediente = data.get('expediente', '')
        clase_contrato = data.get('clase_contrato', '')
        area_geografica = data.get('area_geografica', '')
        empresa = data.get('empresa', '')
        fecha_adjudicacion = data.get('fecha_adjudicacion', '')
        
        # Determine amount (prioritize euros_empresa > importe > importe_from_desc)
        importe_str = (data.get('euros_empresa') or 
                      data.get('importe') or 
                      data.get('importe_from_desc', ''))
        
        if not importe_str:
            return {'status': 'skipped', 'reason': 'Sin importe especificado'}
        
        # Clean and convert amount
        amount = parse_amount_string(importe_str)
        if amount is None:
            return {'status': 'skipped', 'reason': f'Importe inválido: {importe_str}'}
        
        print(f"Processing record with amount: €{amount:,.2f}")
        
        # FILTER 1: Amount must be over 20 million EUR
        if amount < 20000000:
            return {
                'status': 'skipped',
                'reason': f'Importe bajo: €{amount:,.0f} < €20M'
            }
        
        # FILTER 2: Must contain "Obras" in contract class
        if clase_contrato and 'obras' not in clase_contrato.lower():
            return {
                'status': 'skipped',
                'reason': f'No es obra: {clase_contrato[:30]}...'
            }
        
                # Extract project name
        name = extract_project_name(descripcion)
        if len(name) > 255:
            name = name[:255]
        
        # Extract location
        city = extract_city_from_area(area_geografica)
        province = extract_province_from_area(area_geografica)
        
        # Process date - ESTO FALTABA
        start_date = parse_spanish_date(fecha_adjudicacion)
        if start_date:
            start_date = start_date + timedelta(days=60)  # +2 months
        
        # Geocode location if available
        latitude, longitude = 40.4168, -3.7038  # Default: Madrid
        
        if city or province:
            try:
                from geopy.geocoders import Nominatim
                import time
                
                geolocator = Nominatim(user_agent="nova_construction_app")
                location_query = f"{city}, {province}, España" if city and province else f"{city or province}, España"
                
                # Add delay to avoid rate limiting
                time.sleep(1)
                location = geolocator.geocode(location_query, timeout=5)
                
                if location:
                    latitude = float(location.latitude)
                    longitude = float(location.longitude)
                    print(f"Geocoded {location_query}: {latitude}, {longitude}")
                else:
                    print(f"Could not geocode: {location_query}")
                    
            except Exception as e:
                print(f"Geocoding error for {city}, {province}: {e}")
                # Keep default coordinates
        
        # Check for duplicates
        existing = BigProjectLocation.objects.filter(
            name__icontains=name[:50] if len(name) > 50 else name,
            amount=amount
        ).first()
        
        if existing:
            return {
                'status': 'duplicate',
                'reason': f'Similar a: {existing.name[:40]}...'
            }
        
        # Create record
        big_project = BigProjectLocation.objects.create(
            name=name,
            amount=amount,
            developer=empresa[:255] if empresa else 'No especificado',
            start_date=start_date,  # Ahora está definido
            city=city[:100] if city else '',
            province=province[:100] if province else '',
            description=descripcion[:1000] if descripcion else '',
            latitude=latitude,
            longitude=longitude
        )
        
        return {
            'status': 'imported',
            'reason': f'Creado: {name[:30]}... (€{amount:,.0f})',
            'project_id': big_project.id
        }
        
    except Exception as e:
        import traceback
        print(f"Error processing record: {traceback.format_exc()}")
        return {
            'status': 'error',
            'reason': f'Error: {str(e)[:40]}...'
        }

def clean_html_text(text):
    """Clean HTML text from spaces, tags and special characters"""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Normalize spaces and line breaks
    text = re.sub(r'\s+', ' ', text)
    
    # Remove control characters except basic ones
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    return text.strip()

def extract_amount_from_text(text):
    """Extract amounts from text using multiple patterns"""
    if not text:
        return ""
    
    patterns = [
        r'PBL:\s*([\d.,]+)\s*EUROS',
        r'Valor estimado[^:]*:\s*([\d.,]+)\s*EUR',
        r'Importe[^:]*:\s*([\d.,]+)\s*EUR',
        r'Importe[^:]*:\s*([\d.,]+)\s*€',
        r'([\d]{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*EUR',
        r'([\d]{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*€'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return ""

def parse_amount_string(amount_str):
    """Convert amount string to float"""
    if not amount_str:
        return None
    
    try:
        # Clean: keep only numbers, dots and commas
        clean_amount = re.sub(r'[^\d,.]', '', amount_str)
        
        # Spanish format: 1.234.567,89 -> 1234567.89
        if ',' in clean_amount:
            parts = clean_amount.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                # It's Spanish format
                integer_part = parts[0].replace('.', '')
                decimal_part = parts[1]
                clean_amount = f"{integer_part}.{decimal_part}"
        
        return float(clean_amount)
    except (ValueError, TypeError):
        return None

def extract_project_name(description):
    """Extract project name from description"""
    if not description:
        return "Proyecto sin descripción"
    
    # Take until first period, line break or 100 characters
    lines = description.split('\n')
    first_line = lines[0].strip()
    
    # Look for first period that ends sentence
    sentences = re.split(r'\.\s+[A-Z]', first_line)
    if sentences:
        name = sentences[0].strip()
        if name and len(name) > 10:
            return name
    
    # Fallback: first 100 characters of first line
    if len(first_line) > 10:
        return first_line[:100] if len(first_line) > 100 else first_line
    
    return "Proyecto de construcción"

def extract_city_from_area(area_geografica):
    """Extract city from geographic area"""
    if not area_geografica:
        return ""
    
    # Split by comma and take first part
    parts = area_geografica.split(',')
    if parts:
        city = parts[0].strip()
        return city.title()
    
    return area_geografica.strip()

def extract_province_from_area(area_geografica):
    """Extract province from geographic area"""
    if not area_geografica:
        return ""
    
    parts = area_geografica.split(',')
    if len(parts) >= 2:
        return parts[1].strip().title()
    
    return area_geografica.strip().title()

def parse_spanish_date(date_str):
    """Parse Spanish dates from Gestboes format"""
    if not date_str:
        return None
    
    try:
        from datetime import datetime
        
        # Clean weekday
        clean_date = re.sub(r'^(lunes|martes|miércoles|jueves|viernes|sábado|domingo),?\s*', '', date_str.lower())
        
        # Try different formats
        formats = [
            '%d/%m/%Y',
            '%d/%m/%y',
            '%Y-%m-%d'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(clean_date.strip(), fmt).date()
            except ValueError:
                continue
        
        # Extract numbers if standard format doesn't work
        numbers = re.findall(r'\d+', date_str)
        if len(numbers) >= 3:
            day, month, year = int(numbers[0]), int(numbers[1]), int(numbers[2])
            if year < 100:
                year += 2000
            return datetime(year, month, day).date()
            
    except Exception:
        pass
    
    return None

def truncate_text(text, max_length):
    """Truncate text keeping complete words"""
    if not text or len(text) <= max_length:
        return text
    
    truncated = text[:max_length]
    # Find last space to not cut words
    last_space = truncated.rfind(' ')
    if last_space > max_length * 0.8:
        truncated = truncated[:last_space]
    
    return truncated + '...'

@login_required
def import_summary(request):
    """View to show detailed import summary"""
    details = request.session.get('import_details', [])
    summary = request.session.get('import_summary', {})
    
    # Clear session after showing
    if 'import_details' in request.session:
        del request.session['import_details']
    if 'import_summary' in request.session:
        del request.session['import_summary']
    
    return render(request, 'project_maps/import_summary.html', {
        'details': details,
        'summary': summary
    })