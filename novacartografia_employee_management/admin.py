from django.contrib import admin
from .models import Project, Employee, ProjectMovementLine, EmployeeNeeded

# Register your models here.
admin.site.register(Project)
admin.site.register(Employee)
admin.site.register(ProjectMovementLine)
admin.site.register(EmployeeNeeded)