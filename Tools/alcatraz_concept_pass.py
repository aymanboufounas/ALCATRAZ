"""Revision 08: original geometry following the user-approved concept.

Decorative additions are kept outside chapter anchors and patrol corridors.
The new coastal trail is carved into the terrain before its collider is written.
"""
import json
import math
import numpy as np
from scipy.spatial import ConvexHull
from geometry import Mesh, cylinder, tube, ellipsoid

COASTAL_TRAIL = [
    (-63, 8.5, -109), (-65.5, 9, -93), (-68.5, 10, -69),
    (-72, 10.8, -45), (-75, 11.7, -20), (-79, 12.6, 5),
    (-80, 13.2, 27), (-80.2, 14.4, 48), (-76.5, 16.5, 70),
    (-71.5, 19, 89), (-61, 21, 116), (-60, 21, 116),
]


def trail_distance(x, z):
    p = np.array([x, z])
    result = math.inf
    for a, c in zip(COASTAL_TRAIL, COASTAL_TRAIL[1:]):
        a, c = np.array(a)[[0, 2]], np.array(c)[[0, 2]]
        v = c - a
        t = np.clip(np.dot(p - a, v) / max(np.dot(v, v), .0001), 0, 1)
        result = min(result, np.linalg.norm(p - a - v * t))
    return result


def fractured_rock(seed):
    """A reusable irregular convex rock with physically outward face normals."""
    rng = np.random.default_rng(seed)
    points = rng.normal(size=(96, 3))
    points /= np.linalg.norm(points, axis=1)[:, None]
    points *= rng.uniform(.72, 1.15, (96, 1))
    points[:, 1] = np.round(points[:, 1] * 5) / 5
    hull = ConvexHull(points)
    mesh = Mesh()
    for ids in hull.simplices:
        p = points[ids].copy()
        normal = np.cross(p[1] - p[0], p[2] - p[0])
        if np.dot(normal, p.mean(axis=0)) < 0:
            p = p[[0, 2, 1]]
            normal = -normal
        axis = int(np.argmax(abs(normal)))
        axes = [k for k in range(3) if k != axis]
        mesh.tri(*p, uvs=[v[axes].tolist() for v in p])
    return mesh


def prepare_materials(b):
    uw = b.uw
    uw.meta(b.BASE + '/Shaders/MarineSky.shader', 'ShaderImporter')
    for i in range(3):
        uw.save_mesh('Alc_Rock_' + str(i), fractured_rock(810 + i), 'Coast')
    texture = b.BASE + '/Art/Textures/CoastalScrub_Concept08.png'
    uw.material('Alc_Earth', [.82, .88, .80, 1], .97, texture=texture,
                normal='Assets/Game/Textures/PBR_forest_floor_Normal.png', tiling=.42)
    uw.material('Alc_Scrub', [.34, .40, .24, 1], .98, texture=texture, tiling=.8)
    uw.material('Alc_ScrubDry', [.49, .45, .30, 1], .98, texture=texture, tiling=.8)
    uw.material('Alc_TankBlue', [.43, .56, .61, 1], .68, .5,
                texture='Assets/Game/Textures/PBR_brushed_concrete_Base.png', tiling=.7)
    pale = b.BASE + '/Art/Textures/PaleCoastalRock_Concept08.png'
    uw.material('Alc_Rock', [.93, .94, .92, 1], .90,
                texture=pale, normal='Assets/Game/Textures/PBR_seaside_rock_Normal.png', tiling=.36)
    uw.material('Alc_RockPale', [.96, .97, .93, 1], .90,
                texture=pale,
                normal='Assets/Game/Textures/PBR_seaside_rock_Normal.png', tiling=.6)
    uw.material('Alc_WetRock', [.34, .39, .34, 1], .4,
                texture='Assets/Game/Textures/PBR_seaside_rock_Base.png',
                normal='Assets/Game/Textures/PBR_seaside_rock_Normal.png', tiling=.65)
    sky_path = b.BASE + '/Resources/Alcatraz/MarineSky.mat'
    original = uw.material('Alc_MarineSky', [.68, .79, .86, 1], .9,
                           shader_guid=uw.guid(b.BASE + '/Shaders/MarineSky.shader'))
    uw.write(sky_path, (b.ROOT / original).read_text())
    uw.meta(sky_path, 'NativeFormatImporter', '  mainObjectFileID: 2100000\n')


