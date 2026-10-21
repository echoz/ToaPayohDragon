"""Engineered body kit: closed hoops, keyed beam modules, and lay-in rails.

Coordinates are final assembly millimetres. Designed as a glue-assembled PLA
prototype; suggested 0.30 mm total clearances require a physical test print.
"""
import math
from functools import lru_cache
import numpy as np
import manifold3d as m3d
from .common import (F,Part,load_source,union,box,prism,from_mesh,to_trimesh,
                     route_path,sample_route,sample_source_route,frame_rotation)

UP=np.array([0.,0.,1.])
COLORS=['cream','blue','sage','sage','red','red','cream','blue','blue',
        'blue','blue','cream','blue','sage','red','cream','blue','blue']
CUTS=[0,4.5/17,9.5/17,13.5/17,1]
RAIL_ANGLES=[35,145,215,325]
BEAM_WIDTH=7.0
BEAM_TOP=-2.15
BEAM_BOTTOM=-6.15
KEY_REAR=-2.6*F+.45
KEY_FRONT=2.30
KEY_WIDTH=4.20
KEY_BOTTOM=-4.75
KEY_TOP=-1.65
KEY_SOCKET_CLEARANCE_TOTAL=.30
KEY_SOCKET_BOTTOM=-4.95
KEY_SHOULDER_Z=-3.00
KEY_SOCKET_MIN_FLOOR=1.20
KEY_ENGAGEMENT=KEY_SHOULDER_Z-KEY_BOTTOM
RAIL_CLEARANCE_PER_SIDE=.20
RAIL_BUTT_GAP=.25
PIER_BEARING_BOTTOM=BEAM_BOTTOM-1.25
PIER_BEARING_HALF_WIDTH=2.60
PIER_BEARING_HALF_LENGTH=1.50
TAIL_OPEN_START=15  # zero-based: stations 16–18 become the open climbing entry
UPPER_RAIL_END=14/17+2.8/np.linalg.norm(np.diff(route_path(),axis=0),axis=1).sum()

def open_tail_rung(solid,p,t,n):
    """Retain the puffy lower oval and add round tips, with a flat print back."""
    end_height=10.8*F
    solid=solid.trim_by_plane((0,0,-1),-float(p[2]+end_height))
    x=9.5*F*math.sqrt(1-((13-10.8)/13)**2)
    cap=m3d.Manifold.sphere(1,28)
    for sign in [-1,1]:
        c=p+n*(sign*x)+UP*end_height
        transform=np.column_stack((n*(2.4*F),UP*(2.4*F),t*(2.6*F),c))
        solid=union(solid,cap.transform(transform))
        # The visible ellipsoid tip stays rounded. A small hidden rear pad
        # reaches the existing printing/key plane so its steep first layers
        # do not grow out into air. The 2.0 mm pad reaches t=-1.8, beyond the
        # ellipsoid's 45 degree tangent and its coarse-facet transition.
        pad=m3d.Manifold.cylinder(-1.8-KEY_REAR,2.0,2.0,56)
        pad=pad.transform(np.column_stack((n,UP,t,c+t*KEY_REAR)))
        solid=union(solid,pad)
    return solid ^ local_box(p,n,UP,t,[-80,-30,KEY_REAR],[80,80,30])


def local_box(p,u,v,w,lo,hi):
    lo,hi=np.array(lo,float),np.array(hi,float)
    return box((lo+hi)/2,hi-lo).transform(np.column_stack((u,v,w,np.asarray(p))))


def sweep(points,frames,cross):
    """Closed polygon sweep with consistently triangulated rectangular caps."""
    verts=[]
    for p,(u,v) in zip(points,frames):
        verts.extend(p+x*u+y*v for x,y in cross)
    n=len(cross);faces=[]
    for i in range(len(points)-1):
        for j in range(n):
            a=i*n+j;b=i*n+(j+1)%n;c=(i+1)*n+(j+1)%n;d=(i+1)*n+j
            faces.extend([(a,b,c),(a,c,d)])
    # Cross-sections here are convex.
    for j in range(1,n-1):
        faces.extend([(0,j+1,j),((len(points)-1)*n,(len(points)-1)*n+j,(len(points)-1)*n+j+1)])
    return from_mesh(verts,faces)


