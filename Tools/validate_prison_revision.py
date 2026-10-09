"""Revision 04 role, geometry and static route checks, never Unity Play Mode."""
from pathlib import Path
import hashlib,json,re,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'Documentation/BlackstoneAuthoring.json').read_text())
nodes=data['nodes'];meshes=data['meshes'];errors=[];passed=[]
def check(ok,label):(passed if ok else errors).append(label)
names=[n['name'] for n in nodes if n.get('active',True)]
sys.path.insert(0,str(ROOT/'Tools'))
from prison_character import PROFILES
check(PROFILES['Elias'][3]=='PrisonOrange','Player profile is an orange-uniform inmate')
for mesh in ['Elias_Body_PrisonOrange','Elias_Body_PrisonOrangeTrousers','Elias_Body_EliasFrontID','Elias_Body_EliasBackID']:
    check(any(n.get('mesh')==mesh for n in nodes),'Player runtime mesh: '+mesh)
check('Officer Harrow' in names,'Guard remains a separate NPC')
ui=(ROOT/'Assets/Game/Scripts/UI/PrisonHUD.cs').read_text()
for text in ['GOAL: ESCAPE THE PRISON','INMATE ELIAS VALE','New game — Enter Cell B-04','UPPER GALLERY','MESS','WASH']:
    check(text in ui,'Role/navigation UI: '+text)
build=(ROOT/'ProjectSettings/EditorBuildSettings.asset').read_text()
check(re.search(r'enabled: 1\s+path: Assets/Game/Scenes/SC_Blackstone(?:Island|Story_Upgraded).unity',build) is not None,'Prison chapter or its upgraded copy is an enabled build scene')
check(sum(n.startswith('Cell B-') for n in names)==8,'Eight original B-row cells retained')
check(sum(n=='Opposite cell bars' for n in names)==8,'Eight ground C-row cells retained')
check(sum(bool(re.match(r'Upper cell [BC]-\d+',n)) for n in names)==16,'Sixteen upper cells: 32 cells in total')
for name in ['Inmate canteen','Inmate showers','Inmate workshop','Upper gallery landing','Prison main identity','North prison razor wire']:
    check(name in names,'Prison facility: '+name)
stairs=sorted([n for n in nodes if re.match(r'Gallery stair \d+$',n['name'])],key=lambda n:n['pos'][2])
check(len(stairs)==21,'21 collision steps to the upper gallery')
tops=[];treads=[]
for n in stairs:
    v=np.array(meshes[n['mesh']]['v']);bounds=v.max(0)-v.min(0)
    tops.append(n['pos'][1]+v[:,1].max());treads.append(bounds[2])
check(len(tops)==21 and np.allclose(np.diff(tops),.17,atol=.001),'Stair rises are .17 m, below .30 m step offset')
check(len(treads)==21 and min(treads)>.35,'Stair treads have .36 m depth')
landing=next(n for n in nodes if n['name']=='Upper gallery landing');v=np.array(meshes[landing['mesh']]['v'])
check(abs(landing['pos'][1]+v[:,1].max()-tops[-1])<.003,'Top step and gallery landing align')

# Conservative capsule/AABB samples on authored static boxes. Dynamic NPCs,
# swept collisions, sloped movement, camera collision and skinning are excluded.
colliders=json.loads((ROOT/'Documentation/BlackstoneColliders.json').read_text())
def route_clear(points):
    hits=[]
    for a,b in zip(points,points[1:]):
        a=np.array(a);b=np.array(b)
        for t in np.linspace(0,1,max(2,int(np.linalg.norm(b-a)/.14)+1)):
            p=a*(1-t)+b*t;lo=p+np.array([-.25,.005,-.25]);hi=p+np.array([.25,1.78,.25])
            for name,c,size in colliders:
                c=np.array(c);size=np.array(size);clo=c-size/2;chi=c+size/2
                if np.all(lo<chi-1e-5) and np.all(hi>clo+1e-5):hits.append(name)
    return sorted(set(hits))
routes={
    'Left upper gallery':[(0,3.665,1.9),(-3.08,3.665,1.9),(-3.08,3.665,-25)],
    'Right upper gallery':[(0,3.665,1.9),(3.08,3.665,1.9),(3.08,3.665,-25)],
    'Canteen doorway/centre':[(31,.092,26),(31,.092,29),(31,.092,34)],
    'Showers doorway/changing area':[(36,.092,12),(36,.092,14.3),(36,.092,17)],
    'Workshop access to contact':[(11.4,.11,28.5),(11.4,.11,32.2),(12,.11,32.2)],
}
for name,points in routes.items():
    hits=route_clear(points);check(not hits,name+' is clear of static boxes: '+', '.join(hits))
preserved=None
baseline_path=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'Validation/Revision04_PreservedFiles.json'
if baseline_path.is_file():
    baseline=json.loads(baseline_path.read_text());failed=[]
    for path,expected in baseline.items():
        p=ROOT/path
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:failed.append(path)
    check(not failed,'Approved movement, footsteps, voices, story code and player anatomy unchanged: '+', '.join(failed))
    preserved=len(baseline)
hidden=[n for n in nodes if n.get('mesh') and not n.get('rendered',True)]
check(len(hidden)>40,'Offline preview excludes invisible physics-only slabs')
report=dict(status='PASS' if not errors else 'FAIL',checks=len(passed)+len(errors),errors=errors,passed_checks=passed,
    counts=dict(cells=32,upper_cells=16,stairs=len(stairs),new_inmate_facilities=3,preserved_source_and_audio_files=preserved,static_routes=len(routes)),
    limitations='Native/source, dimensions and static AABB samples only. No Unity import, shaders, live movement, swept physics, camera collision, animation, final lighting or performance test.')
(ROOT/'Validation/Revision04_PrisonChecks.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='passed_checks'},indent=2))
raise SystemExit(bool(errors))
