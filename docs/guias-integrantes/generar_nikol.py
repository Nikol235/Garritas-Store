"""Guía de Nikol: explicación → contenido → direcciones/conexiones/diseño → código.
Reutiliza el formato de las guías individuales sin regenerar sus PDF.
"""
from pathlib import Path
import json,re,subprocess,hashlib
import generar as g
OUT=Path(__file__).resolve().parent
# Explicaciones específicas: no cambiar la lógica ni los datos de la aplicación.
g.EXPLAIN.update({
 'VentaService':'Acepta la compra: impide ADMIN comprador, verifica clave/propietario, valida sede/productos/tarifa, calcula el total en el servidor y guarda venta+detalles+Outbox. listar filtra por dueño salvo ADMIN; obtener también comprueba propiedad.',
 'VentaEvents':'Consume resultados de inventario/pago, aplica Inbox y transiciones condicionadas por estado anterior. Un pago aprobado crea un despacho único solo si se cobró delivery. No confirma CANCELADA antes de la liberación cuando hubo reserva.',
 'PrestacionService':'Administra servicios y paquetes; valida componentes y bloquea cambios concurrentes del grafo. guardarOferta relaciona sede/prestación con precio, duración y disponibilidad. No asigna el precio de un paquete globalmente a todas las sedes.',
 'SedeService':'CRUD de sedes. ADMIN puede ver inactivas; el cliente consulta activas. Eliminar desactiva sin borrar historia. DTO y mapper separan API y persistencia.',
 'CatalogoConsulta':'Envuelve la consulta Feign de producto con el Circuit Breaker catalogo. El error controlado no inventa stock/precios para vender igual.',
 'LogisticaConsulta':'Envuelve el cliente Feign de cobertura con el Circuit Breaker logistica. Si no hay tarifa confiable, no se acepta la compra con un monto inventado.',
 'ProductoClient':'Contrato Feign por nombre lógico garritas-catalogo-ms. Se resuelve con Eureka; no utiliza un puerto de instancia fijo en la anotación.',
 'LogisticaClient':'Contrato Feign de cobertura por transportista y zona. El maestro y sus tarifas pertenecen a Envío, aunque Venta los utilice al cobrar.',
 'FeignConfiguration':'Propaga autorización y correlación a las llamadas Feign. No coloca un Access Token de Mercado Pago en Angular.',
 'VentaMapper':'Convierte la entidad a respuesta; calcula subtotal como total menos costoEnvio y expone los detalles/precios de la operación ya persistida.',
 'DespachoService':'Seguimiento del delivery cobrado. listar/obtener verifican dueño; crear solo devuelve el despacho existente si la venta pagada incluye esos datos. En tránsito/entregado son transiciones ADMIN; no implementa reembolso bancario.',
})
b=g.Book('Nikol',['venta','institucion'],'Nikol-Venta-e-Institucion.pdf')
b.h('PARTE I · Qué son tus microservicios',new=True)
b.p('Tu responsabilidad asignada es Venta e Institución. Un microservicio es una aplicación de backend independiente con puerto, configuración y base propios; no es una pestaña. Venta ya existía aunque antes Angular lo llamara Mis pedidos. Ahora ADMIN ve Ventas y CLIENTE Mis compras: ambas pantallas utilizan el mismo servicio y el mismo historial.')
b.table(['Tu servicio','Qué administra','Cómo defenderlo'],[['Venta','Compras, detalles, total, estado de la Saga y despacho del delivery cobrado.','Transaccional: registra una compra coherente y coordina su avance con inventario/pago.'],['Institución','Sedes, prestaciones, paquetes y condiciones de oferta por sede.','Maestro: datos de referencia. Tu N:M principal es Sede ↔ Prestación con precio, duración y estado en la asociación.']])
b.p('La etiqueta académica maestro/no transaccional no significa que Institución carezca de @Transactional. También confirma/revierte sus cambios locales. La diferencia es su responsabilidad: Venta ejecuta la compra; Institución define dónde y qué se ofrece.')
b.p('Estado real de esta revisión: los pagos siguen simulados. Elegir YAPE en el laboratorio no deposita dinero real. Mercado Pago, Railway y Supabase aún no están conectados/desplegados en este código. La constancia PDF no es una boleta ni una factura SUNAT.')
b.p('Lee primero las partes I y II para entender. En la parte III están todas las direcciones, rutas y conexiones. La parte IV responde dónde están el diseño y las letras. Los anexos tienen un mapa de archivos y el código completo, numerado para consultar.')
b.h('1. Venta: qué hace desde que el cliente compra',new=True)
b.diagram('nikol-flujo-compra','''rankdir=TB;a[label="Cliente en Angular\nconfirma carrito"];g[label="Gateway valida JWT"];v[label="Venta valida sede,\nproductos y tarifa"];db[label="Guarda venta + detalles\ny evento Outbox\ntransacción PostgreSQL local"];k[label="Kafka: venta.creada"];c[label="Catálogo reserva stock"];p[label="Pago simulado"];ok[label="PAGADA\ndespacho si delivery cobrado"];bad[label="COMPENSANDO\nCatálogo devuelve reserva\nCANCELADA al confirmar liberación"];a->g->v->db->k->c->p;p->ok[label="aprobado"];p->bad[label="rechazado"];''','Resumen de compra. Si el inventario se rechaza antes del pago, se cancela sin compensar una reserva que no se confirmó.')
b.p('Venta consulta datos reales del servidor; no confía en precios, total o identidad enviados por el navegador. Identifica al comprador por sub del JWT, agrupa cantidades y guarda precios acordados. El cargo de envío se suma al subtotal y forma parte del importe que procesa Pago.')
b.table(['Dato','Qué significa'],[['Venta (cabecera)','Identificador, cliente, sede, fecha, estado, método, total y entrega.'],['DetalleVenta','Producto de referencia, cantidad, precio unitario y subtotal de esa compra.'],['Subtotal / envío / total','Productos + costo de envío = total. Recojo no lleva tarifa de delivery.'],['Idempotency-Key','Identifica un intento de compra: reintentar lo mismo no crea dos ventas.'],['Estado','Etapa verificable del proceso; no se cambia libremente desde un botón ADMIN.']])
b.h('2. Institución: qué hace y quién puede utilizarlo',new=True)
b.p('Institución mantiene las sedes y sus ofertas. El cliente consulta sedes activas, elige dónde recoger o atenderse y ve los servicios disponibles. ADMIN crea/edita/desactiva sedes, prestaciones y paquetes y configura el precio/duración por sede. No crea usuarios ni autentica contraseñas.')
b.table(['Concepto','Ejemplo didáctico','Dónde está la regla'],[['Sede','Local de Lima, Arequipa o Cusco.','SedeService filtra disponibilidad y aplica baja lógica.'],['Prestación','Baño, corte o consulta.','PrestacionService guarda nombre, descripción y estado.'],['Paquete','Baño + corte, como oferta conjunta.','Componentes individuales activos; no paquetes dentro de paquetes ni incluirse a sí mismo.'],['Oferta por sede','Paquete en sede A a S/ 45 y 60 minutos; en sede B a otro precio.','SedePrestacion guarda las condiciones de esa pareja.']])
b.p('Las sedes de db/demo son ejemplos ficticios del Perú. El precio de una prestación no está fijado para todo el sistema: la oferta de cada sede lo determina. Citas consulta esa oferta y conserva su precio/duración acordados en su propio detalle.')
b.diagram('nikol-relaciones','''rankdir=LR;v[label="ventas"];d[label="detalle_ventas"];s[label="sedes"];o[label="sede_prestacion\nprecio, duración, activo"];p[label="prestaciones"];v->d[label="1:N"];s->o[label="1:N"];p->o[label="1:N"];''','Venta → detalles es 1:N. Sede ↔ prestación es N:M a través de una entidad con atributos. Los IDs externos de productos o sedes en Venta no son FK entre bases.')
b.h('PARTE II · Qué contiene tu código y por qué',new=True)
b.table(['Capa','Qué contiene','Cómo explicarla'],[['Application','Entrada Spring Boot e importaciones de infraestructura común.','Arranca el servicio; incorpora seguridad y mensajería si corresponde.'],['Controller','Rutas HTTP, DTO de entrada y validación.','Recibe, valida y delega; no concentra toda la compra.'],['Service','Reglas y transacciones del negocio.','Valida, consulta otros servicios y coordina persistencia.'],['Repository','Consultas JPA, búsquedas por cliente/clave y persistencia.','Spring genera la implementación; las consultas y bloqueos importan.'],['Entity','Tablas y relaciones locales.','Representa datos; no debe confundirse con el JSON del cliente.'],['DTO y mapper','Request/Response y conversión.','Controlan qué entra/sale sin serializar un grafo JPA completo.'],['client / messaging','Llamadas síncronas y consumidores de eventos.','Feign consulta; Kafka comunica resultados diferidos.'],['db/migration','Evolución SQL con Flyway.','V1 no es todo el modelo; se aplican todas las versiones en orden.']])
b.p('Al leer los inicios de una clase: package ubica el nombre; import incorpora tipos; @Service o @RestController registra un componente; @RequiredArgsConstructor genera el constructor de los campos final. @Transactional define commit/rollback de esa base, no una transacción global entre servicios.')
b.h('3. VentaService: operación transaccional paso a paso',new=True)
for t in ['Rechaza a ADMIN como comprador: el administrador gestiona y utiliza otra cuenta para comprar.','Valida entrega: recojo sin campos/cargos de envío; delivery requiere zona, transportista, tarifa cotizada y dirección suficiente.','Obtiene el subject del JWT y toma un bloqueo por propietario + Idempotency-Key.','Si la clave ya existe, compara los datos de la operación. Misma petición devuelve la venta existente; clave con otra petición responde 409.','Consulta Institución para comprobar sede activa. Agrupa productos repetidos y sus cantidades.','Si hay delivery, consulta Envío: cobertura activa, tarifa válida y plazo. Si cambió la tarifa cotizada, devuelve conflicto para confirmar un nuevo total.','Consulta Catálogo y valida producto activo, stock observado y precio vigente. La reserva definitiva se decidirá después en Catálogo.','Construye la cabecera y los detalles con precios acordados. Calcula el total e impide importes fuera del rango permitido.','Guarda venta y Outbox venta.creada en una transacción local. Responde pendiente de stock; no declara que ya está pagada.']:
 b.bullet(t)
