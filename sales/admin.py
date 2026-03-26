from django.contrib import admin
from .models import Customer, Sale, SaleItem, Quotation, QuotationItem, Return, ReturnItem


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'is_active', 'created_at')
    search_fields = ('name', 'email', 'tax_id')
    list_filter = ('is_active',)


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'customer', 'warehouse', 'status', 'payment_method', 'total', 'created_at')
    list_filter = ('status', 'payment_method', 'warehouse')
    search_fields = ('invoice_number', 'customer__name')
    inlines = [SaleItemInline]
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')


class QuotationItemInline(admin.TabularInline):
    model = QuotationItem
    extra = 1


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ('quotation_number', 'customer', 'status', 'valid_until', 'created_at')
    list_filter = ('status',)
    search_fields = ('quotation_number', 'customer__name')
    inlines = [QuotationItemInline]


class ReturnItemInline(admin.TabularInline):
    model = ReturnItem
    extra = 1


@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ('id', 'sale', 'restock', 'created_at')
    list_filter = ('restock',)
    inlines = [ReturnItemInline]

