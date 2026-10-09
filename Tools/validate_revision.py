"""Revision 02 asset/binding checks. Does not execute Unity or certify Play Mode."""
from pathlib import Path
import hashlib, json, re, wave
import numpy as np
from PIL import Image
import yaml

ROOT = Path(__file__).resolve().parents[1]
errors, passed = [], []
def check(condition, label):
    (passed if condition else errors).append(label)
def script_guid(relative):
    return re.search(r'^guid: (\w+)', (ROOT/relative).with_suffix('.cs.meta').read_text(), re.M)[1]
scene = (ROOT/'Assets/Game/Scenes/SC_BlackstoneIsland.unity').read_text()
parts = re.split(r'^--- !u!\d+ &(\d+)\n', scene, flags=re.M)
docs = {int(parts[i]): yaml.load(parts[i+1],Loader=yaml.CSafeLoader) for i in range(1,len(parts),2)}
def components(script):
    guid = script_guid('Assets/Game/Scripts/'+script)
    return [d['MonoBehaviour'] for d in docs.values() if 'MonoBehaviour' in d and d['MonoBehaviour']['m_Script']['guid']==guid]
actors = components('AI/PrisonActor.cs')
walkers = [a for a in actors if a.get('patrolEnabled') and len(a.get('patrol',[]))>=4]
seated = [a for a in actors if a.get('pose') in (8,9,10)]
check(len(actors)==22, 'Player and 21 NPC actor bindings')
check(len(walkers)==5, 'Four walking inmates and patrolling guard have routes')
check(len(seated)==6, 'Six seated table actors have authored poses')
check(any(a.get('pose')==11 for a in actors), 'Workout actor authored')
rigs=components('Actors/PrisonLocomotion.cs')
check(len(rigs)==22 and all(len(r['skeleton'])==23 for r in rigs), 'All 22 articulated locomotion rigs bind 23 bones')
check(all(docs[r['skeleton'][-1]['fileID']]['Transform']['m_GameObject']['fileID'] in docs for r in rigs), 'Every jaw transform resolves')
feet=components('Audio/PrisonFootsteps.cs')
check(len(feet)==22 and all(len(f['concrete'])==4 and len(f['metal'])==4 and f['locomotion']['fileID'] in docs for f in feet), 'All actors bind contact footsteps and both four-clip surfaces')
poker=components('Activities/PrisonPokerTable.cs')
talk=components('Activities/PrisonConversationTable.cs')
check(len(poker)==1 and len(poker[0]['players'])==3 and poker[0]['playerSeat']['fileID'] in docs, 'Playable poker table has three NPCs and player seat')
check(len(talk)==1 and talk[0]['playerSeat']['fileID'] in docs, 'Conversation table binds a player seat')
population=components('AI/PrisonPopulation.cs')
check(len(population)==1 and len(population[0]['contacts'])==5, 'Nearby population speech binds five contacts')

from prison_character import PROFILES
check(len(PROFILES)==10 and len({p[2] for p in PROFILES.values()})==5 and PROFILES['Heavy'][1]>PROFILES['Lean'][1], 'Ten body profiles, five skin tones and distinct heavy/lean bodies')
check(all((ROOT/'Assets/Game/Resources/Blackstone/Cards'/('card_%02d.png'%i)).is_file() for i in range(52)), 'All 52 playing-card textures packaged')

pngs=list((ROOT/'Assets').rglob('*.png'))+list((ROOT/'Documentation/BlackstonePreviews').glob('*.png'))
for path in pngs:
    try:
        with Image.open(path) as image: image.load()
    except Exception as exc: errors.append('PNG decode: '+str(path.relative_to(ROOT))+': '+str(exc))
check(not any(e.startswith('PNG decode:') for e in errors), 'Every asset PNG and final geometry preview decodes fully')

provenance=json.loads((ROOT/'Documentation/VoiceProduction_Provenance.json').read_text())
check(len(provenance['clips'])==68 and provenance['distinct_speakers']==5, 'Neural voice provenance covers 68 recordings and five speakers')
durations, peaks=[], []
for clip in provenance['clips']:
    path=ROOT/'Assets/Game/Resources/Blackstone/Dialogue'/(clip['id']+'.wav')
    try:
        check(hashlib.sha256(path.read_bytes()).hexdigest()==clip['sha256'], 'Voice hash: '+clip['id'])
        with wave.open(str(path)) as wav:
            frames=wav.getnframes();rate=wav.getframerate();raw=wav.readframes(frames)
            check(wav.getnchannels()==1 and wav.getsampwidth()==2 and rate==22050 and len(raw)==frames*2, 'Voice PCM: '+clip['id'])
        samples=np.frombuffer(raw,dtype='<i2').astype(float)/32768
        peaks.append(float(np.max(np.abs(samples))));durations.append(frames/rate)
        check(peaks[-1]<=.861 and durations[-1]>.5, 'Voice level/duration: '+clip['id'])
    except Exception as exc: errors.append('Voice decode: '+clip['id']+': '+str(exc))
foley=list((ROOT/'Assets/Game/Audio').glob('*.wav'))
check(len(foley)==25, '25 authored effect/ambience/score recordings')
for path in foley:
    try:
        with wave.open(str(path)) as wav:
            check(len(wav.readframes(wav.getnframes()))==wav.getnframes()*wav.getnchannels()*wav.getsampwidth(), 'Effect PCM: '+path.stem)
    except Exception as exc: errors.append('Effect decode: '+path.stem+': '+str(exc))
report=dict(status='PASS' if not errors else 'FAIL',checks=len(passed)+len(errors),errors=errors,passed_checks=passed,
    counts=dict(actors=len(actors),walking_routes=len(walkers),seated_actors=len(seated),rig_bones=23,body_profiles=len(PROFILES),decoded_pngs=len(pngs),neural_voice_clips=len(durations),effect_clips=len(foley)),
    total_voice_seconds=round(sum(durations),2),maximum_voice_peak=round(max(peaks),4),
    limitations='Static native asset/binding and file checks only; not Unity import, animation, lighting, collisions, playback or performance.')
(ROOT/'Validation/Revision02_AssetChecks.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='passed_checks'},indent=2))
raise SystemExit(bool(errors))
