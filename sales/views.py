import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from accounts.audit import log_action
from accounts.decorators import manager_required
from .models import Sale, SaleItem, Customer, Quotation, QuotationItem, Return, ReturnItem
from inventory.models import Warehouse, StockItem, StockMovement
from products.models import Product


@login_required
def sales_list(request):
    status = request.GET.get('status', '')
    query = request.GET.get('q', '')
    sales = Sale.objects.select_related('customer', 'warehouse', 'sold_by').order_by('-created_at')
    if status:
        sales = sales.filter(status=status)
    if query:
        sales = sales.filter(Q(invoice_number__icontains=query) | Q(customer__name__icontains=query))
    paginator = Paginator(sales, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'sales/list.html', {
        'page': page, 'statuses': Sale.STATUS_CHOICES, 'selected_status': status, 'query': query,
    })


@login_required
def sale_detail(request, pk):
    sale = get_object_or_404(Sale.objects.select_related('customer', 'warehouse', 'sold_by'), pk=pk)
    items = sale.items.select_related('product')
    return render(request, 'sales/detail.html', {'sale': sale, 'items': items})


@login_required
def pos_view(request):
    if request.method == 'POST':
        try:
            cart_data = json.loads(request.POST.get('cart_data', '[]'))
        except (json.JSONDecodeError, TypeError):
            cart_data = []

        if not cart_data:
            messages.error(request, 'El carrito está vacío.')
            return redirect('sales:pos')

        warehouse_id = request.POST.get('warehouse')
        customer_id = request.POST.get('customer') or None
        payment_method = request.POST.get('payment_method', Sale.PAYMENT_CASH)

        if not warehouse_id:
            messages.error(request, 'Debes seleccionar un almacén.')
            return redirect('sales:pos')

        try:
            warehouse = Warehouse.objects.get(pk=warehouse_id, is_active=True)
        except Warehouse.DoesNotExist:
            messages.error(request, 'Almacén no válido.')
            return redirect('sales:pos')

        # Generar número de factura correlativo
        today = timezone.now().strftime('%Y%m%d')
        prefix = f'POS-{today}-'
        last = Sale.objects.filter(invoice_number__startswith=prefix).order_by('-invoice_number').first()
        seq = int(last.invoice_number.split('-')[-1]) + 1 if last else 1
        invoice_number = f'{prefix}{seq:04d}'

        with transaction.atomic():
            sale = Sale.objects.create(
                invoice_number=invoice_number,
                customer_id=customer_id,
                warehouse=warehouse,
                status=Sale.STATUS_COMPLETED,
                payment_method=payment_method,
                sold_by=request.user,
            )

            for item in cart_data:
                try:
                    product = Product.objects.get(pk=item['id'], is_active=True)
                    qty = int(item.get('qty', 1))
                    price = float(item.get('price', 0))
                except (Product.DoesNotExist, KeyError, ValueError, TypeError):
                    continue

                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=qty,
                    unit_price=price,
                )

                # Registrar movimiento de salida y descontar stock
                StockMovement.objects.create(
                    movement_type=StockMovement.TYPE_OUT,
                    product=product,
                    from_warehouse=warehouse,
                    quantity=qty,
                    reference=invoice_number,
                    performed_by=request.user,
                )
                stock_item = StockItem.objects.filter(product=product, warehouse=warehouse).first()
                if stock_item:
                    stock_item.quantity = max(0, stock_item.quantity - qty)
                    stock_item.save()

        log_action(request, 'create', sale)
        messages.success(request, f'Venta {invoice_number} registrada correctamente.')
        return redirect('sales:detail', pk=sale.pk)

    return render(request, 'sales/pos.html', {
        'warehouses': Warehouse.objects.filter(is_active=True),
        'customers': Customer.objects.filter(is_active=True).order_by('name'),
        'products': Product.objects.filter(is_active=True).order_by('name'),
        'payment_methods': Sale.PAYMENT_CHOICES,
    })


