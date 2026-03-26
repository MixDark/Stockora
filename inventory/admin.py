from django.contrib import admin
from .models import Warehouse, Location, StockItem, StockMovement, InventoryCount, InventoryCountLine


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'manager', 'is_active')
    search_fields = ('code', 'name')


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('warehouse', 'aisle', 'shelf', 'level', 'is_active')
    list_filter = ('warehouse',)


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'warehouse', 'location', 'quantity', 'reserved_quantity', 'available_quantity')
    list_filter = ('warehouse',)
    search_fields = ('product__sku', 'product__name')


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'movement_type', 'product', 'quantity', 'from_warehouse', 'to_warehouse', 'reference')
    list_filter = ('movement_type', 'from_warehouse', 'to_warehouse')
    search_fields = ('product__sku', 'reference')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)


class InventoryCountLineInline(admin.TabularInline):
    model = InventoryCountLine
    extra = 0


@admin.register(InventoryCount)
class InventoryCountAdmin(admin.ModelAdmin):
    list_display = ('name', 'warehouse', 'status', 'created_at')
    list_filter = ('status', 'warehouse')
    inlines = [InventoryCountLineInline]

