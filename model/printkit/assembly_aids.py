"""Open, flat-bottom cradles for registering the bare cream laminations.

A foot floor and narrow full-perimeter frame register the complete bare pair.
The centre stays open beneath raised eye rims and other exterior reliefs.
No print surface or mating interface of a production part is modified.
"""
import numpy as np
from shapely.geometry import Polygon, GeometryCollection, box as rect
from .common import Part, box, union, prism, to_trimesh


def filled_projection(solid):
    shape=GeometryCollection()
    for contour in solid.project().to_polygons():
        if len(contour)>=3:shape=shape.symmetric_difference(Polygon(contour))
    components=[shape] if shape.geom_type=='Polygon' else list(shape.geoms)
    from shapely.ops import unary_union
    return unary_union([Polygon(p.exterior) for p in components if p.geom_type=='Polygon'])


def build(parts):
    by={p.name:p for p in parts};aids=[];records=[]
    pairs=[(f'head_{s}',f'head_{s}_cream_inner',f'head_{s}_cream_outer') for s in ['A','B']]
    pairs += [(f'pier_{i:02}',f'pier_{i:02}_front_half',f'pier_{i:02}_back_half') for i in range(1,6)]
    pairs += [(f'tail_{s}',f'tail_{s}_cream_inner',f'tail_{s}_cream_outer') for s in ['A','B']]
    for label,upper_name,lower_name in pairs:
        upper,lower=by[upper_name],by[lower_name]
        rot=np.asarray(upper.orientation)
        matrix=np.column_stack((rot,np.zeros(3)))
        pair=union(upper.solid,lower.solid)
        # All prescribed lamination rotations put world Z along print Y.
        assert np.allclose(rot[1],[0,0,1])
        foot=pair^box((0,0,3.5),(1000,1000,17.)) # Z -5..12
        transformed=foot.transform(matrix)
        zmin=np.asarray(transformed.bounding_box())[2]
        whole=pair.transform(matrix).translate((0,0,1.2-zmin))
        foot=transformed.translate((0,0,1.2-zmin))
        bb=np.asarray(foot.bounding_box())
        outline=filled_projection(whole)
        outside=outline.buffer(3.,join_style='round')
        foot_floor=outside.intersection(rect(bb[0]-3,bb[1]-3,bb[3]+3,10.))
        # A narrow bearing rim follows the whole silhouette. Its open centre
        # avoids the head's raised eye rings, which sit below the foot datum.
        full_frame=outside.difference(outline.buffer(-.8,join_style='round'))
        blank=foot_floor.union(full_frame)
        height=float(bb[5]+.8)
        cavity=outline.buffer(.15,join_style='round')
        jig=prism(blank,0,height)-prism(cavity,1.2,height+1)
        assert len(jig.decompose())==1,(label,'jig disconnected')
        assert abs((jig^whole).volume())<1e-5,(label,'jig collides with bare pair')
        note=f'Assembly cradle for {label} ONLY. Lay the bare {lower_name} exterior down, central glue face up; place {upper_name} on top, key on the correct side. The foot rests on the floor and the full perimeter guides both outlines. Seat both halves against the same side and foot datum, clamp their flat backs together, and check the complete outline. Lift the glued pair straight up out of the open-top frame. Remove before fitting colour inserts. Keep glue out of cradle. 0.15 mm side allowance; it is an alignment aid, not a tight clamp.'
        aids.append(Part('test_jig_'+label,'cream',jig,np.eye(3),note,'none',
                         {'test':True,'purpose':'assembly_jig','production_parts':[lower_name,upper_name]}))
        records.append({'name':'test_jig_'+label,'parts':[lower_name,upper_name],
                        'clearance_per_side_mm':.15,'floor_mm':1.2,'foot_floor_world_z_max_mm':10.,
                        'captured_world_z_max_mm':float(whole.bounding_box()[4]),
                        'full_outline_registration':True,'open_center':True,
                        'placement_rotation_world_to_jig':rot.tolist(),'placement_translation_jig':[0,0,float(1.2-zmin)],
                        'source_overlap_mm3':float((jig^whole).volume())})
    return aids,{'metadata':{'purpose':'Optional open-top perimeter cradles register bare cream laminations before gluing. Print only when ready to assemble that family.','jigs':records}}
