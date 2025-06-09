import folium
from folium.plugins import MarkerCluster, Fullscreen
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse, NoReverseMatch
from django.core.cache import cache
from .models import ProjectLocation
from novacartografia_employee_management.models import Employee, Project
import time
import random
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable, GeocoderRateLimited


@login_required
def project_map(request):
    # Crear un mapa centrado en España
    m = folium.Map(location=[38, -4.7038], zoom_start=7,
                   tiles='OpenStreetMap', min_zoom=6, max_zoom=14, prefer_canvas=True)
    
    marker_cluster = MarkerCluster().add_to(m)
    marker_cluster_projects = MarkerCluster(name='Trabajos').add_to(m)
    
    # Añadir controles de pantalla completa
    Fullscreen(
        position='topleft',
        title='Ver pantalla completa',
        title_cancel='Salir de pantalla completa',
        force_separate_button=True
    ).add_to(m)
    
    # Verificar cuántos proyectos tienen coordenadas
    project_locations = ProjectLocation.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    ).select_related('project')
    
    print(f"Proyectos con coordenadas: {project_locations.count()}")
    
    # Añadir marcadores para cada proyecto
    for location in project_locations:
        project = location.project
        
        # Verificar y convertir coordenadas
        try:
            lat = float(location.latitude)
            lng = float(location.longitude)
            
            # Verificar rangos válidos
            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                print(f"Coordenadas inválidas para {project.name}: [{lat}, {lng}]")
                continue
                
            print(f"Añadiendo marcador para {project.name} en [{lat}, {lng}]")
            
            # Color según tipo de proyecto
            
            if hasattr(project, 'type'):
                project_type = project.type.lower() if hasattr(project.type, 'lower') else ''
                if 'project' in project_type:
                    color = 'green'
                elif 'external' in project_type:
                    color = 'purple'
            
            # Popup básico para pruebas
            popup_text = f"""
                <div style="width:200px">
                    <h4>{project.name}</h4>
                    <p>Tipo: {project.type if hasattr(project, 'type') else 'No especificado'}</p>
                    <p>Ubicación: {location.city if hasattr(location, 'city') else ''}, 
                                {location.province if hasattr(location, 'province') else ''}</p>
                    <p>Manager: {project.manager if hasattr(project, 'manager') else 'No asignado'}</p>
                    <p>Empleados: {project.employee_set.count() if hasattr(project, 'employee_set') else 0}</p>
                    <p><a href="/projects/{project.id}/" target="_blank">Ver proyecto</a></p>
                </div>
            """
            
            # Añadir marcador directamente al mapa
            folium.Marker(
                location=[lat, lng],
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=project.name,
                icon=folium.Icon(color=color, icon="building", prefix="fa"),
            ).add_to(m)
            
        except (ValueError, TypeError) as e:
            print(f"Error con coordenadas de {project.name}: {e}")
    
    # Añadir empleados al mapa
    
    # Intenta obtener empleados con coordenadas almacenadas
    employees_with_coords = Employee.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    )
    
    print(f"Empleados con coordenadas almacenadas: {employees_with_coords.count()}")
    
    employees_with_project = Employee.objects.filter(
        project_id__isnull=False
    ).select_related('project_id')
    
    try:
        # Añadir marcadores para empleados con coordenadas
        # Usaremos la ubicación de sus proyectos como alternativa
        for employee in employees_with_project:
            try:
                # Solo obtener la ubicación del proyecto una vez por empleado
                try:
                    project_location = ProjectLocation.objects.get(
                        project=employee.project_id,
                        latitude__isnull=False,
                        longitude__isnull=False
                    )
                except ProjectLocation.DoesNotExist:
                    # Si el proyecto no tiene ubicación, saltamos este empleado
                    continue
                    
                # Obtener coordenadas del proyecto
                lat = float(project_location.latitude)
                lon = float(project_location.longitude)
                
                # Añadir un pequeño desplazamiento aleatorio para evitar solapamiento
                lat += (random.random() + 0.8) * 0.01
                lon += (random.random() - 0.8) * 0.01
                
                # Obtener provincia del empleado y del proyecto para comparar
                employee_state = employee.get_state_display() if hasattr(employee, 'get_state_display') else None
                if employee_state is None and hasattr(employee, 'state'):
                    employee_state = employee.state
                
                project_state = employee.project_id.state if hasattr(employee.project_id, 'state') else None
                
                # Determinar el color basado en si las provincias coinciden
                if employee_state and project_state and employee_state != project_state:
                    color = "red"  # Provincias diferentes
                    location_mismatch = True
                    mismatch_text = f"<p class='text-red-600'>¡Ubicación diferente! (Empleado: {employee_state}, Proyecto: {project_state})</p>"
                else:
                    color = "blue"  # Provincias iguales o falta información
                    location_mismatch = False
                    mismatch_text = ""
                
                # Logging para debugging
                print(f"Empleado: {employee.name}, Estado empleado: {employee_state}, Estado proyecto: {project_state}, Color: {color}")
                
                # Popup para el empleado
                popup_text = f"""
                    <div style="width:200px">
                        <h4>{employee.name if hasattr(employee, 'name') else 'Empleado'}</h4>
                        <p>Puesto: {employee.job if hasattr(employee, 'job') and employee.job else 'No especificado'}</p>
                        <p>Ubicación: {
                            f"{employee.city}, " if hasattr(employee, 'city') and employee.city else ''
                        }{employee_state or 'No especificado'}</p>
                        <p>Proyecto: {
                            employee.project_id.name if hasattr(employee, 'project_id') and employee.project_id else 'Sin proyecto'
                        }</p>
                        {mismatch_text}
                    </div>
                """
                
                # Crear y añadir el marcador
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_text, max_width=300),
                    tooltip=employee.name,
                    icon=folium.Icon(color=color, icon="user", prefix="fa"),
                ).add_to(m)
                
            except Exception as e:
                # Capturar cualquier error y loggear para debugging
                print(f"Error procesando empleado {employee.name}: {str(e)}")
                continue
                
            except (ValueError, TypeError, AttributeError) as e:
                print(f"Error con coordenadas de empleado {employee.name}: {e}")
    
    except Exception as e:
        # Si los campos latitude/longitude no existen en Employee, usaremos geocodificación
        print(f"No se pueden mostrar empleados con coordenadas: {str(e)}")
        print("Intentando geocodificar empleados usando su ubicación...")
        
        # Usaremos la ubicación de sus proyectos como alternativa
        employees_by_project = Employee.objects.filter(
            project_id__isnull=False
        ).select_related('project_id')
        
        # Diccionario para almacenar empleados por proyecto
        employees_by_project_dict = {}
        
        # Agrupar empleados por proyecto
        for employee in employees_by_project:
            project_id = employee.project_id.id
            if project_id not in employees_by_project_dict:
                employees_by_project_dict[project_id] = []
            employees_by_project_dict[project_id].append(employee)
        
        # Añadir empleados usando las coordenadas de sus proyectos
        for project_id, employees in employees_by_project_dict.items():
            try:
                # Obtener ubicación del proyecto
                project_location = ProjectLocation.objects.get(
                    project_id=project_id,
                    latitude__isnull=False,
                    longitude__isnull=False
                )
                
                # Obtener la provincia del proyecto
                project_province = project_location.province
                
                lat = float(project_location.latitude)
                lng = float(project_location.longitude)
                
                # Para múltiples empleados en el mismo proyecto, agregar ligera dispersión
                for i, employee in enumerate(employees):
                    # Obtener la provincia del empleado (si tiene)
                    employee_province = employee.state if hasattr(employee, 'province') and employee.province else None
                    employee_job = employee.job if hasattr(employee, 'job') else "No especificado"
                    
                    # Determinar color del marcador basado en coincidencia de provincias
                    marker_color = ""  # Color por defecto
                    icon_color = "green"
                    if "TOPÓGRAFO" in employee_job:
                        # Si el empleado es topógrafo, cambiar el color del icono
                        icon_color = " #20f00b"
                    elif "Auxiliar" in employee_job:
                        icon_color = " #f0e20b "  # Amarillo para auxiliares
                    elif "Piloto" in employee_job:
                        icon_color = " #0b99f0 "
                    else: 
                        icon_color = "orange"
                    
                    # Si las provincias no coinciden, usar rojo
                    if project_province and employee_province and project_province.lower() != employee_province.lower():
                        marker_color = "red"
                        province_match_text = f"<p class='text-red-600'>¡Provincia diferente! Empleado: {employee_province}, Proyecto: {project_province}</p>"
                    else:
                        marker_color = "blue"
                        
                    # Añadir una pequeña variación para evitar solapamiento
                    employee_lat = lat + (random.random() - 0.5) * 0.01
                    employee_lng = lng + (random.random() - 0.5) * 0.01
                    
                    # Popup para el empleado con información de provincias
                    popup_text = f"""
                    <div style="width:250px">
                        <h4>{employee.name}</h4>
                        <p>Puesto: {employee.job}</p>
                        <p>Proyecto: {employee.project_id.name}</p>
                        <p>Ubicación: {project_province}</p>
                        {province_match_text}
                    </div>
                    """
                    
                    # Añadir marcador usando las coordenadas del proyecto
                    folium.Marker(
                        location=[employee_lat, employee_lng],
                        popup=folium.Popup(popup_text, max_width=300),
                        tooltip=employee.name,
                        icon=folium.Icon(color=marker_color,icon_color=icon_color, icon="user", prefix="fa"),
                    ).add_to(marker_cluster)  # Añade al cluster de marcadores
                    
            except (ProjectLocation.DoesNotExist, ValueError, TypeError) as e:
                # Proyecto sin ubicación o coordenadas inválidas
                continue
    
    # Filtramos solo los empleados sin proyecto asignado o aquellos que queremos mostrar en su ubicación real
    employees_with_coords = Employee.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False,
        project_id__isnull=True  # Solo mostrar empleados sin proyecto en sus propias coordenadas
    )
    
    for employee in employees_with_coords:
        # Crear popup para el empleado
        popup_html = f"""
        <div style="width:200px">
            <h4>{employee.name}</h4>
            <p>Puesto: {employee.job if employee.job else 'No especificado'}</p>
            <p>Ubicación: {employee.province if hasattr(employee, 'province') and employee.province else 'No especificada'}</p>
            <p class="text-green-600">Disponible para asignación</p>
        </div>
        """
        icon_color = "green"
        if "TOPÓGRAFO" in employee.job:
            # Si el empleado es topógrafo, cambiar el color del icono
            icon_color = " #20f00b"
        elif "Auxiliar" in employee.job:
            icon_color = " #f0e20b "  # Amarillo para auxiliares
        elif "Piloto" in employee.job:
            icon_color = " #0b99f0 "
        else: 
            icon_color = "orange"
        
        # Añadir marcador con la ubicación real del empleado
        folium.Marker(
            location=[employee.latitude, employee.longitude],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=employee.name,
            icon=folium.Icon(color="gray",icon_color=icon_color, icon="user", prefix="fa"),  # Verde para empleados disponibles
        ).add_to(marker_cluster)
        
    # Recopilar proyectos sin ubicación
    projects_without_location = {}
    for project in Project.objects.all():
        try:
            location = ProjectLocation.objects.get(project=project)
            if location.latitude is None or location.longitude is None:
                projects_without_location[project.id] = {
                    'name': project.name,
                    'manager': project.manager if hasattr(project, 'manager') else "No asignado",
                    'type': project.type if hasattr(project, 'type') else "No especificado"
                }
        except ProjectLocation.DoesNotExist:
            projects_without_location[project.id] = {
                'name': project.name,
                'manager': project.manager if hasattr(project, 'manager') else "No asignado",
                'type': project.type if hasattr(project, 'type') else "No especificado"
            }
    
    # Renderizar el mapa
    map_html = m._repr_html_()
    
    # Renderizar la plantilla con datos adicionales para debugging
    return render(request, 'project_maps/map.html', {
        'map': map_html,
        'projects_without_location': projects_without_location,
        'project_count': project_locations.count()
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
    
    return render(request, 'project_maps/employee_locations_list.html', {
        'employees': employees,
        'employees_with_coords': employees_with_coords,
        'employees_without_coords': employees_without_coords,
        'total_employees': total_employees
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
