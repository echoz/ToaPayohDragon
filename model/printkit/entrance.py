"""Tail entrance and ladder manufactured as glued single-colour PLA components."""
import math
import numpy as np
import manifold3d as m3d
from shapely.geometry import Polygon,Point,LineString,box as poly_box
from .common import F,Part,union,box,prism,cylinder_between,frame_rotation,sample_route,spline,to_trimesh

UP=np.array([0.,0.,1.])


def tube(points,radius):
    points=np.asarray(points,float)
    return union(*[cylinder_between(a,b,radius,24) for a,b in zip(points[:-1],points[1:])],
                 *[m3d.Manifold.sphere(radius,20).translate(p) for p in points])


def build():
    parts=[];p,t,n=sample_route(1)
    # Centre the straight paired walls on the short descending entrance run.
    # Its chord remains aligned when the route eases away from the slide.
    uphill=sample_route(15/17)[0]
    u=uphill-p;u[2]=0;u/=np.linalg.norm(u)
    n=np.cross(u,UP)
    origin=np.array([p[0],p[1],0.])
    # Final-mm, photo-informed crest: tall entrance, pronounced near-entry
    # peak, then a swept shoulder beside the final three open U-rungs.
    outline=Polygon([(-5,0),(43,0),(43,33.5),(32,33.5),(21,35.0),
                     (10,39.5),(2,32),(-5,25)])
    outline=outline.buffer(-.45,join_style='round').buffer(.45,join_style='round')
    plain_colour=outline.buffer(-2.1,join_style='mitre')
    # Two cream wedges cut into one connected orange flame. The inside keeps
    # the solid blue field visible in the entrance photographs.
    flame=plain_colour.difference(Polygon([(1,-2),(11,-2),(13,16.5),(7.2,21),(9,10)]))
    flame=flame.difference(Polygon([(46,20),(46,28.5),(27,28.5),(36.5,24.4)]))
    flame=flame.buffer(-.18,join_style='round').buffer(.18,join_style='round')
    assert flame.geom_type=='Polygon' and not flame.is_empty
    half=2.4;offset=16.3
    tail_slot=poly_box(-.15,-.20,3.4,2.60)
    post_centres=[(0,20.5),(30,31.0)]
    pitch=np.asarray(post_centres[1])-np.asarray(post_centres[0]);pitch/=np.linalg.norm(pitch)
    def post_shape(index,radius):
        centre=np.asarray(post_centres[index])
        if index==0:return Point(centre).buffer(radius,quad_segs=12)
        return LineString([centre-pitch*.30,centre+pitch*.30]).buffer(radius,cap_style='round',quad_segs=12)
    # Blue is a clearance skin, never the locator. A 3.6 mm shoulder passes
    # through a 4.8 mm opening (0.6 nominal radial; about 0.45 after insert drift).
    blue_apertures=post_shape(0,2.4).union(post_shape(1,2.4))
    base_cutters=[];sand_cutters=[]
    # The rail is a planar 2.9 mm rounded ribbon. The two locating posts grow
    # perpendicular to its flat printed face, so neither requires supports.
    rail_path=LineString([(0,22.5),(8,26.1),(20,30.9),(32,34.3)])
    rail_profile=rail_path.buffer(1.45,cap_style='round',join_style='round')
    for foot,top in zip(post_centres,[(0,22.5),(32,34.3)]):
        rail_profile=rail_profile.union(LineString([foot,top]).buffer(1.45,cap_style='round')).union(Point(foot).buffer(1.85,quad_segs=12))
    for sign,label in ((1,'A'),(-1,'B')):
        c=sign*offset
        def panel(poly,lo,hi):return prism(poly,c+lo,c+hi,origin,u,UP,n)
        def lateral(poly,lo,hi):
            a,b=sorted((sign*lo,sign*hi))
            return prism(poly,a,b,origin,u,UP,n)
        cream=panel(outline,-half,half)
        orange=panel(flame,sign*(half+.30)-(.0 if sign<0 else 1.2),sign*(half+.30)+(.0 if sign>0 else 1.2))
        blue_shape=plain_colour.difference(tail_slot.buffer(.15,join_style='mitre')).difference(blue_apertures)
        blue=panel(blue_shape,-sign*(half+.30)-(.0 if sign>0 else 1.2),-sign*(half+.30)+(.0 if sign<0 else 1.2))
        # Different outside/inside motifs have separate shallow recesses.
        for shape,side in [(flame,sign),(blue_shape,-sign)]:
            cutshape=shape.buffer(.15,join_style='round')
            lo,hi=(half+.30-1.2-.20,half+1) if side>0 else (-half-1,-half-.30+1.2+.20)
            cream=cream-panel(cutshape,lo,hi)
            # Three non-collinear pads stop the insert at its intended back
            # plane. The surrounding recess retains 0.20 mm adhesive space.
            points=[(-1,16),(21,7),(29,20)] if side==sign else [(-1,7),(18,10),(34,23)]
            for x,z in points:
                land=Point(x,z).buffer(1.2,quad_segs=12)
                assert shape.contains(land),(label,side,x,z,'inlay seating land outside insert')
                a,b=(1.25,1.50) if side>0 else (-1.50,-1.25)
                cream=union(cream,panel(land,a,b))
        # Inner bottom socket accepts the threshold tongue by vertical drop.
        slo,shi=(-half-.1,-half+1.35) if sign>0 else (half-1.35,half+.1)
        cream=cream-panel(tail_slot,slo,shi)
        rail=lateral(rail_profile,10.8,13.2)
        for index,(x,z) in enumerate(post_centres):
            # Shoulder bears on a cream pad left behind by the larger blue
            # aperture; it fixes the rail back at 13.2, 0.4 off the blue face.
            shoulder=lateral(Point(x,z).buffer(1.8,quad_segs=12),13.1,13.9)
            pin=lateral(Point(x,z).buffer(1.30,quad_segs=12),13.8,15.4)
            rail=union(rail,shoulder,pin)
            cream=cream-lateral(post_shape(index,1.45),13.7,15.6)
        # One whole key belongs to each inner half. Its broad print face is
        # coplanar with the central glue face: no first-layer floating peg.
        key_profile=Polygon([(4,.8),(8,.8),(8,-3.8),(7.6,-4.2),(4.4,-4.2),(4,-3.8)])
        foot_key=lateral(key_profile,14.3,16.3)
        key_plan=poly_box(4-.15,14.3-.15,8+.15,16.3+.15)
        sand_plan=poly_box(4-.50,14.3-.50,8+.50,16.3+.50)
        if sign<0:
            from shapely.affinity import scale
            key_plan=scale(key_plan,xfact=1,yfact=-1,origin=(0,0))
            sand_plan=scale(sand_plan,xfact=1,yfact=-1,origin=(0,0))
        base_cutters.append(prism(key_plan,-4.4,.2,origin,u,n,UP))
        sand_cutters.append(prism(sand_plan,-2.1,.2,origin,u,n,UP))
        outward=n*sign
        rot_out=frame_rotation(u*sign,UP,outward)
        rot_in=frame_rotation(-u*sign,UP,-outward)
        upper=panel(poly_box(-100,-100,100,100),0,10)
        lower=panel(poly_box(-100,-100,100,100),-10,0)
        outer_half=cream^(upper if sign>0 else lower)
        inner_half=union(cream^(lower if sign>0 else upper),foot_key)
        for name,color,solid,rot,note in [
            (f'tail_{label}_cream_outer','cream',outer_half,rot_out,'Print broad central glue face down; angular orange pocket up. Glue to matching inner half and align the full crest outline.'),
            (f'tail_{label}_cream_inner','cream',inner_half,rot_in,'Print broad central glue face down; blue pocket and two handrail sockets up. Bottom notch fits the cream threshold tongue.'),
            (f'tail_{label}_orange','orange',orange,rot_out,'One connected 1.2 mm flat flame insert, with two angular cream wedges visible through its edge notches. Rest on its three cream seating lands; put glue only in the lower recess, not on the lands.'),
            (f'tail_{label}_blue','blue',blue,rot_in,'1.2 mm flat inside insert. Oversized openings clear handrail shoulders; cream pads locate the pins. Rest on its three cream seating lands; put glue only in the lower recess, not on the lands. Align the threshold notch before gluing.'),
            (f'tail_{label}_cream_handrail','cream',rail,rot_out,'Print the broad flat front face down and posts up. First round cream socket locates; second slotted cream socket allows pitch error. Press both shoulders onto the cream pads through the oversized blue openings; 1.5 mm cream engagement and 0.2 mm blind-end reserve.')]:
            parts.append(Part(name,color,solid,rot,note,tags={'family':'tail','side':label}))
    # Low centre meets rung18's flat sole; wings locate the wider sidewalls.
    inside=offset-half-.30-.15
    plan=poly_box(-3.1,-inside,3.1,inside)
    threshold=prism(plan,0,.70,origin,u,n,UP)
    for sign in [-1,1]:
        wing=poly_box(-3.1,4.1,3.1,inside) if sign>0 else poly_box(-3.1,-inside,3.1,-4.1)
        tongue=poly_box(0,inside-.1,3.2,offset-half+1.15) if sign>0 else poly_box(0,-offset+half-1.15,3.2,-inside+.1)
        threshold=union(threshold,prism(wing,0,2.4,origin,u,n,UP),prism(tongue,0,2.4,origin,u,n,UP))
    parts.append(Part('tail_threshold_landing','cream',threshold,None,
                      'Print flat ground face down. Drop the two assembled tail walls onto the side tongues. Centre landing at Z0.70 receives open rung18 flat sole; glue all three to the base.',tags={'family':'tail'}))

    # Ladder geometry is kept on the approved route; the original loose rails
    # gain posts and the treads become a single manageable cream comb.
    start=np.array([35,-13.8,1.3])*F;end=np.array([62,-13.8,40])*F
    tangent=(end-start)/np.linalg.norm(end-start);across=np.array([0.,1.,0.]);back=np.cross(tangent,across)
    orient=frame_rotation(tangent,across,back)
    blue=[];yoff=3.1*F
    for sign in [-1,1]:
        off=np.array([0.,sign*yoff,0.])
        blue.append(cylinder_between(start+off,end+off,1.5))
        blue.append(box((start[0],start[1]+off[1],.80),(3.5,3.1,1.6)))
        lower=start+(end-start)*.5+off
        railtop=end+off+np.array([0,0,8])*F
        railpoints=[lower+np.array([0,0,7])*F,railtop,railtop+np.array([3,0,0])*F,end+off+np.array([4,0,0])*F]
        blue.append(tube(spline(railpoints,10),1.05))
        blue.append(cylinder_between(lower,railpoints[0],1.1))
        blue.append(cylinder_between(end+off,railpoints[-1],1.15))
    for a in [start,end]:blue.append(cylinder_between(a+np.array([0,-yoff,0]),a+np.array([0,yoff,0]),1.25))
    frame=union(*blue)
    steps=[];clearances=[];centres=[]
    for j in range(1,10):
        at=start+(end-start)*j/10;centres.append(at)
        steps.append(box(at,(3.6*F,5.8,1.6)))
        clearances.append(box(at+np.array([6,0,0]),(3.6*F+.60+12,5.8+.60,2.2)))
    spine_a=centres[0]+np.array([0,0,-.80]);spine_b=centres[-1]+np.array([0,0,-.80])
    comb=union(*steps,cylinder_between(spine_a,spine_b,1.0))
    frame=frame-union(*clearances)
    # All nine seats are open toward +world X with 0.30 mm per-side clearance.
    # This is a real straight horizontal approach, not a nominal static fit.
    # The central spine also has a swept clearance volume in this approach.
    spine_clearance=union(*[cylinder_between(spine_a+np.array([x,0,0]),spine_b+np.array([x,0,0]),1.30)
                           for x in np.linspace(0,12,41)])
    frame=frame-spine_clearance
    parts.append(Part('ladder_blue_frame','blue',frame,orient,
                      '3.0 mm stringers, 2.1 mm handrails, joined posts and end crossbars. Seats open horizontally toward +X in assembly coordinates. Slide the cream comb in along -X at its final height; 0.30 mm nominal approach clearance. Keep the supplied supported orientation.',
                      'Required: removable supports under raised handrails and tread seats.',{'family':'ladder'}))
    parts.append(Part('ladder_cream_tread_comb','cream',comb,orient,
                      'Nine 1.6 mm treads joined by a hidden 2 mm spine. After cleaning supports, approach horizontally from the headward (+X) side and slide along -X at final height into the open seats. Dry-fit before glue; do this before installing the ladder on the base.',
                      'Required: removable supports under stair tread overhangs.',{'family':'ladder'}))
    from .body import build as body_build
    from .head import build as head_build
    body_parts,_=body_build();head_parts,_=head_build()
    tail_obstacles=union(*[part.solid for part in body_parts if part.name=='body_hoop_18'])
    clearance_offsets=[(.20,0,0),(-.20,0,0),(0,.20,0),(0,-.20,0),(0,0,.20),(0,0,-.20)]
    head_obstacles=union(*[p.solid for p in head_parts])
    # A box dilation guarantees at least 0.20 mm separation in every
    # direction, unlike a union of six shifted copies near thin edges.
    bounds=np.asarray(frame.bounding_box())
    window=box((bounds[:3]+bounds[3:])/2,bounds[3:]-bounds[:3]+1.0)
    head_clearance=(head_obstacles^window).minkowski_sum(box((0,0,0),(.4,.4,.4)))
    for part in parts:
        if part.name=='tail_threshold_landing':
            # Preserve the complete Z0.70 bearing, but add real horizontal
            # side clearance above it. The upper 0.35 mm has a wider entry
            # relief so the descending rung finds the seat without binding.
            side_kernel=m3d.Manifold.cylinder(.0002,.201,.201,48).translate((0,0,-.0001))
            entry_kernel=m3d.Manifold.cylinder(.0002,.401,.401,48).translate((0,0,-.0001))
            sides=tail_obstacles.minkowski_sum(side_kernel).trim_by_plane((0,0,1),.70)
            entry=tail_obstacles.minkowski_sum(entry_kernel).trim_by_plane((0,0,1),2.05)
            part.solid=part.solid-union(sides,entry)
        elif part.name=='ladder_blue_frame':
            part.solid=part.solid-head_clearance
        part.solid=part.solid.simplify(1e-4)
    return parts,{'base_socket_cutters':base_cutters,'sand_clearance_cutters':sand_cutters,
                  'metadata':{'tail_inlay_mm':1.2,'tail_clearance_per_side_mm':.15,'tail_inlay_glue_gap_mm':.20,'tail_inlay_seating_lands':3,'tail_inlay_land_diameter_mm':2.4,
                              'tail_landing_top_mm':.70,'tail_wall_cream_mm':4.8,
                              'tail_wall_peak_mm':39.5,'tail_wall_length_mm':48,
                              'tail_wall_inner_blue_face_lateral_mm':13.6,
                              'tail_handrail_depth_mm':2.4,'tail_handrail_ribbon_width_mm':2.9,
                              'tail_handrail_post_diameter_mm':2.6,'tail_handrail_socket_diameter_mm':2.9,
                              'tail_handrail_second_socket_pitch_freedom_mm':.6,'tail_handrail_cream_engagement_mm':1.5,
                              'tail_handrail_bottom_reserve_mm':.2,'tail_handrail_shoulder_diameter_mm':3.6,
                              'tail_handrail_blue_opening_diameter_mm':4.8,'tail_handrail_standoff_mm':.4,
                              'tail_rung_side_clearance_mm':.2,'tail_rung_entry_clearance_mm':.4,
                              'tail_keys':[{'side':side,'local_u_mm':6,'size_mm':[4,2,4.2],'base_socket_mm':[4.3,2.3,4.4],'sand_opening_mm':[5,3]} for side in ['A','B']],
                              'tail_wall_assembly':'four cream half panels laminated in pairs; two blue and two angular orange inserts; two separate flat-printing cream handrails with locating posts',
                              'ladder_treads':9,'ladder_tread_thickness_mm':1.6,'ladder_blue_stringer_diameter_mm':3.0,'ladder_tread_width_mm':5.8,'ladder_seat_clearance_per_side_mm':.30,
                              'ladder_rail_diameter_mm':2.1,'ladder_assembly':'straight horizontal comb insertion from +X toward -X at final height; nominal 0.30 mm clearance. Glue lower feet to sand and upper frame via accessible glue pads; do not force against head.'}}

if __name__=='__main__':
    import json
    from .common import ROOT,save_debug
    parts,info=build()
    print(json.dumps(save_debug(parts,ROOT/'exports/dragon-pla-kit/work/entrance-debug'),indent=2))
