#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import threading
import webbrowser
import time
from waitress import serve
from core.wsgi import application

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    # Si no se pasa ningún subcomando, inicia el servidor de producción con Waitress
    if len(sys.argv) == 1:
        port = 7000
        url = f"http://127.0.0.1:{port}"
        print(f"Iniciando servidor de producción con Waitress en {url}")
        # Abrir navegador automáticamente después de un pequeño retardo
        threading.Timer(2, lambda: webbrowser.open(url)).start()
        # Servir favicon.ico si no existe, usando WhiteNoise
        try:
            from whitenoise import WhiteNoise
            static_dir = os.path.join(os.path.dirname(__file__), 'static')
            app_with_static = WhiteNoise(application, root=static_dir)
            serve(app_with_static, host="0.0.0.0", port=port)
        except ImportError:
            serve(application, host="0.0.0.0", port=port)
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
