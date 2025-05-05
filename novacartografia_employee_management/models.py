from django.db import models
from django.utils import timezone
from django.db.models.signals import pre_save
from django.dispatch import receiver

# Create your models here.
class Project(models.Model):
    PROJECT_TYPES = [
        ('obra', 'Obra'),
        ('proyecto', 'Proyecto'),
        # Otras opciones que necesites...
    ]
    
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50, choices=PROJECT_TYPES, default='proyecto')
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
    
    
    
class Employee(models.Model):
    name = models.CharField(max_length=100)
    job = models.CharField(max_length=100)
    project_id = models.ForeignKey(Project, on_delete=models.SET_NULL, related_name='employee_set', blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    
    
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

