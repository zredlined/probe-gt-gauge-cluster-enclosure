"""Repeatable geometric checks; open scans are not certified solid obstacles."""
from pathlib import Path
import json,itertools
import numpy as np
import trimesh
from scipy.spatial import cKDTree
import cadquery as cq
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'design/output'
T=np.array(json.loads((OUT/'placement.json').read_text())['T']); R=T[:3,:3]
def car(shape):return shape.rotate((0,0,0),(0,1,-1),180).rotate((0,0,0),(1,0,0),-28).translate(tuple(T[:3,3]))
cluster=trimesh.load(ROOT/'reference/cluster_scan/cluster_onshape_reference_mm.stl'); cluster.apply_transform(T)
context=trimesh.load(ROOT/'reference/cage_scan/dash_surroundings_mm.stl')
switch=trimesh.load(ROOT/'reference/cage_scan/master_switch_region_scan_mm.stl')
cage=trimesh.load(ROOT/'reference/cage_scan/cage_primary_tubes_mm.stl')
manifest=json.loads((OUT/'parts_manifest.json').read_text())
parts={p.stem:trimesh.load(p) for p in sorted((OUT/'assembly').glob('*.stl'))}
solids={}
for item in manifest:
 if item['sample']:continue
 name=item['name']; solid=cq.importers.importStep(str(OUT/'step'/f'{name}.step')).val()
 if item['frame']=='scan':solid=car(solid)
 solids[name]=solid
report={'method':'Exact B-rep part intersections; source-mesh vertices tested inside watertight parts; sampled surface-to-triangle distances. Open scans cannot prove no unobserved interference.','parts':{},'part_intersections':[]}
for a,b in itertools.combinations(solids,2):
 if not np.all(parts[a].bounds[1]>=parts[b].bounds[0]) or not np.all(parts[b].bounds[1]>=parts[a].bounds[0]):continue
 v=solids[a].intersect(solids[b]).Volume()
 if v>0.01:report['part_intersections'].append({'a':a,'b':b,'volume_mm3':round(v,3)})
for name,part in parts.items():
 row={}
 for ref_name,ref in [('cluster',cluster),('context',context),('switch',switch),('cage',cage)]:
  lo,hi=part.bounds
  near=ref.vertices[((ref.vertices>lo-.01)&(ref.vertices<hi+.01)).all(axis=1)]
  inside=part.contains(near) if len(near) else np.zeros(0,dtype=bool)
  row[ref_name+'_vertices_inside']=int(inside.sum())
  if inside.any():row[ref_name+'_collision_bbox']=np.array([near[inside].min(axis=0),near[inside].max(axis=0)]).round(2).tolist()
  # Deterministic samples + vertices: surface distance, not a rigorous minimum.
  samples=np.vstack([part.vertices, trimesh.sample.sample_surface(part,1500,seed=24)[0]])
  d=[]
  for batch in np.array_split(samples,max(1,len(samples)//500)):
   _,dist,_=trimesh.proximity.closest_point(ref,batch);d.extend(dist)
  row[ref_name+'_sampled_gap_mm']=round(float(min(d)),3)
 report['parts'][name]=row
 print(name,row,flush=True)

# Conservative ribbon envelopes in cluster scan frame; opening and latch geometry
# comes from previous notes, not a measured current harness routing.
ribbons=[]
for side,xc,h in [('passenger',-176,90),('driver',164.5,90)]:
 mesh=trimesh.creation.box(extents=[18,h,70]);mesh.apply_translation([xc,27,-65]);mesh.apply_transform(T)
 ribbons.append((side,mesh))
 mesh.export(OUT/f'{side}_ribbon_keepout.stl')
report['ribbon_keepout']={}
for side,mesh in ribbons:
 hit=[]
 # Exact boxes in local scan frame against the generated B-reps.
 ref=car(cq.Solid.makeBox(18,90,70,cq.Vector(-185 if side=='passenger' else 155.5,-18,-100)))
 for name,solid in solids.items():
  v=ref.intersect(solid).Volume()
  if v>.01:hit.append({'part':name,'volume_mm3':round(v,3)})
 report['ribbon_keepout'][side]=hit

report['cluster_bbox_car_mm']=cluster.bounds.round(2).tolist()
report['new_printed_mount_bbox_car_mm']=np.array([np.min([m.bounds[0] for m in parts.values()],axis=0),np.max([m.bounds[1] for m in parts.values()],axis=0)]).round(2).tolist()
report['old_enclosure_bbox_car_mm']=json.loads((ROOT/'geometry/placement_checks_v07.json').read_text())['enclosure_bbox_car']
(OUT/'geometry_check.json').write_text(json.dumps(report,indent=2))
print('INTERSECTIONS',report['part_intersections'],flush=True)
print('RIBBON',report['ribbon_keepout'],flush=True)
