from django import forms

from .models import Employee, GetEmployeeLocked, Project, EmployeeNeeded

class EmployeeCSVImportForm(forms.Form):
    csv_file = forms.FileField(
        label="Select a CSV file",
        help_text="Upload a CSV file containing employee data. Max size: 5MB.",
    )

class ProjectCSVImportForm(forms.Form):
    csv_file = forms.FileField(
        label='Select a CSV file',
        help_text='Max. 5 megabytes - CSV format only with columns: name, type, description'
    )
    
class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'name', 'job', 'project_id', 'street', 'city', 'state', 'academic_training',
            'driver_license', 'twenty_hours', 'sixty_hours', 
            'confine', 'height' , 'mining', 'railway_carriage', 'railway_mounting', 
            'building', 'office_work', 'scanner', 'leveling', 
            'static', 'drag', 'locked', 'active', 'start_date', 'end_date', 'vacations_from', 'vacations_to',
            'leave_from', 'leave_to',
        ]
        
        
        labels = {
            'name': 'Full Name',
            'job': 'Job Title',
            'project_id': 'Project',
            'city': 'City',
            'street': 'Street',
            'active': 'Active',
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'state': 'Province',
            'academic_training': 'Academic Training',
            'driver_license': 'Driver License',
            'twenty_hours': '20h Training',
            'sixty_hours': '60h Training',
            'confine': 'Confined Spaces',
            'height': 'Height',
            'mining': 'Mining',
            'railway_carriage': 'Railway Carriage',
            'railway_mounting': 'Railway Mounting',
            'building': 'Building',
            'office_work': 'Office Work',
            'scanner': 'Scanner',
            'leveling': 'Leveling',
            'static': 'Static',
            'drag': 'Drag',
            'locked': 'Locked',
            'vacations_from': 'Vacation From',
            'vacations_to': 'Vacation To',
            'leave_from': 'Leave From',
            'leave_to': 'Leave To',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter employee name'}),
            'job': forms.TextInput(attrs={'placeholder': 'Enter job title'}),
            'project_id': forms.Select(attrs={'placeholder': 'Select project'}),
            'state': forms.Select(attrs={'placeholder': 'Select province'}),
            'academic_training': forms.TextInput(attrs={'placeholder': 'E.g. Engineering, Technical degree...'}),
            'driver_license': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'twenty_hours': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'sixty_hours': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'confine': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'height': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'mining': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'railway_carriage': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'railway_mounting': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'building': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'office_work': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'scanner': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'leveling': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'static': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'drag': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'locked': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-300 focus:ring focus:ring-primary-200 focus:ring-opacity-50'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-300 focus:ring focus:ring-primary-200 focus:ring-opacity-50'}),
            'street': forms.TextInput(attrs={'placeholder': 'Enter street address'}),
            'city': forms.TextInput(attrs={'placeholder': 'Enter city'}),
            'vacations_from': forms.DateInput(attrs={'type': 'date', 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-300 focus:ring focus:ring-primary-200 focus:ring-opacity-50'}),
            'vacations_to': forms.DateInput(attrs={'type': 'date', 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-300 focus:ring focus:ring-primary-200 focus:ring-opacity-50'}),
            'leave_from': forms.DateInput(attrs={'type': 'date', 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-300 focus:ring focus:ring-primary-200 focus:ring-opacity-50'}),
            'leave_to': forms.DateInput(attrs={'type': 'date', 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-300 focus:ring focus:ring-primary-200 focus:ring-opacity-50'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        job = cleaned_data.get('job')
        
        if not name or not job:
            raise forms.ValidationError("Name and job title are required.")
        
        return cleaned_data
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Añadir Tailwind classes a los campos de texto, select, etc.
        text_fields = ['name', 'job', 'project_id', 'state', 'academic_training']
        for field_name in text_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-300 focus:ring focus:ring-primary-200 focus:ring-opacity-50',
                    'placeholder': self.fields[field_name].label,
                })
        
        # Añadir clases específicas para campos booleanos (checkboxes)
        checkbox_fields = [
            'driver_license', 'twenty_hours', 'sixty_hours', 
            'confine', 'height', 'mining', 'railway_carriage', 'railway_mounting', 
            'building', 'office_work', 'scanner', 'leveling', 
            'static', 'drag'
        ]
        for field_name in checkbox_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    'class': 'h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500',
                })
        
        # Reorganizar el orden de los campos para agruparlos lógicamente
        field_order = [
            # Información personal
            'name', 'job', 'project_id', 'state', 'academic_training', 'vacations_from', 'vacations_to',
            'leave_from', 'leave_to',
            
            # Licencias y formaciones
            'driver_license', 'twenty_hours', 'sixty_hours', 
            
            # Habilidades específicas
            'confine', 'mining', 'railway_carriage', 'railway_mounting', 
            'building', 'office_work', 'scanner', 'leveling', 
            'static', 'drag'
        ]
        
        # Actualizar el orden de los campos
        self.order_fields(field_order)
        
        # Añadir ayuda contextual a los campos booleanos
        help_texts = {
            'driver_license': 'Has valid driver\'s license',
            'twenty_hours': 'Has completed 20h safety training',
            'sixty_hours': 'Has completed 60h advanced training',
            'confine': 'Certified for confined spaces work',
            'mining': 'Experience in mining environments',
            'railway_carriage': 'Qualified for railway carriage tasks',
            'railway_mounting': 'Certified for railway mounting operations',
            'building': 'Experience with building construction',
            'office_work': 'Can perform office administrative tasks',
            'scanner': 'Proficient with scanning equipment',
            'leveling': 'Experienced in terrain leveling',
            'static': 'Qualified for static measurements',
            'drag': 'Trained for drag operations'
        }
        
        # Aplicar los textos de ayuda
        for field, help_text in help_texts.items():
            if field in self.fields:
                self.fields[field].help_text = help_text

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'type', 'description', 'manager', 'state', 'date_from','date_to', 'academic_training','twenty_hours', 'sixty_hours', 
                  'confine', 'height', 'mining', 'railway_carriage', 'railway_mounting', 'building', 
                  'office_work', 'scanner', 'leveling', 'static', 'drag']
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50'}),
            'type': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50'}),
            'manager': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50'}),
            'state': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50'}),
            'date_from': forms.DateInput(attrs={'type': 'date', 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50'}),
            'date_to': forms.DateInput(attrs={'type': 'date', 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50'}),
            'academic_training': forms.TextInput(attrs={'placeholder': 'E.g. Engineering, Technical degree...', 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50'}),
            'twenty_hours': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'sixty_hours': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'confine': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'height': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'mining': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'railway_carriage': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'railway_mounting': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'building': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'office_work': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'scanner': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'leveling': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'static': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'drag': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
        }
        
        labels = {
            'name': 'Project Name',
            'type': 'Project Type',
            'description': 'Description',
            'manager': 'Project Manager',
            'state': 'Province',
            'date_from': 'Start Date',
            'date_to': 'End Date',
            'academic_training': 'Academic Training',
            'twenty_hours': '20h Training',
            'sixty_hours': '60h Training',
            'confine': 'Confined Spaces',
            'height': 'Height',
            'mining': 'Mining',
            'railway_carriage': 'Railway Carriage',
            'railway_mounting': 'Railway Mounting',
            'building': 'Building',
            'office_work': 'Office Work',
            'scanner': 'Scanner',
            'leveling': 'Leveling',
            'static': 'Static',
            'drag': 'Trace',
        }
        help_texts = {
            'name': 'Enter a descriptive name for this project',
            'type': 'Select the type of project',
            'description': 'Optional: Add details about this project',
            'manager': 'Select the manager responsible for this project',
            'state': 'Enter the province where the project is located',
            'date_from': 'Select the start date of the project',
            'date_to': 'Select the end date of the project',
            'academic_training': 'E.g. Engineering, Technical degree...',
            'twenty_hours': 'Has completed 20h safety training',
            'sixty_hours': 'Has completed 60h advanced training',
            'confine': 'Certified for confined spaces work',
            'height': 'Certified for working at heights',
            'mining': 'Experience in mining environments',
            'railway_carriage': 'Qualified for railway carriage tasks',
            'railway_mounting': 'Certified for railway mounting operations',
            'building': 'Experience with building construction',
            'office_work': 'Can perform office administrative tasks',
            'scanner': 'Proficient with scanning equipment',
            'leveling': 'Experienced in terrain leveling',
            'static': 'Qualified for static measurements',
            'drag': 'Trained for trace operations'
        }
        error_messages = {
            'name': {
                'max_length': "This name is too long.",
            },
            'type': {
                'required': "Please select a project type.",
            },
        }
    
    # El método clean debería estar aquí, fuera de la clase Meta
    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        type = cleaned_data.get('type')
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError("End date must be after start date.")
        
        if not name or not type:
            raise forms.ValidationError("Project name and type are required.")
        
        return cleaned_data
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Añade Tailwind clases a los fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50',
                'placeholder': field.label,
            })

class EmployeeNeededForm(forms.ModelForm):
    class Meta:
        model = EmployeeNeeded
        fields = ['project_id', 'type', 'quantity', 'start_date', 'description']
        widgets = {
            'project_id': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50'}),
            'type': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50'}),
            'quantity': forms.NumberInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50'}),
        }
        labels = {
            'project_id': 'Proyecto',
            'type': 'Tipo de Posición',
            'quantity': 'Número de Empleados Necesarios',
            'start_date': 'Fecha de Inicio',
            'description': 'Descripción',
        }
        help_texts = {
            'project_id': 'Selecciona el proyecto para el cual necesitas empleados',
            'type': 'Selecciona el tipo de posición necesaria',
            'quantity': 'Introduce el número de empleados necesarios',
            'start_date': 'Selecciona la fecha cuando necesitas que estos empleados comiencen',
            'description': 'Proporciona una descripción detallada de la solicitud de empleado',
        }
        
        # El método clean debería estar aquí, fuera de la clase Meta
    def clean(self):
        cleaned_data = super().clean()
        project_id = cleaned_data.get('project_id')
        type = cleaned_data.get('type')
        quantity = cleaned_data.get('quantity')
        
        if not project_id or not type or not quantity:
            raise forms.ValidationError("Project, position type, and quantity are required.")
        
        return cleaned_data
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Añade Tailwind clases a los fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50',
                'placeholder': field.label,
            })

class GetEmployeeLockedForm(forms.ModelForm):
    class Meta:
        model = GetEmployeeLocked
        fields = ['next_project', 'employee', 'start_date', 'end_date' ,'fulfilled']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'next_project': 'Future Project',
            'employee': 'Employee',
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'fulfilled': 'Mark as Fulfilled',
        }
        help_texts = {
            'next_project': 'Select the future project for this employee',
            'employee': 'Select the employee to lock for future assignment',
            'start_date': 'When should the employee start in the new project',
            'end_date': 'When should the employee end in the current project',
            'fulfilled': 'If checked, the employee will be immediately assigned to the new project',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar empleados para mostrar solo los que tienen "TOPÓGRAFO" en el campo job
        # self.fields['employee'].queryset = Employee.objects.filter(job__icontains='TOPÓGRAFO').exclude(locked=True)
        self.fields['employee'].queryset = Employee.objects.all()
        
        # Añadir clases de Tailwind a los campos
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50',
            })
            
from django import forms
from django.core.exceptions import ValidationError
from .models import EmployeeVacation, Employee

class EmployeeVacationForm(forms.ModelForm):
    class Meta:
        model = EmployeeVacation
        fields = ['employee', 'date_from', 'date_to']
        widgets = {
            'employee': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'date_from': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True,
            }),
            'date_to': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True,
            }),
        }
        labels = {
            'employee': 'Empleado',
            'date_from': 'Fecha de Inicio',
            'date_to': 'Fecha de Fin',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar solo empleados activos
        self.fields['employee'].queryset = Employee.objects.filter(
            active=True
        ).order_by('name')
        
        # Añadir placeholder y ayuda
        self.fields['employee'].empty_label = "Selecciona un empleado"
        self.fields['date_from'].help_text = "Fecha de inicio de las vacaciones"
        self.fields['date_to'].help_text = "Fecha de fin de las vacaciones"
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        employee = cleaned_data.get('employee')
        
        if date_from and date_to:
            # Validar que date_from sea anterior o igual a date_to
            if date_from > date_to:
                raise ValidationError(
                    'La fecha de inicio no puede ser posterior a la fecha de fin.'
                )
            
            # Validar que no haya solapamiento con otras vacaciones del mismo empleado
            if employee:
                overlapping_vacations = EmployeeVacation.objects.filter(
                    employee=employee,
                    date_from__lte=date_to,
                    date_to__gte=date_from
                )
                
                # Si estamos editando, excluir la vacación actual
                if self.instance and self.instance.pk:
                    overlapping_vacations = overlapping_vacations.exclude(pk=self.instance.pk)
                
                if overlapping_vacations.exists():
                    existing = overlapping_vacations.first()
                    raise ValidationError(
                        f'Las fechas se superponen con unas vacaciones existentes: '
                        f'{existing.date_from.strftime("%d/%m/%Y")} - {existing.date_to.strftime("%d/%m/%Y")}'
                    )
        
        return cleaned_data
    
    def clean_date_from(self):
        date_from = self.cleaned_data.get('date_from')
        
        if date_from:
            # Opcional: validar que no sea demasiado en el pasado
            from datetime import date, timedelta
            if date_from < date.today() - timedelta(days=365):
                raise ValidationError(
                    'La fecha de inicio no puede ser de hace más de un año.'
                )
        
        return date_from
    
    def clean_date_to(self):
        date_to = self.cleaned_data.get('date_to')
        
        if date_to:
            # Opcional: validar que no sea demasiado en el futuro
            from datetime import date, timedelta
            if date_to > date.today() + timedelta(days=365):
                raise ValidationError(
                    'La fecha de fin no puede ser de más de un año en el futuro.'
                )
        
        return date_to