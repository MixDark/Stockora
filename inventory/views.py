from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator

from accounts.audit import log_action
from accounts.decorators import admin_required, manager_required, warehouse_or_above
from accounts.models import User
from .models import Warehouse, Location, StockItem, StockMovement, InventoryCount
from products.models import Product


@login_required
def stock_list(request):
    warehouse_id = request.GET.get('warehouse', '')
    query = request.GET.get('q', '')
    stocks = StockItem.objects.select_related('product', 'warehouse', 'location').order_by('product__name')
    if warehouse_id:
        stocks = stocks.filter(warehouse_id=warehouse_id)
    if query:
        stocks = stocks.filter(Q(product__name__icontains=query) | Q(product__sku__icontains=query))
    paginator = Paginator(stocks, 25)
    page = paginator.get_page(request.GET.get('page'))
    warehouses = Warehouse.objects.filter(is_active=True)
    return render(request, 'inventory/stock_list.html', {
        'page': page, 'warehouses': warehouses,
        'selected_warehouse': warehouse_id, 'query': query,
    })


@login_required
def movement_list(request):
    movement_type = request.GET.get('type', '')
    warehouse_id = request.GET.get('warehouse', '')
    query = request.GET.get('q', '')
    movements = StockMovement.objects.select_related(
        'product', 'from_warehouse', 'to_warehouse', 'performed_by'
    ).order_by('-created_at')
    if movement_type:
        movements = movements.filter(movement_type=movement_type)
    if warehouse_id:
        movements = movements.filter(Q(from_warehouse_id=warehouse_id) | Q(to_warehouse_id=warehouse_id))
    if query:
        movements = movements.filter(Q(product__name__icontains=query) | Q(reference__icontains=query))
    paginator = Paginator(movements, 30)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'inventory/movements.html', {
        'page': page, 'movement_types': StockMovement.TYPE_CHOICES,
        'warehouses': Warehouse.objects.filter(is_active=True),
        'selected_type': movement_type, 'selected_warehouse': warehouse_id, 'query': query,
    })


from decimal import Decimal, InvalidOperation

@login_required
@warehouse_or_above
def movement_create(request):
    if request.method == 'POST':
        movement_type = request.POST.get('movement_type')
        product_id = request.POST.get('product')
        try:
            quantity = int(request.POST.get('quantity', 0))
        except (ValueError, TypeError):
            quantity = 0
        from_warehouse_id = request.POST.get('from_warehouse') or None
        to_warehouse_id = request.POST.get('to_warehouse') or None

        # Convertir unit_cost a Decimal de forma segura
        try:
            unit_cost = Decimal(request.POST.get('unit_cost', '0').replace(',', '.'))
        except (InvalidOperation, ValueError):
            unit_cost = Decimal('0')

        # Obtener la ubicación (puede ser from_location o to_location según el tipo)
        location = request.POST.get('location', '')

        if quantity <= 0:
            messages.error(request, 'La cantidad debe ser mayor a 0.')
        else:
            product = get_object_or_404(Product, pk=product_id)
            
            # Si unit_cost es 0, usar el costo del producto
            if unit_cost == 0:
                unit_cost = product.cost_price or Decimal('0')
            
            movement = StockMovement.objects.create(
                movement_type=movement_type, product=product,
                from_warehouse_id=from_warehouse_id, to_warehouse_id=to_warehouse_id,
                quantity=quantity,
                unit_cost=unit_cost,
                location=location,
                from_location_id=request.POST.get('from_location') or None,
                to_location_id=request.POST.get('to_location') or None,
                reference=request.POST.get('reference', ''),
                notes=request.POST.get('notes', ''),
                performed_by=request.user,
            )
            if to_warehouse_id:
                # Obtener o crear la ubicación
                to_location_id = None
                if location:
                    # Buscar o crear la ubicación
                    warehouse = Warehouse.objects.get(pk=to_warehouse_id)
                    location_parts = location.split('-')
                    if len(location_parts) >= 3:
                        to_location, _ = Location.objects.get_or_create(
                            warehouse=warehouse,
                            aisle=location_parts[0],
                            shelf=location_parts[1],
                            level=location_parts[2],
                        )
                        to_location_id = to_location.id
                    elif len(location_parts) == 1:
                        # Solo pasillo
                        to_location, _ = Location.objects.get_or_create(
                            warehouse=warehouse,
                            aisle=location_parts[0],
                            shelf='',
                            level='',
                        )
                        to_location_id = to_location.id
                
                item_kwargs = {'product': product, 'warehouse_id': to_warehouse_id}
                if to_location_id:
                    item_kwargs['location_id'] = to_location_id
                
                item, _ = StockItem.objects.get_or_create(
                    **item_kwargs, defaults={'quantity': 0}
                )
                item.quantity += quantity
                if to_location_id and not item.location_id:
                    item.location_id = to_location_id
                item.save()
            if from_warehouse_id and movement_type in (StockMovement.TYPE_OUT, StockMovement.TYPE_TRANSFER):
                try:
                    item = StockItem.objects.get(product=product, warehouse_id=from_warehouse_id)
                    item.quantity = max(0, item.quantity - quantity)
                    item.save()
                except StockItem.DoesNotExist:
                    pass
            messages.success(request, 'Movimiento registrado exitosamente.')
            log_action(request, 'create', movement)
            return redirect('inventory:stock')

    selected_product_id = request.GET.get('product', '')
    selected_warehouse_id = request.GET.get('warehouse', '')
    selected_unit_cost = ''
    selected_location = request.POST.get('location', '') or request.GET.get('location', '')
    if selected_product_id:
        try:
            product = Product.objects.get(pk=selected_product_id)
            # Convertir Decimal a string para la plantilla
            if product.cost_price:
                selected_unit_cost = str(product.cost_price)
        except Product.DoesNotExist:
            pass
    return render(request, 'inventory/movement_form.html', {
        'products': Product.objects.filter(is_active=True).order_by('name'),
        'warehouses': Warehouse.objects.filter(is_active=True),
        'movement_types': StockMovement.TYPE_CHOICES,
        'selected_product_id': selected_product_id,
        'selected_warehouse_id': selected_warehouse_id,
        'selected_unit_cost': selected_unit_cost,
        'selected_location': selected_location,
    })


