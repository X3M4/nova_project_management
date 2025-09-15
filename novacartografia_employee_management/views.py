import csv
from django.urls import path
from django.utils import timezone
import io
import json
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Group
from .forms import EmployeeCSVImportForm, EmployeeForm, EmployeeNeededForm, GetEmployeeLockedForm, ProjectCSVImportForm, ProjectForm
from .models import Employee, GetEmployeeLocked, Project, ProjectMovementLine, EmployeeNeeded, EmployeeVacation
from django.http import HttpResponse, JsonResponse
from django.db.models import Case, When, Value, CharField, Q, IntegerField, Count, Q, BooleanField, FloatField, F, Min
from django.db.models.functions import Cast
from functools import reduce
import operator
from datetime import datetime, date, timedelta
import re
import locale

# Función auxiliar para verificar permisos de escritura
def can_edit(user):
    """Verifica si el usuario puede editar (no está en grupo solo_lectura)"""
    try:
        solo_lectura_group = Group.objects.get(name='solo_lectura')
        return not user.groups.filter(id=solo_lectura_group.id).exists()
    except Group.DoesNotExist:
        # Si el grupo no existe, permitir edición
        return True

# Decorador personalizado para vistas que requieren permisos de escritura
def require_edit_permission(view_func):
    """Decorador que verifica si el usuario puede editar"""
    def wrapper(request, *args, **kwargs):
        if not can_edit(request.user):
            messages.error(request, 'No tienes permisos para realizar esta acción.')
            return redirect('kanban_board')  # o la vista que prefieras
        return view_func(request, *args, **kwargs)
    return wrapper

# ...existing code...

