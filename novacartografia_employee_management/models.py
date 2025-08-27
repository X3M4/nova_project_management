from django.db import models
from django.utils import timezone
from django.db.models.signals import pre_save
from django.dispatch import receiver

# Create your models here.
class Project(models.Model):
    PROJECT_TYPES = [
        ('external', 'Obra'),
        ('project', 'Proyecto'),
        # Otras opciones que necesites...
    ]
    
    MANAGER_TYPES = [
        ('Jose Cuesta Mejías', 'Cuesta'),
        ('Javier Marín Gimeno', 'Javi'),
        ('Guillermo Boscá Gómez', 'Guillermo'),
        ('Miguel Ángel Martínez García', 'Miguel Ángel'),
        ('Óscar López Valverde', 'Óscar'),
        # Otras opciones que necesites...
    ]
    
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50, choices=PROJECT_TYPES, default='proyecto')
    description = models.TextField(blank=True, null=True)
    manager = models.CharField(max_length=50, choices=MANAGER_TYPES, null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True, )
    date_from = models.DateField(blank=True, null=True)
    date_to = models.DateField(blank=True, null=True)
    
    academic_training = models.CharField(max_length=100, blank=True, null=True)
    twenty_hours = models.BooleanField(default=False)
    sixty_hours = models.BooleanField(default=False)
    confine = models.BooleanField(default=False)
    height = models.BooleanField(default=False)
    mining = models.BooleanField(default=False)
    railway_carriage = models.BooleanField(default=False)
    railway_mounting = models.BooleanField(default=False)
    building = models.BooleanField(default=False)
    office_work = models.BooleanField(default=False)
    scanner = models.BooleanField(default=False)
    leveling = models.BooleanField(default=False)
    static = models.BooleanField(default=False)
    drag = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
    
    
class Employee(models.Model):
    name = models.CharField(max_length=100)
    job = models.CharField(max_length=100)
    project_id = models.ForeignKey(Project, on_delete=models.SET_NULL, related_name='employee_set', blank=True, null=True)
    street = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    active = models.BooleanField(default=True, help_text="Indicates if the employee is currently active")
    start_date = models.DateField(default=timezone.now, help_text="When the employee started working", null=True, blank=True)
    end_date = models.DateField(blank=True, null=True, help_text="When the employee ended working, if applicable")
    state = models.CharField(max_length=50, default='valencia', 
           choices=[
                ('Araba (Álava)', 'Álava'),
                ('Albacete', 'Albacete'),
                ('Alacant (Alicante)', 'Alicante'),
                ('Almería', 'Almería'),
                ('Asturias', 'Asturias'),
                ('Ávila', 'Ávila'),
                ('Badajoz', 'Badajoz'),
                ('Barcelona', 'Barcelona'),
                ('Burgos', 'Burgos'),
                ('Cáceres', 'Cáceres'),
                ('Cádiz', 'Cádiz'),
                ('Cantabria', 'Cantabria'),
                ('Castelló (Castellón)', 'Castellón'),
                ('Ceuta', 'Ceuta'),
                ('Ciudad Real', 'Ciudad Real'),
                ('Córdoba', 'Córdoba'),
                ('Cuenca', 'Cuenca'),
                ('Gerona', 'Gerona'),
                ('Granada', 'Granada'),
                ('Guadalajara', 'Guadalajara'),
                ('Gipuzkoa (Guipúzcoa)', 'Guipúzcoa'),
                ('Huelva', 'Huelva'),
                ('Huesca', 'Huesca'),
                ('Islas Baleares', 'Islas Baleares'),
                ('Jaén', 'Jaén'),
                ('A Coruña (La Coruña)', 'La Coruña'),
                ('La Rioja', 'La Rioja'),
                ('Las Palmas', 'Las Palmas'),
                ('León', 'León'),
                ('Lérida', 'Lérida'),
                ('Lleida', 'Lérida'),  # Agregado porque aparece en tu CSV
                ('Lugo', 'Lugo'),
                ('Madrid', 'Madrid'),
                ('Málaga', 'Málaga'),
                ('Melilla', 'Melilla'),
                ('Murcia', 'Murcia'),
                ('Navarra (Nafarroa)', 'Navarra'),  # Corregido para coincidir con el CSV
                ('Orense', 'Orense'),
                ('Palencia', 'Palencia'),
                ('Pontevedra', 'Pontevedra'),
                ('Salamanca', 'Salamanca'),
                ('Santa Cruz de Tenerife', 'Santa Cruz de Tenerife'),
                ('Segovia', 'Segovia'),
                ('Sevilla', 'Sevilla'),
                ('Soria', 'Soria'),
                ('Tarragona', 'Tarragona'),
                ('Teruel', 'Teruel'),
                ('Toledo', 'Toledo'),
                ('Valencia', 'Valencia'),
                ('Valladolid', 'Valladolid'),
                ('Bizkaia (Vizcaya)', 'Vizcaya'),
                ('Zamora', 'Zamora'),
                ('Zaragoza', 'Zaragoza'),
            ])
    
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    academic_training = models.CharField(max_length=100, blank=True, null=True)
    driver_license = models.BooleanField(default=False)
    twenty_hours = models.BooleanField(default=False)
    sixty_hours = models.BooleanField(default=False)
    confine = models.BooleanField(default=False)
    height = models.BooleanField(default=False)
    mining = models.BooleanField(default=False)
    railway_carriage = models.BooleanField(default=False)
    railway_mounting = models.BooleanField(default=False)
    building = models.BooleanField(default=False)
    office_work = models.BooleanField(default=False)
    scanner = models.BooleanField(default=False)
    leveling = models.BooleanField(default=False)
    static = models.BooleanField(default=False)
    drag = models.BooleanField(default=False)
    
    locked = models.BooleanField(default=False, help_text="Indicates if the employee is locked for a future project")
    
    def __str__(self):
        return f"{self.name} - {self.state}"
    
    
    
