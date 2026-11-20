# Ventas, imágenes locales y constancia PDF

## Venta visible por rol

Angular muestra **Ventas** en Administración para ADMIN y **Mis compras** para CLIENTE. Ambas vistas consumen `GET /api/v1/ventas`: el servidor devuelve todas las ventas al administrador y solo las propias al cliente. El administrador no compra ni cambia a mano el resultado del pago.

La pantalla está en `clients/garritas-frontend/src/app/features/ventas/ventas.component.ts` y `.html`. Contiene lista, filtros por ID/cliente, estado y fechas, detalle, consulta de pago y descarga PDF. Las fechas se comparan como días del navegador. El resumen administrativo considera solo ventas PAGADA e incluye el cargo de envío; no es una contabilidad de ingresos bancarios. Los nombres de productos/sedes se consultan de sus maestros actuales; los precios y cantidades proceden de los detalles históricos de Venta.

La pantalla consulta cada tres segundos mientras detecta operaciones pendientes y cancela la suscripción al salir. El botón Actualizar permite descubrir nuevas ventas. Los estados son PENDIENTE_STOCK, PENDIENTE_PAGO, PAGADA, COMPENSANDO y CANCELADA; cada uno incluye una explicación. Cambiar presentación no cambia la Saga, sus importes ni la clave de idempotencia del checkout.

## Seleccionar una foto de la computadora

Solo ADMIN puede crear, reemplazar o borrar imágenes. En Productos, Especialistas y Sedes: crear/editar → Seleccionar imagen → vista previa → Guardar. La imagen es opcional; Quitar imagen al guardar elimina únicamente la foto. El cliente ve una foto o un marcador cuando no existe.

Cada servicio mantiene su imagen principal mediante:

| Recurso | Endpoint | Base/tabla padre |
|---|---|---|
| Producto | `/api/v1/productos/{id}/imagen` | Catálogo / productos |
| Profesional | `/api/v1/especialistas/{id}/imagen` | Bienestar / profesionales |
| Sede | `/api/v1/sedes/{id}/imagen` | Institución / sedes |

GET lee públicamente; PUT recibe multipart con campo `archivo`; DELETE elimina la referencia y después el archivo. Esas rutas ya se distribuyen por Gateway. La autorización se verifica en Gateway y en el servicio, además de la defensa ADMIN en `LocalImages`.

- JPG/PNG de hasta 5 MB; límite 4096 por lado y 16 millones de píxeles.
- Se verifica con ImageIO y se recodifica; no se conserva el nombre ni el contenido original sin validar.
- Los nombres son UUID, y la tabla local `recurso_imagen` vincula la ruta a la FK del registro. No hay FK entre servicios.
- Al reemplazar, se guarda un archivo nuevo y se cambia la referencia SQL. Después de confirmar se limpia el anterior; ante rollback se limpia el nuevo.
- Una fila del padre se bloquea al modificar la foto para serializar reemplazos/borrados concurrentes.
- Si una foto falla después de crear el producto, el formulario conserva su ID y reintentar no crea otro producto.
- Esto no es una transacción ACID entre disco y PostgreSQL. Una interrupción abrupta puede dejar archivos sin referencia; se deben revisar como mantenimiento, sin borrar archivos todavía referenciados.

Código: `infra/garritas-common/.../LocalImages.java`, `controller/ImagenController.java` de cada dominio y `src/app/shared/{media.ts,image-editor.ts,resource-image.ts}` en Angular.

### Persistencia y respaldo

En DEV se utiliza `uploads/` dentro de la carpeta de cada servicio, independientemente de `.runtime`. Build/reinicio no la borra. Se puede configurar `app.media.directory`. No se versionan las fotos en Git; para mover datos a otra computadora se respaldan **PostgreSQL y estas carpetas**. Clonar el código no copia las fotos.

En Docker integrado se montan volúmenes `catalogo-imagenes`, `bienestar-imagenes` e `institucion-imagenes` sobre `/app/uploads`. No ejecutar `down -v` si se desean conservar datos. En una plataforma de despliegue se necesitan discos persistentes propios: un filesystem efímero no sirve. Varias réplicas necesitan almacenamiento compartido y coherente; este diseño local está pensado para una instancia por servicio con fotos.

Flyway agrega `V6__imagenes.sql` en Catálogo, `V4__imagenes.sql` en Institución y `V2__imagenes.sql` en Bienestar. No se modifican migraciones anteriores.

## Descargar e imprimir un comprobante

En Mis compras/Ventas → Ver detalle → **Descargar comprobante PDF**, disponible solo para PAGADA. El archivo descargado se abre en un lector PDF y desde allí se puede imprimir.

`GET /api/v1/ventas/{id}/comprobante` devuelve un PDF real generado con Apache PDFBox en el servidor. Reutiliza `VentaService.obtener()` para la autorización: propietario o ADMIN. Una compra pendiente/cancelada devuelve 409. El servidor utiliza los detalles, el subtotal, el envío y el total persistidos; el navegador no manda el importe del comprobante. Conserva referencias de producto, cliente y sede para no presentar nombres actuales como históricos.

Código: `ComprobanteService.java` y `VentaController.java` del servicio Venta; llamada HTTP con JWT en `core/api.ts`; descarga en `features/ventas`.

**Es una constancia de compra de laboratorio con pago simulado, sin validez tributaria. No es boleta/factura SUNAT. Mercado Pago aún no está integrado.**

## Ejecutar después de actualizar

Detener Java/Angular, actualizar la rama sin sobrescribir cambios propios, compilar y arrancar. Las migraciones se aplican al iniciar cada servicio.

```powershell
cd "$HOME\proyectos\Garritas-"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force
.\uso-rapido\garritas.ps1 -Accion detener
git pull --ff-only origin feat/garritas-store
$env:NG_CLI_ANALYTICS = "false"
.\uso-rapido\garritas.ps1 -Accion build
.\uso-rapido\garritas.ps1 -Accion iniciar
.\uso-rapido\garritas.ps1 -Accion estado
```

Pruebas: `ComprobanteTest` comprueba PDF, paginación y rechazo de estados no pagados; `ventas.component.spec.ts` verifica filtros, roles y el bloqueo de descarga. `uso-rapido/scripts/ventas_imagenes_smoke.py` realiza login PKCE, prueba los tres recursos con fotos, permisos, rechazo de archivos inválidos/sobredimensionados, reemplazo, borrado, creación con foto, descarga real y compensación de stock. Crea historial de demostración; no borra ventas. Requiere Playwright, Pillow y PyMuPDF. Las evidencias verificadas se conservan en `docs/evidencias-ventas-imagenes/`.
