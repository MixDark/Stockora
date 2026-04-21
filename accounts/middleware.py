from django.shortcuts import redirect
from django.urls import reverse


class CleanLoginNextMiddleware:
    """Normaliza la URL de login para evitar /accounts/login/?next=/ ."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        login_path = reverse('account_login')
        if request.path == login_path and request.GET.get('next') == '/':
            return redirect('account_login')
        return self.get_response(request)


class ForcePasswordChangeMiddleware:
    """Redirige al usuario a cambiar su contraseña si el admin la ha reseteado."""

    EXEMPT_URLS = None

    def __init__(self, get_response):
        self.get_response = get_response

    def _exempt_urls(self):
        if self.EXEMPT_URLS is None:
            ForcePasswordChangeMiddleware.EXEMPT_URLS = {
                reverse('accounts:force_change_password'),
                reverse('account_login'),
                reverse('account_logout'),
            }
        return ForcePasswordChangeMiddleware.EXEMPT_URLS

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and getattr(request.user, 'must_change_password', False)
            and request.path not in self._exempt_urls()
            and not request.path.startswith('/static/')
            and not request.path.startswith('/media/')
        ):
            return redirect('accounts:force_change_password')
        return self.get_response(request)
