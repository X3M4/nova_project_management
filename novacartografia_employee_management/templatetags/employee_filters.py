from django import template
from datetime import datetime

register = template.Library()

@register.filter
def div(value, divisor):
    """División de dos números"""
    try:
        return float(value) / float(divisor)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter  
def mul(value, multiplier):
    """Multiplicación de dos números"""
    try:
        return float(value) * float(multiplier)
    except ValueError:
        return 0

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

@register.filter
def count_unassigned(employees):
    """Cuenta los empleados sin proyecto asignado"""
    if not employees:
        return 0
    return sum(1 for employee in employees if not employee.project_id)

@register.filter
def get_unassigned(employees):
    """Obtiene empleados sin proyecto asignado"""
    if not employees:
        return []
    
    try:
        unassigned = []
        for employee in employees:
            if not hasattr(employee, 'project_id') or not employee.project_id:
                unassigned.append(employee)
        return unassigned
    except:
        return []

@register.filter
def count_assigned(employees):
    """Cuenta empleados con proyecto asignado"""
    if not employees:
        return 0
    
    try:
        count = 0
        for employee in employees:
            if hasattr(employee, 'project_id') and employee.project_id:
                count += 1
        return count
    except:
        return 0

@register.filter
def get_assigned(employees):
    """Obtiene empleados con proyecto asignado"""
    if not employees:
        return []
    
    try:
        assigned = []
        for employee in employees:
            if hasattr(employee, 'project_id') and employee.project_id:
                assigned.append(employee)
        return assigned
    except:
        return []

@register.filter
def get_project_employees(employees, project_id):
    """Obtiene empleados asignados a un proyecto específico"""
    if not employees:
        return []
    
    try:
        project_employees = []
        for employee in employees:
            if (hasattr(employee, 'project_id') and 
                employee.project_id and 
                employee.project_id.id == project_id):
                project_employees.append(employee)
        return project_employees
    except:
        return []

@register.filter
def count_project_employees(employees, project_id):
    """Cuenta empleados asignados a un proyecto específico"""
    if not employees:
        return 0
    
    try:
        count = 0
        for employee in employees:
            if (hasattr(employee, 'project_id') and 
                employee.project_id and 
                employee.project_id.id == project_id):
                count += 1
        return count
    except:
        return 0

@register.filter
def get_on_vacation(employees):
    """Obtiene empleados que están en vacaciones"""
    if not employees:
        return []
    
    from datetime import date
    today = date.today()
    
    try:
        on_vacation = []
        for employee in employees:
            # Verificar si el empleado tiene fechas de vacaciones y está actualmente en vacaciones
            if (hasattr(employee, 'vacations_from') and hasattr(employee, 'vacations_to') and 
                employee.vacations_from and employee.vacations_to and
                employee.vacations_from <= today <= employee.vacations_to):
                on_vacation.append(employee)
            # También verificar si tiene campos leave_from y leave_to (por compatibilidad)
            elif (hasattr(employee, 'leave_from') and hasattr(employee, 'leave_to') and 
                  employee.leave_from and employee.leave_to and
                  employee.leave_from <= today <= employee.leave_to):
                on_vacation.append(employee)
        return on_vacation
    except:
        return []

@register.filter
def count_on_vacation(employees):
    """Cuenta empleados que están en vacaciones"""
    return len(get_on_vacation(employees))

@register.filter
def get_locked_employees(employees):
    """Obtiene empleados bloqueados"""
    if not employees:
        return []
    
    try:
        locked = []
        for employee in employees:
            if hasattr(employee, 'locked') and employee.locked:
                locked.append(employee)
        return locked
    except:
        return []

@register.filter
def count_locked_employees(employees):
    """Cuenta empleados bloqueados"""
    return len(get_locked_employees(employees))

@register.filter
def has_skills_for_project(employee, project):
    """Verifica si un empleado tiene las habilidades requeridas para un proyecto"""
    if not employee or not project:
        return False
    
    try:
        # Lista de habilidades a verificar
        skills = ['twenty_hours', 'sixty_hours', 'confine', 'height', 'mining',
                 'railway_carriage', 'railway_mounting', 'building', 
                 'office_work', 'scanner', 'leveling', 'static', 'drag']
        
        # Contar habilidades coincidentes
        matches = 0
        required = 0
        
        for skill in skills:
            if hasattr(project, skill) and getattr(project, skill, False):
                required += 1
                if hasattr(employee, skill) and getattr(employee, skill, False):
                    matches += 1
        
        # Si el proyecto no requiere habilidades específicas, cualquier empleado sirve
        if required == 0:
            return True
            
        # Retorna True si tiene al menos 50% de las habilidades requeridas
        return (matches / required) >= 0.5
    except:
        return False

