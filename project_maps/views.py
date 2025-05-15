from django.contrib import messages
from .forms import ProjectLocationForm
from .models import ProjectLocation
from novacartografia_employee_management.models import Project
from geopy.geocoders import Nominatim
import folium
from folium.plugins import MarkerCluster, Search
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from branca.element import Template, MacroElement
from django.urls import reverse

@login_required
def project_map(request):
    # Crear un mapa centrado en España
    m = folium.Map(location=[40.4168, -3.7038], zoom_start=7)
    
    # Crear un grupo de marcadores para agrupar marcadores cercanos
    marker_cluster = MarkerCluster().add_to(m)
    
    project_locations = ProjectLocation.objects.all().select_related('project')
    
    # Diccionario para almacenar proyectos sin ubicación
    projects_without_location = {}
    
    # Añadir marcadores para cada proyecto con ubicación
    for location in project_locations:
        project = location.project
        
        # Calcular el número de empleados en el proyecto
        num_employees = project.employee_set.count() if hasattr(project, 'employee_set') else 0
        
        # Determinar el color según el tipo de proyecto
        color = 'blue'
        if project.type.lower() == 'project':
            color = 'green'
        elif project.type.lower() == 'external':
            color = 'purple'
        
        # Crear un popup con información detallada del proyecto
        popup_html = f"""
        <div style="width: 250px;">
            <h4 style="color: #333;">{project.name}</h4>
            <p><strong>Tipo:</strong> {project.type}</p>
            <p><strong>Manager:</strong> {project.manager}</p>
            <p><strong>Empleados:</strong> {num_employees}</p>
            <p><strong>Estado:</strong> {project.state}</p>
            <p><a href="{reverse('project_detail', args=[project.id])}" target="_blank">Ver detalles</a></p>
        </div>
        """
        
        iframe = folium.IFrame(popup_html, width=300, height=200)
        popup = folium.Popup(iframe, max_width=300)
        
        # Crear un tooltip (texto que se muestra al pasar el ratón)
        tooltip = f"{project.name} ({num_employees} empleados)"
        
        # Añadir el marcador al mapa
        folium.Marker(
            location=[location.latitude, location.longitude],
            popup=popup,
            tooltip=tooltip,
            icon=folium.Icon(color=color, icon='info-sign')
        ).add_to(marker_cluster)
    
    # Recopilar proyectos sin ubicación
    for project in Project.objects.all():
        if not hasattr(project, 'location'):
            manager = project.manager if project.manager else "No asignado"
            projects_without_location[project.id] = {
                'name': project.name,
                'manager': manager,
                'type': project.type
            }
    
    # Guardar mapa en HTML
    map_html = m._repr_html_()
    
    # Renderizar la plantilla con el mapa y la lista de proyectos sin ubicación
    return render(request, 'project_maps/map.html', {
        'map': map_html,
        'projects_without_location': projects_without_location
    })

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
        form = ProjectLocationForm(request.POST)
        if form.is_valid():
            location = form.save(commit=False)
            location.project = project
            location.save()
            messages.success(request, f'Ubicación agregada para el proyecto {project.name}')
            return redirect('project_map')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        # Inicializar con valores por defecto para España
        form = ProjectLocationForm(initial={'country': 'España'})
    
    return render(request, 'project_maps/add_location.html', {
        'form': form,
        'project': project,
    })

@login_required
def edit_project_location(request, location_id):
    location = get_object_or_404(ProjectLocation, pk=location_id)
    project = location.project
    
    if request.method == 'POST':
        form = ProjectLocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            messages.success(request, f'Ubicación actualizada para el proyecto {project.name}')
            return redirect('project_map')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = ProjectLocationForm(instance=location)
    
    # Usar la misma plantilla que para añadir, pero con título diferente
    return render(request, 'project_maps/add_location.html', {
        'form': form,
        'project': project,
        'title': 'Editar ubicación'  # Cambia el título para reflejar que es una edición
    })