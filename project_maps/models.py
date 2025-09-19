from django.db import models

# Create your models here.
from django.db import models
from novacartografia_employee_management.models import Project

class ProjectLocation(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='location')
    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    province = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default='España')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Location of {self.project.name}"
    
class BigProjectLocation(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nombre del Proyecto")
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name="Importe",
        help_text="Importe en euros"
    )
    developer = models.CharField(
        max_length=255, 
        verbose_name="Desarrollador/Constructor", 
        blank=True, 
        null=True
    )
    address = models.TextField(verbose_name="Dirección", blank=True, null=True)
    city = models.CharField(max_length=100, verbose_name="Ciudad", blank=True, null=True)
    province = models.CharField(max_length=100, verbose_name="Provincia", blank=True, null=True)
    country = models.CharField(
        max_length=100, 
        verbose_name="País", 
        default="España"
    )
    latitude = models.FloatField(verbose_name="Latitud")
    longitude = models.FloatField(verbose_name="Longitud")
    start_date = models.DateField(
        verbose_name="Fecha de Inicio", 
        blank=True, 
        null=True
    )
    description = models.TextField(
        verbose_name="Descripción", 
        blank=True, 
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado en")
    
    def __str__(self):
        """Representación string del proyecto"""
        if self.amount:
            return f"{self.name} - €{self.amount:,.0f}"
        return self.name
    
    def get_absolute_url(self):
        """URL para ver el detalle del proyecto"""
        from django.urls import reverse
        return reverse('big_project_detail', args=[str(self.id)])
    
    @property
    def location_display(self):
        """Mostrar ubicación completa"""
        parts = []
        if self.city:
            parts.append(self.city)
        if self.province:
            parts.append(self.province)
        if self.country and self.country != "España":
            parts.append(self.country)
        return ", ".join(parts) if parts else "Sin ubicación"
    
    @property
    def google_maps_url(self):
        """URL a Google Maps"""
        if self.latitude and self.longitude:
            return f"https://maps.google.com/?q={self.latitude},{self.longitude}"
        return None
    
    class Meta:
        verbose_name = "Gran Proyecto"
        verbose_name_plural = "Grandes Proyectos"
        ordering = ['-amount', 'name']
        db_table = 'project_maps_bigprojectlocation'