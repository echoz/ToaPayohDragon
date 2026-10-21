"""Three-piece cream PLA fit test: actual hoop key and nominal head pin."""
import numpy as np
from .common import Part,box,union,cylinder_between
from .body import KEY_REAR,KEY_FRONT,KEY_WIDTH,KEY_ENGAGEMENT

CLEARANCES=(.20,.30,.40,.50)
KEY_LENGTH=KEY_FRONT-KEY_REAR
SLOT_DEPTH=KEY_ENGAGEMENT+.20
PIN_DIAMETER=3.0
PIN_ENGAGEMENT=2.40
PIN_HOLE_DEPTH=2.70
BAR_TOP=4.0


def build(body_parts=None):
    if body_parts is None:
        from .body import build as build_body
        body_parts,_=build_body()
    original=next(part for part in body_parts if part.name=='body_hoop_02')
    bar=box((0,0,BAR_TOP/2),(56,25,BAR_TOP))
    ticks=[];marks=[]
    for mark,(x,clearance) in enumerate(zip((-21,-7,7,21),CLEARANCES),1):
        slot=box((x,-3,BAR_TOP-SLOT_DEPTH/2+.1),
                 (KEY_WIDTH+clearance,KEY_LENGTH+clearance,SLOT_DEPTH+.2))
        bore=cylinder_between((x,5,BAR_TOP-PIN_HOLE_DEPTH),
                              (x,5,BAR_TOP+.2),(PIN_DIAMETER+clearance)/2)
        bar=bar-slot-bore
        # Two-nozzle-wide raised strokes need no font and remain easy to count.
        for i in range(mark):
            tx=x+(i-(mark-1)/2)*1.6
            ticks.append(box((tx,-9.0,BAR_TOP+.20),(.8,3,.60)))
        marks.append({'ticks':mark,'clearance_total_mm':clearance,
                      'clearance_per_side_mm':clearance/2,
                      'rectangle_width_mm':KEY_WIDTH+clearance,
                      'rectangle_length_mm':KEY_LENGTH+clearance,
                      'pin_bore_diameter_mm':PIN_DIAMETER+clearance,
                      'rectangle_centre_xy_mm':[x,-3],
                      'pin_bore_centre_xy_mm':[x,5]})
    bar=union(bar,*ticks)

    # Preserve the production hoop, including its prescribed printing rotation.
    matrix=np.column_stack((np.asarray(original.orientation),np.zeros(3)))
    hoop=original.solid.transform(matrix)
    bounds=np.asarray(hoop.bounding_box())
    hoop=hoop.translate(np.array([35.,-12.5,0.])-bounds[:3])

    pin_origin=(24.,20.)
    handle=cylinder_between((*pin_origin,0),(*pin_origin,2),5.0)
    probe=cylinder_between((*pin_origin,1.90),(*pin_origin,2+PIN_ENGAGEMENT),PIN_DIAMETER/2)
    pin=union(handle,probe)
    tags={'test':True,'family':'fit coupon','purpose':'fit_test'}
    parts=[
        Part('test_clearance_bar','cream',bar,np.eye(3),
             'Four columns marked by 1–4 raised ticks: total clearance 0.20, 0.30, 0.40, 0.50 mm. Rectangles accept the hoop02 key; round bores accept the 3 mm handled pin. Pockets up, flat underside on bed.',
             'none',dict(tags)),
        Part('test_hoop_02','cream',hoop,np.eye(3),
             'Exact production hoop02 and flat printing orientation, including integrated key and rail grooves. Try its key in each rectangle pocket without force. Keep as a spare after testing.',
             'none',dict(tags,production_part='body_hoop_02')),
        Part('test_head_pin_3mm','cream',pin,np.eye(3),
             'Nominal 3 mm cylindrical calibration probe, 2.4 mm exposed length, with a 10 mm handle. Print handle down, pin up. This is a generic comparison; use the actual D-foot and platform samples for production fit.',
             'none',dict(tags)),
    ]
    info={'metadata':{
        'purpose':'Quick PLA fit calibration before the full kit; test pieces are not assembly components.',
        'color':'cream','piece_count':3,'recommended_layer_height_mm':.16,
        'minimum_tick_width_mm':.80,'bar_dimensions_mm':[56,25,4.5],
        'body_key_profile_mm':[KEY_WIDTH,KEY_LENGTH],
        'body_key_nominal_engagement_mm':KEY_ENGAGEMENT,
        'rectangular_pocket_depth_mm':SLOT_DEPTH,
        'head_pin_nominal_diameter_mm':PIN_DIAMETER,
        'head_pin_exposed_length_mm':PIN_ENGAGEMENT,
        'round_pocket_depth_mm':PIN_HOLE_DEPTH,
        'columns':marks,'kit_default_total_clearance_mm':.30,
        'interpretation':'Use the smallest clearance that seats fully with light finger pressure and can be removed. Two ticks matches the kit default. If only another column works, adjust mating sockets or calibrated slicer compensation and rerun the coupon before the full kit.',
        'limitation':'General clearance comparison only. Also print the actual interface samples with their supplied orientations and supports; those test curved rails, shoulders, D-feet, platform, ladder and colour inserts.'}}
    return parts,info


if __name__=='__main__':
    from .common import to_trimesh
    parts,info=build()
    for part in parts:
        mesh=to_trimesh(part.solid)
        print(part.name,'watertight',mesh.is_watertight,'components',len(part.solid.decompose()),'volume_mm3',round(mesh.volume,3))
    print(info['metadata'])
