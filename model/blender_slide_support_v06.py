"""Photo-guided slide cheek walls. Coordinates are inferred, in source millimetres.

The v06 channel raises the toe by 2.7 mm and its cheeks widen outward by 0.4 mm.
Profiles use horizontal arclength, with an actual vertical riser at 35 percent.
A subdivided parametric solid follows each slide's curved plan without long,
nonplanar cap polygons. This remains visual-prototype geometry.
"""
import bpy
import bmesh
import math
import json
from bisect import bisect_right
from mathutils import Vector

GROUND_START=.35
BORDER=1.35
INNER=4.35  # small overlap into the channel keeps the assemblies connected
OUTER=6.75

def area(poly):
    return sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1]))/2

def inset(poly,amount):
    """Intersect parallel edge offsets, preserving the stepped cream margin."""
    if area(poly)<0:poly=list(reversed(poly))
    out=[]
    for i,p in enumerate(poly):
        before=Vector(poly[i-1]); here=Vector(p); after=Vector(poly[(i+1)%len(poly)])
        a=(here-before).normalized(); b=(after-here).normalized()
        n1=Vector((-a.y,a.x)); n2=Vector((-b.y,b.x))
        denom=1+a.dot(b)
        shift=(n1+n2)*(amount/max(denom,.02))
        out.append(tuple(here+shift))
    return out

def build_slide_walls(number,line,mats,collection,mesh_obj):
    distances=[0.]
    for p,q in zip(line,line[1:]):
        distances.append(distances[-1]+math.hypot(q.x-p.x,q.y-p.y))
    length=distances[-1]
    def frame(s):
        s=max(0,min(length,s)); i=min(len(line)-2,max(0,bisect_right(distances,s)-1))
        f=(s-distances[i])/(distances[i+1]-distances[i])
        p=line[i].lerp(line[i+1],f)
        # Interpolate vertex tangents for a continuous normal along the curve.
        def tangent(j):
            t=line[min(j+1,len(line)-1)]-line[max(0,j-1)];t.z=0
            return t.normalized()
        t=tangent(i).lerp(tangent(i+1),f).normalized()
        return p,Vector((-t.y,t.x,0))
    # Head → toe along top, then toe → head along ground and cutout.
    samples=max(28,math.ceil(length/2))
    top=[(length*i/samples,frame(length*i/samples)[0].z+3.5) for i in range(samples+1)]
    bottom=[(length,0),(length*.35,0),(length*.35,10),
            (length*.30,13),(length*.22,13),(0,31)]
    profile=top+bottom
    if area(profile)<0:profile.reverse()
    patch=inset(profile,BORDER)

    def solid(name,poly,lo,hi,material,bevel):
        # Planar construction ensures shared vertices at the exact vertical step.
        count=len(poly)
        verts=[(s,d,z) for d in [lo,hi] for s,z in poly]
        faces=[tuple(range(count-1,-1,-1)),tuple(range(count,2*count))]
        faces += [(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
        obj=mesh_obj(name,verts,faces,material,collection)
        bm=bmesh.new();bm.from_mesh(obj.data)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        # Bevel before dense subdivision so short mesh edges don't clamp it away.
        edges=[e for e in bm.edges if e.is_manifold and e.calc_face_angle()>.35]
        bmesh.ops.bevel(bm,geom=edges,offset=bevel,segments=3,affect='EDGES',clamp_overlap=True)
        bmesh.ops.triangulate(bm,faces=list(bm.faces))
        bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=5,use_grid_fill=True)
        for v in bm.verts:
            s,d,z=v.co
            p,n=frame(s)
            v.co=p+n*d;v.co.z=z
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bm.to_mesh(obj.data);bm.free();obj.data.update()
        return obj

    result=[]
    for sign in [-1,1]:
        lo,hi=sorted((sign*INNER,sign*OUTER))
        wall=solid(f'SLIDE_{number}_wall_{sign}',profile,lo,hi,mats['cream'],.40)
        wall['slide_support_profile']='broad grounded wall with upper stepped cutout'
        wall['grounded_fraction']=1-GROUND_START
        wall['profile_sz_mm']=json.dumps(profile)
        lo,hi=sorted((sign*(OUTER-.025),sign*(OUTER+.18)))
        panel=solid(f'SLIDE_{number}_orange_{sign}',patch,lo,hi,mats['orange'],.06)
        result.extend([wall,panel])
    return result
