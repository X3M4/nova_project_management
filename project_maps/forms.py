from django import forms
from .models import ProjectLocation, BigProjectLocation

class ProjectLocationForm(forms.ModelForm):
    class Meta:
        model = ProjectLocation
        fields = ['latitude', 'longitude', 'address', 'city', 'province', 'country']
        widgets = {
            'latitude': forms.NumberInput(attrs={'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'step': '0.000001'}),
        }
        labels = {
            'description': 'Descripción',
            'latitude': 'Latitud',
            'longitude': 'Longitud',
            'address': 'Dirección',
            'city': 'Ciudad',
            'province': 'Provincia',
            'country': 'País',
        }
        
class BigProjectLocationForm(forms.ModelForm):
    class Meta:
        model = BigProjectLocation
        fields = ['name', 'amount', 'developer', 'start_date', 'latitude', 'longitude', 'address', 'city', 'province', 'country', 'description']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'latitude': forms.NumberInput(attrs={'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'step': '0.000001'}),
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
        }
        labels = {
            'name': 'Nombre del Proyecto',
            'amount': 'Monto',
            'developer': 'Desarrollador',
            'start_date': 'Fecha de Inicio',
            'latitude': 'Latitud',
            'longitude': 'Longitud',
            'address': 'Dirección',
            'city': 'Ciudad',
            'province': 'Provincia',
            'country': 'País',
            'description': 'Descripción',
        }