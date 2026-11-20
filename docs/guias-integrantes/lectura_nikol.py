"""Fragmentos reales con explicación al costado para la guía de Nikol."""
import textwrap
from pathlib import Path
from reportlab.platypus import Paragraph,Preformatted,Table,TableStyle,Spacer,KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors

def agregar(b,g):
    registros=[]
    b.h('PARTE V · Código a la izquierda y explicación al costado',new=True)
    b.p('Cada bloque siguiente es un fragmento REAL del repositorio, con su ruta y líneas. A la derecha se explica qué hace y por qué existe en Garritas. No es necesario memorizar imports: entiende la entrada, la regla, el efecto y el resultado. El anexo posterior conserva los archivos completos.')
    st_code=ParagraphStyle('NikolCodeCol',fontName='Code',fontSize=6.5,leading=8.5)
    st_text=ParagraphStyle('NikolExplainCol',fontName='Body',fontSize=8.5,leading=12,spaceAfter=6)
    def par(titulo,p,needle,n,explicaciones,antes=0):
        src=g.read(p).splitlines();hits=[i for i,s in enumerate(src) if needle in s];assert hits,(p,needle)
        a=max(0,hits[0]-antes);z=min(len(src),a+n)
        fragment='\n'.join(src[a:z]);numbered='\n'.join(f'{i+1:4}  {src[i]}' for i in range(a,z))
        wrapped=[]
        for line in numbered.expandtabs(2).splitlines():
            wrapped+=textwrap.wrap(line,width=57,replace_whitespace=False,drop_whitespace=False,break_long_words=True,break_on_hyphens=False,subsequent_indent='      ') or ['']
        b.h(titulo,3);b.ref(p,needle)
        left=Preformatted('\n'.join(wrapped),st_code)
        right=Paragraph('<br/><br/>'.join(g.inline(s) for s in explicaciones),st_text)
        t=Table([[Paragraph('Código real · fragmento',g.styles['Small']),Paragraph('Para qué sirve en Garritas',g.styles['Small'])],[left,right]],colWidths=[264,247],hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#f4dbe6')),('BACKGROUND',(0,1),(0,1),colors.HexColor('#fff4f8')),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#e5c4d3')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
        lead=b.items[-2:];del b.items[-2:]
        b.items += [KeepTogether([*lead,t]),Spacer(1,14)]
        b.md.append('```\n'+numbered+'\n```\n'+'\n'.join('Explicación: '+s for s in explicaciones)+'\n')
        registros.append({'titulo':titulo,'path':p,'start_line':a+1,'end_line':z,'fragmento':fragment,'explicaciones':explicaciones})
    V=lambda s:g.java('venta',s)
    I=lambda s:g.java('institucion',s)
    F=g.front
    b.h('A. Leer la estructura Java y la entrada de Venta',2)
    par('A1. La aplicación importa seguridad, eventos y Feign',V('GarritasVentaMsApplication'),'@org.springframework.context.annotation.Import',10,[
        '**@Import:** incorpora la configuración común que no está en el paquete de Venta.',
        '**SecurityConfiguration:** valida JWT y permisos. **MessagingConfiguration:** prepara Kafka.',
        '**EnableFeignClients:** habilita los contratos de llamadas declarativas. Las anotaciones Swagger documentan el esquema Bearer.'])
    par('A2. Este es el controlador REST de Venta',V('controller/VentaController'),'@RestController',7,[
        '**@RestController:** sus métodos atienden HTTP y producen una respuesta de API.',
        '**@RequestMapping:** agrupa las rutas bajo /api/v1/ventas.',
        '**private final:** dependencias inyectadas por constructor. El controlador delega al servicio; no calcula el carrito aquí.'])
    par('A3. Crear una compra: POST, DTO y clave',V('controller/VentaController'),'  @PostMapping',7,[
        '**POST:** crea una compra; **201 CREATED** es la respuesta de creación.',
        '**@Valid + @RequestBody:** recibe JSON y ejecuta las validaciones del DTO.',
        '**Idempotency-Key:** UUID obligatorio para reconocer reintentos. El servicio compara su contenido antes de reutilizar una venta.'])
    par('A4. El DTO limita sede y tipo de entrega',V('dto/VentaRequest'),'public class VentaRequest',15,[
        '**sedeId:** ID obligatorio y positivo; después el servicio comprobará que esa sede exista y esté activa.',
        '**tipoEntrega:** solo RECOJO o ENVIO. El valor inicial es recojo.',
        '**@Size / @Positive:** limitan campos. Validar el formato no sustituye comprobar referencias o cobrar la tarifa real.'])
    par('A5. Una cantidad válida no puede ser cero',V('dto/DetalleVentaRequest'),'public class DetalleVentaRequest',9,[
        '**idProducto:** referencia positiva de un producto de Catálogo.',
        '**cantidad:** entero obligatorio entre 1 y 10000 según este contrato. No se permite comprar una cantidad negativa para aumentar stock.',
        'El servidor también verifica disponibilidad: pasar la validación del DTO no garantiza que haya inventario.'])
    par('A6. Cabecera y detalles: una relación 1:N',V('entity/Venta'),'  @OneToMany',8,[
        '**mappedBy = venta:** cada detalle indica a qué venta pertenece.',
        '**cascade ALL:** guardar la cabecera propaga la persistencia de sus detalles.',
        '**LAZY:** la colección no se carga siempre por defecto. Se convierte a DTO dentro de la operación de servicio.'])
    b.h('B. Reglas que hacen consistente la compra',2)
    par('B1. La operación es localmente transaccional',V('service/VentaService'),'  public VentaResponse crear',8,[
        '**@Transactional:** protege la escritura local de la compra. Un fallo no debe confirmar solo una parte del agregado.',
        '**CurrentUser.admin():** rechaza ADMIN como comprador.',
        '**validarEntrega / subject:** comprueba entrega y toma la identidad del JWT, no un idCliente escrito por el navegador.'],antes=1)
    par('B2. Bloqueo y búsqueda de una clave ya utilizada',V('service/VentaService'),'    jdbc.queryForObject(',9,[
        '**pg_advisory_xact_lock:** serializa peticiones con la misma combinación de dueño y clave en esta base.',
        '**findByIdClienteAndIdempotencyKey:** busca el resultado anterior de esa operación.',
        'No basta generar un UUID: el mismo reintento debe conservarlo; una clave reutilizada con otros datos se rechaza más adelante.'])
    par('B3. Consultar una sede por nombre de servicio',V('service/VentaService'),'    Reference sede =',7,[
        '**services.get:** llamada HTTP a Institución mediante el cliente común.',
        '**garritas-institucion-ms:** nombre lógico para descubrimiento; no es una tabla de Venta.',
        '**activo:** si la sede no está disponible se rechaza la compra, sin aceptar una referencia falsa.'])
    par('B4. Una tarifa cambiada exige nueva confirmación',V('service/VentaService'),'      if (cobertura.tarifa().compareTo',10,[
        '**compareTo:** compara importes BigDecimal, evitando basarse en un total arbitrario del cliente.',
        '**409 CONFLICT:** la cotización cambió; Angular debe actualizar y el cliente confirmar las condiciones nuevas.',
        'Después se conserva costoEnvio y los datos acordados de la entrega dentro de Venta.'])
    par('B5. Producto, cantidad y subtotal calculado por el servidor',V('service/VentaService'),'      var producto = catalogo.obtener',12,[
        '**catalogo.obtener:** consulta el producto real.',
        '**activo / stock:** comprobación previa de elegibilidad; la reserva definitiva se decide luego en Catálogo.',
        '**precio × cantidad:** calcula el subtotal con BigDecimal y construye el detalle con el precio acordado.'])
    par('B6. Guardar y registrar venta.creada',V('service/VentaService'),'    repository.saveAndFlush(venta)',16,[
        '**saveAndFlush:** persiste la venta y sus detalles.',
        '**outbox.append:** registra el evento en la misma transacción local. No envía directamente un pago bancario.',
        '**eventId / ventaId / owner / traceId:** distinguen mensaje, agregado, propietario y correlación; no son cuatro nombres de la misma clave.'])
    par('B7. El listado también aplica el rol en el servidor',V('service/VentaService'),'  public List<VentaResponse> listar',10,[
        '**ADMIN:** recupera todas las ventas.',
        '**Cliente:** obtiene solo las del subject autenticado.',
        '**mapper + orden:** convierte a DTO y presenta las más recientes. La tabla Angular no recibe ventas ajenas para ocultarlas después.'])
    par('B8. Outbox exige una transacción activa',g.COMMON+'Outbox.java','  public void append',10,[
        '**isActualTransactionActive:** evita usar Outbox sin el límite transaccional requerido.',
        '**event.validate:** comprueba el contrato antes de persistirlo.',
        '**INSERT outbox_event:** guarda el mensaje con los datos locales. Un publicador posterior lo enviará a Kafka.'])
    par('B9. Feign más Circuit Breaker no inventa stock',V('client/CatalogoConsulta'),'        .create("catalogo")',11,[
        '**create(catalogo):** utiliza el circuito configurado para esa dependencia.',
        '**run:** ejecuta la consulta o maneja su fallo. Un producto inexistente y un servicio no disponible se distinguen.',
        'El fallback es un error controlado; no devuelve un producto ficticio para seguir vendiendo.'])
    b.h('C. Eventos, compensación y comprobante',2)
    par('C1. Filtrar eventos y deduplicar consumo',V('messaging/VentaEvents'),'    if (!java.util.Set.of(',11,[
        'Solo procesa los tipos de inventario/pago que le corresponden; otros eventos se ignoran.',
        '**inbox.claim:** evita repetir el mismo eventId en una transacción confirmada.',
        'El estado previo y las restricciones del negocio aportan protección adicional frente a repeticiones semánticas.'])
    par('C2. La transición SQL comprueba el estado anterior',V('messaging/VentaEvents'),'      int changed =',12,[
        '**WHERE id AND estado:** aplica la transición solo si la venta sigue en el estado esperado.',
        '**changed == 1:** un cambio realmente aplicado puede desencadenar el despacho.',
        'El INSERT usa datos de una venta ENVIO ya pagada. No crea un delivery gratuito para un recojo.'])
    par('C3. La reserva solo se libera una vez (Catálogo)',g.java('catalogo','messaging/InventarioEvents'),'  private void liberar',17,[
        '**Código de colaboración de Catálogo:** la devolución del stock sucede aquí, no escribiendo desde Venta otra base.',
        '**FOR UPDATE / RESERVADA:** bloquea la reserva y verifica que aún pueda liberarse.',
        '**stock + cantidad:** devuelve unidades originales; luego marca LIBERADA y añade inventario.liberado al Outbox.'])
    par('C4. El PDF comprueba identidad y estado antes de crearse',V('service/ComprobanteService'),'  public byte[] generar',12,[
        '**ventas.obtener:** reutiliza el control de propietario/ADMIN.',
        '**PAGADA:** si no está confirmada, responde conflicto en vez de emitir una constancia engañosa.',
        '**lines:** prepara contenido desde datos persistidos. Declara pago simulado y ausencia de validez tributaria.'])
    b.h('D. Institución: CRUD, relación y ofertas',2)
    par('D1. Sedes visibles según disponibilidad y rol',I('service/SedeService'),'  public List<SedeResponse> listar',9,[
        '**findAll:** obtiene entidades de la base propia.',
        '**filter:** ADMIN puede ver todas; un cliente consulta activas.',
        '**sorted y mapper:** ordena por ciudad/nombre y prepara una respuesta de API, sin exponer directamente JPA.'])
    par('D2. Crear y actualizar una sede son operaciones distintas',I('service/SedeService'),'  public SedeResponse crear',16,[
        '**crear:** convierte el DTO y guarda un registro nuevo.',
        '**actualizar:** busca por ID y cambia nombre, dirección, ciudad, teléfono y activo.',
        'La identidad de una sede se mantiene al editar: no se crea otra para cada cambio.'])
    par('D3. Eliminar es una baja lógica',I('service/SedeService'),'  public void eliminar',5,[
        '**buscarOFallar:** no acepta un ID inexistente como éxito.',
        '**setActivo(false):** desactiva la sede, conserva la fila y el historial.',
        'El verbo HTTP DELETE no obliga a borrar físicamente una tabla.'])
    par('D4. Dos relaciones N:1 forman tu N:M con atributos',I('entity/SedePrestacion'),'  @ManyToOne',18,[
        '**id_sede e id_prestacion:** claves foráneas locales hacia los dos lados de la asociación.',
        '**precio / duracionMinutos / activo:** condiciones de esa pareja concreta.',
        'Una sede puede aparecer en muchas filas y una prestación también: así se representa la N:M.'])
    par('D5. La oferta no duplica la pareja sede/prestación',I('service/PrestacionService'),'    SedePrestacion o =',12,[
        '**findBySedeIdAndPrestacionId:** recupera la asociación si ya existe.',
        '**orElseGet:** crea una solo cuando falta.',
        '**setPrecio / setDuracion:** actualiza las condiciones de esa sede; saveAndFlush conserva el resultado.'])
    par('D6. Un paquete contiene prestaciones individuales',I('entity/Prestacion'),'  @ManyToMany',7,[
        '**prestacion_componentes:** tabla intermedia de una asociación autorreferente.',
        '**id_paquete / id_componente:** el mismo tipo Prestacion cumple dos papeles.',
        'La entidad expresa la relación; PrestacionService impide anidamientos y componentes inválidos.'])
    par('D7. Bloquear cambios del grafo evita carreras entre paquetes',I('service/PrestacionService'),'    jdbc.queryForObject(',15,[
        '**garritas:paquetes:** clave de bloqueo de las ediciones del grafo en esta base.',
        '**componentes:** se exige un conjunto válido y no incluir el propio paquete.',
        'La comprobación posterior exige servicios individuales activos y evita paquetes dentro de paquetes.'])
    b.h('E. Angular, diseño y seguridad: lo que se ve en pantalla',2)
    par('E1. El botón Ventas solo aparece en la sección ADMIN',F('app.html'),'ADMINISTRACIÓN</p>',5,[
        '**auth.admin():** la sección que contiene este bloque se presenta al administrador.',
        '**view.set(pedidos):** cambia la vista de Angular; no crea otra venta ni otra API.',
        '**class.selected:** da estilo al botón activo. La autorización real sigue en el servidor.'])
    par('E2. Los filtros son valores derivados de las ventas autorizadas',F('features/ventas/ventas.component.ts'),'  readonly filtered = computed',17,[
        '**computed:** recalcula al cambiar las señales de búsqueda/estado/fechas.',
        '**filter:** reduce la colección que devolvió el servidor.',
        'No reemplaza permisos: el endpoint ya entrega al cliente únicamente sus compras.'])
    par('E3. Un Blob permite descargar el PDF del backend',F('features/ventas/ventas.component.ts'),'          const url = URL.createObjectURL',12,[
        '**createObjectURL:** crea una referencia temporal al archivo recibido.',
        '**anchor.download / click:** inicia la descarga con un nombre reconocible.',
        '**revokeObjectURL:** libera la referencia después. El usuario abre el PDF y lo imprime; el navegador no calcula el comprobante.'])
    par('E4. Seleccionar una foto no obliga a escribir su URL',F('shared/image-editor.ts'),'  persist(id:',12,[
        '**file / removed:** decide si subir, borrar o conservar la foto.',
        '**persist(id):** espera un ID real del registro. Se aplica al guardar el formulario.',
        '**reset:** limpia la selección tras el éxito. Si la foto falla al crear, el padre conserva el ID y no duplica el registro al reintentar.'])
    par('E5. La familia de letras y el tamaño base', 'clients/garritas-frontend/src/styles.css','  font-family:',13,[
        '**font-family:** lista de preferencia; usa la primera fuente disponible en el equipo.',
        '**font-size: 15px:** tamaño raíz. Una medida rem se calcula a partir de este valor.',
        '**line-height:** distancia de líneas. Estas propiedades son presentación, no datos de PostgreSQL.'])
    par('E6. Los colores rosa son reglas CSS', 'clients/garritas-frontend/src/styles.css','/* Rosa pastel',16,[
        '**color / background:** texto y fondo global.',
        '**--rose:** variable reutilizable por botones; cambiarla modifica los lugares que la consumen.',
        'La cascada importa: entre reglas con igual prioridad puede ganar la posterior; revisa también selectores específicos e inline.'])
    par('E7. El título de portada se adapta al tamaño de pantalla','clients/garritas-frontend/src/styles.css','  font-size: clamp(2rem',7,[
        '**clamp:** define mínimo, valor adaptable y máximo de tamaño de letra.',
        '**line-height y max-width:** controlan lectura y ancho del título.',
        'No hay que cambiar Java para ampliar un título: se modifica este estilo y se comprueba en móvil y escritorio.'])
    par('E8. Propiedad del recurso: no basta ocultar un botón',g.COMMON+'CurrentUser.java','  public static void requireOwner',4,[
        '**owner:** identidad persistida del dueño.',
        '**subject():** identidad del JWT autenticado.',
        'Si no es ADMIN y no coincide con el dueño, el backend rechaza el acceso, aunque se llame directamente a la API.'])
    b.p('Para contestar frente a cada bloque: “Esta instrucción hace X; la usamos para proteger o representar Y; recibe Z; si no se cumple la regla responde/error W”. El anexo permite ampliar el contexto sin atribuir a un fragmento aislado más de lo que realmente implementa.')
    return registros
