"""V04 softer toy-like Toa Payoh head; coordinates are raw millimetres.

The approved sparse-soft-ribs-v2 image supplies the design and proportions.
The photographed playground informs connections and the paired-panel splay.
V04 rebalances the entire lower head: continuous cream mouth backing,
a deeper jaw and a fuller cheek-to-neck transition. Foot width is retained.
This is a visual prototype, not a certified printable part. Importing this
module has no scene effects; v03 is retained in blender_head_v03.py.
"""

from math import cos, sin, pi, sqrt


# Continuous cream backing: the photographed mouth is a cream graphic, not
# a hole. The broad jaw and flared neck carry the same weight as the foot.
HEAD_PROFILE = (
    (40.0, 82.0), (49.5, 82.0), (64.5, 64.0),
    (71.0, 64.0), (71.0, 76.0), (79.0, 76.0),
    (94.0, 59.0), (102.0, 59.0), (104.5, 62.0),
    (108.0, 62.0), (112.0, 57.0), (112.0, 44.0),
    (109.0, 30.0), (107.0, 24.0), (100.0, 24.0),
    (96.0, 29.0), (91.0, 29.0),
    (91.0, 0.0), (74.0, 0.0), (73.0, 24.0),
    (68.0, 32.0), (60.0, 43.0), (59.0, 49.0),
    (57.0, 53.0), (62.0, 58.0), (54.5, 64.0), (40.0, 74.0),
)

# The inward zigzag leaves solid cream backing visible as the mouth marking.
# The lower orange jaw is broad, joining the cheek and foot without a thin lip.
FACE_PROFILE = (
    (42.8, 79.2), (48.2, 79.2), (63.2, 61.2),
    (73.8, 61.2), (73.8, 73.2), (77.7, 73.2),
    (92.7, 56.2), (103.3, 56.2), (105.9, 59.2),
    (106.7, 59.2), (109.2, 56.2), (109.2, 45.5),
    (107.0, 43.0), (102.0, 43.0), (98.0, 47.0),
    (91.5, 47.0), (94.0, 40.0), (99.0, 37.0),
    (107.5, 34.5), (105.0, 27.0), (101.0, 27.0),
    (97.1, 31.8), (88.2, 31.8),
    (88.2, 2.8), (76.8, 2.8), (75.8, 24.9),
    (70.4, 33.6), (62.7, 44.0), (61.7, 49.8), (60.4, 53.2),
    (65.7, 58.0), (56.5, 66.1), (42.8, 75.1),
)

# Slightly rearward/below the initial blockout target keeps the whole cream
# eye surround inside the orange cheek rather than merging into the brow.
EYE_CENTRE = (83.0, 51.8)
EYE_RADIUS = 6.5
SPLAY_SLOPE = 0.55
PANEL_THICKNESS = 4.8
# Inlays and surrounds intentionally overlap the backing slightly. Derive their
# depth from panel thickness so further thickness edits cannot leave them buried.
FACE_OVERLAP = 0.25
FACE_RELIEF = 0.55
EYE_SURROUND_RELIEF = 0.85


def _ccw(points):
    points = list(points)
    area2 = sum(a[0] * b[1] - b[0] * a[1]
                for a, b in zip(points, points[1:] + points[:1]))
    return points if area2 > 0 else points[::-1]


def _world(x, z, normal_distance, side):
    """Place a profile on its splayed plane, then offset along its true normal."""
    norm = sqrt(1.0 + SPLAY_SLOPE * SPLAY_SLOPE)
    return (x + normal_distance * SPLAY_SLOPE / norm,
            side * (9.0 + (96.0 - x) * SPLAY_SLOPE)
            + normal_distance * side / norm,
            z)


def _mesh_object(ctx, name, vertices, faces, material=None):
    bpy = ctx['bpy']
    mesh = bpy.data.meshes.new(name + '_Mesh')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    # Triangulate the two concave profile caps explicitly before eye Booleans.
    # This avoids unstable large-ngon triangulation after lower-foot edits.
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    ctx['collection'].objects.link(obj)
    if material is not None:
        mesh.materials.append(material)
    obj['component'] = 'paired_splayed_dragon_head'
    obj['source_units'] = 'millimetres'
    return obj


def _prism(ctx, name, profile, side, lo, hi, material=None):
    points = _ccw(profile)
    count = len(points)
    vertices = [_world(x, z, d, side)
                for d in (lo, hi) for x, z in points]
    faces = [tuple(range(count - 1, -1, -1)),
             tuple(range(count, 2 * count))]
    faces += [(i, (i + 1) % count, (i + 1) % count + count, i + count)
              for i in range(count)]
    # In (X,Z) coordinates a CCW cap points inward on the positive-Y panel.
    if side > 0:
        faces = [tuple(reversed(face)) for face in faces]
    return _mesh_object(ctx, name, vertices, faces, material)


def _octagon(radius):
    x, z = EYE_CENTRE
    return [(x + radius * cos(pi / 8 + i * pi / 4),
             z + radius * sin(pi / 8 + i * pi / 4)) for i in range(8)]


