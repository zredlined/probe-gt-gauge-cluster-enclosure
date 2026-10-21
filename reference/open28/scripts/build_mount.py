"""Probe / OPEN 28: reproducible CadQuery prototype. Millimeters throughout.

Source data are references; parts are new parametric B-rep solids.
Print exports are oriented individually, assembly exports share vehicle frame.
"""
from pathlib import Path
import json, math
import numpy as np
import cadquery as cq
import trimesh

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'design/output'
for f in ['assembly','print','step','fit_samples']: (OUT/f).mkdir(exist_ok=True)
F=json.loads((ROOT/'geometry/frames_and_placement.json').read_text())
H=F['cluster']['holes_scan']
PITCH=28.0; OFFSET=np.array([262.,-40.,95.])
a=math.radians(PITCH); c,s=math.cos(a),math.sin(a)
R=np.array([[-1,0,0],[0,-s,-c],[0,-c,s]])
T=np.eye(4);T[:3,:3]=R;T[:3,3]=OFFSET
(OUT/'placement.json').write_text(json.dumps({'pitch_degrees':PITCH,'T':T.tolist(),
 'lens_allowance_mm':9,'lens_datum':'user: gauge faces; conservative scan front envelope used for checks',
 'status':'prototype, physical placement and eye point unverified'},indent=2))
M=cq.Matrix(T.tolist())

def cylinder(p,n,r,h):
    return cq.Solid.makeCylinder(r,h,cq.Vector(*p),cq.Vector(*n))
def box(mins,maxs):
    return cq.Solid.makeBox(*(np.array(maxs)-mins),cq.Vector(*mins))
def fuse(shapes):
    out=shapes[0]
    for b in shapes[1:]:out=out.fuse(b)
    return out.clean()
def prism(x0,x1,points):
    pl=cq.Plane(origin=(x0,0,0),xDir=(0,1,0),normal=(1,0,0))
    return cq.Workplane(pl).polyline(points).close().extrude(x1-x0).val()
def bar(x0,x1,p,q,r):
    p,q=np.array(p,dtype=float),np.array(q,dtype=float); d=q-p; n=np.array([-d[1],d[0]])/np.linalg.norm(d)*r
    return fuse([prism(x0,x1,[p+n,q+n,q-n,p-n]),
                 cylinder([x0,*p],[1,0,0],r,x1-x0),cylinder([x0,*q],[1,0,0],r,x1-x0)])
def holex(shape,yz,d):
    return shape.cut(cylinder([-1000,*yz],[1,0,0],d/2,2000))
def car(shape):return shape.rotate((0,0,0),(0,1,-1),180).rotate((0,0,0),(1,0,0),-PITCH).translate(tuple(OFFSET))
def uncar(shape):return shape.translate(tuple(-OFFSET)).rotate((0,0,0),(1,0,0),PITCH).rotate((0,0,0),(0,1,-1),180)
def inverse_yz(yz):
    return (R.T@(np.array([262.,*yz])-OFFSET))[1:]

