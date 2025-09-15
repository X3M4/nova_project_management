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