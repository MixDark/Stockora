from django.db import models
from django.conf import settings
from products.models import Product
from inventory.models import Warehouse


class Customer(models.Model):
    """Cliente."""
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    tax_id = models.CharField(max_length=50, blank=True, verbose_name='NIT / RUC')
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['name']

    def __str__(self):
        return self.name


class Sale(models.Model):
    """Venta / factura."""

    STATUS_DRAFT = 'draft'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_RETURNED = 'returned'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Borrador'),
        (STATUS_COMPLETED, 'Completada'),
        (STATUS_CANCELLED, 'Cancelada'),
        (STATUS_RETURNED, 'Devuelta'),
    ]

    PAYMENT_CASH = 'cash'
    PAYMENT_CARD = 'card'
    PAYMENT_TRANSFER = 'transfer'
    PAYMENT_CREDIT = 'credit'

    PAYMENT_CHOICES = [
        (PAYMENT_CASH, 'Efectivo'),
        (PAYMENT_CARD, 'Tarjeta'),
        (PAYMENT_TRANSFER, 'Transferencia'),
        (PAYMENT_CREDIT, 'Crédito'),
    ]

    invoice_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, null=True, blank=True, related_name='sales')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='sales')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default=PAYMENT_CASH)
    discount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    sold_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sales'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-created_at']

    def __str__(self):
        return f'Venta #{self.invoice_number}'

    @property
    def subtotal(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def tax_total(self):
        return sum(item.tax_amount for item in self.items.all())

    @property
    def total(self):
        return self.subtotal + self.tax_total - self.discount


class SaleItem(models.Model):
    """Línea de una venta."""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=14, decimal_places=2)
    discount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Ítem de venta'
        verbose_name_plural = 'Ítems de venta'

    def __str__(self):
        return f'{self.product.name} x{self.quantity}'

    @property
    def subtotal(self):
        return (self.unit_price * self.quantity) - self.discount

    @property
    def tax_amount(self):
        return self.subtotal * (self.tax_rate / 100)


class Quotation(models.Model):
    """Cotización / presupuesto."""

    STATUS_DRAFT = 'draft'
    STATUS_SENT = 'sent'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_EXPIRED = 'expired'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Borrador'),
        (STATUS_SENT, 'Enviada'),
        (STATUS_ACCEPTED, 'Aceptada'),
        (STATUS_REJECTED, 'Rechazada'),
        (STATUS_EXPIRED, 'Vencida'),
    ]

    quotation_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='quotations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    valid_until = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='quotations'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cotización'
        verbose_name_plural = 'Cotizaciones'
        ordering = ['-created_at']

    def __str__(self):
        return f'COT-{self.quotation_number} - {self.customer.name}'

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())


class QuotationItem(models.Model):
    """Línea de una cotización."""
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=14, decimal_places=2)
    discount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    @property
    def subtotal(self):
        return (self.unit_price * self.quantity) - self.discount


class Return(models.Model):
    """Devolución de una venta."""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='returns')
    reason = models.TextField()
    restock = models.BooleanField(default=True, help_text='¿Reingresar al stock?')
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='returns'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Devolución'
        verbose_name_plural = 'Devoluciones'
        ordering = ['-created_at']

    def __str__(self):
        return f'DEV - Venta #{self.sale.invoice_number}'

    @property
    def total(self):
        """Suma de (precio original x cantidad devuelta) para cada ítem."""
        total = 0
        for item in self.items.all():
            sale_item = self.sale.items.filter(product=item.product).first()
            if sale_item:
                total += sale_item.unit_price * item.quantity
        return total


class ReturnItem(models.Model):
    """Línea de una devolución."""
    return_order = models.ForeignKey(Return, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    notes = models.TextField(blank=True)

    def __str__(self):
        return f'{self.product.name} x{self.quantity}'

