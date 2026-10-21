"""Editable Dragon Playground visual prototype. Run inside Blender via MCP.

Source coordinates are millimetres; the assembly parent converts to metres.
Approved full puffy hoops and toy styling; photographs guide connections only.
No survey scale or print-readiness is implied. Original scenes are preserved.
"""
import bpy
import bmesh
import math
import json
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
SCENE_NAME = 'Dragon • Puffy Hoops 06'
PARAMS = {
    'target_length_mm': 230.0,
    'rib_count': 18,
    'rib_radius_mm': 2.4,
    'rib_half_width_mm': 9.5,
    'rib_height_mm': 26.0,
    'rail_radius_mm': 0.7,
    'rib_profile': 'closed oval hoop',
    'rib_axial_radius_mm': 2.6,
    'rail_count': 4,
    'slide_toe_lift_mm': 2.7,
    'slide_wall_thickness_mm': 2.4,
    'body_path_mm': [(62,2,40),(22,0,36),(-35,0,42),(-80,15,43),
                     (-92,42,40),(-72,64,33),(-28,63,23),(16,42,3.4)],
    'support_fractions': [2/17,5/17,8/17,12/17,15/17],
}

def enum_set(item, name, value):
    values=[i.identifier for i in item.bl_rna.properties[name].enum_items]
    if value not in values:
        raise ValueError(f'{name}: {value} not in {values}')
    setattr(item,name,value)

def mesh_obj(name, vertices, faces, mat, collection, bevel=0):
    mesh=bpy.data.meshes.new(name+' mesh')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    bm=bmesh.new(); bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(mesh); bm.free()
    obj=bpy.data.objects.new(name,mesh); collection.objects.link(obj)
    if mat: mesh.materials.append(mat)
    if bevel:
        mod=obj.modifiers.new('Soft edges','BEVEL'); mod.width=bevel; mod.segments=3
        mod2=obj.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return obj

def prism(name, poly, mapping, depth, mat, collection, bevel=.5):
    n=len(poly)
    verts=[tuple(mapping(u,v,d)) for d in [-depth/2,depth/2] for u,v in poly]
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh_obj(name,verts,faces,mat,collection,bevel)

def tube(name, points, radius, mat, collection, sides=12):
    pts=[Vector(p) for p in points]; verts=[]; previous_a=None
    for i,p in enumerate(pts):
        tangent=(pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]).normalized()
        if previous_a is None:
            ref=Vector((0,0,1)) if abs(tangent.z)<.95 else Vector((0,1,0))
            a=tangent.cross(ref).normalized()
        else:
            a=(previous_a-tangent*previous_a.dot(tangent)).normalized()
        b=tangent.cross(a).normalized(); previous_a=a
        for j in range(sides):
            angle=2*math.pi*j/sides
            verts.append(tuple(p+radius*(a*math.cos(angle)+b*math.sin(angle))))
    faces=[]
    for i in range(len(pts)-1):
        for j in range(sides):
            k=i*sides+j; l=i*sides+(j+1)%sides
            faces.append((k,l,l+sides,k+sides))
    faces += [tuple(range(sides-1,-1,-1)),tuple((len(pts)-1)*sides+j for j in range(sides))]
    obj=mesh_obj(name,verts,faces,mat,collection)
    for face in obj.data.polygons: face.use_smooth=len(face.vertices)==4
    return obj

def spline(points, steps=30):
    p=[Vector(x) for x in points]; out=[]
    for i in range(len(p)-1):
        a=p[max(i-1,0)]; b=p[i]; c=p[i+1]; d=p[min(i+2,len(p)-1)]
        for j in range(steps):
            t=j/steps
            out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    return out+[p[-1]]

def sample_path(path, fraction):
    distances=[0.0]
    for a,b in zip(path,path[1:]): distances.append(distances[-1]+(b-a).length)
    target=max(0,min(1,fraction))*distances[-1]
    i=next((i for i,d in enumerate(distances[1:]) if d>=target),len(path)-2)
    t=(target-distances[i])/max(.00001,distances[i+1]-distances[i])
    p=path[i].lerp(path[i+1],t)
    tangent=path[min(i+2,len(path)-1)]-path[max(0,i-1)]
    tangent.z=0; tangent.normalize()
    lateral=Vector((-tangent.y,tangent.x,0))
    return p,tangent,lateral