manifest=[]; assembly=cq.Assembly(name='OPEN_28_prototype')
def save(name,shape,frame='car',print_axis='x',sample=False):
    shape=shape.clean()
    if not shape.isValid(): raise ValueError('Invalid B-rep '+name)
    if len(shape.Solids())!=1:raise ValueError(f'{name}: {len(shape.Solids())} disconnected solids')
    installed=car(shape) if frame=='scan' else shape
    if not sample:cq.exporters.export(installed,str(OUT/'assembly'/f'{name}.stl'),tolerance=.08,angularTolerance=.12)
    cq.exporters.export(shape,str(OUT/'step'/f'{name}.step'))
    printed=shape.rotate((0,0,0),(0,1,0),-90 if print_axis=='x' else 90) if print_axis in ['x','neg_x'] else shape
    b=printed.BoundingBox();printed=printed.translate((-b.xmin,-b.ymin,-b.zmin))
    cq.exporters.export(printed,str(OUT/('fit_samples' if sample else 'print')/f'{name}.stl'),tolerance=.06,angularTolerance=.1)
    mesh=trimesh.load(OUT/('fit_samples' if sample else 'print')/f'{name}.stl')
    if not mesh.is_watertight: raise ValueError('Nonmanifold export '+name)
    if max(mesh.extents)>240:raise ValueError('Exceeds conservative P1S footprint '+name)
    manifest.append({'name':name,'frame':frame,'print_size_mm':mesh.extents.round(2).tolist(),
      'solid_volume_cm3':round(shape.Volume()/1000,2),'watertight':bool(mesh.is_watertight),
      'connected_brep_solids':len(shape.Solids()),'sample':sample})
    if not sample:assembly.add(installed,name=name,color=cq.Color(.72,.72,.68))
    print(name,manifest[-1],flush=True)

def clamp(cx):
    # x axis lies along existing dash crossbar. 0.5 mm half-gap, bore 45.25.
    x0,x1=cx-16,cx+16
    ring=cylinder([x0,0,0],[1,0,0],30,32)
    ears=[box([x0,-12,z-8],[x1,12,z+8]) for z in [-37,37]]
    whole=fuse([ring,*ears]).cut(cylinder([x0-1,0,0],[1,0,0],22.625,34))
    for z in [-37,37]:whole=whole.cut(cylinder([cx,-30,z],[0,1,0],3.3,60))
    rear=whole.intersect(box([x0-1,-100,-100],[x1+1,-.5,100])).rotate((0,0,0),(1,0,0),-90)
    front=whole.intersect(box([x0-1,.5,-100],[x1+1,100,100])).rotate((0,0,0),(1,0,0),-90)
    tabs=[cylinder([x0,y,18],[1,0,0],6,32) for y in [-25,25]]
    rear=fuse([rear,*tabs]).cut(cylinder([x0-1,0,0],[1,0,0],22.625,34))
    for p in [[-25,18],[25,18]]:rear=holex(rear,p,5.5)
    return rear,front

spec=[('passenger',-161.,-157.,-125.,['B2','B3'],'T1',-1),
      ('driver',148.7,109.,144.7,['B5','B6'],'T2',1)]
