"""Small v03 fit samples cut from actual production head solids.

The samples retain assembled coordinates and each source part's supplied print
orientation. No idealized surrogate replaces a hole, peg or split/glue face.
"""
import numpy as np
from shapely.geometry import box as polygon_box
from .common import Part,F,box,to_trimesh
from . import head


def build(parts):
    source={p.name:p for p in parts}
    required=['head_A_cream_inner','head_A_cream_outer','head_platform_snout']
    for name in required:
        if name not in source:raise KeyError(f'Head samples need production part {name}')
    out=[]
    # The mid-plane remains the bed datum. This window retains the actual
    # shelf root, complete open U-slot, blind floor and positive bearing top.
    shelf_profile=polygon_box(72*F*head.NORM-2,head.FLOOR_BOTTOM-head.SHELF_HEIGHT-1.6,
                              89*F*head.NORM+2,head.FLOOR_BOTTOM+2)
    shelf_window=head.plate(shelf_profile,-20,.01,1)
    inner=source['head_A_cream_inner']
    shelf=inner.solid ^ shelf_window
    out.append(Part('test_head_A_shelf_slot','cream',shelf,inner.orientation,
                    'Actual A-side shelf crop. Keep the supplied production orientation: open U-slot upward. The platform-peg coupon drops into this slot and its plate underside must rest on the shelf top.',
                    inner.supports,{'test':True,'purpose':'fit_test','production_part':inner.name,'family':'head_fit_sample'}))

    key=head.world(80.5,head.FLOOR_BOTTOM/F,head.PLATFORM_PEG_D,1);key[2]=head.FLOOR_BOTTOM
    platform=source['head_platform_snout']
    # World-X cropping deliberately keeps a broad flat rear edge for the
    # platform's production orientation. An angled local crop would rest on
    # a corner instead and would cease to represent that print orientation.
    peg_window=box((key[0],key[1],head.FLOOR_BOTTOM+1),(10,7,8))
    peg=platform.solid ^ peg_window
    out.append(Part('test_head_platform_peg_A','cream',peg,platform.orientation,
                    'Actual A-side platform peg and plate crop. Keep the production rear-edge-down orientation and use supports under the horizontal peg. After cleanup, lower the peg vertically into test_head_A_shelf_slot; its plate must seat on the shelf.',
                    platform.supports,{'test':True,'purpose':'fit_test','production_part':platform.name,'family':'head_fit_sample'}))

    # Two complete production pins, their shoulder and both original glue
    # faces. Matching straight crop edges make the small pair easy to hold.
    foot_profile=polygon_box(75.5*F*head.NORM,-head.FOOT_PIN_LENGTH-.1,
                             89.5*F*head.NORM,10.)
    foot_window=head.plate(foot_profile,-20,20,1)
    for suffix,label in [('cream_inner','inner'),('cream_outer','outer')]:
        prod=source['head_A_'+suffix]
        crop=prod.solid ^ foot_window
        notes=('Actual inner-foot crop carrying both whole D-flat pins. Test these pins against the parent kit\'s matching A-foot tray and sand fixture before gluing. '
               if label=='inner' else
               'Actual outer-foot cosmetic crop; it has no locating pins. ')
        notes+='The two foot coupons meet on their flat production glue faces. Align their matching straight crop edges, dry-clamp first, then test a thin glue film if desired.'
        out.append(Part('test_head_A_foot_'+label,'cream',crop,prod.orientation,notes,prod.supports,
                        {'test':True,'purpose':'fit_test','production_part':prod.name,'family':'head_fit_sample'}))
    for p in out:
        p.solid=p.solid.simplify(.001)
        mesh=to_trimesh(p.solid)
        assert mesh.is_watertight and mesh.volume>0,(p.name,'invalid sample mesh')
        assert len(p.solid.decompose())==1,(p.name,'sample has disconnected pieces')
    metadata={'samples':len(out),'geometry':'Cropped production source solids, retaining production print orientations',
              'relationships':[
                  {'parts':['test_head_A_shelf_slot','test_head_platform_peg_A'],
                   'assembly':'Vertical top-drop of peg coupon into shelf coupon; plate underside seats at the actual shelf top.',
                   'bearing_z_mm':head.FLOOR_BOTTOM,'peg_xy_mm':key[:2].tolist(),
                   'tests':['open shelf slot','supported horizontal peg finish','lateral fit','positive vertical seating'],
                   'does_not_test':['full platform travel past eye rims','two-panel span alignment']},
                  {'parts':['test_head_A_foot_inner','test_head_A_foot_outer'],
                   'assembly':'Match flat glue faces and straight crop edges; the inner coupon alone owns both whole locating pins.',
                   'matching_external_fixture':'Parent kit actual A-foot round/slot tray fixture plus relieved sand layer',
                   'tests':['whole D-flat pin print contact','two-pin foot pitch','round/slot tray location when paired with parent fixture','independence from cosmetic glue seam'],
                   'does_not_test':['full head lamination jig','four-pin global head span','complete base flatness']}
              ],'physical_fit':'Not yet printed; these are the proposed representative physical checks.'}
    return out,metadata
