"""Shared final-millimetre CAD helpers for the colour-separated PLA kit."""
from dataclasses import dataclass,field
from pathlib import Path
from functools import lru_cache
import json,math
import numpy as np
import trimesh
import manifold3d as m3d
from shapely.geometry import Polygon,MultiPolygon

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'exports/dragon-pla-kit/work/source-v06'
F=1.0696541014508294
CLEARANCE=.30
COLORS={'cream':'#F4EBDD','orange':'#DA6946','blue':'#387FA7','sage':'#8DAB9B','red':'#B95343','sand':'#DCCBAA'}
@dataclass
class Part:
    name:str
    color:str
    solid:object
    orientation:object=None
    notes:str=''
    supports:str='none'
    tags:dict=field(default_factory=dict)

def from_mesh(vertices,faces):
    tm=trimesh.Trimesh(vertices=np.asarray(vertices),faces=np.asarray(faces),process=True)
    tm.remove_unreferenced_vertices()
    if tm.volume<0:tm.invert()
    result=m3d.Manifold(m3d.Mesh64(np.asarray(tm.vertices,dtype=np.float64),np.asarray(tm.faces,dtype=np.uint64)))
    if result.status()!=m3d.Error.NoError:raise ValueError(f'Mesh import: {result.status()}')
    return result

def load_source(name):
    z=np.load(SOURCE/(name+'.npz'))
    return from_mesh(z['vertices'],z['faces'])

def to_trimesh(solid):
    mesh=solid.to_mesh64()
    return trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:,:3],faces=np.asarray(mesh.tri_verts),process=True)

def union(*solids):
    solids=[m for m in solids if m is not None and not m.is_empty()]
    if not solids:return m3d.Manifold()
    return m3d.Manifold.batch_boolean(solids,m3d.OpType.Add)

def box(center,size):
    return m3d.Manifold.cube(tuple(size),True).translate(tuple(center))

def cross_section(poly):
    if isinstance(poly,Polygon):
        from shapely.geometry.polygon import orient
        p=orient(poly,1)
        return m3d.CrossSection([np.asarray(p.exterior.coords)[:-1]]+[np.asarray(i.coords)[:-1] for i in p.interiors])
    if isinstance(poly,MultiPolygon):
        result=m3d.CrossSection()
        for p in poly.geoms:result=result+cross_section(p)
        return result
    a=np.asarray(poly,dtype=float)
    if sum(a[i,0]*a[(i+1)%len(a),1]-a[(i+1)%len(a),0]*a[i,1] for i in range(len(a)))<0:a=a[::-1]
    return m3d.CrossSection([a])

def prism(poly,lo,hi,origin=(0,0,0),u=(1,0,0),v=(0,1,0),normal=(0,0,1)):
    solid=cross_section(poly).extrude(hi-lo)
    mat=np.column_stack((u,v,normal));offset=np.asarray(origin)+np.asarray(normal)*lo
    return solid.transform(np.column_stack((mat,offset)))

def frame_rotation(u,v,n):
    mat=np.asarray([u,v,n],dtype=float)
    assert np.linalg.det(mat)>.99,(mat,np.linalg.det(mat))
    return mat

def cylinder_between(a,b,r,segments=32):
    a=np.asarray(a,dtype=float);b=np.asarray(b,dtype=float);d=b-a;length=np.linalg.norm(d);n=d/length
    trial=np.asarray([0,0,1]) if abs(n[2])<.9 else np.asarray([1,0,0])
    u=np.cross(trial,n);u/=np.linalg.norm(u);v=np.cross(n,u)
    return m3d.Manifold.cylinder(length,r,r,segments).transform(np.column_stack((u,v,n,a)))

def spline(points,steps=30):
    p=np.asarray(points,dtype=float);out=[]
    for i in range(len(p)-1):
        a,b,c,d=p[max(i-1,0)],p[i],p[i+1],p[min(i+2,len(p)-1)]
        for j in range(steps):
            t=j/steps;out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    return np.asarray(out+[p[-1]])

@lru_cache(maxsize=1)
def source_route_path():
    return spline([(62,2,40),(22,0,36),(-35,0,42),(-80,15,43),(-92,42,40),(-72,64,33),(-28,63,23),(16,42,3.4)])*F

def sample_path(path,fraction):
    lengths=np.r_[0,np.cumsum(np.linalg.norm(np.diff(path,axis=0),axis=1))]
    d=np.clip(fraction,0,1)*lengths[-1];i=min(len(path)-2,max(0,np.searchsorted(lengths,d,side='right')-1))
    alpha=(d-lengths[i])/(lengths[i+1]-lengths[i]);p=path[i]*(1-alpha)+path[i+1]*alpha
    t=path[min(i+2,len(path)-1)]-path[max(0,i-1)];t[2]=0;t/=np.linalg.norm(t)
    return p,t,np.asarray([-t[1],t[0],0.])

TAIL_SHIFT_MM=6.6
TAIL_SHIFT_START=14/17

def sample_source_route(fraction):return sample_path(source_route_path(),fraction)

def _tail_position(fraction):
    p,t,n=sample_source_route(fraction)
    q=np.clip((fraction-TAIL_SHIFT_START)/(1-TAIL_SHIFT_START),0,1)
    blend=q*q*(3-2*q)
    end_n=sample_source_route(1)[2]
    return p-end_n*(TAIL_SHIFT_MM*blend)

def sample_route(fraction):
    if fraction<=TAIL_SHIFT_START:return sample_source_route(fraction)
    p=_tail_position(fraction)
    t=_tail_position(min(1,fraction+.0005))-_tail_position(max(0,fraction-.0005))
    t[2]=0;t/=np.linalg.norm(t)
    return p,t,np.asarray([-t[1],t[0],0.])

@lru_cache(maxsize=1)
def route_path():return np.asarray([sample_route(float(f))[0] for f in np.linspace(0,1,300)])

def save_debug(parts,path):
    path=Path(path);path.mkdir(parents=True,exist_ok=True)
    report=[]
    for p in parts:
        mesh=to_trimesh(p.solid)
        mesh.export(path/(p.name+'.stl'))
        report.append({'name':p.name,'color':p.color,'volume':mesh.volume,'watertight':mesh.is_watertight,'components':len(p.solid.decompose()),'bounds':mesh.bounds.tolist()})
    (path/'report.json').write_text(json.dumps(report,indent=2))
    return report