def beam_segment(f0,f1):
    # Stop before the low final hoop: a separate ground landing supports it,
    # avoiding an unprintable sub-millimetre feather edge beneath its saddle.
    if f1==1:
        length=np.linalg.norm(np.diff(route_path(),axis=0),axis=1).sum()
        f1=1-5.0/length
    fs=np.linspace(f0,f1,max(12,int((f1-f0)*280)))
    points=[];frames=[]
    for f in fs:
        p,t,n=sample_route(f);points.append(p);frames.append((n,UP))
    solid=sweep(points,frames,[(-3.5,BEAM_BOTTOM),(3.5,BEAM_BOTTOM),(3.5,BEAM_TOP),(-3.5,BEAM_TOP)])
    return solid ^ box((0,0,100.1),(1000,1000,200))


def hoop_envelope(p,t,n,margin=.15):
    """Saddle relief with radial and axial assembly clearance."""
    vs=[];fs=[];ns=72;nt=20
    for j in range(ns):
        a=2*math.pi*j/ns
        centre=p+n*(9.5*F*math.cos(a))+UP*(13*F*(1+math.sin(a)))
        r=n*(math.cos(a)/(9.5*F))+UP*(math.sin(a)/(13*F));r/=np.linalg.norm(r)
        for k in range(nt):
            b=2*math.pi*k/nt
            vs.append(centre+r*(2.4*F+margin)*math.cos(b)+t*(2.6*F+margin)*math.sin(b))
    for j in range(ns):
        for k in range(nt):
            a=j*nt+k;b=j*nt+(k+1)%nt;c=((j+1)%ns)*nt+(k+1)%nt;d=((j+1)%ns)*nt+k
            fs.extend([(a,b,c),(a,c,d)])
    return from_mesh(vs,fs)


def rail_location(f,degrees):
    p,t,n=sample_route(f);theta=math.radians(degrees)
    radial=n*(math.cos(theta)/(9.5*F))+UP*(math.sin(theta)/(13*F))
    radial/=np.linalg.norm(radial)
    centre=p+n*(9.5*F*math.cos(theta))+UP*(13*F*(1+math.sin(theta)))
    return centre+1.45*radial,t,radial


def rail_segment(f0,f1,degrees,radius=1.1):
    fs=np.linspace(f0,f1,max(14,int((f1-f0)*300)))
    points=np.asarray([rail_location(f,degrees)[0] for f in fs]);frames=[]
    last=None
    for i,p in enumerate(points):
        tangent=points[min(i+1,len(points)-1)]-points[max(i-1,0)];tangent/=np.linalg.norm(tangent)
        if last is None:
            a=np.cross(tangent,UP);a/=np.linalg.norm(a)
        else:
            a=last-tangent*np.dot(last,tangent);a/=np.linalg.norm(a)
        b=np.cross(tangent,a);frames.append((a,b));last=a
    solid=sweep(points,frames,[(radius*math.cos(a),radius*math.sin(a)) for a in np.linspace(0,2*math.pi,20,endpoint=False)])
    # Neighbouring sampled sections otherwise obtain slightly different end
    # normals. Trim both against one shared tangent plane, with 0.25 mm gap,
    # so curved butt ends cannot overlap or trap a thin sliver at assembly.
    for f,is_start in [(f0,True),(f1,False)]:
        if f<=0 or f>=1:continue
        q=rail_location(f,degrees)[0]
        direction=rail_location(f+.001,degrees)[0]-rail_location(f-.001,degrees)[0]
        direction/=np.linalg.norm(direction)
        normal=direction if is_start else -direction
        plane=q+normal*(RAIL_BUTT_GAP/2)
        solid=solid.trim_by_plane(tuple(normal),float(np.dot(normal,plane)))
    return solid


def rail_install_direction(f0,f1,degrees):
    """One straight outward fitting direction shared by the entire rail piece."""
    f=(f0+f1)/2
    _,_,radial=rail_location(f,degrees)
    tangent=rail_location(f+.001,degrees)[0]-rail_location(f-.001,degrees)[0]
    tangent/=np.linalg.norm(tangent)
    side=np.cross(tangent,radial);side/=np.linalg.norm(side)
    direction=np.cross(side,tangent)
    if abs(f0-CUTS[2])<1e-8 and degrees==215:
        a=math.radians(15)
        direction[:2]=np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])@direction[:2]
    elif abs(f0-CUTS[2])<1e-8 and degrees==35:
        direction[2]*=.8
    return direction/np.linalg.norm(direction)


