"""Dos guías de defensa con código completo, rutas y referencias fijadas a Git.
Requiere reportlab, PyMuPDF y Graphviz. No modifica el código de la aplicación.
"""
from pathlib import Path
import subprocess,re,json,hashlib,textwrap,ast
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Preformatted,Image,Table,TableStyle
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
REV='6e2239c55884c2a6ae53dd921147d9e5b53749ab'
URL=f'https://github.com/Nikol235/Garritas-Store/blob/{REV}/'
TRACKED=subprocess.check_output(['git','ls-tree','-r','--name-only',REV],cwd=ROOT,text=True).splitlines()
CACHE={};REFS={};CONTENTS={};SOURCES={}
def read(p):
 if p not in CACHE:CACHE[p]=subprocess.check_output(['git','show',f'{REV}:{p}'],cwd=ROOT,text=True)
 return CACHE[p]
def java(domain,suffix):return f'services/garritas-{domain}-ms/src/main/java/pe/edu/upeu/garritas/{domain}/{suffix}.java'
def front(p):return 'clients/garritas-frontend/src/app/'+p
COMMON='infra/garritas-common/src/main/java/pe/edu/upeu/garritas/common/'
for n,f in [('Body','DejaVuSans.ttf'),('Bold','DejaVuSans-Bold.ttf'),('Code','DejaVuSansMono.ttf')]:pdfmetrics.registerFont(TTFont(n,'/usr/share/fonts/truetype/dejavu/'+f))
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Text',fontName='Body',fontSize=9.2,leading=14,spaceAfter=8))
styles.add(ParagraphStyle(name='Small',fontName='Body',fontSize=7.5,leading=10.5,spaceAfter=5,wordWrap='CJK'))
styles.add(ParagraphStyle(name='CodeBlock',fontName='Code',fontSize=6.9,leading=9.1,backColor=colors.HexColor('#fff2f7'),borderPadding=5,spaceAfter=10))
for i,size in [(1,18),(2,12.5),(3,10)]:
 s=styles[f'Heading{i}'];s.fontName='Bold';s.fontSize=size;s.leading=size+5;s.textColor=colors.HexColor('#91365f');s.spaceBefore=12;s.spaceAfter=8;s.keepWithNext=True
styles.add(ParagraphStyle(name='CoverTitle',fontName='Bold',fontSize=29,leading=36,textColor=colors.HexColor('#91365f'),spaceAfter=22))
def inline(t):
 t=escape(str(t));t=re.sub(r'`([^`]+)`',r'<font name="Code" size="8">\1</font>',t)
 return re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',t)
class SourceCode(Preformatted):
 def split(self,width,height):
  count=int(height/self.style.leading)
  if count<4:return []
  if 0<len(self.lines)-count<8:count=max(0,len(self.lines)-8)
  if count<4:return []
  return [SourceCode('\n'.join(self.lines[:count]),self.style),SourceCode('\n'.join(self.lines[count:]),self.style)]
class Doc(SimpleDocTemplate):
 def afterFlowable(self,f):
  if isinstance(f,Paragraph) and f.style.name in ('Heading1','Heading2'):
   level=0 if f.style.name=='Heading1' else 1;key='h'+str(self.seq.nextf('h'))
   self.canv.bookmarkPage(key);self.canv.addOutlineEntry(f.getPlainText()[:200],key,level,False);self.notify('TOCEntry',(level,f.getPlainText(),self.page,key))
def footer(c,d):
 c.saveState();c.setStrokeColor(colors.HexColor('#edc8d9'));c.line(42,39,A4[0]-42,39);c.setFont('Body',7);c.setFillColor(colors.HexColor('#745368'));c.drawString(42,26,d.title);c.drawRightString(A4[0]-42,26,str(d.page));c.restoreState()
# Diccionario previo reutilizado como texto, sin ejecutar sus generadores.
SPECIAL={}
for n in ast.parse((ROOT/'docs/manuales/fuentes/generar.py').read_text()).body:
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SPECIAL' for t in n.targets):SPECIAL=ast.literal_eval(n.value)
EXPLAIN={
'ProductoService':'Administra productos: listar/listarPaginado consultan, crear registra y cuenta la métrica, actualizar cambia campos/categorías y eliminar DESACTIVA. asignarCategoriasDesdeRequest resuelve los IDs y rechaza categorías inexistentes; mantiene una categoría principal de compatibilidad.',
'InventarioEvents':'Consumidor Kafka de Catálogo. consume filtra eventos y aplica Inbox; reservar valida todo el pedido y bloquea productos antes de descontar; liberar solo devuelve una reserva RESERVADA y publica inventario.liberado. No llama a un banco.',
'UsuarioService':'Mantiene perfil, búsquedas administrativas y roles internos. guardarMe toma el sub de SecurityContext, normaliza el correo y evita apropiarse de un perfil por coincidencia de email. miUsuario enlaza la identidad real con datos locales. Elimina solo perfiles no vinculados a una cuenta.',
'SuscripcionService':'Operación transaccional local: contratar crea cabecera y primer período; renovar actualiza vencimiento y añade período al precio vigente; cancelar marca CANCELADA. lock serializa por usuario/clave; un reintento compatible devuelve el resultado existente.',
'MascotaService':'Guarda mascotas de un perfil y verifica propiedad. buscarOFallar llama a CurrentUser.requireOwner; verificarUsuario evita mezclar una mascota con otro perfil. Edad entera con unidad DIAS/MESES, no años decimales.',
'CitaService':'Reserva cita con detalles: consulta mascota propia, sede, profesional y ofertas; evita servicios duplicados, calcula duración/precio, bloquea por profesional y comprueba intervalos solapados. confirmar/atender/cancelar aplican transiciones y propiedad.',
'LogisticaService':'Maestro logístico: transportistas, zonas y su cobertura N:M. guardarCobertura crea/actualiza la pareja con tarifa y plazo; exige padres activos. Las bajas desactivan. La respuesta solo considera activa la cobertura cuando también lo están sus dos padres.',
'ImagenController':'Expone GET/PUT/DELETE de la imagen del producto. Delega en LocalImages; PUT recibe multipart archivo. La seguridad exige ADMIN para modificar; GET público permite mostrar el catálogo.',
'LocalImages':'Valida JPG/PNG reales, tamaño y dimensiones, recodifica, crea nombre UUID y guarda referencia SQL local. Sustituye sin sobreescribir el archivo anterior; limpia según commit/rollback. No es almacenamiento de Supabase ni una transacción ACID de disco más base.',
'ComprobanteService':'Referencia externa a las asignaciones: genera constancia PDF para una venta PAGADA y autorizada. Pago sigue simulado. No es factura/boleta SUNAT.',
}
def describe(p):
 name=Path(p).stem;t=read(p)
 if name in EXPLAIN:return EXPLAIN[name]
 if name in SPECIAL:return SPECIAL[name]
 if name.endswith('Application'):return 'Entrada Spring Boot del dominio. main inicia el contexto; revisa @Import para identificar seguridad/comunicación compartida. El nombre de aplicación se obtiene de application.yml y decide qué propiedades recibe de Config.'
 if name.endswith('Controller'):return 'Adaptador HTTP: mappings definen las operaciones reales; recibe DTO con @Valid y delega al servicio. No se deben atribuir endpoints que no aparecen en este archivo; los permisos se completan en SecurityConfiguration.'
 if name.endswith('Repository'):return 'Persistencia Spring Data: interfaz de entidad/clave, consultas y bloqueos. Spring genera su implementación; no es necesario escribir una clase implementadora. Leer junto a su entidad y migraciones.'
 if name.endswith('Mapper'):return 'Conversión entre entidad y DTO. Evita exponer el grafo JPA completo. Lee qué campos copia y qué valores iniciales asigna; no sustituye reglas de negocio ni controles de propiedad.'
 if '/entity/' in p:return 'Modelo JPA local. Sus campos representan datos persistidos; @ManyToOne/@OneToMany/@ManyToMany declaran relaciones entre tablas de ESTA base. Los IDs de otros servicios son referencias remotas, no claves foráneas distribuidas.'
 if '/dto/' in p:return 'Contrato de API: Request es entrada y Response salida. Las anotaciones de validación restringen campos; los record también representan contratos inmutables. No confundir DTO con tabla.'
 if '/src/test/' in p or '.spec.' in p:return 'Prueba: identifica preparación, acción y aserciones. Demuestra los escenarios que realmente ejecuta, no todos los fallos posibles del sistema.'
 if p.endswith('.sql'):return 'Flyway: V crea/evoluciona una vez en orden; R se repite cuando cambia. Las migraciones posteriores completan el esquema. No deducir el modelo final leyendo solo V1.'
 if p.endswith('pom.xml'):return 'Dependencias y configuración Maven del módulo: Java 21, starters, JAR común y plugins. La biblioteca común se llama garritas-distributed aunque su carpeta sea garritas-common.'
 if Path(p).suffix in ('.yml','.yaml'):return 'Configuración del proceso: puerto, conexión propia, seguridad, descubrimiento y/o métricas según sus claves. No es una clase Java ni una tabla.'
 if p.endswith('.ts'):return 'Código Angular: estado con signals, formularios, llamadas HTTP o componentes reutilizables. La plantilla HTML presenta el estado; la autorización efectiva sigue en el servidor.'
 if p.endswith('.html'):return 'Plantilla Angular: campos, tablas, condiciones por rol y eventos que llaman al TypeScript. Cambiar el texto de un botón no cambia el permiso del backend.'
 return 'Archivo de soporte de esta capacidad. El listado completo del anexo permite ubicar su uso en el proyecto real.'
