
# Stockora

Sistema integral para la gestión de inventario, ventas, compras, cotizaciones, reportes, auditoría y notificaciones internas, orientado a PyMES. Desarrollado con Django, PostgreSQL y una interfaz moderna basada en Tailwind CSS y Alpine.js. Incluye servidor de producción con Waitress, manejo de archivos especiales (favicon, .well-known), y estructura modular para fácil mantenimiento y escalabilidad.

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
- Registro y seguimiento de ventas, cotizaciones, compras y devoluciones.
- Reportes y analítica de inventario y ventas.
- Exportación de logs y datos a Excel/CSV.
- Interfaz responsiva y moderna (Tailwind CSS, Alpine.js, FontAwesome).
- Seguridad avanzada: autenticación, permisos, captcha, recuperación y cambio forzado de contraseña.
- Auditoría de acciones de usuario y logs de actividad.
- Sistema de notificaciones internas para alertas y eventos relevantes.
- Soporte para archivos especiales (favicon.ico, /.well-known para integraciones externas).
- Manejo de archivos media para avatares y productos.
- Modularidad: cada módulo (accounts, inventory, sales, etc.) tiene su propia carpeta, modelos y migraciones.

---

## Estructura del proyecto

```
Stockora/
├── accounts/         # Gestión de usuarios, autenticación y auditoría
├── analytics/        # Módulo de analítica y reportes
├── core/             # Configuración principal, settings y urls
├── inventory/        # Inventario y movimientos de stock
├── notifications/    # Notificaciones internas
├── products/         # Catálogo de productos
├── reports/          # Reportes personalizados
├── sales/            # Ventas, cotizaciones y devoluciones
├── static/           # Archivos estáticos (css, js, imágenes, favicon, .well-known)
├── staticfiles/      # Archivos estáticos recolectados para producción
├── suppliers/        # Proveedores y compras
├── media/            # Archivos subidos (avatares, productos)
├── templates/        # Plantillas HTML organizadas por módulo
├── requirements.txt  # Dependencias Python
├── README.md         # Este archivo
├── CHANGELOG.md      # Historial de cambios
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
   git clone https://github.com/MixDark/Stockora.git
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
   Si vas a desplegar en producción, asegúrate de tener waitress y whitenoise instalados (ya incluidos en requirements.txt).
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
8. **Ejecuta el servidor:**
   - Desarrollo: `python manage.py runserver`
   - Producción: `python manage.py` (inicia Waitress en el puerto 7000 y abre el navegador automáticamente)

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
1. Ejecuta `python manage.py collectstatic` y asegúrate de que la carpeta `staticfiles` esté accesible.
2. Coloca archivos especiales (como `.well-known` o favicon.ico) dentro de `static/`.
3. Configura tu servidor web (nginx/Apache) para servir `/static/` y `/.well-known/` desde `staticfiles` si lo deseas, aunque WhiteNoise ya sirve estáticos y favicon automáticamente.
4. Ejecuta la app en producción con:
   ```sh
   python manage.py
   ```
   Esto iniciará Waitress en el puerto 7000 y abrirá el navegador automáticamente.
5. Asegúrate de tener configuradas las variables de entorno de producción (`DEBUG=False`, `ALLOWED_HOSTS`, etc).

---

## Dependencias principales
- Django
- django-allauth
- python-decouple
- psycopg2-binary
- whitenoise
- waitress
- django-crispy-forms, crispy-tailwind
- django-import-export
- tailwindcss (CDN)
- alpine.js (CDN)
- fontawesome (CDN)

**Ver el archivo `requirements.txt` para la lista completa.**

---

## Créditos y licencia
- Autor: Esteban García / Full Stack Developer
- Licencia: MIT
- Inspirado en mejores prácticas de Django y Tailwind
- Repositorio: https://github.com/MixDark/Stockora

¿Dudas o sugerencias? Abre un issue o contacta al equipo de desarrollo.
