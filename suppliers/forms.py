from django import forms

from .models import Supplier


class SupplierForm(forms.Form):
    name = forms.CharField(max_length=200, label='Nombre')
    contact_name = forms.CharField(max_length=150, required=False, label='Contacto')
    email = forms.EmailField(required=False, label='Correo')
    phone = forms.CharField(max_length=30, required=False, label='Teléfono')
    address = forms.CharField(widget=forms.Textarea, required=False, label='Dirección')
    tax_id = forms.CharField(max_length=50, required=False, label='NIT / RUC')

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        qs = Supplier.objects.filter(name__iexact=name)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(f'Ya existe un proveedor con el nombre "{name}".')
        return name
