from django.contrib import admin
from .models import Category, Product, Batch, SerialNumber


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


class BatchInline(admin.TabularInline):
    model = Batch
    extra = 0


class SerialNumberInline(admin.TabularInline):
    model = SerialNumber
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'category', 'cost_price', 'sale_price', 'min_stock', 'is_active')
    list_filter = ('category', 'is_active', 'has_batches', 'has_serial_numbers')
    search_fields = ('sku', 'name', 'barcode')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [BatchInline, SerialNumberInline]


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ('batch_number', 'product', 'expiry_date', 'quantity', 'is_expired')
    list_filter = ('product',)
    search_fields = ('batch_number', 'product__name')


@admin.register(SerialNumber)
class SerialNumberAdmin(admin.ModelAdmin):
    list_display = ('serial', 'product', 'status', 'created_at')
    list_filter = ('status', 'product')
    search_fields = ('serial', 'product__name')

