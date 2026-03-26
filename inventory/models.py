from django.db import models
from django.conf import settings
from products.models import Product, Batch, SerialNumber


class Warehouse(models.Model):
    """Almacén o bodega."""
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='warehouses'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Almacén'
        verbose_name_plural = 'Almacenes'

    def __str__(self):
        return f'{self.code} - {self.name}'


class Location(models.Model):
    """Ubicación física dentro del almacén (pasillo-estante-nivel)."""
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='locations')
    aisle = models.CharField(max_length=20, verbose_name='Pasillo')
    shelf = models.CharField(max_length=20, verbose_name='Estante')
    level = models.CharField(max_length=20, verbose_name='Nivel')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Ubicación'
        verbose_name_plural = 'Ubicaciones'
        unique_together = ('warehouse', 'aisle', 'shelf', 'level')

    def __str__(self):
        return f'{self.warehouse.code} - {self.aisle}-{self.shelf}-{self.level}'

    @property
    def code(self):
        return f'{self.aisle}-{self.shelf}-{self.level}'


class StockItem(models.Model):
    """Stock de un producto en un almacén/ubicación específica."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_items')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stock_items')
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_items')
    quantity = models.IntegerField(default=0)
    reserved_quantity = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Stock'
        verbose_name_plural = 'Stocks'
        unique_together = ('product', 'warehouse', 'location')

    def __str__(self):
        return f'{self.product.sku} @ {self.warehouse.code} - {self.quantity} uds.'

    @property
    def available_quantity(self):
        return self.quantity - self.reserved_quantity

    @property
    def is_low_stock(self):
        return self.quantity <= self.product.min_stock


class StockMovement(models.Model):
    """Movimiento de stock: entrada, salida o transferencia."""

    TYPE_IN = 'in'
    TYPE_OUT = 'out'
    TYPE_TRANSFER = 'transfer'
    TYPE_ADJUSTMENT = 'adjustment'
    TYPE_RETURN = 'return'
    TYPE_COUNT = 'count'

    TYPE_CHOICES = [
        (TYPE_IN, 'Entrada'),
        (TYPE_OUT, 'Salida'),
        (TYPE_TRANSFER, 'Transferencia'),
        (TYPE_ADJUSTMENT, 'Ajuste'),
        (TYPE_RETURN, 'Devolución'),
        (TYPE_COUNT, 'Conteo físico'),
    ]

    movement_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements')
    from_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='outgoing_movements'
    )
    to_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='incoming_movements'
    )
    from_location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='outgoing_movements'
    )
    to_location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='incoming_movements'
    )
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True)
    serial_number = models.ForeignKey(SerialNumber, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField()
    unit_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    location = models.CharField(max_length=100, blank=True, help_text='Ubicación física (pasillo-estante-nivel)')
    reference = models.CharField(max_length=200, blank=True, help_text='N° de orden, factura, etc.')
    notes = models.TextField(blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='movements'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Movimiento de stock'
        verbose_name_plural = 'Movimientos de stock'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_movement_type_display()} - {self.product.sku} x{self.quantity} ({self.created_at:%d/%m/%Y})'


class InventoryCount(models.Model):
    """Conteo físico de inventario."""

    STATUS_DRAFT = 'draft'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Borrador'),
        (STATUS_IN_PROGRESS, 'En progreso'),
        (STATUS_COMPLETED, 'Completado'),
    ]

    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='inventory_counts')
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='inventory_counts'
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Conteo de inventario'
        verbose_name_plural = 'Conteos de inventario'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} - {self.warehouse.name}'


class InventoryCountLine(models.Model):
    """Línea de un conteo físico."""
    count = models.ForeignKey(InventoryCount, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    system_quantity = models.IntegerField(default=0, help_text='Cantidad según el sistema')
    counted_quantity = models.IntegerField(null=True, blank=True, help_text='Cantidad contada físicamente')

    class Meta:
        verbose_name = 'Línea de conteo'
        verbose_name_plural = 'Líneas de conteo'

    def __str__(self):
        return f'{self.product.sku} - Conteo: {self.counted_quantity}'

    @property
    def difference(self):
        if self.counted_quantity is not None:
            return self.counted_quantity - self.system_quantity
        return None