@login_required
def employee_list(request):
    employees = Employee.objects.all()
    
    # Handle search
    search_query = request.GET.get('search')
    if search_query:
        employees = employees.filter(
            Q(name__icontains=search_query) |
            Q(job__icontains=search_query) |
            Q(street__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(state__icontains=search_query) |
            Q(academic_training__icontains=search_query) |
            Q(project_id__name__icontains=search_query)
        )
    
    # Añadir variable de contexto para permisos
    context = {
        'employees': employees,
        'can_edit': can_edit(request.user),
        'search_query': search_query,
    }
    
    return render(request, 'novacartografia_employee_management/employee_list.html', context)

# Create your views here.
@login_required
@require_edit_permission
def import_employees_csv(request):
    # Crear la instancia del formulario fuera de los bloques if/else
    form = EmployeeCSVImportForm()
    
    if request.method == 'POST':
        form = EmployeeCSVImportForm(request.POST, request.FILES)
        
        if form.is_valid():
            csv_file = request.FILES.get('csv_file')
            
            if not csv_file or not csv_file.name.endswith('.csv'):
                messages.error(request, 'Por favor, selecciona un archivo CSV válido.')
                return redirect('employee_list')
            
            try:
                # Read CSV file
                file_data = csv_file.read().decode('utf-8')
                csv_reader = csv.DictReader(io.StringIO(file_data))
                
                created_count = 0
                modified_count = 0
                deleted_count = 0
                error_count = 0
                error_messages = []
                csv_employee_names = []
                
                # Contadores para vacaciones
                vacation_created_count = 0
                vacation_updated_count = 0
                vacation_deleted_count = 0
                
                for row in csv_reader:
                    try:
                        # Procesar datos del empleado
                        employee_data = {}
                        vacation_data = {}
                        
                        # Mapeo de campos del empleado
                        field_mapping = {
                            'Name': 'name',
                            'Job': 'job',
                            'Street': 'street',
                            'City': 'city',
                            'State': 'state',
                            'Academic Training': 'academic_training',
                            'Driver License': 'driver_license',
                            'Twenty Hours': 'twenty_hours',
                            'Sixty Hours': 'sixty_hours',
                            'Confine': 'confine',
                            'Mining': 'mining',
                            'Railway Carriage': 'railway_carriage',
                            'Railway Mounting': 'railway_mounting',
                            'Building': 'building',
                            'Office Work': 'office_work',
                            'Scanner': 'scanner',
                            'Leveling': 'leveling',
                            'Static': 'static',
                            'Drag': 'drag',
                            'Active': 'active',
                            'Service Start Date': 'start_date',
                            'Service Termination Date': 'end_date'
                        }
                        
                        # Procesar campos del empleado
                        for csv_field, model_field in field_mapping.items():
                            if csv_field in row and row[csv_field].strip():
                                value = row[csv_field].strip()
                                
                                # Conversión de tipos específicos
                                if model_field in ['driver_license', 'twenty_hours', 'sixty_hours', 'confine', 'height',
                                                 'mining', 'railway_carriage', 'railway_mounting', 'building', 
                                                 'office_work', 'scanner', 'leveling', 'static', 'drag', 'active']:
                                    employee_data[model_field] = value.lower() in ['true', '1', 'yes', 'sí', 'si']
                                elif model_field in ['start_date', 'end_date']:
                                    try:
                                        # Intentar diferentes formatos de fecha
                                        date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']
                                        for date_format in date_formats:
                                            try:
                                                employee_data[model_field] = datetime.strptime(value, date_format).date()
                                                break
                                            except ValueError:
                                                continue
                                        else:
                                            error_messages.append(f"Formato de fecha inválido para {csv_field}: {value}")
                                            continue
                                    except Exception as e:
                                        error_messages.append(f"Error procesando fecha {csv_field}: {str(e)}")
                                        continue
                                else:
                                    employee_data[model_field] = value
                        
                        # Procesar campos de vacaciones
                        if 'Date from' in row and row['Date from'].strip():
                            try:
                                date_from_str = row['Date from'].strip()
                                date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']
                                for date_format in date_formats:
                                    try:
                                        vacation_data['date_from'] = datetime.strptime(date_from_str, date_format).date()
                                        break
                                    except ValueError:
                                        continue
                                else:
                                    error_messages.append(f"Formato de fecha inválido para Date from: {date_from_str}")
                            except Exception as e:
                                error_messages.append(f"Error procesando Date from: {str(e)}")
                        
                        if 'Date to' in row and row['Date to'].strip():
                            try:
                                date_to_str = row['Date to'].strip()
                                date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']
                                for date_format in date_formats:
                                    try:
                                        vacation_data['date_to'] = datetime.strptime(date_to_str, date_format).date()
                                        break
                                    except ValueError:
                                        continue
                                else:
                                    error_messages.append(f"Formato de fecha inválido para Date to: {date_to_str}")
                            except Exception as e:
                                error_messages.append(f"Error procesando Date to: {str(e)}")
                        
                        # Crear o actualizar empleado
                        if 'name' in employee_data:
                            csv_employee_names.append(employee_data['name'])
                            
                            employee, created = Employee.objects.get_or_create(
                                name=employee_data['name'],
                                defaults=employee_data
                            )
                            
                            if created:
                                created_count += 1
                            else:
                                # Actualizar empleado existente
                                for field, value in employee_data.items():
                                    setattr(employee, field, value)
                                employee.save()
                                modified_count += 1
                            
                            # Crear o actualizar registro de vacaciones
                            if vacation_data:
                                if 'date_from' in vacation_data and 'date_to' in vacation_data:
                                    # Validar que date_from sea anterior o igual a date_to
                                    if vacation_data['date_from'] > vacation_data['date_to']:
                                        error_messages.append(f"Fecha inicio ({vacation_data['date_from']}) no puede ser posterior a fecha fin ({vacation_data['date_to']}) para {employee.name}")
                                    else:
                                        # Buscar si ya existe un registro de vacaciones para estas fechas exactas
                                        vacation, vacation_created = EmployeeVacation.objects.get_or_create(
                                            employee=employee,
                                            date_from=vacation_data['date_from'],
                                            date_to=vacation_data['date_to']
                                        )
                                        
                                        if vacation_created:
                                            vacation_created_count += 1
                                        else:
                                            vacation_updated_count += 1
                                else:
                                    # Si solo hay una fecha, crear un registro de un solo día
                                    if 'date_from' in vacation_data:
                                        vacation, vacation_created = EmployeeVacation.objects.get_or_create(
                                            employee=employee,
                                            date_from=vacation_data['date_from'],
                                            date_to=vacation_data['date_from']  # Mismo día
                                        )
                                        
                                        if vacation_created:
                                            vacation_created_count += 1
                                        else:
                                            vacation_updated_count += 1
                                    elif 'date_to' in vacation_data:
                                        vacation, vacation_created = EmployeeVacation.objects.get_or_create(
                                            employee=employee,
                                            date_from=vacation_data['date_to'],
                                            date_to=vacation_data['date_to']  # Mismo día
                                        )
                                        
                                        if vacation_created:
                                            vacation_created_count += 1
                                        else:
                                            vacation_updated_count += 1
                                
                                # Actualizar campos de vacaciones en el modelo Employee
                                if 'date_from' in vacation_data:
                                    employee.vacations_from = vacation_data['date_from']
                                if 'date_to' in vacation_data:
                                    employee.vacations_to = vacation_data['date_to']
                                
                                employee.save()
                        
                        else:
                            error_count += 1
                            error_messages.append("Falta el nombre del empleado en la fila")
                            
                    except Exception as e:
                        error_count += 1
                        error_messages.append(f"Error procesando fila: {str(e)}")
                
                # Eliminar empleados que no están en el CSV
                employees_to_delete = Employee.objects.exclude(name__in=csv_employee_names)
                deleted_employees = list(employees_to_delete.values_list('name', flat=True))
                deleted_count = employees_to_delete.count()
                
                if deleted_count > 0:
                    # Contar vacaciones que se eliminarán en cascada
                    vacation_deleted_count = EmployeeVacation.objects.filter(employee__in=employees_to_delete).count()
                    employees_to_delete.delete()  # Esto eliminará en cascada las vacaciones
                    print(f'Empleados eliminados: {", ".join(deleted_employees)}')
                
                # Mostrar resultados incluyendo vacaciones
                success_message = f"Importación completada: {created_count} empleados creados, {modified_count} empleados actualizados"
                
                if deleted_count > 0:
                    success_message += f", {deleted_count} empleados eliminados"
                
                # Añadir información sobre vacaciones
                if vacation_created_count > 0 or vacation_updated_count > 0 or vacation_deleted_count > 0:
                    vacation_message = []
                    if vacation_created_count > 0:
                        vacation_message.append(f"{vacation_created_count} vacaciones creadas")
                    if vacation_updated_count > 0:
                        vacation_message.append(f"{vacation_updated_count} vacaciones actualizadas")
                    if vacation_deleted_count > 0:
                        vacation_message.append(f"{vacation_deleted_count} vacaciones eliminadas")
                    
                    success_message += f" | Vacaciones: {', '.join(vacation_message)}"
                
                if error_count > 0:
                    success_message += f" | {error_count} errores encontrados"
                
                messages.success(request, success_message)
                
                # Mostrar errores específicos
                if error_messages:
                    for error in error_messages[:5]:  # Mostrar los primeros 5 errores
                        messages.warning(request, error)
                    if len(error_messages) > 5:
                        messages.warning(request, f"... y {len(error_messages) - 5} errores más")
                
                return redirect('employee_list')
                
            except Exception as e:
                messages.error(request, f'Error al procesar el archivo CSV: {str(e)}')
                return redirect('employee_list')
        
        else:
            # Si el formulario no es válido, mostrar errores
            messages.error(request, 'Error en el formulario. Por favor, verifica los datos.')
    
    # Esta línea ahora funcionará porque 'form' está definido
    return render(request, 'novacartografia_employee_management/import_employees_csv.html', {'form': form})

@login_required
@require_edit_permission
def import_projects_csv(request):
    # Create form instance outside the if/else blocks
    form = ProjectCSVImportForm()
    
    if request.method == 'POST':
        form = ProjectCSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            # Check if file is CSV
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'This is not a CSV file')
                return redirect('import_projects_csv')
            
            # Check file size
            if csv_file.size > 5242880:  # 5MB limit
                messages.error(request, 'CSV file is too large')
                return redirect('import_projects_csv')
                
            # Process CSV
            try:
                # Read CSV
                csv_data = csv_file.read().decode('utf-8')
                io_string = io.StringIO(csv_data)
                reader = csv.DictReader(io_string)
                
                # Verify columns
                imported_count = 0
                modified_count = 0
                deleted_count = 0
                
                # Lista para rastrear los proyectos que están en el CSV
                csv_project_names = []
                csv_project_ids = []
                
                for row in reader:
                    # Extract data from CSV row
                    name = row.get('Name', '')
                    if not name:  # Also try lowercase version
                        name = row.get('name', '')
                    
                    # Get project type
                    project_type = row.get('Type', '') or row.get('type', '') or 'Internal'
                    
                    # Get description
                    description = row.get('Description', '') or row.get('description', '')
                    
                    manager = row.get('Manager', '') or row.get('manager', '')
                    
                    # Skip empty rows
                    if not name:
                        continue
                    
                    # Añadir nombre a la lista de proyectos del CSV
                    csv_project_names.append(name)
                    
                    # Look for any unique identifier in the CSV
                    project_id = row.get('id', '') or row.get('ID', '') or row.get('project_id', '')
                    if project_id:
                        csv_project_ids.append(project_id)
                    
                    # Try to find existing project
                    existing_projects = None
                    if project_id:
                        # If we have an ID, try to find by ID first
                        try:
                            existing_projects = Project.objects.filter(id=project_id)
                        except ValueError:
                            pass
                        
                    if not existing_projects or not existing_projects.exists():
                        # If no match by ID, fall back to name
                        existing_projects = Project.objects.filter(name=name)
                    
                    if existing_projects.exists():
                        if existing_projects.count() == 1:
                            # Just one match, we can update it
                            existing_project = existing_projects.first()
                            updated = False
                            
                            # Check if fields need updating
                            if existing_project.type != project_type:
                                existing_project.type = project_type
                                updated = True
                                
                            if existing_project.description != description:
                                existing_project.description = description
                                updated = True
                            
                            if existing_project.manager != manager:
                                existing_project.manager = manager
                                updated = True
                                
                            if updated:
                                existing_project.save()
                                modified_count += 1
                                print(f'Updated project: {name}')
                            else:
                                print(f'Project already exists and is up to date: {name}')
                        else:
                            # Multiple matches - we'll skip this record
                            print(f'Multiple projects found with name "{name}" - skipping import')
                    else:
                        # Project doesn't exist, create new one
                        Project.objects.create(
                            name=name,
                            type=project_type,
                            description=description,
                            manager=manager
                        )
                        imported_count += 1
                        print(f'Created project: {name}')
                
                # Eliminar proyectos que no están en el CSV
                # Construir filtro para proyectos que NO están en el CSV
                if csv_project_ids:
                    # Si tenemos IDs en el CSV, filtrar por ID o por nombre
                    projects_to_delete = Project.objects.exclude(
                        Q(id__in=csv_project_ids) | Q(name__in=csv_project_names)
                    )
                else:
                    # Si no hay IDs, solo filtrar por nombre
                    projects_to_delete = Project.objects.exclude(name__in=csv_project_names)
                
                deleted_projects = list(projects_to_delete.values_list('name', flat=True))
                deleted_count = projects_to_delete.count()
                
                if deleted_count > 0:
                    projects_to_delete.delete()
                    print(f'Deleted projects: {", ".join(deleted_projects)}')
                
                messages.success(
                    request, 
                    f'Importación completada: {imported_count} proyectos importados, '
                    f'{modified_count} proyectos actualizados, {deleted_count} proyectos eliminados.'
                )
                return redirect('project_list')

            except Exception as e:
                messages.error(request, f'Error processing file: {e}')
    
    # For GET requests or if form is invalid, render the form
    return render(request, 'novacartografia_employee_management/import_projects_csv.html', {'form': form})