@login_required
def customer_list(request):
    query = request.GET.get('q', '')
    customers = Customer.objects.filter(is_active=True).order_by('name')
    if query:
        customers = customers.filter(Q(name__icontains=query) | Q(email__icontains=query))
    paginator = Paginator(customers, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'sales/customers.html', {'customers': page, 'query': query})


@login_required
@manager_required
def customer_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'El nombre del cliente es obligatorio.')
            return redirect('sales:customers')
        customer = Customer.objects.create(
            name=name,
            email=request.POST.get('email', '').strip(),
            phone=request.POST.get('phone', '').strip(),
            tax_id=request.POST.get('tax_id', '').strip(),
            address=request.POST.get('address', '').strip(),
        )
        log_action(request, 'create', customer)
        messages.success(request, f'Cliente "{name}" creado correctamente.')
    return redirect('sales:customers')


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    sales = customer.sales.select_related('warehouse').order_by('-created_at')[:20]
    return render(request, 'sales/customer_detail.html', {'customer': customer, 'sales': sales})


@login_required
@manager_required
def customer_delete(request, pk):
    if request.method == 'POST':
        customer = get_object_or_404(Customer, pk=pk)
        name = customer.name
        try:
            log_action(request, 'delete', customer)
            customer.delete()
            messages.success(request, f'Cliente "{name}" eliminado correctamente.')
        except Exception:
            messages.error(request, f'No se puede eliminar "{name}" porque tiene registros asociados.')
    return redirect('sales:customers')


@login_required
@manager_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'El nombre del cliente es obligatorio.')
            return redirect('sales:customers')
        customer.name    = name
        customer.email   = request.POST.get('email', '').strip()
        customer.phone   = request.POST.get('phone', '').strip()
        customer.tax_id  = request.POST.get('tax_id', '').strip()
        customer.address = request.POST.get('address', '').strip()
        customer.save()
        log_action(request, 'update', customer)
        messages.success(request, f'Cliente "{name}" actualizado correctamente.')
    return redirect('sales:customers')


@login_required
@manager_required
def quotation_delete(request, pk):
    if request.method == 'POST':
        quotation = get_object_or_404(Quotation, pk=pk)
        number = quotation.quotation_number
        try:
            log_action(request, 'delete', quotation)
            quotation.delete()
            messages.success(request, f'Cotización {number} eliminada correctamente.')
        except Exception:
            messages.error(request, f'No se puede eliminar la cotización {number}.')
    return redirect('sales:quotations')


@login_required
def quotation_list(request):
    qs = Quotation.objects.select_related('customer', 'created_by').order_by('-created_at')
    status = request.GET.get('status', '')
    query  = request.GET.get('q', '')
    if status:
        qs = qs.filter(status=status)
    if query:
        qs = qs.filter(
            Q(quotation_number__icontains=query) | Q(customer__name__icontains=query)
        )
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'sales/quotations.html', {
        'page': page, 'quotations': page.object_list,
        'selected_status': status, 'query': query,
    })


