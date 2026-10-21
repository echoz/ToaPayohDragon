"""Build the colour STL kit, assembled geometry and validation manifest."""
from pathlib import Path
import sys,json,math,io
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import trimesh
from model.printkit.common import *
from model.printkit import body,head,slides,supports_base
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'exports/dragon-pla-kit-v03'

def plain(o):
    if isinstance(o,np.ndarray):return o.tolist()
    if isinstance(o,(np.floating,np.integer)):return o.item()
    raise TypeError(type(o).__name__)

def clean_info(info):
    if 'metadata' in info:return info['metadata']
    return {k:v for k,v in info.items() if not k.endswith('_cutters')}

def make_parts():
    b,bi=body.build();print('Body',len(b),flush=True)
    h,hi=head.build();print('Head',len(h),flush=True)
    from model.printkit.entrance import build as entrance_build
    e,ei=entrance_build();print('Entrance',len(e),flush=True)
    s,si=slides.build(union(*(p.solid for p in h)), union(*(p.solid for p in e)));print('Slides',len(s),flush=True)
    beams=union(*(p.solid for p in b if p.name.startswith('body_beam')))
    pi,pii=supports_base.build_piers(beams);print('Piers',len(pi),flush=True)
    sockets=hi['base_socket_cutters']+si['base_socket_cutters']+pii['base_socket_cutters']+ei.get('base_socket_cutters',[])
    sand_sockets=[]
    for family in [hi,si,pii,ei]:sand_sockets+=family.get('sand_clearance_cutters',family.get('base_socket_cutters',[]))
    base,basei=supports_base.build_base(sockets,sand_sockets);print('Base',len(base),flush=True)
    from model.printkit.coupon import build as coupon_build
    c,ci=coupon_build(b);print('Test pieces',len(c),flush=True)
    parts=b+h+s+pi+e+base
    info={name:clean_info(x) for name,x in [('body',bi),('head',hi),('slides',si),('piers',pii),('entrance',ei),('base',basei),('coupon',ci)]}
    from model.printkit import body_samples,head_samples,entrance_samples,base_samples,assembly_aids
    for module in [body_samples,head_samples,entrance_samples,base_samples,assembly_aids]:
        sample,sample_info=module.build(parts)
        c+=sample;info[module.__name__.split('.')[-1]]=clean_info(sample_info)
        print(module.__name__.split('.')[-1],len(sample),flush=True)
    return parts,c,info

def collision_check(parts):
    bounds=[np.asarray(p.solid.bounding_box()).reshape(2,3) for p in parts]
    result=[]
    for i,p in enumerate(parts):
        for j in range(i):
            q=parts[j]
            if np.any(np.minimum(bounds[i][1],bounds[j][1])-np.maximum(bounds[i][0],bounds[j][0])<.005):continue
            volume=(p.solid ^ q.solid).volume()
            if volume>.015:result.append({'a':p.name,'b':q.name,'overlap_mm3':round(volume,5)})
    return sorted(result,key=lambda x:-x['overlap_mm3'])

def print_mesh(part):
    # Check the actual float32 format. Keep closed topology rather than deleting
    # individual tiny triangles. At most 5 microns of cleanup is permitted.
    for tolerance in [.001,0.,.0001,.003,.005]:
        solid=part.solid.simplify(tolerance) if tolerance else part.solid
        mesh=to_trimesh(solid)
        if not mesh.is_watertight:continue
        if part.orientation is not None:
            rot=np.asarray(part.orientation)
            assert rot.shape==(3,3) and np.linalg.det(rot)>.999
            mesh.vertices=mesh.vertices@rot.T
        mesh.vertices-=mesh.bounds[0]
        check=trimesh.load(io.BytesIO(mesh.export(file_type='stl')),file_type='stl',force='mesh',process=True)
        if not check.is_watertight or check.volume<=0:continue
        try:
            s=from_mesh(check.vertices,check.faces)
        except ValueError:continue
        if len(s.decompose())!=1:continue
        check.metadata['simplification_tolerance_mm']=tolerance
        return check
    raise ValueError((part.name,'No valid connected STL after permitted cleanup'))