for side,xp,xlo,xhi,holes,ear,sign in spec:
    # Clamp inner edge meets the inboard face of the side plate.
    plate_car_x=262-xp; cx=375 if side=='passenger' else plate_car_x+sign*20
    rear,front=clamp(cx)
    save(f'{side}_clamp_body',rear);save(f'{side}_clamp_cap',front)
    if side=='passenger':
        for i,y in enumerate([-25,25]):
            spacer=cylinder([391,y,18],[1,0,0],6,28).cut(cylinder([390,y,18],[1,0,0],2.75,30))
            save(f'passenger_bridge_spacer_{i+1}',spacer)
    lower_nodes=[np.array([97.,-22.]),np.array([104.,-30.])]
    upper_nodes=[np.array([-34.,-48.]),np.array([-48.,-37.])]
    clamp_nodes=[inverse_yz([-25,18]),inverse_yz([25,18])]
    spine_low=np.array([40.,-56.]); spine_top=np.array([-43.,-56.])
    links=[(lower_nodes[0],lower_nodes[1]),(lower_nodes[1],spine_low),
           (spine_low,spine_top),(spine_top,upper_nodes[0]),(upper_nodes[0],upper_nodes[1]),
           (clamp_nodes[0],spine_low),(clamp_nodes[1],spine_low),
           (clamp_nodes[0],lower_nodes[1]),(clamp_nodes[1],lower_nodes[0])]
    plate=fuse([bar(xp-4,xp+4,p,q,7.5) for p,q in links])
    # Real cage exclusion, not a guessed planar outline.
    bore_car=cylinder([0,0,0],[1,0,0],24.225,800)
    plate=plate.cut(uncar(bore_car))
    for n in lower_nodes+upper_nodes:plate=holex(plate,n,4.5)
    for n in clamp_nodes:
        plate=holex(plate,n,5.5)
        entry=[xp-4 if sign<0 else xp+4,*n]
        axis=[1 if sign<0 else -1,0,0]
        plate=plate.cut(cq.Solid.makeCone(5.3,2.75,2.55,cq.Vector(*entry),cq.Vector(*axis)))
    save(f'{side}_side_plate',plate,'scan')

    lower=prism(xlo,xhi,[(78,-18),(92,-17),(111,-19),(111,(17-s*111)/c),(78,(17-s*78)/c)])
    for hid in holes:
        p=np.array(H[hid]['centre']);n=np.array(H[hid]['normal']);n/=np.linalg.norm(n)
        lower=lower.fuse(cylinder(p-n*12,n,6.6,11.2))
    for hid in holes:
        p=np.array(H[hid]['centre']);n=np.array(H[hid]['normal']);n/=np.linalg.norm(n)
        lower=lower.cut(cylinder(p-n*80,n,2.25,90))
        pc=R@p+OFFSET;nc=R@n
        seat_depth=(pc[1]+57)/nc[1]-1.8
        lower=lower.cut(cylinder(p-n*80,n,5.2,80-seat_depth))
    for node in lower_nodes:lower=holex(lower,node,4.5)
    save(f'{side}_lower_tab_adapter',lower,'scan','neg_x' if side=='passenger' else 'x')

    p=np.array(H[ear]['centre']);n=np.array(H[ear]['normal']);n/=np.linalg.norm(n)
    # Ear seat follows the measured 3D normal. Body stays behind/outside housing.
    ex0=min(xp-4,p[0]-n[0]*28-7); ex1=max(xp+4,p[0]-n[0]*28+7)
    # Adapter sits on the outboard side of plate, except local pad at OEM hole.
    if sign<0:ex1=xp-4
    else:ex0=xp+4
    earbody=prism(ex0,ex1,[(-58,-56),(-27,-56),(-27,-42),(-36,-28),(-40,8),(-47,8),(-58,-25)])
    earbody=earbody.intersect(uncar(box([-1000,-1000,-1000],[1000,1000,(R@p+OFFSET)[2]+6.5])))
    # 30 mm inclined pad column plus a rear bridge to the side-fastening block.
    earbody=earbody.fuse(cylinder(p-n*32,n,7.3,20))
    earbody=earbody.fuse(cq.Solid.makeCone(7.3,5.0,11.2,cq.Vector(*(p-n*12)),cq.Vector(*n)))
    # Bridge in x from inclined column to the adapter polygon.
    q=p-n*27
    earbody=earbody.fuse(cylinder([min(ex0,q[0]-6),q[1],q[2]],[1,0,0],7,max(ex1,q[0]+6)-min(ex0,q[0]-6)))
    earbody=earbody.cut(cylinder(p-n*100,n,2.25,115))
    # Rear nut/socket access: nut seats 28 mm behind the OEM reference face.
    # This keeps the ear bolt to M4x45 rather than an inaccessible 80+ mm screw.
    earbody=earbody.cut(cylinder(p-n*110,n,5.0,82))
    for node in upper_nodes:earbody=holex(earbody,node,4.5)
    save(f'{side}_upper_ear_adapter',earbody,'scan')

upper,cap=clamp(375)
for label,shape in [('upper',upper),('lower',cap)]:
    coupon=shape.intersect(box([369,-100,-100],[381,100,100]))
    save(f'fit_45p25_{label}',coupon,sample=True)
assembly.save(str(OUT/'open28_assembly.step'))
(OUT/'parts_manifest.json').write_text(json.dumps(manifest,indent=2))
print('COMPLETE',flush=True)
