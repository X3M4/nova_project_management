from django import forms

from .models import Employee

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
        fields = ['name', 'job', 'project_id']
        labels = {
            'name': 'Full Name',
            'job': 'Job Title',
            'project_id': 'Project',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter employee name'}),
            'job': forms.TextInput(attrs={'placeholder': 'Enter job title'}),
            'project': forms.Select(attrs={'placeholder': 'Select project'}),
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
        #Añade Tailwind clases a los fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-300 focus:ring focus:ring-primary-200 focus:ring-opacity-50',
                'placeholder': field.label,
            })

