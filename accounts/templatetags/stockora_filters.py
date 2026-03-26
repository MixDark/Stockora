from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()


@register.filter
def peso(value):
    """
    Formatea un número como entero con separador de miles usando punto.
    Ejemplo: 65000.00 → 65.000
    """
    try:
        num = int(round(Decimal(str(value))))
        return '{:,}'.format(num).replace(',', '.')
    except (InvalidOperation, TypeError, ValueError):
        return value