def srgb_hex(hexcode):
    c=[int(hexcode[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c)+(1,)

def material(name, color, roughness=.42):
    mat=bpy.data.materials.new('DRAGON '+name); mat.use_nodes=True
    rgba=srgb_hex(color); mat.diffuse_color=rgba
    shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    next(s for s in shader.inputs if s.identifier=='Base Color').default_value=rgba
    next(s for s in shader.inputs if s.identifier=='Roughness').default_value=roughness
    return mat

def build():
    # Preserve previous scenes and free object names for the current revision.
    for prior_name,prefix in [('Dragon • Soft Loops 01','V01 | '),('Dragon • Puffy Hoops 02','V02 | '),('Dragon • Puffy Hoops 03','V03 | '),('Dragon • Puffy Hoops 04','V04 | '),('Dragon • Puffy Hoops 05','V05 | ')]:
        prior=bpy.data.scenes.get(prior_name)
        if prior:
            for obj in prior.objects:
                if obj.get('dragon_owned') and not obj.name.startswith(prefix):
                    obj.name=prefix+obj.name
    old=bpy.data.scenes.get(SCENE_NAME)
    if old:
        for ob in list(old.objects):
            if ob.get('dragon_owned'): bpy.data.objects.remove(ob,do_unlink=True)
        bpy.data.scenes.remove(old)
    scene=bpy.data.scenes.new(SCENE_NAME)
    bpy.context.window.scene=scene
    enum_set(scene.unit_settings,'system','METRIC')
    scene.unit_settings.scale_length=1
    values=[i.identifier for i in scene.unit_settings.bl_rna.properties['length_unit'].enum_items]
    if 'MILLIMETERS' in values: scene.unit_settings.length_unit='MILLIMETERS'
    groups={}
    for name in ['Head','Body','Supports','Slides','Ladder','Tail','Base','Studio']:
        group=bpy.data.collections.new('Dragon | '+name); scene.collection.children.link(group); groups[name]=group
    mats={name:material(name,color) for name,color in {
        'cream':'F4EBDD','orange':'DA6946','blue':'387FA7','sage':'8DAB9B',
        'red':'B95343','sand':'DCCBAA','rail':'4C778C','studio':'ECE5DA'}.items()}
    assembly=bpy.data.objects.new('DRAGON | 230 mm assembly',None); groups['Body'].objects.link(assembly)
    namespace={}; headpath=ROOT/'model/blender_head_v04.py'
    exec(compile(headpath.read_text(),str(headpath),'exec'),namespace)
    namespace['build_head']({'bpy':bpy,'collection':groups['Head'],'materials':mats})
    # Shared wedge floor, narrowing toward the snout. All four branches meet x=62.
    floor=[(61.3,-28),(61.3,28),(96,9.3),(96,-9.3)]
    prism('HEAD_Shared platform',floor,lambda x,y,d:(x,y,38.7+d),2.6,mats['cream'],groups['Head'],.65)
    prism('HEAD_Snout closing wall',[(0,0),(19,0),(19,5),(0,5)],
          lambda u,z,d:(96+d,u-9.5,40+z),2.5,mats['cream'],groups['Head'],.6)
    path=spline(PARAMS['body_path_mm'])
    half=PARAMS['rib_half_width_mm']; height=PARAMS['rib_height_mm']
    colors=['cream','blue','sage','sage','red','red','cream','blue','blue',
            'blue','blue','cream','blue','sage','red','cream','blue','blue']
    # Closed oval hoops, with their bottoms held on the existing support route.
    # Periodic mesh indices join the seam: no overlapping end caps or top gap.
    for i in range(PARAMS['rib_count']):
        fraction=i/(PARAMS['rib_count']-1)
        p,t,n=sample_path(path,fraction)
        vertices=[]; faces=[]; segments=96; sides=20
        up=Vector((0,0,1)); vertical_radius=height/2
        for j in range(segments):
            theta=2*math.pi*j/segments
            centre=p+n*(half*math.cos(theta))+up*(vertical_radius*(1+math.sin(theta)))
            normal=(n*(math.cos(theta)/half)+up*(math.sin(theta)/vertical_radius)).normalized()
            for k in range(sides):
                a=2*math.pi*k/sides
                vertices.append(tuple(centre+normal*(PARAMS['rib_radius_mm']*math.cos(a))
                                      +t*(PARAMS['rib_axial_radius_mm']*math.sin(a))))
        for j in range(segments):
            for k in range(sides):
                faces.append((j*sides+k,j*sides+(k+1)%sides,
                              ((j+1)%segments)*sides+(k+1)%sides,((j+1)%segments)*sides+k))
        ob=mesh_obj(f'BODY_Rib_{i+1:02}',vertices,faces,mats[colors[i]],groups['Body'])
        for face in ob.data.polygons:face.use_smooth=True
        ob['route_fraction']=fraction
        ob['profile']='Full oval hoop; continuous closed seam'
    # Four understated rails, leaving the puffy hoop silhouette prominent.
    for rail_i,degrees in enumerate([35,145,215,325]):
        theta=math.radians(degrees); points=[]
        for j in range(241):
            p,t,n=sample_path(path,j/240)
            points.append(p+n*(half*math.cos(theta))+Vector((0,0,height/2*(1+math.sin(theta)))))
        tube(f'BODY_Rail_{rail_i+1:02}',points,PARAMS['rail_radius_mm'],mats['rail'],groups['Body'])
    # Five provisional supports: broad transverse slabs; coordinates are inferred.
    for i,f in enumerate(PARAMS['support_fractions']):
        p,t,n=sample_path(path,f); top=p.z+.3
        shape=[(-11,0),(11,0),(7,top),( -7,top)]
        mapping=lambda u,z,d,p=p,t=t,n=n: Vector((p.x,p.y,0))+n*u+t*d+Vector((0,0,z))
        prism(f'PIER_{i+1:02}_cream',shape,mapping,4.2,mats['cream'],groups['Supports'],.65)
        patch=[(-8.7,.8),(8.7,.8),(5.6,top-1),(-5.6,top-1)]
        for sign in [-1,1]:
            prism(f'PIER_{i+1:02}_inset_{sign}',patch,
                  lambda u,z,d,mp=mapping,sign=sign:mp(u,z,d+sign*2.13),.22,
                  mats['orange' if i in [0,3] else 'blue'],groups['Supports'],.12)
    # Slide channels: both begin on the raised shared platform.
    slide_paths=[[(62,-23,40),(52,-27,38),(9,-43,4),(-8,-47,1.8)],
                 [(62,21,40),(55,28,38),(24,63,9),(6,88,1.8)]]
    for slide_i,knots in enumerate(slide_paths):
        line=spline(knots,24); verts=[]; width=9
        for point in line: point.z=max(point.z,1.8)
        # A deeper toe, like the reference: lift the lower channel gently while
        # retaining its underside, so the front end gains solid material.
        plan_distances=[0.]
        for a,b in zip(line,line[1:]):
            plan_distances.append(plan_distances[-1]+math.hypot(b.x-a.x,b.y-a.y))
        toe_lifts=[]
        for point,distance in zip(line,plan_distances):
            t=max(0.,min(1.,(distance/plan_distances[-1]-.45)/.55))
            lift=PARAMS['slide_toe_lift_mm']*t*t*(3-2*t)
            point.z+=lift
            toe_lifts.append(lift)
        frames=[]
        for j,p in enumerate(line):
            t=line[min(j+1,len(line)-1)]-line[max(j-1,0)]; t.z=0;t.normalize()
            n=Vector((-t.y,t.x,0)); frames.append((p,t,n))
            verts += [tuple(p+n*y+Vector((0,0,z))) for y,z in [(-width/2,0),(width/2,0),(-width/2,-1.7-toe_lifts[j]),(width/2,-1.7-toe_lifts[j])]]
        faces=[]
        for j in range(len(line)-1):
            a=j*4;b=a+4
            faces += [(a,b,b+1,a+1),(a+2,a+3,b+3,b+2),(a,a+2,b+2,b),(a+1,b+1,b+3,a+3)]
        faces += [(0,1,3,2),tuple((len(line)-1)*4+k for k in [0,2,3,1])]
        deck=mesh_obj(f'SLIDE_{slide_i+1}_channel',verts,faces,mats['cream'],groups['Slides'],.45)
        # Broad ground-bearing cheeks, traced from the user's slide-support crop.
        # Each wall is an explicit profile with a vertical step, not a swept ribbon.
        wall_namespace={}
        wall_source=ROOT/'model/blender_slide_support_v06.py'
        exec(compile(wall_source.read_text(),str(wall_source),'exec'),wall_namespace)
        wall_namespace['build_slide_walls'](slide_i+1,line,mats,groups['Slides'],mesh_obj)
    # Straight direct access ladder on the body side, not the snout side.
    start=Vector((35,-13.8,1.3)); end=Vector((62,-13.8,40))
    for side in [-1,1]:
        offset=Vector((0,side*3.1,0))
        tube(f'LADDER_Stringer_{side}',[start+offset,end+offset],.82,mats['blue'],groups['Ladder'])
        top=end+offset
        rail=[start.lerp(end,.50)+offset+Vector((0,0,7)),top+Vector((0,0,8)),top+Vector((3,0,8)),top+Vector((4,0,0))]
        tube(f'LADDER_Handrail_{side}',spline(rail,12),.65,mats['blue'],groups['Ladder'])
    for j in range(1,10):
        p=start.lerp(end,j/10)
        prism(f'LADDER_Tread_{j:02}',[(-1.8,-2.9),(1.8,-2.9),(1.8,2.9),(-1.8,2.9)],
              lambda x,y,d,p=p:p+Vector((x,y,d)),1.0,mats['cream'],groups['Ladder'],.25)
    # Tail starts at ground level and flows into the returning climbing ribs.
    p,t,n=sample_path(path,1); inward=-t
    for sign in [-1,1]:
        profile=[(-3,0),(18,0),(18,20),(12,23),(6,17),(-3,10)]
        mp=lambda u,z,d,sign=sign:Vector((p.x,p.y,0))+inward*u+n*(sign*11.7+d)+Vector((0,0,z))
        prism(f'TAIL_Wall_{sign}',profile,mp,2.5,mats['cream'],groups['Tail'],.8)
        patch=[(-1,1.3),(16.5,1.3),(16.5,19.1),(12.2,21),(6.2,15.2),(-1,9.4)]
        prism(f'TAIL_Orange_{sign}',patch,lambda u,z,d,mp=mp,sign=sign:mp(u,z,sign*1.28+d),.25,mats['orange'],groups['Tail'],.2)
        prism(f'TAIL_Blue_{sign}',patch,lambda u,z,d,mp=mp,sign=sign:mp(u,z,-sign*1.28+d),.25,mats['blue'],groups['Tail'],.2)
    prism('TAIL_Low threshold',[(-4,-10),(2,-10),(2,10),(-4,10)],
          lambda u,v,d:Vector((p.x,p.y,0))+inward*u+n*v+Vector((0,0,1.8+d)),2.5,mats['cream'],groups['Tail'],.45)
    # Rounded rectangular sandpit keeps the broad plan legible.
    def rounded_rect(x0,x1,y0,y1,r):
        pts=[]
        for cx,cy,start in [(x1-r,y1-r,0),(x0+r,y1-r,90),(x0+r,y0+r,180),(x1-r,y0+r,270)]:
            for j in range(13):
                a=math.radians(start+j*90/12);pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
        return pts
    outline=rounded_rect(-116,126,-61,102,15)
    prism('BASE_Porcelain rim',outline,lambda x,y,d:(x,y,-3.5+d),7,mats['cream'],groups['Base'],1.5)
    sand=rounded_rect(-112,122,-57,98,12)
    prism('BASE_Sand inset',sand,lambda x,y,d:(x,y,-.25+d),.8,mats['sand'],groups['Base'],.12)
    for name,group in groups.items():
        if name=='Studio':continue
        for obj in group.objects:
            if obj!=assembly:obj.parent=assembly
            obj['dragon_owned']=True
    bpy.context.view_layer.update()
    model=[o for name,g in groups.items() if name not in ['Base','Studio'] for o in g.objects if o.type=='MESH' and not o.hide_render]
    deps=bpy.context.evaluated_depsgraph_get()
    points=[o.matrix_world@Vector(v) for o in model for v in o.evaluated_get(deps).bound_box]
    extent=max(p.x for p in points)-min(p.x for p in points)
    factor=PARAMS['target_length_mm']/extent
    assembly.scale=(factor*.001,)*3
    assembly['parameters_json']=json.dumps(PARAMS)
    assembly['status']='Visual prototype; dimensions estimated; print validation pending'
    studio=groups['Studio']
    # Floor in metres, independent of assembly scale.
    mesh_obj('STUDIO_Backdrop',[(-20,-20,-.008),(20,-20,-.008),(20,20,-.008),(-20,20,-.008)],[(0,1,2,3)],mats['studio'],studio)
    def aim(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    for name,loc,power,size in [('Key',(.02,-.20,.34),.38,.28),('Fill',(-.23,-.01,.21),.22,.23),('Rim',(.05,.27,.30),.42,.20)]:
        data=bpy.data.lights.new('STUDIO_'+name,'AREA'); data.energy=power;data.size=size
        obj=bpy.data.objects.new('STUDIO_'+name,data);studio.objects.link(obj);obj.location=loc;aim(obj,(0,.02,.025))
    world=bpy.data.worlds.new('Dragon warm studio');world.use_nodes=True
    bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND')
    bg.inputs[0].default_value=(.78,.82,.88,1);bg.inputs[1].default_value=.15;scene.world=world
    views={
        'hero':((.28,-.52,.23),(.006,.022,.033),.33),
        'opposite':((-.20,.42,.24),(.0,.025,.032),.32),
        'top':((.003,.022,.65),(.003,.022,0),.30),
        'side_a':((.0,-.6,.040),(.0,.021,.04),.31),
        'side_b':((.0,.6,.040),(.0,.021,.04),.31),
        'head_end':((.65,.025,.11),(.0,.025,.04),.25),
        'return_end':((-.65,.025,.14),(.0,.025,.04),.25),
        'junction':((.12,-.24,.24),(.065,.001,.033),.15),
        'slide_detail':((-.04,-.40,.14),(.025,-.035,.023),.14),
    }
    for name,(loc,target,scale) in views.items():
        data=bpy.data.cameras.new('VIEW_'+name);enum_set(data,'type','ORTHO');data.ortho_scale=scale;data.clip_start=.001;data.clip_end=100
        obj=bpy.data.objects.new('VIEW_'+name,data);studio.objects.link(obj);obj.location=loc;aim(obj,target)
    scene.camera=bpy.data.objects['VIEW_hero']
    scene.render.resolution_x=1400;scene.render.resolution_y=1050;scene.render.resolution_percentage=100
    enum_set(scene.render.image_settings,'file_format','PNG')
    scene.render.film_transparent=False
    scene.view_settings.exposure=2.15
    try:scene.render.engine='CYCLES'
    except TypeError:pass
    if scene.render.engine=='CYCLES':
        scene.cycles.samples=40;scene.cycles.use_denoising=True
    for obj in studio.objects:obj['dragon_owned']=True
    # Saved viewport matches the primary review angle.
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active
                space.clip_start=.001;space.clip_end=100
                space.region_3d.view_location=(.0,.023,.035)
                space.region_3d.view_distance=.31
                space.region_3d.view_rotation=scene.camera.rotation_euler.to_quaternion()
                space.overlay.show_overlays=False
                shade=space.shading
                vals=[i.identifier for i in shade.bl_rna.properties['color_type'].enum_items]
                if 'MATERIAL' in vals:shade.color_type='MATERIAL'
    bpy.context.view_layer.update()
    # Named editable source text is embedded for portable review.
    for source in [ROOT/'model/blender_dragon_v06.py',headpath,ROOT/'model/blender_slide_support_v06.py']:
        txt=bpy.data.texts.get(source.name) or bpy.data.texts.new(source.name)
        txt.clear();txt.write(source.read_text())
    (ROOT/'model/blender').mkdir(parents=True,exist_ok=True)
    (ROOT/'renders/blender-v06').mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'model/blender/dragon-puffy-hoops-v06.blend'))
    metrics={'target_length_mm':230,'scale_factor':factor,'rib_count':PARAMS['rib_count'],
             'support_count':len(PARAMS['support_fractions']),'slide_count':2,
             'object_count':len(scene.objects),'parameters':PARAMS,'blender_version':bpy.app.version_string,
             'slide_support':'Ground-bearing lower 65 percent with stepped upper cutout; deeper 8 mm toe and 2.4 mm cheeks',
             'print_status':'Not assessed; editable visual prototype'}
    (ROOT/'model/blender/build-v06.json').write_text(json.dumps(metrics,indent=2))
    print(json.dumps(metrics))
    return scene

if __name__=='__main__':
    build()
