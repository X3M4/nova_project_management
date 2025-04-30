import csv
from django.utils import timezone
import io
import json
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import EmployeeCSVImportForm, EmployeeForm, ProjectCSVImportForm, ProjectForm
from .models import Employee, Project, ProjectMovementLine
from django.http import HttpResponse, JsonResponse

@login_required
def employee_list(request):
    employees = Employee.objects.all()
    return render(request, 'novacartografia_employee_management/employee_list.html', {'employees': employees})

# Create your views here.
@login_required
def import_employees_csv(request):
    # Create form instance outside the if/else blocks
    form = EmployeeCSVImportForm()
    
    if request.method == 'POST':
        form = EmployeeCSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            # Check if file is CSV
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'This is not a CSV file')
                return redirect('import_employees_csv')
            
            # Check file size
            if csv_file.size > 5242880:  # 5MB limit
                messages.error(request, 'CSV file is too large')
                return redirect('import_employees_csv')
                
            # Process CSV
            try:
                # Read CSV
                csv_data = csv_file.read().decode('utf-8')
                io_string = io.StringIO(csv_data)
                reader = csv.DictReader(io_string)
                
                # Verify columns
                imported_count = 0
                modified_count = 0
                
                for row in reader:
                    # Get project if exists
                    project = None
                    if 'project_id' in row and row['project_id']:
                        try:
                            project = Project.objects.get(id=row['project_id'])
                        except Project.DoesNotExist:
                            pass
                    
                    # Check if the name field exists in the CSV row
                    name = row.get('Name', '')
                    if not name:  # Also try lowercase version
                        name = row.get('name', '')
                    
                    # Check if the job field exists in the CSV row
                    job = row.get('Job', '')
                    if not job:  # Also try lowercase version
                        job = row.get('job', '')
                    
                    # Skip empty rows
                    if not name:
                        continue
                    
                    # Look for any unique identifier in the CSV
                    employee_id = row.get('id', '') or row.get('ID', '') or row.get('employee_id', '')
                    
                    # Try to find an existing employee
                    if employee_id:
                        # If we have an ID, try to find by ID first
                        existing_employees = Employee.objects.filter(id=employee_id)
                        if not existing_employees.exists():
                            # If no match by ID, fall back to name
                            existing_employees = Employee.objects.filter(name=name)
                    else:
                        # Otherwise just search by name
                        existing_employees = Employee.objects.filter(name=name)
                    
                    if existing_employees.exists():
                        # Employee(s) exist with this name
                        if existing_employees.count() == 1:
                            # Just one match, we can update it
                            existing_employee = existing_employees.first()
                            
                            # Check if job or project has changed
                            if existing_employee.job != job or existing_employee.project_id != project:
                                # Update the employee
                                existing_employee.job = job
                                existing_employee.project_id = project
                                existing_employee.save()
                                modified_count += 1
                                print(f'Updated employee: {name}')
                            else:
                                # No changes needed
                                print(f'Employee already exists and is up to date: {name}')
                        else:
                            # Multiple matches - we need to handle this carefully
                            # Option 1: Skip this record and log it
                            print(f'Multiple employees found with name "{name}" - skipping import')
                            # Option 2: Create a new employee with a slightly different name
                            # new_name = f"{name} (Imported {timezone.now().strftime('%Y-%m-%d %H:%M')})"
                            # Employee.objects.create(name=new_name, job=job, project_id=project)
                            # imported_count += 1
                            # print(f'Created employee with modified name: {new_name}')
                    else:
                        # Employee doesn't exist, create a new one
                        Employee.objects.create(
                            name=name,
                            job=job,
                            project_id=project,
                        )
                        imported_count += 1
                        print(f'Created employee: {name}')

                messages.success(request, f'Successfully imported {imported_count} employees and updated {modified_count} existing employees.')
                return redirect('employee_list')

            except Exception as e:
                messages.error(request, f'Error processing file: {e}')
    
    # For GET requests or if form is invalid, render the form
    return render(request, 'novacartografia_employee_management/import_employees_csv.html', {'form': form})

@login_required
def import_projects_csv(request):
    # Create form instance outside the if/else blocks
    form = ProjectCSVImportForm()  # You'll need to create this form
    
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
                
                for row in reader:
                    # Extract data from CSV row
                    # Check if the name field exists in the CSV row
                    name = row.get('Name', '')
                    if not name:  # Also try lowercase version
                        name = row.get('name', '')
                    
                    # Get project type
                    project_type = row.get('Type', '') or row.get('type', '') or 'Internal'
                    
                    # Get description
                    description = row.get('Description', '') or row.get('description', '')
                    
                    # Skip empty rows
                    if not name:
                        continue
                    
                    # Look for any unique identifier in the CSV
                    project_id = row.get('id', '') or row.get('ID', '') or row.get('project_id', '')
                    
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
                            description=description
                        )
                        imported_count += 1
                        print(f'Created project: {name}')
                
                messages.success(request, f'Successfully imported {imported_count} projects and updated {modified_count} existing projects.')
                return redirect('project_list')

            except Exception as e:
                messages.error(request, f'Error processing file: {e}')
    
    # For GET requests or if form is invalid, render the form
    return render(request, 'novacartografia_employee_management/import_projects_csv.html', {'form': form})

def export_employees_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="employees.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Name', 'Job', 'Project ID'])
    
    employees = Employee.objects.all()
    for employee in employees:
        writer.writerow([employee.name, employee.job, employee.project_id.id if employee.project_id else ''])
    return response


@login_required
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
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    
    if request.method == 'POST':
        employee_name = employee.name
        employee.delete()
        messages.success(request, f'Employee {employee_name} deleted successfully.')
        return redirect('employee_list')
    return render(request, 'novacartografia_employee_management/employee_confirm_delete.html', {'employee': employee})


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
    projects = Project.objects.all()
    return render(request, 'novacartografia_employee_management/project_list.html', {'projects': projects})

@login_required
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
    
    context = {
        'project': project,
        # Los empleados asignados se obtienen en el template con project.employee_set.all
    }
    
    return render(request, 'novacartografia_employee_management/project_detail.html', context)

@login_required
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
    # Usar employee_set en lugar de employees
    projects = Project.objects.all().prefetch_related('employee_set')
    employees = Employee.objects.all()
    
    return render(request, 'novacartografia_employee_management/kanban_board.html', {
        'projects': projects,
        'employees': employees
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