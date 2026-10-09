"""Revision 05 source, FBX skin, recording and chapter preservation checks.

This cannot validate Unity import, Animator playback, rendering or live physics.
"""
from pathlib import Path
import hashlib, json, re, wave
import numpy as np
import yaml
from PIL import Image
from fbx_inspect import summary
from fbx_pose import Character, animation

ROOT = Path(__file__).resolve().parents[1]
RESOURCE = ROOT/'Assets/Game/Resources/BlackstoneFoundation'
ANIMATIONS = ROOT/'Assets/Game/Foundation/Animations/Rocketbox'
passed, errors = [], []

def check(ok, label):
    (passed if ok else errors).append(label)

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def blocks(text):
    parts = re.split(r'^--- !u!\d+ &(-?\d+)\n', text, flags=re.M)
    return {int(parts[i]):parts[i+1] for i in range(1,len(parts),2)}

def bone_paths(rig):
    def path(i):
        return path(rig.parents[i])+'/'+rig.names[i] if i in rig.parents else rig.names[i]
    return {rig.names[i]:path(i) for i,n in rig.models.items() if n.props[2]=='LimbNode'}

def script_guid(relative):
    return re.search(r'^guid: (\w+)', (ROOT/(relative+'.meta')).read_text(), re.M)[1]

model_counts = []
models = sorted((RESOURCE/'Characters').glob('*/*.fbx'))
check(len(models)==5, 'Five complete rigged character FBX files')
expected_clips = {'Idle','WalkSlow','Walk','WalkFast','Run','RunFast','Start','Stop','Crouch','Seated','TurnLeft','TurnRight'}
clips = sorted(ANIMATIONS.glob('*.fbx'))
check({p.stem for p in clips}==expected_clips, 'Twelve distinct supplied source animation clips')
rigs = {p.stem:animation(p) for p in clips}
for p in clips:
    info=summary(p)
    check(info['curves']>100 and rigs[p.stem].duration>.1, 'Animation curves and duration: '+p.stem)
for p in models:
    try:
        character=Character(p);info=summary(p);paths=bone_paths(character.rig)
        check(info['control_points']>3000 and info['polygons']>6000 and info['clusters']>=60,
              'Complete weighted model: '+p.stem)
        # Character() checks every vertex's total skin weight within 0.002.
        check(all(all(paths[n]==bone_paths(r)[n] for n in paths) for r in rigs.values()),
              'All weighted skeleton paths match all source clips: '+p.stem)
        rendered=character.meshes(rigs['Idle'],.4)
        points=np.concatenate([m['v'] for m in rendered])
        check(np.isfinite(points).all() and 1.6<np.ptp(points[:,1])<1.95,
              'Finite normalized idle skin sample: '+p.stem)
        check(all(m['texture'].is_file() for m in rendered), 'Body/head texture assignments: '+p.stem)
        for m in rendered:
            check((p.parent/(m['name']+'.mat')).is_file(), 'URP material: '+p.stem+'/'+m['name'])
        model_counts.append({'model':p.stem,'control_points':info['control_points'],
                             'polygons':info['polygons'],'skin_clusters':info['clusters']})
    except Exception as exc:
        errors.append('FBX skin sampling: '+p.stem+': '+str(exc))

gait=json.loads((RESOURCE/'GaitSpeeds.json').read_text())
check(len(gait['thresholds'])==6 and all(a<b for a,b in zip(gait['thresholds'],gait['thresholds'][1:])),
      'Six strictly increasing locomotion blend thresholds')
for row in gait['measurements']:
    rig=rigs[row['clip']]
    before=rig.sample(0,False)['Bip01'][:3,3]
    after=rig.sample(rig.duration,False)['Bip01'][:3,3]
    speed=np.linalg.norm((after-before)[[0,2]])*.01/rig.duration
    check(abs(speed-row['source_speed_m_s'])<.00001, 'Recorded root-travel speed: '+row['clip'])
    anchored0=rig.sample(0)['Bip01'][:3,3][[0,2]]
    anchored1=rig.sample(rig.duration)['Bip01'][:3,3][[0,2]]
    check(np.allclose(anchored0,anchored1,atol=.00001), 'Offline anchored root X/Z: '+row['clip'])

provenance=json.loads((ROOT/'Documentation/Revision05_RocketboxProvenance.json').read_text())
check(len(provenance['files'])==54, '54 source/model/texture/license provenance entries')
for record in provenance['files']:
    path=ROOT/record['path']
    check(path.is_file() and digest(path)==record['sha256'], 'Rocketbox file hash: '+record['path'])
for path in (RESOURCE/'Characters').rglob('*.png'):
    try:
        with Image.open(path) as im: im.verify()
        with Image.open(path) as im: im.load()
    except Exception as exc:
        errors.append('Character PNG decode: '+str(path.relative_to(ROOT))+': '+str(exc))
check((RESOURCE/'Characters/Male_Adult_16/m019_body_inmate.png').is_file(), 'Adapted orange inmate clothing texture')
check((ROOT/'Documentation/Licenses/Microsoft_Rocketbox_MIT.md').is_file(), 'Rocketbox MIT copyright/license included')

audio=json.loads((ROOT/'Documentation/Revision05_AudioProvenance.json').read_text())
check(len(audio['files'])==44, '44 packaged foundation sound recordings')
for record in audio['sources']:
    path=ROOT/'Tools/ArtSources/FoundationAudio'/record['name']
    check(path.is_file() and digest(path)==record['sha256'], 'Audio source hash: '+record['name'])
