from django.apps import AppConfig


class NovacartografiaEmployeeManagementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "novacartografia_employee_management"
    
    def ready(self):
        import novacartografia_employee_management.models
