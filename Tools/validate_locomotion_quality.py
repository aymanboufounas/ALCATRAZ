"""Verify licensed transition sources, rig compatibility and measured gait phases.

Samples actual FBX data. This does not run Unity import, Animator or physics.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import numpy as np
from fbx_pose import Character, animation

ROOT = Path(__file__).resolve().parents[1]
CLIPS = ROOT / 'Assets/Game/Foundation/Animations/Rocketbox'


def validate():
    checks = 0
    errors = []

    def check(condition, message):
        nonlocal checks
        checks += 1
        if not condition:
            errors.append(message)

    provenance = json.loads((ROOT / 'Documentation/LocomotionClipProvenance.json').read_text())
    original = json.loads((ROOT / 'Documentation/Revision05_RocketboxProvenance.json').read_text())
    check(provenance['repository_commit'] == original['repository_commit'], 'Transition sources use the existing pinned upstream commit.')
    check(provenance['license'] == 'MIT', 'Transition license is MIT.')
    check(hashlib.sha256((ROOT / provenance['license_file']).read_bytes()).hexdigest() == provenance['license_sha256'], 'The original MIT copyright/license is retained.')
    transitions = {}
    for row in provenance['files']:
        path = ROOT / row['path']
        data = path.read_bytes()
        check(hashlib.sha256(data).hexdigest() == row['sha256'], f'Source SHA256: {path.name}')
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        check(blob == row['git_blob_sha1'] and blob.startswith(row['upstream_html_blob_prefix']), f'Recorded source identity: {path.name}')
        check(f"/{provenance['repository_commit']}/" in row['source_url'], f'Pinned source URL: {path.name}')
        metadata = Path(str(path) + '.meta')
        check(metadata.is_file() and re.search(r'^guid: [a-f0-9]{32}$', metadata.read_text(), re.M) is not None, f'Unity GUID: {path.name}')
        rig = animation(path)
        check(.2 < rig.duration < 2, f'Usable transient duration: {path.name}')
        root_start = rig.sample(0, False)['Bip01'][:3, 3]
        root_end = rig.sample(rig.duration, False)['Bip01'][:3, 3]
        check(root_end[2] - root_start[2] > 30, f'Original running transition has forward root travel: {path.name}')
        check(np.allclose(rig.sample(0)['Bip01'][[0, 2], 3], rig.sample(rig.duration)['Bip01'][[0, 2], 3]), f'In-place sampling anchors root XZ: {path.name}')
        transitions[path.stem] = rig
    check(set(transitions) == {'RunStart', 'RunStop'}, 'Both running transitions are present.')

    def paths(rig):
        def full(bone):
            return full(rig.parents[bone]) + '/' + rig.names[bone] if bone in rig.parents else rig.names[bone]
        return {name: full(bone) for bone, name in rig.names.items()}

    pairs = []
    sampled_poses = 0
    for path in sorted((ROOT / 'Assets/Game/Resources/BlackstoneFoundation/Characters').glob('*/*.fbx')):
        character = Character(path)
        expected_paths = paths(character.rig)
        weighted = {cluster[0] for cluster in character.clusters}
        for name, rig in transitions.items():
            clip_paths = paths(rig)
            check(all(bone in clip_paths and clip_paths[bone] == expected_paths[bone] for bone in weighted), f'All weighted bone paths match: {path.stem}/{name}')
            heights = []
            centers = []
            for t in np.linspace(0, rig.duration, 9):
                points = np.concatenate([mesh['v'] for mesh in character.meshes(rig, t)])
                lower, upper = points.min(axis=0), points.max(axis=0)
                height = float(upper[1] - lower[1])
                horizontal_center = float(np.linalg.norm(((lower + upper) * .5)[[0, 2]]))
                check(np.isfinite(points).all() and 1.2 < height < 2.1 and horizontal_center < .8, f'Finite, plausible weighted body: {path.stem}/{name} at {t:.3f}s')
                heights.append(height)
                centers.append(horizontal_center)
                sampled_poses += 1
            pairs.append({'character': path.stem, 'clip': name, 'seconds': float(rig.duration),
                          'weighted_bones': len(weighted), 'min_height_m': min(heights),
                          'max_height_m': max(heights), 'max_horizontal_center_m': max(centers)})
    check(len(pairs) == 10, 'Both transitions fit all five shipped character rigs.')

    # Compare actual right-foot lift curves. The old slow walk was nearly
    # opposite in phase to its adjacent blend partner, causing feet to cancel.
    curves = {}
    times = np.arange(120) / 120
    for name in ['WalkSlow', 'Walk', 'WalkFast', 'Run', 'RunFast']:
        rig = animation(CLIPS / f'{name}.fbx')
        curve = np.array([rig.sample(t * rig.duration)['Bip01 R Foot'][1, 3] for t in times])
        curves[name] = (curve - curve.mean()) / curve.std()
    aligned = np.roll(curves['WalkSlow'], -60)
    phases = []
    for name in ['Walk', 'WalkFast', 'Run', 'RunFast']:
        before = float(np.dot(curves['WalkSlow'], curves[name]) / 120)
        after = float(np.dot(aligned, curves[name]) / 120)
        check(after > .5 and after > before + .8, f'Half-cycle slow walk offset aligns foot lift with {name}.')
        phases.append({'reference': name, 'slow_walk_cycle_offset': .5,
                       'correlation_before': before, 'correlation_after': after})
    return {'status': 'FAIL' if errors else 'PASS', 'checks': checks, 'errors': errors,
            'source_transition_pairs': pairs, 'sampled_weighted_poses': sampled_poses,
            'measured_phase_alignment': phases,
            'scope': 'Pinned source hashes/license, FBX weighted bone paths, 90 sampled weighted body poses and source foot-lift phase correlation. Unity import, animation graph evaluation, physics, rendering and visual quality remain unverified.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    result = validate()
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(result['status'] != 'PASS')
