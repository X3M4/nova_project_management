from django import template

register = template.Library()

@register.filter
def count_unassigned(employees):
    """Cuenta los empleados sin proyecto asignado"""
    if not employees:
        return 0
    return sum(1 for employee in employees if not employee.project_id)