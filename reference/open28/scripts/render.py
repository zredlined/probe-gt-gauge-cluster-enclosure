"""Blender render of real source meshes and generated parts, not illustrative geometry."""
import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'design/renders'
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)

def mat(name,c,metal=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*c,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*c,1)
    p.inputs['Roughness'].default_value=.65; p.inputs['Metallic'].default_value=metal
    return m
gold=mat('Existing cage / ochre',(.48,.30,.085),.3)
grey=mat('Scanned surroundings',(.30,.33,.34))
ivory=mat('Mount / warm grey',(.69,.70,.66))
orange=mat('Service hardware / orange',(.95,.19,.025),.2)
dark=mat('Existing cluster',(.14,.16,.17))
graphite=mat('Mount / graphite',(.055,.067,.071))
steel=mat('Fasteners / black oxide',(.08,.085,.09),.6)

def stl(path,name,m):
    bpy.ops.wm.stl_import(filepath=str(path)); ob=bpy.context.object; ob.name=name
    ob.data.materials.clear(); ob.data.materials.append(m)
    return ob

placement=ROOT/'design/output/placement.json'
if placement.exists(): T=json.loads(placement.read_text())['T']
else:
    a=math.radians(28); T=[[-1,0,0,262],[0,-math.sin(a),-math.cos(a),-30],[0,-math.cos(a),math.sin(a),100],[0,0,0,1]]

bpy.ops.wm.ply_import(filepath=str(ROOT/'onshape_reference_package/cluster_onshape_reference_color.ply'))
cluster=bpy.context.object; cluster.name='Existing cluster scan'; cluster.matrix_world=Matrix(T)
cm=mat('Captured scan colour',(.2,.2,.2)); cluster.data.materials.clear(); cluster.data.materials.append(cm)
if cluster.data.color_attributes:
    attr=cm.node_tree.nodes.new('ShaderNodeVertexColor'); attr.layer_name=cluster.data.color_attributes[0].name
    cm.node_tree.links.new(attr.outputs['Color'],cm.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
cage=stl(ROOT/'reference/cage_scan/cage_primary_tubes_mm.stl','Existing cage',gold)
context=stl(ROOT/'reference/cage_scan/dash_surroundings_mm.stl','Scanned context',grey)
parts=[]
for path in sorted((ROOT/'design/output/assembly').glob('*.stl')):
    parts.append(stl(path,path.stem,orange if 'spacer' in path.stem else graphite))
hardware=[]
for path in sorted((ROOT/'design/output/hardware').glob('*.stl')):
    hardware.append(stl(path,path.stem,steel))

scene=bpy.context.scene
scene.render.engine='CYCLES'; scene.cycles.samples=32
scene.cycles.use_denoising=True
scene.world.color=(.65,.65,.65)
scene.render.resolution_x=1500; scene.render.resolution_y=1050; scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
scene.render.image_settings.file_format='PNG'; scene.render.film_transparent=False
def area(name,loc,power,size):
    bpy.ops.object.light_add(type='AREA',location=loc); l=bpy.context.object; l.name=name
    l.data.energy=power; l.data.shape='DISK'; l.data.size=size
    l.rotation_euler=(Vector((260,0,70))-l.location).to_track_quat('-Z','Y').to_euler()
area('Key',(0,-450,700),17000000,600)
area('Fill',(800,150,450),13000000,500)
area('Rim',(-300,300,200),10000000,400)
bpy.ops.object.camera_add(); cam=bpy.context.object; scene.camera=cam; cam.data.type='ORTHO'; cam.data.clip_end=10000
def render(name,loc,target,scale,ctx=True,cg=True):
    context.hide_render=not ctx; cage.hide_render=not cg
    cam.location=loc; cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=scale
    scene.render.filepath=str(OUT/(name+'.png'))
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'design/output/review.blend'))
    bpy.ops.render.render(write_still=True)
render('01-installed-oblique',(900,-1000,620),(260,-15,70),680)
render('02-rear-open',(760,750,450),(262,-15,65),540,False)
render('03-side',(1100,-25,130),(262,-15,90),440)
render('04-front',(262,-1100,400),(262,-20,100),500,False)
cluster.hide_render=True
render('06-mount-only',(760,750,450),(262,-15,65),540,False)
cluster.hide_render=False
# Dedicated connector access review: volume proxies, not actual plug geometry.
cyan=mat('Reserved plug volume',(.07,.49,.65))
for side in ['driver','passenger']:
    ob=stl(ROOT/f'design/output/{side}_ribbon_keepout.stl',side+' plug allowance',cyan)
    mod=ob.modifiers.new('Keepout wire outline','WIREFRAME');mod.thickness=.8;mod.use_replace=True
render('07-ribbon-access',(470,900,370),(262,-15,75),510,False,False)
