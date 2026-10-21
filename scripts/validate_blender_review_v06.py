"""Targeted visual-prototype checks; not a slicer or print validation."""
import bpy
import bmesh
import json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
scene=bpy.data.scenes['Dragon • Puffy Hoops 06']
bpy.context.window.scene=scene
bpy.context.view_layer.update()
deps=bpy.context.evaluated_depsgraph_get()
objects=[o for o in scene.objects if o.type=='MESH' and not o.hide_render and not o.name.startswith('STUDIO')]
def bounds(items):
    points=[o.matrix_world@Vector(v) for o in items for v in o.evaluated_get(deps).bound_box]
    low=[min(v[a] for v in points)*1000 for a in range(3)]
    high=[max(v[a] for v in points)*1000 for a in range(3)]
    return {'min_mm':low,'max_mm':high,'dimensions_mm':[b-a for a,b in zip(low,high)]}
topology=[]
for obj in objects:
    mesh=obj.evaluated_get(deps).to_mesh()
    bm=bmesh.new();bm.from_mesh(mesh)
    bad=sum(not edge.is_manifold for edge in bm.edges)
    if bad:topology.append({'object':obj.name,'non_manifold_edges':bad})
    bm.free();obj.evaluated_get(deps).to_mesh_clear()
namespace={}
exec(compile((ROOT/'model/blender_head_v04.py').read_text(),'blender_head_v04.py','exec'),namespace)
cx,cz=namespace['EYE_CENTRE']
eye_checks=[]
for label,side in [('A',1),('B',-1)]:
    origin=Vector(namespace['_world'](cx,cz,10,side))
    dest=Vector(namespace['_world'](cx,cz,-10,side))
    for part in ['CreamPanel','OrangeExterior','BlueInterior']:
        obj=bpy.data.objects[f'HEAD_{label}_{part}']
        hit=obj.evaluated_get(deps).ray_cast(origin,(dest-origin).normalized(),distance=20)[0]
        eye_checks.append({'object':obj.name,'centre_ray_clear':not hit})
def bvh(obj):
    ev=obj.evaluated_get(deps);mesh=ev.to_mesh();mesh.calc_loop_triangles()
    tree=BVHTree.FromPolygons([obj.matrix_world@v.co for v in mesh.vertices],[t.vertices[:] for t in mesh.loop_triangles],all_triangles=True)
    ev.to_mesh_clear();return tree
support_checks=[]
for i,rib_number in enumerate([3,6,9,13,16],1):
    support=bpy.data.objects[f'PIER_{i:02}_cream'];rib=bpy.data.objects[f'BODY_Rib_{rib_number:02}']
    count=len(bvh(support).overlap(bvh(rib)))
    support_checks.append({'support':support.name,'rib':rib.name,'intersecting_triangle_pairs':count,'connected':count>0})
report={
 'blender_version':bpy.app.version_string,
 'playground':bounds([o for o in objects if not o.name.startswith('BASE')]),
 'including_base':bounds(objects),
 'evaluated_visible_mesh_count':len(objects),
 'rib_count':sum(o.name.startswith('BODY_Rib') for o in objects),
 'rail_count':sum(o.name.startswith('BODY_Rail') for o in objects),
 'slide_channels':sum(o.name.startswith('SLIDE_') and o.name.endswith('_channel') for o in objects),
 'non_manifold_object_results':topology,
 'eye_openings':eye_checks,'support_connections':support_checks,
 'limitations':['Individual mesh-edge checks do not prove assembly printability.','Intended overlaps are not boolean-unioned into print parts.','Head-panel snout overlap and separate decorative inserts remain prototype geometry.','Self-intersections, minimum thickness, clearance coupons, slicer setup and physical fit are not comprehensively validated.','Support count, dimensions and exact layout are estimated; no measured reconstruction claim.']}
assert abs(report['playground']['dimensions_mm'][0]-230)<.01
assert all(r['centre_ray_clear'] for r in eye_checks)
assert all(r['connected'] for r in support_checks)
assert report['rib_count']==18
assert report['rail_count']==4
assert not topology
# A closed hoop is a connected genus-one surface, unlike the former capped U tube.
hoop_topology=[]
for obj in objects:
    if not obj.name.startswith('BODY_Rib'):continue
    m=obj.data
    chi=len(m.vertices)-len(m.edges)+len(m.polygons)
    assert chi==0, (obj.name,chi)
    hoop_topology.append({'object':obj.name,'euler_characteristic':chi,'closed_hoop':True})
report['hoop_topology']=hoop_topology
# The old physical mouth notch must now be backed by solid cream material.
mouth_checks=[]
for label,side in [('A',1),('B',-1)]:
    obj=bpy.data.objects[f'HEAD_{label}_CreamPanel']
    for x,z in [(98,40),(104,38),(103,30),(68,39)]:
        origin=Vector(namespace['_world'](x,z,10,side))
        dest=Vector(namespace['_world'](x,z,-10,side))
        hit=obj.evaluated_get(deps).ray_cast(origin,(dest-origin).normalized(),distance=20)[0]
        mouth_checks.append({'object':obj.name,'point_xz':[x,z],'solid_backing':bool(hit)})
assert all(r['solid_backing'] for r in mouth_checks)
report['mouth_and_cheek_backing']=mouth_checks

# Sample the generated slide walls: broad ground contact, upper opening,
# and actual channel overlap. These are geometry checks, not profile assertions.
from bisect import bisect_right
source=ROOT/'model/blender_dragon_v06.py'
main_ns={'__name__':'validation_geometry','__file__':str(source)}
exec(compile(source.read_text(),str(source),'exec'),main_ns)
slide_knots=[[(62,-23,40),(52,-27,38),(9,-43,4),(-8,-47,1.8)],
             [(62,21,40),(55,28,38),(24,63,9),(6,88,1.8)]]
slide_checks=[]
for number,knots in enumerate(slide_knots,1):
    line=main_ns['spline'](knots,24)
    distances=[0.]
    for a,b in zip(line,line[1:]):
        q=b-a;q.z=0;distances.append(distances[-1]+q.length)
    def station(fraction):
        s=fraction*distances[-1]
        i=min(len(line)-2,max(0,bisect_right(distances,s)-1))
        point=line[i].lerp(line[i+1],(s-distances[i])/(distances[i+1]-distances[i]))
        tangent=line[i+1]-line[i];tangent.z=0;tangent.normalize()
        return point,Vector((-tangent.y,tangent.x,0))
    deck=bpy.data.objects[f'SLIDE_{number}_channel']
    for sign in [-1,1]:
        wall=bpy.data.objects[f'SLIDE_{number}_wall_{sign}']
        ev=wall.evaluated_get(deps)
        def hit(fraction,height):
            p,n=station(fraction);p.z=height
            return bool(ev.ray_cast(p,n*sign,distance=9)[0])
        ground=[hit(f,1) for f in [.45,.65,.85,.95]]
        upper_open=not hit(.12,5)
        upper_solid=hit(.12,32)
        connection=len(bvh(wall).overlap(bvh(deck)))>0
        item={'object':wall.name,'grounded_lower_run_samples':ground,
              'upper_cutout_open':upper_open,'upper_connection_solid':upper_solid,
              'channel_intersects_wall':connection}
        slide_checks.append(item)
        assert all(ground) and upper_open and upper_solid and connection,item
report['slide_support_geometry']=slide_checks

destination=ROOT/'model/blender/validation-v06.json'
destination.write_text(json.dumps(report,indent=2))
print(json.dumps(report))
