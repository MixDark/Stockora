from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta

from inventory.models import StockItem, StockMovement
from products.models import Product, Category
from sales.models import SaleItem


@login_required
def analytics_home(request):
    today = timezone.now().date()
    last_30 = today - timedelta(days=30)
    last_90 = today - timedelta(days=90)

    # --- Top 10 productos más vendidos (últimos 90 días) ---
    top_products = (
        SaleItem.objects
        .filter(sale__created_at__date__gte=last_90)
        .values('product__name')
        .annotate(total_qty=Sum('quantity'), total_revenue=Sum(F('quantity') * F('unit_price')))
        .order_by('-total_qty')[:10]
    )

    # --- Stock por categoría ---
    category_stock = (
        StockItem.objects
        .values('product__category__name')
        .annotate(total_stock=Sum('quantity'))
        .filter(total_stock__gt=0)
        .order_by('-total_stock')[:8]
    )

    # --- Análisis ABC basado en valor de ventas acumuladas ---
    sales_data = list(
        SaleItem.objects
        .values('product__name')
        .annotate(
            total_qty=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('unit_price')),
        )
        .order_by('-total_revenue')
    )
    grand_total = sum(item['total_revenue'] or 0 for item in sales_data)
    cumulative = 0
    abc_analysis = []
    for item in sales_data:
        cumulative += float(item['total_revenue'] or 0)
        cumulative_pct = (cumulative / float(grand_total) * 100) if grand_total else 0
        if cumulative_pct <= 70:
            abc_class = 'A'
        elif cumulative_pct <= 90:
            abc_class = 'B'
        else:
            abc_class = 'C'
        abc_analysis.append({
            'product__name': item['product__name'],
            'total_qty': item['total_qty'],
            'total_revenue': item['total_revenue'],
            'cumulative_pct': round(cumulative_pct, 1),
            'abc_class': abc_class,
        })

    # --- Productos de lento movimiento (con stock pero sin salidas en 30 días) ---
    moved_ids = (
        StockMovement.objects
        .filter(created_at__date__gte=last_30, movement_type='out')
        .values_list('product_id', flat=True)
    )
    slow_moving_items = []
    for stock_item in (
        StockItem.objects
        .filter(quantity__gt=0)
        .exclude(product_id__in=moved_ids)
        .select_related('product')
        .order_by('-quantity')[:20]
    ):
        last_mv = (
            StockMovement.objects
            .filter(product=stock_item.product)
            .order_by('-created_at')
            .values_list('created_at', flat=True)
            .first()
        )
        slow_moving_items.append({
            'product': stock_item.product,
            'quantity': stock_item.quantity,
            'immobilized_value': stock_item.quantity * stock_item.product.cost_price,
            'last_movement': last_mv.date() if last_mv else None,
        })

    context = {
        'top_products': top_products,
        'category_stock': category_stock,
        'abc_analysis': abc_analysis,
        'slow_moving': slow_moving_items,
    }
    return render(request, 'analytics/home.html', context)

