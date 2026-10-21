#!/usr/bin/env python3
"""Screen the actual tail STLs for printing overhangs; does not prove print success.

Run using .venv-print/bin/python. Manifold3D supplies horizontal sections and
Shapely supplies planar overlap tests, so SciPy is not required. STL coordinates
are used directly: exported print orientation and millimetres, not assembly pose.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import manifold3d as m3d
import numpy as np
import trimesh
from shapely.geometry import GeometryCollection, Polygon
from shapely import make_valid

ROOT = Path(__file__).resolve().parents[1]


def section_geometry(solid: m3d.Manifold, z: float):
    # Contours include both outer boundaries and holes. Even-odd combination
    # preserves holes without relying on their winding direction.
    result = GeometryCollection()
    for points in solid.slice(float(z)).to_polygons():
        if len(points) >= 3:
            poly = make_valid(Polygon(np.asarray(points)))
            result = result.symmetric_difference(poly)
    return make_valid(result)


def polygons(geometry):
    if geometry.geom_type == 'Polygon':
        yield geometry
    elif hasattr(geometry, 'geoms'):
        for child in geometry.geoms:
            yield from polygons(child)


def selected(name: str, extra: list[str]) -> bool:
    return (name.startswith('tail_')
            or re.fullmatch(r'body_hoop_(16|17|18)', name) is not None
            or re.fullmatch(r'body_rail_0[1-4]_section_04', name) is not None
            or name == 'body_beam_04'
            or name in extra)


def audit_part(record: dict, directory: Path, layer_height: float,
               first_sample: float, area_threshold: float) -> dict:
    path = directory / record['file']
    mesh = trimesh.load_mesh(path, process=True)
    solid = m3d.Manifold(m3d.Mesh64(
        np.asarray(mesh.vertices, dtype=np.float64),
        np.asarray(mesh.faces, dtype=np.uint64)))
    if solid.status() != m3d.Error.NoError:
        raise ValueError(f'{record["name"]}: {solid.status()}')
    z_min, z_max = mesh.bounds[:, 2]
    sample_z = z_min + min(first_sample, (z_max - z_min) / 2)
    previous = section_geometry(solid, sample_z)
    bed_contact = section_geometry(solid, z_min + 1e-5)
    first_area = previous.area
    bed_components = [g.area for g in polygons(bed_contact)]
    flagged = []
    max_projected_area = 0.0
    island_layer_count = 0
    edge_layer_count = 0
    layer_count = 1
    for z in np.arange(sample_z + layer_height, z_max - 1e-6, layer_height):
        current = section_geometry(solid, z)
        # A 45 degree wall grows one layer height laterally per layer.
        reachable = previous.buffer(layer_height + 1e-5, quad_segs=12)
        excess = current.difference(reachable)
        excess_area = excess.area
        # A new island has effectively zero actual vertical contact with the
        # previous cross-section, even if its outline comes within 45 degrees.
        islands = [float(component.area) for component in polygons(current)
                   if component.area > area_threshold
                   and component.intersection(previous.buffer(1e-5)).area < 1e-5]
        edge_flag = excess_area > area_threshold
        if edge_flag or islands:
            flagged.append({
                'z_mm': round(float(z), 5),
                'beyond_45_degree_projection_mm2': round(excess_area, 6),
                'new_island_areas_mm2': [round(a, 6) for a in islands],
                'projection_bounds_xy_mm': [round(float(v), 5) for v in excess.bounds]
                if edge_flag else [],
            })
        edge_layer_count += bool(edge_flag)
        island_layer_count += bool(islands)
        max_projected_area = max(max_projected_area, excess_area)
        previous = current
        layer_count += 1

    # Faces at the build plane are intentionally excluded. The face test can
    # flag rounded edges even if the section test has adequate prior contact.
    above_bed = np.max(mesh.triangles[:, :, 2], axis=1) > z_min + first_sample
    downward = above_bed & (mesh.face_normals[:, 2] < -math.sqrt(.5) - 1e-5)
    down_area = float(mesh.area_faces[downward].sum())
    down_projected = float((-mesh.face_normals[downward, 2] * mesh.area_faces[downward]).sum())
    declared_support = record.get('supports', 'unspecified')
    support_required = declared_support.lower() != 'none'
    return {
        'part': record['name'],
        'file': record['file'],
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'declared_supports': declared_support,
        'notes': record.get('notes', ''),
        'dimensions_mm': [round(float(v), 5) for v in mesh.extents],
        'watertight': bool(mesh.is_watertight),
        'positive_volume': bool(mesh.volume > 0),
        'connected_components': len(solid.decompose()),
        'bottom_z_mm': round(float(z_min), 6),
        'bed_contact_area_mm2': round(bed_contact.area, 6),
        'bed_contact_component_areas_mm2': [round(a, 6) for a in bed_components],
        'first_sample_area_mm2': round(first_area, 6),
        'sampled_layer_count': layer_count,
        'flagged_layer_count': len(flagged),
        'beyond_45_degree_layer_count': edge_layer_count,
        'max_projection_area_mm2': round(max_projected_area, 6),
        'new_island_layer_count': island_layer_count,
        'downward_over_45_degree_face_area_mm2': round(down_area, 6),
        'downward_over_45_degree_projected_area_mm2': round(down_projected, 6),
        'unresolved_support_free_flag': bool(not support_required and (flagged or down_area > area_threshold)),
        'layers': flagged,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', nargs='?', type=Path,
                        default=ROOT / 'exports/dragon-pla-kit-v02/manifest.json')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--layer-height', type=float, default=.16)
    parser.add_argument('--first-sample', type=float, default=.10)
    parser.add_argument('--area-threshold', type=float, default=.02)
    parser.add_argument('--include', action='append', default=[],
                        help='Additional exact part name to audit; repeat as needed.')
    args = parser.parse_args()
    manifest_path = args.manifest.resolve()
    manifest = json.loads(manifest_path.read_text())
    records = [p for p in manifest['parts'] if selected(p['name'], args.include)]
    if not records:
        raise ValueError('No tail parts matched the requested manifest.')
    results = []
    for record in records:
        result = audit_part(record, manifest_path.parent, args.layer_height,
                            args.first_sample, args.area_threshold)
        results.append(result)
        print(f"{result['part']}: {result['flagged_layer_count']} flagged layers; "
              f"{result['new_island_layer_count']} new-island layers; "
              f"max projection {result['max_projection_area_mm2']:.3f} mm²; "
              f"bed contact {result['bed_contact_area_mm2']:.2f} mm²", flush=True)
    report = {
        'manifest': str(manifest_path),
        'manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        'method': {
            'geometry': 'Actual exported individual STL in supplied print orientation.',
            'layer_height_mm': args.layer_height,
            'first_sample_above_bottom_mm': args.first_sample,
            'projection_area_threshold_mm2': args.area_threshold,
            'edge_growth_angle_deg_from_vertical': 45,
            'new_island_contact_area_threshold_mm2': 1e-5,
            'limits': 'Geometric heuristic only. Does not simulate extrusion, bridge anchoring, cooling, support contacts or support removal; does not prove physical printing or fit.',
        },
        'part_count': len(results),
        'unresolved_support_free_parts': [r['part'] for r in results if r['unresolved_support_free_flag']],
        'parts': results,
    }
    output = args.output or manifest_path.parent / 'validation/tail-v02-print-audit.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(f'Wrote {output}')


if __name__ == '__main__':
    main()
