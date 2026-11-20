"""Verifica la guía documental de Nikol contra el código fijado en Git."""
from pathlib import Path
import hashlib,json,subprocess
import fitz
ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent
meta=json.loads((OUT/'Nikol-referencias.json').read_text()); rev=meta['commit']
def read(p):return subprocess.check_output(['git','show',f'{rev}:{p}'],cwd=ROOT,text=True)
norm=lambda s:''.join(s.split())
doc=fitz.open(OUT/'Nikol-Venta-e-Institucion.pdf'); texts=[p.get_text() for p in doc]; text='\n'.join(texts)
md=(OUT/'Nikol-Venta-e-Institucion.md').read_text()
assert len(doc.get_toc())>30
assert all(len(t)>70 for t in texts)
for r in meta['referencias']:
 data=read(r['path'])
 if r['needle']:assert r['needle'] in data.splitlines()[r['line']-1],r
 assert norm(r['path']) in norm(text),r['path']
printed={x['path'] for x in meta['fuentes']}
tracked=subprocess.check_output(['git','ls-tree','-r','--name-only',rev],cwd=ROOT,text=True).splitlines()
expected={p for p in tracked if any(p.startswith(f'services/garritas-{d}-ms/src/') for d in ['venta','institucion']) and p.endswith('.java')}
assert expected<=printed,expected-printed
for item in meta['fuentes']:
 data=read(item['path']);assert hashlib.sha256(data.encode()).hexdigest()==item['sha256']
 numbered='\n'.join(f'{i:4}  {line}'.rstrip() for i,line in enumerate(data.splitlines(),1))
 assert numbered in md,item['path']
for item in meta['lectura_comentada']:
 assert '\n'.join(read(item['path']).splitlines()[item['start_line']-1:item['end_line']])==item['fragmento']
 for explanation in item['explicaciones']:assert explanation in md
assert text.count('Para qué sirve en Garritas')==len(meta['lectura_comentada'])
for i,p in enumerate(doc):
 assert all(w[0]>=0 and w[2]<=p.rect.width+1 for w in p.get_text('words')),i+1
for needle in ['VentaService','SedePrestacion','styles.css','font-family','COMPENSANDO','Keycloak']:assert needle in text,needle
for needle in ['Código real · fragmento','Nikol ·','font-size: clamp']:
 for i,p in enumerate(doc):
  if needle in p.get_text() and i>3:
   p.get_pixmap(matrix=fitz.Matrix(1.3,1.3)).save('/tmp/nikol-muestra-'+str(i+1)+'.png');break
report={'commit':rev,'alcance':'Verificación documental, no ejecución funcional de la aplicación.','paginas':len(doc),'marcadores':len(doc.get_toc()),'referencias':len(meta['referencias']),'archivos_completos':len(printed),'java_y_pruebas_de_venta_institucion':len(expected),'bloques_con_explicacion_al_costado':len(meta['lectura_comentada']),'enlaces':sum(len(p.get_links()) for p in doc),'codigo_y_lineas':'coinciden con Git','texto_seleccionable':True,'sin_paginas_vacias_ni_desbordamiento_horizontal':True}
(OUT/'Nikol-verificacion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