class EmployeeNeeded(models.Model):
    POSITION_TYPES = [
        ('topo', 'Topo'),
        ('auxiliar', 'Auxiliar'),
        ('piloto', 'Piloto'),
    ]
    
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE)
    type = models.CharField(max_length=50, choices=POSITION_TYPES, default='topo')
    quantity = models.PositiveIntegerField()
    start_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    fulfilled = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.project_id.name} - {self.type} ({self.quantity})"
    


class ProjectMovementLine(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='movements')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='project_movements')
    date = models.DateTimeField(default=timezone.now)
    previous_project = models.ForeignKey(
        Project, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='outgoing_movements'
    )
    
    class Meta:
        ordering = ['-date']  # Most recent movements first
    
    def __str__(self):
        prev_project = self.previous_project.name if self.previous_project else "None"
        return f"{self.employee.name}: {prev_project} → {self.project.name} ({self.date.strftime('%Y-%m-%d %H:%M')})"
    
    @classmethod
    def log_movement(cls, employee, new_project, previous_project=None):
        """Create a movement record when an employee changes projects"""
        return cls.objects.create(
            employee=employee,
            project=new_project,
            previous_project=previous_project
        )


@receiver(pre_save, sender='novacartografia_employee_management.Employee')
def track_project_change(sender, instance, **kwargs):
    """Signal to track when an employee's project changes"""
    # Skip for new employees (no project change)
    if not instance.pk:
        return
        
    try:
        # Get the employee's previous state
        old_instance = sender.objects.get(pk=instance.pk)
        
        # If project has changed, log the movement
        if old_instance.project_id != instance.project_id and instance.project_id is not None:
            ProjectMovementLine.log_movement(
                employee=instance,
                new_project=instance.project_id,
                previous_project=old_instance.project_id
            )
    except sender.DoesNotExist:
        # Employee is new, no previous project
        pass

class GetEmployeeLocked(models.Model):
    """
    Model to represent an employee that is locked for a future project assignment
    """
    next_project = models.ForeignKey(Project, on_delete=models.CASCADE, 
                                    related_name='future_employee_assignments',
                                    help_text="The project the employee will be assigned to")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE,  # Cambiado de ManyToManyField a ForeignKey
                               related_name='future_assignment',
                               null=True,  # Añadido para la migración
                               blank=True,  # Añadido para la migración
                               help_text="The employee to be assigned to the project")
    start_date = models.DateField(help_text="When the employee should start in the new project")
    end_date = models.DateField(help_text="When the employee should end in the new project", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    fulfilled = models.BooleanField(default=False, 
                                   help_text="When marked as fulfilled, the employee will be assigned to the new project")
    
    class Meta:
        verbose_name = "Future Employee Assignment"
        verbose_name_plural = "Future Employee Assignments"
    
    def save(self, *args, **kwargs):
        # Guarda primero para obtener un ID si es un objeto nuevo
        is_new = not self.pk
        super().save(*args, **kwargs)
        
        # Ahora podemos actualizar el empleado de manera segura
        if is_new and self.employee:  # Verificar que hay un empleado
            # Si es una nueva asignación, bloquear al empleado
            if not self.employee.locked:
                self.employee.locked = True
                self.employee.save()
        elif self.fulfilled and self.employee:  # Verificar que hay un empleado
            # Si estamos marcando como cumplido, asignar y desbloquear
            self.employee.project_id = self.next_project
            self.employee.locked = False
            self.employee.save()
    
    def __str__(self):
        try:
            employee_name = self.employee.name if self.employee else "No employee"
            project_name = self.next_project.name if self.next_project else "No project"
            return f"{employee_name} → {project_name} (Start: {self.start_date})"
        except Exception:
            return f"Future Assignment {self.pk}"