@login_required
def warehouse_list(request):
    warehouses = Warehouse.objects.all().order_by('name')
    users = User.objects.filter(is_active=True).order_by('first_name', 'username')
    return render(request, 'inventory/warehouses.html', {'warehouses': warehouses, 'users': users})


@login_required
def warehouse_detail(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)
    stock_items = warehouse.stock_items.select_related('product', 'location').order_by('product__name')
    return render(request, 'inventory/warehouse_detail.html', {'warehouse': warehouse, 'stock_items': stock_items})


@login_required
@admin_required
def warehouse_edit(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'El nombre es obligatorio.')
            return redirect('inventory:warehouses')
        warehouse.name = name
        warehouse.address = request.POST.get('address', '').strip()
        warehouse.phone = request.POST.get('phone', '').strip()
        warehouse.manager_id = request.POST.get('manager') or None
        warehouse.save()
        log_action(request, 'update', warehouse)
        messages.success(request, f'Almacén "{warehouse.name}" actualizado correctamente.')
    return redirect('inventory:warehouses')


@login_required
@admin_required
def warehouse_delete(request, pk):
    if request.method == 'POST':
        warehouse = get_object_or_404(Warehouse, pk=pk)
        name = warehouse.name
        try:
            log_action(request, 'delete', warehouse)
            warehouse.delete()
            messages.success(request, f'Almacén "{name}" eliminado correctamente.')
        except Exception:
            messages.error(request, f'No se puede eliminar "{name}" porque tiene stock asociado.')
    return redirect('inventory:warehouses')


@login_required
@admin_required
def warehouse_create(request):
    """Crea un nuevo almacén."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip().upper()
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()
        if not name or not code:
            messages.error(request, 'El nombre y el código son obligatorios.')
        elif Warehouse.objects.filter(code=code).exists():
            messages.error(request, f'Ya existe un almacén con el código "{code}".')
        else:
            manager_id = request.POST.get('manager') or None
            warehouse_obj = Warehouse.objects.create(
                name=name, code=code, address=address, phone=phone,
                manager_id=manager_id,
            )
            log_action(request, 'create', warehouse_obj)
            messages.success(request, f'Almacén "{name}" creado exitosamente.')
            return redirect('inventory:warehouses')
    return redirect('inventory:warehouses')


@login_required
@manager_required
def stock_item_delete(request, pk):
    """Elimina un registro de stock (StockItem)."""
    if request.method == 'POST':
        item = get_object_or_404(StockItem, pk=pk)
        product_name = item.product.name
        warehouse_name = item.warehouse.name
        try:
            log_action(request, 'delete', item)
            item.delete()
            messages.success(request, f'Stock de "{product_name}" en "{warehouse_name}" eliminado correctamente.')
        except Exception:
            messages.error(request, f'No se pudo eliminar el stock de "{product_name}".')
    return redirect('inventory:stock')


@login_required
@warehouse_or_above
def stock_edit(request, pk):
    """Edita un registro de stock."""
    item = get_object_or_404(StockItem, pk=pk)
    
    if request.method == 'POST':
        # Actualizar cantidad
        new_quantity = request.POST.get('quantity', '').strip()
        if new_quantity:
            try:
                item.quantity = int(new_quantity)
            except ValueError:
                pass
        
        # Actualizar cantidad reservada
        new_reserved = request.POST.get('reserved_quantity', '').strip()
        if new_reserved:
            try:
                item.reserved_quantity = int(new_reserved)
            except ValueError:
                pass
        
        # Actualizar ubicación
        new_location = request.POST.get('location', '').strip()
        
        if new_location:
            # Buscar o crear la ubicación
            location_parts = new_location.split('-')
            if len(location_parts) >= 3:
                location, created = Location.objects.get_or_create(
                    warehouse=item.warehouse,
                    aisle=location_parts[0],
                    shelf=location_parts[1],
                    level=location_parts[2],
                )
                item.location = location
            elif len(location_parts) == 1 and location_parts[0]:
                # Solo pasillo
                location, created = Location.objects.get_or_create(
                    warehouse=item.warehouse,
                    aisle=location_parts[0],
                    shelf='',
                    level='',
                )
                item.location = location
        else:
            item.location = None
        
        item.save()
        log_action(request, 'update', item)
        messages.success(request, 'Stock actualizado correctamente.')
        return redirect('inventory:stock')
    
    return render(request, 'inventory/stock_edit.html', {'item': item})

