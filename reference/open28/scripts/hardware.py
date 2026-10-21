"""Nominal fastener envelopes for assembly review; confirm purchased hardware."""
from pathlib import Path
import json,itertools,numpy as np,cadquery as cq,trimesh
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'design/output'
(OUT/'hardware').mkdir(exist_ok=True)
T=np.array(json.loads((OUT/'placement.json').read_text())['T']);R=T[:3,:3]
H=json.loads((ROOT/'geometry/frames_and_placement.json').read_text())['cluster']['holes_scan']
manifest=json.loads((OUT/'parts_manifest.json').read_text())
def car(shape):return shape.rotate((0,0,0),(0,1,-1),180).rotate((0,0,0),(1,0,0),-28).translate(tuple(T[:3,3]))
def cyl(p,n,r,h):return cq.Solid.makeCylinder(r,h,cq.Vector(*p),cq.Vector(*n))
solids={}
for item in manifest:
 if item['sample']:continue
 sh=cq.importers.importStep(str(OUT/'step'/f"{item['name']}.step")).val()
 solids[item['name']]=car(sh) if item['frame']=='scan' else sh
hardware={};rows=[]
def countersunk(name,face,axis,length,nut_face):
 p=np.array(face,dtype=float);n=np.array(axis,dtype=float);p=p+n*.3
 head=cq.Solid.makeCone(5,2.5,2.5,cq.Vector(*p),cq.Vector(*n))
 bolt=head.fuse(cyl(p+n*2.5,n,2.5,length-2.5))
 q=np.array(nut_face,dtype=float)
 washer=cyl(q,n,5.5,1).cut(cyl(q-n*.1,n,2.75,1.2))
 nut=cyl(q+n,n,4.8,5).cut(cyl(q+n*.9,n,2.65,5.2))
 shape=cq.Compound.makeCompound([bolt,washer,nut]);hardware[name]=shape
 cq.exporters.export(shape,str(OUT/'hardware'/f'{name}.stl'),tolerance=.1,angularTolerance=.15)
 grip=float((q+n-p)@n)
 rows.append({'name':name,'bolt':f'M5 x {length} countersunk 90deg (length includes head)','grip_to_nut_mm':round(grip,2),'thread_beyond_nut_mm':round(length-grip-5,2)})
def fastener(name,p,axis,dia,length,grip,nut_height=None):
 p=np.array(p,dtype=float);n=np.array(axis,dtype=float);n/=np.linalg.norm(n)
 wh=1.;headr={4:4.,5:4.5,6:5.5}[dia];headh=dia
 nutr={4:4.2,5:4.8,6:6.0}[dia]; nh=nut_height or {4:5,5:5,6:6}[dia]
 # p = underside of head; grip includes front washer, bodies, rear washer.
 bolt=cyl(p,n,dia/2,length).fuse(cyl(p-n*headh,n,headr,headh))
 washers=[]
 for dist in [0,grip-1]:
  washers.append(cyl(p+n*dist,n,headr+1,wh).cut(cyl(p+n*(dist-.1),n,dia/2+.25,wh+.2)))
 nut=cyl(p+n*grip,n,nutr,nh).cut(cyl(p+n*(grip-.1),n,dia/2+.15,nh+.2))
 shape=cq.Compound.makeCompound([bolt,*washers,nut])
 hardware[name]=shape
 cq.exporters.export(shape,str(OUT/'hardware'/f'{name}.stl'),tolerance=.1,angularTolerance=.15)
 rows.append({'name':name,'bolt':f'M{dia} x {length}','grip_to_nut_mm':round(float(grip),2),'thread_beyond_nut_mm':round(float(length-grip-nh),2)})

