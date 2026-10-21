"""Verify tail/ladder v03 fit and assembly access; never exports production files.

Default checks source solids and actual float32 STL round trips in memory.
--assembly-dir accepts restored production STL NPZ meshes for the final audit.
--json writes an optional machine-readable review (otherwise stdout only).
"""
from pathlib import Path
import sys,json,math,argparse,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import trimesh
from shapely.geometry import LineString
from shapely.ops import polygonize,unary_union
from model.printkit.common import from_mesh,to_trimesh,union,box,sample_route
from model.printkit.entrance import build
from scripts.build_print_kit import print_mesh

UP=np.array([0.,0.,1.])

def horizontal_section(mesh,z):
    lines=trimesh.intersections.mesh_plane(mesh,UP,[0,0,z])
    if not len(lines):return None
    # Polygons are individually nested. Symmetric difference retains holes.
    loops=list(polygonize(unary_union([LineString(np.round(x[:,:2],7)) for x in lines])))
    if not loops:return None
    # Classify each planar face against the original segment set. This
    # retains holes instead of filling them via a union of all polygon faces.
    segments=np.asarray(lines)[:,:,:2];filled=[]
    for poly in loops:
        q=poly.representative_point();x,y=q.x,q.y
        crossings=0
        for a,b in segments:
            if (a[1]>y)!=(b[1]>y):
                at=a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1])
                if at>x:crossings+=1
        if crossings%2:filled.append(poly)
    return unary_union(filled)

def print_screen(mesh,layer=.16):
    maxz=mesh.bounds[1,2];zs=list(np.arange(.08,maxz,layer))
    if not zs:zs=[maxz/2]
    rows=[];prev=None;last=None
    for z in zs:
        section=horizontal_section(mesh,z)
        if section is None:continue
        if prev is not None:
            grown=section.difference(prev.buffer(z-last+.005))
            islands=[]
            for poly in getattr(section,'geoms',[section]):
                if not poly.intersects(prev.buffer(.005)) and poly.area>.02:islands.append(poly.area)
            if grown.area>.01 or islands:rows.append({'z_mm':z,'growth_beyond_45_deg_mm2':grown.area,'new_island_areas_mm2':islands})
        prev=section;last=z
    return {'layers':len(zs),'flagged_layers':rows}