@register.filter
def skill_match_percentage(employee, project):
    """Calcula el porcentaje de coincidencia de habilidades"""
    if not employee or not project:
        return 0
    
    try:
        skills = ['twenty_hours', 'sixty_hours', 'confine', 'height', 'mining',
                 'railway_carriage', 'railway_mounting', 'building', 
                 'office_work', 'scanner', 'leveling', 'static', 'drag']
        
        matches = 0
        required = 0
        
        for skill in skills:
            if hasattr(project, skill) and getattr(project, skill, False):
                required += 1
                if hasattr(employee, skill) and getattr(employee, skill, False):
                    matches += 1
        
        if required == 0:
            return 100  # Si no hay requisitos, 100% compatible
            
        return round((matches / required) * 100, 1)
    except:
        return 0

@register.filter
def is_on_vacation_today(employee):
    """Verifica si un empleado está en vacaciones hoy"""
    if not employee:
        return False
    
    from datetime import date
    today = date.today()
    
    try:
        # Verificar vacaciones
        if (hasattr(employee, 'vacations_from') and hasattr(employee, 'vacations_to') and 
            employee.vacations_from and employee.vacations_to and
            employee.vacations_from <= today <= employee.vacations_to):
            return True
            
        # Verificar bajas médicas/permisos
        if (hasattr(employee, 'leave_from') and hasattr(employee, 'leave_to') and 
            employee.leave_from and employee.leave_to and
            employee.leave_from <= today <= employee.leave_to):
            return True
            
        return False
    except:
        return False

@register.filter
def vacation_status(employee):
    """Obtiene el estado de vacaciones de un empleado"""
    if not employee:
        return 'unknown'
    
    from datetime import date
    today = date.today()
    
    try:
        # Verificar vacaciones actuales
        if (hasattr(employee, 'vacations_from') and hasattr(employee, 'vacations_to') and 
            employee.vacations_from and employee.vacations_to):
            if employee.vacations_from <= today <= employee.vacations_to:
                return 'current'
            elif employee.vacations_from > today:
                return 'upcoming'
            elif employee.vacations_to < today:
                return 'past'
        
        # Verificar bajas médicas/permisos
        if (hasattr(employee, 'leave_from') and hasattr(employee, 'leave_to') and 
            employee.leave_from and employee.leave_to):
            if employee.leave_from <= today <= employee.leave_to:
                return 'on_leave'
            elif employee.leave_from > today:
                return 'leave_upcoming'
            elif employee.leave_to < today:
                return 'leave_past'
        
        return 'none'
    except:
        return 'unknown'
    
# Añadir esta función a tu archivo de filtros existente:

@register.filter
def get_employee_attr(skill_name, employee):
    """Obtiene el valor de un atributo del empleado por nombre"""
    return getattr(employee, skill_name, False)

@register.filter  
def replace(value, args):
    """Reemplaza texto en un string"""
    old, new = args.split(',') if ',' in args else (args, ' ')
    return value.replace(old, new)

@register.filter
def formato_habilidad(skill_name):
    """Convierte nombres de habilidades de código a texto legible en español"""
    traducciones = {
        'twenty_hours': '20 horas',
        'sixty_hours': '60 horas',
        'confine': 'Espacios confinados',
        'height': 'Trabajos en altura',
        'mining': 'Minería',
        'railway_carriage': 'Carruaje ferroviario',
        'railway_mounting': 'Montaje ferroviario',
        'building': 'Construcción',
        'office_work': 'Trabajo de oficina',
        'scanner': 'Escáner',
        'leveling': 'Nivelación',
        'static': 'Estático',
        'drag': 'Arrastre',
        'driver_license': 'Carnet de conducir'
    }
    return traducciones.get(skill_name, skill_name.replace('_', ' ').title())

@register.filter
def obtener_atributo_empleado(empleado, nombre_habilidad):
    """Obtiene el valor de un atributo del empleado por nombre"""
    return getattr(empleado, nombre_habilidad, False)