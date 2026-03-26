from django import forms
from django.contrib.auth.password_validation import validate_password

from .models import User


class UserCreateForm(forms.Form):
    username = forms.CharField(max_length=150, label='Nombre de usuario')
    email = forms.EmailField(required=False, label='Correo electrónico')
    first_name = forms.CharField(max_length=150, required=False, label='Nombre')
    last_name = forms.CharField(max_length=150, required=False, label='Apellido')
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, label='Rol')
    password1 = forms.CharField(widget=forms.PasswordInput, label='Contraseña')
    password2 = forms.CharField(widget=forms.PasswordInput, label='Confirmar contraseña')

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(f'El usuario "{username}" ya existe.')
        return username

    def clean_role(self):
        role = self.cleaned_data['role']
        valid = [r[0] for r in User.ROLE_CHOICES]
        if role not in valid:
            raise forms.ValidationError('Rol no válido.')
        return role

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1', '')
        p2 = cleaned.get('password2', '')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Las contraseñas no coinciden.')
        elif p1:
            try:
                validate_password(p1)
            except forms.ValidationError as exc:
                self.add_error('password1', exc)
        return cleaned


class UserResetPasswordForm(forms.Form):
    password1 = forms.CharField(widget=forms.PasswordInput, label='Nueva contraseña')
    password2 = forms.CharField(widget=forms.PasswordInput, label='Confirmar contraseña')

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1', '')
        p2 = cleaned.get('password2', '')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Las contraseñas no coinciden.')
        elif p1:
            try:
                validate_password(p1, user=self.user)
            except forms.ValidationError as exc:
                self.add_error('password1', exc)
        return cleaned


class ProfileForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=False, label='Nombre')
    last_name = forms.CharField(max_length=150, required=False, label='Apellido')
    phone = forms.CharField(max_length=20, required=False, label='Teléfono')
    company = forms.CharField(max_length=100, required=False, label='Empresa')
    avatar = forms.ImageField(required=False, label='Avatar')

    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
    MAX_AVATAR_SIZE = 2 * 1024 * 1024

    def clean_avatar(self):
        import os
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            _, ext = os.path.splitext(avatar.name)
            if ext.lower() not in self.ALLOWED_EXTENSIONS:
                raise forms.ValidationError('Solo se permiten imágenes JPG, PNG, WEBP o GIF.')
            if avatar.size > self.MAX_AVATAR_SIZE:
                raise forms.ValidationError('La imagen no puede superar 2 MB.')
        return avatar
