#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import threading
import webbrowser

from decouple import config


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    if len(sys.argv) == 1:
        host = config('APP_HOST', default='127.0.0.1')
        port = config('APP_PORT', default=7000, cast=int)
        url = f'http://{host}:{port}/'
        try:
            from waitress import serve
            from core.wsgi import application
        except ImportError as exc:
            raise ImportError(
                "No se pudo importar Waitress. Instala dependencias con: pip install -r requirements.txt"
            ) from exc

        print(f'Iniciando servidor con Waitress en {url}')
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
        serve(application, host=host, port=port)
        return
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. ¿Está instalado y disponible en tu "
            "variable de entorno PYTHONPATH? ¿Olvidaste activar el entorno virtual?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
