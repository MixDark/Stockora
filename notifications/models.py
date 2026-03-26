from django.db import models
from django.conf import settings
from products.models import Product
from inventory.models import Warehouse


class Notification(models.Model):
    """Notificación del sistema para un usuario."""

    TYPE_INFO = 'info'
    TYPE_WARNING = 'warning'
    TYPE_DANGER = 'danger'
    TYPE_SUCCESS = 'success'

    TYPE_CHOICES = [
        (TYPE_INFO, 'Información'),
        (TYPE_WARNING, 'Advertencia'),
        (TYPE_DANGER, 'Peligro'),
        (TYPE_SUCCESS, 'Éxito'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications'
    )
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_INFO)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.notification_type}] {self.title} → {self.user.username}'


class StockAlert(models.Model):
    """Alerta de stock bajo para un producto en un almacén."""

    STATUS_ACTIVE = 'active'
    STATUS_ACKNOWLEDGED = 'acknowledged'
    STATUS_RESOLVED = 'resolved'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Activa'),
        (STATUS_ACKNOWLEDGED, 'Reconocida'),
        (STATUS_RESOLVED, 'Resuelta'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='alerts')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='alerts')
    current_quantity = models.IntegerField()
    threshold = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Alerta de stock'
        verbose_name_plural = 'Alertas de stock'
        ordering = ['-created_at']
        unique_together = ('product', 'warehouse', 'status')

    def __str__(self):
        return f'Alerta: {self.product.name} @ {self.warehouse.name} ({self.current_quantity} uds.)'

