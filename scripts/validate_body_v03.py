#!/usr/bin/env python3
"""Validate v03 body fit using float32 STL geometry in assembly coordinates.

Default: build only the body and restore its in-memory STL roundtrips.
After full export: --restored <actual-assembly-npz-directory> --manifest <json>.
No production files are exported or changed. Results are a geometric screen,
not a prediction of physical fit or printer dimensional accuracy.
"""
from pathlib import Path
import argparse,json,math,sys,tempfile
import numpy as np
import trimesh
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from model.printkit.common import ROOT,from_mesh,to_trimesh,union,sample_route
from model.printkit.body import (build,CUTS,RAIL_ANGLES,UPPER_RAIL_END,rail_location,
    rail_install_direction,KEY_REAR,KEY_FRONT,KEY_WIDTH,KEY_BOTTOM,KEY_SOCKET_BOTTOM,
    KEY_SHOULDER_Z,KEY_SOCKET_MIN_FLOOR,RAIL_BUTT_GAP,PIER_BEARING_BOTTOM,
    PIER_BEARING_HALF_WIDTH,PIER_BEARING_HALF_LENGTH,local_box)


def overlap(a,b):return float((a^b).volume())


def first_contact(moving,fixed,direction,limit=.8,step=.025):
    d=np.asarray(direction,float);d/=np.linalg.norm(d)
    for high in np.arange(step,limit+step/2,step):
        if overlap(moving.translate(d*high),fixed)>1e-5:
            low=high-step
            for _ in range(15):
                middle=(low+high)/2
                if overlap(moving.translate(d*middle),fixed)>1e-5:high=middle
                else:low=middle
            return round(float((low+high)/2),6)
    return None


def rotation(axis,degrees):
    a=math.radians(degrees);x,y,z=axis
    k=np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
    return np.eye(3)+math.sin(a)*k+(1-math.cos(a))*(k@k)


def tilt_contact(moving,fixed,centre,axis,sign):
    def interferes(a):
        r=rotation(axis,a*sign)
        return overlap(moving.transform(np.column_stack((r,centre-r@centre))),fixed)>1e-5
    for high in np.arange(.05,12.05,.05):
        if interferes(high):
            low=high-.05
            for _ in range(15):
                middle=(low+high)/2
                if interferes(middle):high=middle
                else:low=middle
            return round(float((high+low)/2),6)
    return None