@lru_cache(maxsize=32)
def rail_install_envelope(f0,f1,degrees):
    # The expanded rail uses precisely the same sampled centreline and frames
    # as the delivered rail. The polygon correction plus 5 microns protects
    # the requested normal gap between corresponding polygon faces.
    radius=1.1+RAIL_CLEARANCE_PER_SIDE/math.cos(math.pi/20)+.005
    rail=rail_segment(f0,f1,degrees,radius)
    direction=rail_install_direction(f0,f1,degrees)
    a=np.cross(direction,UP)
    if np.linalg.norm(a)<1e-8:a=np.array([1.,0.,0.])
    a/=np.linalg.norm(a);b=np.cross(direction,a)
    # Minkowski sum with a narrow prism is a continuous outward sweep. Its
    # 2 micron transverse footprint only increases the clearance.
    extrusion=m3d.Manifold.cube((.002,.002,7.0)).translate((-.001,-.001,0))
    extrusion=extrusion.transform(np.column_stack((a,b,direction,np.zeros(3))))
    return rail.minkowski_sum(extrusion)


def printable_slot(envelope,p,t,n):
    # Keep the envelope local to this hoop, then project it through the flat
    # printing thickness. This retains the curved-rail fitting allowance while
    # making the groove an open, constant section through the printed layers.
    lo=KEY_REAR-.20;hi=2.6*F+.20
    window=local_box(p,n,UP,t,[-80,-30,KEY_REAR-.01],[80,80,2.6*F+.01])
    local=envelope^window
    if local.is_empty():return local
    rotation=np.asarray([n,UP,t])
    local=local.transform(np.column_stack((rotation,-rotation@p)))
    section=m3d.CrossSection(local.project().to_polygons(),m3d.FillRule.Positive)
    # Projection of many coplanar sweep faces can leave zero-width contour
    # contacts. A 10 micron expansion joins them before STL float32 welding;
    # it increases the intended assembly clearance rather than reducing it.
    section=section.offset(.01,m3d.JoinType.Miter).simplify(.002)
    slot=section.extrude(hi-lo).translate((0,0,lo))
    return slot.transform(np.column_stack((n,UP,t,p)))


def beam_print_rotation(f0,f1):
    a=sample_route(f0)[0];b=sample_route(f1)[0]
    x=b-a;x[2]=0;x/=np.linalg.norm(x);y=np.cross(UP,x)
    return frame_rotation(x,y,UP)


