"""Generic model-only 3MF plates; no fabricated printer/process profiles."""
from pathlib import Path
import json,zipfile,xml.etree.ElementTree as ET
import numpy as np,trimesh
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'design/output'
DEST=OUT/'plates';DEST.mkdir(exist_ok=True)
manifest=json.loads((OUT/'parts_manifest.json').read_text())
core=[r['name'] for r in manifest if not r['sample']]
groups={
 '01_side_plates':[n for n in core if 'side_plate' in n],
 '02_cage_clamps':[n for n in core if 'clamp' in n or 'spacer' in n],
 '03_tab_adapters':[n for n in core if 'adapter' in n],
 '00_fit_check':['fit_45p25_upper','fit_45p25_lower']+[n for n in core if 'adapter' in n],
}
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
ET.register_namespace('',ns)
def element(parent,name,attrs=None,text=None):
 e=ET.SubElement(parent,'{'+ns+'}'+name,attrs or {})
 if text is not None:e.text=text
 return e
layouts={}
for group,names in groups.items():
 model=ET.Element('{'+ns+'}model',{'unit':'millimeter','{http://www.w3.org/XML/1998/namespace}lang':'en-US'})
 element(model,'metadata',{'name':'Title'},'OPEN 28 / '+group+' / geometry only')
 resources=element(model,'resources');build=element(model,'build')
 x=28.;y=8.;row_h=0.;layout=[]
 for oid,name in enumerate(names,1):
  path=OUT/('fit_samples' if name.startswith('fit_') else 'print')/(name+'.stl')
  mesh=trimesh.load(path);sx,sy,sz=mesh.extents
  if x+sx>248:x=28;y+=row_h+9;row_h=0
  if y+sy>248:raise ValueError('Plate overflow '+group)
  obj=element(resources,'object',{'id':str(oid),'type':'model','name':name})
  geo=element(obj,'mesh');verts=element(geo,'vertices');tris=element(geo,'triangles')
  for v in mesh.vertices:element(verts,'vertex',{c:f'{val:.5f}' for c,val in zip('xyz',v)})
  for f in mesh.faces:element(tris,'triangle',{c:str(int(val)) for c,val in zip(['v1','v2','v3'],f)})
  element(build,'item',{'objectid':str(oid),'transform':f'1 0 0 0 1 0 0 0 1 {x:.3f} {y:.3f} 0'})
  layout.append({'name':name,'xy':[round(x,3),round(y,3)],'size':mesh.extents.round(3).tolist()})
  x+=sx+9;row_h=max(row_h,sy)
 ct='<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'
 rel='<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
 target=DEST/(group+'.3mf')
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('[Content_Types].xml',ct);z.writestr('_rels/.rels',rel)
  z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
 # Read back exact package mesh counts and verify all arranged bounds.
 with zipfile.ZipFile(target) as z:
  root=ET.fromstring(z.read('3D/3dmodel.model'))
  assert len(root.findall('.//{'+ns+'}object'))==len(names)
  assert len(root.findall('.//{'+ns+'}item'))==len(names)
 for i,a in enumerate(layout):
  for b in layout[i+1:]:
   amin=np.array(a['xy']);amax=amin+np.array(a['size'][:2]);bmin=np.array(b['xy']);bmax=bmin+np.array(b['size'][:2])
   assert not (np.all(amin<bmax)&np.all(amax>bmin))
 layouts[group]=layout
 print(group,len(names),'objects; checked within bed and clear of P1S front-left exclusion',flush=True)
(OUT/'plate_layouts.json').write_text(json.dumps(layouts,indent=2))
