"""Import final STL-kit assembly into a separate Blender scene and render it."""
from pathlib import Path
import bpy,json,numpy as np,math
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'exports/dragon-pla-kit-v03'
src=bpy.data.scenes.get('Dragon • Puffy Hoops 06')
assert src
name='Dragon • Fit Revision 03'
assert name not in bpy.data.scenes,'Preview already exists; inspect before replacing'
scene=src.copy();scene.name=name
# Use a separate collection tree to leave the visual master untouched.
for col in list(scene.collection.children):scene.collection.children.unlink(col)
for ob in list(scene.collection.objects):scene.collection.objects.unlink(ob)
for ob in src.objects:
    if ob.type in {'CAMERA','LIGHT'} or ob.name.startswith('STUDIO'):
        scene.collection.objects.link(ob)
manifest=json.loads((OUT/'manifest.json').read_text())
mats={}
for color,hx in manifest['colors'].items():
    rgb=[int(hx[i:i+2],16)/255 for i in (1,3,5)]
    rgba=tuple((v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4) for v in rgb)+(1.,)
    mat=bpy.data.materials.new('PRINT_V03_'+color);mat.use_nodes=True
    bsdf=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value=rgba
    bsdf.inputs['Roughness'].default_value=.62
    mat.diffuse_color=rgba;mats[color]=mat
for rec in json.loads((OUT/'work/assembly.json').read_text()):
    z=np.load(OUT/'work/assembly'/Path(rec['file']).name);mesh=bpy.data.meshes.new('KIT03_'+rec['name'])
    mesh.from_pydata((z['vertices']*.001).tolist(),[],z['faces'].tolist());mesh.update()
    for poly in mesh.polygons:poly.use_smooth=True
    if hasattr(mesh,'set_sharp_from_angle'):mesh.set_sharp_from_angle(angle=math.radians(35))
    ob=bpy.data.objects.new('KIT03_'+rec['name'],mesh);scene.collection.objects.link(ob)
    ob.data.materials.append(mats[rec['color']])
from mathutils import Vector
scene.camera=bpy.data.objects['VIEW_opposite']
scene.render.resolution_x=1400;scene.render.resolution_y=1050;scene.render.resolution_percentage=100
if hasattr(scene,'cycles'):scene.cycles.samples=48
bpy.context.window.scene=scene
(OUT/'preview').mkdir(exist_ok=True)
# Own detail camera; studio and existing review cameras remain unchanged.
cam=src.camera.copy();cam.data=src.camera.data.copy();cam.name='VIEW_tail_v03_detail';scene.collection.objects.link(cam)
p=Vector((.01415,.03903,0));t=Vector((.8936,-.4489,0));n=Vector((.4489,.8936,0))
target=p-t*.018+Vector((0,0,.020))
cam.location=target+t*.13+n*.04+Vector((0,0,.15))
cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.14
scene.render.filepath=str(OUT/'preview/opposite.png')
bpy.data.libraries.write(str(ROOT/'model/blender/dragon-print-kit-v03.blend'),{scene},compress=True)
print(json.dumps({'scene':scene.name,'parts':len([o for o in scene.objects if o.name.startswith('KIT03_')])}))
queue=[('opposite',bpy.data.objects['VIEW_opposite']),('tail_detail',cam),('hero',bpy.data.objects['VIEW_hero']),('top',bpy.data.objects['VIEW_top'])]
completed=[]
def render():
    try:
        name,camera=queue.pop(0);scene.camera=camera
        scene.render.filepath=str(OUT/'preview'/(name+'.png'))
        bpy.ops.render.render(write_still=True,scene=scene.name);completed.append(name)
        if queue:
            (OUT/'work/render-status.json').write_text(json.dumps({'status':'running','completed':completed}))
            return .3
        scene.camera=bpy.data.objects['VIEW_opposite']
        bpy.data.libraries.write(str(ROOT/'model/blender/dragon-print-kit-v03.blend'),{scene},compress=True)
        (OUT/'work/render-status.json').write_text(json.dumps({'status':'complete','completed':completed}))
    except Exception as e:(OUT/'work/render-status.json').write_text(json.dumps({'status':'error','message':str(e)}))
    return None
bpy.app.timers.register(render,first_interval=.3)
