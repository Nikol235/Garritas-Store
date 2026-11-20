"""Prueba DEV real: PKCE, fotos con permisos, ventas/PDF y compensación.
Crea registros de demostración; conserva las ventas como historial.
Requiere el entorno completo y Playwright + Pillow + PyMuPDF.
"""
from pathlib import Path
import io,json,os,time,uuid,urllib.request,urllib.error
import fitz
from PIL import Image
from playwright.sync_api import sync_playwright,expect
from smoke import API,request,login,wait_state
OUT=Path('docs/evidencias-ventas-imagenes')

def photo(path,token=None,content=None,method='PUT',expected=204,mime='image/png'):
 headers={}
 if token:headers['Authorization']='Bearer '+token
 body=None
 if content is not None:
  boundary='garritas'+uuid.uuid4().hex
  body=(f'--{boundary}\r\nContent-Disposition: form-data; name="archivo"; filename="foto.png"\r\nContent-Type: {mime}\r\n\r\n'.encode()+content+f'\r\n--{boundary}--\r\n'.encode())
  headers['Content-Type']='multipart/form-data; boundary='+boundary
 req=urllib.request.Request(API+path,data=body,method=method,headers=headers)
 try:
  with urllib.request.urlopen(req,timeout=30) as r:status=r.status;data=r.read()
 except urllib.error.HTTPError as e:status=e.code;data=e.read()
 assert status==expected,(path,status,expected,data[:400])
 return data

