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
            'static', 'drag', 'locked', 'active', 'start_date', 'end_date'
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
            'name', 'job', 'project_id', 'state', 'academic_training',
            
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
        fields = ['name', 'type', 'description', 'manager', 'state', 'academic_training','twenty_hours', 'sixty_hours', 
                  'confine', 'height', 'mining', 'railway_carriage', 'railway_mounting', 'building', 
                  'office_work', 'scanner', 'leveling', 'static', 'drag']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50'}),
            'type': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50'}),
            'manager': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50'}),
            'state': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50'}),
            'academic_training': forms.TextInput(attrs={'placeholder': 'E.g. Engineering, Technical degree...'}),
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
        fields = ['project_id', 'type', 'quantity', 'start_date']
        widgets = {
            'project_id': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50'}),
            'type': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50'}),
            'quantity': forms.NumberInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50'}),
        }
        labels = {
            'project_id': 'Project',
            'type': 'Position Type',
            'quantity': 'Number of Employees Needed',
            'start_date': 'Start Date'
        }
        help_texts = {
            'project_id': 'Select the project for which you need employees',
            'type': 'Select the type of position needed',
            'quantity': 'Enter the number of employees needed',
            'start_date': 'Select the date when you need these employees to start'
        }
        error_messages = {
            'project_id': {
                'required': "Please select a project.",
            },
            'type': {
                'required': "Please select a position type.",
            },
            'quantity': {
                'required': "Please enter the number of employees needed.",
            },
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
        self.fields['employee'].queryset = Employee.objects.filter(job__icontains='TOPÓGRAFO').exclude(locked=True)
        
        # Añadir clases de Tailwind a los campos
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50',
            })