"""Comprobación documental: rutas/líneas/código, PDF y enlaces. No prueba la aplicación."""
from pathlib import Path
import hashlib,json,subprocess
import fitz
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
meta=json.loads((OUT/'referencias.json').read_text());revision=meta['commit']
report={'commit':revision,'alcance':'Verificación documental; no repite pruebas funcionales ni ejecuta servicios.','guias':[]}
for who,filename,domains in [('Fio','Fio-Catalogo-y-Usuario',['catalogo','usuario']),('Deissy','Deissy-Citas-y-Envio',['citas','envio'])]:
 doc=fitz.open(OUT/(filename+'.pdf'));texts=[p.get_text() for p in doc];text='\n'.join(texts);norm=lambda s:''.join(s.split())
 assert len(doc.get_toc())>=20
 assert all(len(t)>70 for t in texts),[(i+1,len(t)) for i,t in enumerate(texts) if len(t)<=70]
 md=(OUT/(filename+'.md')).read_text()
 for item in meta['referencias'][who]:
  data=subprocess.check_output(['git','show',f'{revision}:{item["path"]}'],cwd=ROOT,text=True)
  if item['needle']:assert item['needle'] in data.splitlines()[item['line']-1],item
  assert norm(item['path']) in norm(text),item['path']
 printed={x['path'] for x in meta['fuentes'][who]}
 expected=set()
 tracked=subprocess.check_output(['git','ls-tree','-r','--name-only',revision],cwd=ROOT,text=True).splitlines()
 for d in domains:expected.update(p for p in tracked if p.startswith(f'services/garritas-{d}-ms/src/') and p.endswith('.java'))
 assert expected<=printed,expected-printed
 for item in meta['fuentes'][who]:
  data=subprocess.check_output(['git','show',f'{revision}:{item["path"]}'],cwd=ROOT,text=True)
  assert hashlib.sha256(data.encode()).hexdigest()==item['sha256']
  numbered='\n'.join(f'{i:4}  {line}'.rstrip() for i,line in enumerate(data.splitlines(),1))
  assert numbered in md,item['path']
 for i,p in enumerate(doc):
  assert all(w[0]>=0 and w[2]<=p.rect.width+1 for w in p.get_text('words')),(filename,i+1)
 assert 'MercadoPago' in norm(text) and 'simulado' in norm(text)
 assert 'Mapa completo' in text and 'Anexo:' in text
 for needle in (['SuscripcionService','InventarioEvents','LocalImages'] if who=='Fio' else ['CitaService','LogisticaService','Cobertura','DespachoService']):assert needle in text
 report['guias'].append({'integrante':who,'pdf':filename+'.pdf','paginas':len(doc),'marcadores':len(doc.get_toc()),'referencias':len(meta['referencias'][who]),'archivos_completos':len(printed),'clases_y_pruebas_de_los_dos_dominios':len(expected),'texto_seleccionable':True,'enlaces':sum(len(p.get_links()) for p in doc),'rutas_y_lineas':'coinciden con Git','codigo_completo':'coincide con fuente numerada','sin_paginas_vacias':True})
 # Muestras para inspección visual; temporales fuera del repositorio.
 for i,p in enumerate(doc):
  if ('Tu mapa:' in p.get_text() and i>2) or ('10. Suscripciones:' in p.get_text() and i>2):
   p.get_pixmap(matrix=fitz.Matrix(1.4,1.4)).save('/tmp/'+who+'-pagina-'+str(i+1)+'.png')
(OUT/'verificacion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
