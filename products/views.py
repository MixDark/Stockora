import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils.text import slugify
from django.http import JsonResponse

from accounts.audit import log_action
from accounts.decorators import manager_required
from .models import Product, Category, Batch, SerialNumber


@login_required
def product_list(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    status = request.GET.get('status', 'active')

    products = Product.objects.select_related('category').order_by('name')
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(sku__icontains=query) | Q(barcode__icontains=query)
        )
    if category_id:
        products = products.filter(category_id=category_id)
    if status == 'active':
        products = products.filter(is_active=True)
    elif status == 'inactive':
        products = products.filter(is_active=False)

    paginator = Paginator(products, 20)
    page = paginator.get_page(request.GET.get('page'))
    categories = Category.objects.all()
    return render(request, 'products/list.html', {
        'page': page, 'categories': categories,
        'query': query, 'selected_category': category_id, 'status': status,
    })


@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    stock_items = product.stock_items.select_related('warehouse', 'location')
    batches = product.batches.order_by('expiry_date')
    serials = product.serial_numbers.filter(status=SerialNumber.STATUS_AVAILABLE)
    movements = product.movements.select_related(
        'from_warehouse', 'to_warehouse', 'performed_by'
    ).order_by('-created_at')[:20]
    return render(request, 'products/detail.html', {
        'product': product, 'stock_items': stock_items,
        'batches': batches, 'serials': serials, 'movements': movements,
    })


@login_required
@manager_required
def product_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        sku = request.POST.get('sku', '').strip()
        if not name or not sku:
            messages.error(request, 'El nombre y el SKU son obligatorios.')
        elif Product.objects.filter(sku=sku).exists():
            messages.error(request, f'Ya existe un producto con SKU "{sku}".')
        else:
            img_file = request.FILES.get('image')
            if img_file:
                _, ext = os.path.splitext(img_file.name)
                if ext.lower() not in {'.jpg', '.jpeg', '.png', '.webp', '.gif'}:
                    messages.error(request, 'Solo se permiten imágenes JPG, PNG, WEBP o GIF.')
                    return render(request, 'products/form.html', {
                        'categories': Category.objects.all(), 'action': 'Crear',
                        'units': Product.UNIT_CHOICES, 'valuation_methods': Product.VALUATION_CHOICES,
                    })
                if img_file.size > 5 * 1024 * 1024:
                    messages.error(request, 'La imagen no puede superar 5 MB.')
                    return render(request, 'products/form.html', {
                        'categories': Category.objects.all(), 'action': 'Crear',
                        'units': Product.UNIT_CHOICES, 'valuation_methods': Product.VALUATION_CHOICES,
                    })
            product = Product(
                sku=sku, name=name, slug=slugify(name),
                barcode=request.POST.get('barcode', ''),
                description=request.POST.get('description', ''),
                category_id=request.POST.get('category') or None,
                cost_price=request.POST.get('cost_price') or 0,
                sale_price=request.POST.get('sale_price') or 0,
                tax_rate=request.POST.get('tax_rate') or 0,
                unit=request.POST.get('unit', Product.UNIT_UNIT),
                min_stock=request.POST.get('min_stock') or 0,
                max_stock=request.POST.get('max_stock') or 1000,
                reorder_point=request.POST.get('reorder_point') or 0,
                reorder_quantity=request.POST.get('reorder_quantity') or 0,
                has_batches=bool(request.POST.get('has_batches')),
                has_serial_numbers=bool(request.POST.get('has_serial_numbers')),
                valuation_method=request.POST.get('valuation_method', Product.VALUATION_AVG),
                created_by=request.user,
            )
            if img_file:
                product.image = img_file
            product.save()
            log_action(request, 'create', product)
            messages.success(request, f'Producto "{product.name}" creado exitosamente.')
            return redirect('products:detail', pk=product.pk)

    categories = Category.objects.all()
    return render(request, 'products/form.html', {
        'categories': categories, 'action': 'Crear',
        'units': Product.UNIT_CHOICES, 'valuation_methods': Product.VALUATION_CHOICES,
    })


@login_required
@manager_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.name = request.POST.get('name', product.name).strip()
        product.barcode = request.POST.get('barcode', '')
        product.description = request.POST.get('description', '')
        product.category_id = request.POST.get('category') or None
        product.cost_price = request.POST.get('cost_price') or 0
        product.sale_price = request.POST.get('sale_price') or 0
        product.tax_rate = request.POST.get('tax_rate') or 0
        product.unit = request.POST.get('unit', product.unit)
        product.min_stock = request.POST.get('min_stock') or 0
        product.notes = request.POST.get('notes', '')
        img_file = request.FILES.get('image')
        if img_file:
            _, ext = os.path.splitext(img_file.name)
            if ext.lower() not in {'.jpg', '.jpeg', '.png', '.webp', '.gif'}:
                messages.error(request, 'Solo se permiten imágenes JPG, PNG, WEBP o GIF.')
                return redirect('products:edit', pk=product.pk)
            if img_file.size > 5 * 1024 * 1024:
                messages.error(request, 'La imagen no puede superar 5 MB.')
                return redirect('products:edit', pk=product.pk)
            product.image = img_file
        product.save()
        log_action(request, 'update', product)
        messages.success(request, 'Producto actualizado exitosamente.')
        return redirect('products:detail', pk=product.pk)

    categories = Category.objects.all()
    return render(request, 'products/form.html', {
        'product': product, 'categories': categories, 'action': 'Editar',
        'units': Product.UNIT_CHOICES, 'valuation_methods': Product.VALUATION_CHOICES,
    })


@login_required
@manager_required
def product_delete(request, pk):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=pk)
        name = product.name
        try:
            log_action(request, 'delete', product)
            product.delete()
            messages.success(request, f'Producto "{name}" eliminado correctamente.')
        except Exception:
            messages.error(request, f'No se puede eliminar "{name}" porque tiene registros asociados.')
    return redirect('products:list')


@login_required
def category_list(request):
    categories = Category.objects.all().order_by('name')
    return render(request, 'products/categories.html', {'categories': categories})


@login_required
def category_create_quick(request):
    """Crea una categoría rápidamente vía AJAX y devuelve JSON."""
    if not request.user.is_manager:
        return JsonResponse({'error': 'Acceso restringido.'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido.'}, status=405)
    name = request.POST.get('name', '').strip()
    if not name:
        return JsonResponse({'error': 'El nombre es obligatorio.'}, status=400)
    if Category.objects.filter(name__iexact=name).exists():
        return JsonResponse({'error': f'La categoría "{name}" ya existe.'}, status=400)
    cat = Category.objects.create(name=name)
    return JsonResponse({'id': cat.id, 'name': cat.name})