def pack_group(items):
    plates=[]
    for item in sorted(items,key=lambda x:-(x['mesh'].extents[0]+6)*(x['mesh'].extents[1]+6)):
        chosen=None
        for ip,plate in enumerate(plates):
            for ir,(x,y,w,h) in enumerate(plate['free']):
                for rotate in [False,True]:
                    a,b=item['mesh'].extents[:2]
                    if rotate:a,b=b,a
                    a+=6;b+=6
                    if a<=w+1e-6 and b<=h+1e-6:
                        score=min(w-a,h-b)
                        if chosen is None or score<chosen[0]:chosen=(score,ip,ir,rotate,a,b)
        if chosen is None:
            plates.append({'free':[(0.,0.,220.,215.)],'items':[]})
            ip=len(plates)-1;ir=0;rotate=False;a,b=item['mesh'].extents[:2]+6
            if not(a<=220 and b<=215):
                a,b=b,a;rotate=True
            assert a<=220 and b<=215,(item['part'].name,a,b)
        else:_,ip,ir,rotate,a,b=chosen
        plate=plates[ip];x,y,w,h=plate['free'].pop(ir)
        # Non-overlapping guillotine split; deliberately conservative spacing.
        if w-a>1e-6:plate['free'].append((x+a,y,w-a,b))
        if h-b>1e-6:plate['free'].append((x,y+b,w,h-b))
        mesh=item['mesh'].copy()
        if rotate:
            mesh.vertices=mesh.vertices@np.array([[0,1,0],[-1,0,0],[0,0,1]])
            mesh.vertices-=mesh.bounds[0]
        mesh.vertices+=np.array([25+x+3,30+y+3,0])
        plate['items'].append({'item':item,'mesh':mesh,'rotate90':rotate,'origin_mm':[25+x+3,30+y+3,0]})
    return plates

