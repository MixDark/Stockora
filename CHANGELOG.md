# CHANGELOG

## [1.0.0] - 2026-03-25

### Características principales
- Sistema de gestión de inventario, ventas, compras, reportes, cuentas de usuario, notificaciones y proveedores.
- Interfaz web basada en Django con panel de administración y vistas personalizadas para cada módulo.
- Migración a servidor de producción Waitress para mayor robustez y compatibilidad multiplataforma.
- Apertura automática del navegador al iniciar el servidor en modo producción.
- Manejo de archivos estáticos y favicon.ico usando WhiteNoise para servir recursos correctamente en producción.
- Estructura modular: apps separadas para accounts, analytics, inventory, notifications, products, reports, sales y suppliers.
- Soporte para autenticación de usuarios, cambio forzado de contraseña y auditoría de acciones.
- Gestión de productos, categorías, almacenes, movimientos de stock y ubicaciones.
- Registro y seguimiento de ventas, cotizaciones, devoluciones y clientes.
- Módulo de proveedores con órdenes de compra y gestión de relaciones.
- Generación de reportes de inventario, movimientos y ventas.
- Sistema de notificaciones internas para alertas y eventos relevantes.
- Plantillas HTML organizadas por módulo y uso de partials para componentes reutilizables.
- Archivos de migración iniciales para todas las apps principales.
- Configuración de entorno virtual y dependencias en requirements.txt.
- Archivos de configuración para desarrollo y producción (settings.py, settings_dev.py).
- Inclusión de archivos estáticos y media para recursos de la aplicación.
- Estructura preparada para internacionalización (carpeta locale).
- Documentación inicial en README.md.

### Mejoras técnicas
- Limpieza y organización de imports en todos los módulos.
- Separación clara entre lógica de negocio, vistas y modelos.
- Uso de threading para apertura no bloqueante del navegador.
- .gitignore adaptado para entornos Python, VSCode y archivos temporales.

---
