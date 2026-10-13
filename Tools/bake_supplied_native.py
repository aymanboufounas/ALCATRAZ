"""Bake the nine supplied models into native Unity assets, including the dog rig.

The default game uses these committed assets rather than requiring a successful
glTF editor reimport at Play. Original model data and all 17 dog clips are retained.
Requires Tools/requirements-supplied.txt; no Unity Editor is used by this tool.
"""
import hashlib
import json
import re
import zlib
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from scipy.spatial.transform import Rotation

import render_supplied_previews as r
import unity_writer as u

BASE = 'Assets/Game/Supplied/Resources/AlcatrazSupplied/Baked'
u.ART = BASE
u.CLASSES[111] = 'Animation'


def metadata():
    for p in sorted((u.ROOT / BASE).rglob('*')):
        rel = str(p.relative_to(u.ROOT))
        if p.is_dir():
            u.write(rel + '.meta', 'fileFormatVersion: 2\nguid: ' + u.guid(rel) +
                    '\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n')
        elif p.suffix != '.meta' and not Path(str(p) + '.meta').exists():
            u.meta(rel, 'TextScriptImporter' if p.suffix == '.json' else 'DefaultImporter')
    u.write(BASE + '.meta', 'fileFormatVersion: 2\nguid: ' + u.guid(BASE) +
            '\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n')


def material(name, data):
    texture = str(Path(data['texture']).relative_to(u.ROOT)) if data['texture'] else None
    color=list(data['color'])
    glass=name.startswith('Helicopter_') and data['name']=='vidrio'
    # glTF transmission is not represented by baseColor alpha. Approximate the
    # source transmissive cockpit with standard URP transparent, double-sided glass.
    if glass:color[3]=.18
    path=u.material(name,color,rough=.05 if glass else .85,texture=texture,
                    transparent=color[3]<.99)
    if glass:
        source=(u.ROOT/path).read_text().replace('- _Cull: 2','- _Cull: 0')
        u.write(path,source)
    return path


