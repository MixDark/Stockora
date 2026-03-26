from django import forms

from .models import Customer


class CustomerForm(forms.Form):
    name = forms.CharField(max_length=200, label='Nombre')
    email = forms.EmailField(required=False, label='Correo')
    phone = forms.CharField(max_length=30, required=False, label='Teléfono')
    tax_id = forms.CharField(max_length=50, required=False, label='NIT / RUC')
    address = forms.CharField(widget=forms.Textarea, required=False, label='Dirección')

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError('El nombre del cliente es obligatorio.')
        return name