def export_employees_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="employees.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Name', 'Job', 'Project ID', 'Street', 'City', 'State', 'Academic Training', 'Driver License', 'Twenty Hours', 'Sixty Hours', 'Confine', 'Height', 'Mining', 'Railway Carriage', 'Railway Mounting', 'Building', 'Office Work', 'Scanner', 'Leveling', 'Static', 'Drag'])
    
    employees = Employee.objects.all()
    for employee in employees:
        writer.writerow([employee.name, employee.job, employee.project_id.name if employee.project_id else '', 
                        employee.street if employee.street else '',
                        employee.city if employee.city else '', 
                        employee.state if employee.state else '', 
                        employee.academic_training if employee.academic_training else '',
                        employee.driver_license if employee.driver_license else 'False',
                        employee.twenty_hours if employee.twenty_hours else 'False',
                        employee.sixty_hours if employee.sixty_hours else 'False',
                        employee.confine if employee.confine else 'False',
                        employee.height if employee.height else 'False',
                        employee.mining if employee.mining else 'False',
                        employee.railway_carriage if employee.railway_carriage else 'False',
                        employee.railway_mounting if employee.railway_mounting else 'False',
                        employee.building if employee.building else 'False',
                        employee.office_work if employee.office_work else 'False',
                        employee.scanner if employee.scanner else 'False',
                        employee.leveling if employee.leveling else 'False',
                        employee.static if employee.static else 'False',
                        employee.drag if employee.drag else 'False'])
    return response