class Book:
 def __init__(self,who,domains,filename):
  self.who=who;self.domains=domains;self.filename=filename;self.items=[];self.md=[];self.refs=[];self.sources=[]
  self.items += [Spacer(1,70),Paragraph('GARRITAS STORE · ESTUDIAR Y DEFENDER',styles['Small']),Paragraph(who,styles['CoverTitle']),Paragraph(' + '.join({'catalogo':'Catálogo','usuario':'Usuario','citas':'Citas','envio':'Envío'}[d] for d in domains),styles['Heading1']),Paragraph('Qué hace cada microservicio, cómo se conecta y dónde encontrar su código.',styles['Text']),Spacer(1,16),Paragraph('Primero: explicación y guion de demostración. Después: catálogo de archivos y código completo para consultar.',styles['Text']),Paragraph('Repositorio: Nikol235/Garritas-Store · rama main',styles['Small']),Paragraph('Versión analizada: '+REV,styles['Small']),Paragraph('Edición de estudio: 20 de noviembre de 2026 · código Java 21 y Angular 22.',styles['Small']),PageBreak()]
  toc=TableOfContents();toc.levelStyles=[ParagraphStyle('TOC0',fontName='Body',fontSize=8,leading=10.5,spaceBefore=2),ParagraphStyle('TOC1',fontName='Body',fontSize=7,leading=8.5,leftIndent=12)]
  self.items += [Paragraph('Índice navegable',styles['Heading1']),toc]
 def h(self,t,level=1,new=False):
  if new:self.items.append(PageBreak())
  self.items.append(Paragraph(escape(t),styles[f'Heading{level}']));self.md.append('\n'+'#'*level+' '+t+'\n')
 def p(self,t):self.items.append(Paragraph(inline(t),styles['Text']));self.md.append(t+'\n')
 def bullet(self,t):self.items.append(Paragraph('• '+inline(t),styles['Text']));self.md.append('- '+t+'\n')
 def table(self,headers,rows):
  vals=[[Paragraph(inline(x),styles['Small']) for x in row] for row in [headers,*rows]]
  t=Table(vals,colWidths=[511/len(headers)]*len(headers),repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#f9e3ed')),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#e7ced9')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]));self.items+=[t,Spacer(1,9)];self.md+=[' | '.join(headers),'\n'.join(' | '.join(map(str,r)) for r in rows)]
 def code(self,text):
  lines=[]
  for line in text.expandtabs(2).splitlines():lines+=textwrap.wrap(line,width=113,replace_whitespace=False,drop_whitespace=False,break_long_words=True,break_on_hyphens=False,subsequent_indent='     ') or ['']
  # Preformatted puede partirse naturalmente entre páginas sin numeración inventada.
  self.items.append(SourceCode('\n'.join(lines),styles['CodeBlock']));self.md.append('```\n'+text+'\n```\n')
 def ref(self,p,needle=None,explain=None,excerpt=0):
  text=read(p);hits=[i for i,line in enumerate(text.splitlines(),1) if needle is None or needle in line];assert hits,(p,needle)
  line=hits[0];self.refs.append({'path':p,'line':line,'needle':needle,'url':URL+p+f'#L{line}'})
  self.items.append(Paragraph(f'<link href="{URL+p}#L{line}" color="#006b80">{escape(p)} · línea {line}</link>',styles['Small']));self.md.append(p+f':{line}\n')
  if explain:self.p(explain)
  if excerpt:
   src=text.splitlines();lo=max(0,line-2);hi=min(len(src),line+excerpt);self.code('\n'.join(f'{i+1:4}  {src[i]}' for i in range(lo,hi)))
 def diagram(self,name,body,caption):
  out=OUT/'diagramas';out.mkdir(exist_ok=True)
  dot='digraph G {graph [bgcolor="white",fontname="DejaVu Sans",pad="0.2",nodesep="0.3",ranksep="0.45"];node [shape=box,style="rounded,filled",fillcolor="#fff0f6",color="#a94e79",fontname="DejaVu Sans",fontsize=11];edge [fontname="DejaVu Sans",fontsize=9,color="#69445b"];'+body+'}'
  (out/(name+'.dot')).write_text(dot)
  for ext in ['png','svg']:subprocess.run(['dot','-T'+ext,str(out/(name+'.dot')),'-o',str(out/(name+'.'+ext))],check=True)
  from PIL import Image as PI
  p=out/(name+'.png');w,h=PI.open(p).size;scale=min(511/w,510/h)
  self.items.extend([Image(str(p),width=w*scale,height=h*scale),Paragraph(inline(caption),styles['Small'])]);self.md.append(f'![{caption}](diagramas/{name}.png)\n')
 def save(self):
  doc=Doc(str(OUT/self.filename),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=42,bottomMargin=51,title='Garritas · '+self.who,author='Garritas Store')
  doc.multiBuild(self.items,onFirstPage=footer,onLaterPages=footer)
  stem=Path(self.filename).stem
  (OUT/(stem+'.md')).write_text('\n'.join(line.rstrip() for line in '\n'.join(self.md).splitlines()).rstrip()+'\n')
  REFS[self.who]=self.refs;SOURCES[self.who]=self.sources

def common_intro(b):
 b.h('1. Cómo estudiar y qué te corresponde',new=True)
 b.p('Esta guía describe el código de la versión indicada, no funcionalidades futuras. Lee primero los capítulos de explicación; usa el índice y Ctrl+F para localizar una clase. El anexo reproduce el código de tus dominios y sus pantallas. Las líneas y enlaces corresponden al commit analizado.')
 b.p('Estado vigente: los pagos de compra son simulados. TRANSFERENCIA representa un rechazo didáctico; seleccionar YAPE no realiza un depósito real. Mercado Pago todavía no está conectado. Las suscripciones guardan períodos e importes, pero no realizan cobros bancarios.')
 b.p('En VS Code abre la carpeta raíz Garritas-Store. Presiona Ctrl+P y pega una ruta completa. Ctrl+G lleva a una línea; Ctrl+Shift+F busca un nombre en todo el proyecto. En el PDF puedes pulsar las rutas para abrir GitHub en la línea citada.')
 b.p('Defender no consiste en memorizar todas las líneas. Debes seguir una operación desde Angular hasta la base, identificar sus reglas y explicar qué sucede si falla. Diferencia lo que implementaste personalmente de lo que integraste con el equipo o con ayuda.')
 b.table(['Idea','Explicación sencilla'],[['Microservicio','Aplicación independiente con responsabilidad, puerto y base propios. No equivale a una pestaña Angular.'],['Maestro / no transaccional','Administra datos de referencia. Puede usar transacciones SQL locales; la etiqueta académica no significa ausencia de @Transactional.'],['Transaccional','Opera un proceso de negocio con datos que deben quedar coherentes: reserva, contratación o compra.'],['Relación N:M','Cada elemento de ambos lados puede asociarse a varios del otro. Se materializa con una tabla de unión; puede tener entidad propia.'],['Relación 1:N','Una cabecera o propietario tiene varios detalles o elementos.'],['Referencia remota','Un ID de otra base, validado por API; no una FK entre PostgreSQL de servicios distintos.']])
 b.h('2. Cómo leer una clase Java sin perderte',new=True)
 b.table(['Elemento','Qué decir al mostrarlo'],[['package e import','Ubican la clase e incorporan los tipos utilizados; no realizan una llamada remota por existir.'],['@SpringBootApplication / main','Arranca el contexto y registra componentes del paquete. @Import añade configuración común.'],['@RestController / Mapping','Declaran rutas y verbos HTTP. El controlador recibe, valida y delega.'],['@Service / constructor','Concentra reglas. @RequiredArgsConstructor genera el constructor para inyectar campos final.'],['Repository','Interfaz Spring Data; su implementación se genera al iniciar. Las consultas y bloqueos son parte de la consistencia.'],['@Entity, @Table, @Id','Mapean clase, tabla e identidad local. Flyway crea el esquema real.'],['DTO / mapper','El contrato HTTP no es la entidad. El mapper traduce campos entre ambos.'],['@Transactional','Define commit/rollback de una base local. No convierte llamadas HTTP o Kafka en una única transacción global.'],['@Valid y constraints','Validan entradas; las reglas que cruzan recursos se comprueban en servicios.'],['signal / computed / subscribe','Angular almacena estado, deriva valores y recibe respuestas HTTP asíncronas.']])
 b.p('Ejemplo verbal: “Este controlador recibe el Request; @Valid comprueba sus campos; el servicio aplica reglas; el repositorio escribe; el mapper devuelve un Response. La autorización se comprueba también antes de llegar al controlador”.')

 b.h('2.1. Diccionario de campos para explicar el código',new=True)
 b.table(['Campo o tipo','Cómo interpretarlo'],[['id / Long','Identificador numérico de una fila local. No es la contraseña ni el sub de Keycloak.'],['subject / idCliente','Identidad del JWT: String. Permite comprobar quién posee el recurso.'],['idMascota, idSede, idProducto, prestacionId','Referencia a otro registro. Mira la migración para saber si es FK local o un ID remoto validado por API.'],['BigDecimal / NUMERIC','Importes exactos en el backend/base. El total del navegador es una vista previa, no la autoridad.'],['activo','Disponibilidad o baja lógica. Puede depender también del estado de los padres.'],['estado','Etapa del proceso; no se cambia libremente a cualquier cadena. Las transiciones están en el servicio/consumidor.'],['Instant / fechaInicio / fechaFin','Momento y vigencia. El navegador puede mostrar la zona local; la API no debe confundir fecha con texto visual.'],['version / @Version','Control optimista para detectar modificaciones concurrentes de la misma entidad. No es la versión del proyecto Maven.'],['idempotencyKey','Identifica una operación reintentada; se conserva para repetir la misma petición y cambia para una operación nueva.'],['eventId','Identifica un evento para Inbox. Una repetición semántica puede tener otro eventId y requiere además unicidad de negocio.'],['traceId / X-Trace-ID','Correlación para diagnóstico entre logs; no sustituye autenticación ni deduplicación.'],['Request / Response / record','Datos que acepta o devuelve la API. Un record no es automáticamente una tabla.']])
 b.p('Al explicar una colección, indica qué guarda y cómo se relaciona: categorias, roles, detalles o periodos. “Es una lista” describe el tipo; “son las prestaciones acordadas de esta cita” explica el negocio.')

def shared(b):
 b.h('Seguridad, configuración y diagnóstico que debes conocer',new=True)
 b.p('Angular inicia sesión en Keycloak con Authorization Code + PKCE. El JWT vive en memoria. Un interceptor lo agrega a la API del Gateway. Gateway y cada microservicio validan firma, issuer y audiencia; los permisos efectivos proceden de realm_access.roles. El sub es una cadena, no el id numérico de una tabla local.')
 for p,needle,msg in [(front('core/auth.ts'),'pkceMethod','Login, renovación y consulta de roles en Angular.'),(front('core/interceptor.ts'),'Authorization','Token solo para la API propia.'),(COMMON+'SecurityConfiguration.java','SecurityFilterChain','Rutas públicas, ADMIN y operaciones del propietario.'),(COMMON+'CurrentUser.java','requireOwner','Comparación entre dueño persistido y sub del autenticado.'),(COMMON+'ServiceClient.java','public','Cliente HTTP común con descubrimiento, token, correlación y espera acotada.')]:b.ref(p,needle,msg,5)
 b.p('Eureka publica instancias; Gateway distribuye peticiones; Config Server entrega propiedades DEV/PROD. Feign aparece en Venta para Catálogo/Logística. No afirmes que Citas usa Feign: su código utiliza ServiceClient. Un timeout acota una llamada; Circuit Breaker recuerda fallos de varias llamadas y rechaza rápido mientras está abierto.')
 b.table(['Herramienta','Cómo usarla en tu defensa'],[['Eureka · 18761','Mostrar el nombre de tus dos servicios registrado. No demuestra por sí solo su lógica de negocio.'],['Swagger · puerto del servicio /swagger-ui.html','Mostrar endpoints reales y DTO. Una ruta protegida necesita JWT válido.'],['Actuator · /actuator/health/readiness','Comprobar disponibilidad configurada; no sustituye una compra/cita real.'],['Prometheus · 19090','Consulta up{job="garritas-microservicios"}; /targets ayuda a detectar scrape fallido.'],['Grafana · 13000','Dashboard Garritas - Infraestructura: instancias, tráfico, conexiones y logs.'],['Loki / X-Trace-ID','Correlacionar logs de una operación. No equivale a trazas OpenTelemetry completas.'],['Kafka UI · 18085','Observar topic/eventos/grupos cuando el flujo participa realmente en Kafka.']])
 b.p('No enseñes tokens privados, contraseñas personales ni credenciales productivas. Los accesos de laboratorio están en el README; cliente/Cliente123! y admin-store/Admin123! sirven solo en DEV si no se modificaron.')
fio=Book('Fio',['catalogo','usuario'],'Fio-Catalogo-y-Usuario.pdf');common_intro(fio)
fio.h('3. Tu mapa: Catálogo y Usuario',new=True)
fio.table(['Servicio','Responsabilidad','Defensa principal'],[['Catálogo · 8085 / PG 15445','Productos, categorías, imágenes e inventario.','Maestro del catálogo; N:M producto/categoría. Además participa transaccionalmente en la Saga.'],['Usuario · 8086 / PG 15446','Perfil, mascotas, roles internos, planes, suscripciones y períodos.','Suscripciones: operación transaccional local. Usuario no reemplaza el login de Keycloak.']])
fio.diagram('fio-conexiones','''rankdir=TB; a[label="Angular"];g[label="Gateway"];k[label="Keycloak"];c[label="Catálogo 8085"];u[label="Usuario 8086"];pc[label="PostgreSQL Catálogo\n15445"];pu[label="PostgreSQL Usuario\n15446"];v[label="Venta"];q[label="Kafka"];ct[label="Citas"];a->k[label="login / JWT"];a->g[label="API + JWT"];g->c;g->u;c->pc;u->pu;v->c[label="consulta Feign"];v->q[label="eventos"];q->c[label="reserva / compensación"];c->q[label="resultado inventario"];ct->u[label="mascota propia / HTTP"];''','Los datos de Catálogo y Usuario viven en bases diferentes. Usuario no consume eventos de la Saga de compra en esta versión.')
fio.h('4. Catálogo: sigue un CRUD de producto',new=True)
fio.p('Cuando ADMIN guarda un producto, Angular envía nombre, descripción, precio, stock, estado y categorías. Gateway autoriza la escritura y reenvía a Catálogo. El servicio resuelve los IDs, actualiza la entidad y devuelve un DTO. El cliente consulta los productos, pero no puede modificar sus precios con una petición directa.')
for suffix,needle,msg in [('controller/ProductoController','public class ProductoController','Primero muestra los mappings y la diferencia entre lista completa y consulta paginada.'),('dto/ProductoRequest','public class ProductoRequest','Explica las restricciones de precio, cantidad y categorías que acepta la API.'),('service/ProductoService','public ProductoResponse crear','Crear: mapper, categorías válidas, persistencia y contador de productos creados.'),('service/ProductoService','public ProductoResponse actualizar','Actualizar: modifica los campos de un producto existente. El stock administrativo es un ajuste de inventario, no una venta.'),('service/ProductoService','public void eliminar','Eliminar en esta API desactiva el producto para preservar historial y reservas.'),('repository/ProductoRepository','public interface','Las búsquedas y el grafo/carga de categorías evitan perder asociaciones al responder.'),('mapper/ProductoMapper','public','La conversión define qué propiedades ven Angular y Venta.')]:fio.ref(java('catalogo',suffix),needle,msg,7)
fio.p('No confundas precio actual del producto con el precio acordado de una venta antigua. Venta guarda su detalle. Cambiar el maestro no debe reescribir importes históricos. El borrado lógico tampoco debe destruir la referencia de compras existentes.')
fio.h('5. Catálogo: dónde está la relación muchos a muchos',new=True)
fio.diagram('fio-relaciones','''rankdir=LR;p[label="productos"];j[label="producto_categoria\nFK producto + FK categoría"];c[label="categorias"];p->j[label="1:N"];c->j[label="1:N"];u[label="usuarios"];s[label="suscripciones"];pl[label="planes"];per[label="suscripcion_periodos"];m[label="mascotas"];u->s[label="1:N"];pl->s[label="1:N"];s->per[label="1:N"];u->m[label="1:N"];''','Producto ↔ categoría es N:M. Usuario ↔ plan se representa por suscripciones, que además contienen períodos de negocio. Ver los nombres SQL exactos en las migraciones reproducidas.')
fio.ref(java('catalogo','entity/Producto'),'@ManyToMany','El conjunto de categorías se mapea con una tabla de unión.',12)
fio.ref(java('catalogo','service/ProductoService'),'private void asignarCategoriasDesdeRequest','El servicio comprueba que cada ID seleccionado exista. Una categoría principal se mantiene por compatibilidad, sin eliminar las demás asociaciones.',14)
fio.ref('services/garritas-catalogo-ms/src/main/resources/db/migration/V5__producto_categorias_many_to_many.sql',None,'La tabla intermedia y sus restricciones son la evidencia SQL, además de la anotación Java.',10)
fio.p('Demostración: como ADMIN asigna dos categorías a un producto, guarda y vuelve a editarlo. Como cliente filtra por cada categoría y verifica que aparezca en ambas. Frase: “No dupliqué el producto; guardé dos asociaciones en la tabla intermedia”.')
fio.h('6. Inventario: la parte transaccional de Catálogo',new=True)
fio.ref(java('catalogo','messaging/InventarioEvents'),'public void consume','consume recibe JSON, filtra venta.creada/pago.fallido y registra Inbox dentro de la transacción.',12)
fio.ref(java('catalogo','messaging/InventarioEvents'),'private void reservar','Se crea una reserva única por venta y se agrupan cantidades. Los productos se bloquean en orden determinista; primero se validan todos y después se descuenta.',28)
fio.ref(java('catalogo','messaging/InventarioEvents'),'private void liberar','Compensación: solo RESERVADA puede pasar a LIBERADA. Se devuelven las cantidades originales y se registra inventario.liberado en Outbox.',23)
fio.p('Hay dos niveles de protección: Inbox deduplica eventId; reservas_stock, única por venta, evita repetir el efecto aunque se reproduzca la misma operación con otro eventId. El versionado del producto se incrementa al modificar stock.')
fio.p('Outbox persiste el evento junto al cambio local. El publicador puede repetirlo si falla después de enviar y antes de marcarlo; por eso se habla de entrega al menos una vez. No prometas exactamente una vez de extremo a extremo.')
fio.table(['Caso','Qué explicar'],[['Pago rechaza después de reservar','Sí hay compensación: Catálogo devuelve inventario. Venta espera inventario.liberado antes de terminar CANCELADA.'],['No se pudo reservar','Rechazo sin descuento; no hay una reserva confirmada que compensar.'],['Kafka/Pago temporalmente detenido','El proceso puede quedar pendiente. Una demora no equivale automáticamente a cancelación.'],['Error SQL dentro del consumidor','Rollback local de Inbox, stock y Outbox. No es una compensación global.'],['Evento imposible de procesar','Reintentos y DLT; necesita diagnóstico/reproceso. No se garantiza recuperación automática infinita.']])
fio.h('7. Imágenes de producto: qué agregamos y cómo defenderlo',new=True)
fio.p('ADMIN selecciona JPG/PNG de su computadora; Angular muestra la vista previa. Después de guardar el producto, manda multipart con campo archivo. Catálogo valida contenido y límites, recodifica, guarda un archivo UUID y su referencia SQL. El cliente solo ve la imagen. No usamos Supabase para las fotos en esta versión.')
fio.ref(java('catalogo','controller/ImagenController'),'@RequestMapping','GET muestra; PUT sube/reemplaza; DELETE quita solo la foto.',13)
fio.ref(COMMON+'LocalImages.java','public void upload','Máximo 5 MB, dimensiones limitadas, bloqueo y referencia transaccional. Reemplazar no sobrescribe el archivo anterior antes de confirmar.',14)
fio.ref(front('shared/image-editor.ts'),'persist(','El editor compartido aplica la foto al guardar. Si falla tras crear producto, el formulario conserva el ID para no duplicarlo al reintentar.',10)
fio.p('La carpeta uploads/ de Catálogo se conserva entre reinicios. Git no transporta esas fotos; se respaldan junto a PostgreSQL. En Docker integrado hay un volumen de imágenes. Una interrupción abrupta puede dejar archivos huérfanos: disco y PostgreSQL no comparten una única transacción ACID.')
fio.h('8. Usuario: perfil, Keycloak y mascotas',new=True)
fio.p('Keycloak autentica y emite el JWT. Usuario guarda nombre, correo de contacto, DNI, teléfono, dirección y mascotas. El sub del token enlaza el perfil con la cuenta. Cambiar el correo de contacto local no cambia automáticamente el correo de login en Keycloak.')
fio.ref(java('usuario','controller/MiCuentaController'),'@RequestMapping','Las rutas /usuarios/me trabajan con el autenticado, no con un sub arbitrario enviado en JSON.',9)
fio.ref(java('usuario','service/UsuarioService'),'public UsuarioResponse guardarMe','Normaliza datos, evita apropiación por email y obtiene la identidad de CurrentUser. No asigna roles de seguridad desde el formulario.',22)
fio.ref(java('usuario','service/UsuarioService'),'public Usuario miUsuario','Recupera o crea el perfil a partir de la identidad autenticada. Si el correo coincide con otro subject, exige revisión en lugar de enlazarlo automáticamente.',15)
fio.ref(java('usuario','service/MascotaService'),'private Mascota buscarOFallar','Verifica propiedad antes de devolver/modificar una mascota. Un usuario no obtiene otra mascota cambiando el id en la URL.',12)
fio.ref(java('usuario','dto/MascotaRequest'),None,'La edad se valida como entero y tiene unidad explícita. Mostrar 3 MESES o 20 DIAS; no decir que guarda años decimales.',12)
fio.p('Una relación 1:N importante es Usuario → Mascotas. Usuario → Suscripciones y Suscripción → Períodos también son 1:N. El perfil vinculado a Keycloak no se borra libremente desde Clientes para evitar perder historial.')
fio.h('9. Roles internos: no son permisos de Keycloak',new=True)
fio.ref(java('usuario','entity/Usuario'),'@ManyToMany','Usuario ↔ Rol es otra N:M local. Es clasificación del negocio, no el emisor de permisos JWT.',12)
fio.ref(java('usuario','controller/UsuarioController'),'public class UsuarioController','Las operaciones administrativas y asignación de roles internos se explican junto a SecurityConfiguration, no como un login propio.',10)
fio.p('Frase defendible: “Usamos Keycloak para autenticación y autorización distribuida. Las tablas de Usuario almacenan información del negocio. Un rol de esas tablas no transforma un token CLIENTE en ADMIN”. Cambiar un botón o el localStorage tampoco concede permisos en el backend.')
fio.h('10. Suscripciones: tu defensa transaccional principal',new=True)
fio.diagram('fio-suscripcion','''rankdir=TB;a[label="Cliente contrata / renueva\nIdempotency-Key"];o[label="Identificar usuario y operación"];l[label="Bloqueo por usuario + clave"];k[label="¿Operación ya aplicada?",shape=diamond];r[label="Mismo tipo y recurso:\n devolver resultado existente"];s[label="Validar plan y vigencia\nguardar suscripción + período\nmisma transacción local"];b[label="Commit local; si falla, rollback"];a->o->l->k;k->r[label="sí"];k->s[label="no"];s->b;''','La clave identifica una operación. Renovar de verdad usa otra clave; reintentar la misma petición conserva la original.')
fio.ref(java('usuario','service/SuscripcionService'),'public SuscripcionResponse contratar','Contratar: un plan activo, sin duplicar otro vigente; crea cabecera y período ALTA con precio/vigencia acordados.',34)
fio.ref(java('usuario','service/SuscripcionService'),'public SuscripcionResponse renovar','Renovar: bloquea, refresca después del bloqueo, comprueba reintento, rechaza canceladas y añade un período al precio actual del plan.',30)
fio.ref(java('usuario','service/SuscripcionService'),'private void addPeriod','El período conserva su propio precio y fechas. Cambiar el plan no reescribe ese historial.',17)
fio.ref(java('usuario','service/SuscripcionService'),'private void lock','Bloqueos advisory de PostgreSQL viven hasta finalizar la transacción. Controlan carreras incluso entre instancias que comparten esta base.',8)
fio.p('Ejemplo: contraté por S/ 30; el plan cambia a S/ 35; renuevo. El período anterior sigue en 30 y el nuevo conserva 35. Renovación extiende desde fechaFin si aún está vigente o desde ahora si venció. Cancelar marca el estado, conserva períodos y no realiza un reembolso bancario.')
fio.p('Por qué sí es transaccional: si se actualizara fechaFin sin guardar el período, el historial no explicaría la vigencia; si solo se guardara el período sin extender vigencia, se perdería el efecto del negocio. La operación evita ambos estados parciales mediante una transacción local, reglas y restricciones.')
fio.p('Límite: no es un cobro ni un beneficio automático de suscripción. Usuario no forma parte de la Saga de compra solo por usar @Transactional.')
fio.h('11. Tus pantallas Angular y dónde cambiar cada cosa',new=True)
fio.table(['Pantalla / archivo bajo src/app','Qué mostrar / estudiar'],[['features/catalogo/product-catalog.ts y .html','Catálogo público, búsqueda, filtro, paginación y botón añadir; ResourceImage muestra la foto.'],['features/admin/productos.component.ts y .html','Modal crear/editar, categorías múltiples, stock, precio y persistencia de imagen sin duplicar producto.'],['app.ts y app.html','Administración de categorías sigue en el componente raíz; buscar save(), edit() y remove().'],['features/cuenta/cuenta.component.ts y .html','save() hace PUT y confirma por GET; guardado() solo se activa con el dato persistido.'],['features/planes/planes.component.ts y .html','operation conserva una clave por reintento; contratar/renovar/cancelar llaman al backend.'],['features/admin/clientes.component.*','Búsqueda y gestión administrativa del perfil.'],['features/admin/roles.component.ts; usuarios-roles.component.*','Roles internos y sus asignaciones; no cambiar autorización Keycloak.'],['shared/image-editor.ts, media.ts, resource-image.ts','Selector, subida multipart y foto/marcador.'],['src/styles.css','Colores rosa, fuentes y tamaños. Editar estilo no cambia una regla de negocio.']])
fio.ref(front('features/cuenta/cuenta.component.ts'),'  save()','Guardar mi perfil no se demuestra por el toast: la pantalla confirma la lectura persistida.',22)
fio.ref(front('features/planes/planes.component.ts'),'  operation(','Una firma de operación conserva la clave para reintentar; la consistencia final la verifica el servidor.',13)
shared(fio)
fio.h('12. Guion de demostración y defensa de Fio',new=True)
fio.table(['Tiempo','Qué hacer en Angular','Qué explicar'],[['0:00–0:40','ADMIN: producto con dos categorías y una foto. Guardar, reabrir y filtrar.','N:M con tabla de unión; escritura ADMIN; imagen opcional validada por servidor.'],['0:40–1:15','CLIENTE: guardar perfil y volver a cargar; mascota con edad/unidad.','Keycloak autentica; Usuario conserva datos del negocio y verifica propiedad con sub.'],['1:15–2:15','Contratar plan y renovar; mostrar períodos/vencimiento.','Cabecera/períodos, precios históricos, clave de reintento y bloqueo. No afirmar cobro real.'],['2:15–3:00','Compra preparada que rechaza pago; comparar stock.','Catálogo compensa reserva; mostrar InventarioEvents.liberar y evento inventario.liberado.']])
fio.p('Presentación sugerida: “Soy responsable de Catálogo y Usuario. Catálogo mantiene productos y categorías, relacionados de muchos a muchos, y controla inventario. Usuario vincula la identidad de Keycloak con perfil y mascotas; su capacidad transaccional es contratar y renovar suscripciones guardando períodos históricos. Puedo demostrar permisos, persistencia e idempotencia”.')
fio.table(['Pregunta probable','Respuesta'],[['¿Catálogo no es transaccional?','Su responsabilidad principal es maestra, pero inventario sí realiza transacciones y participa en la Saga.'],['¿Guardar perfil prueba tu transacción de negocio?','No es mi evidencia principal; muestro suscripción y período guardados juntos y la renovación coherente.'],['¿Cómo demuestras N:M?','Dos categorías en un producto y otro producto compartiendo una; entidad, tabla intermedia y servicio que resuelve IDs.'],['¿El rol de PostgreSQL autoriza ADMIN?','No. El permiso real viene del JWT de Keycloak; el backend lo valida.'],['¿Kafka evita todos los duplicados?','No. Inbox y unicidad de reserva por venta hacen idempotentes los efectos; la entrega es al menos una vez.'],['¿Qué compensa Catálogo?','Devuelve unidades ya reservadas cuando Pago rechaza; no reembolsa dinero.'],['¿Los planes cobran de verdad?','No, guardan importes y períodos; Mercado Pago sigue pendiente.'],['¿Qué evidencia tienes?','Respuesta recargada de perfil, asociaciones persistidas, períodos, stock antes/después y logs/eventos con la misma operación.']])
dei=Book('Deissy',['citas','envio'],'Deissy-Citas-y-Envio.pdf');common_intro(dei)
dei.h('3. Tu mapa: Citas y Envío',new=True)
dei.table(['Servicio','Responsabilidad','Defensa principal'],[['Citas · 8084 / PG 15444','Reserva de atención para una mascota, profesional, sede y prestaciones.','Transaccional: cabecera/detalles, reglas de agenda, propiedad e importes históricos.'],['Envío · 8083 / PG 15443','Transportistas, zonas y coberturas con tarifa/plazo.','Maestro logístico; N:M transportista/zona mediante Cobertura.'],['Despacho en Venta · 8081','Seguimiento operativo del envío ya cobrado en una compra.','Es una conexión con el módulo de Nikol; no atribuir su persistencia a la base de Envío.']])
dei.diagram('deissy-conexiones','''rankdir=TB;a[label="Angular"];g[label="Gateway"];c[label="Citas 8084"];e[label="Envío 8083\nmaestros logísticos"];u[label="Usuario\nmascota propia"];i[label="Institución\nsede / oferta"];b[label="Bienestar\nprofesional"];v[label="Venta 8081\ncompra + despacho"];pc[label="PG Citas 15444"];pe[label="PG Envío 15443"];a->g;g->c;g->e;g->v[label="/envios, /despachos"];c->u[label="HTTP"];c->i[label="HTTP"];c->b[label="HTTP"];c->pc;e->pe;v->e[label="Feign / tarifa"];''','Citas consulta tres dominios. Envío cotiza cobertura; el despacho de compra pertenece a Venta. No hay FK entre las bases.')
dei.h('4. Citas: del formulario a la reserva',new=True)
dei.p('El cliente selecciona mascota propia, sede, profesional, servicios o paquete y un horario futuro. Angular calcula una vista previa; el servidor vuelve a obtener precios y duración de Institución. No confía en un total escrito por el navegador.')
dei.ref(java('citas','controller/CitaController'),'@RequestMapping','La API expone listar, obtener, crear, confirmar, atender y cancelar. No tiene edición libre ni borrado físico de citas.',32)
dei.ref(java('citas','dto/CitaRequest'),'public class CitaRequest','Validación de IDs positivos, fecha futura, prestaciones no vacías y motivo. La entrada no pide un total confiable del navegador.',24)
dei.ref(java('citas','mapper/CitaMapper'),'public','El mapper establece los campos iniciales; identifica cómo toma idCliente y estado programado.',16)
dei.ref(java('citas','service/CitaService'),'public CitaResponse crear','La operación empieza comprobando intervalos y consultando referencias; sigue hasta la persistencia de cabecera y detalles.',24)
dei.p('Para explicar un POST: CitaController.crear recibe @Valid CitaRequest → CitaService.crear comprueba reglas y referencias → Cita/DetalleCita modelan los datos → CitaRepository.saveAndFlush guarda → CitaMapper produce el Response que Angular muestra.')
dei.h('5. Citas: conexiones exactas y autorización',new=True)
dei.table(['Destino','Qué obtiene','Por qué importa'],[['Usuario: /usuarios/me/mascotas/{id}','Mascota del autenticado.','No basta que exista: debe pertenecer al cliente. La llamada propaga su token.'],['Institución: /sedes/{id}','Sede y estado activo.','Evita reservar en una sede no disponible.'],['Bienestar: /especialistas/{id}','Profesional, estado y sede asignada.','Rechaza profesional inactivo o de otra sede cuando tiene sede específica.'],['Institución: /sedes/{id}/prestaciones','Oferta, precio, duración y componentes del paquete.','Evita aceptar servicios no ofrecidos en esa sede o precios manipulados.']])
dei.ref(java('citas','service/CitaService'),'private final ServiceClient','Cliente HTTP común inyectado. No es un @FeignClient propio de Citas.',5)
dei.ref(COMMON+'ServiceClient.java',None,'Lee cómo resuelve el nombre, propaga JWT y correlación y convierte fallos remotos en error controlado.',28)
dei.ref(java('citas','service/CitaService'),'private Cita owned','Después de recuperar la cita verifica al propietario mediante sub. ADMIN puede gestionar según las rutas protegidas.',12)
dei.p('Si un servicio de referencia no responde, Citas no debe inventar mascota, precio o profesional. La creación se rechaza de forma controlada; los cambios locales no quedan confirmados. Eso es validación/resiliencia y rollback local, no compensación de una Saga de citas.')
dei.h('6. Citas: detalle, precio histórico y paquetes',new=True)
dei.ref(java('citas','entity/Cita'),'@OneToMany','Relación 1:N: una cita guarda varios detalles. Cascade permite persistir el agregado.',12)
dei.ref(java('citas','entity/DetalleCita'),None,'Cada detalle conserva prestación remota, nombre, precio, duración y componentes acordados.',24)
dei.ref(java('citas','service/CitaService'),'var ids = new LinkedHashSet','Evita IDs repetidos y comprueba la oferta activa. Después expande componentes efectivos de paquetes.',27)
dei.p('Ejemplo: baño cuesta 30 y corte 20, pero el paquete cuesta 45 y dura 60 minutos. Si eliges el paquete, el detalle conserva 45 y sus componentes. No se permite añadir de nuevo el baño incluido: repetidos() en Angular ayuda al usuario y el backend lo verifica otra vez.')
dei.p('Cita → detalles es 1:N. El id de prestación corresponde a Institución, pero no existe una relación JPA @ManyToMany entre dos bases. Para cumplir la N:M de tu pareja de servicios, la evidencia más clara está en Envío: Transportista ↔ Zona a través de Cobertura.')
dei.h('7. Citas: concurrencia y por qué sí es transaccional',new=True)
dei.diagram('deissy-reserva','''rankdir=TB;f[label="Formulario válido / cliente"];r[label="Consultar mascota, sede,\nprofesional y ofertas"];d[label="Construir detalles\nprecio + duración"];l[label="Bloqueo PostgreSQL\npor profesional"];o[label="¿Se cruza con PROGRAMADA\no CONFIRMADA?",shape=diamond];x[label="409: no guardar reserva"];s[label="Guardar cita + detalles\ncommit local"];f->r->d->l->o;o->x[label="sí"];o->s[label="no"];''','Dos navegadores pueden enviar a la vez. El servidor serializa la comprobación y escritura por profesional; esconder horarios en Angular no basta.')
dei.ref(java('citas','service/CitaService'),'SELECT pg_advisory_xact_lock','Bloqueo transaccional por profesional, seguido de comparación de intervalos de inicio/fin.',18)
dei.p('Dos intervalos se cruzan si el inicio existente es anterior al fin nuevo y el fin existente es posterior al inicio nuevo. Por eso no basta comparar si empieza a la misma hora: una atención de 60 minutos también ocupa el segundo bloque de 30.')
dei.p('Se aceptan comienzos alineados a 30 minutos y duración total hasta ocho horas. El DTO exige futuro. Un índice único protege el mismo profesional/hora y la comprobación de intervalos cubre solapamientos más amplios. @Version añade control optimista de cambios de la cita.')
dei.p('La operación es transaccional porque cabecera, detalles, total y duración deben persistir coherentemente. Si guardar un detalle falla, no debe confirmarse una cabecera incompleta. El bloqueo de PostgreSQL se libera al confirmar o revertir la transacción local.')
dei.h('8. Citas: estados y operaciones permitidas',new=True)
dei.table(['Acción','Transición / regla'],[['Crear','PROGRAMADA.'],['Confirmar','Solo ADMIN: PROGRAMADA → CONFIRMADA; repetir el mismo destino es tolerado por transition.'],['Atender','Solo ADMIN: CONFIRMADA → ATENDIDA. No se permite saltar desde un estado incompatible.'],['Cancelar','Propietario/ADMIN según la seguridad. Una cita ATENDIDA no se cancela.'],['Lectura','Cliente ve las propias; ADMIN puede ver todas.'],['Eliminar / editar libremente','No son endpoints expuestos. No presentes un CRUD completo si no tiene PUT/DELETE.']])
dei.ref(java('citas','service/CitaService'),'private CitaResponse transition','Compara estado esperado y siguiente antes de guardar.',12)
dei.ref(java('citas','service/CitaService'),'public CitaResponse cancelar','Revisa propietario y estado atendido. Cancelar conserva el historial.',10)
dei.p('La cancelación de una cita es una transición local. No la presentes como devolución bancaria ni como compensación de stock: esas operaciones pertenecen a otro proceso.')
dei.h('9. Envío: maestros y CRUD real',new=True)
dei.p('Envío administra quién transporta, dónde cubre y cuánto cobra. No necesita crear una venta para registrar un transportista o una zona: por eso su responsabilidad académica principal es maestra/no transaccional. Aun así usa transacciones SQL locales para consistencia.')
dei.ref(java('envio','controller/LogisticaController'),'@RequestMapping','Todos los endpoints logísticos parten de /api/v1. Identifica GET/POST/PUT/DELETE de transportistas y zonas; cobertura se crea/actualiza mediante PUT.',28)
dei.ref(java('envio','service/LogisticaService'),'public TransportistaResponse guardarTransportista','ID null crea; ID existente actualiza. DTO valida teléfono y otros campos.',17)
dei.ref(java('envio','service/LogisticaService'),'public void borrarTransportista','Las bajas son lógicas: desactivar conserva referencias e historial.',10)
dei.p('Si el profesor pide un CRUD, muestra los verbos del controlador y el servicio que ejecutan. Explica que DELETE no siempre elimina una fila: aquí cambia activo=false. No confundas “borrar” del botón con un DELETE SQL físico.')
dei.h('10. Envío: relación muchos a muchos con atributos',new=True)
dei.diagram('deissy-relaciones','''rankdir=LR;t[label="transportistas"];c[label="coberturas\ntarifa, días, activo\nUNIQUE transportista + zona"];z[label="zonas"];ci[label="citas"];dc[label="cita_detalles\nprecio / duración acordados"];t->c[label="1:N"];z->c[label="1:N"];ci->dc[label="1:N"];''','Transportista ↔ Zona es N:M con entidad de asociación. Cada cobertura representa una pareja y sus condiciones de servicio.')
dei.ref(java('envio','entity/Cobertura'),'@ManyToOne','Dos relaciones N:1 materializan una N:M con atributos propios. No es necesario que aparezca literalmente @ManyToMany.',22)
dei.ref(java('envio','service/LogisticaService'),'public CoberturaResponse guardarCobertura','Resuelve ambos padres, exige que estén activos cuando se activa la cobertura y busca la pareja antes de crear otra.',23)
dei.ref(java('envio','repository/CoberturaRepository'),'findByTransportistaIdAndZonaId','La búsqueda por pareja evita duplicados a nivel de negocio; la restricción SQL refuerza el mismo criterio.',4)
dei.p('Ejemplo de defensa: Transportista A cubre Miraflores y Arequipa; Miraflores también tiene Transportista B. La cobertura A/Miraflores puede costar 10 y B/Miraflores 15. La tarifa pertenece a la asociación, no solo al transportista ni solo a la zona.')
dei.p('Para comprobarlo en Angular: ADMIN → Logística → crear dos zonas y dos transportistas → asignar coberturas → consultar las combinaciones. Desactivar un padre hace que su cobertura deje de considerarse disponible al cliente.')
dei.h('11. Cómo se cobra el envío y dónde vive el despacho',new=True)
dei.p('El cliente elige delivery en el carrito. Venta consulta a Envío la cobertura real, compara tarifa cotizada y calcula subtotal + envío. Cuando la Saga confirma el pago, Venta crea un despacho único en su propia base. Un pedido de recojo no genera despacho ni puede recibir delivery gratis después de pagarse.')
dei.ref(java('venta','client/LogisticaClient'),'@FeignClient','Conexión desde Venta al nombre lógico garritas-envio-ms. Es código de otro dominio que consume tu capacidad logística.',12)
dei.ref(java('venta','service/VentaService'),'var cobertura = logistica.obtener','Verifica cobertura y tarifa actual; guarda una copia de condiciones e incluye el cargo en el total.',22)
dei.ref(java('venta','messaging/VentaEvents'),'INSERT INTO despachos','La creación del despacho está en Venta, en la misma transacción que su avance de estado e Inbox.',8)
dei.ref('infra/garritas-config/config-repo/garritas-gateway-dev.yml','id: garritas-envio','El alias /envios y /despachos se dirige a Venta; las rutas de transportistas/zonas/coberturas van a Envío.',8)
dei.p('Puede existir una tabla envios histórica en la base de Envío por las primeras migraciones. No es prueba de que la implementación actual la use como despacho operativo. El lanzador conserva y migra históricos mediante uso-rapido/scripts/migrar-despachos.* sin borrar el origen.')
dei.p('Si el profesor pregunta “¿Dónde está tu microservicio Envío?”, abre LogisticaController y LogisticaService en garritas-envio-ms. Después muestra quién consume su tarifa. La pantalla “Envíos” es un seguimiento integrado de otro agregado, no una correspondencia exacta de nombre de pestaña y base.')
dei.h('12. Tus pantallas Angular y recorrido del código',new=True)
dei.table(['Ruta bajo clients/garritas-frontend/src/app','Qué hace'],[['features/citas/citas.component.ts y .html','load carga referencias; loadOfertas obtiene prestaciones; total/duration calculan vista previa; repetidos detecta componentes compartidos; save envía la reserva; action ejecuta transiciones.'],['features/logistica/logistica.component.ts y .html','Formularios y tablas de transportistas, zonas y cobertura. saveT/saveZ/saveC llaman a los endpoints reales.'],['features/envios/envios.component.ts y .html','Seguimiento de despachos de Venta. Solo ADMIN marca en tránsito/entregado; cliente observa los suyos.'],['features/cart/cart-store.ts y cart-panel.*','Selección y cotización de delivery. Los importes definitivos los comprueba Venta.'],['core/domain-api.ts','Tipos Cita, Cobertura, Transportista, Zona y Envio y llamadas HTTP compartidas.'],['core/auth.ts e interceptor.ts','Login, roles y JWT para el Gateway.'],['../styles.css','Tamaños, colores, formularios y tablas. No cambiar una regla de negocio únicamente aquí.']])
dei.ref(front('features/citas/citas.component.ts'),'  save()','La interfaz valida lo necesario y hace POST /citas. Revisa la respuesta y el error; el servidor vuelve a validar la operación.',27)
dei.ref(front('features/logistica/logistica.component.ts'),'  saveC()','La asociación de transportista/zona se envía como cobertura, no como un despacho.',8)
dei.ref(front('features/envios/envios.component.html'),'Elige el delivery','La propia pantalla explica que el envío se cobra durante checkout y aparece automáticamente al pagarse.',8)
shared(dei)
dei.h('13. Fallos, Saga y límites que debes distinguir',new=True)
dei.table(['Situación','Tu respuesta'],[['Dos reservas solapadas','Citas serializa por profesional y rechaza la segunda; no es una compensación.'],['Institución/Usuario/Bienestar caído','Consulta HTTP controlada; no inventar datos ni confirmar una cita incompleta.'],['Envío caído al validar checkout','Venta aplica su cliente resiliente y no acepta la compra con tarifa desconocida. El Circuit Breaker está en Venta, no en LogisticaService.'],['Pago rechaza tras stock reservado','La Saga Venta–Catálogo–Pago devuelve el inventario. Citas/Envío no son consumidores de esa Saga en esta versión.'],['Pago aprobado con delivery','Venta crea el despacho del envío cobrado; la tarifa ya está incluida.'],['Cancelar una cita','Transición local; no devuelve dinero de un pago que Citas no implementa.']])
dei.p('Frase útil: “Yo aporto la reserva consistente de atención y el maestro de cobertura logística. Esas capacidades se conectan por APIs con otros dominios. No digo que todas mis operaciones sean una Saga: la Saga implementada corresponde a la compra”.')
dei.h('14. Guion de demostración y defensa de Deissy',new=True)
dei.table(['Tiempo','Qué hacer','Qué explicar'],[['0:00–0:45','ADMIN → Logística: mostrar un transportista con dos zonas y una zona con dos transportistas.','N:M con Cobertura y atributos tarifa/días/activo.'],['0:45–1:20','CLIENTE → carrito: elegir zona/transportista y comparar total.','Venta obtiene y valida tarifa en Envío. El navegador no decide el monto final.'],['1:20–2:15','CLIENTE → Citas: mascota, sede, profesional y paquete. Guardar y abrir detalle.','Cabecera/detalles, importes históricos, propiedad y validación de referencias.'],['2:15–3:00','Intentar cita solapada; mostrar error. Abrir bloqueo y consulta de intervalos en CitaService.','Control concurrente del servidor, transacción local y diferencia con Saga.']])
dei.p('Presentación sugerida: “Mis servicios son Citas y Envío. Citas registra una reserva con varios detalles y controla horarios concurrentes por profesional. Envío mantiene transportistas y zonas vinculados mediante coberturas con precio y plazo. La compra utiliza esa tarifa y el despacho se administra dentro de Venta”.')
dei.table(['Pregunta probable','Respuesta'],[['¿Por qué Citas sí es transaccional?','La reserva guarda cabecera, detalles, total y duración juntos, con reglas y control de concurrencia.'],['¿Dónde está tu muchos a muchos?','Cobertura, dos @ManyToOne, búsqueda por pareja y UNIQUE en SQL; lo demuestro con combinaciones en Logística.'],['¿Una FK une Citas con Usuario?','No. Son bases distintas; se consulta la API y se guardan referencias/snapshots.'],['¿Citas usa Feign y Circuit Breaker?','Usa ServiceClient con espera acotada; los clientes Feign con Circuit Breaker del ejemplo logístico están en Venta.'],['¿Por qué una cita a otra hora puede cruzarse?','La duración ocupa un intervalo; comparo inicio y fin, no solo igualdad de hora.'],['¿Dónde está el envío pagado?','En despachos de Venta. Envío aporta el maestro de cobertura y tarifa.'],['¿Envío no tiene transacciones?','Sí usa transacciones locales; es maestro por responsabilidad, no por ausencia de SQL transaccional.'],['¿Está integrado Mercado Pago/Yape real?','No. El pago del laboratorio sigue simulado; no atribuir cobros reales a esta versión.']])
def selected_sources(b):
 files=[]
 for d in b.domains:
  root=f'services/garritas-{d}-ms/'
  files += [p for p in TRACKED if p.startswith(root+'src/') and Path(p).suffix in {'.java','.sql','.yml','.yaml','.xml','.properties'}]
  files += [root+'pom.xml',root+'compose-dev.yml']
  files += [f'infra/garritas-config/config-repo/garritas-{d}-ms-{profile}.yml' for profile in ['dev','prod']]
 shared_names=['CurrentUser','SecurityConfiguration','ServiceClient','HttpServices','DomainErrors','Reference']
 if b.who=='Fio':shared_names+=['Inbox','Outbox','MessagingConfiguration','SagaEvent','LocalImages']
 files += [COMMON+n+'.java' for n in shared_names]
 files += [front('core/'+n+'.ts') for n in ['api','domain-api','auth','interceptor','config']]
 if b.who=='Fio':
  folders=['features/catalogo/','features/cuenta/','features/planes/']
  stems=['features/admin/productos.component','features/admin/clientes.component','features/admin/usuarios-roles.component','features/admin/roles.component']
  files += [p for p in TRACKED if p.startswith(front('')) and (any(p.startswith(front(f)) for f in folders) or any(p.startswith(front(s)) for s in stems)) and Path(p).suffix in {'.ts','.html'} and '.spec.' not in p]
  files += [front('app.ts'),front('app.html')]+[front('shared/'+s+'.ts') for s in ['image-editor','resource-image','media']]
 else:
  files += [p for p in TRACKED if any(p.startswith(front(f)) for f in ['features/citas/','features/logistica/','features/envios/','features/cart/']) and Path(p).suffix in {'.ts','.html'} and '.spec.' not in p]
  files += [java('venta',p) for p in ['client/LogisticaClient','client/LogisticaConsulta','despacho/service/DespachoService','messaging/VentaEvents']]
 files += ['infra/garritas-config/config-repo/garritas-gateway-dev.yml','clients/garritas-frontend/src/styles.css']
 return sorted(set(files),key=lambda p:(0 if any(p.startswith(f'services/garritas-{d}-ms/') for d in b.domains) else 1,p))

def endpoints(b):
 b.h('Mapa de endpoints: qué operaciones existen de verdad',new=True)
 b.p('Las rutas siguientes se extraen de los controladores de tus módulos. En Angular se consumen a través de Gateway en http://localhost:18080. La tabla no sustituye la autorización: las escrituras maestras son ADMIN y las operaciones propias requieren identidad/propiedad, según SecurityConfiguration.')
 for d in b.domains:
  b.h(d.capitalize(),2)
  rows=[]
  for p in TRACKED:
   if p.startswith(f'services/garritas-{d}-ms/src/main/java/') and '/controller/' in p and p.endswith('.java'):
    t=read(p);pref=re.search(r'@RequestMapping\("([^"]*)"\)',t);prefix=pref[1] if pref else ''
    for m in re.finditer(r'@(Get|Post|Put|Delete|Patch)Mapping(?:\(([^)]*)\))?',t):
     args=m[2] or '';strings=re.findall(r'"([^"]*)"',args);route=next((v for v in strings if v.startswith('/')),'')
     line=t[:m.start()].count('\n')+1
     rows.append([m[1].upper(),prefix+route,Path(p).name+':'+str(line)])
  b.table(['Verbo','Ruta','Dónde localizar'],rows)
 b.p('Citas y suscripciones exponen acciones del negocio, no necesariamente PUT y DELETE genéricos. En cobertura, PUT crea o actualiza la asociación. Los borrados lógicos mantienen historial. No inventes un CRUD uniforme si el dominio requiere estados y reglas.')

def catalog(b,files):
 b.h('Mapa completo: archivos y qué debes explicar',new=True)
 b.p('Estas fichas son tu ruta de estudio. Primero localiza la clase, explica su responsabilidad y reconoce sus métodos. Después usa el anexo para leer la implementación completa. El código compartido o de otro dominio se etiqueta como contexto, no como autoría individual.')
 for d in b.domains:
  b.h('Backend '+d.capitalize(),2)
  for p in files:
   if not p.startswith(f'services/garritas-{d}-ms/') or not p.endswith('.java'):continue
   b.h(Path(p).name,3);b.ref(p);b.p(describe(p))
   methods=[]
   for i,line in enumerate(read(p).splitlines(),1):
    m=re.match(r'\s*(?:public|private|protected)\s+(?:(?:static|final)\s+)*(?:[\w.<>, ?\[\]]+)\s+(\w+)\s*\(',line)
    if m:methods.append(f'{m[1]}() L{i}')
   if methods:b.p('Métodos para ubicar: '+', '.join(methods)+'.')
 b.h('Base de datos, configuración y frontend',2)
 for p in files:
  if p.endswith('.java') and any(p.startswith(f'services/garritas-{d}-ms/') for d in b.domains):continue
  b.ref(p,explain=describe(p))
  if p.endswith('.ts'):
   methods=[]
   for i,line in enumerate(read(p).splitlines(),1):
    m=re.match(r'\s*(?:(?:private|public)\s+)?(\w+)\([^\n;]*\)\s*\{',line)
    if m:methods.append(f'{m[1]}() L{i}')
   if methods:b.p('Entradas de lógica: '+', '.join(methods)+'.')

def source_appendix(b,files):
 b.h('Anexo: código completo de tus módulos y conexiones',new=True)
 b.p('Contenido literal de la revisión analizada, con números de línea añadidos para estudiar. Las líneas largas se ajustan visualmente al ancho; para copiar un archivo ejecutable usa el original de GitHub y no incluyas la numeración. No se omiten clases ni se sustituyen cuerpos por puntos suspensivos.')
 b.p('Se incluyen todos los Java de src/main y src/test de tus dos dominios, SQL y configuración, las pantallas asignadas y el soporte común pertinente. Los wrappers Maven, dependencias descargadas, binarios y código de otros dominios no necesarios para esta defensa no se imprimen. Esto es una guía de estudio de tu parte, no un ZIP autónomo para reconstruir el proyecto entero.')
 previous=None
 for p in files:
  if p.startswith('services/'):
   group=p.split('/')[1]
  elif p.startswith('clients/'):group='Angular y estilos'
  else:group='Soporte común y configuración'
  if group!=previous:b.h(group,2);previous=group
  b.h(Path(p).name,3);b.ref(p);b.p(describe(p))
  t=read(p);b.sources.append({'path':p,'sha256':hashlib.sha256(t.encode()).hexdigest(),'lines':len(t.splitlines())})
  b.code('\n'.join(f'{i:4}  {line}' for i,line in enumerate(t.splitlines(),1)))

def finalcheck(b):
 b.h('Lista para repasar antes de exponer',new=True)
 for t in ['Ubico mi Application, Controller, Service, Repository, Entity, DTO y mapper sin buscar al azar.','Sigo una acción de Angular hasta la base y conozco el endpoint real.','Muestro mi N:M persistida y mi operación transaccional con datos coherentes.','Distingo roles de Keycloak, roles internos y propietario sub.','Puedo explicar un caso inválido y qué estado/datos quedan después del rechazo.','No afirmo que todas las llamadas son Feign, todas las operaciones son Saga o los pagos son reales.','Reconozco qué código es mío, qué es compartido y qué módulo aporta mi compañera.','Tengo el entorno probado y datos de demostración preparados antes de los tres minutos.']:
  b.bullet(t)
 b.p('Para cada archivo importante responde: qué recibe, qué valida, a quién llama, qué guarda, qué devuelve y qué ocurre si falla. Ese recorrido explica el código mejor que leer sus imports en voz alta.')
 b.p('Referencia docente: https://262dist.github.io/pagatu/ (sesiones 1–11). Referencia verificable de esta guía: '+URL+'README.md. Las funciones nuevas de fotos/PDF están documentadas en docs/ventas-imagenes-y-comprobantes.md. El despliegue y Mercado Pago todavía están pendientes en esta revisión.')

if __name__=='__main__':
 for b in [fio,dei]:
  files=selected_sources(b);endpoints(b);catalog(b,files);source_appendix(b,files);finalcheck(b);b.save();print(b.filename,len(files),'archivos completos',len(b.refs),'referencias',flush=True)
 (OUT/'referencias.json').write_text(json.dumps({'commit':REV,'referencias':REFS,'fuentes':SOURCES},ensure_ascii=False,indent=2)+'\n')
