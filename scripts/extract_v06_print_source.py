import bpy,numpy as np,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
scene=bpy.data.scenes['Dragon • Puffy Hoops 06']
assert bpy.context.scene==scene
out=ROOT/'exports/dragon-pla-kit/work/source-v06';out.mkdir(parents=True,exist_ok=True)
deps=bpy.context.evaluated_depsgraph_get();inventory=[]
for obj in scene.objects:
    if obj.type!='MESH' or obj.hide_render or obj.name.startswith('STUDIO'):continue
    ev=obj.evaluated_get(deps);mesh=ev.to_mesh();mesh.calc_loop_triangles()
    vertices=np.asarray([tuple(obj.matrix_world@v.co) for v in mesh.vertices],dtype=np.float64)*1000
    faces=np.asarray([t.vertices[:] for t in mesh.loop_triangles],dtype=np.uint32)
    np.savez_compressed(out/(obj.name+'.npz'),vertices=vertices,faces=faces)
    inventory.append({'name':obj.name,'file':obj.name+'.npz','material':obj.data.materials[0].name if obj.data.materials else None,'vertices':len(vertices),'triangles':len(faces)})
    ev.to_mesh_clear()
(out/'inventory.json').write_text(json.dumps(inventory,indent=2))
print('Read-only source extraction:',len(inventory),'evaluated meshes, final millimetres.')
