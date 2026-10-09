"""Fetch licensed Rocketbox source assets and verify their Git blob hashes."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen
from urllib.parse import quote
from io import BytesIO
import hashlib, json, os, time
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT.parents[1] / 'rebuild-cache'
BASE = 'https://raw.githubusercontent.com/microsoft/Microsoft-Rocketbox/master/'
CHARACTERS = 'Assets/Game/Resources/BlackstoneFoundation/Characters'
ANIMATIONS = 'Assets/Game/Foundation/Animations/Rocketbox'
CLIPS = {
    'Idle': ('static', 'm_idle_neutral_01'),
    'WalkSlow': ('xy', 'm_walk_slow_01'),
    'Walk': ('xy', 'm_walk_neutral_01'),
    'WalkFast': ('xy', 'm_walk_fast_01'),
    'Run': ('xy', 'm_run_neutral_01'),
    'RunFast': ('xy', 'm_run_fast_01'),
    'Start': ('xy', 'm_walk_start'),
    'Stop': ('xy', 'm_walk_stop'),
    'Crouch': ('static', 'm_crouch_idle'),
    'TurnLeft': ('xyz', 'm_turn_left_90'),
    'TurnRight': ('xyz', 'm_turn_right_90'),
    'Seated': ('static', 'm_sit_chair_idle_neutral_01'),
}

def atomic_bytes(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.partial')
    with open(tmp, 'wb', buffering=0) as target:
        for start in range(0, len(data), 32768):
            part = memoryview(data)[start:start+32768]
            while part:
                n = target.write(part)
                if not n: raise IOError('Incomplete write: ' + str(path))
                part = part[n:]
    if tmp.stat().st_size != len(data): raise IOError('Wrong file size')
    os.replace(tmp, path)

def main():
    tree = json.loads((CACHE/'RocketboxTree.json').read_text())
    entries = {x['path']: x for x in tree['tree'] if x['type'] == 'blob'}
    work = []
    for number in ['16', '07', '12', '17', '20']:
        name = 'Male_Adult_' + number
        prefix = 'Assets/Avatars/Adults/' + name + '/'
        work.append((prefix+'Export/'+name+'_facial.fbx', CHARACTERS+'/'+name+'/'+name+'.fbx', 'copy'))
        work.append((prefix+name+'.png', CHARACTERS+'/'+name+'/Portrait.png', 'copy'))
        for src in entries:
            if src.startswith(prefix+'Textures/') and src.endswith('.tga'):
                work.append((src, CHARACTERS+'/'+name+'/'+Path(src).stem+'.png', 'texture'))
    for key, (mode, name) in CLIPS.items():
        src = 'Assets/Animations/all_animations_max_motextr_'+mode+'/'+name+'.max.fbx'
        work.append((src, ANIMATIONS+'/'+key+'.fbx', 'copy'))
    work.append(('LICENSE.md', 'Documentation/Licenses/Microsoft_Rocketbox_MIT.md', 'copy'))

    def fetch(item):
        src, dst, kind = item
        expected = entries[src]['sha']; cache = CACHE/'rocketbox'/src
        data = cache.read_bytes() if cache.exists() else None
        if data is None:
            for attempt in range(3):
                try:
                    request = Request(BASE+quote(src), headers={'User-Agent':'Blackstone-Foundation'})
                    with urlopen(request, timeout=60) as response: data=response.read()
                    break
                except Exception:
                    if attempt == 2: raise
                    time.sleep(1+attempt)
            atomic_bytes(cache, data)
        git_sha = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if git_sha != expected: raise ValueError('Source integrity mismatch: '+src)
        if kind == 'texture':
            im=Image.open(BytesIO(data)); im.load()
            out=BytesIO();im.save(out, format='PNG'); saved=out.getvalue()
        else: saved=data
        atomic_bytes(ROOT/dst, saved)
        if kind == 'texture':
            im=Image.open(ROOT/dst);im.verify()
        return {'source':src, 'source_url':BASE+quote(src), 'git_blob_sha1':expected,
                'path':dst, 'sha256':hashlib.sha256(saved).hexdigest(), 'size':len(saved)}

    provenance=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(fetch, item) for item in work]):
            provenance.append(future.result())
    provenance.sort(key=lambda x:x['path'])
    target=ROOT/'Documentation/Revision05_RocketboxProvenance.json'
    atomic_bytes(target, (json.dumps({'repository_commit':tree['sha'], 'license':'MIT', 'files':provenance},indent=2)+'\n').encode())
    print(json.dumps({'downloaded_assets':len(provenance),'bytes':sum(x['size'] for x in provenance)}))

if __name__ == '__main__': main()
