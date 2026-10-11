"""Render revision 11 source assets; these images are not Unity captures.

Run with python3 Tools/render_current_previews.py after installing
Tools/requirements-supplied.txt. The offline renderer does not reproduce URP
shadows, ocean shading, post processing, UI, animation playback or physics.
"""
from functools import lru_cache
import json
import re

import numpy as np
import yaml
from PIL import ImageDraw, ImageFont
from scipy.spatial.transform import Rotation

import render_supplied_previews as r
from fbx_pose import Character, animation

OUT = r.ROOT / 'Documentation/Revision11Previews'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
DECK = (.48, .43, .34, 1)


def translated(position, yaw=0):
    matrix = np.eye(4)
    matrix[:3, :3] = Rotation.from_euler('y', yaw, degrees=True).as_matrix()
    matrix[:3, 3] = position
    return matrix


def cube(name, position, size, color=DECK, rotation=None):
    vertices, normals, indices = [], [], []
    half = np.array(size) / 2
    for axis in range(3):
        other = [i for i in range(3) if i != axis]
        for sign in (-1, 1):
            points = []
            normal = np.eye(3)[axis] * sign
            for u, v in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
                point = np.zeros(3)
                point[axis] = half[axis] * sign
                point[other] = half[other] * [u, v]
                points.append(point)
            if np.dot(np.cross(points[1] - points[0], points[2] - points[0]), normal) < 0:
                points.reverse()
            first = len(vertices)
            vertices.extend(points)
            normals.extend([normal] * 4)
            indices.extend([(first, first + 1, first + 2), (first, first + 2, first + 3)])
    matrix = translated(position)
    if rotation is not None:
        matrix[:3, :3] = rotation
    return r.transform(r.mesh(vertices, indices, normal=normals,
                              color=color, name=name), matrix)


def island_source():
    island = [r.transform(m, translated((-63, 45, 12))) for m in r.gltf('Island')]
    coast = json.loads((r.RES / 'Island/Coastline.json').read_text())['points']
    for m in island:
        centers = m['v'][m['t']].mean(1)
        inside = np.zeros(len(centers), bool)
        for i, a in enumerate(coast):
            b = coast[i - 1]
            crossing = ((a['z'] > centers[:, 2]) != (b['z'] > centers[:, 2]))
            edge = ((b['x'] - a['x']) * (centers[:, 2] - a['z']) /
                    (b['z'] - a['z'] + 1e-20) + a['x'])
            inside ^= crossing & (centers[:, 0] < edge)
        m['t'] = m['t'][inside]
    return island


def ground(island, x, z):
    """Downward ray through the cropped scan, matching the world floor probe."""
    highest = -np.inf
    for m in island:
        triangles = m['v'][m['t']].astype('f8')
        a, b, c = triangles[:, 0], triangles[:, 1], triangles[:, 2]
        bx, bz = b[:, 0] - a[:, 0], b[:, 2] - a[:, 2]
        cx, cz = c[:, 0] - a[:, 0], c[:, 2] - a[:, 2]
        denominator = bx * cz - bz * cx
        valid = np.abs(denominator) > 1e-10
        denominator = np.where(valid, denominator, 1)
        u = ((x - a[:, 0]) * cz - (z - a[:, 2]) * cx) / denominator
        v = (bx * (z - a[:, 2]) - bz * (x - a[:, 0])) / denominator
        valid &= (u >= -1e-7) & (v >= -1e-7) & (u + v <= 1 + 1e-7)
        if valid.any():
            y = a[:, 1] + u * (b[:, 1] - a[:, 1]) + v * (c[:, 1] - a[:, 1])
            highest = max(highest, y[valid].max())
    if not np.isfinite(highest):
        raise ValueError(f'No scan floor at {x}, {z}')
    return np.array([x, highest, z])


def placed(source, height, position, yaw=0):
    rotated = [r.transform(m, translated((0, 0, 0), yaw)) for m in source]
    return r.fit(rotated, height, position)


@lru_cache(None)
def native_mesh(guid):
    source = r.ASSETS[guid].read_text()
    count = int(re.search(r'm_VertexCount: (\d+)', source)[1])
    size = int(re.search(r'm_DataSize: (\d+)', source)[1])
    raw = bytes.fromhex(re.search(r'_typelessdata: ([0-9a-f]+)', source)[1])
    stride = size // count
    vertices = np.ndarray((count, 3), '<f4', raw, strides=(stride, 4))
    normals = np.ndarray((count, 3), '<f4', raw, offset=12, strides=(stride, 4))
    uv = np.ndarray((count, 2), '<f4', raw, offset=40, strides=(stride, 4))
    indices = np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: ([0-9a-f]+)', source)[1]),
                            '<u4' if 'm_IndexFormat: 1' in source else '<u2').reshape(-1, 3)
    return vertices, indices, normals, uv