def build():
    parts=[];beams=[beam_segment(a,b) for a,b in zip(CUTS,CUTS[1:])]
    rail_envelopes={}
    for degrees in RAIL_ANGLES:
        for j,(f0,f1) in enumerate(zip(CUTS,CUTS[1:])):
            if degrees in [35,145]:f1=min(f1,UPPER_RAIL_END)
            rail_envelopes[degrees,j]=rail_install_envelope(f0,f1,degrees)
    # Tongues project in assembly direction into open butt sockets.
    joint_info=[]
    for j,f in enumerate(CUTS[1:-1]):
        p,t,n=sample_route(f)
        # Use true centreline slope for the peg so descending sections meet.
        pa=sample_route(f-.002)[0];pb=sample_route(f+.002)[0]
        direction=pb-pa;direction/=np.linalg.norm(direction)
        lateral=np.cross(UP,direction);lateral/=np.linalg.norm(lateral)
        vertical=np.cross(direction,lateral)
        centre=p+UP*(-4.15)
        tongue=local_box(centre,direction,lateral,vertical,[-.6,-1.6,-.85],[4.8,1.6,.85])
        socket=local_box(centre,direction,lateral,vertical,[-.3,-1.75,-1.0],[5.05,1.75,1.0])
        beams[j]=union(beams[j],tongue)
        beams[j+1]=beams[j+1]-socket
        joint_info.append({'fraction':f,'tongue_width_mm':3.2,'tongue_height_mm':1.7,'tongue_projection_mm':4.8,'clearance_total_mm':.30})
    hoop_info=[]
    for i,color in enumerate(COLORS):
        f=i/17;p,t,n=sample_route(f)
        solid=load_source(f'BODY_Rib_{i+1:02}')
        if i>=TAIL_OPEN_START:
            oldp,oldt,oldn=sample_source_route(f)
            rotation=np.column_stack((n,UP,t))@np.column_stack((oldn,UP,oldt)).T
            solid=solid.transform(np.column_stack((rotation,p-rotation@oldp)))
        # A broad rear contact face also includes the key, so the whole outline
        # starts on the build plate when laid flat.
        clip=local_box(p,n,UP,t,[-80,-30,KEY_REAR],[80,80,30])
        solid=solid ^ clip
        if i>=TAIL_OPEN_START:solid=open_tail_rung(solid,p,t,n)
        beam_i=int(min(len(beams)-1,np.searchsorted(CUTS,f,side='right')-1))
        for degrees in RAIL_ANGLES:
            if i>=TAIL_OPEN_START and degrees in [35,145]:continue
            solid=solid-printable_slot(rail_envelopes[degrees,beam_i],p,t,n)
        if i<17:
            key=local_box(p,n,UP,t,[-KEY_WIDTH/2,KEY_BOTTOM,KEY_REAR],[KEY_WIDTH/2,KEY_TOP,KEY_FRONT])
            solid=union(solid,key)
            for sign in [-1,1]:
                a,b=sorted((sign*2.4,sign*3.4))
                shoulder=local_box(p,n,UP,t,[a,KEY_SHOULDER_Z,KEY_REAR],[b,-.75,KEY_FRONT])
                solid=union(solid,shoulder)
            # Local reinforcement ensures a real 1.20 mm socket floor even
            # where the route slope would otherwise cut through the beam.
            reinforcement=local_box(p,n,UP,t,[-3.5,KEY_SOCKET_BOTTOM-KEY_SOCKET_MIN_FLOOR,KEY_REAR-.40],
                                    [3.5,KEY_SHOULDER_Z,KEY_FRONT+.40])
            beams[beam_i]=union(beams[beam_i],reinforcement)
            socket=local_box(p,n,UP,t,[-KEY_WIDTH/2-.15,KEY_SOCKET_BOTTOM,KEY_REAR-.15],
                             [KEY_WIDTH/2+.15,KEY_TOP+.20,KEY_FRONT+.15])
            beams[beam_i]=beams[beam_i]-socket
        else:
            # Last hoop bottoms near the plinth; no downward key is possible.
            sole=local_box(p,n,UP,t,[-4.0,.70-p[2],KEY_REAR],[4.0,2.70-p[2],KEY_FRONT])
            solid=union(solid,sole)
        # A flat-bottom clearance saddle avoids knife-edge contacts where the
        # round hoop would only graze the narrow beam side.
        relief=local_box(p,n,UP,t,[-4.0,KEY_SHOULDER_Z,KEY_REAR-.20],[4.0,6.0,2.6*F+.20])
        beams[beam_i]=beams[beam_i]-relief
        notes=(f'{"Open U-rung" if i>=TAIL_OPEN_START else "Closed hoop"} {i+1:02} in head-to-tail order. Flat rear face is the build-plate face. '
               +('Two lower outside-open seats receive the blue rails; rounded tips leave the entrance open above. ' if i>=TAIL_OPEN_START else 'Four outside-open seats receive the 2.2 mm blue rails. ')
               +('Seat both shoulder pads on the beam ledges; the wider key retains 0.30 mm total insertion clearance and 0.20 mm bottom relief.' if i<17 else 'No downward key: glue the integrated flat sole to the tail landing.'))
        parts.append(Part(f'body_hoop_{i+1:02}',color,solid,frame_rotation(n,UP,t),notes,'none',{'hoop':i+1,'fraction':f,'key':i<17,'shape':'open_U' if i>=TAIL_OPEN_START else 'closed_oval'}))
        hoop_info.append({'number':i+1,'color':color,'fraction':f,'key':i<17,'beam':beam_i+1,'rear_flat_mm':.45,'shape':'open_U' if i>=TAIL_OPEN_START else 'closed_oval',
                          'shoulder_bearing_z_mm':float(p[2]+KEY_SHOULDER_Z) if i<17 else None})
    for f in [2/17,5/17,8/17,12/17,15/17]:
        p,t,n=sample_route(f);j=int(min(3,np.searchsorted(CUTS,f,side='right')-1))
        landing=local_box(p,n,UP,t,[-PIER_BEARING_HALF_WIDTH,PIER_BEARING_BOTTOM,-PIER_BEARING_HALF_LENGTH],
                          [PIER_BEARING_HALF_WIDTH,BEAM_BOTTOM+1.2,PIER_BEARING_HALF_LENGTH])
        beams[j]=union(beams[j],landing)
    for i,solid in enumerate(beams):
        parts.append(Part(f'body_beam_{i+1:02}','blue',solid,beam_print_rotation(CUTS[i],CUTS[i+1]),
            f'Beam module {i+1}, head to tail. Seat hoops before fitting rails; dry-fit all beam butt tongues before glue. Preserve all top key sockets.',
            'Required: use removable supports beneath curved beam; keep socket interiors clear.',{'module':i+1,'fraction_start':CUTS[i],'fraction_end':CUTS[i+1]}))
    for r,degrees in enumerate(RAIL_ANGLES):
        for j,(f0,f1) in enumerate(zip(CUTS,CUTS[1:])):
            if r<2:f1=min(f1,UPPER_RAIL_END)
            solid=rail_segment(f0,f1,degrees)
            rotation=beam_print_rotation(f0,f1)
            support='Required: slim curved rail needs removable supports and a brim; handle gently until glued.'
            if r<2 and j==3:
                x=rail_location(f1,degrees)[0]-rail_location(f0,degrees)[0];x/=np.linalg.norm(x)
                y=np.cross(UP,x);y/=np.linalg.norm(y);z=np.cross(x,y)
                rotation=frame_rotation(x,y,z)
                bottom=float((to_trimesh(solid).vertices@z).min())
                solid=solid.trim_by_plane(tuple(z),bottom+.60)
                support='none'
            parts.append(Part(f'body_rail_{r+1:02}_section_{j+1:02}','blue',solid,rotation,
                f'Rail track {r+1} at {degrees} degrees; section {j+1}, head to tail. 2.2 mm diameter. Lay into open hoop grooves and glue. '+('Upper tracks stop just beyond closed hoop15, before the open tail entry. ' if r<2 and j==3 else '')+'Butt ends join at beam seams; do not try to thread through hoops.',
                support,{'track':r+1,'section':j+1,'diameter_mm':2.2,'flat_back_mm':.60 if r<2 and j==3 else 0.0,
                         'installation_direction':rail_install_direction(f0,f1,degrees).tolist(),'butt_gap_mm':RAIL_BUTT_GAP}))
    seats=[]
    for f in [2/17,5/17,8/17,12/17,15/17]:
        p,t,n=sample_route(f)
        seats.append({'fraction':f,'p':p.tolist(),'t':t.tolist(),'n':n.tolist(),'floor_z':float(p[2]+PIER_BEARING_BOTTOM),'beam_width':BEAM_WIDTH,'trough_width':7.30,'shoulder_height':1.5,
                      'bearing_floor_offset_mm':PIER_BEARING_BOTTOM,'bearing_footprint_mm':[2*PIER_BEARING_HALF_WIDTH,2*PIER_BEARING_HALF_LENGTH]})
    p,t,n=sample_route(1)
    info={'hoops':hoop_info,'beam_joints':joint_info,'pier_seats':seats,'rail_diameter_mm':2.2,
          'rail_groove_minimum_clearance_per_side_mm':RAIL_CLEARANCE_PER_SIDE,'rail_groove_method':'expanded actual sampled rail envelope, continuously swept outward, projected through hoop print thickness',
          'rail_butt_gap_mm':RAIL_BUTT_GAP,'rail_segments':16,'beam_segments':4,'hoop_count':18,'closed_hoop_count':15,'open_tail_rungs':3,'upper_rail_end_fraction':UPPER_RAIL_END,'clearance_total_mm':.30,
          'hoop_key':{'width_mm':KEY_WIDTH,'axial_length_mm':KEY_FRONT-KEY_REAR,'rear_mm':KEY_REAR,'front_mm':KEY_FRONT,'bottom_offset_mm':KEY_BOTTOM,
                      'socket_bottom_offset_mm':KEY_SOCKET_BOTTOM,'bottom_relief_mm':KEY_BOTTOM-KEY_SOCKET_BOTTOM,'shoulder_plane_offset_mm':KEY_SHOULDER_Z,
                      'engagement_mm':KEY_ENGAGEMENT,'socket_minimum_floor_mm':KEY_SOCKET_MIN_FLOOR,'shoulder_pads_n_ranges_mm':[[-3.4,-2.4],[2.4,3.4]],
                      'total_insertion_clearance_mm':KEY_SOCKET_CLEARANCE_TOTAL},
          'tail_seat':{'centre':p.tolist(),'t':t.tolist(),'n':n.tolist(),'hoop_lowest_z_mm':.70,
                       'beam_stops_before_last_hoop_mm':5.0,'required_landing_top_z_mm':.70,'landing_width_across_n_mm':8.0,'landing_depth_along_t_mm':6.0},
          'assembly':'Dry-fit beam modules, then glue beam to pier saddles. Place keyed hoops in numbered seats. Lay in each outside-open rail track; glue ends at module boundaries.',
          'limitations':'Glue assembly; print supports needed for beam and rails. Thin rails are non-load-bearing and must be handled carefully. Fit clearance has not been physically calibrated.'}
    return parts,info

if __name__=='__main__':
    from .common import save_debug,ROOT
    parts,info=build()
    import json
    p=ROOT/'exports/dragon-pla-kit/work/body-debug'
    report=save_debug(parts,p)
    (p/'body-info.json').write_text(json.dumps(info,indent=2))
    print(json.dumps(report,indent=2))
