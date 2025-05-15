from django import forms
from .models import ProjectLocation

class ProjectLocationForm(forms.ModelForm):
    class Meta:
        model = ProjectLocation
        fields = ['latitude', 'longitude', 'address', 'city', 'province', 'country']
        widgets = {
            'latitude': forms.NumberInput(attrs={'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'step': '0.000001'}),
        }
        labels = {
            'latitude': 'Latitud',
            'longitude': 'Longitud',
            'address': 'Dirección',
            'city': 'Ciudad',
            'province': 'Provincia',
            'country': 'País',
        }