"""Validate head v03 CAD and STL-roundtrip mating paths without production export.

Only audit JSON is written. Actual production STLs can be substituted with
--stl-root after the parent exports the kit; then no generated triangles replace
the delivered geometry. All reported clearances are in assembled millimetres.
"""
from pathlib import Path
import sys, json, io, argparse, hashlib
import numpy as np
import trimesh
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from model.printkit.common import to_trimesh,from_mesh,union,box
from model.printkit import head,body

ROOT=Path(__file__).resolve().parents[1]
VOLUME_EPS=1e-5


def overlap(a,b):return max(0.,float((a^b).volume()))


def stl_solids(parts,stl_root=None):
    result={};records=[]
    for p in parts:
        mesh=to_trimesh(p.solid.simplify(.001))
        rot=np.eye(3) if p.orientation is None else np.asarray(p.orientation)
        mesh.vertices=mesh.vertices@rot.T;origin=mesh.bounds[0].copy();mesh.vertices-=origin
        if stl_root:
            path=Path(stl_root)/'parts'/p.color/(p.name+'.stl');raw=path.read_bytes()
        else:raw=mesh.export(file_type='stl')
        loaded=trimesh.load(io.BytesIO(raw),file_type='stl',force='mesh',process=True)
        assert loaded.is_watertight,(p.name,'STL watertightness')
        error=float(np.max(np.abs(mesh.extents-loaded.extents)))
        assert error<2e-5,(p.name,'STL/source size mismatch',error)
        world=(loaded.vertices+origin)@rot
        m=from_mesh(world,loaded.faces)
        assert len(m.decompose())==1,(p.name,'STL component count')
        result[p.name]=m
        records.append({'part':p.name,'sha256':hashlib.sha256(raw).hexdigest(),'watertight':True,
                        'components':1,'dimension_error_mm':error,'triangles':len(loaded.faces)})
    return result,records


def path_samples(moving,fixed,direction,distances):
    axis=np.asarray(direction,float)
    return [{'travel_mm':float(t),'overlap_mm3':overlap(moving.translate(axis*t),fixed)} for t in distances]


