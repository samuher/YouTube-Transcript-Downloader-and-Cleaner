# Seguridad y privacidad

Transcript Studio es una herramienta **local**. No expongas el puerto de la API en una red pública: el servidor no implementa usuarios, sesiones propias ni autenticación HTTP.

## Reportar una vulnerabilidad

Mientras el repositorio sea privado, utiliza los mecanismos privados de comunicación de GitHub con su propietario. Si se hace público, configura **Private Vulnerability Reporting** en Settings → Security antes de aceptar informes. No publiques pruebas con credenciales, cookies ni transcripciones privadas.

Indica la versión y plataforma, los pasos mínimos para reproducir el fallo y el impacto esperado. No incluyas cookies, encabezados de autorización, contraseñas ni documentos personales.

## Diseño de seguridad

- Los datos de la biblioteca se almacenan localmente mediante SQLite.
- El servidor se inicia en `127.0.0.1`; no está diseñado para uso remoto.
- Los proveedores y los controles de YouTube pueden rechazar solicitudes. La aplicación no intenta eludir restricciones de acceso.
- Las cookies son opcionales y solo deben utilizarse con cuentas y contenidos autorizados. **Un archivo de cookies equivale a una credencial de acceso.** No lo subas al repositorio ni lo adjuntes a un issue.
- La aplicación valida las URL de YouTube antes de entregarlas al proveedor.
- No existe cifrado de la base de datos local. Protege la carpeta de datos mediante los permisos del sistema operativo y las copias de seguridad correspondientes.

## Actualizaciones

Revisa las propuestas de Dependabot y las alertas de dependencias antes de integrarlas. La presencia de GitHub Actions no sustituye las revisiones de seguridad.

## Alcance conocido

No se ha realizado una auditoría externa de seguridad ni pruebas de penetración. Los tests unitarios y de API no garantizan ausencia de vulnerabilidades.
