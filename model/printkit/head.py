"""V03 printable head with whole inner-half pins and open shelf locating slots.

The approved v06 visible silhouette is retained. All solids are in assembled
millimetres; head laminations print on their broad central glue faces. Hidden
joints use positive seating lands and full insertion-path reliefs.
"""
import math
from functools import lru_cache
import numpy as np
import manifold3d as m3d
from shapely.geometry import Polygon, Point, box as polygon_box
from model.blender_head_v04 import FACE_PROFILE, EYE_CENTRE
from .common import F, Part, load_source, union, box, prism, cylinder_between, frame_rotation

SPLAY=.55
NORM=math.sqrt(1+SPLAY*SPLAY)
HALF=2.4*F
INLAY=1.4
SIDE_CLEARANCE=.20
GLUE_RELIEF=.20
FLOOR_BOTTOM=37.4*F
FLOOR_TOP=40.0*F
SHELF_HEIGHT=3.4
SHELF_SLOT_DEPTH=2.2
SHELF_SLOT_RADIUS=1.75
PLATFORM_PEG_D=-HALF-2.9
PLATFORM_EYE_CLEARANCE=.30
FOOT_PIN_D=-1.0
FOOT_PIN_RADIUS=1.5
FOOT_PIN_LENGTH=4.2
FOOT_SOCKET_RADIUS=1.7
FOOT_SOCKET_DEPTH=4.5
FOOT_SLOT_HALF_LENGTH=.50
SAND_CLEARANCE_RADIUS=2.1
INLAY_LANDS_RAW=((47,76),(82,12),(70,48))


def axes(side):
    u=np.array([1/NORM,-side*SPLAY/NORM,0.])
    v=np.array([0.,0.,1.])
    n=np.array([SPLAY/NORM,side/NORM,0.])
    origin=np.array([0.,side*61.8*F,0.])
    return origin,u,v,n


def profile(poly):
    return Polygon([(x*F*NORM,z*F) for x,z in poly])


def plate(poly,lo,hi,side):
    origin,u,v,n=axes(side)
    return prism(poly,lo,hi,origin,u,v,n)


def world(x,z,d,side):
    origin,u,v,n=axes(side)
    return origin+u*x*F*NORM+v*z*F+n*d


def octagon(radius):
    x,z=EYE_CENTRE
    return profile([(x+radius*math.cos(math.pi/8+i*math.pi/4),
                     z+radius*math.sin(math.pi/8+i*math.pi/4)) for i in range(8)])


def vertical_cylinder(p,radius,z0,z1):
    return cylinder_between((p[0],p[1],z0),(p[0],p[1],z1),radius,48)


def slot_from_round(solid,u,half_length):
    if not half_length:return solid
    # Convex segment dilation: a true capsule, not a row of overlapping holes.
    # A near-zero transverse sweep made coplanar flakes at the tray floor.
    # A 1-micron kernel adds only 0.0005 mm transverse/axial allowance per
    # side and remains stable when the cutter reaches the real tray solid.
    return solid.minkowski_sum(box((0,0,0),(2*half_length,.001,.001)).transform(
        np.column_stack((u,(-u[1],u[0],0),(0,0,1),(0,0,0))))).simplify(.001)


@lru_cache(maxsize=1)
def first_hoop_receiving_relief():
    from .body import build as body_build
    body_parts,_=body_build()
    first=next(p.solid for p in body_parts if p.name=='body_hoop_01')
    low=FLOOR_BOTTOM-4.5;high=FLOOR_TOP+.35
    local=first ^ box((0,0,(low+high)/2),(1000,1000,high-low))
    return local.minkowski_sum(box((0,0,2.),(.5,.5,4.5)))


