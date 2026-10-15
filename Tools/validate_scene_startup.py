"""Check serialized startup bindings in every enabled build scene.

These are source checks, not Unity import, compilation, rendering, or Play Mode.
No tracked validation report is rewritten unless --report is supplied.
"""
from pathlib import Path
import argparse
import json
import re

import yaml

ROOT = Path(__file__).resolve().parents[1]
NATIVE_TYPES = {1: 'GameObject', 4: 'Transform', 20: 'Camera',
                81: 'AudioListener', 114: 'MonoBehaviour', 143: 'CharacterController'}
SCRIPTS = {
    'movement': 'Assets/_DesertShift/Scripts/Player/PlayerMovement.cs',
    'input': 'Assets/_DesertShift/Scripts/Player/PlayerInputHandler.cs',
    'actor': 'Assets/Game/Scripts/AI/PrisonActor.cs',
    'bootstrap': 'Assets/Game/Foundation/Scripts/FoundationBootstrap.cs',
}


def documents(text):
    result = {}
    for match in re.finditer(r'^--- !u!(\d+) &(-?\d+)\n(.*?)(?=^--- !u!|\Z)', text, re.M | re.S):
        kind, file_id, body = int(match[1]), int(match[2]), match[3]
        decoded = yaml.load(body, Loader=yaml.CSafeLoader)
        result[file_id] = (kind, next(iter(decoded)), next(iter(decoded.values())))
    return result


def inspect_scene(path, script_guids):
    errors, checks = [], 0
    docs = documents(path.read_text())

    def check(condition, label):
        nonlocal checks
        checks += 1
        if not condition:
            errors.append(label)

    def items(kind):
        return [(file_id, value) for file_id, (native, _, value) in docs.items() if native == kind]

    def components(role):
        return [(file_id, value) for file_id, value in items(114)
                if value.get('m_Script', {}).get('guid') == script_guids[role]]

    def active(game_id):
        visited = set()
        while game_id:
            if game_id in visited or game_id not in docs:
                return False
            visited.add(game_id)
            _, name, game = docs[game_id]
            if name != 'GameObject' or not game.get('m_IsActive'):
                return False
            transform = next((docs.get(c['component']['fileID']) for c in game.get('m_Component', [])
                              if docs.get(c['component']['fileID'], (0,))[0] == 4), None)
            if transform is None:
                return False
            scale = transform[2].get('m_LocalScale', {})
            if any(abs(scale.get(axis, 0)) < .0001 for axis in ('x', 'y', 'z')):
                return False
            parent_id = transform[2].get('m_Father', {}).get('fileID', 0)
            if not parent_id:
                return True
            game_id = docs.get(parent_id, (0, '', {}))[2].get('m_GameObject', {}).get('fileID', 0)
            if not game_id:
                return False
        return False

    for file_id, (kind, type_name, value) in docs.items():
        if kind in NATIVE_TYPES:
            check(type_name == NATIVE_TYPES[kind], f'{file_id}: native class ID {kind} does not match {type_name}')
        if kind == 114:
            binding = value.get('m_Script', {})
            check(binding.get('fileID') == 11500000 and bool(binding.get('guid')),
                  f'{file_id}: MonoBehaviour has no native script binding')

    players = components('movement')
    check(len(players) == 1, 'scene must contain exactly one PlayerMovement')
    if players:
        _, movement = players[0]
        game_id = movement['m_GameObject']['fileID']
        check(movement.get('m_Enabled') == 1 and active(game_id), 'player and ancestor transforms must be active with nonzero scale')
        for role in ('input', 'actor'):
            check(any(c['m_GameObject']['fileID'] == game_id and c.get('m_Enabled') == 1
                      for _, c in components(role)), f'player must have enabled {role} binding')
        check(any(c['m_GameObject']['fileID'] == game_id and c.get('m_Enabled') == 1
                  for _, c in items(143)), 'player must have an enabled CharacterController')
        target = docs.get(movement.get('cameraTarget', {}).get('fileID'), (0, '', {}))
        check(target[0] == 4 and target[2].get('m_Father', {}).get('fileID') in
              [file_id for file_id, transform in items(4) if transform['m_GameObject']['fileID'] == game_id],
              'camera target must be a child of the player transform')

    bootstraps = components('bootstrap')
    check(len(bootstraps) == 1 and bootstraps[0][1].get('m_Enabled') == 1
          and active(bootstraps[0][1]['m_GameObject']['fileID']), 'scene must have one enabled, active character/camera bootstrap')
    cameras = [(file_id, camera) for file_id, camera in items(20)
               if camera.get('m_Enabled') == 1 and active(camera['m_GameObject']['fileID'])
               and docs[camera['m_GameObject']['fileID']][2].get('m_TagString') == 'MainCamera']
    check(len(cameras) == 1, 'scene must have exactly one enabled, active MainCamera')
    if cameras:
        _, camera = cameras[0]
        check(camera.get('orthographic') == 0 and .01 <= camera.get('near clip plane', 0) <= .1,
              'gameplay camera must use perspective with a close near clip plane')
        camera_id = camera['m_GameObject']['fileID']
        listeners = [(file_id, listener) for file_id, listener in items(81)
                     if listener.get('m_Enabled') == 1 and active(listener['m_GameObject']['fileID'])]
        check(len(listeners) == 1 and listeners[0][1]['m_GameObject']['fileID'] == camera_id,
              'MainCamera must own the scene\'s single enabled native AudioListener (class ID 81)')
        if players:
            player_id = players[0][1]['m_GameObject']['fileID']
            layer = docs[player_id][2].get('m_Layer', 0)
            check(camera.get('m_CullingMask', {}).get('m_Bits', 0) & (1 << layer), 'gameplay camera must include the player layer')
    return checks, errors


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    build = yaml.load(re.sub(r'^%.*\n|^--- !u!\d+ &-?\d+\n', '',
                            (ROOT / 'ProjectSettings/EditorBuildSettings.asset').read_text(), flags=re.M),
                      Loader=yaml.CSafeLoader)['EditorBuildSettings']
    script_guids = {role: re.search(r'^guid: (\w+)', (ROOT / (path + '.meta')).read_text(), re.M)[1]
                    for role, path in SCRIPTS.items()}
    results = []
    for scene in build['m_Scenes']:
        if scene['enabled']:
            checks, errors = inspect_scene(ROOT / scene['path'], script_guids)
            results.append({'scene': scene['path'], 'checks': checks, 'errors': errors})
    report = {'status': 'FAIL' if any(scene['errors'] for scene in results) else 'PASS',
              'checks': sum(scene['checks'] for scene in results), 'scenes': results,
              'scope': 'Serialized startup bindings only; Unity import, compilation and Play Mode remain unverified.'}
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    raise SystemExit(report['status'] != 'PASS')


if __name__ == '__main__':
    run()
