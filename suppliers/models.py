from django.db import models
from django.conf import settings
from products.models import Product


class Supplier(models.Model):
    """Proveedor de productos."""
    name = models.CharField(max_length=200)
    contact_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    tax_id = models.CharField(max_length=50, blank=True, verbose_name='NIT / RUC')
    website = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['name']

    def __str__(self):
        return self.name


class SupplierProduct(models.Model):
    """Relación entre proveedor y producto con precio de compra."""
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='supplier_products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='supplier_products')
    supplier_sku = models.CharField(max_length=100, blank=True)
    cost_price = models.DecimalField(max_digits=14, decimal_places=2)
    lead_time_days = models.PositiveIntegerField(default=0, help_text='Días de entrega')
    min_order_quantity = models.PositiveIntegerField(default=1)
    is_preferred = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Producto de proveedor'
        verbose_name_plural = 'Productos de proveedor'
        unique_together = ('supplier', 'product')

    def __str__(self):
        return f'{self.supplier.name} → {self.product.name}'


class PurchaseOrder(models.Model):
    """Orden de compra a un proveedor."""

    STATUS_DRAFT = 'draft'
    STATUS_SENT = 'sent'
    STATUS_PARTIAL = 'partial'
    STATUS_RECEIVED = 'received'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Borrador'),
        (STATUS_SENT, 'Enviada'),
        (STATUS_PARTIAL, 'Recepción parcial'),
        (STATUS_RECEIVED, 'Recibida'),
        (STATUS_CANCELLED, 'Cancelada'),
    ]

    order_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchase_orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    expected_date = models.DateField(null=True, blank=True)
    received_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_auto_generated = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='purchase_orders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Orden de compra'
        verbose_name_plural = 'Órdenes de compra'
        ordering = ['-created_at']

    def __str__(self):
        return f'OC-{self.order_number} - {self.supplier.name}'

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())


class PurchaseOrderItem(models.Model):
    """Línea de una orden de compra."""
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity_ordered = models.PositiveIntegerField()
    quantity_received = models.PositiveIntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=14, decimal_places=2)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Ítem de orden de compra'
        verbose_name_plural = 'Ítems de orden de compra'

    def __str__(self):
        return f'{self.product.name} x{self.quantity_ordered}'

    @property
    def subtotal(self):
        return self.quantity_ordered * self.unit_cost

    @property
    def pending_quantity(self):
        return self.quantity_ordered - self.quantity_received

