from django import forms

from .models import Warehouse, StockMovement
from products.models import Product


class WarehouseForm(forms.Form):
    name = forms.CharField(max_length=150, label='Nombre')
    code = forms.CharField(max_length=20, label='Código')
    address = forms.CharField(widget=forms.Textarea, required=False, label='Dirección')
    phone = forms.CharField(max_length=20, required=False, label='Teléfono')

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance
        super().__init__(*args, **kwargs)

    def clean_code(self):
        code = self.cleaned_data['code'].strip().upper()
        qs = Warehouse.objects.filter(code=code)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(f'Ya existe un almacén con el código "{code}".')
        return code


class StockMovementForm(forms.Form):
    movement_type = forms.ChoiceField(choices=StockMovement.TYPE_CHOICES, label='Tipo de movimiento')
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True).order_by('name'), label='Producto'
    )
    quantity = forms.IntegerField(min_value=1, label='Cantidad')
    from_warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.filter(is_active=True), required=False, label='Almacén origen'
    )
    to_warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.filter(is_active=True), required=False, label='Almacén destino'
    )
    unit_cost = forms.DecimalField(max_digits=14, decimal_places=2, required=False, label='Costo unitario')
    reference = forms.CharField(max_length=100, required=False, label='Referencia')
    notes = forms.CharField(widget=forms.Textarea, required=False, label='Notas')
