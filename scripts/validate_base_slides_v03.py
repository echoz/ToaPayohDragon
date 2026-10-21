#!/usr/bin/env python3
"""Independent v03 base/pier/slide fit checks; production modules are read only.

Default builds the integrated production geometry without test samples. Pass
--assembly-dir to check final restored assembly NPZ instead, and --manifest for
the supplied STL orientations and flat-print screen.
"""
from pathlib import Path
import argparse,json,math,sys,tempfile,hashlib
import numpy as np
import trimesh
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from model.printkit.common import ROOT,from_mesh,to_trimesh,union,box,sample_route
from model.printkit import body,head,entrance,slides,supports_base
from scripts.validate_body_v03 import overlap

UP=np.array([0.,0.,1.])


def first_contact(moving,fixed,direction,limit=.8,step=.025):
    # Broad nominally contacting planes can accumulate minute STL-rounding
    # overlap volume. Test added penetration above that baseline, otherwise a
    # flat bearing would incorrectly report zero horizontal clearance.
    baseline=overlap(moving,fixed);threshold=baseline+1e-4
    d=np.asarray(direction,float);d/=np.linalg.norm(d)
    for high in np.arange(step,limit+step/2,step):
        if overlap(moving.translate(d*high),fixed)>threshold:
            low=high-step
            for _ in range(15):
                middle=(low+high)/2
                if overlap(moving.translate(d*middle),fixed)>threshold:high=middle
                else:low=middle
            return round(float((low+high)/2),6)
    return None


def sampled_cream_web(cream,number):
    from shapely.geometry import Polygon,LineString
    from scripts.audit_tail_v02 import section_geometry
    line,length,frame=slides._path(number)
    patch=Polygon(slides._profile(length,frame)).buffer(-1.35*slides.F,join_style='mitre')
    measured=[];skipped=0
    def lines(geom):
        if geom.geom_type=='LineString':return [geom]
        if hasattr(geom,'geoms'):return [p for g in geom.geoms for p in lines(g)]
        return []
    inner=4.35*slides.F;outer=6.93*slides.F
    for f in np.arange(.1,.951,.05):
        s=float(length*f);intervals=lines(patch.intersection(LineString([(s,-100),(s,100)])))
        for interval in intervals:
            zz=np.asarray(interval.coords)[:,1];low,high=zz.min(),zz.max()
            if high-low<2:continue
            q,t,n=frame(s)
            for vertical_fraction in [.2,.5,.8]:
                z=float(low+(high-low)*vertical_fraction);section=section_geometry(cream,z)
                for sign in [-1,1]:
                    ray=LineString([q[:2]+sign*n[:2]*(inner-.1),q[:2]+sign*n[:2]*(outer+.1)])
                    spans=lines(section.intersection(ray));values=[]
                    for span in spans:
                        d=(np.asarray(span.coords)-q[:2])@(sign*n[:2]);a,b=float(d.min()),float(d.max())
                        if a<=inner+.02 and b>=inner+.02:values.append(b-inner)
                    if values:
                        measured.append({'slide':number,'fraction':float(f),'side':'left' if sign<0 else 'right',
                                         'z_mm':z,'web_from_nominal_inner_wall_mm':max(values)})
                    else:skipped+=1
    return {'slide':number,'sample_count':len(measured),'skipped_empty_or_edge_samples':skipped,
            'minimum_sample':min(measured,key=lambda v:v['web_from_nominal_inner_wall_mm']) if measured else None,
            'samples':measured,'limits':'Normal-line sections at18 route stations and3 interior heights per inlay side; excludes profile edges/head trims. Not a global minimum wall-thickness proof.'}


def source_parts():
    b,bi=body.build();print('Body built',flush=True)
    h,hi=head.build();print('Head built',flush=True)
    e,ei=entrance.build();print('Entrance built',flush=True)
    s,si=slides.build(union(*[p.solid for p in h]),union(*[p.solid for p in e]));print('Slides built',flush=True)
    pi,pii=supports_base.build_piers(union(*[p.solid for p in b if p.name.startswith('body_beam')]))
    sockets=[];sand=[]
    for info in [hi,si,pii,ei]:
        sockets+=info.get('base_socket_cutters',[])
        sand+=info.get('sand_clearance_cutters',info.get('base_socket_cutters',[]))
    base,basei=supports_base.build_base(sockets,sand);print('Piers and base built',flush=True)
    return b+h+e+s+pi+base


