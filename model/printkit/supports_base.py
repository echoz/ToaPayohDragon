"""Five keyed piers and a two-piece tray with separate sand-colour inserts."""
import numpy as np
from shapely.geometry import Polygon,MultiPoint,box as rect
from .common import *
UP=np.array([0.,0.,1.])

def rounded(poly,r=.35):
    return Polygon(poly).buffer(-r,join_style=1).buffer(r,join_style=1,quad_segs=4)

def build_piers(beam_obstacles=None):
    parts=[];sockets=[];sand_sockets=[];record=[]
    for i,f in enumerate([2/17,5/17,8/17,12/17,15/17],1):
        p,t,n=sample_route(f);origin=np.array([p[0],p[1],0.])
        floor=p[2]-6.15;h=floor+1.5;half=2.1*F
        profile=rounded([(-11*F,0),(11*F,0),(7*F,h),(-7*F,h)])
        cream=prism(profile,-half,half,origin,n,UP,t)
        trough=prism(rect(-3.65,floor,3.65,h+2),-half-1,half+1,origin,n,UP,t)
        cream=cream-trough
        # A whole key belongs to the front lamination, avoiding a split pin.
        keypoly=Polygon([(-2.6,-4.2),(2.6,-4.2),(3.,-3.8),(3.,.8),(-3.,.8),(-3.,-3.8)])
        # Attach the whole key only after separating the front lamination.
        # Splitting a key whose rear is exactly on t=0 leaves zero-volume key
        # remnants on the back half, which fail the STL one-solid check.
        foot_key=prism(keypoly,0.,2.0,origin,n,UP,t)
        sockets.append(prism(rect(-3.20,-4.45,3.20,.3),-.20,2.20,origin,n,UP,t))
        sand_sockets.append(prism(rect(-3.6,-2.2,3.6,.3),-.60,2.60,origin,n,UP,t))
        patch=Polygon([(-9.1*F,1.2),(9.1*F,1.2),(5.7*F,floor-1.0),(-5.7*F,floor-1.0)])
        # Keep colour skins clear of the central beam landing and cream pad.
        # The shallow top-centre notch is hidden beneath the seated beam.
        patch=patch.difference(rect(-3.1,p[2]-8.40,3.1,h+2))
        pocket=patch.buffer(.15,join_style=2)
        inserts=[]
        color='orange' if i in [1,4] else 'blue'
        for side in [-1,1]:
            lo,hi=sorted([side*(half-1.40),side*(half+.1)])
            cream=cream-prism(pocket,lo,hi,origin,n,UP,t)
            for px,pz in [(-4.,4.),(4.,4.),(0.,floor-5.)]:
                land=rect(px-.8,pz-.8,px+.8,pz+.8).intersection(patch.buffer(-.3))
                lo,hi=sorted([side*(half-1.45),side*(half-1.2)])
                cream=union(cream,prism(land,lo,hi,origin,n,UP,t))
            lo,hi=sorted([side*(half-1.2),side*half])
            insert=prism(patch,lo,hi,origin,n,UP,t)
            # Both colour inserts print flat on their hidden back faces.
            r=frame_rotation(n,UP,t) if side==1 else frame_rotation(-n,UP,-t)
            inserts.append(Part(f'pier_{i:02}_{"front" if side==1 else "back"}_inlay',color,insert,r,'1.2 mm inlay; 0.15 mm clearance each side. Glue into matching pier.'))
        if beam_obstacles is not None:
            # A zero-clearance cut at the exact saddle floor creates pinched
            # coplanar triangles at the laminate split, which collapse in STL.
            # Offset the local real beam by 0.10 mm before cutting the seat.
            bounds=np.asarray(cream.bounding_box())
            window=box((bounds[:3]+bounds[3:])/2,bounds[3:]-bounds[:3]+1.0)
            local_beam=beam_obstacles^window
            # The world AABB is much wider along the route on diagonal piers.
            # Exclude distant beam geometry before projecting; otherwise a
            # lower neighbouring segment can cut away the bearing's support.
            centre_t=float(np.dot(origin,t))
            local_beam=local_beam.trim_by_plane(tuple(t),centre_t-half-.40)
            local_beam=local_beam.trim_by_plane(tuple(-t),-centre_t-half-.40)
            if not local_beam.is_empty():
                relief=local_beam.minkowski_sum(box((0,0,0),(.40,.40,.40)))
                # Carry the curved/stepped beam envelope through the full pier
                # thickness. A depth-limited pocket otherwise closes at the
                # outside face, creating an unsupported roof when each half
                # prints on its central glue plane.
                rot=np.asarray([n,UP,t])
                local_relief=relief.transform(np.column_stack((rot,-rot@origin)))
                section=m3d.CrossSection(local_relief.project().to_polygons(),m3d.FillRule.Positive)
                section=section.offset(.01,m3d.JoinType.Miter).simplify(.002)
                relief=section.extrude(2*(half+1)).translate((0,0,-half-1))
                relief=relief.transform(np.column_stack((n,UP,t,origin)))
                cream=cream-relief
            # New beam underside blocks have a true flat bearing at p.z-7.40.
            # Pads restore only that intended datum, retaining side clearance.
            bearing=p[2]-7.40
            cream=union(cream,prism(rect(-2.35,bearing-.8,2.35,bearing),-1.30,1.30,origin,n,UP,t))
        # Flat centre faces against bed; both pockets face upward after printing.
        centre=float(np.dot(origin,t))
        for side in [-1,1]:
            # Remove sub-5-micron coplanar slivers left where the curved beam
            # relief meets the flat seat and laminate plane before STL rounding.
            halfsolid=cream.trim_by_plane(tuple(t*side),centre*side).simplify(.005)
            if side==1:
                halfsolid=union(halfsolid,foot_key).simplify(.001)
            r=frame_rotation(n,UP,t) if side==1 else frame_rotation(-n,UP,-t)
            parts.append(Part(f'pier_{i:02}_{"front" if side==1 else "back"}_half','cream',halfsolid,r,'Align paired flat backs in the assembly jig before gluing. Front half has whole 6 x 2.0 mm foot key, 4.2 mm deep; tray locates it through a generous sand passage. Flat top pads establish beam height.'))
        parts+=inserts
        record.append({'pier':i,'fraction':f,'seat_floor_z':floor,'bearing_top_z':float(p[2]-7.40),'seat_side_clearance_mm':.20,'socket_centre_xy':(origin+t)[:2].tolist(),'foot_key_mm':[6.,2.,4.2],'tray_engagement_mm':2.2,'inlay_glue_relief_mm':.20,'inlay_seating_lands':3})
    return parts,{'base_socket_cutters':sockets,'sand_clearance_cutters':sand_sockets,'piers':record}