def add_coast(b, root, height):
    rng = np.random.default_rng(80826)
    # Pale fractured strata between the old outcrops disguise a rounded shoreline.
    for i in range(215):
        a = b.OUTLINE[i % len(b.OUTLINE)]
        c = b.OUTLINE[(i + 1) % len(b.OUTLINE)]
        p = a + (c - a) * rng.uniform(.03, .97)
        inward = -p / np.linalg.norm(p)
        p += inward * rng.uniform(1, 5)
        if trail_distance(*p) < 9:
            continue
        y = height(*p) * rng.uniform(.13, .31)
        geometry = b.uw.PREVIEW['meshes']['Alc_Rock_' + str(i % 3)]
        m = Mesh()
        m.v, m.n, m.uv, m.t = geometry['v'], geometry['n'], geometry['uv'], geometry['t']
        b.batched('Pale fractured shoreline', 'Alc_RockPale', m,
                  (p[0], y, p[1]), (rng.uniform(-24, 24), rng.uniform(0, 360), rng.uniform(-16, 16)),
                  (rng.uniform(2, 6), rng.uniform(3, 8), rng.uniform(2, 5)))
    # Soft shoreline variation belongs to the footprint, never a circular mask.
    foam = Mesh()
    for a, c in zip(b.OUTLINE, np.roll(b.OUTLINE, -1, axis=0)):
        d = c - a
        normal = np.array([d[1], -d[0]]) / np.linalg.norm(d)
        # OUTLINE is counterclockwise in X/Z; select outward using island centre.
        if np.dot(normal, (a + c) / 2) < 0:
            normal = -normal
        length = np.linalg.norm(d)
        for j in range(max(2, int(length / 2))):
            count = max(2, int(length / 2))
            p = a + d * j / count
            q = a + d * (j + 1) / count
            inner, outer = rng.uniform(.2, .9), rng.uniform(1.4, 3.4)
            verts = [(p[0] + normal[0] * inner, .12, p[1] + normal[1] * inner),
                     (q[0] + normal[0] * inner, .12, q[1] + normal[1] * inner),
                     (q[0] + normal[0] * outer, .12, q[1] + normal[1] * outer),
                     (p[0] + normal[0] * outer, .12, p[1] + normal[1] * outer)]
            if np.cross(np.array(verts[1]) - verts[0], np.array(verts[2]) - verts[0])[1] < 0:
                verts.reverse()
            foam.quad(*verts, uv=[(0, 0), (1, 0), (1, 1), (0, 1)])
    path = b.BASE + '/Art/Textures/CoastalScrub_Concept08.png'
    # Groundcover texture breaks the plain foam sheet into mottled fragments.
    b.uw.material('Alc_Foam', [.64, .76, .73, .25], .75, texture=path, transparent=True, tiling=1)
    b.uw.save_mesh('Alc_ShoreFoam', foam, 'Coast')


def add_trail(b, root):
    trail = b.uw.Node('Concept coastal service trail', root)
    b.road(trail, 'West coastal service trail', COASTAL_TRAIL, 2.3, 'Alc_Floor')
    for a, c in zip(COASTAL_TRAIL, COASTAL_TRAIL[1:]):
        a, c = np.array(a, float), np.array(c, float)
        d = c - a
        distance = np.linalg.norm(d[[0, 2]])
        if distance < 3:
            continue
        if c[2] >= 116:
            # Leave an eight metre opening where the old west road joins the trail.
            c = a + d * max(0, (distance - 8) / distance)
            d = c - a
            distance = np.linalg.norm(d[[0, 2]])
            if distance < 3:
                continue
        side = np.array([-d[2], 0, d[0]]) / distance
        mid = (a + c) / 2 + side * 1.25
        yaw = math.degrees(math.atan2(d[0], d[2]))
        # Short stepped sections follow elevation without blocking the 2.3 m deck.
        sections = max(1, math.ceil(abs(d[1]) / .2))
        for j in range(sections):
            aa, cc = a + d * j / sections, a + d * (j + 1) / sections
            p = (aa + cc) / 2 + side * 1.27
            run = np.linalg.norm((cc - aa)[[0, 2]])
            b.slab('Coastal trail stone parapet', trail, p + [0, .40, 0],
                   (.30, .88 + abs(cc[1] - aa[1]), run + .03), 'Alc_Stone', rot=(0, yaw, 0))
            b.b_box('Coastal trail coping', 'Alc_White', p + [0, .86, 0],
                    (.37, .09, run + .05), rot=(0, yaw, 0))
        b.slab('Coastal trail retaining face', trail, mid + [0, -2.2, 0],
               (.40, 4.35, distance + .06), 'Alc_RockPale', rot=(0, yaw, 0))
        # A rock ledge joins the path's retaining wall back to the island,
        # closing the visible seam where the trail is outside the old shoreline.
        # The road's continuous MeshCollider remains the walking surface.
        # Keep the level ledge below the lower end of each sloping road span.
        bed = (a + c) / 2 - side * 1.2 + [0, -2.22 - abs(d[1]) * .5, 0]
        b.slab('Coastal trail bedrock ledge', trail, bed,
               (4.9, 4.30, distance + .06), 'Alc_RockPale', False, rot=(0, yaw, 0))
        if distance > 7:
            for t in [.2, .8]:
                p = a + d * t + side * 1.27
                b.b_box('Coastal handrail posts', 'Alc_Rust', p + [0, 1.16, 0], (.06, .68, .06))
            b.batched('Coastal handrail', 'Alc_Rust',
                      tube([a + side * 1.27 + [0, 1.48, 0], c + side * 1.27 + [0, 1.48, 0]], .035, 6))
    b.sign(trail, 'Coastal service trail notice', (-64.1, 10.1, -106),
           'COASTAL SERVICE PATH\nAUTHORIZED PERSONNEL', (1.6, .55), 180)


