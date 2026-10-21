"""Independent, approximate cluster-to-car placement clearance check."""
from pathlib import Path
import json,numpy as np,trimesh
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'design/output'
T=np.array(json.loads((OUT/'placement.json').read_text())['T'])
cluster=trimesh.load(ROOT/'reference/cluster_scan/cluster_onshape_reference_mm.stl');cluster.apply_transform(T)
context=trimesh.load(ROOT/'reference/cage_scan/dash_surroundings_mm.stl')
d=cKDTree(context.vertices).query(cluster.vertices)[0]
nearest=cluster.vertices[np.argsort(d)[:3000]];gaps=[]
for p in np.array_split(nearest,10):gaps.extend(trimesh.proximity.closest_point(context,p)[1])
F=json.loads((ROOT/'geometry/frames_and_placement.json').read_text());v=cluster.vertices
checks={'cluster_to_context_sampled_mm':float(min(gaps)),
 'method':'3000 cluster vertices nearest context vertices, then exact distances to context triangles; approximate minimum, not intersection proof.'}
segments=[('crossbar',[0,0,0],[782.252,0,0])]+[(name,data['at_bar_plane'],data['at_y_minus_100']) for name,data in F['cage']['arms'].items()]
for name,a,b in segments:
 a,b=np.array(a),np.array(b);vec=b-a;t=np.clip((v-a)@vec/(vec@vec),0,1)
 dist=np.linalg.norm(v-a-t[:,None]*vec,axis=1)-22.225
 checks[name+'_sampled_clearance_mm']=float(dist.min())
(OUT/'cluster_placement_check.json').write_text(json.dumps(checks,indent=2))
print(checks)
