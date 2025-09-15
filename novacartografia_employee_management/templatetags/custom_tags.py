from django import template
from datetime import datetime

register = template.Library()

@register.filter
def count_unassigned(employees):
    """Cuenta los empleados sin proyecto asignado"""
    if not employees:
        return 0
    return sum(1 for employee in employees if not employee.project_id)


@register.filter
def date_diff(date1, date2):
    """Calcula la diferencia en días entre dos fechas"""
    if date1 and date2:
        try:
            if isinstance(date1, str):
                date1 = datetime.strptime(date1, '%Y-%m-%d').date()
            if isinstance(date2, str):
                date2 = datetime.strptime(date2, '%Y-%m-%d').date()
            
            diff = (date1 - date2).days + 1  # +1 para incluir ambos días
            return max(diff, 0)  # No devolver números negativos
        except:
            return 0
    return 0