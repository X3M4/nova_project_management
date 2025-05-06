from django import forms

from .models import Employee, Project, EmployeeNeeded

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
        fields = ['name', 'job', 'project_id', 'state']
        labels = {
            'name': 'Full Name',
            'job': 'Job Title',
            'project_id': 'Project',
            'state': 'State'
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter employee name'}),
            'job': forms.TextInput(attrs={'placeholder': 'Enter job title'}),
            'project': forms.Select(attrs={'placeholder': 'Select project'}),
            'state': forms.TextInput(attrs={'placeholder': 'Enter state'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        job = cleaned_data.get('job')
        state = cleaned_data.get('state')
        
        if not name or not job:
            raise forms.ValidationError("Name and job title are required.")
        
        return cleaned_data
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #Añade Tailwind clases a los fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-300 focus:ring focus:ring-primary-200 focus:ring-opacity-50',
                'placeholder': field.label,
            })

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'type', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50'}),
            'type': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-lime-500 focus:ring focus:ring-lime-500 focus:ring-opacity-50'}),
        }
        labels = {
            'name': 'Project Name',
            'type': 'Project Type',
            'description': 'Description'
        }
        help_texts = {
            'name': 'Enter a descriptive name for this project',
            'type': 'Select the type of project',
            'description': 'Optional: Add details about this project'
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