@login_required
def quotation_create(request):
    customers = Customer.objects.filter(is_active=True).order_by('name')
    products  = Product.objects.filter(is_active=True).order_by('name')

    if request.method == 'POST':
        customer_id = request.POST.get('customer') or None
        valid_until = request.POST.get('valid_until') or None
        notes       = request.POST.get('notes', '').strip()

        try:
            items_data = json.loads(request.POST.get('items_data', '[]'))
        except (json.JSONDecodeError, TypeError):
            items_data = []

        if not items_data:
            messages.error(request, 'Debes agregar al menos un producto.')
            products_list = list(products)
            products_data = json.dumps([
                {'id': p.pk, 'name': p.name, 'price': float(p.sale_price)}
                for p in products_list
            ])
            return render(request, 'sales/quotation_form.html', {
                'customers': customers, 'products': products_list, 'products_data': products_data,
            })

        # Número correlativo
        today  = timezone.now().strftime('%Y%m%d')
        prefix = f'COT-{today}-'
        last   = Quotation.objects.filter(quotation_number__startswith=prefix).order_by('-quotation_number').first()
        seq    = int(last.quotation_number.split('-')[-1]) + 1 if last else 1
        number = f'{prefix}{seq:04d}'

        with transaction.atomic():
            quotation = Quotation.objects.create(
                quotation_number=number,
                customer_id=customer_id,
                valid_until=valid_until,
                notes=notes,
                created_by=request.user,
                status=Quotation.STATUS_DRAFT,
            )
            for item in items_data:
                try:
                    product  = Product.objects.get(pk=item['id'], is_active=True)
                    qty      = int(item.get('qty', 1))
                    price    = float(item.get('price', 0))
                    discount = float(item.get('discount', 0))
                except (Product.DoesNotExist, KeyError, ValueError, TypeError):
                    continue
                QuotationItem.objects.create(
                    quotation=quotation, product=product,
                    quantity=qty, unit_price=price, discount=discount,
                )

        log_action(request, 'create', quotation)
        messages.success(request, f'Cotización {number} creada correctamente.')
        return redirect('sales:quotation_detail', pk=quotation.pk)

    products_list = list(products)
    products_data = json.dumps([
        {'id': p.pk, 'name': p.name, 'price': float(p.sale_price)}
        for p in products_list
    ])
    return render(request, 'sales/quotation_form.html', {
        'customers': customers,
        'products': products_list,
        'products_data': products_data,
    })


@login_required
def quotation_detail(request, pk):
    quotation = get_object_or_404(
        Quotation.objects.select_related('customer', 'created_by'), pk=pk
    )
    items = quotation.items.select_related('product')
    warehouses      = Warehouse.objects.filter(is_active=True)
    payment_methods = Sale.PAYMENT_CHOICES
    return render(request, 'sales/quotation_detail.html', {
        'quotation': quotation, 'items': items,
        'warehouses': warehouses, 'payment_methods': payment_methods,
    })


