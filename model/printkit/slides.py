"""Print-kit slide solids derived from approved v06, in final millimetres.

The orange pieces are 1.2 mm solid curved inlays seated in real cream pockets;
these replace the visual model's approximately 0.22 mm colour skins.
"""
from bisect import bisect_right
import math
import numpy as np
import manifold3d as m3d
from shapely.geometry import Polygon
from .common import (F, Part, from_mesh, load_source, union, prism, box,
                     to_trimesh, frame_rotation, spline, cross_section)

INLAY_THICKNESS = 1.20
INLAY_CLEARANCE = .20
PEG_CLEARANCE = .15
SLIDE_PATHS = [
    [(62,-23,40),(52,-27,38),(9,-43,4),(-8,-47,1.8)],
    [(62,21,40),(55,28,38),(24,63,9),(6,88,1.8)],
]


def _path(number):
    line=spline(SLIDE_PATHS[number-1],24)*F
    line[:,2]=np.maximum(line[:,2],1.8*F)
    distances=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(line[:,:2],axis=0),axis=1))]
    t=np.clip((distances/distances[-1]-.45)/.55,0,1)
    line[:,2]+=2.7*F*t*t*(3-2*t)
    tangents=[]
    for j in range(len(line)):
        tangent=line[min(j+1,len(line)-1)]-line[max(0,j-1)]
        tangent[2]=0; tangent/=np.linalg.norm(tangent)
        tangents.append(tangent)
    tangents=np.asarray(tangents)

    def frame(s):
        s=np.clip(s,0,distances[-1]); i=min(len(line)-2,max(0,bisect_right(distances,s)-1))
        alpha=(s-distances[i])/(distances[i+1]-distances[i])
        p=line[i]*(1-alpha)+line[i+1]*alpha
        tangent=tangents[i]*(1-alpha)+tangents[i+1]*alpha
        tangent/=np.linalg.norm(tangent)
        normal=np.array([-tangent[1],tangent[0],0.])
        return p,tangent,normal
    return line,distances[-1],frame


def _profile(length,frame):
    samples=max(28,math.ceil(length/F/2))
    top=[(length*i/samples,frame(length*i/samples)[0][2]+3.5*F) for i in range(samples+1)]
    bottom=[(length,0),(length*.35,0),(length*.35,10*F),
            (length*.30,13*F),(length*.22,13*F),(0,31*F)]
    return top+bottom


def _curved_profile(poly,lo,hi,frame):
    # (s,-z,d) -> world has positive Jacobian. Refine before bending to follow
    # the approved plan curve with submillimetre chord accuracy.
    if isinstance(poly,m3d.CrossSection):
        profile=poly.mirror((0,1))
    else:
        profile=cross_section([(s,-z) for s,z in poly])
    block=profile.extrude(hi-lo).translate((0,0,lo)).refine_to_length(1.20)
    def bend(vertex):
        s,minus_z,d=vertex
        p,t,n=frame(s)
        q=p+n*d; q[2]=-minus_z
        return q
    return block.warp(bend)


def _oriented_box(center,size,t,n):
    return box((0,0,0),size).transform(np.column_stack((t,n,[0,0,1],center)))


def _single_main(solid,name,removed):
    components=sorted(solid.decompose(),key=lambda item:item.volume(),reverse=True)
    if len(components)>1:
        offcut=sum(item.volume() for item in components[1:])
        if offcut>1.0: raise ValueError(f'{name}: unexpectedly detached {offcut:.3f} mm3 after head trim')
        removed[name]=offcut
    return components[0]


def _trim_entrance(solid,obstacles,name,removed,trims):
    if obstacles is None:
        return solid
    contact=solid^obstacles
    if contact.is_empty() or contact.volume()<1e-7:
        return solid
    # Offset only the contact neighbourhood, keeping clipped cutter boundaries
    # 0.5 mm outside the contact so they cannot create artificial relief edges.
    bounds=np.asarray(contact.bounding_box())
    window=box((bounds[:3]+bounds[3:])/2,bounds[3:]-bounds[:3]+1.0)
    local=obstacles^window
    cutter=local.minkowski_sum(box((0,0,0),(.24,.24,.24)))
    result=_single_main(solid-cutter,name,removed)
    trims[name]={'collision_before_mm3':contact.volume(),
                 'relief_removed_mm3':solid.volume()-result.volume(),
                 'axis_clearance_mm':.12}
    return result