def mesh_parts(name, data, weights=None, joints=None, bind=None):
    """Keep each native vertex buffer small and indices valid after remapping."""
    triangles = np.asarray(data['t']).reshape(-1, 3)
    if weights is None:
        # FBX polygon corners repeat identical attributes. Weld exact visual
        # vertices instead of shipping three copies of every triangle corner.
        attrs = np.round(np.c_[data['v'], data['n'], data['uv']], 6).astype('f4')
        keys = np.ascontiguousarray(attrs).view(np.dtype((np.void, attrs.dtype.itemsize * attrs.shape[1]))).reshape(-1)
        _, first, inverse = np.unique(keys, return_index=True, return_inverse=True)
        data = {**data, 'v': data['v'][first], 'n': data['n'][first], 'uv': data['uv'][first]}
        triangles = inverse[triangles]
    result = []
    for start in range(0, len(triangles), 20000):
        selected = triangles[start:start + 20000]
        used, mapped = np.unique(selected, return_inverse=True)
        key = name + '_' + str(start // 20000)
        uv = data['uv'][used].copy()
        uv[:, 1] = 1 - uv[:, 1]
        mesh = SimpleNamespace(v=data['v'][used], n=data['n'][used], uv=uv,
                               t=mapped.reshape(-1).tolist())
        path = u.save_mesh(key, mesh, folder='Meshes')
        u.PREVIEW['meshes'].pop(key, None)
        if weights is not None:
            # Unity's interleaved BoneWeight layout: four weights, four indices.
            source = (u.ROOT / path).read_text()
            raw = bytes.fromhex(re.search(r'_typelessdata: ([0-9a-f]+)', source)[1])
            vertices = np.frombuffer(raw, '<f4').reshape(-1, 12)
            dtype = np.dtype([('vertex', '<f4', 12), ('weight', '<f4', 4), ('joint', '<u4', 4)])
            packed = np.empty(len(used), dtype)
            packed['vertex'] = vertices
            packed['weight'] = weights[used]
            packed['joint'] = joints[used]
            source = re.sub(r'm_DataSize: \d+', 'm_DataSize: ' + str(packed.nbytes), source)
            source = re.sub(r'_typelessdata: [0-9a-f]+', '_typelessdata: ' + packed.tobytes().hex(), source)
            # Last two vertex channels are blend weights and blend indices.
            marker = '    m_DataSize:'
            first, last = source.split(marker, 1)
            channels = list(re.finditer(r'    - stream: 0\n      offset: \d+\n      format: \d+\n      dimension: \d+\n', first))
            for index, replacement in reversed([(12, (48, 0, 4)), (13, (64, 10, 4))]):
                match = channels[index]
                off, fmt, dim = replacement
                first = first[:match.start()] + f'    - stream: 0\n      offset: {off}\n      format: {fmt}\n      dimension: {dim}\n' + first[match.end():]
            source = first + marker + last
            matrices = '\n' + ''.join('  - ' + '\n    '.join(
                f'e{a}{b}: {matrix[a,b]:.8g}' for a in range(4) for b in range(4)) + '\n' for matrix in bind)
            source = source.replace('m_BindPose: []', 'm_BindPose: ' + matrices.rstrip())
            u.write(path, source)
        result.append((key, path))
    return result


def prefab(root, name):
    def walk(node):
        return [node] + [child for n in node.children for child in walk(n)]
    path = BASE + '/' + name + '.prefab'
    u.write(path, u.HEAD + ''.join(u.node_yaml(n, n is root) for n in walk(root)))
    u.meta(path, 'PrefabImporter')
    return path


def bake_static(name):
    u.Node.all = []
    u.Node.counter = 42000000
    root = u.Node(name, static=False)
    data = r.gltf(name) if name in ['Island', 'Helmet', 'Vest', 'Helicopter'] else r.police() if name == 'Police' else r.fbx(name)
    kept = 0
    coast = json.loads((r.RES / 'Island/Coastline.json').read_text())['points']
    for index, model in enumerate(data):
        if name == 'Island':
            centers = model['v'][model['t']].mean(1) + [-63, 45, 12]
            inside = np.zeros(len(centers), bool)
            for i, a in enumerate(coast):
                b = coast[i-1]
                inside ^= ((a['z'] > centers[:, 2]) != (b['z'] > centers[:, 2])) & (
                    centers[:, 0] < (b['x']-a['x']) * (centers[:, 2]-a['z']) / (b['z']-a['z']+1e-20) + a['x'])
            model['t'] = model['t'][inside]
        if not len(model['t']):
            continue
        key = name + '_' + str(index)
        material(key, model)
        for mesh, path in mesh_parts(key, model):
            node = u.Node(model['name'] or mesh, root, static=False).render(mesh, key)
            if name in ['Island', 'House']:
                node.meshcollider(mesh)
        kept += len(model['t'])
    path = prefab(root, name)
    for generated in (u.ROOT/BASE).rglob(name+'*'):
        if generated.is_file() and generated.suffix in ('.meta','.asset','.mat','.prefab'):
            text=generated.read_text();clean='\n'.join(line.rstrip() for line in text.splitlines())+'\n'
            if text!=clean:u.write(str(generated.relative_to(u.ROOT)),clean)
    print(name, kept, 'triangles', flush=True)
    return {'prefab': path, 'triangles': kept, 'format': 'native Unity mesh/prefab'}


def clip(path, name, curves, duration):
    text = u.HEAD + f'--- !u!74 &7400000\nAnimationClip:\n  m_ObjectHideFlags: 0\n  m_CorrespondingSourceObject: {{fileID: 0}}\n  m_PrefabInstance: {{fileID: 0}}\n  m_PrefabAsset: {{fileID: 0}}\n  m_Name: {json.dumps(name)}\n  serializedVersion: 7\n  m_Legacy: 1\n  m_Compressed: 0\n  m_UseHighQualityCurve: 1\n'
    bindings = []
    for field, attribute, dimension in [('m_RotationCurves', 2, 4), ('m_PositionCurves', 1, 3), ('m_ScaleCurves', 3, 3)]:
        rows = [row for row in curves if row[0] == attribute]
        text += f'  {field}:' + ('\n' if rows else ' []\n')
        for _, node_path, times, values in rows:
            if np.all(np.abs(values-values[0]) < 1e-7):
                times, values = times[:1], values[:1]
            text += '  - curve:\n      serializedVersion: 2\n      m_Curve:\n'
            slopes = np.gradient(values, times, axis=0) if len(times) > 1 else np.zeros_like(values)
            for t, value, slope in zip(times, values, slopes):
                text += f'      - serializedVersion: 3\n        time: {float(t):.7g}\n        value: {u.vec(value)}\n        inSlope: {u.vec(slope)}\n        outSlope: {u.vec(slope)}\n        tangentMode: 0\n        weightedMode: 0\n        inWeight: {u.vec(np.zeros(dimension))}\n        outWeight: {u.vec(np.zeros(dimension))}\n'
            text += '      m_PreInfinity: 2\n      m_PostInfinity: 2\n      m_RotationOrder: 4\n    path: ' + json.dumps(node_path) + '\n'
            bindings.append((zlib.crc32(node_path.encode()) & 0xffffffff, attribute))
    text += '  m_CompressedRotationCurves: []\n  m_EulerCurves: []\n  m_FloatCurves: []\n  m_PPtrCurves: []\n  m_SampleRate: 30\n  m_WrapMode: 2\n  m_Bounds:\n    m_Center: {x: 0, y: 0, z: 0}\n    m_Extent: {x: 10, y: 10, z: 10}\n  m_ClipBindingConstant:\n    genericBindings:\n'
    for node_hash, attribute in bindings:
        text += f'    - serializedVersion: 2\n      path: {node_hash}\n      attribute: {attribute}\n      script: {{fileID: 0}}\n      typeID: 4\n      customType: 0\n      isPPtrCurve: 0\n      isIntCurve: 0\n      isSerializeReferenceCurve: 0\n'
    text += f'    pptrCurveMapping: []\n  m_AnimationClipSettings:\n    serializedVersion: 2\n    m_AdditiveReferencePoseClip: {{fileID: 0}}\n    m_AdditiveReferencePoseTime: 0\n    m_StartTime: 0\n    m_StopTime: {duration:.7g}\n    m_OrientationOffsetY: 0\n    m_Level: 0\n    m_CycleOffset: 0\n    m_HasAdditiveReferencePose: 0\n    m_LoopTime: 1\n    m_LoopBlend: 0\n    m_LoopBlendOrientation: 0\n    m_LoopBlendPositionY: 0\n    m_LoopBlendPositionXZ: 0\n    m_KeepOriginalOrientation: 1\n    m_KeepOriginalPositionY: 1\n    m_KeepOriginalPositionXZ: 1\n    m_HeightFromFeet: 0\n    m_Mirror: 0\n  m_EditorCurves: []\n  m_EulerEditorCurves: []\n  m_HasGenericRootTransform: 0\n  m_HasMotionFloatCurves: 0\n  m_Events: []\n'
    u.write(path, text)
    u.meta(path, 'NativeFormatImporter', '  mainObjectFileID: 7400000\n')


def bake_dog():
    d = json.loads((r.RES / 'Dog/Dog.gltf').read_text())
    buffers = [(r.RES / 'Dog' / b['uri']).read_bytes() for b in d['buffers']]
    from prepare_dog_import import accessor_array
    def accessor(i):
        return accessor_array(d, buffers, i)
    u.Node.all = []
    u.Node.counter = 42000000
    root = u.Node('Dog', static=False)
    parents = {c: i for i, n in enumerate(d['nodes']) for c in n.get('children', [])}
    nodes = {}
    def node(i):
        if i not in nodes:
            data = d['nodes'][i]
            parent = node(parents[i]) if i in parents else root
            if 'matrix' in data:
                m = np.array(data['matrix']).reshape(4, 4).T
                scale = np.linalg.norm(m[:3, :3], axis=0)
                q = Rotation.from_matrix(m[:3, :3] / scale).as_quat()
                position = m[:3, 3]
            else:
                q = np.array(data.get('rotation', [0, 0, 0, 1]))
                position = np.array(data.get('translation', [0, 0, 0]))
                scale = data.get('scale', [1, 1, 1])
            q *= [1, -1, -1, 1]
            nodes[i] = u.Node(data.get('name', 'Joint') + '_' + str(i), parent,
                              pos=position * [-1, 1, 1], rot=Rotation.from_quat(q).as_euler('xyz', degrees=True), scale=scale, static=False)
        return nodes[i]
    for i in range(len(d['nodes'])):
        node(i)
    def node_path(i):
        return node_path(parents[i]) + '/' + nodes[i].name if i in parents else nodes[i].name
    count = 0
    for i, data in enumerate(d['nodes']):
        if 'mesh' not in data:
            continue
        for j, primitive in enumerate(d['meshes'][data['mesh']]['primitives']):
            attrs = primitive['attributes']
            color = d['materials'][primitive['material']].get('pbrMetallicRoughness', {})
            texture = d['textures'][color['baseColorTexture']['index']]['source']
            model = r.mesh(accessor(attrs['POSITION']) * [-1, 1, 1], accessor(primitive['indices']).reshape(-1, 3)[:, [0, 2, 1]],
                           accessor(attrs['TEXCOORD_0']), accessor(attrs['NORMAL']) * [-1, 1, 1],
                           r.RES / 'Dog' / d['images'][texture]['uri'], color.get('baseColorFactor', [1, 1, 1, 1]))
            key = 'Dog_' + str(i) + '_' + str(j)
            material(key, model)
            skin = d['skins'][data['skin']]
            inverse = accessor(skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
            f = np.diag([-1, 1, 1, 1])
            inverse = f @ inverse @ f
            weights = accessor(attrs['WEIGHTS_0']).astype(float)
            weights /= weights.sum(1)[:, None]
            joints = accessor(attrs['JOINTS_0']).astype(int)
            for mesh, path in mesh_parts(key, model, weights, joints, inverse):
                child = u.Node(mesh, nodes[i], static=False)
                body = u.renderer_body(u.MATERIALS[key]) + f'  m_Quality: 4\n  m_UpdateWhenOffscreen: 1\n  m_SkinnedMotionVectors: 1\n  m_Mesh: {u.ref(path)}\n  m_Bones:\n'
                body += ''.join('  - {fileID: ' + str(nodes[b].tid) + '}\n' for b in skin['joints'])
                body += '  m_BlendShapeWeights: []\n  m_RootBone: {fileID: ' + str(nodes[skin['joints'][0]].tid) + '}\n  m_AABB:\n    m_Center: {x: 0, y: 0, z: 0}\n    m_Extent: {x: 10, y: 10, z: 10}\n  m_DirtyAABB: 0\n'
                child.component(137, body)
            count += len(model['t'])
    clips = []
    for i, animation in enumerate(d['animations']):
        curves, duration = [], 0
        for channel in animation['channels']:
            target = channel['target']
            if target['path'] not in ['rotation', 'translation', 'scale']:
                continue
            sampler = animation['samplers'][channel['sampler']]
            times = accessor(sampler['input']).reshape(-1)
            values = accessor(sampler['output']).copy()
            if sampler.get('interpolation') == 'CUBICSPLINE':
                values = values.reshape(len(times), 3, -1)[:, 1]
            duration = max(duration, times[-1])
            if target['path'] == 'rotation':
                values *= [1, -1, -1, 1]
                for k in range(1, len(values)):
                    if np.dot(values[k-1], values[k]) < 0:
                        values[k] *= -1
                attribute = 2
            elif target['path'] == 'translation':
                values *= [-1, 1, 1]
                attribute = 1
            else:
                attribute = 3
            curves.append((attribute, node_path(target['node']), times, values))
        path = BASE + '/Animations/Dog_' + str(i) + '.anim'
        clip(path, animation.get('name', 'Dog clip ' + str(i)), curves, duration)
        clips.append(path)
    idle = next((p for p, a in zip(clips, d['animations']) if 'idle 0_30' in a.get('name', '').lower()), clips[0])
    root.component(111, '  m_Enabled: 1\n  serializedVersion: 3\n  m_Animation: ' + u.ref(idle, 7400000) + '\n  m_Animations:\n' + ''.join('  - ' + u.ref(p, 7400000) + '\n' for p in clips) + '  m_WrapMode: 0\n  m_PlayAutomatically: 0\n  m_AnimatePhysics: 0\n  m_CullingType: 0\n')
    path = prefab(root, 'Dog')
    print('Dog', count, 'triangles /', len(clips), 'native Legacy clips', flush=True)
    return {'prefab': path, 'triangles': count, 'clips': clips, 'joints': 200, 'format': 'native skinned mesh and Legacy clips'}


def main():
    rows = {name: bake_static(name) for name in ['Island', 'Pistol10mm', 'Revolver', 'Police', 'Helmet', 'Vest', 'Helicopter', 'House']}
    rows['Dog'] = bake_dog()
    u.write(BASE + '/Manifest.json', json.dumps({'revision': 12, 'models': rows, 'scope': 'Native source conversion; Unity import and playback require Editor validation'}, indent=2) + '\n')
    metadata()


if __name__ == '__main__':
    main()
