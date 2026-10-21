"""Placement study. Source meshes remain untouched; all coordinates in mm."""
from pathlib import Path
import json
import numpy as np
import trimesh
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'design/output'
scan = trimesh.load(ROOT/'reference/cluster_scan/cluster_onshape_reference_mm.stl')
context = trimesh.load(ROOT/'reference/cage_scan/dash_surroundings_mm.stl')
cage = trimesh.load(ROOT/'reference/cage_scan/cage_primary_tubes_mm.stl')
tree = cKDTree(context.vertices)
cage_tree = cKDTree(cage.vertices)
frames=json.loads((ROOT/'geometry/frames_and_placement.json').read_text())

def rotation(pitch):
    a=np.deg2rad(pitch); c,s=np.cos(a),np.sin(a)
    return np.array([[-1,0,0],[0,-s,-c],[0,-c,s]])

def segment_distance(points,a,b):
    a,b=np.array(a),np.array(b); v=b-a
    t=np.clip((points-a)@v/(v@v),0,1)
    return np.linalg.norm(points-a-t[:,None]*v,axis=1)

def tube_clearance(points):
    ds=[segment_distance(points,[0,0,0],[782.252,0,0])-22.225]
    for arm in frames['cage']['arms'].values():
        ds.append(segment_distance(points,arm['at_bar_plane'],arm['at_y_minus_100'])-22.225)
    return np.min(ds)

rows=[]
v=scan.vertices[::5]
for pitch in [24,28,32]:
    r=rotation(pitch)
    for ty in np.arange(-80,61,10):
        for tz in np.arange(70,121,5):
            p=v@r.T+[262,ty,tz]
            tc=tube_clearance(p)
            if tc<4: continue
            dc=tree.query(p)[0].min()
            if dc<4: continue
            rows.append({'pitch':pitch,'ty':int(ty),'tz':int(tz),'top':round(float(p[:,2].max()),2),
                         'tube_gap':round(float(tc),2),'context_vertex_gap':round(float(dc),2),
                         'front_y':round(float(p[:,1].min()),2),'back_y':round(float(p[:,1].max()),2)})
rows.sort(key=lambda a:(a['top'],abs(a['ty'])))
(OUT/'placement_candidates.json').write_text(json.dumps(rows,indent=2))
print('BEST',json.dumps(rows[:35],indent=2))
for pitch in [28]:
    for ty in [-60,-40,-20,0,20]:
        filtered=[a for a in rows if a['pitch']==pitch and a['ty']==ty]
        print('FIRST for ty',ty,filtered[:1])