for record in audio['files']:
    path=ROOT/record['path']
    check(path.is_file() and digest(path)==record['sha256'], 'Sound file hash: '+path.stem)
    try:
        with wave.open(str(path)) as wav:
            count=wav.getnframes();raw=wav.readframes(count)
            check(wav.getnchannels()==1 and wav.getframerate()==48000 and wav.getsampwidth()==2 and len(raw)==count*2,
                  'Complete mono 48 kHz PCM: '+path.stem)
        values=np.frombuffer(raw,dtype='<i2').astype(float)/32768
        check(.1<float(np.max(np.abs(values)))<=.761, 'Audible unclipped sound: '+path.stem)
    except Exception as exc:
        errors.append('WAV decode: '+path.stem+': '+str(exc))
for group,count in [('Concrete',5),('Metal',5),('Wood',5),('Grass',5),('Pistol',5),('Rifle',4)]:
    files=list((RESOURCE/'Audio'/group).glob('*.wav'))
    check(len(files)==count and len({digest(p) for p in files})==count, 'Distinct recording variations: '+group)

for name in ['Knife','Pistol','Rifle']:
    path=RESOURCE/'Weapons'/(name+'.prefab')
    check(path.is_file() and 'm_Name: "Muzzle"' in path.read_text(), 'Native original equipment prefab: '+name)

scenes=ROOT/'Assets/Game/Scenes'
old_text=(scenes/'SC_BlackstoneIsland.unity').read_text()
story_text=(scenes/'SC_BlackstoneStory_Upgraded.unity').read_text()
scene_record=json.loads((ROOT/'Documentation/Revision05_Scenes.json').read_text())
check(digest(ROOT/scene_record['original_scene'])==scene_record['original_scene_sha256'], 'Original prison chapter scene unchanged')
old_blocks,new_blocks=blocks(old_text),blocks(story_text)
unchanged=[i for i,b in old_blocks.items() if not b.startswith('SceneRoots:')]
check(all(new_blocks.get(i)==old_blocks[i] for i in unchanged) and len(new_blocks)-len(old_blocks)==3,
      'Upgraded story preserves every original scene component; only the bootstrap root is added')
check('  storyMode: 1\n' in story_text, 'Upgraded chapter enables story-mode character replacement')
baseline=json.loads((ROOT/'Validation/Revision04_PreservedFiles.json').read_text())
failed=[p for p,h in baseline.items() if not (ROOT/p).is_file() or digest(ROOT/p)!=h]
check(not failed, '104 approved original code/anatomy/audio files unchanged: '+', '.join(failed))

free_text=(scenes/'SC_BlackstoneFoundation.unity').read_text()
free_docs={i:yaml.load(b,Loader=yaml.CSafeLoader) for i,b in blocks(free_text).items()}
def components(relative):
    guid=script_guid(relative)
    return [d['MonoBehaviour'] for d in free_docs.values() if 'MonoBehaviour' in d and d['MonoBehaviour']['m_Script']['guid']==guid]
actors=components('Assets/Game/Scripts/AI/PrisonActor.cs')
check(len(actors)==22, '22 player/NPC source bindings in the foundation scene')
check(sum(bool(a.get('patrolEnabled')) for a in actors)==5, 'Five preserved NPC patrol routes')
check(sum(a.get('pose') in (8,9,10) for a in actors)==6, 'Six seated activity-table actors')
targets=components('Assets/Game/Foundation/Scripts/FoundationTarget.cs')
check(len(targets)==3, 'Three interactive range targets')
names=[d['GameObject']['m_Name'] for d in free_docs.values() if 'GameObject' in d]
check(all(n in names for n in ['Metal footstep pad','Wood footstep pad','Turf footstep pad']), 'Three collision/footstep surface pads')
for name in ['Inmate canteen','Inmate showers','Inmate workshop','Upper gallery landing','Player','Officer Harrow']:
    check(name in names, 'Foundation map retains '+name)
check(all(c['m_Enabled']==0 for c in components('Assets/Game/Scripts/Missions/PrisonStoryDirector.cs')),
      'Exploration mode leaves chapter mission logic inactive')
build=(ROOT/'ProjectSettings/EditorBuildSettings.asset').read_text()
for name in ['SC_BlackstoneFoundation','SC_BlackstoneStory_Upgraded']:
    check(re.search(r'enabled: 1\s+path: Assets/Game/Scenes/'+name+r'\.unity',build) is not None,
          'Enabled build scene: '+name)

report={'status':'PASS' if not errors else 'FAIL','checks':len(passed)+len(errors),'errors':errors,
        'passed_checks':passed,'models':model_counts,
        'counts':{'character_models':len(models),'source_animation_clips':len(clips),'new_audio_clips':len(audio['files']),
                  'actors':len(actors),'training_targets':len(targets),'protected_original_files':len(baseline)},
        'scope':'File hashes, native scene bindings, source FBX hierarchy/skin sampling and PCM recordings only. Unity import, animation playback, live IK, camera, audio, rendering, gameplay and build are unverified.'}
(ROOT/'Validation/Revision05_FoundationChecks.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='passed_checks'},indent=2))
raise SystemExit(bool(errors))
