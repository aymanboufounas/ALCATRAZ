"""Check the native interior's bindings, geometry and supported player routes.
Discrete static box sampling is not a CharacterController/Unity simulation.
"""
from pathlib import Path
import json,math,re,sys
import numpy as np
import yaml
from scipy.spatial.transform import Rotation

ROOT=Path(__file__).resolve().parents[1]
PATH='Assets/Game/Supplied/Resources/AlcatrazSupplied/Cellhouse/Interior.prefab'

def main():
    text=(ROOT/PATH).read_text();parts=re.split(r'^--- !u!\d+ &(-?\d+)\n',text,flags=re.M)
    docs={int(parts[i]):yaml.load(parts[i+1],Loader=yaml.CSafeLoader) for i in range(1,len(parts),2)}
    objects={i:d['GameObject'] for i,d in docs.items() if 'GameObject' in d}
    ts={i:d['Transform'] for i,d in docs.items() if 'Transform' in d}
    tids={t['m_GameObject']['fileID']:i for i,t in ts.items()};worlds={};checks=[]
    def check(ok,name):checks.append({'pass':bool(ok),'check':name})
    def xyz(v):return np.array([v[k] for k in 'xyz'],float)
    def world(i):
        if i not in worlds:
            t=ts[i];m=np.eye(4);m[:3,:3]=Rotation.from_quat([t['m_LocalRotation'][k] for k in 'xyzw']).as_matrix()@np.diag(xyz(t['m_LocalScale']));m[:3,3]=xyz(t['m_LocalPosition']);parent=t['m_Father']['fileID'];worlds[i]=world(parent)@m if parent else m
        return worlds[i]
    check(all(i=='0' or int(i) in docs for i in re.findall(r'\{fileID: (-?\d+)\}',text)),'Every local prefab binding resolves')
    names={g['m_Name'] for g in objects.values()}
    check(not any(n in names for n in ['Alc_Terrain','Alc_Cliffs','Alcatraz Island Environment','Player','_BlackstoneChapter01']),'Legacy island/player/story director are absent')
    check(any('Cell bars /' in n for n in names) and any('Cell blankets /' in n for n in names),'Furnished barred cells retained')
    check('Dining Hall' in names and 'First gallery stair 01' in names and 'Second gallery stair 01' in names,'Dining hall and both gallery stair flights retained')
    check(sum('Light' in d for d in docs.values())>=16,'Cellhouse and dining lights retained')
    boxes=[]
    for d in docs.values():
        if 'BoxCollider' not in d:continue
        c=d['BoxCollider'];go=c['m_GameObject']['fileID']
        if not c.get('m_Enabled',1) or c.get('m_IsTrigger'):continue
        m=world(tids[go]);scale=np.linalg.norm(m[:3,:3],axis=0);axes=m[:3,:3]/scale;center=(m@np.r_[xyz(c['m_Center']),1])[:3]
        boxes.append((objects[go]['m_Name'],center,xyz(c['m_Size'])*scale/2,axes))
    routes={
        'Entry to Broadway':[(0,30.12,-39),(0,30.02,25)],
        'B04 cell entrance':[(0,30.02,-24.91),(-4.25,30.11,-24.91)],
        'Dining hall':[(0,30.02,25),(0,30.02,47.8),(-2.5,30.02,47.8),(-2.5,30.02,54.6)],
        'First stair':[(0,30.01,29.1),(0,32.76,34.5)],
        'Second stair':[(0,32.76,35.8),(0,35.51,41.2)],
        'Guard patrol':[(-.8,30.03,-25),(-.8,30.03,25)],
        'Samir patrol':[(1,30.03,-12),(1,30.03,20)],
        'Malik patrol':[(-12,30.03,8),(-12,30.03,25)],
        'Tomas station':[(12,30.03,12),(12,30.03,12)],
        'Dining orderly station':[(-3,30.03,49),(-3,30.03,49)],
        'Luis station':[(5,30.03,63),(5,30.03,63)]}
    for tier,y,z in [(2,32.76,35.3),(3,35.51,42.4)]:
        for x in [-22.04,-13.96,-10.04,-1.96,1.96,10.04,13.96,22.04]:
            routes[f'Tier {tier} gallery {x}']=[(0,y,z),(x,y,z),(x,y,-30)]
    assets={}
    for p in (ROOT/'Assets').rglob('*.asset'):
        g=re.search(r'^guid: (\w+)',Path(str(p)+'.meta').read_text(),re.M)
        if g:assets[g[1]]=p
    floor_meshes=[]
    for d in docs.values():
        if 'MeshCollider' not in d:continue
        c=d['MeshCollider']
        if not c.get('m_Enabled',1) or c.get('m_IsTrigger'):continue
        p=assets[c['m_Mesh']['guid']];s=p.read_text();count=int(re.search(r'm_VertexCount: (\d+)',s)[1]);stride=int(re.search(r'm_DataSize: (\d+)',s)[1])//count;raw=bytes.fromhex(re.search(r'_typelessdata: (\w+)',s)[1])
        v=np.ndarray((count,3),'<f4',buffer=raw,strides=(stride,4));t=np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: (\w+)',s)[1]),dtype='<u4' if 'm_IndexFormat: 1' in s else '<u2').reshape(-1,3)
        m=world(tids[c['m_GameObject']['fileID']]);tri=(v@m[:3,:3].T+m[:3,3])[t];n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);tri=tri[np.abs(n[:,1])>.01]
        if len(tri):floor_meshes.append(tri)
    def mesh_support(samples):
        supported=np.zeros(len(samples),bool)
        for tri in floor_meshes:
            lo,hi=tri.min(axis=(0,1)),tri.max(axis=(0,1));ids=np.flatnonzero((samples[:,0]>=lo[0])&(samples[:,0]<=hi[0])&(samples[:,2]>=lo[2])&(samples[:,2]<=hi[2]))
            a=tri[:,0][:,[0,2]];b=tri[:,1][:,[0,2]]-a;c=tri[:,2][:,[0,2]]-a;den=b[:,0]*c[:,1]-b[:,1]*c[:,0]
            for i in ids:
                q=samples[i,[0,2]]-a;u=np.divide(q[:,0]*c[:,1]-q[:,1]*c[:,0],den,out=np.zeros(len(den)),where=abs(den)>1e-8);v=np.divide(b[:,0]*q[:,1]-b[:,1]*q[:,0],den,out=np.zeros(len(den)),where=abs(den)>1e-8)
                inside=(abs(den)>1e-8)&(u>=-.0001)&(v>=-.0001)&(u+v<=1.0001);y=tri[:,0,1]+u*(tri[:,1,1]-tri[:,0,1])+v*(tri[:,2,1]-tri[:,0,1])
                supported[i]|=np.any(inside&(y>=samples[i,1]-.35)&(y<=samples[i,1]+.301))
        return supported
    results={}
    for name,points in routes.items():
        samples=np.concatenate([np.linspace(a,b,max(2,math.ceil(np.linalg.norm(np.array(b)-a)/.12))) for a,b in zip(points,points[1:])]);supported=np.zeros(len(samples),bool);blocked=set()
        for label,c,half,axes in boxes:
            q=(samples-c)@axes;top=c[1]+half[1];bottom=c[1]-half[1]
            if abs(axes[1,1])>.99:
                inside=(abs(q[:,0])<half[0]+.006)&(abs(q[:,2])<half[2]+.006)
                supported|=inside&(top>=samples[:,1]-.35)&(top<=samples[:,1]+.301)
                if re.match(r'(First|Second) gallery stair \d+$',label):continue
                horizontal=np.maximum(np.abs(q[:,[0,2]])-half[[0,2]],0)
                obstruct=(np.linalg.norm(horizontal,axis=1)<.249)&(top>samples[:,1]+.301)&(bottom<samples[:,1]+1.78)
                if obstruct.any():blocked.add(label)
        supported|=mesh_support(samples)
        gaps=int((~supported).sum());check(gaps==0,'Supported route: '+name);check(not blocked,'Clear route: '+name)
        results[name]={'samples':len(samples),'unsupported':gaps,'obstructions':sorted(blocked)}
    result={'status':'PASS' if all(c['pass'] for c in checks) else 'FAIL','checks':len(checks),'errors':[c['check'] for c in checks if not c['pass']],'routes':results,'scope':'Native prefab bindings, retained geometry, native mesh/box floor support and discrete static box clearance; Unity import and swept physics unverified'}
    (ROOT/'Validation/Revision11_PrisonChecks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return result['status']!='PASS'

if __name__=='__main__':sys.exit(main())