def export_all(parts,tests,info):
    (OUT/'work/assembly').mkdir(parents=True,exist_ok=True)
    records=[];items=[];assembly=[]
    for part in parts+tests:
        is_test=part.name.startswith('test_')
        dest=OUT/('test-first' if is_test else 'parts')/part.color/(part.name+'.stl');dest.parent.mkdir(parents=True,exist_ok=True)
        mesh=print_mesh(part);mesh.export(dest)
        loaded=trimesh.load(dest,force='mesh',process=True)
        loaded.remove_unreferenced_vertices()
        # Repair float32 STL welding only when it actually changes topology.
        if not loaded.is_watertight:
            mesh=to_trimesh(part.solid.simplify(.003))
            if part.orientation is not None:mesh.vertices=mesh.vertices@np.asarray(part.orientation).T
            mesh.vertices-=mesh.bounds[0];mesh.export(dest);loaded=trimesh.load(dest,force='mesh',process=True)
        assert loaded.is_watertight,(part.name,'STL roundtrip not watertight')
        s=from_mesh(loaded.vertices,loaded.faces)
        assert len(s.decompose())==1 and loaded.volume>0,(part.name,'loose shell or negative volume')
        r={'name':part.name,'color':part.color,'file':str(dest.relative_to(OUT)),
           'dimensions_mm':np.round(loaded.extents,3).tolist(),'volume_mm3':round(loaded.volume,3),
           'triangles':len(loaded.faces),'watertight':True,'connected_components':1,
           'simplification_tolerance_mm':mesh.metadata.get('simplification_tolerance_mm',.001),
           'orientation':'Already oriented and seated on Z=0; keep 100% scale.',
           'supports':part.supports,'notes':part.notes,'tags':part.tags,'test':is_test}
        records.append(r);items.append({'part':part,'mesh':loaded,'test':is_test})
        # Restore actual exported float32 triangles to assembly coordinates.
        # This same mesh drives the preview and all final tolerance checks.
        tolerance=r['simplification_tolerance_mm']
        source=to_trimesh(part.solid.simplify(tolerance) if tolerance else part.solid)
        rotation=np.eye(3) if part.orientation is None else np.asarray(part.orientation)
        source.vertices=source.vertices@rotation.T
        assert np.max(np.abs(source.extents-loaded.extents))<.02,(part.name,'print transform mismatch')
        world_vertices=(loaded.vertices+source.bounds[0])@rotation
        r['print_rotation_world_to_bed']=rotation.tolist()
        r['print_minimum_before_translation_mm']=source.bounds[0].tolist()
        file=OUT/'work/assembly'/(part.name+'.npz')
        np.savez_compressed(file,vertices=world_vertices,faces=loaded.faces)
        if not is_test:
            assembly.append({'name':part.name,'color':part.color,'file':str(file)})
        print('Exported',part.name,flush=True)
    plate_records=[]
    for color in COLORS:
        for purpose in ['production','fit_test','assembly_jig']:
            test=purpose!='production'
            for supported in [False,True]:
                group=[i for i in items if i['part'].color==color and i['test']==test and (not test or i['part'].tags.get('purpose','fit_test')==purpose) and (i['part'].supports!='none')==supported]
                for k,plate in enumerate(pack_group(group),1):
                    prefix='jig' if purpose=='assembly_jig' else ('test' if test else 'plate')
                    stem=f'{prefix}_{color}_{"supports" if supported else "flat"}_{k:02}'
                    dest=OUT/'plates'/color/(stem+'.stl');dest.parent.mkdir(parents=True,exist_ok=True)
                    trimesh.util.concatenate([i['mesh'] for i in plate['items']]).export(dest)
                    plate_records.append({'name':stem,'color':color,'file':str(dest.relative_to(OUT)),'supports_required':supported,'test':test,'purpose':purpose,
                                          'parts':[{'name':i['item']['part'].name,'origin_mm':i['origin_mm'],'rotate90':i['rotate90']} for i in plate['items']],
                                          'layout_area_mm':[220,215],'packing':'6 mm between object bounding boxes; left/front keep-out margins preserved.'})
    collisions=collision_check(parts)
    report={'target':{'printer':'Bambu Lab X1 Carbon','nozzle_mm':.4,'material':'PLA','unit':'millimetres','bed_nominal_mm':[256,256,256]},
            'status':'Digitally checked prototype; physical fit and complete print untested.',
            'colors':COLORS,'part_count':len(parts),'test_part_count':len(tests),'plate_count':len(plate_records),
            'fit_sample_count':sum(p.tags.get('purpose')!='assembly_jig' for p in tests),'assembly_jig_count':sum(p.tags.get('purpose')=='assembly_jig' for p in tests),
            'parts':records,'plates':plate_records,'interfaces':info,'inter_part_overlaps':collisions,
            'validation':{'all_part_stls_watertight':True,'one_connected_solid_per_part_stl':True,'positive_volumes':True,
                          'max_packing_area_mm':[220,215],'slicer_status':'pending','physical_test':'pending'},
            'notes':['Plate STLs intentionally contain multiple disconnected print pieces.','Individual files are already in print orientation, not assembly coordinates.','No G-code or printer send operation is performed by this script.']}
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2,default=plain))
    (OUT/'work/assembly.json').write_text(json.dumps(assembly,indent=2))
    print('PARTS',len(parts),'TESTS',len(tests),'PLATES',len(plate_records),'OVERLAPS',len(collisions),flush=True)
    print(json.dumps(collisions,indent=2))
    return report

if __name__=='__main__':
    parts,tests,info=make_parts()
    if '--audit-only' in sys.argv:
        collisions=collision_check(parts)
        print(json.dumps(collisions,indent=2))
        (OUT/'work/interference-audit.json').write_text(json.dumps(collisions,indent=2))
    else:export_all(parts,tests,info)