@login_required
@require_edit_permission
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save()
            messages.success(request, f'Employee "{employee.name}" has been created successfully.')
            return redirect('employee_detail', pk=employee.id)
    else:
        form = EmployeeForm()
    
    return render(request, 'novacartografia_employee_management/employee_form.html', {
        'form': form,
        'title': 'Create Employee',
        'button_text': 'Create',
        'is_new': True
    })


@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    project_movements = employee.project_movements.all().order_by('-date')[:5]  # Get the last 5 movements
    context = {
        'employee': employee,
        'movements': project_movements,
    }
    return render(request, 'novacartografia_employee_management/employee_detail.html', context)


@login_required
@require_edit_permission
def employee_update(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, f'Employee "{employee.name}" has been updated successfully.')
            return redirect('kanban_board')
    else:
        form = EmployeeForm(instance=employee)
    
    return render(request, 'novacartografia_employee_management/employee_form.html', {
        'form': form,
        'employee': employee,
        'title': 'Update Employee',
        'button_text': 'Save Changes',
        'is_new': False
    })


@login_required
@require_edit_permission
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    
    if request.method == 'POST':
        employee_name = employee.name
        employee.delete()
        messages.success(request, f'Employee {employee_name} deleted successfully.')
        return redirect('employee_list')
    return render(request, 'novacartografia_employee_management/employee_confirm_delete.html', {'employee': employee})