@lru_cache(None)
def native_material(guid):
    source = r.ASSETS[guid].read_text()
    color = re.search(r'- _BaseColor: \{r: ([\d.e+-]+), g: ([\d.e+-]+), '
                      r'b: ([\d.e+-]+), a: ([\d.e+-]+)', source)
    color = tuple(float(x) for x in color.groups()) if color else (1, 1, 1, 1)
    base = re.search(r'- _BaseMap:\s+m_Texture: \{[^}]*\}\s+'
                     r'm_Scale: \{x: ([\d.e+-]+), y: ([\d.e+-]+)\}\s+'
                     r'm_Offset: \{x: ([\d.e+-]+), y: ([\d.e+-]+)\}', source)
    texture_guid = re.search(r'- _BaseMap:\s+m_Texture: \{fileID: \d+, guid: (\w+)', source)
    texture = r.ASSETS[texture_guid[1]] if texture_guid else None
    scale = np.array([float(x) for x in base.groups()[:2]]) if base else np.ones(2)
    offset = np.array([float(x) for x in base.groups()[2:]]) if base else np.zeros(2)
    return color, texture, scale, offset


def cellhouse_source():
    source = (r.RES / 'Cellhouse/Interior.prefab').read_text()
    source = re.sub(r'^%.*\n', '', source, flags=re.M)
    source = re.sub(r'^--- !u!\d+ &(-?\d+)', r'---\nanchor: \1', source, flags=re.M)
    docs = {d['anchor']: d for d in yaml.load_all(source, Loader=yaml.CSafeLoader)}
    transforms = {i: d['Transform'] for i, d in docs.items() if 'Transform' in d}
    go_transforms = {d['m_GameObject']['fileID']: i for i, d in transforms.items()}
    objects = {i: d['GameObject'] for i, d in docs.items() if 'GameObject' in d}
    renderers = {d['MeshRenderer']['m_GameObject']['fileID']: d['MeshRenderer']
                 for d in docs.values() if 'MeshRenderer' in d}

    @lru_cache(None)
    def world(i):
        data = transforms[i]
        matrix = np.eye(4)
        matrix[:3, :3] = Rotation.from_quat([data['m_LocalRotation'][k] for k in 'xyzw']).as_matrix()
        matrix[:3, :3] @= np.diag([data['m_LocalScale'][k] for k in 'xyz'])
        matrix[:3, 3] = [data['m_LocalPosition'][k] for k in 'xyz']
        parent = data['m_Father']['fileID']
        return world(parent) @ matrix if parent else matrix

    @lru_cache(None)
    def active(i):
        data = transforms[i]
        parent = data['m_Father']['fileID']
        return objects[data['m_GameObject']['fileID']]['m_IsActive'] and (active(parent) if parent else True)

    result = []
    for doc in docs.values():
        if 'MeshFilter' not in doc:
            continue
        data = doc['MeshFilter']
        go = data['m_GameObject']['fileID']
        renderer = renderers.get(go)
        if not renderer or not renderer['m_Enabled'] or not active(go_transforms[go]):
            continue
        vertices, indices, normals, uv = native_mesh(data['m_Mesh']['guid'])
        if len(renderer['m_Materials']) != 1:
            raise ValueError('Preview decoder requires one material per native mesh')
        color, texture, scale, offset = native_material(renderer['m_Materials'][0]['guid'])
        uv = uv * scale + offset
        uv[:, 1] = 1 - uv[:, 1]
        model = r.mesh(vertices, indices, uv, normals, texture, color, objects[go]['m_Name'])
        result.append(r.transform(model, world(go_transforms[go])))
    result.append(cube('West yard security grille', (-26.5, 32, 33), (.3, 4, 8), (.12, .15, .15, 1)))
    print('Decoded active cellhouse renderers:', len(result), flush=True)
    return result


@lru_cache(None)
def character(profile):
    return Character(r.ROOT / f'Assets/Game/Resources/BlackstoneFoundation/Characters/{profile}/{profile}.fbx')


def actor(profile, position, yaw=0, hero=False, harrow=False):
    clip = animation(r.ROOT / 'Assets/Game/Foundation/Animations/Rocketbox/Idle.fbx')
    result = []
    for data in character(profile).meshes(clip, .3):
        texture = data['texture']
        color = (1, 1, 1, 1)
        material_name = data['name']
        if hero:
            material_name = 'm019_body_elias08' if 'body' in data['name'] else 'm019_head_elias08'
        if harrow:
            material_name = 'm013_body_harrow08' if 'body' in data['name'] else 'm013_head_harrow08'
        material = texture.parent / (material_name + '.mat')
        uv = data['uv'].copy()
        if material.exists():
            guid = re.search(r'^guid: (\w+)', material.with_suffix('.mat.meta').read_text(), re.M)[1]
            color, texture, scale, offset = native_material(guid)
            uv = uv * scale + offset
        uv[:, 1] = 1 - uv[:, 1]
        result.append(r.transform(r.mesh(data['v'], data['t'], uv, data['n'], texture, color), translated(position, yaw)))
    return result


