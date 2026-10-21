"""Small v03 fit set cropped from actual production body solids.

Copies retain the source part's print orientation and supported-surface warning.
Only the coupon material is standardized to blue for one filament/plate family;
the interfaces are neither rescaled nor rebuilt as idealized boxes.
"""
import numpy as np
from .common import Part,sample_route
from .body import CUTS,local_box

UP=np.array([0.,0.,1.])


def build(parts):
    production={p.name:p for p in parts}
    samples=[];metadata={'source':'Current production body Part solids before export',
                         'colour':'blue','samples':[],
                         'limitations':'Physical fit remains untested. Cropped pieces preserve their local interface and production print rotation, but do not reproduce the entire beam support field.'}

    def sample(name,source,solid,notes,crop=None):
        src=production[source]
        if len(solid.decompose())!=1 or solid.volume()<=0:
            raise ValueError((name,'Coupon crop is not one positive solid'))
        tags={'test':True,'family':'body fit sample','purpose':'fit_test',
              'production_part':source,'geometry':'full production part' if crop is None else 'crop of production part'}
        if crop is not None:tags['crop']=crop
        samples.append(Part(name,'blue',solid,src.orientation,notes,src.supports,tags))
        metadata['samples'].append({'name':name,'production_part':source,'crop':crop,
                                    'volume_mm3':float(solid.volume()),'supports':src.supports})

    sample('test_body_hoop_11','body_hoop_11',production['body_hoop_11'].solid,
           'Exact production hoop11 including v03 shoulder stops, wider key and curved rail grooves. Keep its supplied flat print orientation. Use with the cropped beam seat and both curved rail samples.')
    for track in [2,3]:
        source=f'body_rail_{track:02}_section_03'
        sample(f'test_body_rail_{track:02}_section_03',source,production[source].solid,
               f'Exact curved production rail track{track}, section3. Print with the production support setting and clean carefully. Test the matching groove of hoop11 without flexing or force; this tests the formerly tight bend.')

    f=10/17;p,t,n=sample_route(f)
    lo=[-8.,-15.,-7.];hi=[8.,6.,7.]
    crop=local_box(p,n,UP,t,lo,hi)
    sample('test_body_seat_hoop_11','body_beam_03',production['body_beam_03'].solid^crop,
           'Production beam03 cropped around the hoop11 socket; the wider socket, 1.20 mm floor and two shoulder ledges are unchanged. Print in the beam orientation with supports, clean, then check that hoop11 seats at the shoulder stops without rocking or force.',
           {'origin_world_mm':p.tolist(),'axes':['route lateral n','world up','route tangent t'],
            'axis_vectors':[n.tolist(),UP.tolist(),t.tolist()],'lower_mm':lo,'upper_mm':hi})

    # Joint between beam02 and beam03; retain the complete male tongue and
    # female cavity while clipping only the remote grip ends of each beam.
    f=CUTS[2];p,t,n=sample_route(f)
    direction=sample_route(f+.002)[0]-sample_route(f-.002)[0];direction/=np.linalg.norm(direction)
    lateral=np.cross(UP,direction);lateral/=np.linalg.norm(lateral);vertical=np.cross(direction,lateral)
    centre=p+UP*(-4.15)
    for label,source,lo,hi in [
        ('male','body_beam_02',[-7.,-6.,-8.],[5.0,6.,8.]),
        ('female','body_beam_03',[-.50,-6.,-8.],[6.25,6.,8.]),
    ]:
        crop=local_box(centre,direction,lateral,vertical,lo,hi)
        sample(f'test_body_beam_joint_{label}',source,production[source].solid^crop,
               f'Actual beam02/03 joint {label} end, cropped only beyond the mating geometry. Keep its production print orientation and support setting. Clean supported faces and check full seating at the beam butt faces without forcing or bending the tongue.',
               {'origin_world_mm':centre.tolist(),'axes':['joint insertion direction','joint lateral','joint vertical'],
                'axis_vectors':[direction.tolist(),lateral.tolist(),vertical.tolist()],'lower_mm':lo,'upper_mm':hi})

    metadata['count']=len(samples)
    metadata['total_volume_mm3']=sum(p.solid.volume() for p in samples)
    metadata['estimated_solid_mass_g_at_1_24g_cm3']=metadata['total_volume_mm3']*.00124
    metadata['mass_note']='Solid-volume estimate excludes slicer supports/brims and depends on PLA density; this is not a slicer filament estimate.'
    return samples,metadata