def run(assembly_dir=None,manifest_path=None):
    parts,info=build();solids={p.name:p.solid for p in parts};report={'geometry_source':'source + in-memory delivered-format STL checks','parts':{},'checks':{},'failures':[]}
    if assembly_dir:
        loaded=set()
        for file in Path(assembly_dir).glob('*.npz'):
            z=np.load(file);solids[file.stem]=from_mesh(z['vertices'],z['faces']);loaded.add(file.stem)
        required={p.name for p in parts}|{'body_hoop_18','head_platform_snout'}
        required|={f'head_{side}_{suffix}' for side in ['A','B'] for suffix in ['cream_inner','cream_outer','orange','blue']}
        if required-loaded:raise ValueError('Missing actual STL meshes: '+', '.join(sorted(required-loaded)))
        report['geometry_source']=str(Path(assembly_dir).resolve())
        manifest_path=Path(manifest_path) if manifest_path else Path(assembly_dir).parent.parent/'manifest.json'
        manifest=json.loads(manifest_path.read_text())
        records={r['name']:r for r in manifest['parts']}
        report['manifest']=str(manifest_path.resolve())
    else:
        from model.printkit.body import build as body_build
        from model.printkit.head import build as head_build
        for p in body_build()[0]+head_build()[0]:solids[p.name]=p.solid
    for part in parts:
        part.solid=solids[part.name]
        if assembly_dir:
            record=records[part.name];stl=manifest_path.parent/record['file']
            mesh=trimesh.load(stl,force='mesh',process=True)
            with np.load(Path(assembly_dir)/(part.name+'.npz')) as data:
                recovered=data['vertices']@np.asarray(record['print_rotation_world_to_bed']).T-np.asarray(record['print_minimum_before_translation_mm'])
                if recovered.shape!=mesh.vertices.shape or not np.array_equal(data['faces'],mesh.faces):
                    raise ValueError(part.name+': delivered STL and restored NPZ topology differ')
            error=float(np.max(np.abs(recovered-mesh.vertices)))
            if error>1e-5:raise ValueError(part.name+': delivered STL and restored NPZ vertices differ')
        else:mesh=print_mesh(part)
        item={'watertight':bool(mesh.is_watertight),'components':len(part.solid.decompose()),'volume_mm3':mesh.volume,'print_height_mm':mesh.extents[2]}
        if assembly_dir:item.update(stl=str(stl),sha256=hashlib.sha256(stl.read_bytes()).hexdigest(),restored_stl_vertex_error_mm=error)
        if not mesh.is_watertight or len(part.solid.decompose())!=1 or mesh.volume<=0:
            report['failures'].append(part.name+' invalid delivered mesh')
        if part.supports=='none':
            item['layer_screen']=print_screen(mesh)
            if item['layer_screen']['flagged_layers']:report['failures'].append(part.name+' print-layer screen flagged')
        report['parts'][part.name]=item
    def check(name,value,ok):
        report['checks'][name]=value
        if not ok:report['failures'].append(name)
    p,t,n0=sample_route(1);u=sample_route(15/17)[0]-p;u[2]=0;u/=np.linalg.norm(u);n=np.cross(u,UP);origin=np.r_[p[:2],0.]
    rung=solids['body_hoop_18'];threshold=solids['tail_threshold_landing']
    above=box((0,0,100.355),(1000,1000,199.29))
    shifts=[]
    for label,axis in [('u',u),('n',n),('diag',(u+n)/np.sqrt(2))]:
        for delta in [-.20,.20]:
            volume=(rung.translate(axis*delta)^threshold^above).volume()
            shifts.append({'axis':label,'shift_mm':delta,'collision_above_landing_mm3':volume})
    check('rung18_0p20_horizontal_allowance',shifts,max(x['collision_above_landing_mm3'] for x in shifts)<.001)
    A=horizontal_section(to_trimesh(threshold),.6999);B=horizontal_section(to_trimesh(rung),.7001)
    area=A.intersection(B).area
    check('rung18_bearing_area_mm2',area,area>31.5)
    def local_clip(s,sign,lo,hi):
        normal=n*sign;d=float(np.dot(normal,origin))
        return s.trim_by_plane(normal,d+lo).trim_by_plane(-normal,-d-hi)
    for side,sign in [('A',1),('B',-1)]:
        cream=union(solids[f'tail_{side}_cream_outer'],solids[f'tail_{side}_cream_inner'])
        rail=solids[f'tail_{side}_cream_handrail'];blue=solids[f'tail_{side}_blue']
        structural_gap=local_clip(rail,sign,14.05,15.35).min_gap(cream,2)
        blue_gap=local_clip(rail,sign,13.61,13.88).min_gap(blue,2)
        stop_volume=(rail.translate(n*sign*.01)^cream).volume()
        check(f'{side}_pin_radial_gap_mm',structural_gap,structural_gap>.145)
        check(f'{side}_shoulder_blue_clearance_mm',blue_gap,blue_gap>.59)
        check(f'{side}_positive_shoulder_stop_probe_mm3',stop_volume,stop_volume>.005)
        blind_gap=local_clip(rail,sign,15.39,15.41).min_gap(local_clip(cream,sign,15.59999,16.3),1)
        check(f'{side}_pin_blind_end_reserve_mm',blind_gap,blind_gap>.199)
        # Isolate the second post and exercise its deliberate pitch freedom.
        rear=local_clip(rail,sign,14.05,15.35).trim_by_plane(u,float(np.dot(u,origin)+20))
        pitch=(u*30+UP*10.5)/np.hypot(30,10.5)
        slotted=[rear.translate(pitch*d).min_gap(cream,1) for d in [-.30,.30]]
        check(f'{side}_second_post_pitch_freedom_gaps_mm',slotted,min(slotted)>.145)
        for color in ['orange','blue']:
            insert=solids[f'tail_{side}_{color}']
            # The seats should stop a 0.01 mm press toward the pocket floor.
            normal=n*(sign if color=='orange' else -sign)
            interference=(insert.translate(-normal*.01)^cream).volume()
            check(f'{side}_{color}_seating_land_stop_probe_mm3',interference,interference>.05)
    frame=solids['ladder_blue_frame'];comb=solids['ladder_cream_tread_comb']
    motion=[]
    for x in np.linspace(0,12,241):
        shifted=comb.translate([float(x),0,0])
        motion.append({'x_offset_mm':float(x),'gap_mm':shifted.min_gap(frame,1),'intersection_mm3':(shifted^frame).volume()})
    gap=min(x['gap_mm'] for x in motion)
    check('ladder_straight_approach',{'samples':len(motion),'sample_step_mm':.05,'distance_mm':12,'minimum_sampled_gap_mm':gap,'continuous_clearance_lower_bound_mm':gap-.025-.005,'lower_bound_basis':'Distance is 1-Lipschitz under translation; subtract half sample spacing and 0.005 mm numerical allowance.','max_intersection_mm3':max(x['intersection_mm3'] for x in motion)},gap-.025-.005>=.20 and max(x['intersection_mm3'] for x in motion)<.001)
    heads=union(*(v for k,v in solids.items() if k.startswith('head_')))
    gap=frame.min_gap(heads,3)
    check('ladder_frame_head_gap_mm',gap,gap>=.199)
    check('two_tail_base_locators',{'tight':len(info['base_socket_cutters']),'sand':len(info['sand_clearance_cutters'])},len(info['base_socket_cutters'])==2 and len(info['sand_clearance_cutters'])==2)
    # Explicit metadata complements actual measured gaps; it is not substituted
    # for the interference or motion checks above.
    report['nominal_interfaces']=info['metadata']
    report['status']='PASS' if not report['failures'] else 'FAIL'
    return report

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--assembly-dir');a.add_argument('--manifest',help='Defaults to the kit manifest above work/assembly');a.add_argument('--json');args=a.parse_args()
    if args.manifest and not args.assembly_dir:a.error('--manifest requires --assembly-dir')
    r=run(args.assembly_dir,args.manifest)
    if args.json:Path(args.json).write_text(json.dumps(r,indent=2))
    print(json.dumps(r,indent=2))
    sys.exit(0 if not r['failures'] else 1)
