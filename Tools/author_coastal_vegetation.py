"""Author original coastal cypress and scrub, supported by the supplied scan.

The root prefab is instantiated at world identity. Every plant reuses a recorded
green ground-cover anchor, checks its entire trunk-root ring on that same source
triangle, and retains conservative access/crown margins. --check regenerates all
bytes without changing the checkout. No downloads, colliders or scene edits.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import io
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import author_environment_dressing as ground
from geometry import Mesh
import unity_writer as u

ROOT = Path(__file__).resolve().parents[1]
BASE = 'Assets/Game/Alcatraz/Resources/Alcatraz/CoastalVegetation'
ANCHORS = ground.BASE + '/Manifest.json'
SEED = 20261024
CHUNK_METRES = 24
TREE_COUNT, SHRUB_COUNT = 8, 36
MAX_STORED_TRIANGLES = 70000
MAX_ACTIVE_TRIANGLES = 60000


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def unit(v):
    v = np.asarray(v, dtype=float)
    return v / max(np.linalg.norm(v), 1e-12)


def root_ring(record, radius, mesh_cache, atlas):
    """Require roots, not only a center sample, to touch the original green face."""
    path = record['source_mesh']
    if path not in mesh_cache:
        mesh_cache[path] = ground.native_mesh(path)
    vertices, uv, indices = mesh_cache[path]
    face = vertices[indices[record['source_triangle']]]
    face_uv = uv[indices[record['source_triangle']]]
    p = np.asarray(record['position'])
    angle = np.linspace(0, math.tau, 12, endpoint=False)
    xz = p[[0, 2]] + radius * np.c_[np.cos(angle), np.sin(angle)]
    bc = np.linalg.solve((face[1:]-face[0])[:, [0, 2]].T,
                         (xz-face[0, [0, 2]]).T).T
    bary = np.c_[1-bc.sum(axis=1), bc]
    if bary.min() < .015 or not ground.green(ground.image_pixels(atlas, bary @ face_uv)).all():
        return None
    center_bary = np.asarray(record['barycentric'])
    if not ground.green(ground.image_pixels(atlas, center_bary @ face_uv)):
        return None
    assert np.linalg.norm(center_bary @ face - p) < 1e-8
    assert np.allclose(np.asarray(record['normal']),
                       unit(np.cross(face[1]-face[0], face[2]-face[0])))
    assert record['normal'][1] >= .90 and p[1] >= 2.5
    return bary @ face, face


def blocked(point, crown_radius):
    """Crown-aware access margins; also leave the active facade approach empty."""
    x, _, z = point
    if ground.excluded(point):
        return True
    for cx, cz, radius in [(-147, 6, 7), (-151, -5, 12),
                            (-113.33, 22.5, 10), (-118, 21, 10),
                            (-105, 25, 10), (-112, 25, 10)]:
        if math.hypot(x-cx, z-cz) < radius + crown_radius:
            return True
    if -160-crown_radius < x < -100+crown_radius and -20-crown_radius < z < 45+crown_radius:
        return True
    return False


def select_plants(manifest, atlas):
    cache, rejected = {}, Counter()
    records = list(enumerate(manifest['placements']))
    # Seeded priority and spacing make a few distinct coastal silhouettes rather
    # than repeatedly planting every tuft in the same original grass cluster.
    priority = np.random.default_rng(SEED).permutation(len(records))
    chosen = []
    for species, desired, root_radius, crown in [('cypress', TREE_COUNT, .14, 2.25),
                                                  ('scrub', SHRUB_COUNT, .065, .90)]:
        for index in priority:
            source_index, record = records[index]
            point = np.asarray(record['position'])
            if any(p['anchor_index'] == source_index for p in chosen):
                continue
            coastal = point[1] < 30 and (point[0] < -170 or abs(point[2]) > 45 or point[0] > 130)
            if species == 'cypress' and not coastal:
                rejected['tree_outside_coastal_height_band'] += 1
                continue
            # The source scan can contain ambiguous green roofs. Avoid the high
            # central plateau entirely in this addition. This is conservative,
            # not a claim that a color mask can distinguish every roof.
            if point[1] >= 38 or blocked(point, crown):
                rejected['elevation_or_access_margin'] += 1
                continue
            if any(np.linalg.norm(point[[0, 2]]-np.asarray(p['position'])[[0, 2]])
                   < crown + p['crown_radius_metres'] + .40 for p in chosen):
                rejected['crown_spacing'] += 1
                continue
            root = root_ring(record, root_radius, cache, atlas)
            if root is None:
                rejected['root_ring_outside_green_source_triangle'] += 1
                continue
            ring, face = root
            chosen.append({'species': species, 'anchor_index': source_index,
                           'source_cluster': record['cluster'],
                           'source_mesh': record['source_mesh'],
                           'source_triangle': record['source_triangle'],
                           'barycentric': record['barycentric'],
                           'position': record['position'], 'normal': record['normal'],
                           'root_radius_metres': root_radius,
                           'crown_radius_metres': crown,
                           'root_contacts': ring.tolist(), '_face': face})
            if sum(p['species'] == species for p in chosen) == desired:
                break
        assert sum(p['species'] == species for p in chosen) == desired, \
            f'Not enough supported {species} anchors; no mask was relaxed'
    return chosen, rejected


def tapered_tube(mesh, points, radii, sides, root_face=None):
    """A UV-mapped smoothly shaded, curved, tapered branch, with optional grounded flare."""
    points = np.asarray(points, dtype=float)
    rings, normals = [], []
    distances = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    for i, (p, radius) in enumerate(zip(points, radii)):
        direction = unit(points[min(i+1, len(points)-1)]-points[max(i-1, 0)])
        reference = [1, 0, 0] if abs(direction[1]) > .85 else [0, 1, 0]
        side = unit(np.cross(direction, reference))
        other = unit(np.cross(direction, side))
        ring, ns = [], []
        for j in range(sides+1):
            a = math.tau*j/sides
            n = unit(math.cos(a)*side + math.sin(a)*other)
            vertex = p + n*radius
            if i == 0 and root_face is not None:
                # Root flare is slightly buried in the exact local source
                # plane; source normals are never used to tilt whole trees.
                f = root_face
                plane_n = unit(np.cross(f[1]-f[0], f[2]-f[0]))
                vertex[1] = (np.dot(plane_n, f[0])-plane_n[0]*vertex[0]
                             -plane_n[2]*vertex[2])/plane_n[1] - .07
            ring.append(vertex)
            ns.append(n.tolist())
        rings.append(ring)
        normals.append(ns)
    for i in range(len(points)-1):
        for j in range(sides):
            pts = [rings[i][j], rings[i][j+1], rings[i+1][j+1], rings[i+1][j]]
            ns = [normals[i][j], normals[i][j+1], normals[i+1][j+1], normals[i+1][j]]
            uv = [(j/sides, distances[i]*1.5), ((j+1)/sides, distances[i]*1.5),
                  ((j+1)/sides, distances[i+1]*1.5), (j/sides, distances[i+1]*1.5)]
            # Verify outward winding rather than depending on a tube convention.
            if np.dot(np.cross(pts[1]-pts[0], pts[2]-pts[0]), ns[0]) < 0:
                order = [3, 2, 1, 0]
                pts, ns, uv = ([v[k] for k in order] for v in (pts, ns, uv))
            for a, b, c in [(0, 1, 2), (0, 2, 3)]:
                mesh.tri(pts[a], pts[b], pts[c], [uv[a], uv[b], uv[c]], [ns[a], ns[b], ns[c]])


def leaf(mesh, base, direction, length, width, roll):
    """Four creased opaque leaf triangles, with explicit outward back faces."""
    direction = unit(direction)
    side = unit(np.cross(direction, [0, 1, .07]))
    if np.linalg.norm(side) < .01:
        side = np.array([1., 0, 0])
    normal = unit(np.cross(side, direction))
    side = unit(side*math.cos(roll) + normal*math.sin(roll))
    normal = unit(np.cross(side, direction))
    base = np.asarray(base)
    tip = base + direction*length
    mid = base + direction*length*.48 + normal*width*.22
    left, right = mid-side*width*.5, mid+side*width*.5
    crest = mid + normal*width*.20
    for points, uv in [([base, left, crest], [(0.5, 0), (0, .48), (.5, .48)]),
                       ([base, crest, right], [(0.5, 0), (.5, .48), (1, .48)]),
                       ([left, tip, crest], [(0, .48), (.5, 1), (.5, .48)]),
                       ([crest, tip, right], [(.5, .48), (.5, 1), (1, .48)])]:
        mesh.tri(*points, uv)
        mesh.tri(*points[::-1], uv[::-1])


def spray(mesh, center, direction, size, rng, lod):
    direction = unit(direction)
    across = unit(np.cross(direction, [0, 1, .1]))
    if np.linalg.norm(across) < .01:
        across = np.array([1., 0, 0])
    # Alternating small scale-like leaves form an irregular flattened cypress
    # fan. Broad scrub leaves use the same authored topology at wider aspect.
    for k in (range(5) if lod == 0 else (1, 4)):
        fraction = (k+.25)/5
        side = -1 if k % 2 else 1
        start = center + direction*size*fraction*.6
        leaf_dir = direction*.65 + across*side*rng.uniform(.40, .8) + [0, rng.uniform(-.1, .22), 0]
        leaf(mesh, start, leaf_dir, size*rng.uniform(.65, 1.05),
             size*rng.uniform(.13, .20), rng.uniform(-.55, .55))


def branch_card(mesh, center, direction, size, rotation):
    """A bowed foliage spray with an original cutout needle silhouette."""
    vertical = unit(direction)
    side = unit(np.cross(vertical, [0, 0, 1]))
    if np.linalg.norm(side) < .01:
        side = np.array([1., 0, 0])
    normal = unit(np.cross(side, vertical))
    side = side*math.cos(rotation)+normal*math.sin(rotation)
    normal = unit(np.cross(side, vertical))
    center = np.asarray(center)
    bottom = center-vertical*size*.48
    top = center+vertical*size*.52
    middle = center+normal*size*.12
    left, right = side*size*.44, -side*size*.44
    for points, uv in [([bottom+left, bottom+right, middle+right, middle+left],
                       [(0, 0), (1, 0), (1, .5), (0, .5)]),
                       ([middle+left, middle+right, top+right*.78, top+left*.78],
                       [(0, .5), (1, .5), (1, 1), (0, 1)])]:
        for ids in [(0, 1, 2), (0, 2, 3)]:
            mesh.tri(*(points[i] for i in ids), [uv[i] for i in ids])
            mesh.tri(*(points[i] for i in ids[::-1]), [uv[i] for i in ids[::-1]])


def plant_meshes(plant, lod):
    rng = np.random.default_rng(SEED + plant['anchor_index']*101)
    trunk, foliage, weathered, sprays = Mesh(), Mesh(), Mesh(), Mesh()
    tree = plant['species'] == 'cypress'
    height = rng.uniform(4.4, 6.2) if tree else rng.uniform(.95, 1.55)
    yaw = rng.uniform(0, math.tau)
    wind = np.array([math.cos(yaw)*.8, 0, math.sin(yaw)*.8])
    origin = np.asarray(plant['position'])
    branches = []
    if tree:
        points = [origin + [0, -.02, 0], origin+[0, height*.20, 0],
                  origin+wind*.18+[0, height*.43, 0],
                  origin+wind*.52+[0, height*.68, 0],
                  origin+wind*.92+[0, height*.86, 0]]
        radii = [.14, .115, .082, .047, .013]
        tapered_tube(trunk, points, radii, 10 if lod == 0 else 6, plant['_face'])
        for k in range(6):
            angle = yaw + k*2.39996 + rng.uniform(-.22, .22)
            horizontal = np.array([math.cos(angle), 0, math.sin(angle)])
            level = .43 + .29*k/5
            start = origin+wind*level*.55+[0, height*level, 0]
            reach = rng.uniform(1.1, 1.85) * (1-.30*k/6)
            end = start + horizontal*reach + wind*.38 + [0, rng.uniform(.6, 1.1), 0]
            points = [start, start+horizontal*reach*.38+[0, .22, 0],
                      end-horizontal*.25-[0, .15, 0], end]
            tapered_tube(trunk, points, [.055, .040, .024, .009], 6 if lod == 0 else 4)
            for side in (-1, 1):
                tangent = np.array([-horizontal[2], 0, horizontal[0]])
                twig_start = np.asarray(points[2])
                cluster = end+tangent*side*rng.uniform(.35, .62)+wind*.12+[0, rng.uniform(-.12, .26), 0]
                tapered_tube(trunk, [twig_start, (twig_start+cluster)*.5+[0, .10, 0], cluster],
                             [.018, .012, .003], 4 if lod == 0 else 3)
                branches.append((cluster, horizontal, .48 if tree else .24))
    else:
        for k in range(5):
            angle = yaw + k*2.39996
            horizontal = np.array([math.cos(angle), 0, math.sin(angle)])
            end = origin + horizontal*rng.uniform(.27, .52) + wind*.15 + [0, height*rng.uniform(.65, 1), 0]
            points = [origin+[0, -.035, 0], origin+horizontal*.10+[0, height*.30, 0],
                      end-horizontal*.10-[0, .13, 0], end]
            tapered_tube(trunk, points, [.045, .034, .019, .004], 6 if lod == 0 else 3,
                         plant['_face'])
            branches.append((end, horizontal, .28))
    # The same seeded branch skeleton is retained by both LODs. LOD1 uses fewer
    # leaf fans, rather than replacing trees with angular cones or flat cards.
    for cluster_index, (center, horizontal, size) in enumerate(branches):
        count = 3 if tree else 2
        cluster_rng = np.random.default_rng(SEED + plant['anchor_index']*101 + cluster_index*13)
        for fan_index in range(count):
            a = cluster_rng.uniform(0, math.tau)
            offset = np.array([math.cos(a), cluster_rng.uniform(-.24, .30), math.sin(a)])
            anchor = center + offset*size*.62
            direction = unit(horizontal*.25+offset+[0, .30, 0]+wind*.18)
            if lod == 1 and fan_index % 2:
                continue
            target = weathered if (cluster_index+fan_index) % 9 == 0 else foliage
            spray(target, anchor, direction, size, cluster_rng, lod)
        card_rng = np.random.default_rng(SEED + plant['anchor_index']*317 + cluster_index*29)
        for card_index in range(4 if lod == 0 else 2):
            angle = card_index*2.39996+card_rng.uniform(-.3, .3)
            offset = np.array([math.cos(angle), card_rng.uniform(-.2, .3), math.sin(angle)])
            direction = unit(offset*.65+[0, .60, 0]+wind*.35)
            branch_card(sprays, center+offset*size*.25, direction,
                        size*(2.5 if tree else 2.2), card_rng.uniform(0, math.tau))
    parts = {'Bark': trunk, 'Needles': foliage, 'SaltTips': weathered, 'Sprays': sprays}
    # Coastal crowns remain compact enough to honor their access-clearance
    # envelopes. Keep the exact source-plane root flare unchanged.
    for mesh in parts.values():
        for vertex in mesh.v:
            if vertex[1] > origin[1]+.15:
                fraction = np.clip((vertex[1]-origin[1]-.15)/.35, 0, 1)
                horizontal_scale = 1-fraction*(.34 if tree else .25)
                vertex[0] = origin[0]+(vertex[0]-origin[0])*horizontal_scale
                vertex[2] = origin[2]+(vertex[2]-origin[2])*horizontal_scale
        # Recompute smooth normal directions under the constant upper-crown
        # anisotropic scaling; the small base blend is visually negligible.
        horizontal_scale = .66 if tree else .75
        mesh.n = [unit(np.asarray(n)/[horizontal_scale, 1, horizontal_scale]).tolist() for n in mesh.n]
    return parts, height


def png_bytes(array):
    output = io.BytesIO()
    Image.fromarray(np.asarray(array, dtype=np.uint8)).save(output, format='PNG', optimize=False)
    return output.getvalue()


def texture_maps():
    """Original periodic fissures and leaf-scale microstructure, never photo enlargements."""
    result = {}
    n = 512
    y, x = np.mgrid[:n, :n]/n
    grooves = (.5+.5*np.sin(math.tau*(x*17+.13*np.sin(y*math.tau*3)
                                    +.04*np.sin(y*math.tau*11))))**8
    fine = np.sin(math.tau*(x*61+y*.4))*.045 + np.sin(math.tau*(y*77+x*9))*.025
    height = .63-.46*grooves+fine
    bark = np.clip(np.stack([.35+.18*height, .305+.14*height, .235+.12*height], axis=-1)*255, 0, 255)
    dx = (np.roll(height, -1, 1)-np.roll(height, 1, 1))*7
    dy = (np.roll(height, -1, 0)-np.roll(height, 1, 0))*7
    normal = np.stack([-dx, dy, np.ones_like(x)], axis=-1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    packed = np.zeros((n, n, 4)); packed[..., 1] = (.72+.28*height)*255
    packed[..., 2] = 255; packed[..., 3] = (.12+.10*height)*255
    result['CypressBark_Base.png'] = png_bytes(bark)
    result['CypressBark_Normal.png'] = png_bytes((normal*.5+.5)*255)
    result['CypressBark_Surface.png'] = png_bytes(packed)
    n = 256
    y, x = np.mgrid[:n, :n]/(n-1)
    edge = np.abs(x-.5)*2
    veins = .5+.5*np.cos((y*16+np.abs(x-.5)*10)*math.tau)
    grain = np.sin(x*math.tau*37+y*math.tau*19)*.015
    tone = .10+veins*.026+edge*.018+grain
    leaf_map = np.stack([tone*.79, tone*1.37, tone*.78], axis=-1)*255
    result['CoastalNeedles_Base.png'] = png_bytes(np.clip(leaf_map, 0, 255))
    # An original scale-leaf branch silhouette. Hundreds of tiny tapered
    # needles are drawn individually, so a handful of curved cutout sprays can
    # carry natural foliage density without tens of thousands of alpha planes.
    canvas = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    rng = np.random.default_rng(SEED)
    def needle_branch(start, end, count):
        delta = end-start
        direction = unit(delta)
        across = np.array([-direction[1], direction[0]])
        draw.line([tuple(start), tuple(end)], fill=(74, 80, 51, 255), width=2)
        for needle_index in range(count):
            t = (needle_index+.5)/(count+1)
            base = start+delta*t
            for needle_side in (-1, 1):
                length = rng.uniform(9, 19)*(1-t*.25)
                tip = base+direction*length*.75+across*needle_side*length*.66
                middle = base+(tip-base)*.55
                width = rng.uniform(1.3, 2.4)
                green = rng.uniform(.80, 1.15)
                color = (int(66*green), int(86*green), int(53*green), 255)
                draw.polygon([tuple(base), tuple(middle+across*width), tuple(tip),
                              tuple(middle-across*width)], fill=color)
    draw.line([(256, 495), (252, 392), (260, 285)], fill=(99, 91, 63, 255), width=5)
    for branch_index in range(21):
        a = math.radians(-156+branch_index*6.35)+rng.uniform(-.05, .05)
        start = np.array([256+rng.uniform(-15, 15), rng.uniform(340, 445)])
        direction = np.array([math.cos(a), math.sin(a)])
        reach = rng.uniform(205, 305)
        end = start+direction*reach
        needle_branch(start, end, 27)
        across = np.array([-direction[1], direction[0]])
        for t in (.38, .61, .80):
            for side in (-1, 1):
                base = start+(end-start)*t
                twig = base+direction*rng.uniform(29, 48)+across*side*rng.uniform(20, 44)
                needle_branch(base, twig, 9)
    result['CypressSprays_Base.png'] = png_bytes(np.asarray(canvas))
    return result


def texture_meta(path, normal=False, linear=False, cutout=False):
    return ('fileFormatVersion: 2\nguid: '+u.guid(path)+'\nTextureImporter:\n'
            '  externalObjects: {}\n  serializedVersion: 13\n  mipmaps:\n'
            '    mipMapMode: 0\n    enableMipMap: 1\n'
            f'    sRGBTexture: {0 if linear or normal else 1}\n'
            f'  isReadable: 0\n  textureType: {1 if normal else 0}\n'
            '  textureShape: 1\n  maxTextureSize: 512\n  textureSettings:\n'
            '    serializedVersion: 2\n    filterMode: 1\n    aniso: 4\n'
            '    mipBias: 0\n    wrapU: 0\n    wrapV: 0\n    wrapW: 0\n'
            f'  alphaIsTransparency: {1 if cutout else 0}\n  alphaUsage: {1 if cutout else 0}\n'
            '  userData: Original procedural coastal vegetation art; no external texture source\n'
            '  assetBundleName: \n  assetBundleVariant: \n')


def author():
    anchors = json.loads((ROOT / ANCHORS).read_text())
    for path, expected in anchors['source_hashes'].items():
        assert sha(path) == expected, f'Ground-cover anchor source changed: {path}'
    atlas_path = ground.SOURCE+'/Island/Island_Texture_00.jpg'
    atlas = np.asarray(Image.open(ROOT/atlas_path).convert('RGB'))
    plants, rejected = select_plants(anchors, atlas)
    sources = {path: sha(path) for path in [ANCHORS, atlas_path, 'Tools/author_coastal_vegetation.py',
                                          'Tools/author_environment_dressing.py', 'Tools/geometry.py',
                                          'Tools/unity_writer.py',
                                          *sorted({p['source_mesh'] for p in plants})]}
    chunks = defaultdict(lambda: defaultdict(lambda: defaultdict(Mesh)))
    for plant in plants:
        for lod in (0, 1):
            parts, height = plant_meshes(plant, lod)
            plant['skeletal_height_metres'] = height
            cell = tuple(np.floor(np.asarray(plant['position'])[[0, 2]]/CHUNK_METRES).astype(int))
            for material, mesh in parts.items():
                chunks[cell][lod][material].merge(mesh)
            plant[f'lod{lod}_triangles'] = sum(len(m.t)//3 for m in parts.values())
            points = np.concatenate([m.v for m in parts.values() if m.v])
            plant[f'lod{lod}_bounds'] = [points.min(0).tolist(), points.max(0).tolist()]
            if lod == 0:
                plant['height_metres'] = float(points[:, 1].max()-points[:, 1].min())
            distance = np.linalg.norm((points-np.asarray(plant['position']))[:, [0, 2]], axis=1).max()
            assert distance <= plant['crown_radius_metres'], (plant['species'], distance)
        del plant['_face']
    active_triangles = sum(p['lod0_triangles'] for p in plants)
    stored_triangles = active_triangles+sum(p['lod1_triangles'] for p in plants)
    assert 40000 <= active_triangles <= MAX_ACTIVE_TRIANGLES
    assert stored_triangles <= MAX_STORED_TRIANGLES
    result = {}
    original_write, original_art = u.write, u.ART
    def capture(path, text):
        result[str(path)] = ('\n'.join(line.rstrip() for line in text.splitlines())+'\n').encode()
        return ROOT/path
    u.write, u.ART = capture, BASE
    try:
        for name, data in texture_maps().items():
            path = BASE+'/Textures/'+name
            result[path] = data
            capture(path+'.meta', texture_meta(path, '_Normal' in name, '_Surface' in name, 'Sprays' in name))
        prefix = BASE+'/Textures/'
        u.material('Bark', [1, 1, 1, 1], rough=.86, texture=prefix+'CypressBark_Base.png',
                   normal=prefix+'CypressBark_Normal.png', surface=prefix+'CypressBark_Surface.png',
                   occlusion=prefix+'CypressBark_Surface.png')
        u.material('Needles', [1, 1, 1, 1], rough=.83, texture=prefix+'CoastalNeedles_Base.png')
        u.material('SaltTips', [1.34, 1.16, .85, 1], rough=.91, texture=prefix+'CoastalNeedles_Base.png')
        spray_material = u.material('Sprays', [1, 1, 1, 1], rough=.87, texture=prefix+'CypressSprays_Base.png')
        text = result[spray_material].decode().replace('m_ValidKeywords: []', 'm_ValidKeywords: ["_ALPHATEST_ON"]')
        text = text.replace('m_CustomRenderQueue: -1', 'm_CustomRenderQueue: 2450')
        text = text.replace('stringTagMap: {RenderType: Opaque}', 'stringTagMap: {RenderType: TransparentCutout}')
        text = text.replace('- _AlphaClip: 0', '- _AlphaClip: 1').replace('- _Cutoff: 0.5', '- _Cutoff: 0.42')
        capture(spray_material, text)
        u.Node.all, u.Node.counter = [], 65000000
        root = u.Node('CoastalVegetation', static=False)
        output_chunks = []
        for cell, lods in sorted(chunks.items()):
            chunk = u.Node(f'Coastal_{cell[0]}_{cell[1]}', root, static=False)
            renderers = {}
            bounds_points = []
            output_meshes = []
            for lod, parts in sorted(lods.items()):
                renderers[lod] = []
                for material, mesh in sorted(parts.items()):
                    if not mesh.v:
                        continue
                    assert np.isfinite(np.asarray(mesh.v)).all()
                    assert np.isfinite(np.asarray(mesh.n)).all()
                    assert len(mesh.t)%3 == 0 and max(mesh.t) < len(mesh.v)
                    name = f'Coastal_{cell[0]}_{cell[1]}_LOD{lod}_{material}'
                    path = u.save_mesh(name, mesh, 'Meshes')
                    node = u.Node(name, chunk, static=False).render(name, material, shadow=1)
                    renderers[lod].append(node.parts[-1][1])
                    v = np.asarray(mesh.v)
                    bounds_points.extend(v)
                    output_meshes.append({'path': path, 'lod': lod, 'material': material,
                                          'vertices': len(mesh.v), 'triangles': len(mesh.t)//3,
                                          'bounds': [v.min(0).tolist(), v.max(0).tolist()]})
            bounds_points = np.asarray(bounds_points)
            low, high = bounds_points.min(0), bounds_points.max(0)
            center, size = (low+high)*.5, float(max(high-low))
            body = ('  serializedVersion: 2\n  m_LocalReferencePoint: '+u.vec(center)+'\n'
                    f'  m_Size: {size:.8g}\n  m_FadeMode: 0\n  m_AnimateCrossFading: 0\n'
                    '  m_LastLODIsBillboard: 0\n  m_LODs:\n')
            for lod, threshold in [(0, .10), (1, .012)]:
                body += f'  - screenRelativeHeight: {threshold}\n    fadeTransitionWidth: 0\n    renderers:\n'
                for renderer in renderers[lod]:
                    body += f'    - renderer: {{fileID: {renderer}}}\n'
            body += '  m_Enabled: 1\n'
            chunk.component(205, body)
            output_chunks.append({'cell': [int(k) for k in cell], 'bounds': [low.tolist(), high.tolist()],
                                  'lod_reference': center.tolist(), 'lod_size': size, 'meshes': output_meshes})
        path = BASE+'/CoastalVegetation.prefab'
        capture(path, u.HEAD+''.join(u.node_yaml(n, n is root) for n in u.Node.all))
        u.meta(path, 'PrefabImporter')
        for folder in [BASE, BASE+'/Meshes', BASE+'/Materials', BASE+'/Textures']:
            capture(folder+'.meta', 'fileFormatVersion: 2\nguid: '+u.guid(folder)+
                    '\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n')
        manifest = {'schema': 1, 'seed': SEED, 'resource': 'Alcatraz/CoastalVegetation/CoastalVegetation',
                    'world_position': [0, 0, 0], 'art_origin': 'Original deterministic procedural geometry and texture maps',
                    'source_hashes': sources, 'trees': TREE_COUNT, 'shrubs': SHRUB_COUNT,
                    'lod0_triangles': active_triangles,
                    'lod1_triangles': stored_triangles-active_triangles,
                    'stored_triangles': stored_triangles, 'max_stored_triangles': MAX_STORED_TRIANGLES,
                    'max_active_triangles': MAX_ACTIVE_TRIANGLES,
                    'vertices': sum(m['vertices'] for c in output_chunks for m in c['meshes']),
                    'chunk_metres': CHUNK_METRES, 'colliders': 0,
                    'lod_screen_heights': [.10, .012], 'chunk_count': len(output_chunks),
                    'rules': ['Only previously authored green ground-cover anchors are eligible',
                              'Root center and twelve root-circle contacts must be green and inside the same original scan triangle',
                              'Root contacts are barycentrically projected to the exact original face; trunk flare is buried by .07 m',
                              'Existing source normal/height/access masks are retained; plants above 38 m are excluded',
                              'Trees are limited to the lower coastal band under 30 m; crowns remain separated',
                              'Crown margins exclude spawn, helipad, gate, guards, dog, dock access and facade approach',
                              'Each spatial cell has two native geometry LODs and separate bark/foliage mesh parts',
                              'Original cutout needle sprays and opaque leaves surround the branched trunks at both LODs',
                              'No cones, billboard-only trees, physics colliders or runtime ground queries'],
                    'limitations': ['No Unity import, API execution, lighting or GPU performance has been verified here',
                                    'Green color/elevation masks are placement heuristics and do not prove every face is natural ground',
                                    'This sparse authored vegetation kit improves confirmed supplied-island patches; it is not a full biome rebuild',
                                    'Cutout needle sprays trade additional alpha-test overdraw for denser foliage; profiling is still required',
                                    'Wind shape is authored into static branches; this kit does not add a runtime wind shader'],
                    'rejected': dict(sorted(rejected.items())), 'chunks': output_chunks, 'placements': plants}
        capture(BASE+'/Manifest.json', json.dumps(manifest, indent=2)+'\n')
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
        for path, data in outputs.items():
            assert (ROOT/path).read_bytes() == data, f'Generated file differs: {path}'
        actual = {str(p.relative_to(ROOT)) for p in (ROOT/BASE).rglob('*') if p.is_file()}
        assert actual == set(outputs)-{BASE+'.meta'}, 'Unexpected or stale generated files'
    else:
        for path, data in outputs.items():
            target = ROOT/path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    print(json.dumps({'status': 'PASS', 'mode': 'check' if args.check else 'author',
                      'trees': manifest['trees'], 'shrubs': manifest['shrubs'],
                      'lod0_triangles': manifest['lod0_triangles'],
                      'lod1_triangles': manifest['lod1_triangles'],
                      'stored_triangles': manifest['stored_triangles'],
                      'chunks': manifest['chunk_count'], 'output_files': len(outputs),
                      'colliders': 0}, indent=2))


if __name__ == '__main__':
    main()