def clear_site(b, x, z):
    # All low vegetation and garden rocks stay clear of every walkable floor.
    for landmark in b.LANDMARKS:
        lx, _, lz = landmark['position']
        w, _, d = landmark['size']
        if abs(x - lx) < w / 2 + 2 and abs(z - lz) < d / 2 + 2:
            return False
    for points, width in b.PATH_CUTS:
        for a, c in zip(points, points[1:]):
            p, q = np.array(a)[[0, 2]], np.array(c)[[0, 2]]
            v = q - p
            t = np.clip(np.dot(np.array([x, z]) - p, v) / max(np.dot(v, v), .0001), 0, 1)
            if np.linalg.norm(np.array([x, z]) - p - v * t) < width / 2 + 1.6:
                return False
    return True


def add_scrub(b, root, height):
    from matplotlib.path import Path as Polygon
    outline = Polygon(b.OUTLINE)
    rng = np.random.default_rng(80828)
    for i in range(500):
        x, z = rng.uniform(-74, 87), rng.uniform(-165, 166)
        if not outline.contains_point((x, z)) or not clear_site(b, x, z):
            continue
        y = height(x, z)
        # Three overlapping clumps create volume without transparent leaf overdraw.
        material = 'Alc_ScrubDry' if i % 5 == 0 else 'Alc_Scrub'
        for k in range(3):
            width = rng.uniform(.38, 1.35)
            pos = (x + rng.uniform(-.7, .7), y + .16, z + rng.uniform(-.7, .7))
            b.batched('Salt tolerant coastal scrub', material,
                      ellipsoid((width, rng.uniform(.25, .65), width * .8), 5, 8), pos)
        if i % 3 == 0:
            b.batched('Garden exposed stone', 'Alc_RockPale', fractured_rock(820 + i % 3),
                      (x + .9, y + .15, z), (0, rng.uniform(0, 360), 0), (.7, .4, .6))


def add_architecture(b, root):
    # Existing silhouettes stay intact; trims, joints and utilities add human scale.
    for name, x, y, z, w, d, h in [
        ('Waterfront barracks', 65, 5, -91, 32, 39, 12),
        ('Storehouse', 70, 5, -30, 28, 39, 7),
        ('Power house', 62, 7.3, 113, 28, 34, 9),
        ('North industries', -38, 9.3, 122, 29, 42, 9),
    ]:
        for s in [-1, 1]:
            for yy in [1.1, h - .3]:
                b.b_box('Weathered facade cornices', 'Alc_Stone',
                        (x + s * (w / 2 + .12), y + yy, z), (.28, .18, d + .25))
            for zz in np.arange(z - d / 2 + .5, z + d / 2, 6.0):
                b.b_box('Facade downpipes', 'Alc_Rust',
                        (x + s * (w / 2 + .20), y + h / 2, float(zz)), (.08, h - .4, .08))
            for zz in [z - d / 2 + 1, z + d / 2 - 1]:
                b.b_box('Facade corner pilasters', 'Alc_White',
                        (x + s * (w / 2 + .08), y + h / 2, zz), (.20, h, .40))
        for s in [-1, 1]:
            b.b_box('Roof perimeter coping', 'Alc_White',
                    (x, y + h + .25, z + s * (d / 2 + .1)), (w + .7, .25, .35))
        for zz in [z - d * .2, z + d * .2]:
            b.batched('Roof vent stacks', 'Alc_DarkSteel', cylinder(.22, .8, 10), (x, y + h + .5, zz))
    # Main cellhouse rainwater runs frame the existing window recesses.
    for x in [-26.78, 26.78]:
        for z in [-40, -16, 8, 32]:
            b.b_box('Cellhouse rainwater downpipes', 'Alc_Rust', (x, 35.2, z), (.075, 10.2, .075))
    for x in [-19, -6, 6, 19]:
        for z in [-37, 38]:
            b.b_box('Cellhouse roof maintenance plates', 'Alc_Iron', (x, 41.1, z), (1.2, .07, 2.3))


def add_details(b, root, lights, height):
    add_coast(b, root, height)
    add_trail(b, root)
    add_scrub(b, root, height)
    add_architecture(b, root)
    b.flush_batches(root)
    b.uw.write('Documentation/Revision08_ConceptImplementation.json', json.dumps({
        'revision': '08', 'approved_concept': 'Documentation/ApprovedConcept/Alcatraz_MapCharacters.png',
        'coastal_trail': COASTAL_TRAIL, 'trail_width_metres': 2.3,
        'visual_target': 'Reference-video island footprint and approved marine-daylight concept',
        'character_rigs': 'Existing MIT Rocketbox rigs; new head albedo and per-character materials',
        'limitations': ['Concept is an art target, not a Unity capture',
                        'No imported photogrammetry island or bespoke sculpted faces',
                        'Unity import, Play Mode and performance require local verification']
    }, indent=2) + '\n')
