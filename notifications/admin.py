from django.contrib import admin
from .models import Notification, StockAlert


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'notification_type', 'title', 'is_read')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('title', 'user__username')
    date_hierarchy = 'created_at'


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'product', 'warehouse', 'current_quantity', 'threshold', 'status')
    list_filter = ('status', 'warehouse')
    search_fields = ('product__name', 'product__sku')
    date_hierarchy = 'created_at'