def build(head_obstacles=None,entrance_obstacles=None):
    head_clearance=None if head_obstacles is None else union(head_obstacles,head_obstacles.translate((-.10,0,0)))
    parts=[]; removed={}; trims={}; info={'removed_interface_offcuts_mm3':removed,'entrance_reliefs':trims,'base_socket_cutters':[], 'sand_clearance_cutters':[], 'slide_keys':[], 'interfaces':[],
                    'head_clearance_in_approach_direction_mm':.10 if head_clearance is not None else None,
                    'inlay_thickness_mm':INLAY_THICKNESS,
                    'inlay_clearance_per_side_mm':INLAY_CLEARANCE,
                    'minimum_nominal_cream_web_mm':(6.93-4.35)*F-INLAY_THICKNESS-INLAY_CLEARANCE}
    for number in (1,2):
        line,length,frame=_path(number)
        profile=cross_section(Polygon(_profile(length,frame)))
        patch=profile.offset(-1.35*F,m3d.JoinType.Miter,2)
        expanded_patch=patch.offset(INLAY_CLEARANCE,m3d.JoinType.Miter,2)
        cream=union(load_source(f'SLIDE_{number}_channel'),
                    load_source(f'SLIDE_{number}_wall_-1'),
                    load_source(f'SLIDE_{number}_wall_1'))
        if len(cream.decompose())!=1:
            raise ValueError(f'Slide {number}: source channel and cheeks do not connect')
        fitted_inserts=[]
        for sign in (-1,1):
            outer=6.93*F
            inner=outer-INLAY_THICKNESS
            lo,hi=sorted((sign*inner,sign*outer))
            orange=_curved_profile(patch,lo,hi,frame)
            if head_clearance is not None: orange=_single_main(orange-head_clearance,f'slide_{number}_orange_{sign}',removed)
            orange=_trim_entrance(orange,entrance_obstacles,f'slide_{number}_orange_{sign}',removed,trims)
            fitted_inserts.append(orange)
            clo,chi=sorted((sign*(inner-INLAY_CLEARANCE),sign*(outer+.50)))
            pocket=_curved_profile(expanded_patch,clo,chi,frame)
            # Clear the whole rigid insert's straight approach, not just its
            # seated outline. Minkowski addition with a narrow directional
            # prism is a continuous swept envelope with 0.20 mm edge reserve.
            p,t,n=frame(length*.55)
            direction=n*sign
            sweep_kernel=box((0,0,0),(.40,.40,3.40)).transform(np.column_stack((t,np.array([0.,0.,1.]),direction,direction*1.50)))
            pocket=union(pocket,orange.minkowski_sum(sweep_kernel))
            cream=cream-pocket
            # Three small lands preserve the intended visible face level.
            for fraction in [.30,.60,.86]:
                q,qt,qn=frame(length*fraction)
                z=max(3.0, q[2]-2.5*F)
                land_profile=patch ^ cross_section([(length*fraction-1,z-1),(length*fraction+1,z-1),(length*fraction+1,z+1),(length*fraction-1,z+1)])
                if land_profile.is_empty():continue
                a,b=sorted((sign*(inner-.30),sign*inner))
                cream=union(cream,_curved_profile(land_profile,a,b,frame))
            orientation=frame_rotation(t,-sign*np.array([0.,0.,1.]),sign*n)
            side='left' if sign<0 else 'right'
            parts.append(Part(f'slide_{number}_orange_{side}','orange',orange,orientation,
                notes='1.2 mm curved orange inlay. Approach along the outward normal at its midpoint, then seat on the small bearing lands. 0.20 mm clearance envelope; apply glue in recessed areas. Support marks belong on hidden curved back.',
                supports='Build plate supports under curved hidden back; 3 mm brim recommended.',
                tags={'module':'slides','inlay_thickness_mm':1.2,'sign':sign}))

        # Share the actual insert facets at the seating lands. Independently
        # refined curved profiles otherwise leave submillimetre contact chips.
        cream=cream-union(*fitted_inserts)
        # A single broad removable key beneath the thick toe lets the slide
        # rest flat on the print bed; narrow sidewall pegs would be fragile.
        p,t,n=frame(length*.95)
        center=p.copy(); center[2]=-1.10
        size=np.array([4.0,6.0,6.20])
        peg=_oriented_box(center,size,t,n)
        cavity=_oriented_box(center,[4.40,6.40,6.60],t,n)
        cream=cream-cavity
        cutter=_oriented_box([center[0],center[1],-2.125],[4.40,6.40,4.65],t,n)
        info['base_socket_cutters'].append(cutter)
        info['sand_clearance_cutters'].append(_oriented_box([center[0],center[1],-1.],[5.2,7.2,2.4],t,n))
        info['slide_keys'].append({'name':f'slide_{number}_peg',
                                   'center_mm':center.tolist(),'tangent':t.tolist(),
                                   'size_mm':size.tolist(),'slide':number,'tray_engagement_mm':2.20,'sand_clearance_per_side_mm':.60})
        parts.append(Part(f'slide_{number}_peg','cream',peg,np.eye(3),
            notes='Broad loose toe key: 2 mm into slide and 4.2 mm below ground, including 2.2 mm into the structural tray. The wider sand passage does not locate it. Slide ground faces establish its final height; dry-fit before gluing.',
            supports='none',tags={'module':'slides','kind':'locating peg'}))

        if head_clearance is not None: cream=_single_main(cream-head_clearance,f'slide_{number}_cream',removed)
        cream=_trim_entrance(cream,entrance_obstacles,f'slide_{number}_cream',removed,trims)
        parts.append(Part(f'slide_{number}_cream','cream',cream,np.eye(3),
            notes='Approved broad v06 walls and thick toe. Both cheeks and chute are fused as one solid. Keep ground faces flat; glue orange inlays after removing supports.',
            supports='Build plate supports under raised head-end cutout/chute; support interface on hidden underside. 3 mm brim.',
            tags={'module':'slides','kind':'structural slide'}))
        start,t,n=frame(0)
        info['interfaces'].append({'slide':number,'head_origin_mm':start.tolist(),
                                  'tangent':t.tolist(),'normal':n.tolist(),
                                  'nominal_channel_width_mm':9*F})
    info['metadata']={key:value for key,value in info.items() if not key.endswith('_cutters')}
    return parts,info


if __name__=='__main__':
    from .common import save_debug,ROOT
    from .head import build as build_head
    head_parts,_=build_head()
    parts,info=build(union(*[part.solid for part in head_parts]))
    report=save_debug(parts,ROOT/'exports/dragon-pla-kit/work/slides-debug')
    for item in report: print(item['name'],item['watertight'],item['components'],round(item['volume'],2))
    print('minimum nominal cream web',info['minimum_nominal_cream_web_mm'])
