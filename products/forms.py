from django import forms

from .models import Product, Category


ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
MAX_IMAGE_SIZE = 5 * 1024 * 1024


def _validate_image(image_file):
    import os
    if image_file:
        _, ext = os.path.splitext(image_file.name)
        if ext.lower() not in ALLOWED_IMAGE_EXTENSIONS:
            raise forms.ValidationError('Solo se permiten imágenes JPG, PNG, WEBP o GIF.')
        if image_file.size > MAX_IMAGE_SIZE:
            raise forms.ValidationError('La imagen no puede superar 5 MB.')
    return image_file


class ProductForm(forms.Form):
    name = forms.CharField(max_length=200, label='Nombre')
    sku = forms.CharField(max_length=100, label='SKU', required=False)
    barcode = forms.CharField(max_length=100, required=False, label='Código de barras')
    description = forms.CharField(widget=forms.Textarea, required=False, label='Descripción')
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(), required=False, label='Categoría'
    )
    cost_price = forms.DecimalField(max_digits=14, decimal_places=2, required=False, label='Costo')
    sale_price = forms.DecimalField(max_digits=14, decimal_places=2, required=False, label='Precio venta')
    tax_rate = forms.DecimalField(max_digits=5, decimal_places=2, required=False, label='IVA %')
    unit = forms.ChoiceField(choices=Product.UNIT_CHOICES, label='Unidad')
    min_stock = forms.IntegerField(min_value=0, required=False, label='Stock mínimo')
    max_stock = forms.IntegerField(min_value=0, required=False, label='Stock máximo')
    reorder_point = forms.IntegerField(min_value=0, required=False, label='Punto de reorden')
    reorder_quantity = forms.IntegerField(min_value=0, required=False, label='Cantidad de reorden')
    has_batches = forms.BooleanField(required=False, label='Maneja lotes')
    has_serial_numbers = forms.BooleanField(required=False, label='Maneja números de serie')
    valuation_method = forms.ChoiceField(choices=Product.VALUATION_CHOICES, label='Método de valoración')
    notes = forms.CharField(widget=forms.Textarea, required=False, label='Notas')
    image = forms.ImageField(required=False, label='Imagen')

    def clean_image(self):
        return _validate_image(self.cleaned_data.get('image'))


class CategoryQuickForm(forms.Form):
    name = forms.CharField(max_length=100, label='Nombre')

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError('El nombre es obligatorio.')
        if Category.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError(f'La categoría "{name}" ya existe.')
        return name
