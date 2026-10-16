"""Bake grounded, fully textured courtyard surfaces over the supplied island.

Every polygon is clipped from an original upward scan triangle, including its
height and source UVs. The visual skin sits 6 mm above that source plane and has
no collider. Native scan collision, vertical walls and travel anchors stay
authoritative. Existing CC0 2K maps are referenced at metre scale, never enlarged.
Use --check to regenerate in memory and verify every committed output byte.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.spatial import ConvexHull

from author_environment_dressing import OFFSET, SOURCE, native_mesh
from geometry import Mesh
import unity_writer as u

ROOT = Path(__file__).resolve().parents[1]
BASE = 'Assets/Game/Alcatraz/Resources/Alcatraz/CourtyardSurfaces'
NORMAL_Y = .80
OFFSET_METRES = .006
SEAM_OFFSET_METRES = .0066
MAX_SOURCE_ERROR = .01
TEXTURE_REPEAT_METRES = 2.
JOINT_PITCH = 3.
JOINT_WIDTH = .018
WALL_CLEARANCE = .50
MIN_WALL_HEIGHT = 1.
WALL_FOOTPRINT_RADIUS = .52
WALL_FOOTPRINT_SIDES = 16
# These are independent floors, not a flat connecting plaza. The lower east
# edge stays west of the source retaining wall x ~= -141.9 - .162 z.
REGIONS = [
    {'name': 'ArrivalCourt', 'height': [29.5, 33.5],
     'polygon': [[-168.5, -14.], [-141.0, -14.], [-146.4, 19.], [-168.5, 19.]],
     'material': 'ArrivalWornConcrete'},
    {'name': 'CellhouseGateWalk', 'height': [48., 50.5],
     'polygon': [[-121., 17.5], [-119., 17.5], [-99.5, 29.5],
                 [-100.5, 32.], [-119.5, 23.]],
     'material': 'GateBrushedConcrete'},
]
HELIPAD_BOUNDS = [-157.35, -144.65, -11.35, 1.35]


def sha(path):
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


def clip(poly, value):
    """Sutherland-Hodgman half-plane clip, interpolating XYZ and source UV."""
    if len(poly) < 3:
        return np.empty((0, 5))
    result = []
    previous = poly[-1]
    previous_value = float(value(previous))
    for current in poly:
        current_value = float(value(current))
        if (previous_value >= -1e-9) != (current_value >= -1e-9):
            ratio = previous_value/(previous_value-current_value)
            result.append(previous+ratio*(current-previous))
        if current_value >= -1e-9:
            result.append(current)
        previous, previous_value = current, current_value
    if len(result) < 3:
        return np.empty((0, 5))
    # Repeated vertices can arise at a grid/source boundary. Remove them before
    # creating triangle fans, without altering the original plane.
    cleaned = [result[0]]
    for point in result[1:]:
        if np.linalg.norm(point[:3]-cleaned[-1][:3]) > 1e-8:
            cleaned.append(point)
    if len(cleaned) > 1 and np.linalg.norm(cleaned[-1][:3]-cleaned[0][:3]) < 1e-8:
        cleaned.pop()
    return np.array(cleaned) if len(cleaned) >= 3 else np.empty((0, 5))


def clip_rectangle(poly, x0, x1, z0, z1):
    for axis, bound, sign in [(0, x0, 1), (0, x1, -1),
                               (2, z0, 1), (2, z1, -1)]:
        poly = clip(poly, lambda p, a=axis, b=bound, s=sign: (p[a]-b)*s)
    return poly


def clip_region(poly, region):
    boundary = np.asarray(region['polygon'])
    # The region definitions are counterclockwise in XZ; the retained side is
    # the left of each edge, independently of Unity triangle winding.
    signed = np.sum(boundary[:, 0]*np.roll(boundary[:, 1], -1)
                    - np.roll(boundary[:, 0], -1)*boundary[:, 1])
    assert signed > 0, 'Courtyard polygon must be counterclockwise'
    for a, b in zip(boundary, np.roll(boundary, -1, axis=0)):
        delta = b-a
        poly = clip(poly, lambda p, a=a, d=delta:
                    d[0]*(p[2]-a[1])-d[1]*(p[0]-a[0]))
    for bound, sign in zip(region['height'], [1, -1]):
        poly = clip(poly, lambda p, b=bound, s=sign: (p[1]-b)*s)
    return poly


def subtract_helipad(poly):
    """Partition the polygon into disjoint areas outside the deck + 35cm."""
    x0, x1, z0, z1 = HELIPAD_BOUNDS
    result = []
    remaining = poly
    # Every subsequent outside strip is clipped from the previous inside part,
    # so the four pieces have no duplicated or overlapping surface triangles.
    for axis, bound, sign in [(0, x0, 1), (0, x1, -1),
                               (2, z0, 1), (2, z1, -1)]:
        outside = clip(remaining, lambda p, a=axis, b=bound, s=sign: -(p[a]-b)*s)
        if len(outside) >= 3:
            result.append(outside)
        remaining = clip(remaining, lambda p, a=axis, b=bound, s=sign: (p[a]-b)*s)
        if len(remaining) < 3:
            break
    return result


def subtract_convex(poly, boundary):
    """Continuous polygon difference; preserve XYZ/UV for every new vertex."""
    intersection = poly
    for a, b in zip(boundary, np.roll(boundary, -1, axis=0)):
        delta = b-a
        intersection = clip(intersection, lambda p, a=a, d=delta:
                            d[0]*(p[2]-a[1])-d[1]*(p[0]-a[0]))
        if len(intersection) < 3:
            return [poly]
    if area(intersection) < 1e-10:
        return [poly]
    result = []
    remaining = poly
    for a, b in zip(boundary, np.roll(boundary, -1, axis=0)):
        delta = b-a
        def left(point):
            return delta[0]*(point[2]-a[1])-delta[1]*(point[0]-a[0])
        outside = clip(remaining, lambda p: -left(p))
        if area(outside) >= .002:
            result.append(outside)
        remaining = clip(remaining, left)
        if len(remaining) < 3:
            break
    return result


def subtract_walls(poly, walls):
    low, high = poly[:, :3].min(0), poly[:, :3].max(0)
    radius = WALL_FOOTPRINT_RADIUS
    candidates = walls[(walls[:, :, 0].max(1) >= low[0]-radius)
                       & (walls[:, :, 0].min(1) <= high[0]+radius)
                       & (walls[:, :, 2].max(1) >= low[2]-radius)
                       & (walls[:, :, 2].min(1) <= high[2]+radius)
                       & (walls[:, :, 1].max(1) >= low[1]-.10)
                       & (walls[:, :, 1].min(1) <= high[1]+.10)]
    angles = np.arange(WALL_FOOTPRINT_SIDES)*math.tau/WALL_FOOTPRINT_SIDES
    offsets = np.column_stack((np.cos(angles), np.sin(angles)))*radius
    # The inscribed polygon remains outside the required 50cm circle. This is
    # a conservative continuous clearance band, not a rejected grid of tiles.
    assert radius*math.cos(math.pi/WALL_FOOTPRINT_SIDES) >= WALL_CLEARANCE
    parts = [poly]
    for wall in candidates:
        points = (wall[:, None, [0, 2]]+offsets[None, :, :]).reshape(-1, 2)
        hull = points[ConvexHull(points).vertices]
        next_parts = []
        for part in parts:
            next_parts.extend(subtract_convex(part, hull))
        parts = next_parts
        if not parts:
            break
    return parts


def area(poly):
    if len(poly) < 3:
        return 0.
    return sum(np.linalg.norm(np.cross(poly[i, :3]-poly[0, :3],
                                       poly[i+1, :3]-poly[0, :3]))/2
               for i in range(1, len(poly)-1))


def segment_distance(a, b, c, d):
    """Exact distance for two 2D line segments, including intersections."""
    def point_distance(p, x, y):
        delta = y-x
        t = np.clip(np.dot(p-x, delta)/max(np.dot(delta, delta), 1e-20), 0, 1)
        return float(np.linalg.norm(p-x-t*delta))
    ab, cd = b-a, d-c
    denominator = ab[0]*cd[1]-ab[1]*cd[0]
    if abs(denominator) > 1e-12:
        ca = c-a
        t = (ca[0]*cd[1]-ca[1]*cd[0])/denominator
        s = (ca[0]*ab[1]-ca[1]*ab[0])/denominator
        if 0 <= t <= 1 and 0 <= s <= 1:
            return 0.
    return min(point_distance(a, c, d), point_distance(b, c, d),
               point_distance(c, a, b), point_distance(d, a, b))


def wall_distance(poly, walls):
    if len(walls) == 0:
        return math.inf
    low, high = poly[:, :3].min(0), poly[:, :3].max(0)
    candidates = walls[(walls[:, :, 0].max(1) >= low[0]-WALL_CLEARANCE)
                       & (walls[:, :, 0].min(1) <= high[0]+WALL_CLEARANCE)
                       & (walls[:, :, 2].max(1) >= low[2]-WALL_CLEARANCE)
                       & (walls[:, :, 2].min(1) <= high[2]+WALL_CLEARANCE)
                       & (walls[:, :, 1].max(1) >= low[1]-.10)
                       & (walls[:, :, 1].min(1) <= high[1]+.10)]
    minimum = math.inf
    points = poly[:, [0, 2]]
    for wall in candidates[:, :, [0, 2]]:
        for a, b in zip(points, np.roll(points, -1, axis=0)):
            for c, d in zip(wall, np.roll(wall, -1, axis=0)):
                minimum = min(minimum, segment_distance(a, b, c, d))
                if minimum < WALL_CLEARANCE:
                    return minimum
    return minimum


def add_polygon(mesh, poly, normal, offset, source_face):
    maximum = 0.
    matrix = np.column_stack((source_face[1]-source_face[0], source_face[2]-source_face[0]))
    for index in range(1, len(poly)-1):
        original = poly[[0, index, index+1], :3]
        if np.linalg.norm(np.cross(original[1]-original[0], original[2]-original[0])) < 1e-9:
            continue
        vertices = original+normal*offset
        quantized = vertices.astype('<f4').astype(float)
        maximum = max(maximum, float(np.max(np.linalg.norm(quantized-original, axis=1))))
        assert maximum <= MAX_SOURCE_ERROR
        # The source face is the authoritative floor even when adjacent native
        # triangles have different slopes; no vertices use a guessed flat Y.
        bary_pair = np.linalg.lstsq(matrix, (original-source_face[0]).T, rcond=None)[0].T
        bary = np.column_stack((1-bary_pair.sum(1), bary_pair))
        assert bary.min() >= -1e-7 and bary.max() <= 1+1e-7
        assert np.max(np.linalg.norm(bary @ source_face-original, axis=1)) < 1e-7
        mesh.tri(*vertices, uvs=(original[:, [0, 2]]/TEXTURE_REPEAT_METRES).tolist(),
                 normals=[normal.tolist()]*3)
    return maximum


def author():
    source_paths = [str(p.relative_to(ROOT)) for p in sorted(
        (ROOT/SOURCE/'Baked/Meshes').glob('Island_*.asset'))]
    assert len(source_paths) == 11
    atlas_path = SOURCE+'/Island/Island_Texture_00.jpg'
    prefab_path = SOURCE+'/Baked/Island.prefab'
    assert Image.open(ROOT/atlas_path).size == (8192, 8192)
    source_prefab = (ROOT/prefab_path).read_text()
    assert source_prefab.count('m_LocalPosition: {x: 0, y: 0, z: 0}') == 12
    assert source_prefab.count('m_LocalScale: {x: 1, y: 1, z: 1}') == 12
    texture_paths = [f'Assets/Game/Textures/PBR_{stem}_{kind}.png'
                     for stem in ['concrete_floor_worn_001', 'brushed_concrete']
                     for kind in ['Base', 'Normal', 'Surface']]
    for path in texture_paths:
        assert Image.open(ROOT/path).size == (2048, 2048)
    sources = {p: sha(p) for p in [*source_paths, atlas_path, prefab_path,
        *texture_paths, 'Tools/author_courtyard_surfaces.py',
        'Tools/author_environment_dressing.py', 'Tools/geometry.py', 'Tools/unity_writer.py',
        'Assets/Game/Supplied/Scripts/SuppliedIslandWorld.cs',
        'Documentation/ThirdParty_Art_Credits.md', 'Tools/ArtSources/download-provenance.json']}
    loaded = []
    walls = []
    for path in source_paths:
        vertices, uv, indices = native_mesh(path)
        faces = vertices[indices]
        cross = np.cross(faces[:, 1]-faces[:, 0], faces[:, 2]-faces[:, 0])
        lengths = np.linalg.norm(cross, axis=1)
        normals = cross/np.maximum(lengths[:, None], 1e-12)
        # Broad phase only. Final boundaries are clipped and independently
        # checked on the actual source triangle, not its centroid.
        near = ((faces[:, :, 0].max(1) >= -170) & (faces[:, :, 0].min(1) <= -98)
                & (faces[:, :, 2].max(1) >= -16) & (faces[:, :, 2].min(1) <= 34))
        walls.extend(faces[near & (np.abs(normals[:, 1]) <= .25) & (lengths > .02)
                           & (np.ptp(faces[:, :, 1], axis=1) >= MIN_WALL_HEIGHT)])
        use = np.flatnonzero(near & (normals[:, 1] >= NORMAL_Y) & (lengths > .01))
        loaded.extend((path, int(i), faces[i], uv[indices[i]], normals[i]) for i in use)
    walls = np.asarray(walls)
    meshes = {r['name']: Mesh() for r in REGIONS}
    seams = {r['name']: Mesh() for r in REGIONS}
    records = []
    rejected = Counter()
    maximum_error = 0.
    minimum_wall_distance = math.inf
    for region in REGIONS:
        for path, face_id, face, uv, normal in loaded:
            if face[:, 1].max() < region['height'][0] or face[:, 1].min() > region['height'][1]:
                continue
            initial = clip_region(np.column_stack((face, uv)), region)
            if area(initial) < .002:
                continue
            for outside_pad in subtract_helipad(initial):
                for piece_id, poly in enumerate(subtract_walls(outside_pad, walls)):
                    covered = area(poly)
                    if covered < .002:
                        continue
                    distance = wall_distance(poly, walls)
                    assert distance >= WALL_CLEARANCE-1e-7, 'Continuous wall clip lost its clearance'
                    minimum_wall_distance = min(minimum_wall_distance, distance)
                    before_surface = len(meshes[region['name']].t)//3
                    maximum_error = max(maximum_error, add_polygon(
                        meshes[region['name']], poly, normal, OFFSET_METRES, face))
                    surface_triangles = len(meshes[region['name']].t)//3-before_surface
                    # Narrow opaque joint strips share this exact accepted
                    # source polygon; they cannot bridge an excluded area,
                    # helipad, wall, elevation break or missing scan triangle.
                    joint_triangles = 0
                    for axis in [0, 2]:
                        lower, upper = poly[:, axis].min(), poly[:, axis].max()
                        for seam_index in range(math.floor(lower/JOINT_PITCH),
                                                math.ceil(upper/JOINT_PITCH)+1):
                            middle = seam_index*JOINT_PITCH
                            line = clip(poly, lambda p, a=axis, m=middle: p[a]-m+JOINT_WIDTH/2)
                            line = clip(line, lambda p, a=axis, m=middle: m+JOINT_WIDTH/2-p[a])
                            if area(line) < .0001:
                                continue
                            before = len(seams[region['name']].t)//3
                            maximum_error = max(maximum_error, add_polygon(
                                seams[region['name']], line, normal, SEAM_OFFSET_METRES, face))
                            joint_triangles += len(seams[region['name']].t)//3-before
                    records.append({'region': region['name'], 'source_mesh': path,
                        'source_triangle': face_id, 'clipped_piece': piece_id,
                        'source_normal': np.round(normal, 9).tolist(),
                        'source_area_m2': round(covered, 9),
                        'source_bounds': [poly[:, :3].min(0).tolist(), poly[:, :3].max(0).tolist()],
                        'surface_triangles': surface_triangles, 'joint_triangles': joint_triangles})
    assert records and maximum_error <= MAX_SOURCE_ERROR
    assert len(meshes['ArrivalCourt'].v) > 0 and len(meshes['CellhouseGateWalk'].v) > 0
    result = {}
    original_write, original_art = u.write, u.ART
    u.ART = BASE
    def capture(path, text):
        result[str(path)] = ('\n'.join(line.rstrip() for line in text.splitlines())+'\n').encode()
        return ROOT/path
    u.write = capture
    try:
        u.Node.all, u.Node.counter = [], 64000000
        root = u.Node('CourtyardSurfaces', static=False)
        for name, stem, tint in [
                ('ArrivalWornConcrete', 'concrete_floor_worn_001', [.79, .79, .75, 1]),
                ('GateBrushedConcrete', 'brushed_concrete', [.77, .76, .70, 1])]:
            prefix = 'Assets/Game/Textures/PBR_'+stem
            u.material(name, tint, rough=.85, texture=prefix+'_Base.png',
                       normal=prefix+'_Normal.png', surface=prefix+'_Surface.png',
                       occlusion=prefix+'_Surface.png', tiling=1)
        u.material('ConcreteExpansionJoints', [.105, .10, .085, 1], rough=.97)
        summaries = []
        for region in REGIONS:
            region_mesh = meshes[region['name']]
            surface_path = u.save_mesh(region['name'], region_mesh, 'Meshes')
            u.Node(region['name'], root, static=False).render(region['name'], region['material'], shadow=0)
            seam_mesh = seams[region['name']]
            if seam_mesh.v:
                seam_name = region['name']+'ExpansionJoints'
                seam_path = u.save_mesh(seam_name, seam_mesh, 'Meshes')
                u.Node(seam_name, root, static=False).render(seam_name, 'ConcreteExpansionJoints', shadow=0)
            else:
                seam_path = None
            selected = [r for r in records if r['region'] == region['name']]
            vertices = np.asarray(region_mesh.v)
            summaries.append({**region, 'surface_mesh': surface_path, 'joint_mesh': seam_path,
                'source_area_m2': round(sum(r['source_area_m2'] for r in selected), 6),
                'source_face_count': len({(r['source_mesh'], r['source_triangle']) for r in selected}),
                'accepted_clipped_polygons': len(selected),
                'surface_vertices': len(region_mesh.v), 'surface_triangles': len(region_mesh.t)//3,
                'joint_vertices': len(seam_mesh.v), 'joint_triangles': len(seam_mesh.t)//3,
                'bounds': [vertices.min(0).tolist(), vertices.max(0).tolist()]})
        prefab = BASE+'/CourtyardSurfaces.prefab'
        u.write(prefab, u.HEAD+''.join(u.node_yaml(n, n is root) for n in u.Node.all))
        u.meta(prefab, 'PrefabImporter')
        for folder in [BASE, BASE+'/Meshes', BASE+'/Materials']:
            u.write(folder+'.meta', 'fileFormatVersion: 2\nguid: '+u.guid(folder)
                    +'\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n')
        manifest = {'schema': 1, 'resource': 'Alcatraz/CourtyardSurfaces/CourtyardSurfaces',
            'world_position': [0, 0, 0], 'world_scale': [1, 1, 1], 'scan_offset': OFFSET.tolist(),
            'source_hashes': sources, 'source_atlas_dimensions': [8192, 8192],
            'referenced_pbr_dimensions': [2048, 2048],
            'texture_repeat_metres': TEXTURE_REPEAT_METRES,
            'source_normal_y_minimum': NORMAL_Y,
            'coverage_policy': 'Continuously repave each authored floor region; no source-color or one-metre tile eligibility mask',
            'visual_offset_metres': OFFSET_METRES, 'joint_offset_metres': SEAM_OFFSET_METRES,
            'maximum_quantized_vertex_distance_from_source_metres': maximum_error,
            'maximum_allowed_vertex_distance_metres': MAX_SOURCE_ERROR,
            'vertical_wall_clearance_metres': WALL_CLEARANCE,
            'minimum_architecture_wall_height_metres': MIN_WALL_HEIGHT,
            'wall_footprint_radius_metres': WALL_FOOTPRINT_RADIUS,
            'wall_footprint_polygon_sides': WALL_FOOTPRINT_SIDES,
            'minimum_measured_vertical_wall_distance_metres':
                minimum_wall_distance if math.isfinite(minimum_wall_distance) else None,
            'excluded_helipad_bounds_x0_x1_z0_z1': HELIPAD_BOUNDS,
            'colliders': 0, 'source_geometry_or_collision_modified': False,
            'surface_area_m2': round(sum(r['source_area_m2'] for r in summaries), 6),
            'vertices': sum(len(m.v) for m in [*meshes.values(), *seams.values()]),
            'triangles': sum(len(m.t)//3 for m in [*meshes.values(), *seams.values()]),
            'regions': summaries, 'rejected': dict(sorted(rejected.items())),
            'rules': ['Clip original source XYZ and UVs to independent floor polygons and height bands',
                      'Reject source normals below .80 Y; no guessed flat connecting floor',
                      'Repave the entire selected floor polygon continuously; source atlas colors do not create holes',
                      'Keep every accepted polygon at least .50m from vertical architecture source triangles spanning >=1m in height',
                      'Exclude the 12m helipad footprint plus .35m on every side',
                      'Full opaque CC0 PBR texture replacement, 2m world UV repeat; no scan-color blend',
                      'Every visual and joint vertex remains within .01m of its own authoritative source triangle',
                      'No colliders, floor changes, wall edits, NPC edits, camera edits or access obstacles'],
            'limitations': ['Conservative continuous architecture clearance footprints require Unity visual review',
                            'Only two confirmed floor areas receive replacement; the complete island is not rebuilt',
                            'No Unity shader compilation, rendering, collision playthrough or performance capture was run'],
            'source_faces': records}
        u.write(BASE+'/Manifest.json', json.dumps(manifest, indent=2)+'\n')
        u.meta(BASE+'/Manifest.json', 'TextScriptImporter')
    finally:
        u.write, u.ART = original_write, original_art
    return result, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    outputs, manifest = author()
    if args.check:
        expected = set(outputs)
        actual = {str(p.relative_to(ROOT)) for p in (ROOT/BASE).rglob('*') if p.is_file()}
        actual.add(BASE+'.meta')
        assert actual == expected, f'Unexpected/missing bake outputs: {sorted(actual ^ expected)}'
        for path, data in outputs.items():
            assert (ROOT/path).read_bytes() == data, f'Generated output changed: {path}'
    else:
        for path, data in outputs.items():
            target = ROOT/path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    print(json.dumps({'status': 'PASS', 'mode': 'check' if args.check else 'author',
        'regions': [{k: r[k] for k in ['name', 'source_area_m2', 'source_face_count',
                    'surface_vertices', 'surface_triangles', 'joint_triangles']} for r in manifest['regions']],
        'surface_area_m2': manifest['surface_area_m2'], 'vertices': manifest['vertices'],
        'triangles': manifest['triangles'], 'source_plane_error_metres':
            manifest['maximum_quantized_vertex_distance_from_source_metres'],
        'colliders': 0, 'output_files': len(outputs)}, indent=2))


if __name__ == '__main__':
    main()