b.p('Tu defensa: “Si falla la escritura de detalles o del Outbox, no debe quedar una venta confirmada parcialmente. @Transactional protege ese conjunto local. El resultado remoto de inventario/pago llega después por eventos; no hay ACID único entre las tres bases”.')
b.h('4. Estados, Saga y compensación: qué sí sucede',new=True)
b.table(['Estado','Qué ocurre','Qué ve el usuario'],[['PENDIENTE_STOCK','Venta creada; Catálogo intenta reservar.','Aún no hay compra pagada.'],['PENDIENTE_PAGO','Reserva confirmada; se espera el resultado del pago simulado.','Pendiente, no volver a crear otro intento distinto por impaciencia.'],['PAGADA','Pago aprobado; despacho único si el delivery fue cobrado.','Constancia PDF disponible.'],['COMPENSANDO','Pago rechazado tras reserva; Catálogo debe devolver stock.','Cancelación en curso.'],['CANCELADA','Inventario rechazado, o liberación confirmada tras compensar.','La compra no se completó.']])
b.p('VentaEvents escucha inventario.reservado, inventario.rechazado, pago.validado, pago.fallido e inventario.liberado. Usa Inbox y UPDATE condicionado al estado esperado para no aplicar transiciones fuera de secuencia. Cuando el pago es aprobado, el INSERT del despacho comparte transacción con Inbox y el cambio de venta.')
b.p('La devolución física del stock la realiza Catálogo, en InventarioEvents.liberar. Venta no modifica directamente la base de Catálogo; espera su evento inventario.liberado. Compensar es una nueva operación de negocio que revierte un efecto ya confirmado, no deshacer toda la historia con un rollback global.')
b.table(['Situación','Cómo responder al ingeniero'],[['Catálogo/Envío cae antes de aceptar checkout','Error controlado; todavía no se guardó una venta para compensar.'],['No alcanza el stock al reservar','Rechazo de inventario; no continuar al pago.'],['Pago rechaza después de reservar','Sí hay compensación: devolver reserva y después terminar CANCELADA.'],['Kafka o Pago demora','Puede quedar pendiente para recuperación. Una demora no cancela automáticamente.'],['Evento duplicado','Inbox deduplica por eventId y las reglas/restricciones por venta evitan repetir el efecto.'],['Error SQL dentro de una operación','Rollback de esa base. No equivale a compensación entre servicios.']])
b.p('Outbox publica después del commit local, pero un fallo entre enviar y registrar confirmación puede duplicar el mensaje. Se diseña para entrega al menos una vez. Los reintentos tienen límite y existe DLT para mensajes que necesitan diagnóstico; no se promete recuperación automática de cualquier fallo.')
b.h('5. Institución: la N:M, las ofertas y los paquetes',new=True)
b.p('La N:M defendible es Sede ↔ Prestación: una sede ofrece muchas prestaciones y una prestación puede ofrecerse en muchas sedes. SedePrestacion tiene dos @ManyToOne, precio, duración y activo. Es una N:M relacional con entidad de asociación, aunque no se anote literalmente @ManyToMany.')
b.p('guardarOferta busca primero sede y prestación; impide activar una oferta si sus padres no están disponibles y exige duración múltiplo de 30 minutos. Si la pareja ya existe, actualiza sus condiciones. No es necesario duplicar una prestación para ofrecerla en otra sede.')
b.p('Prestacion también tiene una asociación con sus componentes para representar paquetes. Se exigen componentes individuales activos y al menos dos; el DTO limita cuántos se aceptan. No se permiten paquetes anidados ni incluirse a sí mismo. Un bloqueo serializa cambios concurrentes del grafo para que dos solicitudes no creen una estructura inválida.')
b.p('Ejemplo: creo Baño y Corte; creo el paquete Baño + Corte; lo ofrezco en una sede a S/ 45 y 60 min. En otra sede la misma prestación puede tener otro precio. Citas toma una copia del acuerdo, de modo que cambiar mañana la oferta no modifica una cita antigua.')
b.h('6. Imágenes, despacho y PDF: contenido adicional de tu parte',new=True)
b.table(['Capacidad','Qué implementa','Límite que debes decir'],[['Foto de sede','Selector local en Angular → multipart → Institución valida y guarda archivo + referencia SQL.','Solo ADMIN modifica. JPG/PNG de hasta 5 MB. Git no copia fotos ni bases.'],['Despacho','Venta crea seguimiento al aprobarse un pago que incluye delivery. ADMIN marca tránsito/entrega.','La tarifa maestra viene de Envío. No se añade delivery gratis a un recojo pagado.'],['Constancia PDF','Venta verifica propiedad y PAGADA y genera un archivo PDF con importes persistidos.','Es laboratorio sin validez tributaria, no comprobante electrónico SUNAT.'],['Cancelar un envío cobrado','El servicio rechaza una cancelación simple que simule devolver dinero.','No existe reembolso bancario integrado.']])
b.p('El botón de la pantalla no crea por sí solo la seguridad: el servidor comprueba las reglas. Un cliente no puede editar sede, cambiar el resultado del pago ni descargar el comprobante de otro cliente mediante una URL directa.')
b.h('PARTE III · Direcciones exactas y conexiones',new=True)
b.p('Todas las rutas se interpretan desde la carpeta raíz Garritas-Store. En VS Code usa Ctrl+P para pegar la ruta y Ctrl+G para ir a la línea. En este PDF las direcciones azules abren el archivo en GitHub en el commit analizado. Para explicar una clase, indica qué recibe, qué valida, a quién llama, qué guarda y qué devuelve.')
b.code('''Garritas-Store/
  services/garritas-venta-ms/
    src/main/java/pe/edu/upeu/garritas/venta/
      controller/  service/  repository/  entity/  dto/  mapper/
      client/  messaging/  despacho/
    src/main/resources/db/migration/
  services/garritas-institucion-ms/
    src/main/java/pe/edu/upeu/garritas/institucion/
      controller/  service/  repository/  entity/  dto/  mapper/
    src/main/resources/db/migration/ y db/demo/
  clients/garritas-frontend/src/app/features/
    ventas/  sedes/  prestaciones/  cart/
  clients/garritas-frontend/src/styles.css
  infra/garritas-config/config-repo/
  infra/garritas-common/''')
