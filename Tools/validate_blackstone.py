"""Chapter-specific offline reference and coarse navigation checks; not Play Mode."""
import json,re,collections,math
from pathlib import Path
import numpy as np
import yaml

ROOT=Path(__file__).resolve().parents[1]
errors=[];checks=[]
def check(condition,label):
    checks.append(label)
    if not condition:errors.append(label)
def parse(path):
    text=path.read_text()
    parts=re.split(r'^--- !u!\d+ &(\d+)\n',text,flags=re.M)
    return {int(parts[i]):yaml.safe_load(parts[i+1]) for i in range(1,len(parts),2)}
def local_refs(value):
    if isinstance(value,dict):
        if 'fileID' in value and not value.get('guid') and value['fileID']:
            yield value['fileID']
        for v in value.values():yield from local_refs(v)
    elif isinstance(value,list):
        for v in value:yield from local_refs(v)

guid_to_path={}
for p in (ROOT/'Assets').rglob('*.meta'):
    m=re.search(r'^guid: (\w+)',p.read_text(),re.M)
    if m:guid_to_path[m[1]]=str(p.relative_to(ROOT))[:-5]
paths=[ROOT/'Assets/Game/Scenes/SC_BlackstoneIsland.unity',ROOT/'Assets/Game/Scenes/CharacterTest.unity',
       ROOT/'Assets/Game/Prefabs/Characters/PF_EliasVale_Player.prefab',ROOT/'Assets/Game/Prefabs/Characters/PF_EliasVale_Model.prefab']
for p in paths:
    docs=parse(p)
    missing=sorted({ref for doc in docs.values() for ref in local_refs(doc) if ref not in docs})
    check(not missing,p.name+' all local fileIDs resolve: '+str(missing))
    if p.suffix=='.unity':
        scripts=[];listeners=0;players=0
        for doc in docs.values():
            if 'MonoBehaviour' in doc:scripts.append(guid_to_path.get(doc['MonoBehaviour']['m_Script']['guid'],''))
            if 'AudioListener' in doc:listeners+=1
            if 'GameObject' in doc and doc['GameObject'].get('m_TagString')=='Player':players+=1
        check(players==1 and listeners==1,p.name+' exactly one Player tag and AudioListener')
        check(sum(x.endswith('/PlayerMovement.cs') for x in scripts)==1,p.name+' one movement controller')
        check(sum(x.endswith('/PlayerInputHandler.cs') for x in scripts)==1,p.name+' one input owner')
    if p.name=='SC_BlackstoneIsland.unity':
        director=next(d['MonoBehaviour'] for d in docs.values() if 'MonoBehaviour' in d and guid_to_path.get(d['MonoBehaviour']['m_Script']['guid'],'').endswith('/PrisonStoryDirector.cs'))
        check(len(director['targets'])==16,'All 16 story target roles bound')
        check(len(director['shots'])==11,'All 11 chapter camera shots bound')
        check(director['fightAtSeconds']==240,'Normal routine pacing is four minutes before incident')
        for r in director['targets']:
            data=docs[r['fileID']]['MonoBehaviour']
            check(data['director']['fileID'] in docs,'Interaction bound to shipping director')

book=json.loads((ROOT/'Assets/Game/Resources/Blackstone/story-dialogue.json').read_text())
ids=[l['id'] for g in book['scenes'] for l in g['lines']]
check(len(ids)==len(set(ids)),'Unique dialogue line ids')
check(all((ROOT/'Assets/Game/Resources/Blackstone/Dialogue'/(i+'.wav')).is_file() for i in ids),'Every subtitle has packaged speech')
check(all((ROOT/'Assets/Game/Resources/Blackstone/Dialogue'/(i+'.wav')).is_file() for i in ['incident_niko','incident_guard']),'Incident dialogue packaged')

# A conservative 2D occupancy pass on authored box colliders, with the B-04 door open.
boxes=json.loads((ROOT/'Documentation/BlackstoneColliders.json').read_text())
step=.20;xs=np.arange(-17,17.2,step);zs=np.arange(-29,40,step)
blocked=np.zeros((len(xs),len(zs)),bool)
for name,pos,size in boxes:
    lo=np.array(pos)-np.array(size)/2;hi=np.array(pos)+np.array(size)/2
    if hi[1]<.2 or lo[1]>1.7:continue
    blocked|=((xs[:,None]>=lo[0]-.26)&(xs[:,None]<=hi[0]+.26)&(zs[None,:]>=lo[2]-.26)&(zs[None,:]<=hi[2]+.26))
def coord(x,z):return int(round((x-xs[0])/step)),int(round((z-zs[0])/step))
start=coord(-7,-15);seen=set();q=collections.deque([start])
while q:
    a,b=q.popleft()
    if (a,b) in seen or a<0 or b<0 or a>=len(xs) or b>=len(zs) or blocked[a,b]:continue
    seen.add((a,b));q.extend([(a+1,b),(a-1,b),(a,b+1),(a,b-1)])
for name,x,z in [('Reader',-8,12),('Cook',12,9),('Fixer',13,32),('Niko',6,21),('Leader',-10,24.5),('Tattooist',-12,10)]:
    possible=any(math.hypot(xs[a]-x,zs[b]-z)<=2 for a,b in seen)
    check(possible,'Coarse path from B-04 to '+name)
report=dict(status='PASS' if not errors else 'FAIL',checks=len(checks),errors=errors,passed_checks=checks,
    dialogue_lines=len(ids)+2,reachable_grid_cells=len(seen),limitations='Static AABB navigation approximation; not Unity physics, import, shader compilation or Play Mode.')
(ROOT/'Validation/Chapter01_OfflineValidation.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='passed_checks'},indent=2))
raise SystemExit(1 if errors else 0)
