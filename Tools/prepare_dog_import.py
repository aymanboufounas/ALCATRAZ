"""Remove unused exporter rig data without changing the dog's visible animation.

Run after importing the supplied archives: python Tools/prepare_dog_import.py
The original archive stays untouched. Every weighted joint's ancestor and every
one of the 17 clips is retained; mesh and retained animation payloads are checked
byte-for-byte before the packaged glTF is replaced.
"""
from pathlib import Path
import copy
import hashlib
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DOG = ROOT / 'Assets/Game/Supplied/Resources/AlcatrazSupplied/Dog'
WIDTH = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
DTYPE = {5121: '<u1', 5123: '<u2', 5125: '<u4', 5126: '<f4'}


def accessor_array(document, buffers, index):
    a = document['accessors'][index]
    if 'sparse' in a:
        raise ValueError('Dog rig compaction requires dense accessors')
    v = document['bufferViews'][a['bufferView']]
    dtype = np.dtype(DTYPE[a['componentType']])
    width = WIDTH[a['type']]
    stride = v.get('byteStride', width * dtype.itemsize)
    offset = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    return np.ndarray((a['count'], width), dtype=dtype,
                      buffer=buffers[v['buffer']], offset=offset,
                      strides=(stride, dtype.itemsize)).copy()


def compact(document, buffers):
    original = document
    d = copy.deepcopy(document)
    if len(d['skins']) != 1:
        raise ValueError('Expected the supplied dog to have one skin')
    skin = d['skins'][0]
    parents = {c: i for i, n in enumerate(d['nodes']) for c in n.get('children', [])}
    weighted = set()
    for mesh in d['meshes']:
        for primitive in mesh['primitives']:
            attrs = primitive['attributes']
            joints = accessor_array(d, buffers, attrs['JOINTS_0'])
            weights = accessor_array(d, buffers, attrs['WEIGHTS_0'])
            weighted.update(int(i) for i in joints[weights > 0])
    if not weighted or max(weighted) >= len(skin['joints']):
        raise ValueError('Invalid dog joint indices')
    joint_indices = sorted(weighted)
    keep = {skin['joints'][i] for i in joint_indices}
    keep.update(i for i, n in enumerate(d['nodes']) if 'mesh' in n)
    keep.update(i for scene in d['scenes'] for i in scene['nodes'])
    for i in list(keep):
        seen = {i}
        while i in parents:
            i = parents[i]
            if i in seen:
                raise ValueError('Cycle in the dog rig')
            seen.add(i)
            keep.add(i)
    nodes = {old: new for new, old in enumerate(sorted(keep))}
    d['nodes'] = [d['nodes'][i] for i in sorted(keep)]
    for n in d['nodes']:
        if 'children' in n:
            children = [nodes[c] for c in n['children'] if c in keep]
            if children:
                n['children'] = children
            else:
                del n['children']
    for scene in d['scenes']:
        scene['nodes'] = [nodes[i] for i in scene['nodes']]
    if 'skeleton' in skin:
        skin['skeleton'] = nodes[skin['skeleton']]
    skin['joints'] = [nodes[skin['joints'][i]] for i in joint_indices]
    for animation in d['animations']:
        channels = [c for c in animation['channels'] if c['target']['node'] in keep]
        samplers = sorted({c['sampler'] for c in channels})
        sampler_map = {old: new for new, old in enumerate(samplers)}
        animation['samplers'] = [animation['samplers'][i] for i in samplers]
        animation['channels'] = channels
        for channel in channels:
            channel['target']['node'] = nodes[channel['target']['node']]
            channel['sampler'] = sampler_map[channel['sampler']]

    payloads = list(buffers)
    def replacement(index, array):
        accessor = copy.deepcopy(d['accessors'][index])
        accessor['bufferView'] = len(d['bufferViews'])
        accessor.pop('byteOffset', None)
        accessor.pop('min', None)
        accessor.pop('max', None)
        accessor['count'] = len(array)
        data = array.tobytes()
        d['bufferViews'].append({'buffer': len(payloads), 'byteLength': len(data)})
        payloads.append(data)
        d['accessors'].append(accessor)
        return len(d['accessors']) - 1

    bind_index = skin['inverseBindMatrices']
    skin['inverseBindMatrices'] = replacement(bind_index,
        accessor_array(original, buffers, bind_index)[joint_indices])
    joint_map = np.zeros(len(original['skins'][0]['joints']), dtype=np.uint16)
    for new, old in enumerate(joint_indices):
        joint_map[old] = new
    replacements = {}
    for mesh in d['meshes']:
        for primitive in mesh['primitives']:
            attrs = primitive['attributes']
            index = attrs['JOINTS_0']
            if index not in replacements:
                array = accessor_array(original, buffers, index)
                replacements[index] = replacement(index, joint_map[array].astype(array.dtype))
            attrs['JOINTS_0'] = replacements[index]

    used = {skin['inverseBindMatrices']}
    for mesh in d['meshes']:
        for p in mesh['primitives']:
            used.update(p['attributes'].values())
            if 'indices' in p:
                used.add(p['indices'])
            for target in p.get('targets', []):
                used.update(target.values())
    for a in d['animations']:
        for s in a['samplers']:
            used.update((s['input'], s['output']))
    accessors = {old: new for new, old in enumerate(sorted(used))}
    d['accessors'] = [d['accessors'][i] for i in sorted(used)]
    skin['inverseBindMatrices'] = accessors[skin['inverseBindMatrices']]
    for mesh in d['meshes']:
        for p in mesh['primitives']:
            p['attributes'] = {key: accessors[i] for key, i in p['attributes'].items()}
            if 'indices' in p:
                p['indices'] = accessors[p['indices']]
            for target in p.get('targets', []):
                for key, i in list(target.items()):
                    target[key] = accessors[i]
    for a in d['animations']:
        for s in a['samplers']:
            s['input'], s['output'] = accessors[s['input']], accessors[s['output']]
    views = {}
    data = bytearray()
    for a in d['accessors']:
        index = a['bufferView']
        if index not in views:
            v = d['bufferViews'][index]
            start = v.get('byteOffset', 0)
            payload = payloads[v['buffer']][start:start + v['byteLength']]
            data.extend(b'\0' * ((-len(data)) % 4))
            views[index] = dict(v, buffer=0, byteOffset=len(data))
            data.extend(payload)
    view_indices = {old: new for new, old in enumerate(views)}
    d['bufferViews'] = list(views.values())
    for a in d['accessors']:
        a['bufferView'] = view_indices[a['bufferView']]
    d['buffers'] = [{'uri': 'Dog_Buffer_00.bin', 'byteLength': len(data)}]
    verify_equivalence(original, buffers, d, [data], nodes, joint_indices)
    return d, bytes(data)