b.h('7. Los archivos de Venta que debes abrir primero',new=True)
for suffix,needle,explain,lines in [
 ('GarritasVentaMsApplication','@SpringBootApplication','Tu aplicación existe de forma independiente. @Import incluye seguridad/mensajería y @EnableFeignClients activa clientes declarativos.',9),
 ('controller/VentaController','@RequestMapping','Entrada real: /api/v1/ventas. POST recibe DTO + Idempotency-Key; GET lista/consulta y la ruta de comprobante devuelve PDF.',18),
 ('service/VentaService','public VentaResponse crear','Esta es la operación principal: empieza por autorización, entrega, propietario y clave.',18),
 ('service/VentaService','Reference sede','Consulta síncrona a Institución por nombre de servicio.',9),
 ('service/VentaService','var cobertura = logistica.obtener','Valida tarifa real. No confiar en una suma enviada desde Angular.',17),
 ('service/VentaService','repository.saveAndFlush(venta)','Venta y Outbox se guardan bajo la misma transacción local.',17),
 ('service/VentaService','public List<VentaResponse> listar','ADMIN ve todas; CLIENTE solo las del sub autenticado. No basta filtrar en la plantilla.',11),
 ('service/VentaService','private Venta owned','Protege la consulta individual y, por reutilización, el comprobante.',13),
 ('entity/Venta','@OneToMany','Tu relación 1:N local. Los detalles se guardan con la cabecera.',9),
 ('entity/DetalleVenta','@ManyToOne','Cada detalle pertenece a una venta. idProducto es una referencia remota.',10),
 ('repository/VentaRepository','public interface','Busca el dueño y las claves de reintento. El SQL de bloqueo está en el servicio.',10),
 ('messaging/VentaEvents','public void consume','Recibe resultados, filtra tipos y aplica Inbox antes de cambiar estados.',19),
 ('messaging/VentaEvents','UPDATE ventas SET','Compara el estado anterior y evita transiciones incompatibles. El despacho es único por venta.',16),
 ('service/ComprobanteService','public byte[] generar','Obtiene la venta con propiedad validada y exige PAGADA antes de crear el PDF.',17),
 ('despacho/service/DespachoService','public DespachoResponse crear','El endpoint de compatibilidad no agrega un envío sin cobrar: verifica la venta y devuelve el despacho ya preparado.',19),
]:b.ref(g.java('venta',suffix),needle,explain,lines)
b.p('VentaController no expone PUT ni DELETE de la venta: no se permite reescribir importes históricos o borrar compras como un producto maestro. Sus estados avanzan con la Saga. Los endpoints adicionales del despacho tienen sus propias reglas.')
b.h('8. Los archivos de Institución que debes abrir primero',new=True)
for suffix,needle,explain,lines in [
 ('GarritasInstitucionMsApplication','@SpringBootApplication','Entrada del servicio Institución y su contexto.',7),
 ('controller/SedeController','@RequestMapping','Rutas CRUD de /sedes; @Valid activa validación del Request.',15),
 ('service/SedeService','public List<SedeResponse> listar','Disponibilidad y orden de sedes según rol.',10),
 ('service/SedeService','public SedeResponse crear','Crear pasa por mapper y repositorio. Actualizar modifica el registro existente.',18),
 ('service/SedeService','public void eliminar','Eliminar se implementa como baja lógica activo=false.',9),
 ('entity/SedePrestacion','@ManyToOne','Dos referencias locales forman la entidad de asociación N:M.',20),
 ('service/PrestacionService','public OfertaResponse guardarOferta','Precio/duración por sede, padres disponibles y búsqueda de pareja existente.',24),
 ('entity/Prestacion','@ManyToMany','La prestación puede ser paquete de componentes locales.',13),
 ('service/PrestacionService','public PrestacionResponse guardar','Bloqueo del grafo y validación de paquetes.',30),
 ('controller/PrestacionController','@GetMapping("/sedes/{id}/prestaciones")','Citas y la interfaz consumen esta oferta por sede.',11),
 ('controller/ImagenController','@RequestMapping','GET/PUT/DELETE de foto de sede, con validación compartida.',18),
]:b.ref(g.java('institucion',suffix),needle,explain,lines)
b.p('Las migraciones de Institución crean sedes, prestaciones/ofertas, componentes de paquetes e imágenes. db/demo añade ejemplos peruanos. No edites V1 para explicar el esquema final: consulta todas las migraciones en orden.')
b.h('9. Con quién se conecta cada servicio y dónde',new=True)
b.diagram('nikol-conexiones','''rankdir=TB;a[label="Angular 4200"];gw[label="Gateway 18080"];v[label="Venta 8081"];i[label="Institución 8082"];c[label="Catálogo 8085"];e[label="Envío 8083"];ct[label="Citas 8084"];k[label="Kafka\nVenta - Catálogo - Pago"];pv[label="PG Venta 15441"];pi[label="PG Institución 15442"];a->gw;gw->v;gw->i;v->i[label="ServiceClient / sede"];v->c[label="Feign / producto"];v->e[label="Feign / tarifa"];v->pv;v->k[label="Outbox / Inbox"];ct->i[label="HTTP / oferta"];i->pi;''','Las flechas HTTP no son FK entre bases. Institución ofrece referencias a Venta/Citas; no es consumidor de la Saga de compra.')
b.table(['Origen → destino','Para qué','Código exacto'],[['Angular → Gateway','Entrada de negocio con JWT.','core/api.ts, core/domain-api.ts e interceptor.ts.'],['Gateway → Venta / Institución','Rutas lb:// por Eureka.','config-repo/garritas-gateway-dev.yml.'],['Venta → Catálogo','Producto, precio, activo y stock observado.','client/ProductoClient.java y CatalogoConsulta.java.'],['Venta → Envío','Cobertura, tarifa y días estimados.','client/LogisticaClient.java y LogisticaConsulta.java.'],['Venta → Institución','Sede activa.','VentaService.crear, services.get con nombre lógico.'],['Citas → Institución','Sede y oferta con precio/duración/componentes.','CitaService.crear de Deissy; PrestacionController.ofertas de tu dominio.'],['Venta ↔ Kafka','Evento de creación y resultados.','VentaService + Outbox; VentaEvents + Inbox.'],['Servicio → PostgreSQL propio','Datos persistidos.','YAML datasource; repositorios/JdbcTemplate y migraciones.']])
for p,needle,msg in [
 (g.java('venta','client/ProductoClient'),'@FeignClient','Nombre lógico de Catálogo, no dirección fija de instancia.'),
 (g.java('venta','client/LogisticaClient'),'@FeignClient','Nombre lógico de Envío y contrato de cobertura.'),
 (g.java('venta','client/CatalogoConsulta'),'create(','Circuit Breaker alrededor de la consulta de producto.'),
 (g.java('venta','client/FeignConfiguration'),None,'Token de usuario y correlación de las llamadas.'),
 ('infra/garritas-config/config-repo/garritas-venta-ms-dev.yml','connectTimeout','Timeout de conexión/lectura de Feign; revisar también los circuitos.'),
 ('infra/garritas-config/config-repo/garritas-venta-ms-dev.yml','sliding-window-size','Ventana, mínimo de llamadas, umbral y tiempo abierto.'),
 ('infra/garritas-config/config-repo/garritas-gateway-dev.yml','id: garritas-institucion','Ruta pública de API hacia el nombre lógico de Institución.'),
 (g.java('catalogo','messaging/InventarioEvents'),'private void liberar','Código de colaboración: Catálogo devuelve el stock reservado; tú consumes su confirmación.'),
]:b.ref(p,needle,msg,11)
b.p('Timeout y Circuit Breaker no son sinónimos. El timeout limita una espera individual; el circuito recuerda fallos y rechaza rápido cuando el destino no está saludable. Aquí el error controlado no inventa precios ni stock para seguir vendiendo. Las referencias a Institución y Citas usan ServiceClient, no todos los enlaces son Feign con circuito.')
b.h('10. Seguridad: cómo se conectan Keycloak y tus tablas',new=True)
b.p('Keycloak autentica y emite el JWT con sub y realm_access.roles. Angular conserva el token en memoria y lo adjunta a la API. Gateway y cada microservicio vuelven a validar firma, issuer y audiencia. La identidad del comprador no se toma de un idCliente enviado en JSON.')
for p,needle,msg in [(g.front('core/auth.ts'),'pkceMethod','Authorization Code con PKCE S256, login/logout y roles.'),(g.front('core/interceptor.ts'),'Authorization','Bearer solo para nuestra API.'),(g.COMMON+'SecurityConfiguration.java','SecurityFilterChain','ADMIN para maestros; CLIENTE/ADMIN para recursos propios, con excepciones por acción.'),(g.COMMON+'SecurityConfiguration.java','/api/v1/ventas','POST compra requiere CLIENTE y rechaza ADMIN aunque tenga ambos roles.'),(g.COMMON+'CurrentUser.java','requireOwner','Identidad persistida frente al sujeto autenticado; ADMIN puede auditar.')]:b.ref(p,needle,msg,9)
b.p('Las tablas locales no sustituyen Keycloak. Institución guarda sedes/ofertas; Venta guarda compras. La tabla de roles internos de Usuario es otra capacidad: cambiarla no cambia por sí solo un JWT a ADMIN. Ocultar botones es presentación, no la barrera de seguridad.')
b.h('11. Direcciones para abrir y comprobar el sistema',new=True)
b.table(['Componente','Dirección local','Qué puedes mostrar'],[['Angular','http://localhost:4200','ADMIN → Ventas/Sedes; CLIENTE → Mis compras.'],['Venta Swagger','http://localhost:8081/swagger-ui.html','Endpoints y DTO reales.'],['Institución Swagger','http://localhost:8082/swagger-ui.html','Sedes, prestaciones, ofertas e imágenes.'],['Gateway','http://localhost:18080/api/v1/sedes','API a través del punto de entrada. No tiene una portada de tienda en /.'],['Health Venta / Institución','http://localhost:8081/actuator/health/readiness y puerto 8082','Disponibilidad configurada; no sustituye la prueba de negocio.'],['Eureka','http://localhost:18761','Tus servicios registrados por nombre.'],['Config','http://localhost:18888/garritas-venta-ms/dev','Propiedades entregadas a Venta.'],['Keycloak','http://localhost:18180/admin/','Realm garritas, usuarios y roles efectivos.'],['Kafka UI','http://localhost:18085','Eventos y grupos del topic garritas.ventas.v1.'],['Grafana / Prometheus','http://localhost:13000 / http://localhost:19090','Panel, métricas y targets.'],['PostgreSQL propio','Venta 15441; Institución 15442','Cliente SQL, no navegador. garritas_venta_db / garritas_institucion_db.']])
b.p('Credenciales iniciales DEV: cliente / Cliente123!; administrador de tienda admin-store / Admin123!; consola Keycloak admin / local-admin-change-me; Grafana admin / local-grafana. Si se cambiaron en una base persistente, el valor actual puede ser otro. No utilizar estas credenciales de demostración para publicar una tienda real.')
b.h('PARTE IV · Diseño, letras, colores y pantallas',new=True)
b.p('Esta es la respuesta directa a “¿dónde cambiaste el diseño y las letras?”. La presentación está en Angular: HTML define la estructura, TypeScript maneja datos/acciones y CSS define cómo se ve. Las clases Java y PostgreSQL no deciden el tamaño de letra de la página.')
b.table(['Qué quieres localizar','Ruta exacta'],[['Pantalla Ventas/Mis compras','clients/garritas-frontend/src/app/features/ventas/ventas.component.html'],['Filtros, carga, detalle y descarga de PDF','clients/garritas-frontend/src/app/features/ventas/ventas.component.ts'],['Sedes: tarjetas y formulario','clients/garritas-frontend/src/app/features/sedes/sedes.component.html y .ts'],['Servicios/paquetes por sede','clients/garritas-frontend/src/app/features/prestaciones/prestaciones.component.html y .ts'],['Menú por rol, portada y navegación','clients/garritas-frontend/src/app/app.html y app.ts'],['Fuentes, colores, tamaños y responsive','clients/garritas-frontend/src/styles.css'],['Registro del CSS global','clients/garritas-frontend/angular.json → build.options.styles'],['Foto/selector reutilizable','clients/garritas-frontend/src/app/shared/image-editor.ts, resource-image.ts y media.ts']])
b.p('En esta versión los componentes comparten CSS global. No necesitas encontrar ventas.component.css: Ventas declara templateUrl y los selectores visuales se encuentran en styles.css. El selector de fotos contiene su plantilla dentro del archivo image-editor.ts.')
b.h('12. Dónde están exactamente las letras y el rosa',new=True)
css='clients/garritas-frontend/src/styles.css'
for needle,msg,n in [('font-family:','Familia de letras global. El navegador elige la primera disponible: Inter es una preferencia, no se descarga una fuente por nombrarla.',10),('font-size: 15px','Tamaño base de texto. rem se calcula a partir de ese tamaño raíz.',5),('/* Rosa pastel','Inicio del tema nuevo: fondo, variables y colores de marca. Las reglas al final pueden sustituir las anteriores.',18),('font-size: clamp(2rem','Título de portada adaptable: crece dentro de límites según el ancho de pantalla.',9),('.sales-summary','Distribución de tarjetas de resumen administrativo.',13),('app-resource-image','Presentación de la foto y su contenedor. No es el almacenamiento del archivo.',11)]:b.ref(css,needle,msg,n)
b.ref('clients/garritas-frontend/angular.json','"styles"','Angular incorpora src/styles.css al compilar. No editar el CSS con nombre hash de dist para mantener cambios.',5)
b.p('Paleta principal: rosa profundo #a92f69 para acciones sobre fondos suaves, con texto oscuro para lectura. La portada usa degradado pastel y títulos adaptables. Las tablas y botones tienen clases compartidas; una regla específica puede ganar a otra global. Un estilo inline también puede tener prioridad.')
b.p('Para demostrar un cambio pequeño, puedes añadir ejemplos como estos al final de styles.css. Son ejercicios de estudio, no cambios aplicados automáticamente por esta guía:')
b.code('''/* Solo el título de la pantalla de Ventas/Mis compras */
app-ventas h1 {
  font-size: 2rem;
  color: #91365f;
}
/* Solo los títulos de tarjetas en Sedes */
app-sedes h2 {
  font-size: 1.25rem;
}
/* Solo el panel de detalle de la compra */
app-ventas .sale-detail {
  border-radius: 20px;
}''')
b.p('Procedimiento: identifica el texto en su HTML → encuentra su clase/selector en CSS → cambia una propiedad → guarda → revisa escritorio y móvil. Con ng serve el navegador actualiza la presentación. En producción hay que compilar y desplegar la versión nueva; guardar un archivo local no actualiza una web publicada.')
b.p('Si no se aplica el color/tamaño, inspecciona el elemento con F12 y revisa Styles/Computed: allí ves qué regla gana y qué fuente se usa. Los cambios hechos únicamente en DevTools son temporales; se conservan editando el archivo fuente en VS Code. Evita cambiar node_modules, target o archivos generados para personalizar la página.')
b.h('13. Cómo funciona tu pantalla de Ventas',new=True)
b.ref(g.front('app.html'),'Ventas</button>','El botón ADMIN lleva a la vista pedidos que monta app-ventas. El cliente recibe Mis compras; el nombre visual no crea otra base ni otra API.',6)
b.ref(g.front('features/ventas/ventas.component.ts'),'export class VentasComponent','Componente separado: estado, filtros, selección, carga de venta y consulta de pago.',17)
b.ref(g.front('features/ventas/ventas.component.ts'),'readonly filtered','Combina búsqueda, estado y rango de días locales del navegador. No es la autorización: el servidor ya filtra lo que puede recibir el cliente.',18)
b.ref(g.front('features/ventas/ventas.component.ts'),'info(estado','Traduce el estado técnico a nombre y explicación comprensible.',7)
b.ref(g.front('features/ventas/ventas.component.ts'),'comprobante(venta','Solo solicita PDF para PAGADA y usa el endpoint autenticado; descarga el Blob y libera su URL temporal.',23)
b.ref(g.front('core/api.ts'),'ventas()','GET /ventas carga la misma API para ambos roles.',8)
b.ref(g.front('app.ts'),'checkout()','La compra se crea desde el carrito; conserva Idempotency-Key al reintentar. No se duplicó ese proceso dentro de la tabla de administración.',18)
b.p('Frase para defender el menú: “Antes el rótulo Mis pedidos ocultaba la responsabilidad del módulo. Ahora hay una vista administrativa Ventas y una vista del cliente Mis compras, con el mismo backend y permisos por identidad. La autorización no depende del texto del menú”.')
b.h('14. Fotos de sedes y constancia imprimible',new=True)
b.ref(g.front('features/sedes/sedes.component.html'),'app-image-editor','Selector de imagen en el formulario de sede; no hay URL que el administrador tenga que escribir manualmente.',5)
b.ref(g.front('shared/image-editor.ts'),'persist(','El editor envía la foto cuando ya existe el ID del registro. También aplica el borrado al guardar.',12)
b.ref(g.COMMON+'LocalImages.java','public void upload','Valida el contenido real, recodifica y guarda con nombre UUID. Sustituye la referencia local bajo transacción; no promete ACID entre disco y base.',18)
b.ref('services/garritas-institucion-ms/src/main/resources/db/migration/V4__imagenes.sql',None,'La referencia pertenece a la sede mediante FK local. El archivo se conserva en uploads/.',7)
b.ref(g.java('venta','service/ComprobanteService'),'public byte[] generar','El PDF se produce en Java mediante PDFBox, desde el registro autorizado y pagado; Angular no envía el importe a imprimir.',22)
b.p('Demostración PDF: CLIENTE → Mis compras → Ver detalle de una PAGADA → Descargar comprobante PDF → abrir el archivo → Imprimir. Para CANCELADA/PENDIENTE el botón no aparece y el backend responde 409 si se intenta acceder. Otro cliente no puede descargarlo. Los nombres actuales de producto/sede no se presentan como un snapshot histórico en el PDF: conserva referencias e importes de la operación.')
b.p('Una foto eliminada no elimina la sede. Un clon Git no incluye fotos subidas ni datos de compras. La carpeta uploads y PostgreSQL deben respaldarse; el modo Docker integrado tiene volúmenes. Una plataforma con disco efímero requiere almacenamiento persistente antes de publicar.')
from lectura_nikol import agregar
anotaciones = agregar(b,g)
b.h('PARTE VI · Cómo demostrar y responder al ingeniero',new=True)
b.table(['Tiempo aproximado','Acción preparada','Qué defiendes'],[['0:00–0:45','ADMIN: Sedes y oferta con un paquete. Mostrar la misma prestación en dos sedes.','Institución es maestro y posee N:M con atributos de precio/duración.'],['0:45–1:30','CLIENTE: comprar un producto, elegir entrega y confirmar una sola vez.','Venta calcula total y guarda cabecera/detalles/Outbox.'],['1:30–2:10','ADMIN: Ventas, filtros, detalle. CLIENTE: Mis compras y PDF de una pagada.','Una API por rol, seguridad por propietario y constancia desde datos persistidos.'],['2:10–3:00','Compra con TRANSFERENCIA preparada: estado y stock antes/después.','Compensación real de inventario; no camino feliz únicamente.']])
b.p('Prepara dos ventanas con sesiones distintas, datos y pantallas antes de empezar el tiempo. Elige un caso pequeño y una ruta de código clave por idea. No gastes los tres minutos recorriendo imports o instalando dependencias.')
b.p('Presentación sugerida: “Mis servicios son Venta e Institución. Institución mantiene sedes y prestaciones relacionadas mediante ofertas con precio/duración. Venta registra compras de clientes, consulta referencias, guarda cabecera y detalles y participa en la Saga con Catálogo y Pago. ADMIN supervisa desde Ventas y el cliente consulta Mis compras. Puedo demostrar una aprobación y una compensación”.')
b.table(['Pregunta probable','Respuesta defendible'],[['¿Dónde está Venta si el cliente ve compras?','Es la misma operación: cliente compra, tienda vende. El servicio independiente es garritas-venta-ms y ambas vistas usan /ventas.'],['¿Por qué sí es transaccional?','Guarda cabecera/detalles/Outbox coherentes en una base, con reglas, clave de reintento y participación en un proceso distribuido.'],['¿Institución no usa transacciones?','Sí usa transacciones locales. Se clasifica como maestro por su responsabilidad, no por ausencia de @Transactional.'],['¿Dónde está tu N:M?','SedePrestacion con dos @ManyToOne y sus FK; muestro varias prestaciones por sede y la misma en otra sede.'],['¿Quién devuelve el stock?','Catálogo. Venta entra COMPENSANDO y termina CANCELADA al recibir inventario.liberado.'],['¿Qué evita quedar esperando?','Timeout limita la llamada; Circuit Breaker de Venta evita insistir tras fallos. No todos los clientes HTTP tienen el mismo mecanismo.'],['¿Por qué seguridad en el servicio y Gateway?','Una petición directa no debe saltarse la validación JWT ni la propiedad.'],['¿Dónde están el color y las letras?','En src/styles.css; HTML aporta estructura/clases y angular.json registra ese CSS. F12 muestra la regla y fuente efectivas.'],['¿Una tabla de roles de Usuario da ADMIN?','No, el permiso efectivo procede del JWT de Keycloak.'],['¿Pago real o factura electrónica?','No: pago simulado y constancia sin validez tributaria. Mercado Pago y SUNAT no están implementados.']])
b.p('Explica con honestidad qué desarrollaste, qué integraste con ayuda y qué verificaste personalmente. Sustenta tu comprensión con código y evidencia.')
b.h('PARTE VII · Endpoints, archivos y código completo',new=True)
b.p('La tabla siguiente se extrae de los controladores reales. Las rutas /envios y /despachos son alias del mismo controlador en Venta. No cuentan como dos microservicios. Las escrituras maestras son ADMIN; confirmar compra es CLIENTE sin ADMIN; las consultas de recursos propios vuelven a comprobar dueño en el servidor.')
for domain in b.domains:
 b.h('API '+domain.capitalize(),2);rows=[]
 for p in g.TRACKED:
  if p.startswith(f'services/garritas-{domain}-ms/src/main/java/') and '/controller/' in p and p.endswith('.java'):
   text=g.read(p);m=re.search(r'@RequestMapping\((.*?)\)',text,re.S);prefixes=re.findall(r'"([^"]*)"',m[1]) if m else ['']
   for match in re.finditer(r'@(Get|Post|Put|Delete|Patch)Mapping(?:\(([^)]*)\))?',text):
    args=match[2] or '';route=next((v for v in re.findall(r'"([^"]*)"',args) if v.startswith('/')),'');line=text[:match.start()].count('\n')+1
    for pref in prefixes:rows.append([match[1].upper(),pref+route,Path(p).name+':'+str(line)])
 b.table(['Verbo','Ruta','Controlador / línea'],rows)

