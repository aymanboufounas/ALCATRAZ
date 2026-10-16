"""Bake sparse original grass onto confirmed green areas of the supplied scan.

No colliders, scene edits, network downloads, texture upscaling, or Unity import
are involved. The baked root is placed at world identity. --check regenerates
in memory and verifies every committed byte, source hash, placement, and budget.
Requires Tools/requirements.txt (NumPy, SciPy and Pillow).
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re

import numpy as np
from PIL import Image
from scipy.spatial import cKDTree

from geometry import Mesh
import unity_writer as u

ROOT = Path(__file__).resolve().parents[1]
BASE = 'Assets/Game/Alcatraz/Resources/Alcatraz/EnvironmentDressing'
SOURCE = 'Assets/Game/Supplied/Resources/AlcatrazSupplied'
OFFSET = np.array([-63., 45., 12.])
SEED = 20261016
CHUNK_SIZE = 32
MAX_VERTICES = 80000
MIN_NORMAL_Y = .90
MIN_HEIGHT = 2.5
MAX_CLUSTERS = 144


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def native_mesh(path):
    text = (ROOT / path).read_text()
    raw = bytes.fromhex(re.search(r'_typelessdata: ([0-9a-f]+)', text)[1])
    count = int(re.search(r'm_VertexCount: (\d+)', text)[1])
    stride = int(re.search(r'm_DataSize: (\d+)', text)[1]) // count
    assert stride == 48, f'Unexpected native vertex stride in {path}'
    data = np.frombuffer(raw, '<f4').reshape(count, 12)
    indices = np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: ([0-9a-f]+)', text)[1]),
                            '<u4' if 'm_IndexFormat: 1' in text else '<u2').reshape(-1, 3)
    assert indices.max() < count
    return data[:, :3].astype('f8') + OFFSET, data[:, 10:12].astype('f8'), indices


def green(rgb):
    r, g, b = np.moveaxis(np.asarray(rgb, dtype=float) / 255, -1, 0)
    return ((g > r * 1.045) & (g > b * 1.08) & (g-r > .025)
            & (g > .15) & (g < .70))


def image_pixels(image, uv):
    height, width = image.shape[:2]
    x = np.clip(np.rint(uv[..., 0] * (width-1)).astype(int), 0, width-1)
    y = np.clip(np.rint((1-uv[..., 1]) * (height-1)).astype(int), 0, height-1)
    return image[y, x]


def excluded(position):
    # Supplied-world anchors are different from the authored chapter's road map.
    # Generous margins keep all grass outside the visible entrances and vehicles.
    x, _, z = position
    for cx, cz, radius in [(-147, 6, 6), (-151, -5, 10), (-113.33, 22.5, 8),
                            (-118, 21, 5), (-105, 25, 5), (-112, 25, 5)]:
        if (x-cx)**2 + (z-cz)**2 < radius**2:
            return True
    if abs(x + 165) < 24 and abs(z - 162) < 20:
        return True
    start, end = np.array([-173., 80.]), np.array([-165., 147.])
    delta = end-start
    t = np.clip(np.dot(np.array([x, z])-start, delta) / np.dot(delta, delta), 0, 1)
    return np.linalg.norm(np.array([x, z])-start-t*delta) < 5


def author():
    rng = np.random.default_rng(SEED)
    source_paths = [str(p.relative_to(ROOT)) for p in sorted(
        (ROOT / SOURCE / 'Baked/Meshes').glob('Island_*.asset'))]
    assert len(source_paths) == 11, 'Expected the existing eleven supplied mesh chunks'
    prefab_path = SOURCE + '/Baked/Island.prefab'
    prefab = (ROOT / prefab_path).read_text()
    assert prefab.count('m_LocalPosition: {x: 0, y: 0, z: 0}') == 12
    assert prefab.count('m_LocalScale: {x: 1, y: 1, z: 1}') == 12
    atlas_path = SOURCE + '/Island/Island_Texture_00.jpg'
    atlas = np.asarray(Image.open(ROOT / atlas_path).convert('RGB'))
    assert atlas.shape[:2] == (8192, 8192)
    sources = {path: sha(path) for path in [prefab_path, atlas_path, *source_paths,
                                           'Tools/author_environment_dressing.py',
                                           'Tools/geometry.py', 'Tools/unity_writer.py']}
    faces, coordinates, references = [], [], []
    for path in source_paths:
        vertices, uv, indices = native_mesh(path)
        faces.append(vertices[indices])
        coordinates.append(uv[indices])
        references.extend((path, int(index)) for index in range(len(indices)))
    faces, coordinates = np.concatenate(faces), np.concatenate(coordinates)
    cross = np.cross(faces[:, 1]-faces[:, 0], faces[:, 2]-faces[:, 0])
    lengths = np.linalg.norm(cross, axis=1)
    normals = cross / np.maximum(lengths[:, None], 1e-12)
    area = lengths/2
    centers = faces.mean(axis=1)
    usable = ((normals[:, 1] >= MIN_NORMAL_Y) & (centers[:, 1] >= MIN_HEIGHT)
              & (area > .005) & (area < 100))
    usable_ids = np.flatnonzero(usable)
    tree = cKDTree(centers[usable_ids][:, [0, 2]])
    rejected = Counter()

    def surface_point(face_id, xz):
        face = faces[face_id]
        matrix = (face[1:]-face[0])[:, [0, 2]].T
        bc = np.linalg.solve(matrix, np.asarray(xz)-face[0, [0, 2]])
        bary = np.array([1-bc.sum(), *bc])
        if np.min(bary) < .015:
            return None
        return bary @ face, bary

    def accept(face_id, point, bary):
        if point[1] < MIN_HEIGHT or excluded(point):
            rejected['height_or_access_margin'] += 1
            return False
        if not green(image_pixels(atlas, bary @ coordinates[face_id])):
            rejected['non_green_atlas'] += 1
            return False
        # A conservative roof-risk rejection: greenery must remain near the
        # lower local surface, rather than elevated above adjacent ground.
        nearby = tree.query_ball_point(point[[0, 2]], 8.)
        local_low = np.quantile(centers[usable_ids[nearby], 1], .20)
        if point[1] > local_low + 1.25:
            rejected['elevated_roof_risk_or_steep_terrain'] += 1
            return False
        return True

    candidates = []
    for face_id in usable_ids:
        count = int(np.clip(math.ceil(area[face_id]*8), 4, 128))
        pairs = rng.random((count, 2))
        pairs[pairs.sum(axis=1) > 1] = 1-pairs[pairs.sum(axis=1) > 1]
        bary = np.c_[1-pairs.sum(axis=1), pairs]
        rgb = image_pixels(atlas, bary @ coordinates[face_id])
        for b in bary[green(rgb)]:
            p = b @ faces[face_id]
            if accept(face_id, p, b):
                candidates.append((int(face_id), p, b))
    if not candidates:
        raise RuntimeError('No safe green ground remains; no road filter was relaxed')
    selected, cells = [], defaultdict(list)
    for index in rng.permutation(len(candidates)):
        face_id, p, b = candidates[index]
        key = tuple(np.floor(p[[0, 2]] / 1.2).astype(int))
        neighbors = [q for dx in (-1, 0, 1) for dz in (-1, 0, 1)
                     for q in cells[(key[0]+dx, key[1]+dz)]]
        if any(np.linalg.norm(p[[0, 2]]-q[[0, 2]]) < 1.2 for q in neighbors):
            continue
        selected.append((face_id, p, b))
        cells[key].append(p)
        if len(selected) >= MAX_CLUSTERS:
            break

    chunks, placements = defaultdict(Mesh), []
    vertices_used = 0
    for cluster_id, (face_id, anchor, _) in enumerate(selected):
        for _ in range(12):
            xz = anchor[[0, 2]] + rng.normal(0, .24, 2)
            projected = surface_point(face_id, xz)
            if projected is None:
                rejected['cluster_crosses_source_face'] += 1
                continue
            point, bary = projected
            if not accept(face_id, point, bary):
                continue
            clump = Mesh()
            blade_bases = []
            for blade in range(3):
                angle = rng.uniform(0, math.tau)
                width = rng.uniform(.012, .025)
                across = np.array([math.cos(angle), math.sin(angle)]) * width
                edges = [surface_point(face_id, xz-across), surface_point(face_id, xz+across)]
                if any(edge is None or not accept(face_id, *edge) for edge in edges):
                    continue
                left, right = (edge[0] for edge in edges)
                height = rng.uniform(.12, .32)
                lean = np.array([-math.sin(angle), 0, math.cos(angle)]) * height*.22
                mid = point + [0, height*.55, 0] + lean*.30
                tip = point + [0, height, 0] + lean
                ml, mr = mid + (left-point)*.55, mid + (right-point)*.55
                # Two tapering sections are duplicated for outward-facing backs;
                # opaque triangles avoid alpha-card overdraw and need no cull hack.
                for triangle in [(left, right, ml), (right, mr, ml), (ml, mr, tip)]:
                    clump.tri(*triangle)
                    clump.tri(*triangle[::-1])
                blade_bases.append([left.tolist(), right.tolist()])
            if not clump.v:
                continue
            if vertices_used + len(clump.v) > MAX_VERTICES:
                break
            key = tuple(np.floor(point[[0, 2]] / CHUNK_SIZE).astype(int))
            chunks[key].merge(clump)
            vertices_used += len(clump.v)
            path, local_face = references[face_id]
            assert bary.min() >= .015 and abs(bary.sum()-1) < 1e-10
            assert np.linalg.norm(point-bary @ faces[face_id]) < 1e-8
            assert normals[face_id, 1] >= MIN_NORMAL_Y and point[1] >= MIN_HEIGHT
            for edges in blade_bases:
                for edge in edges:
                    base, base_bary = surface_point(face_id, np.asarray(edge)[[0, 2]])
                    assert np.linalg.norm(base-edge) < 1e-8 and base_bary.min() >= .015
            placements.append({'cluster': cluster_id, 'source_mesh': path,
                               'source_triangle': local_face, 'barycentric': bary.tolist(),
                               'position': point.tolist(), 'normal': normals[face_id].tolist(),
                               'blade_bases': blade_bases})
        if vertices_used >= MAX_VERTICES-54:
            break
    assert placements and 0 < vertices_used <= MAX_VERTICES
    assert all(np.isfinite(np.asarray(m.v)).all() for m in chunks.values())
    assert all(max(m.t) < len(m.v) and len(m.t) % 3 == 0 for m in chunks.values())
    result = {}
    original_write, original_art = u.write, u.ART
    u.ART = BASE
    def capture(path, text):
        result[str(path)] = ('\n'.join(line.rstrip() for line in text.splitlines())+'\n').encode()
        return ROOT / path
    u.write = capture
    try:
        u.Node.all, u.Node.counter = [], 62000000
        root = u.Node('SuppliedGroundCover', static=False)
        u.material('CoastalGroundcover', [.155, .205, .105, 1], rough=.97)
        output_chunks = []
        for key, mesh in sorted(chunks.items()):
            name = f'Groundcover_{key[0]}_{key[1]}'
            path = u.save_mesh(name, mesh, 'Meshes')
            u.Node(name, root, static=False).render(name, 'CoastalGroundcover', shadow=0)
            v = np.array(mesh.v)
            output_chunks.append({'path': path, 'cell': [int(k) for k in key], 'vertices': len(mesh.v),
                                  'triangles': len(mesh.t)//3,
                                  'bounds': [v.min(0).tolist(), v.max(0).tolist()]})
        path = BASE + '/SuppliedGroundCover.prefab'
        u.write(path, u.HEAD + ''.join(u.node_yaml(n, n is root) for n in u.Node.all))
        u.meta(path, 'PrefabImporter')
        for folder in [BASE, BASE+'/Meshes', BASE+'/Materials']:
            u.write(folder+'.meta', 'fileFormatVersion: 2\nguid: '+u.guid(folder)+
                    '\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n')
        positions = np.array([p['position'] for p in placements])
        manifest = {'schema': 1, 'seed': SEED,
                    'resource': 'Alcatraz/EnvironmentDressing/SuppliedGroundCover',
                    'world_position': [0, 0, 0], 'scan_offset': OFFSET.tolist(),
                    'source_hashes': sources, 'source_triangles': len(faces),
                    'eligible_upward_triangles': len(usable_ids), 'green_candidates': len(candidates),
                    'accepted_clusters': len({p['cluster'] for p in placements}),
                    'tufts': len(placements), 'vertices': vertices_used,
                    'triangles': sum(len(m.t)//3 for m in chunks.values()),
                    'bounds': [positions.min(0).tolist(), positions.max(0).tolist()],
                    'chunk_metres': CHUNK_SIZE, 'vertex_budget': MAX_VERTICES,
                    'min_source_normal_y': MIN_NORMAL_Y, 'min_world_height': MIN_HEIGHT,
                    'blade_height_metres': [.12, .32], 'colliders': 0,
                    'rules': ['Original 8K scan colors only; green > 1.045 red and 1.08 blue, green-red > .025',
                              'Every blade base is barycentrically projected within its original upward source triangle',
                              'Point and both blade base edges must pass the green mask; source triangle margin .015',
                              'World height >= 2.5 metres; source normal Y >= .90',
                              'Reject surfaces > 1.25 metres above local 20th percentile in an 8 metre neighborhood',
                              'Exclude supplied spawn, gate, NPC path anchors, helipad, dock and house access margins',
                              'Clusters separated >= 1.2 metres; blade height .12 to .32 metres',
                              'Opaque original geometry, no physics, no floor changes, no runtime ground queries'],
                    'limitations': ['Sparse confirmed patches; most of this dry scan is not green',
                                    'Color and local-elevation masks are conservative heuristics; Unity visual inspection still required',
                                    'Only the supplied scan receives this prefab; authored chapter vegetation is retained separately'],
                    'rejected': dict(sorted(rejected.items())), 'chunks': output_chunks,
                    'placements': placements}
        u.write(BASE+'/Manifest.json', json.dumps(manifest, indent=2)+'\n')
        u.meta(BASE+'/Manifest.json', 'TextScriptImporter')
    finally:
        u.write, u.ART = original_write, original_art
    return result, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Verify committed bake without writing files')
    args = parser.parse_args()
    outputs, manifest = author()
    if args.check:
        for path, data in outputs.items():
            assert (ROOT / path).read_bytes() == data, f'Generated file differs: {path}'
    else:
        for path, data in outputs.items():
            target = ROOT / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    print(json.dumps({'status': 'PASS', 'mode': 'check' if args.check else 'author',
                      'tufts': manifest['tufts'], 'clusters': manifest['accepted_clusters'],
                      'chunks': len(manifest['chunks']), 'vertices': manifest['vertices'],
                      'triangles': manifest['triangles'], 'colliders': 0,
                      'output_files': len(outputs)}, indent=2))


if __name__ == '__main__':
    main()