def save(scene, filename, title, eye, center, fov=42):
    im = r.render(scene, (1920, 1080), eye=eye, center=center, fov=fov,
                  near_clip=1 if filename == 'Island.png' else .055,
                  background=(.6, .7, .7))
    draw = ImageDraw.Draw(im)
    draw.rectangle((0, 1004, 1920, 1080), fill='#101b21')
    draw.text((28, 1015), title, font=ImageFont.truetype(FONT, 24), fill='#efe4ce')
    draw.text((28, 1050), 'REVISION 11 / OFFLINE SOURCE PREVIEW / NOT A UNITY SCREENSHOT',
              font=ImageFont.truetype(FONT, 17), fill='#b6c5ca')
    OUT.mkdir(parents=True, exist_ok=True)
    im.convert('RGB').save(OUT / filename)
    print('Saved', filename, flush=True)


def frame_island(scene):
    vertices = np.concatenate([m['v'][np.unique(m['t'])] for m in scene
                               if m['name'] != 'Pacific Ocean'])
    center = (vertices.min(0) + vertices.max(0)) / 2
    direction = np.array([415, 280, 430], float)
    direction /= np.linalg.norm(direction)
    view = r.view(center + direction, center)
    points = (vertices - center) @ view[:3, :3].T
    q = 1 / np.tan(np.radians(42) / 2)
    distance = max((points[:, 2] + abs(points[:, 0]) * q * 1080 / 1920 / .92).max(),
                   (points[:, 2] + abs(points[:, 1]) * q / .82).max())
    return center + direction * distance, center


def main():
    island = island_source()
    landing = ground(island, -151, -5)
    for x in (-5, 0, 5):
        for z in (-5, 0, 5):
            landing[1] = max(landing[1], ground(island, -151 + x, -5 + z)[1])
    landing[1] += .08
    world = list(island)
    world.append(cube('Pacific Ocean', (0, -.65, 0), (4000, 1, 4000), (.07, .22, .26, 1)))
    world.append(cube('Helicopter landing deck', landing - (0, .16, 0), (12, .3, 12)))
    for i in range(3):
        world.append(cube('Dock practice target', landing + (-3 + i * 3, 1.35, -4), (.7, 1.1, .12)))
    world += placed(r.gltf('Helicopter'), 2.8, landing + (0, .02, 0), 110)
    guard = placed(r.police(), 1.82, ground(island, -118, 21), 180)
    lo, hi = r.bounds(guard)
    world += guard
    world += r.fit(r.gltf('Helmet'), .32, ((lo[0] + hi[0]) / 2, hi[1] - .12, (lo[2] + hi[2]) / 2), bottom=False)
    world += r.fit(r.gltf('Vest'), .58, ((lo[0] + hi[0]) / 2, lo[1] + 1.27, (lo[2] + hi[2]) / 2), bottom=False)
    world += placed(r.gltf('Dog'), .82, ground(island, -105, 25))
    world += placed(r.fbx('House'), 14, (-165, 2, 162))
    world.append(cube('House dock platform', (-165, 1.85, 162), (42, .3, 34)))
    start = ground(island, -173, 80) + (0, .15, 0)
    end = np.array([-165, 2, 147])
    delta = end - start
    forward = delta / np.linalg.norm(delta)
    right = np.cross((0, 1, 0), forward)
    right /= np.linalg.norm(right)
    rotation = np.array([right, np.cross(forward, right), forward]).T
    world.append(cube('Coastal service pier', (start + end) / 2 - (0, .12, 0),
                      (3.2, .24, np.linalg.norm(delta)), rotation=rotation))
    for i in range(9):
        point = start + (end - start) * i / 8
        world.append(cube('Pier support', (point[0], (point[1] - 1) / 2, point[2]),
                          (.24, max(1, point[1] + 1), .24)))
    eye, center = frame_island(world)
    save(world, 'Island.png', 'CURRENT ALCATRAZ ISLAND / SCANNED EXTERIOR', eye, center)

    spawn = ground(island, -147, 6) + (0, .12, 0)
    hero = actor('Male_Adult_16', spawn, 200, hero=True)
    camera = Rotation.from_euler('xy', [12, 200], degrees=True)
    facing = camera.apply((0, 0, 1))
    eye = spawn + (0, 1.45, 0) + camera.apply((.48, .08, 0)) - facing * 3.15
    save(world + hero, 'HelicopterStart.png', 'STARTING AREA / ELIAS VALE + LITTLE BIRD HELICOPTER',
         eye, eye + facing * 8, fov=58)

    interior = cellhouse_source()
    for profile, position, yaw, harrow in [
        ('Male_Adult_07', (-.8, 30.03, 25), 180, True),
        ('Male_Adult_17', (1, 30.03, -12), 0, False),
        ('Male_Adult_12', (-12, 30.03, 8), 0, False),
        ('Male_Adult_20', (12, 30.03, 12), 180, False),
        ('Male_Adult_20', (-3, 30.03, 49), 90, False),
        ('Male_Adult_20', (5, 30.03, 63), 270, False),
    ]:
        interior += actor(profile, position, yaw, harrow=harrow)
    entry = np.array([0, 30.12, -39])
    interior += actor('Male_Adult_16', entry, 0, hero=True)
    save(interior, 'Cellhouse.png', 'CONNECTED CELLHOUSE / THREE TIERS + FURNISHED CELLS',
         (.48, 32.2, -42.1), (.48, 33.9, 18), fov=58)


if __name__ == '__main__':
    main()