def verify_equivalence(old, old_buffers, new, new_buffers, node_map, joint_indices):
    """Structural proof of identical transforms and weighted skin deformation."""
    old_parents = {c: i for i, n in enumerate(old['nodes']) for c in n.get('children', [])}
    new_parents = {c: i for i, n in enumerate(new['nodes']) for c in n.get('children', [])}
    for old_i, new_i in node_map.items():
        before = {k: v for k, v in old['nodes'][old_i].items() if k != 'children'}
        after = {k: v for k, v in new['nodes'][new_i].items() if k != 'children'}
        assert before == after, 'Retained node transform changed'
        assert new_parents.get(new_i) == node_map.get(old_parents.get(old_i)), 'Ancestor changed'
    for old_mesh, new_mesh in zip(old['meshes'], new['meshes']):
        for a, b in zip(old_mesh['primitives'], new_mesh['primitives']):
            for key, index in a['attributes'].items():
                before = accessor_array(old, old_buffers, index)
                after = accessor_array(new, new_buffers, b['attributes'][key])
                if key == 'JOINTS_0':
                    weights = accessor_array(old, old_buffers, a['attributes']['WEIGHTS_0'])
                    original_joint = np.asarray(old['skins'][0]['joints'])[before]
                    new_joint = np.asarray(new['skins'][0]['joints'])[after]
                    inverse_nodes = {v: k for k, v in node_map.items()}
                    remapped = np.vectorize(inverse_nodes.__getitem__)(new_joint)
                    assert np.array_equal(original_joint[weights > 0], remapped[weights > 0])
                else:
                    assert before.tobytes() == after.tobytes(), 'Mesh attribute changed'
            if 'indices' in a:
                assert accessor_array(old, old_buffers, a['indices']).tobytes() == accessor_array(new, new_buffers, b['indices']).tobytes()
    assert accessor_array(old, old_buffers, old['skins'][0]['inverseBindMatrices'])[joint_indices].tobytes() == accessor_array(new, new_buffers, new['skins'][0]['inverseBindMatrices']).tobytes()
    assert len(old['animations']) == len(new['animations']) == 17
    for a, b in zip(old['animations'], new['animations']):
        assert a['name'] == b['name'], 'Clip removed or renamed'
        old_channels = {(node_map[c['target']['node']], c['target']['path']): c for c in a['channels'] if c['target']['node'] in node_map}
        assert len(old_channels) == len(b['channels']), 'Required animation channel removed'
        for c in b['channels']:
            old_c = old_channels[(c['target']['node'], c['target']['path'])]
            old_s, new_s = a['samplers'][old_c['sampler']], b['samplers'][c['sampler']]
            assert old_s.get('interpolation', 'LINEAR') == new_s.get('interpolation', 'LINEAR')
            for key in ('input', 'output'):
                assert accessor_array(old, old_buffers, old_s[key]).tobytes() == accessor_array(new, new_buffers, new_s[key]).tobytes(), 'Animation payload changed'
    assert old['images'] == new['images'] and old['materials'] == new['materials']


def prepare(folder=DOG):
    path = folder / 'Dog.gltf'
    before = json.loads(path.read_text())
    buffers = [(folder / b['uri']).read_bytes() for b in before['buffers']]
    after, binary = compact(before, buffers)
    json_bytes = (json.dumps(after, ensure_ascii=False, separators=(',', ':')) + '\n').encode()
    report = {
        'status': 'PASS', 'clips': len(after['animations']),
        'skin_joints_before': len(before['skins'][0]['joints']),
        'skin_joints_after': len(after['skins'][0]['joints']),
        'nodes_before': len(before['nodes']), 'nodes_after': len(after['nodes']),
        'channels_before': sum(len(a['channels']) for a in before['animations']),
        'channels_after': sum(len(a['channels']) for a in after['animations']),
        'json_bytes_before': path.stat().st_size, 'json_bytes_after': len(json_bytes),
        'binary_bytes_after': len(binary),
        'geometry_and_weighted_animation': 'Byte-exact payloads and identical ancestor transforms verified',
        'model_sha256': hashlib.sha256(json_bytes).hexdigest(),
        'scope': 'Source equivalence; Unity import and Play Mode require Unity Editor'
    }
    (folder / 'Dog_Buffer_00.bin').write_bytes(binary)
    path.write_bytes(json_bytes)
    return report


if __name__ == '__main__':
    report = prepare()
    (ROOT / 'Validation/Revision09_DogImportChecks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
