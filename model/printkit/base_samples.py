"""Actual tray/sand/slide interface crops, plus labelled fixture context."""
import numpy as np
from .common import Part, box, union, to_trimesh


def build(parts):
    by={p.name:p for p in parts};samples=[];records=[]
    def add(name,source,window,notes,fixture=False):
        p=by[source];solid=p.solid^window
        pieces=sorted(solid.decompose(),key=lambda item:abs(item.volume()),reverse=True)
        assert pieces and sum(abs(item.volume()) for item in pieces[1:])<1e-5,(name,'material disconnected after crop')
        solid=pieces[0]
        if fixture:
            # Tiny positive pads reproduce the production sand's Z=-2 datum
            # when a small crop omits its distant perimeter/bearing pads.
            bb=np.asarray(solid.bounding_box());x0,y0=bb[:2];x1,y1=bb[3:5]
            for x,y in [(x0+1,y0+1),(x1-1,y0+1),(x0+1,y1-1),(x1-1,y1-1)]:
                solid=union(solid,box((x,y,-1.9),(1.5,1.5,.2)))
        assert not solid.is_empty() and len(solid.decompose())==1,(name,'sample invalid')
        samples.append(Part(name,p.color,solid,p.orientation,notes,p.supports,
                            {'test':True,'purpose':'fit_test','production_part':source,
                             'fixture_context':'Four 1.5 mm bearing pads restore the sand datum; holes are unchanged.' if fixture else 'Unmodified crop of production part'}))
        records.append({'name':name,'production_part':source,'notes':notes})
    window=box((88,17,-1),(25,19,16))
    add('test_head_A_tray','base_right_tray',window,'Pair with test_head_A_sand and the head A D-foot sample. Seat sand, then lower the whole D-pins through the larger passages into the tray. The cream foot shoulder should meet the sand without rocking.')
    add('test_head_A_sand','base_right_sand',window,'Actual head-A sand passages; four small carrier pads preserve the full insert bearing height. Visible face down, sockets up.',True)
    # An actual base joining pocket, on both sides of the seam.
    window=box((5.348270507,-40,-3.5),(26,16,10))
    for side in ['left','right']:
        add('test_base_join_'+side,'base_'+side+'_tray',window,'Close the matching two flat seam faces completely, then drop in the production-shaped join key from the open top. Flat faces set the seam; the key is a glue locator.')
    key=by['base_join_key_01']
    samples.append(Part('test_base_join_key','cream',key.solid,key.orientation,key.notes,key.supports,{'test':True,'purpose':'fit_test','production_part':key.name}))
    # Registration uses the actual round boss/socket. The long-slot allowance
    # remains digitally checked on the full 120 mm pitch, rather than shortened.
    window=box((62,-35,-3),(14,14,10))
    add('test_sand_register_tray','base_right_tray',window,'Actual round sand registration boss. Pair with test_sand_register_insert; it should seat fully with light finger pressure.')
    add('test_sand_register_insert','base_right_sand',window,'Actual blind registration socket. Small carrier pads reproduce the production underside datum. Print ground face down.',True)
    for label,source in [('shell','slide_2_cream'),('insert','slide_2_orange_left')]:
        original=by[source]
        note='Exact full production slide2 '+label+' in the actual colour and supported orientation; reusable in the final model. Test the complete rigid insertion path and seating lands after carefully removing supports. Keep dry until the fit is accepted.'
        samples.append(Part('test_slide_2_'+label,original.color,original.solid,original.orientation,note,original.supports,
                            {'test':True,'purpose':'fit_test','production_part':source,'geometry':'full reusable production copy'}))
        records.append({'name':'test_slide_2_'+label,'production_part':source,'notes':note})
    return samples,{'metadata':{'samples':records,'limits':'Actual joint surfaces and production print orientations; cut fixture edges are not cosmetic previews. The complete assembly still needs a physical dry fit.'}}
