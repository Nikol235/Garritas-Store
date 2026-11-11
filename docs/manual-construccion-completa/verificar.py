"""Verifica rutas, bloques de código, ZIP y PDF sin ejecutar la aplicación."""
from pathlib import Path
from html.parser import HTMLParser
import json, zipfile, hashlib, subprocess, re
import fitz
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent
m=json.loads((OUT/'MANIFIESTO.json').read_text()); rev=m['commit']
class Sources(HTMLParser):
    def __init__(self):super().__init__();self.path=None;self.incode=False;self.cur='';self.blocks={}
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='article' and 'data-path' in a:self.path=a['data-path'];self.blocks[self.path]=[]
        if tag=='code' and self.path:self.incode=True;self.cur=''
    def handle_data(self,s):
        if self.incode:self.cur+=s
    def handle_endtag(self,tag):
        if tag=='code' and self.incode:self.blocks[self.path].append(self.cur);self.incode=False
        if tag=='article':self.path=None
parser=Sources();parser.feed((OUT/'01-Codigo-completo.html').read_text())
assert len(parser.blocks)==len(m['archivos'])
root='Garritas-desde-cero/'
with zipfile.ZipFile(OUT/'Garritas-desde-cero.zip') as z:
    assert z.testzip() is None
    names=z.namelist();assert len(names)==len(set(names))
    stages=[]
    for i in range(1,19):
        paths=z.read(root+f'ETAPAS/{i:02d}.txt').decode().splitlines();stages+=paths
        assert all(x['etapa']==i for x in m['archivos'] if x['ruta'] in paths)
    assert set(stages)=={x['ruta'] for x in m['archivos']}
    assert not any(n.endswith('/.env') or '/node_modules/' in n or '/target/' in n or '/.git/' in n for n in names)
    for f in m['archivos']:
        p=f['ruta']; data=z.read(root+'FUENTES/'+p)
        assert hashlib.sha256(data).hexdigest()==f['sha256'],p
        assert data==subprocess.check_output(['git','show',f'{rev}:{p}'],cwd=ROOT),p
        if f['impreso']:assert parser.blocks[p][-1]==data.decode().strip('\n'),p
    for p in OUT.glob('*.pdf'):assert z.read(root+p.name)==p.read_bytes()
report={'commit':rev,'fuentes':len(m['archivos']),'bloques_completos':sum(x['impreso'] for x in m['archivos']),'etapas':18,'pdf':[]}
for p in sorted(OUT.glob('*.pdf')):
    d=fitz.open(p);text=''.join(pg.get_text() for pg in d)
    assert len(d)>0 and len(text)>10000
    assert d.get_toc(),p
    assert all(pg.get_text().strip() for pg in d)
    report['pdf'].append({'archivo':p.name,'paginas':len(d),'marcadores':len(d.get_toc()),'texto_seleccionable':True})
    # Detectar texto cortado horizontalmente, sin contar la posición inicial del pie.
    bad=[]
    for i,pg in enumerate(d):
        for w in pg.get_text('words'):
            if w[0]<-1 or w[2]>pg.rect.width+1:bad.append(i+1)
    assert not bad,(p,bad)
# Navegación y copia sobre el HTML real. Se intercepta solo la API de portapapeles
# para comprobar que el botón pasa el texto exacto, sin depender del escritorio.
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1366,'height':900})
    page.set_content((OUT/'01-Codigo-completo.html').read_text())
    page.evaluate("Object.defineProperty(navigator, 'clipboard', {value:{writeText:async(t)=>{window.copiado=t}},configurable:true})")
    sample='services/garritas-venta-ms/src/main/java/pe/edu/upeu/garritas/venta/service/VentaService.java'
    file=page.locator('article[data-path="'+sample+'"]');file.locator('.copy').last.click()
    expected=subprocess.check_output(['git','show',f'{rev}:{sample}'],cwd=ROOT,text=True).strip('\n')
    assert page.evaluate('window.copiado')==expected
    page.locator('#buscar').fill('VentaService.java')
    assert page.locator('.file:not(.hidden)').count()==1
    page.screenshot(path=str(OUT/'verificacion-html.png'),full_page=False)
    page.set_content((OUT/'00-Manual-paso-a-paso.html').read_text())
    first=page.locator('.toc a').first; dest=first.get_attribute('href');first.click()
    assert page.locator(dest).count()==1
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.screenshot(path=str(OUT/'verificacion-movil.png'),full_page=False)
    browser.close()
report['html']={'copia_exacta':True,'busqueda_por_ruta':True,'navegacion':True,'sin_desbordamiento_horizontal':True}
report['alcance']='Verificación documental; no ejecuta PowerShell ni repite pruebas funcionales Java/Angular.'
(OUT/'verificacion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