files=[]
for domain in b.domains:
 root=f'services/garritas-{domain}-ms/'
 files += [p for p in g.TRACKED if p.startswith(root+'src/') and Path(p).suffix in {'.java','.sql','.yml','.yaml','.properties','.xml'}]
 files += [root+'pom.xml',root+'compose-dev.yml']
 files += [f'infra/garritas-config/config-repo/garritas-{domain}-ms-{profile}.yml' for profile in ['dev','prod']]
files += [g.COMMON+n+'.java' for n in ['CurrentUser','SecurityConfiguration','ServiceClient','HttpServices','DomainErrors','Reference','Inbox','Outbox','SagaEvent','MessagingConfiguration','LocalImages']]
files += [g.java('catalogo','messaging/InventarioEvents'),g.java('pago','messaging/PagoEvents')]
files += [p for p in g.TRACKED if any(p.startswith(g.front(folder)) for folder in ['features/ventas/','features/sedes/','features/prestaciones/','features/cart/','features/envios/']) and Path(p).suffix in {'.ts','.html'}]
files += [g.front(x) for x in ['app.ts','app.html','app.config.ts','core/api.ts','core/domain-api.ts','core/auth.ts','core/interceptor.ts','core/config.ts','shared/media.ts','shared/image-editor.ts','shared/resource-image.ts']]
files += ['clients/garritas-frontend/src/styles.css','clients/garritas-frontend/angular.json','clients/garritas-frontend/public/config.dev.json','infra/garritas-config/config-repo/garritas-gateway-dev.yml']
files=sorted(set(files),key=lambda p:(0 if any(p.startswith(f'services/garritas-{d}-ms/') for d in b.domains) else 1,p))
# Los helpers agregan inventario de archivos y código íntegro numerado, con enlaces.
g.catalog(b,files);g.source_appendix(b,files)
b.h('Repaso final y forma de estudiar',new=True)
for t in ['Explico primero qué negocio resuelve Venta y qué datos mantiene Institución.','Puedo recorrer una compra de Angular a Gateway, servicio, base, Outbox y Kafka.','Ubico VentaService.crear, VentaEvents.consume y la liberación de stock en Catálogo.','Muestro una N:M persistida en SedePrestacion y una 1:N en Venta/DetalleVenta.','Distingo transacción local, compensación distribuida, idempotencia y diagnóstico por traceId.','Sé por qué ADMIN no compra y cómo se protege la consulta del cliente.','Ubico HTML, TypeScript y styles.css; puedo cambiar un título o tamaño sin tocar SQL.','Descargo una constancia PDF de una compra pagada y explico sus límites.','Conozco qué parte hice/integré y qué componentes son compartidos o de mis compañeras.']:
 b.bullet(t)
b.p('Para memorizar el recorrido usa estas seis preguntas: qué recibe, qué valida, a quién llama, qué guarda, qué devuelve y qué ocurre si falla. Lleva preparados un caso correcto y uno rechazado. No necesitas leer cada archivo entero durante la exposición; el anexo es para consultar y estudiar.')
b.p('Referencia docente: Pagatu, sesiones 1–11, https://262dist.github.io/pagatu/. Código de esta guía: '+g.REV+'. La revisión documental comprueba rutas, líneas, código reproducido y PDF; no afirma haber vuelto a ejecutar todo el proyecto ni tu PowerShell al generar este documento.')

if __name__=='__main__':
 b.save()
 (OUT/'Nikol-referencias.json').write_text(json.dumps({'commit':g.REV,'referencias':b.refs,'fuentes':b.sources,'lectura_comentada':anotaciones},ensure_ascii=False,indent=2)+'\n')
 print(b.filename,len(b.sources),'archivos completos',len(b.refs),'referencias')