@login_required
def lock_employee(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    
    if request.method == 'POST':
        employee.locked = True
        employee.save()
        messages.success(request, f'Employee {employee.name} has been locked successfully.')
        return redirect('kanban_board')


@login_required
def export_projects_csv(request):
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="projects.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['name', 'type', 'description'])
    
    projects = Project.objects.all()
    for project in projects:
        writer.writerow([project.name, project.type, project.description])
        
    return response

@login_required
def project_list(request):
    # Ordenamiento más sofisticado que coloca los proyectos sin manager al final
    projects = Project.objects.annotate(
        manager_order=Case(
            When(manager__isnull=True, then=Value('ZZZZZZ')),  # Un valor que será ordenado al final
            default='manager',
            output_field=CharField(),
        )
    )
    
    # Handle search
    search_query = request.GET.get('search')
    if search_query:
        projects = projects.filter(
            Q(name__icontains=search_query) |
            Q(manager__icontains=search_query) |
            Q(state__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(type__icontains=search_query)
        )
    
    # Apply ordering after filtering
    projects = projects.order_by('manager_order', 'name')
    
    return render(request, 'novacartografia_employee_management/project_list.html', {
        'projects': projects,
        'search_query': search_query
    })

@login_required
@require_edit_permission
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save()
            messages.success(request, f'Project "{project.name}" has been created successfully.')
            return redirect('project_list')
    else:
        form = ProjectForm()
    
    return render(request, 'novacartografia_employee_management/project_form.html', {
        'form': form,
        'title': 'Create Project',
        'button_text': 'Create Project',
        'is_new': True
    })



@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # Contar las habilidades requeridas por el proyecto
    required_skill_fields = [skill for skill in [
        'twenty_hours', 'sixty_hours', 'confine', 'height', 'mining',  # Verificamos que 'height' está aquí
        'railway_carriage', 'railway_mounting', 'building', 
        'office_work', 'scanner', 'leveling', 'static', 'drag'
    ] if getattr(project, skill, False)]
    
    # Añadir diagnóstico
    print(f"Required skills: {required_skill_fields}")
    print(f"Project height value: {project.height}")
    
    required_skills_count = len(required_skill_fields)
    
    # Si hay habilidades requeridas, buscar empleados que coincidan
    if required_skills_count > 0:
        # Obtener empleados que tienen al menos una habilidad coincidente
        # Usamos Q dinámicamente para cada habilidad requerida
        skill_filter = reduce(operator.or_, [Q(**{skill: True}) for skill in required_skill_fields])
        employees = Employee.objects.filter(skill_filter)
        
        # Ahora hacemos la consulta directa en Python para calcular coincidencias
        matching_employees = []
        
        for emp in employees:
            # Contar cuántas de las habilidades requeridas tiene este empleado
            matches = sum(1 for skill in required_skill_fields if getattr(emp, skill, False))
            
            # Añadir diagnóstico
            if 'height' in required_skill_fields:
                print(f"Employee {emp.name} height: {emp.height}, height matches: {'height' in required_skill_fields and emp.height}")
            
            percentage = (matches / required_skills_count) * 100
            
            # Añadir atributos calculados para usar en la plantilla
            emp.match_count = matches
            emp.required_count = required_skills_count
            emp.match_percentage = percentage
            emp.is_available = emp.project_id is None
            
            matching_employees.append(emp)
        
        # Ordenar la lista en Python
        matching_employees.sort(key=lambda e: (-e.match_percentage, e.name))
        
        # Limitar a 50 candidatos
        employees_with_matching_skills = matching_employees[:30]
    else:
        employees_with_matching_skills = []
    
    context = {
        'project': project,
        'employees_with_matching_skills': employees_with_matching_skills,
        'debug': True,  # Añadir para mostrar mensajes de debug en la template
    }
    
    return render(request, 'novacartografia_employee_management/project_detail.html', context)

@login_required
@require_edit_permission
def project_update(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, f'Project "{project.name}" has been updated successfully.')
            return redirect('project_detail', pk=project.id)
    else:
        form = ProjectForm(instance=project)
    
    return render(request, 'novacartografia_employee_management/project_form.html', {
        'form': form,
        'project': project,
        'title': 'Update Project',
        'button_text': 'Save Changes',
        'is_new': False
    })

@login_required
@require_edit_permission
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    if request.method == 'POST':
        project_name = project.name
        project.delete()
        messages.success(request, f'Employee {project_name} deleted successfully.')
        return redirect('employee_list')
    return render(request, 'novacartografia_employee_management/project_confirm_delete.html', {'employee': project})

@login_required
def movement_list(request):
    movements = ProjectMovementLine.objects.all().order_by('-date')
    return render(request, 'novacartografia_employee_management/movement_list.html', {
        'movements': movements
    })

@login_required
def kanban_board(request):
    today = timezone.now().date()
    
    # Anotar proyectos con información sobre necesidades, fechas y manager
    projects = Project.objects.annotate(
        has_needs=Case(
            When(employeeneeded__fulfilled=False, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        ),
        earliest_start_date=Min('employeeneeded__start_date'),
        manager_order=Case(
            When(manager__isnull=True, then=Value('ZZZZZZ')),  # Un valor que será ordenado al final
            default='manager',
            output_field=CharField(),
        )
    ).distinct()
    
    # Handle search
    search_query = request.GET.get('search')
    if search_query:
        projects = projects.filter(
            Q(name__icontains=search_query) |
            Q(manager__icontains=search_query) |
            Q(state__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(type__icontains=search_query)
        )
    
    # Apply ordering after filtering
    projects = projects.order_by('-has_needs', 'earliest_start_date', 'manager_order')
    
    # **NUEVO: Ordenar empleados por vacaciones**
    employees = Employee.objects.annotate(
        # Crear categorías para el ordenamiento de vacaciones
        vacation_category=Case(
            # Vacaciones actuales (en curso)
            When(
                vacations_from__lte=today, 
                vacations_to__gte=today, 
                then=Value(1)
            ),
            # Vacaciones recientes (terminadas hace poco)
            When(
                vacations_to__lt=today, 
                vacations_to__gte=today - timedelta(days=30), 
                then=Value(2)
            ),
            # Vacaciones futuras
            When(
                vacations_from__gt=today, 
                then=Value(3)
            ),
            # Vacaciones muy antiguas o sin vacaciones
            default=Value(4),
            output_field=IntegerField(),
        )
    ).order_by(
        'vacation_category',           # Primero por categoría
        '-vacations_from',            # Luego por fecha de inicio descendente (más recientes primero)
        'name'                        # Finalmente por nombre para consistencia
    )
    
    needs = EmployeeNeeded.objects.filter(fulfilled=False)
    locks = GetEmployeeLocked.objects.filter(fulfilled=False)
    
    return render(request, 'novacartografia_employee_management/kanban_board.html', {
        'projects': projects,
        'employees': employees,
        'needs': needs,
        'locks': locks,
        'search_query': search_query,
    })

@login_required
def update_employee_project(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method allowed'})
    
    try:
        data = json.loads(request.body)
        employee_id = data.get('employee_id')
        project_id = data.get('project_id')
        
        if not employee_id:
            return JsonResponse({'success': False, 'error': 'Employee ID is required'})
        
        employee = get_object_or_404(Employee, id=employee_id)
        
        if project_id:
            project = get_object_or_404(Project, id=project_id)
            employee.project_id = project
        else:
            employee.project_id = None
        
        # Al guardar el empleado, el signal track_project_change se activará automáticamente
        # y creará el registro de movimiento si es necesario
        employee.save()
        
        return JsonResponse({'success': True})
        
    except Employee.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Employee not found'})
    except Project.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Project not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def employee_needed_list(request):
    employee_needed = EmployeeNeeded.objects.all()
    return render(request, 'novacartografia_employee_management/employee_needed_list.html', {'employee_needed': employee_needed})

@login_required
@require_edit_permission
def employee_needed_create(request):
    # Verificar si se proporcionó un project_id en la URL
    project_id = request.GET.get('project_id')
    project = None
    initial_data = {}
    
    if project_id:
        try:
            project = Project.objects.get(pk=project_id)
            initial_data = {'project_id': project}
        except Project.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = EmployeeNeededForm(request.POST)
        if form.is_valid():
            employee_needed = form.save()
            messages.success(request, f'Request for {employee_needed.quantity} {employee_needed.type} created successfully.')
            # Cambiar esta línea para redirigir a kanban_board en lugar de employee_needed_list
            return redirect('kanban_board')
    else:
        form = EmployeeNeededForm(initial=initial_data)
    
    title = 'Create Employee Request'
    if project:
        title = f'Create Employee Request for {project.name}'
    
    return render(request, 'novacartografia_employee_management/employee_needed_form.html', {
        'form': form,
        'title': title,
        'button_text': 'Create Request',
        'is_new': True,
        'project': project
    })

@login_required
@require_edit_permission
def employee_needed_update(request, pk):
    employee_needed = get_object_or_404(EmployeeNeeded, pk=pk)
    
    if request.method == 'POST':
        form = EmployeeNeededForm(request.POST, instance=employee_needed)
        if form.is_valid():
            form.save()
            messages.success(request, f'Employee request updated successfully.')
            # Asegurar que también redirija a kanban_board
            return redirect('kanban_board')
    else:
        form = EmployeeNeededForm(instance=employee_needed)
    
    return render(request, 'novacartografia_employee_management/employee_needed_form.html', {
        'form': form,
        'employee_needed': employee_needed,
        'title': 'Update Employee Request',
        'button_text': 'Save Changes',
        'is_new': False,
        'project': employee_needed.project_id  # Pasar el proyecto para consistencia
    })
    
@login_required
@require_edit_permission
def employee_needed_delete(request, pk):
    employee_needed = get_object_or_404(EmployeeNeeded, pk=pk)
    
    if request.method == 'POST':
        employee_needed_name = employee_needed
        employee_needed.delete()
        messages.success(request, f'Employee needed {employee_needed_name} deleted successfully.')
        return redirect('kanban_board')
    return render(request, 'novacartografia_employee_management/employee_needed_confirm_delete.html', {'employee_needed': employee_needed})

@login_required
def employee_needed_fulfill(request, pk):
    employee_needed = get_object_or_404(EmployeeNeeded, pk=pk)
    
    if request.method == 'POST':
        employee_needed.fulfilled = True
        employee_needed.save()
        messages.success(request, f'Employee needed "{employee_needed}" has been fulfilled successfully.')
        return redirect('kanban_board')
    
    return render(request, 'novacartografia_employee_management/employee_needed_confirm_fulfill.html', {'employee_needed': employee_needed})

@login_required
@require_edit_permission
def employee_needed_create_from_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    
    if request.method == 'POST':
        form = EmployeeNeededForm(request.POST)
        if form.is_valid():
            employee_needed = form.save()
            messages.success(request, f'Request for {employee_needed.quantity} {employee_needed.type} created successfully.')
            return redirect('kanban_board')
    else:
        # Inicializar el formulario con el proyecto preseleccionado
        form = EmployeeNeededForm(initial={'project_id': project})
    
    return render(request, 'novacartografia_employee_management/employee_needed_form.html', {
        'form': form,
        'title': f'Create Employee Request for {project.name}',
        'button_text': 'Create Request',
        'is_new': True,
        'project': project
    })

@login_required
def home_redirect(request):
    return redirect('kanban_board')

urlpatterns = [
    # Otras URLs...
    path("", home_redirect, name='home'),
    # Resto de URLs...
]

@login_required
@require_edit_permission
def assign_employee_to_project(request, employee_id, project_id):
    if request.method == 'POST':
        employee = get_object_or_404(Employee, pk=employee_id)
        project = get_object_or_404(Project, pk=project_id)
        
        # Guardar proyecto anterior para el mensaje
        old_project = employee.project_id
        
        # Asignar el empleado al proyecto
        employee.project_id = project
        employee.save()
        
        # Crear mensaje apropiado
        if old_project:
            messages.success(
                request, 
                f'{employee.name} has been reassigned from {old_project.name} to {project.name}.'
            )
        else:
            messages.success(
                request, 
                f'{employee.name} has been assigned to {project.name}.'
            )
        
        return redirect('project_detail', pk=project_id)
    
    # Si no es POST, redirigir a la página de detalle del proyecto
    return redirect('project_detail', pk=project_id)


@login_required
@require_edit_permission
def unassign_employee_from_project(request, employee_id):
    if request.method == 'POST':
        employee = get_object_or_404(Employee, pk=employee_id)
        
        # Guardar proyecto anterior para el mensaje
        old_project = employee.project_id
        
        # Desasignar el empleado del proyecto
        employee.project_id = None
        employee.save()
        
        # Crear mensaje apropiado
        messages.success(
            request, 
            f'{employee.name} has been unassigned from {old_project.name}.'
        )
        
        return redirect('project_detail', pk=old_project.id)
    
    # Si no es POST, redirigir a la página de detalle del empleado
    return redirect('employee_detail', pk=employee_id)

@login_required
@require_edit_permission
def get_employee_locked_create(request, project_id=None):
    # Si se proporciona un ID de proyecto, pre-seleccionamos ese proyecto
    initial_data = {}
    
    if project_id:
        try:
            project = Project.objects.get(pk=project_id)
            initial_data = {'next_project': project}
        except Project.DoesNotExist:
            # Si el proyecto no existe, simplemente no lo preseleccionamos
            messages.warning(request, f'Project with ID {project_id} not found. Please select a project.')
    
    if request.method == 'POST':
        form = GetEmployeeLockedForm(request.POST)
        if form.is_valid():
            future_assignment = form.save()
            messages.success(request, f'Future assignment created for {future_assignment.employee.name}. The employee is now locked.')
            return redirect('project_detail', pk=future_assignment.next_project.id)
    else:
        form = GetEmployeeLockedForm(initial=initial_data)
    
    return render(request, 'novacartografia_employee_management/future_assignment_form.html', {
        'form': form,
        'title': 'Create Future Assignment',
    })

@login_required
@require_edit_permission
def get_employee_locked_update(request, pk):
    future_assignment = get_object_or_404(GetEmployeeLocked, pk=pk)
    
    if request.method == 'POST':
        form = GetEmployeeLockedForm(request.POST, instance=future_assignment)
        if form.is_valid():
            updated_assignment = form.save()
            messages.success(request, f'Future assignment updated for {updated_assignment.employee.name}.')
            return redirect('employee_detail', pk=updated_assignment.employee.id)
    else:
        form = GetEmployeeLockedForm(instance=future_assignment)
    
    return render(request, 'novacartografia_employee_management/future_assignment_form.html', {
        'form': form,
        'title': 'Update Future Assignment',
    })

@login_required
def get_employee_locked_fulfill(request, pk):
    future_assignment = get_object_or_404(GetEmployeeLocked, pk=pk)
    
    if request.method == 'POST':
        future_assignment.fulfilled = True
        future_assignment.save()
        messages.success(
            request, 
            f'{future_assignment.employee.name} has been assigned to {future_assignment.next_project.name}.'
        )
        return redirect('project_detail', pk=future_assignment.next_project.id)
    
    return render(request, 'novacartografia_employee_management/future_assignment_fulfill.html', {
        'future_assignment': future_assignment,
    })

@login_required
def get_employee_locked_list(request):
    future_assignments = GetEmployeeLocked.objects.filter(fulfilled=False)
    
    return render(request, 'novacartografia_employee_management/future_assignment_list.html', {
        'future_assignments': future_assignments,
    })

