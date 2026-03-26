from django.db import models
from django.utils import timezone
from django.conf import settings


class Category(models.Model):
    """Categoría jerárquica de productos."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text='Clase de icono (ej: heroicons)')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """Producto del inventario."""

    UNIT_UNIT = 'unit'
    UNIT_KG = 'kg'
    UNIT_LT = 'lt'
    UNIT_MT = 'mt'
    UNIT_BOX = 'box'
    UNIT_PACK = 'pack'

    UNIT_CHOICES = [
        (UNIT_UNIT, 'Unidad'),
        (UNIT_KG, 'Kilogramo'),
        (UNIT_LT, 'Litro'),
        (UNIT_MT, 'Metro'),
        (UNIT_BOX, 'Caja'),
        (UNIT_PACK, 'Paquete'),
    ]

    VALUATION_FIFO = 'fifo'
    VALUATION_LIFO = 'lifo'
    VALUATION_AVG = 'avg'

    VALUATION_CHOICES = [
        (VALUATION_FIFO, 'FIFO - Primero en entrar, primero en salir'),
        (VALUATION_LIFO, 'LIFO - Último en entrar, primero en salir'),
        (VALUATION_AVG, 'Costo promedio ponderado'),
    ]

    # Identificación
    sku = models.CharField(max_length=100, unique=True)
    barcode = models.CharField(max_length=100, blank=True, db_index=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    # Precios
    cost_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text='% IVA')

    # Stock
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default=UNIT_UNIT)
    min_stock = models.PositiveIntegerField(default=10)
    max_stock = models.PositiveIntegerField(default=1000)
    reorder_point = models.PositiveIntegerField(default=20)
    reorder_quantity = models.PositiveIntegerField(default=50)

    # Control
    has_batches = models.BooleanField(default=False, help_text='¿Maneja lotes y fechas de vencimiento?')
    has_serial_numbers = models.BooleanField(default=False, help_text='¿Maneja números de serie?')
    valuation_method = models.CharField(max_length=10, choices=VALUATION_CHOICES, default=VALUATION_AVG)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['name']

    def __str__(self):
        return f'[{self.sku}] {self.name}'

    @property
    def profit_margin(self):
        if self.cost_price > 0:
            return ((self.sale_price - self.cost_price) / self.cost_price) * 100
        return 0


class Batch(models.Model):
    """Lote de un producto con fecha de vencimiento."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=100)
    manufacture_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    quantity = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Lote'
        verbose_name_plural = 'Lotes'
        ordering = ['expiry_date']

    def __str__(self):
        return f'Lote {self.batch_number} - {self.product.name}'

    @property
    def is_expired(self):
        return self.expiry_date and self.expiry_date < timezone.now().date()

    @property
    def days_to_expiry(self):
        if self.expiry_date:
            return (self.expiry_date - timezone.now().date()).days
        return None


class SerialNumber(models.Model):
    """Número de serie para trazabilidad individual."""

    STATUS_AVAILABLE = 'available'
    STATUS_SOLD = 'sold'
    STATUS_RESERVED = 'reserved'
    STATUS_DAMAGED = 'damaged'

    STATUS_CHOICES = [
        (STATUS_AVAILABLE, 'Disponible'),
        (STATUS_SOLD, 'Vendido'),
        (STATUS_RESERVED, 'Reservado'),
        (STATUS_DAMAGED, 'Dañado'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='serial_numbers')
    serial = models.CharField(max_length=200, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_AVAILABLE)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Número de serie'
        verbose_name_plural = 'Números de serie'

    def __str__(self):
        return f'{self.serial} - {self.product.name}'