def main():
 OUT.mkdir(parents=True,exist_ok=True);evidence={};suffix=uuid.uuid4().hex[:7]
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox'])
  ac,ap,admin=login(browser,'admin-store','Admin123!');cc,cp,client=login(browser,'cliente','Cliente123!')
  category=request('/categorias',admin,'POST',{'nombre':'Fotos '+suffix,'descripcion':'Prueba de archivos'},expected=201)
  product=request('/productos',admin,'POST',{'nombre':'Juguete Rosita '+suffix,'descripcion':'Foto de demostracion','precio':10,'stock':12,'activo':True,'categoriaIds':[category['id']],'categoriaId':category['id']},expected=201)
  sede=request('/sedes',admin,'POST',{'nombre':'Sede Rosita '+suffix,'direccion':'Av. Las Flores 123','ciudad':'Lima','telefono':'987654321','activo':True},expected=201)
  especialidad=request('/especialidades')[0]
  pro=request('/especialistas',admin,'POST',{'nombre':'Dra. Rosa '+suffix,'email':suffix+'@example.test','telefono':'987654321','sedeId':sede['id'],'activo':True,'especialidadIds':[especialidad['id']]},expected=201)
  buf=io.BytesIO();Image.new('RGB',(240,180),'pink').save(buf,'PNG');png=buf.getvalue();OUT.joinpath('foto-prueba.png').write_bytes(png)
  for resource,obj in [('productos',product),('sedes',sede),('especialistas',pro)]:
   endpoint=f'/{resource}/{obj["id"]}/imagen'
   photo(endpoint,client,png,expected=403);photo(endpoint,None,png,expected=401)
   photo(endpoint,admin,png);raw=photo(endpoint,method='GET',expected=200)
   assert Image.open(io.BytesIO(raw)).size==(240,180)
   photo(endpoint,admin,b'<svg onload="alert(1)"/>',expected=400)
   assert photo(endpoint,method='GET',expected=200)==raw
   other=io.BytesIO();Image.new('RGB',(240,180),'purple').save(other,'PNG')
   photo(endpoint,admin,other.getvalue());assert photo(endpoint,method='GET',expected=200)!=raw
   photo(endpoint,admin,method='DELETE');photo(endpoint,method='GET',expected=404)
   photo(endpoint,admin,method='DELETE')
   photo(endpoint,admin,png)
   evidence[resource]='carga, reemplazo, borrado, idempotencia y permisos OK'
  photo('/productos/999999999/imagen',admin,png,expected=404)
  photo(f'/productos/{product["id"]}/imagen',admin,b'x'*(5*1024*1024+1),expected=413)
  body={'sedeId':sede['id'],'metodoPago':'YAPE','detalles':[{'idProducto':product['id'],'cantidad':2}]}
  key=str(uuid.uuid4());sale=request('/ventas',client,'POST',body,key,expected=201)
  assert request('/ventas',client,'POST',body,key,expected=201)['id']==sale['id']
  sale=wait_state(sale['id'],client,'PAGADA');assert sale['total']==20
  photo(f'/ventas/{sale["id"]}/comprobante',method='GET',expected=401)
  pdf=photo(f'/ventas/{sale["id"]}/comprobante',client,method='GET',expected=200)
  OUT.joinpath('comprobante-demo.pdf').write_bytes(pdf)
  with fitz.open(stream=pdf,filetype='pdf') as doc:
   text=''.join(x.get_text() for x in doc);assert 'TOTAL: S/ 20.00' in text and 'pago simulado' in text
  stock=request('/productos/'+str(product['id']))['stock']
  rejected=request('/ventas',client,'POST',{**body,'metodoPago':'TRANSFERENCIA'},str(uuid.uuid4()),expected=201)
  wait_state(rejected['id'],client,'CANCELADA');assert request('/productos/'+str(product['id']))['stock']==stock
  photo(f'/ventas/{rejected["id"]}/comprobante',client,method='GET',expected=409)
  # Pantallas reales de ambos roles y filtros.
  ap.get_by_role('button',name='Ventas',exact=True).click();expect(ap.get_by_role('heading',name='Ventas',exact=True)).to_be_visible()
  ap.get_by_role('searchbox').fill(str(sale['id']));ap.get_by_role('button',name=f'Ver detalle de compra {sale["id"]}',exact=True).click()
  expect(ap.locator('.sale-totals')).to_contain_text('20.00');ap.screenshot(path=str(OUT/'ventas-admin.png'),full_page=True)
  cp.get_by_role('button',name='Mis compras',exact=True).click();expect(cp.get_by_role('heading',name='Mis compras',exact=True)).to_be_visible()
  cp.get_by_role('searchbox').fill(str(sale['id']));cp.get_by_role('button',name=f'Ver detalle de compra {sale["id"]}',exact=True).click()
  with cp.expect_download() as download:cp.get_by_role('button',name='Descargar comprobante PDF',exact=True).click()
  assert download.value.suggested_filename==f'Garritas-compra-{sale["id"]}.pdf'
  cp.screenshot(path=str(OUT/'mis-compras.png'),full_page=True)
  expect(cp.get_by_role('button',name='Ventas',exact=True)).to_have_count(0)
  expect(ap.get_by_role('button',name='Carrito',exact=True)).to_have_count(0)
  ap.get_by_role('button',name='Catálogo',exact=True).click();ap.screenshot(path=str(OUT/'inicio-rosa.png'),full_page=True)
  # Formulario real: crear producto nuevo con imagen desde el selector de archivos.
  ap.get_by_role('button',name='Productos',exact=True).click();ap.get_by_role('button',name='+ Nuevo Producto',exact=True).click()
  modal=ap.get_by_role('dialog');modal.get_by_label('Nombre del producto',exact=True).fill('Foto nueva '+suffix)
  modal.get_by_label('Precio en soles (S/)',exact=True).fill('15');modal.get_by_label('Stock disponible (unidades)',exact=True).fill('5')
  modal.locator('input[type="file"]').set_input_files(str(OUT/'foto-prueba.png'))
  modal.locator('input[type="checkbox"]').last.check()
  ap.screenshot(path=str(OUT/'nuevo-producto-imagen.png'),full_page=True)
  save=modal.locator('button.primary').last
  with ap.expect_response(lambda r:r.request.method=='PUT' and '/imagen' in r.url) as upload:save.click()
  assert upload.value.status==204
  expect(modal).to_have_count(0)
  nuevo=next(x for x in request('/productos') if x['nombre']=='Foto nueva '+suffix)
  ap.get_by_role('searchbox').fill('Foto nueva '+suffix)
  ap.get_by_role('button',name='Editar producto Foto nueva '+suffix,exact=True).click()
  modal=ap.get_by_role('dialog')
  other=io.BytesIO();Image.new('RGB',(240,180),'purple').save(other,'PNG')
  modal.locator('input[type="file"]').set_input_files({'name':'otra.png','mimeType':'image/png','buffer':other.getvalue()})
  with ap.expect_response(lambda r:r.request.method=='PUT' and '/imagen' in r.url) as replaced:modal.get_by_role('button',name='Guardar cambios',exact=True).click()
  assert replaced.value.status==204
  expect(modal).to_have_count(0)
  ap.get_by_role('button',name='Editar producto Foto nueva '+suffix,exact=True).click()
  modal=ap.get_by_role('dialog');modal.get_by_role('button',name='Quitar imagen al guardar',exact=True).click()
  with ap.expect_response(lambda r:r.request.method=='DELETE' and '/imagen' in r.url) as deleted:modal.get_by_role('button',name='Guardar cambios',exact=True).click()
  assert deleted.value.status==204
  photo(f'/productos/{nuevo["id"]}/imagen',method='GET',expected=404)
  ap.set_viewport_size({'width':390,'height':844});ap.get_by_role('button',name='Catálogo',exact=True).click();ap.screenshot(path=str(OUT/'inicio-movil.png'),full_page=True)
  assert ap.evaluate('document.documentElement.scrollWidth <= innerWidth')
  evidence.update({'venta':sale['id'],'cancelada':rejected['id'],'PDF':'descarga real desde Angular; backend rechaza no pagadas y sin JWT','stock':'compensacion y clave de reintento verificadas','pantallas':'roles, filtros, detalle, vista previa, creación, reemplazo y borrado de foto desde Angular','movil':'390px sin desbordamiento horizontal'})
  OUT.joinpath('resultado.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n');print(json.dumps(evidence,ensure_ascii=False,indent=2))
  browser.close()
if __name__=='__main__':main()