def build():
    parts=[];base_sockets=[];sand_clearances=[];feet=[];shelves=[];platform_pegs=[]
    land_records=[];foot_pin_shapes=[]
    face=profile(FACE_PROFILE).buffer(-.25,join_style='round').buffer(.25,join_style='round')
    face=face.difference(octagon(9).buffer(SIDE_CLEARANCE,join_style='round'))
    shelf_profile=polygon_box(72*F*NORM,FLOOR_BOTTOM-SHELF_HEIGHT,89*F*NORM,FLOOR_BOTTOM)
    outer_back=HALF+.55*F-INLAY
    inner_back=-HALF-.55*F+INLAY
    half_profile=polygon_box(-500,-500,500,500)
    for side,label in ((1,'A'),(-1,'B')):
        origin,u,v,n=axes(side)
        keep=box((0,side*150.15,50),(1000,300,300))
        cream=union(load_source(f'HEAD_{label}_CreamPanel'),
                    load_source(f'HEAD_{label}_OuterEyeSurround'),
                    load_source(f'HEAD_{label}_InnerEyeSurround')) ^ keep
        outside_cutter=plate(face.buffer(SIDE_CLEARANCE,join_style='round'),outer_back-GLUE_RELIEF,HALF+1.4,side)
        inside_shape=face.difference(shelf_profile.buffer(SIDE_CLEARANCE,join_style='mitre'))
        inside_cutter=plate(inside_shape.buffer(SIDE_CLEARANCE,join_style='round'),-HALF-1.4,inner_back+GLUE_RELIEF,side)
        cream=cream-outside_cutter-inside_cutter

        # Three broad lands positively set each insert's visible level. Glue
        # occupies the surrounding 0.20 mm relief rather than lifting the face.
        for color,shape,low,high in [('orange',face,outer_back-GLUE_RELIEF-.05,outer_back),
                                     ('blue',inside_shape,inner_back,inner_back+GLUE_RELIEF+.05)]:
            for x,z in INLAY_LANDS_RAW:
                land=Point(x*F*NORM,z*F).buffer(1.1,quad_segs=12)
                assert shape.buffer(-.25).contains(land),(label,color,x,z)
                cream=union(cream,plate(land,low,high,side))
                land_records.append({'side':label,'color':color,'profile_xz_raw_mm':[x,z],
                                     'diameter_mm':2.2,'glue_relief_mm':GLUE_RELIEF})

        shelf=plate(shelf_profile,-HALF-4.9,-HALF+INLAY+.55,side)^keep
        key=world(80.5,FLOOR_BOTTOM/F,PLATFORM_PEG_D,side);key[2]=FLOOR_BOTTOM
        socket=vertical_cylinder(key,SHELF_SLOT_RADIUS,FLOOR_BOTTOM-SHELF_SLOT_DEPTH,FLOOR_BOTTOM+.25)
        # The opening runs to the inward shelf tip, which faces upward during
        # printing. No horizontal bore crown or hidden ceiling remains.
        opening_profile=polygon_box(80.5*F*NORM-SHELF_SLOT_RADIUS,
                                    FLOOR_BOTTOM-SHELF_SLOT_DEPTH,
                                    80.5*F*NORM+SHELF_SLOT_RADIUS,FLOOR_BOTTOM+.25)
        opening=plate(opening_profile,-HALF-5.25,PLATFORM_PEG_D,side)
        shelf=shelf-union(socket,opening)
        cream=union(cream,shelf)
        shelves.append({'side':label,'type':'inward-open U-slot','top_z_mm':FLOOR_BOTTOM,
                        'peg_xy_mm':key[:2].tolist(),'slot_width_mm':2*SHELF_SLOT_RADIUS,
                        'slot_depth_mm':SHELF_SLOT_DEPTH,'floor_thickness_mm':SHELF_HEIGHT-SHELF_SLOT_DEPTH,
                        'opening_direction_xyz':(-n).tolist(),'peg_diameter_mm':3.,
                        'peg_engagement_mm':1.8,'bottom_allowance_mm':SHELF_SLOT_DEPTH-1.8})
        platform_pegs.append(vertical_cylinder(key,1.5,FLOOR_BOTTOM-1.8,FLOOR_BOTTOM+.45))

        orange=plate(face,outer_back,HALF+.55*F,side)^keep
        blue=plate(inside_shape,-HALF-.55*F,inner_back,side)^keep
        cream_orientation=frame_rotation(side*u,v,-n)
        orange_orientation=frame_rotation(-side*u,v,n)
        outer_half=cream ^ plate(half_profile,0,30,side)
        inner_half=cream ^ plate(half_profile,-30,0,side)
        for index,x in enumerate((79,86)):
            p=world(x,0,FOOT_PIN_D,side);p[2]=0
            pin=vertical_cylinder(p,FOOT_PIN_RADIUS,-FOOT_PIN_LENGTH,0.)
            # Whole D-flat pins belong only to the inner half. Their clipped
            # backs share its glue/build datum; no locating pin crosses a seam.
            pin=pin^plate(half_profile,-30,0,side)
            inner_half=union(inner_half,pin)
            foot_pin_shapes.append(pin)
            slot_half=FOOT_SLOT_HALF_LENGTH if index else 0.
            socket=vertical_cylinder(p,FOOT_SOCKET_RADIUS,-FOOT_SOCKET_DEPTH,.3)
            lead=m3d.Manifold.cylinder(.5,FOOT_SOCKET_RADIUS,2.0,48).translate((p[0],p[1],-2.45))
            socket=slot_from_round(union(socket,lead),u,slot_half)
            sand_cut=slot_from_round(vertical_cylinder(p,SAND_CLEARANCE_RADIUS,-2.4,.5),u,slot_half)
            base_sockets.append(socket);sand_clearances.append(sand_cut)
            feet.append({'side':label,'index':index+1,'owner':f'head_{label}_cream_inner',
                         'xy_mm':p[:2].tolist(),'type':'round locator' if index==0 else 'slot locator',
                         'pin_profile':'D-flat, whole on inner half','pin_diameter_mm':3.,
                         'pin_flat_chord_mm':2*math.sqrt(FOOT_PIN_RADIUS**2-FOOT_PIN_D**2),'pin_tip_z_mm':-FOOT_PIN_LENGTH,
                         'pin_length_below_shoulder_mm':FOOT_PIN_LENGTH,'tip_lead_in_mm':0.,'lead_in':'female tray mouth only; flat pin nose preserves support-free print contact',
                         'socket_diameter_mm':2*FOOT_SOCKET_RADIUS,'slot_extra_length_mm':2*slot_half,
                         'slot_numeric_kernel_mm':.001 if slot_half else 0.,
                         'slot_numeric_simplify_mm':.001 if slot_half else 0.,
                         'slot_direction_xyz':u.tolist(),'depth_mm':FOOT_SOCKET_DEPTH,
                         'socket_entry_chamfer_top_z_mm':-1.95,'socket_entry_diameter_mm':4.,
                         'sand_hole_diameter_mm':2*SAND_CLEARANCE_RADIUS,
                         'sand_clearance_per_side_mm':SAND_CLEARANCE_RADIUS-FOOT_PIN_RADIUS})
        for name,color,solid,orient,note in [
            (f'head_{label}_cream_outer','cream',outer_half,orange_orientation,
             'Print central glue face down. Align this cosmetic half to its matching inner half in the head lamination jig; the outer half has no foot pins.'),
            (f'head_{label}_cream_inner','cream',inner_half,cream_orientation,
             'Print central glue face down. Whole D-flat foot pins belong to this half. Use the head lamination jig; inward-open platform slots face up in print orientation.'),
            (f'head_{label}_orange','orange',orange,orange_orientation,
             '1.4 mm exterior insert. Seat its back on the three cream lands. Use small glue amounts in the surrounding 0.20 mm relief; do not coat the lands.'),
            (f'head_{label}_blue','blue',blue,cream_orientation,
             '1.4 mm interior insert. Pass the aperture around the shelf, then seat on three cream lands. Glue in surrounding 0.20 mm relief; keep lands clear.')]:
            parts.append(Part(name,color,solid,orient,note,tags={'family':'head','side':label}))
    def inside_y(x):
        # The eye surround, not the thinner blue face, sets the top-drop corridor.
        return (61.8-.55*x)*F-NORM*(HALF+.85*F+PLATFORM_EYE_CLEARANCE)
    floor=Polygon([(61.3*F,-inside_y(61.3)),(61.3*F,inside_y(61.3)),
                   (96*F,inside_y(96)),(96*F,-inside_y(96))])
    platform=prism(floor,FLOOR_BOTTOM,FLOOR_TOP+.10)
    snout_plan=Polygon([(94.75*F,-inside_y(94.75)+.05),(94.75*F,inside_y(94.75)-.05),
                        (97.25*F,inside_y(97.25)-.05),(97.25*F,-inside_y(97.25)+.05)])
    snout=prism(snout_plan,40*F-.15,45*F)
    platform=union(platform,snout,*platform_pegs)
    # The continuous upward sweep is the reverse of downward hoop insertion.
    platform=platform-first_hoop_receiving_relief()
    platform_orientation=frame_rotation((0,1,0),(0,0,1),(1,0,0))
    parts.append(Part('head_platform_snout','cream',platform,platform_orientation,
                      'Rear edge down with a 5 mm brim and supports beneath the two locating pegs. Drop between head panels; pegs enter open U-slots while the floor rests positively on both shelves.',
                      supports='build-plate-only for horizontal locating pegs',tags={'family':'head'}))
    info={'base_socket_cutters':base_sockets,'sand_clearance_cutters':sand_clearances,
          'foot_pin_shapes':foot_pin_shapes,
          'metadata':{'revision':'v03','inlay_thickness_mm':INLAY,'inlay_xy_clearance_per_side_mm':SIDE_CLEARANCE,
                      'glue_relief_mm':GLUE_RELIEF,'pocket_depth_clearance_mm':0.,
                      'inlay_seating':'three positive lands per insert at the intended visible face level',
                      'inlay_lands':land_records,'nose_gap_mm':.30,
                      'eye_surround':'integral raised cream borders; true aperture retained',
                      'foot_pins':feet,'platform_shelves':shelves,
                      'platform_eye_corridor_clearance_mm':PLATFORM_EYE_CLEARANCE,
                      'platform_assembly':'vertical top drop before head is fixed to the base',
                      'first_hoop_receiver':'continuous 0–4 mm vertical insertion sweep plus 0.25 mm XYZ clearance',
                      'lamination_registration':'external head-outline jig; whole D-flat pins remain on the inner half',
                      'head_glue_face_normal_by_side':{str(s):axes(s)[3].tolist() for s in (1,-1)}}}
    for part in parts:part.solid=part.solid.simplify(1e-4)
    return parts,info