def source_outline(name):
    mesh=to_trimesh(load_source(name));return MultiPoint(mesh.vertices[:,:2]).convex_hull

def build_base(socket_cutters=(),sand_clearance_cutters=()):
    parts=[];outer=source_outline('BASE_Porcelain rim');sand_outline=source_outline('BASE_Sand inset')
    bottom=-7.0*F
    tray=load_source('BASE_Porcelain rim')
    # Flatten the underside fillet by removing its first 0.50 mm. The ground
    # and joint heights remain fixed; the wider bed face avoids early flare.
    tray=tray.trim_by_plane((0,0,1),bottom+.50)
    # Ground level is z=0. 2 mm sand inserts bear on the tray floor.
    tray=tray-prism(sand_outline.buffer(.15,join_style=1),-2.0,2.0)
    sand=prism(sand_outline,-2.0,0.)
    sockets=union(*socket_cutters)
    sand_sockets=union(*(sand_clearance_cutters or socket_cutters))
    tray=tray-sockets;sand=sand-sand_sockets
    # Recessed glue areas on the hidden sand underside; the rim and pads are
    # positive 2 mm thickness datums. Print visible face down, recesses up.
    relief=prism(sand_outline.buffer(-2.0),-2.01,-1.80)
    for x,y in [(-85,-30),(-85,75),(-35,15),(40,-30),(95,60),(40,85)]:
        relief=relief-box((x,y,-1.9),(5,5,.5))
    sand=sand-relief
    # Each sand half has a round datum and an elongated secondary socket.
    # This prevents loose decorative sheets from controlling structural feet.
    sand_register=[]
    for label,x in [('left',-65.),('right',62.)]:
        for index,y in enumerate([-35.,85.]):
            a=(x,y,-2.15);b=(x,y,-1.10)
            boss=cylinder_between(a,b,1.8,32)
            tray=union(tray,boss)
            if index==0:
                socket=cylinder_between((x,y,-2.2),(x,y,-.85),2.0,32)
            else:
                socket=union(cylinder_between((x,y-.6,-2.2),(x,y-.6,-.85),2.0,32),cylinder_between((x,y+.6,-2.2),(x,y+.6,-.85),2.0,32),box((x,y,-1.525),(4.,1.2,1.35)))
            sand=sand-socket
            sand_register.append({'side':label,'xy':[x,y],'boss_diameter':3.6,'socket_width':4.0,'secondary_slot':bool(index),'engagement_mm':.9})
    split=5*F;gap=0.
    peg_meta=[]
    for i,y in enumerate([-40.,82.],1):
        centre=(split,y,-4.6);size=(10.,4.,2.)
        # Join pockets are open from the tray top; there is no bridged roof.
        tray=tray-box((split,y,-3.75),(10.4,4.4,3.70))
        peg=box(centre,size)
        parts.append(Part(f'base_join_key_{i:02}','cream',peg,None,'Close the tray seam fully, drop this key into the open-top pocket, then glue. Add sand after joining the trays. No blind bridged slot.'))
        peg_meta.append({'centre':centre,'key_size':size})
    for label,side in [('left',-1),('right',1)]:
        offset=(split+gap/2)*side if side==1 else -(split-gap/2)
        for color,solid in [('cream',tray),('sand',sand)]:
            half=solid.trim_by_plane((side,0,0),offset)
            rotation=None if color=='cream' else frame_rotation((1,0,0),(0,-1,0),(0,0,-1))
            notes='Close the two-piece base seam fully. Open-top joining pockets are covered after the sand is installed. Keep at 100% scale.' if color=='cream' else 'Print visible ground face down, glue recesses and registration sockets up. Glue only recessed underside areas; bearing rim/pads set the height. Round plus slotted sockets register to tray; generous foot passages are not locators.'
            parts.append(Part(f'base_{label}_{"tray" if color=="cream" else "sand"}',color,half,rotation,notes))
    return parts,{'split_x':split,'seam_gap_mm':gap,'sand_top_z':0.,'sand_thickness_mm':2.,'sand_glue_relief_mm':.20,'sand_registration':sand_register,'join_keys':peg_meta,'join_pockets':'open_top','bottom_flattened_mm':.50}
