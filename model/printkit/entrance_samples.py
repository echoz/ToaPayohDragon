"""Seven modest test pieces copied/cropped from the actual entrance production parts.

All samples retain their production print orientations and colours. They test
real interfaces, including supported ladder surfaces, rather than idealized
replacement pins or slots. No production part is changed by this module.
"""
from dataclasses import replace
import numpy as np
from .common import F


def build(parts):
    by_name={part.name:part for part in parts}
    required=['tail_A_cream_inner','tail_A_blue','tail_A_cream_handrail',
              'tail_threshold_landing','body_hoop_18',
              'ladder_blue_frame','ladder_cream_tread_comb']
    missing=[name for name in required if name not in by_name]
    if missing:raise ValueError('Entrance samples need production parts: '+', '.join(missing))
    samples=[]

    def sample(source_name,test_name,group,note,solid=None,crop=None):
        source=by_name[source_name]
        geometry=source.solid if solid is None else solid
        if geometry.is_empty() or len(geometry.decompose())!=1 or geometry.volume()<=0:
            raise ValueError(test_name+': cropped sample is not one connected positive-volume solid')
        orientation=None if source.orientation is None else np.asarray(source.orientation).copy()
        tags=dict(source.tags)
        tags.update(test=True,purpose='fit_test',production_part=source_name,
                    fit_group=group,geometry='exact production copy' if solid is None else 'production crop')
        if crop is not None:tags['crop']=crop
        result=replace(source,name=test_name,solid=geometry,orientation=orientation,
                       notes=note,tags=tags)
        samples.append(result)
        return result

    # These full parts are small (a few grams together). Retaining the whole
    # inner wall preserves the actual seating lands, both pin positions and the
    # integral base key, and avoids adding a new coupon-only backing plate.
    sample('tail_A_cream_inner','test_tail_A_wall_inner','tail_handrail',
           'Exact v03 tail A inner wall, including inlay seating lands, round/slotted handrail sockets and base key. Print the production glue face down. Dry-fit the matching blue insert and handrail; do not put glue on the seating lands during the test. This full piece may be kept for final assembly if undamaged.')
    sample('tail_A_blue','test_tail_A_blue_insert','tail_handrail',
           'Exact v03 tail A blue insert. It should rest on all three cream seating lands without rocking. Its larger openings must clear the handrail shoulders; the blue insert does not locate the pins. Use the intended production blue PLA.')
    sample('tail_A_cream_handrail','test_tail_A_handrail','tail_handrail',
           'Exact v03 tail A handrail. Print its broad front face down and pins up. Seat both shoulders on the cream pads through the blue openings using light finger pressure. Verify repeatable stand-off and removal; do not force a tight pin. Test with the matching wall and blue insert together.')

    sample('tail_threshold_landing','test_tail_threshold_landing','tail_rung_landing',
           'Exact v03 threshold, printed ground face down. Test with the cropped rung18 lower section: its flat sole should sit on the landing while the raised side relief remains free. Check a small horizontal movement, not an interference fit. Keep as a final assembly piece if undamaged.')
    # Only the actual mating lower section is needed. The crop plane is well
    # above the 2.4 mm threshold, leaving the complete sole and relief surfaces.
    rung=by_name['body_hoop_18'].solid.trim_by_plane((0,0,-1),-5.0)
    sample('body_hoop_18','test_tail_rung18_lower','tail_rung_landing',
           'Actual rung18 geometry below assembly Z5.0, including the whole flat sole and threshold contact region. Keep the production rear-flat print orientation. Place the sole on the matching landing and check that the sides do not bind. Cropped test piece only; do not use it as a full production rung.',
           rung,{'assembly_z_max_mm':5.0})

    # Include the bottom frame crossbar and both feet so the frame coupon stays
    # one connected part. Two full tread seats fit below the halfway plane
    # between production tread positions 2 and 3; no test-only connector is added.
    start=np.array([35,-13.8,1.3])*F
    end=np.array([62,-13.8,40])*F
    tangent=(end-start)/np.linalg.norm(end-start)
    cut=start+(end-start)*.25
    plane=-float(np.dot(tangent,cut))
    crop={'assembly_plane_normal':(-tangent).tolist(),
          'assembly_plane_offset_mm':plane,'retained_treads':[1,2],
          'retained_frame':'bottom crossbar, feet and first two open seats'}
    frame=by_name['ladder_blue_frame'].solid.trim_by_plane(tuple(-tangent),plane)
    comb=by_name['ladder_cream_tread_comb'].solid.trim_by_plane(tuple(-tangent),plane)
    sample('ladder_blue_frame','test_ladder_lower_frame','ladder_two_treads',
           'Actual lower production frame, including both feet, bottom crossbar and first two open tread seats. Keep the production orientation, supports and brim so the test reproduces supported mating surfaces. After cleanup, slide the matching two-tread comb horizontally from the headward side at final height; do not insert vertically or perpendicular to the ladder plane.',
           frame,crop)
    sample('ladder_cream_tread_comb','test_ladder_two_tread_comb','ladder_two_treads',
           'Actual first two production treads and their connected spine, cropped with the same plane as the frame sample. Keep the production supported orientation. At final tread height, slide horizontally from the headward (+X) side toward the frame (-X). It should seat and withdraw without twisting, flexing the frame or scraping a supported face.',
           comb,crop)

    info={'metadata':{
        'purpose':'Real production-interface tests before the full v03 kit. All samples preserve production orientations, colours and support requirements.',
        'piece_count':len(samples),
        'groups':[
            {'name':'tail_handrail','parts':['test_tail_A_wall_inner','test_tail_A_blue_insert','test_tail_A_handrail'],
             'checks':['Blue insert rests on three lands without rocking.','Both handrail shoulders contact cream pads; blue openings remain clearance features.','Pins enter and withdraw with light pressure; rail stand-off is repeatable.'],
             'production_reusable':True},
            {'name':'tail_rung_landing','parts':['test_tail_threshold_landing','test_tail_rung18_lower'],
             'checks':['Rung sole bears on Z0.70 landing.','Raised threshold sides do not bind during insertion or a small horizontal adjustment.'],
             'production_reusable':['test_tail_threshold_landing']},
            {'name':'ladder_two_treads','parts':['test_ladder_lower_frame','test_ladder_two_tread_comb'],
             'checks':['Use the production supports and clean the actual mating surfaces.','Straight horizontal insertion at final height; no narrow vertical-offset manoeuvre.','Seat and remove without forcing or flexing the frame.'],
             'production_reusable':False}],
        'source_rule':'Samples are full production copies or plane crops; no joint dimensions are independently recreated.',
        'ladder_crop_fraction':.25,
        'rung_crop_assembly_z_max_mm':5.0,
        'limitation':'A two-tread sample checks local fit and support cleanup, not accumulated alignment across all nine ladder seats. Dry-fit the final complete comb and frame before glue. No physical print has yet validated these samples.'}}
    return samples,info
