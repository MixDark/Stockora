from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from accounts.audit import log_action
from accounts.decorators import manager_required
from .models import Supplier, PurchaseOrder, PurchaseOrderItem
from products.models import Product


@login_required
def supplier_list(request):
    query = request.GET.get('q', '')
    suppliers = Supplier.objects.filter(is_active=True).order_by('name')
    if query:
        suppliers = suppliers.filter(Q(name__icontains=query) | Q(email__icontains=query))
    paginator = Paginator(suppliers, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'suppliers/list.html', {'page': page, 'query': query})


@login_required
@manager_required
def supplier_create(request):
    """Crea un nuevo proveedor."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        contact_name = request.POST.get('contact_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        tax_id = request.POST.get('tax_id', '').strip()
        if not name:
            messages.error(request, 'El nombre es obligatorio.')
        elif Supplier.objects.filter(name__iexact=name).exists():
            messages.error(request, f'Ya existe un proveedor con el nombre "{name}".')
        else:
            supplier = Supplier.objects.create(
                name=name, contact_name=contact_name,
                email=email, phone=phone,
                address=address, tax_id=tax_id,
            )
            log_action(request, 'create', supplier)
            messages.success(request, f'Proveedor "{name}" creado exitosamente.')
            return redirect('suppliers:list')
    return redirect('suppliers:list')


@login_required
def supplier_detail(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    orders = supplier.purchase_orders.order_by('-created_at')[:10]
    return render(request, 'suppliers/detail.html', {'supplier': supplier, 'orders': orders})


@login_required
@manager_required
def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'El nombre es obligatorio.')
            return redirect('suppliers:list')
        supplier.name = name
        supplier.contact_name = request.POST.get('contact_name', '').strip()
        supplier.email = request.POST.get('email', '').strip()
        supplier.phone = request.POST.get('phone', '').strip()
        supplier.address = request.POST.get('address', '').strip()
        supplier.tax_id = request.POST.get('tax_id', '').strip()
        supplier.save()
        log_action(request, 'update', supplier)
        messages.success(request, f'Proveedor "{supplier.name}" actualizado correctamente.')
    return redirect('suppliers:list')


@login_required
@manager_required
def supplier_delete(request, pk):
    if request.method == 'POST':
        supplier = get_object_or_404(Supplier, pk=pk)
        name = supplier.name
        try:
            log_action(request, 'delete', supplier)
            supplier.delete()
            messages.success(request, f'Proveedor "{name}" eliminado correctamente.')
        except Exception:
            messages.error(request, f'No se puede eliminar "{name}" porque tiene órdenes asociadas.')
    return redirect('suppliers:list')


@login_required
@manager_required
def purchase_order_edit(request, pk):
    order = get_object_or_404(PurchaseOrder, pk=pk)
    if request.method == 'POST':
        order.expected_date = request.POST.get('expected_date') or None
        order.notes = request.POST.get('notes', '').strip()
        new_status = request.POST.get('status', '')
        if new_status in [s[0] for s in PurchaseOrder.STATUS_CHOICES]:
            order.status = new_status
        order.save()
        log_action(request, 'update', order)
        messages.success(request, f'Orden {order.order_number} actualizada correctamente.')
    return redirect('suppliers:orders')


@login_required
@manager_required
def purchase_order_delete(request, pk):
    if request.method == 'POST':
        order = get_object_or_404(PurchaseOrder, pk=pk)
        number = order.order_number
        try:
            log_action(request, 'delete', order)
            order.delete()
            messages.success(request, f'Orden {number} eliminada correctamente.')
        except Exception:
            messages.error(request, f'No se puede eliminar la orden {number}.')
    return redirect('suppliers:orders')


@login_required
def purchase_order_list(request):
    status = request.GET.get('status', '')
    orders = PurchaseOrder.objects.select_related('supplier', 'created_by').order_by('-created_at')
    if status:
        orders = orders.filter(status=status)
    paginator = Paginator(orders, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'suppliers/orders.html', {
        'page': page, 'statuses': PurchaseOrder.STATUS_CHOICES, 'selected_status': status,
    })


@login_required
@manager_required
def purchase_order_create(request):
    suppliers = Supplier.objects.filter(is_active=True).order_by('name')
    products = Product.objects.filter(is_active=True).order_by('name')

    if request.method == 'POST':
        supplier_id = request.POST.get('supplier')
        expected_date = request.POST.get('expected_date') or None
        notes = request.POST.get('notes', '').strip()

        supplier = get_object_or_404(Supplier, pk=supplier_id)

        today = timezone.now()
        prefix = today.strftime('%Y%m%d')
        count = PurchaseOrder.objects.filter(order_number__startswith=prefix).count() + 1
        order_number = f'{prefix}-{count:04d}'

        order = PurchaseOrder.objects.create(
            order_number=order_number,
            supplier=supplier,
            expected_date=expected_date,
            notes=notes,
            created_by=request.user,
        )

        for key, val in request.POST.items():
            if key.startswith('qty_'):
                product_id = key[4:]
                qty = int(val) if val.strip().isdigit() else 0
                if qty > 0:
                    cost_val = request.POST.get(f'cost_{product_id}', '0') or '0'
                    try:
                        cost = float(cost_val)
                    except ValueError:
                        cost = 0
                    product = get_object_or_404(Product, pk=product_id)
                    PurchaseOrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity_ordered=qty,
                        unit_cost=cost,
                    )

        log_action(request, 'create', order)
        messages.success(request, f'Orden {order_number} creada exitosamente.')
        return redirect('suppliers:order_detail', order.pk)

    return render(request, 'suppliers/order_create.html', {
        'suppliers': suppliers,
        'products': products,
    })


@login_required
def purchase_order_detail(request, pk):
    order = get_object_or_404(PurchaseOrder.objects.select_related('supplier'), pk=pk)
    items = order.items.select_related('product')
    return render(request, 'suppliers/order_detail.html', {'order': order, 'items': items})

