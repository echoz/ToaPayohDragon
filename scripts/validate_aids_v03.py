"""Independent checks of lamination cradles and actual base-interface samples.

This reads production modules without changing them. All printing checks use
float32 STL round trips; placements retain the assembly-aid metadata transform.
"""
from pathlib import Path
import sys,json,argparse,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import trimesh
from model.printkit.common import Part,from_mesh,to_trimesh,union,box
from scripts.build_print_kit import make_parts,print_mesh
from scripts.validate_entrance_v03 import print_screen
from model.printkit import assembly_aids,base_samples


def restore_roundtrip(part):
    mesh=print_mesh(part)
    R=np.eye(3) if part.orientation is None else np.asarray(part.orientation)
    tolerance=mesh.metadata.get('simplification_tolerance_mm',0)
    src=to_trimesh(part.solid.simplify(tolerance) if tolerance else part.solid)
    lo=(src.vertices@R.T).min(0)
    assembly=(mesh.vertices+lo)@R
    return from_mesh(assembly,mesh.faces),mesh


BASE_SAMPLE_NAMES=['test_head_A_tray','test_head_A_sand','test_base_join_left',
    'test_base_join_right','test_base_join_key','test_sand_register_tray',
    'test_sand_register_insert','test_slide_2_shell','test_slide_2_insert']


def load_actual(assembly_dir,manifest_path,jigs_only):
    """Use only delivered geometry and its saved placement/print transforms."""
    assembly_dir=Path(assembly_dir);manifest_path=Path(manifest_path)
    manifest=json.loads(manifest_path.read_text())
    records={r['name']:r for r in manifest['parts']}
    interface=manifest['interfaces']['assembly_aids']
    interface=interface.get('metadata',interface)
    jrecords=interface['jigs']
    required={r['name'] for r in jrecords}
    required.update(name for r in jrecords for name in r['parts'])
    if not jigs_only:
        required.update(BASE_SAMPLE_NAMES)
        required.update(records[name]['tags']['production_part'] for name in BASE_SAMPLE_NAMES)
        required.update(['head_A_cream_inner','head_A_cream_outer'])
    by={};meshes={};provenance={}
    for name in sorted(required):
        record=records[name]
        path=assembly_dir/(name+'.npz');stl=manifest_path.parent/record['file']
        with np.load(path) as data:
            vertices=np.asarray(data['vertices']);faces=np.asarray(data['faces'])
        mesh=trimesh.load(stl,force='mesh',process=True)
        rotation=np.asarray(record['print_rotation_world_to_bed'])
        origin=np.asarray(record['print_minimum_before_translation_mm'])
        recovered=vertices@rotation.T-origin
        if recovered.shape!=mesh.vertices.shape or len(faces)!=len(mesh.faces):
            raise ValueError(name+': restored NPZ does not match delivered STL topology')
        if not np.array_equal(faces,mesh.faces):
            raise ValueError(name+': restored NPZ does not preserve delivered STL face indexing')
        error=float(np.max(np.abs(recovered-mesh.vertices)))
        if error>1e-5:raise ValueError(name+': restored NPZ/STL vertex error '+str(error))
        solid=from_mesh(vertices,faces)
        by[name]=Part(name,record['color'],solid,rotation,record.get('notes',''),record['supports'],record.get('tags',{}))
        meshes[name]=mesh
        provenance[name]={'stl':str(stl),'sha256':hashlib.sha256(stl.read_bytes()).hexdigest(),
                          'assembly_npz':str(path),'restored_stl_vertex_error_mm':error}
    return by,[by[r['name']] for r in jrecords],{'metadata':interface},meshes,provenance,manifest