@login_required
def quotation_change_status(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status', '')
        allowed    = {
            Quotation.STATUS_DRAFT:    [Quotation.STATUS_SENT],
            Quotation.STATUS_SENT:     [Quotation.STATUS_ACCEPTED, Quotation.STATUS_REJECTED],
            Quotation.STATUS_ACCEPTED: [],
            Quotation.STATUS_REJECTED: [],
            Quotation.STATUS_EXPIRED:  [],
        }
        if new_status in allowed.get(quotation.status, []):
            quotation.status = new_status
            quotation.save()
            log_action(request, 'update', quotation)
            messages.success(request, f'Estado actualizado a "{quotation.get_status_display()}".')
        else:
            messages.error(request, 'Cambio de estado no permitido.')
    return redirect('sales:quotation_detail', pk=pk)


@login_required
def quotation_convert(request, pk):
    """Convierte una cotización aceptada en una venta."""
    quotation = get_object_or_404(Quotation, pk=pk)

    if quotation.status != Quotation.STATUS_ACCEPTED:
        messages.error(request, 'Solo se pueden convertir cotizaciones aceptadas.')
        return redirect('sales:quotation_detail', pk=pk)

    if request.method == 'POST':
        warehouse_id    = request.POST.get('warehouse')
        payment_method  = request.POST.get('payment_method', Sale.PAYMENT_CASH)

        try:
            warehouse = Warehouse.objects.get(pk=warehouse_id, is_active=True)
        except Warehouse.DoesNotExist:
            messages.error(request, 'Almacén no válido.')
            return redirect('sales:quotation_detail', pk=pk)

        today  = timezone.now().strftime('%Y%m%d')
        prefix = f'VTA-{today}-'
        last   = Sale.objects.filter(invoice_number__startswith=prefix).order_by('-invoice_number').first()
        seq    = int(last.invoice_number.split('-')[-1]) + 1 if last else 1
        invoice_number = f'{prefix}{seq:04d}'

        with transaction.atomic():
            sale = Sale.objects.create(
                invoice_number=invoice_number,
                customer=quotation.customer,
                warehouse=warehouse,
                status=Sale.STATUS_COMPLETED,
                payment_method=payment_method,
                notes=f'Generada desde cotización {quotation.quotation_number}',
                sold_by=request.user,
            )
            for q_item in quotation.items.select_related('product'):
                SaleItem.objects.create(
                    sale=sale, product=q_item.product,
                    quantity=q_item.quantity, unit_price=q_item.unit_price,
                    discount=q_item.discount,
                )
                StockMovement.objects.create(
                    movement_type=StockMovement.TYPE_OUT,
                    product=q_item.product,
                    from_warehouse=warehouse,
                    quantity=q_item.quantity,
                    reference=invoice_number,
                    performed_by=request.user,
                )
                stock_item = StockItem.objects.filter(
                    product=q_item.product, warehouse=warehouse
                ).first()
                if stock_item:
                    stock_item.quantity = max(0, stock_item.quantity - q_item.quantity)
                    stock_item.save()

            quotation.status = Quotation.STATUS_ACCEPTED
            quotation.save()

        log_action(request, 'create', sale)
        messages.success(request, f'Venta {invoice_number} generada desde la cotización.')
        return redirect('sales:detail', pk=sale.pk)

    return redirect('sales:quotation_detail', pk=pk)


# ─── Devoluciones ────────────────────────────────────────────────────────────

@login_required
def returns_list(request):
    returns = Return.objects.select_related('sale', 'processed_by').order_by('-created_at')
    paginator = Paginator(returns, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'sales/returns.html', {
        'page': page, 'returns': page.object_list,
    })


@login_required
def return_create(request, sale_pk):
    sale       = get_object_or_404(Sale, pk=sale_pk, status=Sale.STATUS_COMPLETED)
    sale_items = sale.items.select_related('product')

    if request.method == 'POST':
        reason  = request.POST.get('reason', '').strip()
        restock = request.POST.get('restock') == 'on'

        if not reason:
            messages.error(request, 'El motivo de la devolución es obligatorio.')
            return render(request, 'sales/return_create.html', {'sale': sale, 'sale_items': sale_items})

        items_to_return = []
        for item in sale_items:
            qty_str = request.POST.get(f'qty_{item.pk}', '0').strip()
            try:
                qty = int(qty_str)
            except (ValueError, TypeError):
                qty = 0
            if qty > 0:
                items_to_return.append((item, min(qty, item.quantity)))

        if not items_to_return:
            messages.error(request, 'Selecciona al menos un producto a devolver.')
            return render(request, 'sales/return_create.html', {'sale': sale, 'sale_items': sale_items})

        with transaction.atomic():
            ret = Return.objects.create(
                sale=sale,
                reason=reason,
                restock=restock,
                processed_by=request.user,
            )
            for sale_item, qty in items_to_return:
                ReturnItem.objects.create(
                    return_order=ret,
                    product=sale_item.product,
                    quantity=qty,
                )
                if restock:
                    StockMovement.objects.create(
                        movement_type=StockMovement.TYPE_RETURN,
                        product=sale_item.product,
                        to_warehouse=sale.warehouse,
                        quantity=qty,
                        reference=f'DEV-{ret.pk:05d}',
                        performed_by=request.user,
                    )
                    stock_item, _ = StockItem.objects.get_or_create(
                        product=sale_item.product, warehouse=sale.warehouse,
                        defaults={'quantity': 0, 'min_stock': 0},
                    )
                    stock_item.quantity += qty
                    stock_item.save()

            # Marcar la venta como devuelta si todos los ítems fueron devueltos
            sale.status = Sale.STATUS_RETURNED
            sale.save()

        log_action(request, 'create', ret)
        messages.success(request, f'Devolución DEV-{ret.pk:05d} registrada correctamente.')
        return redirect('sales:return_detail', pk=ret.pk)

    return render(request, 'sales/return_create.html', {
        'sale': sale, 'sale_items': sale_items,
    })


@login_required
def return_detail(request, pk):
    ret = get_object_or_404(
        Return.objects.select_related('sale', 'processed_by'), pk=pk
    )
    items = ret.items.select_related('product')
    return render(request, 'sales/return_detail.html', {'ret': ret, 'items': items})