def validate(solids):
    failures=[];report={'hoops':[],'rail_grooves':[],'rail_seams':[],
                        'rail_insertion_paths':[],'pier_landings':[],'intersections':[]}
    def check(ok,message):
        if not ok:failures.append(message)
    names=list(solids)
    for name,solid in solids.items():
        check(len(solid.decompose())==1 and solid.volume()>0,f'{name}: not one positive solid')
        if name.startswith('body_hoop_'):
            expected=0 if int(name[-2:])<=15 else 2
            check(to_trimesh(solid).euler_number==expected,f'{name}: closed-loop/open-U topology changed')
    bounds={name:np.array(solid.bounding_box()).reshape(2,3) for name,solid in solids.items()}
    for i,a in enumerate(names):
        for b in names[:i]:
            if np.any(np.minimum(bounds[a][1],bounds[b][1])-np.maximum(bounds[a][0],bounds[b][0])<.005):continue
            vol=overlap(solids[a],solids[b])
            if vol>.001:report['intersections'].append({'a':a,'b':b,'mm3':vol})
    check(not report['intersections'],'Body pieces overlap by more than .001 mm3')
    for i in range(17):
        f=i/17;p,t,n=sample_route(f);j=min(3,np.searchsorted(CUTS,f,side='right')-1)
        hoop=solids[f'body_hoop_{i+1:02}'];beam=solids[f'body_beam_{j+1:02}']
        row={'hoop':i+1,'beam':int(j+1),'downward_free_motion_mm':first_contact(hoop,beam,(0,0,-1)),
             'side_free_motion_mm':[first_contact(hoop,beam,n),first_contact(hoop,beam,-n)],
             'axial_free_motion_mm':[first_contact(hoop,beam,t),first_contact(hoop,beam,-t)]}
        row['max_upward_removal_overlap_mm3']=max(overlap(hoop.translate((0,0,float(d))),beam) for d in np.arange(0,6.01,.25))
        check(row['downward_free_motion_mm'] is not None and row['downward_free_motion_mm']<.005,f'Hoop {i+1}: no positive height stop')
        check(all(x is not None and .14<x<.16 for x in row['side_free_motion_mm']+row['axial_free_motion_mm']),f'Hoop {i+1}: unexpected insertion clearance')
        check(row['max_upward_removal_overlap_mm3']<.001,f'Hoop {i+1}: upward insertion path blocked')
        floor=local_box(p,n,np.array([0,0,1.]),t,[-KEY_WIDTH/2-.15,KEY_SOCKET_BOTTOM-KEY_SOCKET_MIN_FLOOR,KEY_REAR-.15],
                        [KEY_WIDTH/2+.15,KEY_SOCKET_BOTTOM,KEY_FRONT+.15])
        missing=float((floor-beam).volume());row['missing_socket_floor_mm3']=missing
        check(missing<.002,f'Hoop {i+1}: incomplete {KEY_SOCKET_MIN_FLOOR} mm socket floor')
        if i in [1,10,15]:
            centre=p+np.array([0,0,KEY_SHOULDER_Z])
            row['seated_tilt_to_contact_deg']={label:[tilt_contact(hoop,beam,centre,axis,s) for s in [-1,1]]
                                               for label,axis in [('across',t),('along',n)]}
            check(all(x is not None and x<.05 for v in row['seated_tilt_to_contact_deg'].values() for x in v),f'Hoop {i+1}: seated shoulders permit excessive tilt')
            lifted=hoop.translate((0,0,.1))
            row['tilt_after_lifting_0_1mm_deg']={label:[tilt_contact(lifted,beam,centre+np.array([0,0,.1]),axis,s) for s in [-1,1]]
                                               for label,axis in [('across',t),('along',n)]}
        report['hoops'].append(row)
    fixed=union(*[s for n,s in solids.items() if n.startswith(('body_hoop','body_beam'))])
    for track,angle in enumerate(RAIL_ANGLES,1):
        for j,f in enumerate(CUTS[1:-1],1):
            q=rail_location(f,angle)[0];d=rail_location(f+.001,angle)[0]-rail_location(f-.001,angle)[0];d/=np.linalg.norm(d)
            ext=[]
            for section in [j,j+1]:
                v=to_trimesh(solids[f'body_rail_{track:02}_section_{section:02}']).vertices
                v=v[np.linalg.norm(v-q,axis=1)<4];ext.append((v-q)@d)
            gap=float(ext[1].min()-ext[0].max());report['rail_seams'].append({'track':track,'between':[j,j+1],'gap_mm':gap})
            check(abs(gap-RAIL_BUTT_GAP)<.003,f'Rail {track}, seam {j}: unexpected butt gap {gap}')
        for j,(a,b) in enumerate(zip(CUTS,CUTS[1:]),1):
            if track<=2:b=min(b,UPPER_RAIL_END)
            name=f'body_rail_{track:02}_section_{j:02}';direction=rail_install_direction(a,b,angle)
            maximum=max(overlap(solids[name].translate(direction*d),fixed) for d in np.arange(0,6.01,.25))
            report['rail_insertion_paths'].append({'part':name,'direction':direction.tolist(),'max_overlap_mm3':maximum})
            check(maximum<.001,f'{name}: whole segment insertion path blocked')
        for i in range(18 if track>=3 else 15):
            f=i/17;p,t,n=sample_route(f);j=min(3,np.searchsorted(CUTS,f,side='right')-1)
            rail=solids[f'body_rail_{track:02}_section_{j+1:02}'];hoop=solids[f'body_hoop_{i+1:02}']
            q,_,rad=rail_location(f,angle);rt=rail_location(min(1,f+.001),angle)[0]-rail_location(max(0,f-.001),angle)[0];rt/=np.linalg.norm(rt)
            side=np.cross(rt,rad);side/=np.linalg.norm(side);rad=np.cross(side,rt);rad/=np.linalg.norm(rad)
            vals=[first_contact(rail,hoop,d,limit=1.0) for d in [side,-side,-rad]]
            report['rail_grooves'].append({'track':track,'hoop':i+1,'side_positive_negative_inward_mm':vals})
            check(all(v is None or v>=.199 for v in vals),f'Rail {track}, hoop {i+1}: <0.20 mm directional fitting margin {vals}')
    for i,f in enumerate([2/17,5/17,8/17,12/17,15/17],1):
        p,t,n=sample_route(f);j=min(3,np.searchsorted(CUTS,f,side='right')-1);beam=solids[f'body_beam_{j+1:02}']
        landing=local_box(p,n,np.array([0,0,1.]),t,[-PIER_BEARING_HALF_WIDTH,PIER_BEARING_BOTTOM,-PIER_BEARING_HALF_LENGTH],
                         [PIER_BEARING_HALF_WIDTH,PIER_BEARING_BOTTOM+.1,PIER_BEARING_HALF_LENGTH])
        missing=(landing-beam).volume()
        report['pier_landings'].append({'pier':i,'beam':int(j+1),'bottom_z_mm':float(p[2]+PIER_BEARING_BOTTOM),'footprint_mm':[5.2,3.0],'missing_bearing_skin_mm3':missing})
        check(missing<.002,f'Pier {i}: incomplete flat beam bearing')
    report['failures']=failures;report['passed']=not failures
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--restored',type=Path)
    parser.add_argument('--manifest',type=Path)
    parser.add_argument('--output',type=Path,default=ROOT/'exports/dragon-pla-kit-v03/work/body-fit-validation.json')
    args=parser.parse_args();solids={};print_meshes={}
    if args.restored:
        for path in sorted(args.restored.glob('body_*.npz')):
            z=np.load(path);solids[path.stem]=from_mesh(z['vertices'],z['faces'])
        basis='Delivered STL triangles restored to assembly coordinates: '+str(args.restored)
        if len(solids)!=38:raise ValueError(f'Expected 38 body parts, found {len(solids)}')
        if args.manifest:
            manifest=json.loads(args.manifest.read_text())
            for part in manifest['parts']:
                if part['name'] in solids and part['supports']=='none':
                    print_meshes[part['name']]=trimesh.load_mesh(args.manifest.parent/part['file'],process=True)
    else:
        from scripts.build_print_kit import print_mesh
        parts,info=build()
        for part in parts:
            mesh=print_mesh(part);tol=mesh.metadata.get('simplification_tolerance_mm',.001)
            reference=to_trimesh(part.solid.simplify(tol) if tol else part.solid)
            rot=np.eye(3) if part.orientation is None else part.orientation
            origin=(reference.vertices@rot.T).min(axis=0)
            solids[part.name]=from_mesh((mesh.vertices+origin)@rot,mesh.faces)
            if part.supports=='none':print_meshes[part.name]=mesh
        basis='Current source body only, actual float32 STL roundtrip restored to assembly coordinates. Production outputs not modified.'
    report=validate(solids);report['basis']=basis
    if print_meshes:
        from scripts.audit_tail_v02 import audit_part
        report['flat_print_screen']=[]
        with tempfile.TemporaryDirectory(prefix='dragon-body-v03-screen-') as temp:
            directory=Path(temp)
            for name,mesh in print_meshes.items():
                path=directory/(name+'.stl');mesh.export(path)
                result=audit_part({'name':name,'file':path.name,'supports':'none'},directory,.16,.10,.02)
                report['flat_print_screen'].append(result)
                if result['unresolved_support_free_flag']:
                    report['failures'].append(name+': unresolved flat-print overhang flag')
        report['passed']=not report['failures']
    report['limits']='Geometric contact and sampled straight insertion tests; no physical fit, support-removal or continuous-path guarantee. Contact threshold 0.00001 mm3. Values are not printer precision claims.'
    if args.manifest:report['manifest']=str(args.manifest)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':report['passed'],'failures':report['failures'],'parts':len(solids),'output':str(args.output)},indent=2))
    if not report['passed']:raise SystemExit(1)


if __name__=='__main__':main()