def fixture_pads(sample,original,actual):
    """Isolate added pads without mistaking STL cleanup films for fixtures."""
    added=sample.solid-original
    if not actual:return added,0.
    # The only permitted source addition is four 1.5 x 1.5 x 0.2 mm pads,
    # centred one millimetre in from the exact crop's four XY corners.
    bb=np.asarray(sample.solid.bounding_box());x0,y0=bb[:2];x1,y1=bb[3:5]
    windows=union(*(box((x,y,-1.9),(1.502,1.502,.202)) for x,y in
        [(x0+1,y0+1),(x1-1,y0+1),(x0+1,y1-1),(x1-1,y1-1)]))
    return added^windows,float((added-windows).volume())


def run(jigs_only=False,assembly_dir=None,manifest_path=None):
    actual=assembly_dir is not None
    if actual:
        by,aids,info,meshes,provenance,manifest=load_actual(assembly_dir,manifest_path,jigs_only)
        production=list(by.values())
    else:
        production,_,_=make_parts();by={p.name:p for p in production}
        aids,info=assembly_aids.build(production)
    def printable(part):
        return (part.solid,meshes[part.name]) if actual else restore_roundtrip(part)
    result={'jigs':{},'base_samples':{},'failures':[],
            'geometry_mode':'delivered STL triangles in saved assembly poses' if actual else 'source geometry with float32 print round trips',
            'limits':['No physical glue or clamp test.','A cradle with 0.15 mm side allowance can permit up to about 0.30 mm relative lateral movement between loose halves.','Angular and insertion probes are sampled geometric screens, not a physical clamp or assembly test.']}
    if actual:result.update(manifest=str(manifest_path),assembly_dir=str(assembly_dir),provenance=provenance)
    for aid,record in zip(aids,info['metadata']['jigs']):
        jig,mesh=printable(aid)
        R=np.asarray(record['placement_rotation_world_to_jig']);T=np.asarray(record['placement_translation_jig'])
        placed={name:by[name].solid.transform(np.column_stack((R,T))) for name in record['parts']}
        pair=union(*placed.values())
        whole_bounds=np.asarray(pair.bounding_box())
        row={'float32_watertight':bool(mesh.is_watertight),'float32_connected_components':len(jig.decompose()),
             'print_dimensions_mm':mesh.extents.tolist(),'placement':record,
             'whole_pair_bench_clearance_mm':float(whole_bounds[2]),
             'at_final_pose_intersection_mm3':float((jig^pair).volume()),
             'per_half':{},'side_fit':{},'layer_screen':print_screen(mesh)}
        if whole_bounds[2]<-.001:result['failures'].append(aid.name+' whole pair extends below bench')
        if abs((jig^pair).volume())>.001:result['failures'].append(aid.name+' target pose collides')
        for name,solid in placed.items():
            shifts=[0,.05,.10,.25,.5,1,2,5,10,20]
            movement=[{'z_lift_mm':v,'intersection_mm3':float((solid.translate((0,0,v))^jig).volume())} for v in shifts]
            # Check physical floor bearing by pressing the lower face by 0.01;
            # upper halves instead bear on their mating lamination.
            floor_probe=float((solid.translate((0,0,-.01))^jig).volume())
            row['per_half'][name]={'world_in_jig_bounds_mm':list(solid.bounding_box()),'floor_press_0p01_collision_mm3':floor_probe,
                                   'drop_and_lift_max_collision_mm3':max(x['intersection_mm3'] for x in movement),'movement':movement}
            if max(x['intersection_mm3'] for x in movement)>.001:result['failures'].append(aid.name+' obstructed vertical access for '+name)
        # Quantify how much each loose half can rotate in the complete
        # silhouette guides before its outline meets a side wall.
        pivot=np.array([(jig.bounding_box()[0]+jig.bounding_box()[3])/2,2.,0.])
        for name,solid in placed.items():
            moves={}
            for axis,label in [(np.array([1.,0,0]),'x'),(np.array([0.,1,0]),'y')]:
                moves[label]=[{'translation_mm':d,'collision_mm3':float((solid.translate(axis*d)^jig).volume())} for d in [-.155,.155]]
            rotations=[]
            for degrees in [-1,-.75,-.5,-.25,-.20,-.15,-.10,-.075,-.05,-.025,.025,.05,.075,.10,.15,.20,.25,.5,.75,1]:
                angle=np.deg2rad(degrees);co,si=np.cos(angle),np.sin(angle)
                Rz=np.array([[co,-si,0],[si,co,0],[0,0,1]])
                moved=solid.transform(np.column_stack((Rz,pivot-Rz@pivot)))
                vertices=to_trimesh(solid).vertices
                max_move=float(np.max(np.linalg.norm((vertices@Rz.T+pivot-Rz@pivot)-vertices,axis=1)))
                rotations.append({'degrees':degrees,'collision_mm3':float((moved^jig).volume()),'maximum_outline_motion_mm':max_move})
            row['per_half'][name]['independent_side_probes']=moves
            row['per_half'][name]['independent_rotation_probes']=rotations
            free=[p['maximum_outline_motion_mm'] for p in rotations if p['collision_mm3']<=.001]
            row['per_half'][name]['maximum_tested_free_outline_motion_mm']=max(free,default=0.)
            if max(free,default=0.)>.25:result['failures'].append(aid.name+' excessive sampled angular play for '+name)
        a,b=placed.values()
        row['lamination_nominal_overlap_mm3']=float((a^b).volume())
        row['lamination_gap_mm']=float(a.min_gap(b,2))
        # Assess registration within the captured band, not only the entire
        # pair: jig floor intentionally touches and masks a global min gap.
        above_floor=box((0,0,101.3),(2000,2000,200)) # lower z 1.3
        sidewalls=jig^above_floor
        for axis,label in [(np.array([1.,0,0]),'x'),(np.array([0.,1,0]),'y')]:
            probes=[]
            for sign in [-1,1]:
                first=None
                for shift in [.05,.10,.145,.155,.20,.30,.5,1,2,4,8,16]:
                    vol=float((pair.translate(axis*(sign*shift))^sidewalls).volume())
                    if vol>.001:first={'translation_mm':sign*shift,'intersection_mm3':vol};break
                probes.append(first)
            row['side_fit'][label]=probes
        if row['layer_screen']['flagged_layers']:result['failures'].append(aid.name+' print-layer screen flagged')
        if not mesh.is_watertight or len(jig.decompose())!=1:result['failures'].append(aid.name+' invalid delivered mesh')
        result['jigs'][aid.name]=row
    if not jigs_only:
        try:
            if actual:
                samples=[by[name] for name in BASE_SAMPLE_NAMES]
                sinfo={'metadata':manifest['interfaces']['base_samples']}
            else:samples,sinfo=base_samples.build(production)
        except Exception as exc:
            result['failures'].append('base_samples build failed: '+repr(exc))
        else:
            sb={p.name:p for p in samples};tested={};pads={}
            for sample in samples:
                solid,mesh=printable(sample);tested[sample.name]=solid
                original=by[sample.tags['production_part']].solid
                added=solid-original
                row={'float32_watertight':bool(mesh.is_watertight),'float32_components':len(solid.decompose()),
                     'print_dimensions_mm':mesh.extents.tolist(),'roundtrip_positive_difference_vs_production_mm3':float(added.volume()),
                     'layer_screen':print_screen(mesh) if sample.supports=='none' else {'skipped':'Production part requires supports','flagged_layers':[]}, 'notes':sample.notes}
                if 'Four 1.5 mm bearing pads' in sample.tags.get('fixture_context',''):
                    exact_added,outside=fixture_pads(sample,original,actual);pads[sample.name]=exact_added
                    row['exact_fixture_added_mm3']=float(exact_added.volume())
                    row['positive_difference_outside_fixture_windows_mm3']=outside
                    row['fixture_added_bounds_mm']=list(exact_added.bounding_box())
                    row['fixture_floor_z_mm']=float(exact_added.bounding_box()[2])
                    row['fixture_high_z_mm']=float(exact_added.bounding_box()[5])
                    if exact_added.bounding_box()[2]<-2.0001 or exact_added.bounding_box()[5]>-1.7999:
                        result['failures'].append(sample.name+' fixture changes intended sand datum')
                    if abs(exact_added.volume()-1.8)>.01 or outside>.01:
                        result['failures'].append(sample.name+' fixture differs from four prescribed bearing pads')
                    if sample.name=='test_head_A_sand':
                        head=union(by['head_A_cream_inner'].solid,by['head_A_cream_outer'].solid)
                        row['added_pads_to_actual_head_gap_mm']=float(exact_added.min_gap(head,20))
                        row['added_pads_head_intersection_mm3']=float((exact_added^head).volume())
                        if row['added_pads_head_intersection_mm3']>.001:result['failures'].append(sample.name+' pads obstruct actual head feet')
                result['base_samples'][sample.name]=row
                if row['layer_screen']['flagged_layers']:result['failures'].append(sample.name+' print-layer screen flagged')
                if not mesh.is_watertight or len(solid.decompose())!=1:result['failures'].append(sample.name+' invalid delivered mesh')
            for tray,insert in [('test_head_A_tray','test_head_A_sand'),('test_sand_register_tray','test_sand_register_insert')]:
                a,b=tested[tray],tested[insert]
                intersection=float((a^b).volume())
                result['base_samples'][insert]['paired_tray_overlap_mm3']=intersection
                result['base_samples'][insert]['paired_tray_min_gap_mm']=float(a.min_gap(b,2))
                row=result['base_samples'][insert]
                row['seating_press_0p01_collision_mm3']=float((b.translate((0,0,-.01))^a).volume())
                row['drop_access_max_collision_mm3']=max(float((b.translate((0,0,z))^a).volume()) for z in np.linspace(0,3,31))
                exact_added=pads[insert]
                raised_boss=a.trim_by_plane((0,0,1),-1.7999)
                row['added_pads_to_raised_socket_boss_gap_mm']=float(exact_added.min_gap(raised_boss,20)) if not raised_boss.is_empty() else None
                if intersection>.001:result['failures'].append(insert+' fixture pads collide with paired tray')
                if row['drop_access_max_collision_mm3']>.001:result['failures'].append(insert+' blocked vertical sample insertion')
                if row['seating_press_0p01_collision_mm3']<.01:result['failures'].append(insert+' fixture lacks positive floor seating')
            joined=union(tested['test_base_join_left'],tested['test_base_join_right'])
            key=tested['test_base_join_key']
            result['base_join_test']={'seam_gap_mm':float(tested['test_base_join_left'].min_gap(tested['test_base_join_right'],2)),
                'key_gap_mm':float(key.min_gap(joined,2)),
                'key_drop_max_collision_mm3':max(float((key.translate((0,0,z))^joined).volume()) for z in np.linspace(0,8,81))}
            if result['base_join_test']['key_drop_max_collision_mm3']>.001:result['failures'].append('Base join key blocked during vertical drop')
            result['sample_metadata']=sinfo['metadata']
    result['status']='PASS' if not result['failures'] else 'FAIL'
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--jigs-only',action='store_true');ap.add_argument('--json')
    ap.add_argument('--assembly-dir',type=Path,help='Restored actual-STL NPZ directory; requires --manifest')
    ap.add_argument('--manifest',type=Path,help='Delivered kit manifest including interface and print transforms')
    args=ap.parse_args()
    if bool(args.assembly_dir)!=bool(args.manifest):ap.error('--assembly-dir and --manifest must be supplied together')
    r=run(args.jigs_only,args.assembly_dir,args.manifest)
    if args.json:Path(args.json).write_text(json.dumps(r,indent=2))
    print(json.dumps(r,indent=2))
    sys.exit(0 if r['status']=='PASS' else 1)
