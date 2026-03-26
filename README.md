
# Stockora

Sistema integral para la gestión de inventario, ventas, compras, cotizaciones y reportes, orientado a PyMES. Desarrollado con Django, PostgreSQL y una interfaz moderna basada en Tailwind CSS y Alpine.js.

---

## Tabla de contenidos
- [Características](#características)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Variables de entorno](#variables-de-entorno)
- [Comandos útiles](#comandos-útiles)
- [Despliegue en producción](#despliegue-en-producción)
- [Dependencias principales](#dependencias-principales)
- [Créditos y licencia](#créditos-y-licencia)

---

## Características
- Gestión de productos, almacenes, proveedores, clientes y usuarios.
- Control de stock y movimientos de inventario (entradas, salidas, transferencias).
- Registro y seguimiento de ventas, cotizaciones y compras.
- Reportes y analítica de inventario y ventas.
- Exportación de logs y datos a Excel/CSV.
- Interfaz responsiva y moderna (Tailwind CSS, Alpine.js, FontAwesome).
- Seguridad avanzada: autenticación, permisos, captcha, recuperación de contraseña.
- Soporte para archivos especiales (ej: /.well-known para integraciones externas).

---

## Estructura del proyecto

```
Stockora/
├── accounts/         # Gestión de usuarios y autenticación
├── analytics/        # Módulo de analítica y reportes
├── core/             # Configuración principal y urls
├── inventory/        # Inventario y movimientos de stock
├── products/         # Catálogo de productos
├── sales/            # Ventas y cotizaciones
├── static/           # Archivos estáticos (css, js, imágenes, .well-known)
├── suppliers/        # Proveedores y compras
├── templates/        # Plantillas HTML
├── requirements.txt  # Dependencias Python
├── README.md         # Este archivo
└── ...
```

---

## Requisitos
- Python 3.10 o superior
- PostgreSQL
- Node.js (solo para desarrollo frontend)

---

## Instalación

1. **Clona el repositorio:**
   ```sh
   git clone <repo-url>
   cd Stockora
   ```
2. **Crea y activa un entorno virtual:**
   ```sh
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   ```
3. **Instala las dependencias:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Configura las variables de entorno:**
   - Copia `.env.example` a `.env` y edítalo con tus datos (DB, email, etc).
5. **Realiza las migraciones:**
   ```sh
   python manage.py migrate
   ```
6. **Crea un superusuario:**
   ```sh
   python manage.py createsuperuser
   ```
7. **Carga datos de ejemplo (opcional):**
   ```sh
   python manage.py loaddata fixtures/demo.json
   ```
8. **Ejecuta el servidor de desarrollo:**
   ```sh
   python manage.py runserver
   ```

---

## Variables de entorno
Ejemplo de `.env`:
```
SECRET_KEY=tu_clave_secreta
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=stockora_db
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=usuario@gmail.com
EMAIL_HOST_PASSWORD=clave
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=Stockora <noreply@stockora.com>
```

---

## Comandos útiles
- Ejecutar migraciones: `python manage.py migrate`
- Crear superusuario: `python manage.py createsuperuser`
- Ejecutar servidor: `python manage.py runserver`
- Recolectar estáticos: `python manage.py collectstatic`
- Exportar dependencias: `pip freeze > requirements.txt`

---

## Despliegue en producción
1. Ejecuta `collectstatic` y asegúrate de que la carpeta `staticfiles` esté accesible.
2. Coloca archivos especiales (como `.well-known`) dentro de `static/.well-known`.
3. Configura tu servidor web (nginx/Apache) para servir `/static/` y `/.well-known/` desde `staticfiles`.
4. Usa Gunicorn/UWSGI + nginx para servir la app Django.
5. Asegúrate de tener configuradas las variables de entorno de producción (`DEBUG=False`, `ALLOWED_HOSTS`, etc).

---

## Dependencias principales
- Django
- django-allauth
- python-decouple
- psycopg2-binary
- whitenoise
- django-crispy-forms, crispy-tailwind
- django-import-export
- tailwindcss (CDN)
- alpine.js (CDN)
- fontawesome (CDN)

**Ver el archivo `requirements.txt` para la lista completa.**

---

## Créditos y licencia
- Autor: Tu Nombre / Equipo
- Licencia: MIT
- Inspirado en mejores prácticas de Django y Tailwind

¿Dudas o sugerencias? Abre un issue o contacta al equipo de desarrollo.