def validate(solids):
    results={'pier_seats':[],'pier_feet':[],'pier_inlays':[],'sand':[],
             'base_join_keys':[],'slide_feet':[],'slide_inlays':[],'intersections':[],'sampled_slide_webs':[]}
    failures=[]
    def check(ok,message):
        if not ok:failures.append(message)
    def path(moving,fixed,direction,distance,step=.2):
        d=np.asarray(direction,float)
        return max(overlap(moving.translate(d*x),fixed) for x in np.arange(0,distance+step/2,step))
    focus=[n for n in solids if n.startswith(('pier_','base_','slide_'))]
    bounds={n:np.array(s.bounding_box()).reshape(2,3) for n,s in solids.items()}
    done=set()
    for a in focus:
        check(len(solids[a].decompose())==1 and solids[a].volume()>0,a+': not one positive solid')
        for b in solids:
            pair=tuple(sorted([a,b]))
            if a==b or pair in done:continue
            done.add(pair)
            if np.any(np.minimum(bounds[a][1],bounds[b][1])-np.maximum(bounds[a][0],bounds[b][0])<.005):continue
            v=overlap(solids[a],solids[b])
            if v>.005:results['intersections'].append({'a':a,'b':b,'volume_mm3':v})
    check(not results['intersections'],'Material overlap in base/pier/slide interfaces')
    trays=union(solids['base_left_tray'],solids['base_right_tray'])
    sand=union(solids['base_left_sand'],solids['base_right_sand'])
    base=union(trays,sand)
    below_sand=box((0,0,-12),(1000,1000,20)) # top Z=-2
    sand_depth=box((0,0,-1),(1000,1000,1.9998))
    for i,f in enumerate([2/17,5/17,8/17,12/17,15/17],1):
        p,t,n=sample_route(f);j=min(3,np.searchsorted(body.CUTS,f,side='right')-1)
        pier=union(solids[f'pier_{i:02}_front_half'],solids[f'pier_{i:02}_back_half'])
        beam=solids[f'body_beam_{j+1:02}']
        row={'pier':i,'beam':int(j+1),'down_to_contact_mm':first_contact(beam,pier,-UP),
             'side_to_contact_mm':[first_contact(beam,pier,n),first_contact(beam,pier,-n)],
             'upward_path_overlap_mm3':path(beam,pier,UP,4)}
        check(row['down_to_contact_mm'] is not None and row['down_to_contact_mm']<.005,f'Pier{i}: beam lacks positive height stop')
        check(row['upward_path_overlap_mm3']<.005,f'Pier{i}: beam vertical insertion blocked')
        results['pier_seats'].append(row)
        deep=pier^below_sand;passage=pier^sand_depth
        row={'pier':i,'tray_engagement_mm':-2-float(np.array(deep.bounding_box())[2]),
             'ground_stop_down_mm':first_contact(pier,base,-UP),
             'tray_clearance_n_mm':[first_contact(deep,trays,n),first_contact(deep,trays,-n)],
             'tray_clearance_t_mm':[first_contact(deep,trays,t),first_contact(deep,trays,-t)],
             'sand_passage_n_mm':[first_contact(passage,sand,n,limit=1.2),first_contact(passage,sand,-n,limit=1.2)],
             'sand_passage_t_mm':[first_contact(passage,sand,t,limit=1.2),first_contact(passage,sand,-t,limit=1.2)],
             'vertical_insertion_overlap_mm3':path(pier,base,UP,5)}
        check(abs(row['tray_engagement_mm']-2.2)<.003,f'Pier{i}: wrong structural tray engagement')
        check(row['ground_stop_down_mm'] is not None and row['ground_stop_down_mm']<.005,f'Pier{i}: no ground height datum')
        check(all(v is not None and .19<=v<=.21 for v in row['tray_clearance_n_mm']+row['tray_clearance_t_mm']),f'Pier{i}: unexpected tray side clearance')
        check(row['vertical_insertion_overlap_mm3']<.005,f'Pier{i}: deep key insertion blocked')
        results['pier_feet'].append(row)
        for sign,label in [(1,'front'),(-1,'back')]:
            inlay=solids[f'pier_{i:02}_{label}_inlay'];direction=t*sign
            row={'pier':i,'side':label,'inward_to_contact_mm':first_contact(inlay,pier,-direction),
                 'outward_insertion_overlap_mm3':path(inlay,pier,direction,2)}
            check(row['inward_to_contact_mm'] is not None and row['inward_to_contact_mm']<.005,f'Pier{i}/{label}: inlay lacks seating land')
            check(row['outward_insertion_overlap_mm3']<.005,f'Pier{i}/{label}: inlay insertion blocked')
            results['pier_inlays'].append(row)
    for label in ['left','right']:
        sheet=solids[f'base_{label}_sand']
        row={'side':label,'down_to_contact_mm':first_contact(sheet,trays,-UP),
             'xy_to_contact_mm':{name:first_contact(sheet,trays,d) for name,d in [('x+', [1,0,0]),('x-',[-1,0,0]),('y+',[0,1,0]),('y-',[0,-1,0])]},
             'upward_insertion_overlap_mm3':path(sheet,trays,UP,2)}
        check(row['down_to_contact_mm'] is not None and row['down_to_contact_mm']<.005,f'{label} sand: no height datum')
        check(row['upward_insertion_overlap_mm3']<.005,f'{label} sand: register insertion blocked')
        results['sand'].append(row)
    for family in ['tray','sand']:
        l=to_trimesh(solids[f'base_left_{family}']).bounds[1,0]
        r=to_trimesh(solids[f'base_right_{family}']).bounds[0,0]
        results[family+'_seam_gap_mm']=float(r-l)
        check(abs(r-l)<.003,f'{family}: seam not closed at intended datum')
    for i in [1,2]:
        peg=solids[f'base_join_key_{i:02}']
        row={'key':i,'down_to_contact_mm':first_contact(peg,trays,-UP),
             'open_top_insertion_overlap_mm3':path(peg,trays,UP,4),
             'xy_to_contact_mm':[first_contact(peg,trays,d) for d in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0)]]}
        check(row['down_to_contact_mm'] is not None and row['down_to_contact_mm']<.005,f'Tray key{i}: no bottom stop')
        check(row['open_top_insertion_overlap_mm3']<.005,f'Tray key{i}: open-top insertion blocked')
        results['base_join_keys'].append(row)
    for number in [1,2]:
        line,length,frame=slides._path(number)
        cream=solids[f'slide_{number}_cream'];peg=solids[f'slide_{number}_peg']
        web=sampled_cream_web(cream,number);results['sampled_slide_webs'].append(web)
        check(web['minimum_sample'] is not None and web['minimum_sample']['web_from_nominal_inner_wall_mm']>=1.0,
              f'Slide{number}: sampled cream web falls below1.0mm review threshold')
        q,t,n=frame(length*.95);deep=peg^below_sand;passage=peg^sand_depth
        row={'slide':number,'ground_stop_down_mm':first_contact(cream,base,-UP),
             'tray_engagement_mm':-2-float(np.array(deep.bounding_box())[2]),
             'tray_side_clearance_mm':[first_contact(deep,trays,d) for d in [t,-t,n,-n]],
             'sand_passage_clearance_mm':[first_contact(passage,sand,d,limit=1.2) for d in [t,-t,n,-n]],
             'slide_cavity_clearance_mm':[first_contact(peg,cream,d) for d in [t,-t,n,-n]],
             'slide_over_peg_insertion_overlap_mm3':path(cream,peg,UP,3),
             'peg_into_tray_insertion_overlap_mm3':path(peg,trays,UP,5)}
        check(row['ground_stop_down_mm'] is not None and row['ground_stop_down_mm']<.005,f'Slide{number}: no ground datum')
        check(abs(row['tray_engagement_mm']-2.2)<.003,f'Slide{number}: wrong tray engagement')
        check(all(v is not None and .19<=v<=.21 for v in row['tray_side_clearance_mm']+row['slide_cavity_clearance_mm']),f'Slide{number}: unexpected key side fit')
        check(row['slide_over_peg_insertion_overlap_mm3']<.005 and row['peg_into_tray_insertion_overlap_mm3']<.005,f'Slide{number}: key insertion blocked')
        results['slide_feet'].append(row)
        p,t,n=frame(length*.55)
        for sign,label in [(-1,'left'),(1,'right')]:
            orange=solids[f'slide_{number}_orange_{label}'];direction=n*sign
            row={'slide':number,'side':label,'direction':direction.tolist(),
                 'inward_to_contact_mm':first_contact(orange,cream,-direction),
                 'outward_insertion_overlap_mm3':path(orange,cream,direction,3.2,.1)}
            check(row['inward_to_contact_mm'] is not None and row['inward_to_contact_mm']<.005,f'Slide{number}/{label}: no inlay seating stop')
            check(row['outward_insertion_overlap_mm3']<.005,f'Slide{number}/{label}: curved inlay insertion blocked')
            results['slide_inlays'].append(row)
    results['failures']=failures;results['passed']=not failures
    return results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assembly-dir',type=Path)
    parser.add_argument('--manifest',type=Path)
    parser.add_argument('--output',type=Path,default=ROOT/'exports/dragon-pla-kit-v03/work/base-slides-fit-validation.json')
    args=parser.parse_args();solids={};print_meshes={};file_evidence=[]
    if args.assembly_dir:
        for file in args.assembly_dir.glob('*.npz'):
            if file.stem.startswith('test_'):continue
            data=np.load(file);solids[file.stem]=from_mesh(data['vertices'],data['faces'])
        basis='Restored final assembly meshes: '+str(args.assembly_dir)
        if args.manifest:
            m=json.loads(args.manifest.read_text())
            for p in m['parts']:
                if p['test']:continue
                if 'print_rotation_world_to_bed' in p and 'print_minimum_before_translation_mm' in p:
                    file=args.manifest.parent/p['file'];actual=trimesh.load_mesh(file,process=True)
                    rot=np.asarray(p['print_rotation_world_to_bed']);origin=np.asarray(p['print_minimum_before_translation_mm'])
                    solids[p['name']]=from_mesh((actual.vertices+origin)@rot,actual.faces)
                    file_evidence.append({'name':p['name'],'file':p['file'],'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
                if p['name'].startswith(('pier_','base_','slide_')) and p['supports']=='none' and not p['test']:
                    print_meshes[p['name']]=trimesh.load_mesh(args.manifest.parent/p['file'],process=True)
            if file_evidence:basis='Actual delivered STL triangles restored with the final manifest print transforms; assembly NPZ supplies fallback geometry only.'
    else:
        from scripts.build_print_kit import print_mesh
        for part in source_parts():
            mesh=print_mesh(part);tol=mesh.metadata.get('simplification_tolerance_mm',.001)
            reference=to_trimesh(part.solid.simplify(tol) if tol else part.solid)
            rot=np.eye(3) if part.orientation is None else part.orientation
            origin=(reference.vertices@rot.T).min(axis=0)
            solids[part.name]=from_mesh((mesh.vertices+origin)@rot,mesh.faces)
            if part.name.startswith(('pier_','base_','slide_')) and part.supports=='none':print_meshes[part.name]=mesh
        basis='Integrated current production source; float32 STL roundtrips restored to world coordinates. No test samples built and no production exports changed.'
    results=validate(solids);results['basis']=basis
    if file_evidence:results['actual_stl_files']=file_evidence
    if print_meshes:
        from scripts.audit_tail_v02 import audit_part
        results['flat_print_screen']=[]
        with tempfile.TemporaryDirectory(prefix='dragon-base-slides-v03-') as temp:
            directory=Path(temp)
            for name,mesh in print_meshes.items():
                path=directory/(name+'.stl');mesh.export(path)
                row=audit_part({'name':name,'file':path.name,'supports':'none'},directory,.16,.10,.02)
                # Float32 conversion can tip a mathematically45 degree chamfer
                # by ~.001 degree. Retain raw metrics, and distinguish this
                # numerical boundary from a material overhang using0.01 degree.
                triangles=mesh.triangles
                down=(mesh.face_normals[:,2]<-math.sin(math.radians(45.01)))&(triangles[:,:,2].max(axis=1)>.1)
                meaningful=float(mesh.area_faces[down].sum())
                row['face_angle_numerical_tolerance_deg']=.01
                row['downward_area_beyond_45_01deg_mm2']=meaningful
                row['raw_unresolved_support_free_flag']=row['unresolved_support_free_flag']
                row['unresolved_support_free_flag']=bool(row['flagged_layer_count'] or meaningful>.02)
                results['flat_print_screen'].append(row)
                if row['unresolved_support_free_flag']:results['failures'].append(name+': unresolved flat-print overhang flag')
    results['passed']=not results['failures']
    results['limits']='Geometric checks using0.0001mm3 added penetration above baseline STL contact for first-contact probes, and sampled straight insertion paths. Face screen allows0.01degree numerical tolerance at45degree chamfers. Not a physical fit, continuous-motion or support-removal guarantee.'
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps({'passed':results['passed'],'failures':results['failures'],'intersections':results['intersections'],'output':str(args.output)},indent=2))
    if not results['passed']:raise SystemExit(1)


if __name__=='__main__':main()