def run(stl_root=None):
    hp,info=head.build();bp,_=body.build()
    hoop=next(p for p in bp if p.name=='body_hoop_01')
    source={p.name:p.solid for p in hp+[hoop]}
    actual,records=stl_solids(hp+[hoop],stl_root)
    report={'status':'pending','geometry':'Delivered STL' if stl_root else 'In-memory binary STL roundtrip; no production STL export',
            'physical_fit':'untested','source_and_stl':{},'parts':records,'interfaces':info['metadata']}
    for kind,solids in [('source',source),('stl',actual)]:
        panels=union(*[s for name,s in solids.items() if name.startswith('head_') and name!='head_platform_snout'])
        platform=solids['head_platform_snout'];first=solids['body_hoop_01']
        # Begin 0.01 mm above the seat: seated broad-plane STL rounding is
        # classified separately rather than treated as an insertion obstacle.
        heights=np.r_[.01,np.arange(.125,50.001,.125)]
        drops=path_samples(platform,panels,[0,0,1],heights)
        hoop_drop=path_samples(first,platform,[0,0,1],np.r_[.01,np.arange(.05,8.001,.05)])
        inserts=[]
        for side,label in [(1,'A'),(-1,'B')]:
            origin,u,v,n=head.axes(side)
            cream=union(solids[f'head_{label}_cream_outer'],solids[f'head_{label}_cream_inner'])
            for color,axis in [('orange',n),('blue',-n)]:
                name=f'head_{label}_{color}';samples=path_samples(solids[name],cream,axis,np.arange(.01,8.001,.05))
                inserts.append({'part':name,'max_insertion_overlap_mm3':max(x['overlap_mm3'] for x in samples),
                                'seated_raw_contact_overlap_mm3':overlap(solids[name],cream)})
        seating_intersection=platform^panels
        # Intersections confined to the known seat plane by <10 nm are mesh
        # origin/float conversion noise, not a geometric interference.
        contact_depth=0.
        if not seating_intersection.is_empty():
            bb=np.asarray(seating_intersection.bounding_box()).reshape(2,3)
            contact_depth=float(np.max(np.abs(bb[:,2]-head.FLOOR_BOTTOM)))
        r={'platform_top_drop':{'range_mm':[.01,50],'step_mm':.125,'max_overlap_mm3':max(x['overlap_mm3'] for x in drops),'samples':drops},
           'first_hoop_drop':{'range_mm':[.01,8],'step_mm':.05,'max_overlap_mm3':max(x['overlap_mm3'] for x in hoop_drop),'samples':hoop_drop},
           'inserts':inserts,'platform_seated_raw_contact_overlap_mm3':overlap(platform,panels),
           'platform_seated_contact_max_distance_from_datum_mm':contact_depth}
        report['source_and_stl'][kind]=r
        assert r['platform_top_drop']['max_overlap_mm3']<VOLUME_EPS,(kind,'platform path',r['platform_top_drop']['max_overlap_mm3'])
        assert r['first_hoop_drop']['max_overlap_mm3']<VOLUME_EPS,(kind,'hoop path',r['first_hoop_drop']['max_overlap_mm3'])
        assert max(x['max_insertion_overlap_mm3'] for x in inserts)<VOLUME_EPS,(kind,'inset path')
        assert contact_depth<1e-5,(kind,'platform seating beyond float precision',contact_depth)
    # Whole D pins are owned by the inner parts only; outside halves stop at Z0.
    ownership=[]
    for label in ['A','B']:
        outer=actual[f'head_{label}_cream_outer'];inner=actual[f'head_{label}_cream_inner']
        outer_below=overlap(outer,box((0,0,-10.01),(1000,1000,20)))
        inner_min=inner.bounding_box()[2]
        assert outer_below<VOLUME_EPS,(label,'outer half still owns a foot pin')
        assert abs(inner_min+4.2)<1e-5,(label,'wrong pin tip',inner_min)
        ownership.append({'side':label,'outer_material_below_minus_0_01_mm3':outer_below,'inner_pin_tip_z_mm':inner_min})
    report['pin_ownership']=ownership
    # Digital tray/sand fixtures use the returned production cutters. A shifted
    # sand layer must not touch pins while they are located by the fixed tray.
    tray=box((85,0,-3.35),(45,65,2.7))-union(*info['base_socket_cutters'])
    sand=box((85,0,-1),(45,65,2.0))-union(*info['sand_clearance_cutters'])
    inners=union(actual['head_A_cream_inner'],actual['head_B_cream_inner'])
    shifted=[]
    for dx in [-.3,0,.3]:
        for dy in [-.3,0,.3]:
            value=overlap(inners,sand.translate((dx,dy,0)))
            shifted.append({'sand_translation_xy_mm':[dx,dy],'overlap_mm3':value})
            assert value<VOLUME_EPS,('shifted sand hits pins',dx,dy,value)
    report['synthetic_ground_fixture']={'tray_pin_overlap_mm3':overlap(inners,tray),'sand_shift_samples':shifted,
                                       'note':'Returned cutters in independent flat slabs; parent must also verify the real assembled v03 base.'}
    assert overlap(inners,tray)<VOLUME_EPS,'head pins do not fit tray locator cutters'
    report['status']='passed'
    return report


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--stl-root',type=Path)
    ap.add_argument('--out',type=Path,default=ROOT/'exports/dragon-pla-kit-v03/work/head-fit-validation.json')
    args=ap.parse_args();report=run(args.stl_root);args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2))
    print(json.dumps({'status':report['status'],'report':str(args.out),'parts':len(report['parts']),
                      'platform_stl_max_overlap_mm3':report['source_and_stl']['stl']['platform_top_drop']['max_overlap_mm3'],
                      'hoop_stl_max_overlap_mm3':report['source_and_stl']['stl']['first_hoop_drop']['max_overlap_mm3']},indent=2))

if __name__=='__main__':main()