for side,cx in [('driver',133.3),('passenger',375)]:
 for i,y in enumerate([-37,37]):fastener(f'{side}_cage_{i+1}',[cx,y,13],[0,0,-1],6,40,26)
 for i,y in enumerate([-25,25]):
  if side=='driver':countersunk(f'{side}_plate_{i+1}',[109.3,y,18],[1,0,0],50,[149.3,y,18])
  else:countersunk(f'{side}_plate_{i+1}',[427,y,18],[-1,0,0],80,[359,y,18])
 for i,(y,z) in enumerate([(97,-22),(104,-30)]):
  q=np.array([0,y,z])@R.T+T[:3,3]
  if side=='driver':q[0]=108.3;direction=[1,0,0];length=55;grip=45.7
  else:q[0]=428;direction=[-1,0,0];length=50;grip=42
  fastener(f'{side}_lower_cross_{i+1}',q,direction,4,length,grip)
 # Upper adapters sit outboard of the side plates.
 shape=solids[f'{side}_upper_ear_adapter'];bb=shape.BoundingBox()
 for i,(y,z) in enumerate([(-34,-48),(-48,-37)]):
  q=np.array([0,y,z])@R.T+T[:3,3]
  if side=='driver':q[0]=118.3;direction=[-1,0,0];grip=q[0]-bb.xmin+1
  else:q[0]=418;direction=[1,0,0];grip=bb.xmax-q[0]+1
  # Provisional 35 mm permits the conservative adapter bounds.
  fastener(f'{side}_upper_cross_{i+1}',q,direction,4,35,grip)
 for hid in (['B5','B6','T2'] if side=='driver' else ['B2','B3','T1']):
  p=np.array(H[hid]['centre'])@R.T+T[:3,3];n=np.array(H[hid]['normal'])@R.T;n/=np.linalg.norm(n)
  if hid.startswith('T'):
   # Washer seats at d=28; nut begins at d=29 inside the access well.
   fastener(f'{hid}_oem',p+n*8,-n,4,45,37)
  else:
   d=(p[1]+57)/n[1]-1.8
   fastener(f'{hid}_oem',p+n*5.8,-n,4,25 if side=='driver' else 30,5.8+d+1)

hits=[]
for name,fast in hardware.items():
 b=fast.BoundingBox()
 for part,solid in solids.items():
  c=solid.BoundingBox()
  if b.xmin>c.xmax or b.xmax<c.xmin or b.ymin>c.ymax or b.ymax<c.ymin or b.zmin>c.zmax or b.zmax<c.zmin:continue
  vol=fast.intersect(solid).Volume()
  if vol>.1:hits.append({'fastener':name,'part':part,'overlap_mm3':round(vol,3)})
pair_hits=[]
for (na,sa),(nb,sb) in itertools.combinations(hardware.items(),2):
 b=sa.BoundingBox();c=sb.BoundingBox()
 if b.xmin>c.xmax or b.xmax<c.xmin or b.ymin>c.ymax or b.ymax<c.ymin or b.zmin>c.zmax or b.zmax<c.zmin:continue
 vol=sa.intersect(sb).Volume()
 if vol>.1:pair_hits.append({'a':na,'b':nb,'overlap_mm3':round(vol,3)})
ref_hits=[]
cable_hits=[]
for side,xmin in [('passenger',-185),('driver',155.5)]:
 keepout=car(cq.Solid.makeBox(18,90,70,cq.Vector(xmin,-18,-100)))
 for name,shape in hardware.items():
  v=keepout.intersect(shape).Volume()
  if v>.1:cable_hits.append({'connector':side,'hardware':name,'overlap_mm3':round(v,3)})
refs={name:trimesh.load(ROOT/f'reference/cage_scan/{file}') for name,file in [('context','dash_surroundings_mm.stl'),('cage','cage_primary_tubes_mm.stl')]}
cluster=trimesh.load(ROOT/'reference/cluster_scan/cluster_onshape_reference_mm.stl');cluster.apply_transform(T);refs['cluster']=cluster
for name in hardware:
 m=trimesh.load(OUT/'hardware'/f'{name}.stl')
 for label,ref in refs.items():
  if label=='cluster' and name.endswith('_oem'):continue
  v=ref.vertices;v=v[((v>=m.bounds[0])&(v<=m.bounds[1])).all(axis=1)]
  # Multiple closed overlapping fastener meshes: evaluate constituent convex-ish
  # solids separately in CAD for reliable inside tests, not union-ray parity.
  inside=sum(any(s.isInside(cq.Vector(*p),1e-5) for s in hardware[name].Solids()) for p in v)
  if inside:ref_hits.append({'fastener':name,'reference':label,'vertices_inside':inside})
(OUT/'hardware_check.json').write_text(json.dumps({'fasteners':rows,'part_intersections':hits,'hardware_intersections':pair_hits,'ribbon_keepout_intersections':cable_hits,'reference_vertices_inside':ref_hits,'limitation':'Nominal cylindrical head/nut envelopes. OEM tab thickness comes from prior notes. Purchased hardware, driver access and actual tightening require fit verification.'},indent=2))
print(json.dumps(hits,indent=2))
print('HARDWARE PAIRS',pair_hits,'REFERENCES',ref_hits)
print('CABLE INTERSECTIONS',cable_hits)
