"""Utilidad para registrar acciones en AuditLog sin repetir código."""
from accounts.models import AuditLog


def _get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_action(request, action, obj, changes=None):
    """Registra una acción en AuditLog.

    Args:
        request: HttpRequest actual (para obtener usuario e IP).
        action: una de AuditLog.ACTION_* (create, update, delete, etc.).
        obj: instancia del modelo afectado.
        changes: dict opcional con los cambios realizados.
    """
    AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        model_name=obj.__class__.__name__,
        object_id=str(obj.pk),
        object_repr=str(obj)[:200],
        changes=changes or {},
        ip_address=_get_client_ip(request),
    )
