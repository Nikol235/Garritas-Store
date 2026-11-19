"""Genera una hoja A4 de arranque local; no ejecuta los comandos publicados."""
from pathlib import Path
from html import escape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Preformatted,Spacer,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
import fitz
OUT=Path(__file__).resolve().parent
for n,f in [('Body','DejaVuSans.ttf'),('Bold','DejaVuSans-Bold.ttf'),('Code','DejaVuSansMono.ttf')]:
 pdfmetrics.registerFont(TTFont(n,'/usr/share/fonts/truetype/dejavu/'+f))
style=ParagraphStyle('text',fontName='Body',fontSize=8.2,leading=11,spaceAfter=5)
head=ParagraphStyle('head',fontName='Bold',fontSize=10,leading=13,textColor=colors.HexColor('#135c47'),spaceBefore=6,spaceAfter=4)
code=ParagraphStyle('code',fontName='Code',fontSize=7.3,leading=9.5,backColor=colors.HexColor('#eff5f1'),borderPadding=5,spaceAfter=5)
items=[];txt=[]
def p(t):items.append(Paragraph(t,style));txt.append(t)
def h(t):items.append(Paragraph(t,head));txt.append('\n'+t)
def block(t):items.append(Preformatted(t,code));txt.append(t+'\n')
items.append(Paragraph('GARRITAS STORE · CLONAR Y ARRANCAR TODO',ParagraphStyle('title',fontName='Bold',fontSize=15,leading=19,textColor=colors.HexColor('#135c47'),spaceAfter=6)))
p('<b>Windows · PowerShell · ejecución local.</b> Instalar Git, JDK 21 completo, Node 24.x (24.15 o superior) y Docker Desktop con WSL2. Abrir Docker Desktop y esperar a que arranque. No requiere Maven ni Angular CLI globales.')
h('1. Comprobar herramientas')
block('git --version\njava -version\njavac -version\nnode --version\nnpm.cmd --version\ndocker compose version\ndocker info')
p('docker info debe mostrar Server sin error. Si falta una herramienta, instalarla antes de continuar y abrir una PowerShell nueva.')
h('2. Clonar la rama de trabajo y entrar (primera vez)')
block('cd $HOME\nNew-Item -ItemType Directory -Force proyectos | Out-Null\ncd proyectos\ngit clone --branch feat/garritas-store https://github.com/Nikol235/Garritas-.git\ncd Garritas-')
h('3. Compilar e iniciar; ejecutar en orden y esperar cada resultado')
block('Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force\n$env:NG_CLI_ANALYTICS = "false"\n.\\uso-rapido\\garritas.ps1 -Accion build\n.\\uso-rapido\\garritas.ps1 -Accion iniciar\n.\\uso-rapido\\garritas.ps1 -Accion estado\ndocker compose -f obs/compose-dev.yml up -d\ndocker compose -f obs/compose-dev.yml ps\nStart-Process "http://localhost:4200"')
p('<b>Qué arranca:</b> ocho PostgreSQL, Kafka y su UI, Keycloak con su base; Config, Eureka, Gateway y los ocho servicios Java; Angular. El comando obs añade Grafana, Prometheus, Loki y Promtail. Java y Angular corren fuera de Docker.')
h('4. Enlaces y accesos de laboratorio')
rows=[['Tienda','http://localhost:4200','cliente / Cliente123! · admin-store / Admin123!'],['Keycloak','http://localhost:18180/admin/','admin / local-admin-change-me'],['Kafka UI','http://localhost:18085','Sin login en DEV'],['Grafana','http://localhost:13000','admin / local-grafana'],['Prometheus','http://localhost:19090/targets','Targets y métricas'],['Eureka / Config','18761 / 18888','http://localhost:18761 · configuración en 18888']]
vals=[[Paragraph(escape(x) if j!=1 or not x.startswith('http') else f'<link href="{x}" color="#006b80">{x}</link>',ParagraphStyle('cell',fontName='Body',fontSize=7.1,leading=9)) for j,x in enumerate(r)] for r in rows]
t=Table(vals,colWidths=[65,155,307],hAlign='LEFT');t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f2f6f3')),('GRID',(0,0),(-1,-1),.25,colors.HexColor('#cbded4')),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]));items.append(t)
for r in rows:txt.append(' | '.join(r))
p('<b>APIs:</b> Venta 8081 · Institución 8082 · Envío 8083 · Citas 8084 · Catálogo 8085 · Usuario 8086 · Pago 8087 · Bienestar 8088. Gateway 18080. Swagger por servicio: http://localhost:PUERTO/swagger-ui.html. Bases: 15441–15448; Kafka: 19092; Loki: 13100; gestión Keycloak: 19000.')
h('5. Al volver otro día / detener')
block('cd "$HOME\\proyectos\\Garritas-"\nSet-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force\n# Para iniciar: .\\uso-rapido\\garritas.ps1 -Accion iniciar\n# Para detener Java y Angular:\n.\\uso-rapido\\garritas.ps1 -Accion detener')
p('<b>Importante:</b> no ejecutar iniciar dos veces. detener conserva contenedores y datos. Si cambia Java, repetir build antes de iniciar. Si un puerto está ocupado, identificar el proceso o contenedor (por ejemplo, Pagatu); no borrar volúmenes. Logs: .runtime/&lt;servicio&gt;/console.log y error.log. Las contraseñas pueden diferir si alguien ya las cambió.')
p('<b>Estado del proyecto:</b> pagos simulados; Mercado Pago aún no está conectado. Esta hoja inicia el entorno local, no publica en Railway/Supabase ni habilita cobros reales.')
pdf=OUT/'Garritas-inicio-completo-una-hoja.pdf'
SimpleDocTemplate(str(pdf),pagesize=A4,leftMargin=34,rightMargin=34,topMargin=24,bottomMargin=22,title='Garritas Store: inicio completo en una hoja',author='Garritas Store').build(items)
d=fitz.open(pdf);assert len(d)==1,f'PDF debe tener una página: {len(d)}';assert 'git clone' in d[0].get_text();d[0].get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save('/tmp/garritas-una-hoja.png');print('PDF comprobado: 1 página, texto seleccionable, enlaces:',len(d[0].get_links()))
(OUT/'Garritas-inicio-completo-una-hoja.txt').write_text('\n'.join(txt)+'\n')
