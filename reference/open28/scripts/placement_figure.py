from pathlib import Path
import os,json,numpy as np,trimesh
os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).resolve().parents[1]/'.cache/matplotlib'))
os.environ.setdefault('XDG_CACHE_HOME',str(Path(__file__).resolve().parents[1]/'.cache'))
from scipy.spatial import ConvexHull
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Circle,Rectangle
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'design/output'
F=json.loads((ROOT/'geometry/frames_and_placement.json').read_text())
T=np.array(json.loads((OUT/'placement.json').read_text())['T'])
scan=trimesh.load(ROOT/'reference/cluster_scan/cluster_onshape_reference_mm.stl')
new=trimesh.transform_points(scan.vertices,T)
old=trimesh.transform_points(scan.vertices,np.array(F['placements']['v07']['T']))
# Conservative allowance: +9 mm beyond the foremost scanned surface. This is
# deliberately NOT asserted to be the actual clear-lens geometry or face datum.
v=scan.vertices[scan.vertices[:,2]>36]
h=ConvexHull(v[:,:2]);xy=v[h.vertices,:2]
zfront=float(scan.bounds[1,2]);lens_front=np.c_[xy,np.full(len(xy),zfront+9)]
lens_back=np.c_[xy,np.full(len(xy),zfront)]
points=np.vstack([lens_front,lens_back]);lh=ConvexHull(points)
faces=lh.simplices.copy();tri=points[faces]
norm=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);flip=np.einsum('ij,ij->i',norm,tri.mean(axis=1)-points.mean(axis=0))<0
faces[flip]=faces[flip][:,::-1]
lens=trimesh.Trimesh(points,faces,process=True)
lens.apply_transform(T);lens.export(OUT/'lens_allowance.stl')

plt.rcParams.update({'font.family':'sans-serif','font.size':11})
fig,axes=plt.subplots(1,2,figsize=(14,7),gridspec_kw={'width_ratios':[1.1,1]},facecolor='#f1f0e9')
for ax in axes:
 ax.set_facecolor('#f1f0e9');ax.spines[['top','right']].set_visible(False);ax.grid(alpha=.14);ax.set_aspect('equal')
def hullplot(ax,p,color,alpha,label):
 h=ConvexHull(p);ax.add_patch(Polygon(p[h.vertices],closed=True,color=color,alpha=alpha,label=label))
ax=axes[0]
oldbox=json.loads((ROOT/'geometry/placement_checks_v07.json').read_text())['enclosure_bbox_car']
lo,hi=np.array(oldbox)
ax.add_patch(Rectangle((lo[1],lo[2]),hi[1]-lo[1],hi[2]-lo[2],fill=False,edgecolor='#a35e46',linestyle='--',linewidth=2,label='Previous enclosure: recorded bounding box'))
hullplot(ax,old[:,1:],'#bcac97',.4,'Cluster in previous placement')
hullplot(ax,new[:,1:],'#343f42',.85,'New cluster placement')
hullplot(ax,lens.vertices[:,1:],'#609daa',.5,'Conservative lens allowance')
ax.add_patch(Circle((0,0),22.225,color='#b58a3f',label='44.45 mm dash bar'))
for path in (OUT/'assembly').glob('*.stl'):
 m=trimesh.load(path);hullplot(ax,m.vertices[:,1:],'#e67b3c',.12,None)
ax.set_xlim(-150,165);ax.set_ylim(-50,305);ax.set_xlabel('Vehicle Y (mm)   ← driver     windshield →');ax.set_ylabel('Height above dash-bar centre (mm)')
ax.set_title('Lower position / no tall enclosure',loc='left',fontweight='bold',pad=18)
ax.legend(loc='upper left',bbox_to_anchor=(0,-.18),frameon=False,fontsize=8,ncols=2)
ax.annotate('',xy=(130,lens.bounds[1,2]),xytext=(130,hi[2]),arrowprops={'arrowstyle':'<->','color':'#a35e46'})
ax.text(120,240,f'{hi[2]-lens.bounds[1,2]:.0f} mm lower\nincl. lens allowance',ha='right',fontsize=10,color='#78412e')
ax=axes[1]
hullplot(ax,new[:,[0,2]],'#343f42',.75,'Cluster')
for path in (OUT/'assembly').glob('*.stl'):
 m=trimesh.load(path);hullplot(ax,m.vertices[:,[0,2]],'#e67b3c',.30,None)
ax.add_patch(Rectangle((45,-22.225),450,44.45,color='#b58a3f',alpha=.5))
ax.set_xlim(45,490);ax.set_ylim(-50,305);ax.set_xlabel('Vehicle X (mm)   driver side → passenger side');ax.set_ylabel('Height above dash-bar centre (mm)')
ax.set_title('Mount stays below the cluster crown',loc='left',fontweight='bold',pad=18)
ax.text(265,255,'28° lean back\nNo front lip or brow\nRear connectors stay open',ha='center',va='top',linespacing=1.6)
fig.suptitle('OPEN / 28     •     packaging study',x=.08,y=.98,ha='left',fontsize=20,fontweight='bold')
fig.text(.08,.03,'Orthographic geometry comparison. The old enclosure is a bounding box, not a reconstructed shell.\nEye position, wheel sweep and windshield opening are unmeasured; this is not a validated road sightline.',fontsize=10,color='#555a59')
fig.subplots_adjust(left=.08,right=.97,top=.87,bottom=.28,wspace=.24)
fig.savefig(ROOT/'design/renders/05-placement-comparison.png',dpi=160,facecolor=fig.get_facecolor())
report={'new_scan_top_mm':round(new[:,2].max(),2),'conservative_lens_top_mm':round(lens.bounds[1,2],2),
 'old_recorded_enclosure_top_mm':hi[2],'reduction_including_conservative_lens_mm':round(hi[2]-lens.bounds[1,2],2),
 'lens_envelope_method':'XY convex hull of scan vertices with scan Z>36; front scan maximum Z plus 9 mm. Conservative packaging proxy, not actual lens reconstruction.'}
(OUT/'placement_summary.json').write_text(json.dumps(report,indent=2));print(report)
