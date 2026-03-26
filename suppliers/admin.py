from django.contrib import admin
from .models import Supplier, SupplierProduct, PurchaseOrder, PurchaseOrderItem


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_name', 'email', 'phone', 'is_active')
    search_fields = ('name', 'email', 'tax_id')
    list_filter = ('is_active',)


@admin.register(SupplierProduct)
class SupplierProductAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'product', 'cost_price', 'lead_time_days', 'is_preferred')
    list_filter = ('is_preferred', 'supplier')
    search_fields = ('product__name', 'supplier__name')


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'supplier', 'status', 'expected_date', 'created_at')
    list_filter = ('status', 'supplier')
    search_fields = ('order_number', 'supplier__name')
    inlines = [PurchaseOrderItemInline]
    date_hierarchy = 'created_at'