def _ring(ctx, name, side, lo, hi, material):
    """A manifold annular octagonal prism, leaving the eye genuinely open."""
    outer, inner = _octagon(9.0), _octagon(EYE_RADIUS)
    vertices = [_world(x, z, d, side)
                for d in (lo, hi) for loop in (outer, inner) for x, z in loop]
    faces = []
    for i in range(8):
        j = (i + 1) % 8
        faces += [(i, j, j + 16, i + 16),
                  (i + 8, i + 24, j + 24, j + 8),
                  (i + 16, j + 16, j + 24, i + 24),
                  (i + 8, j + 8, j, i)]
    if side > 0:
        faces = [tuple(reversed(face)) for face in faces]
    return _mesh_object(ctx, name, vertices, faces, material)


def _soften(obj, width, segments=4):
    bevel = obj.modifiers.new('Soft rounded edges', 'BEVEL')
    bevel.width = width
    bevel.segments = segments
    bevel.use_clamp_overlap = True
    if hasattr(bevel, 'harden_normals'):
        bevel.harden_normals = True


def _cut_eye(obj, cutter):
    mod = obj.modifiers.new('True octagonal eye aperture', 'BOOLEAN')
    operation_ids = {item.identifier
                     for item in mod.bl_rna.properties['operation'].enum_items}
    if 'DIFFERENCE' in operation_ids:
        mod.operation = 'DIFFERENCE'
    mod.object = cutter
    if hasattr(mod, 'solver'):
        solver_ids = {item.identifier
                      for item in mod.bl_rna.properties['solver'].enum_items}
        if 'EXACT' in solver_ids:
            mod.solver = 'EXACT'


def build_head(ctx):
    """Build head only; requires bpy, collection and cream/orange/blue materials.

    Returns visible objects and hidden edit-friendly cutters. Parent code owns
    the head platform, slides, ladder, body, base, units, lights and cameras.
    The panel centre lines converge at the snout: their small overlap there is
    intentional in this visual prototype, and is not a resolved print joint.
    """
    bpy = ctx['bpy']
    materials = ctx['materials']
    for obj in list(ctx['collection'].objects):
        if obj.name.startswith('HEAD_'):
            bpy.data.objects.remove(obj, do_unlink=True)

    visible, cutters = [], []
    half_thickness = PANEL_THICKNESS / 2
    cutter_depth = half_thickness + EYE_SURROUND_RELIEF + 4.0
    for side, label in ((1, 'A'), (-1, 'B')):
        cutter = _prism(ctx, 'HEAD_' + label + '_EyeCutter', _octagon(EYE_RADIUS),
                        side, -cutter_depth, cutter_depth)
        display_ids = {item.identifier for item in
                       cutter.bl_rna.properties['display_type'].enum_items}
        if 'WIRE' in display_ids:
            cutter.display_type = 'WIRE'
        cutter.hide_render = True
        cutter.hide_set(True)
        cutter['purpose'] = 'Non-rendering cutter; keep for editable through-eye'
        cutters.append(cutter)

        backing = _prism(ctx, 'HEAD_' + label + '_CreamPanel', HEAD_PROFILE,
                         side, -PANEL_THICKNESS / 2, PANEL_THICKNESS / 2,
                         materials['cream'])
        backing['panel_splay'] = 'y = side * (9 + (96 - x) * 0.55)'
        backing['height_mm'] = 82.0
        backing['thickness_mm'] = PANEL_THICKNESS
        # Round the silhouette before the aperture cut; tiny Boolean edges
        # must not clamp the bevel radius for the whole head.
        _soften(backing, 1.25, 5)
        _cut_eye(backing, cutter)

        orange = _prism(ctx, 'HEAD_' + label + '_OrangeExterior', FACE_PROFILE,
                        side, half_thickness - FACE_OVERLAP,
                        half_thickness + FACE_RELIEF, materials['orange'])
        _soften(orange, 0.35, 4)
        _cut_eye(orange, cutter)

        blue = _prism(ctx, 'HEAD_' + label + '_BlueInterior', FACE_PROFILE,
                      side, -half_thickness - FACE_RELIEF,
                      -half_thickness + FACE_OVERLAP, materials['blue'])
        _soften(blue, 0.35, 4)
        _cut_eye(blue, cutter)

        front_rim = _ring(ctx, 'HEAD_' + label + '_OuterEyeSurround', side,
                          half_thickness - FACE_OVERLAP,
                          half_thickness + EYE_SURROUND_RELIEF,
                          materials['cream'])
        inner_rim = _ring(ctx, 'HEAD_' + label + '_InnerEyeSurround', side,
                          -half_thickness - EYE_SURROUND_RELIEF,
                          -half_thickness + FACE_OVERLAP, materials['cream'])
        _soften(front_rim, 0.38, 4)
        _soften(inner_rim, 0.38, 4)
        visible.extend([backing, orange, blue, front_rim, inner_rim])

    return {'objects': visible, 'cutters': cutters,
            'eye_centre_xz': EYE_CENTRE, 'eye_radius': EYE_RADIUS,
            'panel_thickness': PANEL_THICKNESS,
            'splay_slope': SPLAY_SLOPE,
            'design_bounds_xz': ((40.0, 112.0), (0.0, 82.0))}
