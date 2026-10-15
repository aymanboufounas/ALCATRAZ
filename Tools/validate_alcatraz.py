"""Native scene bindings and sampled static route checks, not Unity Play Mode."""
from pathlib import Path
import hashlib, json, math, re, sys
import numpy as np
import yaml
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[1]
passed, errors = [], []
def check(ok, message):
    (passed if ok else errors).append(message)
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def scene(path):
    text = (ROOT / path).read_text()
    parts = re.split(r'^--- !u!\d+ &(-?\d+)\n', text, flags=re.M)
    return text, {int(parts[i]): yaml.load(parts[i+1], Loader=yaml.CSafeLoader)
                  for i in range(1, len(parts), 2)}
def guid(path):
    return re.search(r'^guid: (\w+)', (ROOT / (path+'.meta')).read_text(), re.M)[1]

layout = json.loads((ROOT/'Documentation/AlcatrazLayout.json').read_text())
scenes = layout['scene_paths']
text, docs = scene(scenes[1])
transforms = {i:d['Transform'] for i,d in docs.items() if 'Transform' in d}
objects = {i:d['GameObject'] for i,d in docs.items() if 'GameObject' in d}
transform_for = {d['m_GameObject']['fileID']:i for i,d in transforms.items()}
worlds = {}
def xyz(value): return np.array([value[k] for k in 'xyz'], float)
def world(tid):
    if tid not in worlds:
        t=transforms[tid];q=t['m_LocalRotation'];m=np.eye(4)
        m[:3,:3]=Rotation.from_quat([q[k] for k in 'xyzw']).as_matrix()@np.diag(xyz(t['m_LocalScale']))
        m[:3,3]=xyz(t['m_LocalPosition']);parent=t['m_Father']['fileID']
        worlds[tid]=world(parent)@m if parent else m
    return worlds[tid]
def active(go):
    t=transforms[transform_for[go]];parent=t['m_Father']['fileID']
    return bool(objects[go]['m_IsActive']) and (not parent or active(transforms[parent]['m_GameObject']['fileID']))
def components(path, source=docs):
    g=guid(path)
    return [d['MonoBehaviour'] for d in source.values() if 'MonoBehaviour' in d
            and d['MonoBehaviour']['m_Script']['guid']==g]

names=[o['m_Name'] for o in objects.values()]
check('Alcatraz Island Environment' in names, 'Native Alcatraz island root replaces the older map')
check('_BlackstoneEnvironment' not in names, 'Older architecture is absent from the Alcatraz scene')
landmarks={l['name'] for l in layout['landmarks']}
for name in ['Cellhouse','Recreation Yard','Water Tower','Lighthouse','Wardens House',
             'New Industries','Model Industries','Power House','Storehouse',
             'Building 64 - Barracks','Guardhouse - Sally Port','Parade Ground','Dock','Dining Hall','Shower Room']:
    check(name in landmarks, 'Authored landmark: '+name)
cells=layout['cells'];bc=[c for c in cells if c['block'] in ['B','C']]
check(len(bc)==336 and {c['tier'] for c in bc}=={1,2,3}, 'B/C blocks have 336 furnished cells across three tiers')
check(sum(c['main'] for c in cells)==1, 'Exactly one playable B-04 cell')
actors=components('Assets/Game/Scripts/AI/PrisonActor.cs')
roster=json.loads((ROOT/'Assets/Game/Alcatraz/Resources/Alcatraz/CharacterRoster.json').read_text())['actors']
check(len(actors)==30 and len(roster)==30, '22 preserved actors plus eight additional ambient actors')
check({a['displayName'] for a in actors}=={a['actorName'] for a in roster},'Every native actor resolves to exactly one roster identity')
check(len({a['actorName'] for a in roster})==30,'Character identities are unique')
check(sum(bool(a.get('patrolEnabled')) for a in actors)==10, 'Ten walking NPC patrol routes')
check(sum(a.get('pose') in (8,9,10) for a in actors)==6, 'Six seated activity-table NPCs')
director=components('Assets/Game/Scripts/Missions/PrisonStoryDirector.cs')[0]
check(director['m_Enabled']==1 and director['fightAtSeconds']==240, 'Chapter enabled with the four-minute fight trigger')
for field, key in [('cellSpawn','cellSpawn'),('yardSpawn','yardSpawn'),('solitarySpawn','solitarySpawn'),
                   ('visitSpawn','visitSpawn'),('sleepPosition','sleepPosition'),
                   ('guardIncidentPoint','guardIncident'),('guardIsolationPoint','guardIsolation'),('rivalIsolationPoint','rivalIsolation')]:
    check(np.allclose(world(director[field]['fileID'])[:3,3],layout['chapter_points'][key]), 'Alcatraz chapter anchor: '+field)
hero=next(a for a in actors if a['displayName']=='Elias Vale')
officer=next(a for a in actors if a['displayName'].startswith('Officer'))
check(hero['m_GameObject']!=officer['m_GameObject'] and hero['m_GameObject']==docs[director['player']['fileID']]['MonoBehaviour']['m_GameObject'],
      'Player is Elias the inmate; the officer is a separate NPC')
check(components('Assets/Game/Foundation/Scripts/FoundationBootstrap.cs')[0]['storyMode']==1, 'Story mode keeps the imported character foundation')
free_text, free_docs=scene(scenes[0])
check(components('Assets/Game/Foundation/Scripts/FoundationBootstrap.cs',free_docs)[0]['storyMode']==0, 'Exploration mode uses its free movement and equipment foundation')
check(components('Assets/Game/Scripts/Missions/PrisonStoryDirector.cs',free_docs)[0]['m_Enabled']==0, 'Exploration keeps timed chapter logic disabled')
check(components('Assets/Game/Foundation/Scripts/FoundationHUD.cs',free_docs)[0]['storyScene']=='SC_AlcatrazChapter01', 'Exploration chapter button opens the Alcatraz chapter')
check(components('Assets/Game/Foundation/Scripts/FoundationHUD.cs',free_docs)[0]['worldTitle']=='ALCATRAZ\nISLAND', 'Alcatraz menu title has the intended two lines')
check(len(components('Assets/Game/Foundation/Scripts/FoundationTarget.cs',free_docs))==3, 'Three practice targets in exploration')
check(bool(components('Assets/Game/Scripts/Activities/PrisonPokerTable.cs')) and bool(components('Assets/Game/Scripts/Activities/PrisonConversationTable.cs')), 'Poker and conversation activities retain their native bindings')
for path in scenes:
    check(re.search(r'enabled: 1\s+path: '+re.escape(path),(ROOT/'ProjectSettings/EditorBuildSettings.asset').read_text()) is not None, 'Enabled build scene: '+path)
    source=(ROOT/path).read_text();ids=set(re.findall(r'^--- !u!\d+ &(-?\d+)',source,re.M))
    missing=set(re.findall(r'\{fileID: (-?\d+)\}',source))-ids-{'0'}
    check(not missing, 'All local scene references resolve: '+path)

# Native BoxCollider data, including the retained tables and chairs. These tests
# model a 0.25 m radius / 1.78 m height controller against stationary obstacles.
# Operable mission doors are excluded only for the routes where they are open.
boxes=[]
dynamic_doors=set()
actor_objects={a['m_GameObject']['fileID'] for a in actors}
for field in ['cellDoor','solitaryDoor']:
    cid=director[field]['fileID'];component=docs[cid]
    dynamic_doors.add(cid if 'GameObject' in component else next(iter(component.values()))['m_GameObject']['fileID'])
def door_child(go):
    if go in dynamic_doors:return True
    p=transforms[transform_for[go]]['m_Father']['fileID']
    return bool(p) and door_child(transforms[p]['m_GameObject']['fileID'])
def actor_child(go):
    if go in actor_objects:return True
    p=transforms[transform_for[go]]['m_Father']['fileID']
    return bool(p) and actor_child(transforms[p]['m_GameObject']['fileID'])
for d in docs.values():
    if 'BoxCollider' not in d:continue
    c=d['BoxCollider'];go=c['m_GameObject']['fileID']
    if not c.get('m_Enabled',1) or c.get('m_IsTrigger') or not active(go) or door_child(go) or actor_child(go):continue
    m=world(transform_for[go]);scale=np.linalg.norm(m[:3,:3],axis=0);axes=m[:3,:3]/scale
    center=(m@np.r_[xyz(c['m_Center']),1])[:3];half=xyz(c['m_Size'])*scale/2
    boxes.append((objects[go]['m_Name'],center,half,axes,go))
def samples(points):
    result=[]
    for a,b in zip(points,points[1:]):
        a=np.array(a,float);b=np.array(b,float)
        result.extend(a+(b-a)*t for t in np.linspace(0,1,max(2,math.ceil(np.linalg.norm(b-a)/.12))))
    return np.array(result)
def route_hits(points):
    pts=samples(points);hits=[]
    for name,c,half,axes,_ in boxes:
        if re.match(r'(First gallery stair|Second gallery stair|Yard to cellhouse steps) \d+$',name):continue
        top=c[1]+(np.abs(axes[1])*half).sum();bottom=c[1]-(np.abs(axes[1])*half).sum()
        relevant=(top>pts[:,1]+.301)&(bottom<pts[:,1]+1.78)
        if not relevant.any():continue
        q=(pts[relevant]-c)@axes
        if abs(axes[1,1])>.99:
            horizontal=np.maximum(np.abs(q[:,[0,2]])-half[[0,2]],0)
            hit=np.linalg.norm(horizontal,axis=1)<.249
        else:
            extent=np.abs(axes)@half
            horizontal=np.maximum(np.abs(pts[relevant][:,[0,2]]-c[[0,2]])-extent[[0,2]],0)
            hit=np.linalg.norm(horizontal,axis=1)<.249
        if hit.any():hits.append(name)
    return sorted(set(hits))

z=layout['chapter_points']['cellSpawn'][2]
routes={
    'B04 exit to Broadway':[(-4.25,30.11,z),(-1.5,30.01,z),(0,30.01,z)],
    'Broadway to yard portal':[(0,30.01,z),(0,30.01,27.6),(-25.7,30.01,33)],
    'Yard stairs':[(-25.7,30.01,33),(-26.5,30.01,33),(-29.6,27.29,33),(-31,27.29,33)],
    'Yard spawn to fallen knife':[(-31,27.29,33),(-43,27.29,40),(-41.75,27.29,42)],
    'D block isolation exit':[(-17.2,30.08,z),(-13.3,30.01,z),(-11,30.01,z)],
    'Visitation prisoner approach':[(0,30.01,-35),(13,30.01,-38),(18.5,30.01,-38)],
    'First gallery flight':[(0,30.01,29.1),(0,32.76,34.5)],
    'Second gallery flight':[(0,32.76,35.8),(0,35.51,41.2)],
    'Dining hall centre entrance':[(0,30.02,41.5),(0,30.02,47.8),(-2.5,30.02,47.8),(-2.5,30.02,54.6)],
    'Shower entrance':[(0,30.04,-43),(0,30.04,-60),(12,30.04,-60),(12,30.04,-54)],
}
for tier, y, end in [(2,32.76,35.3),(3,35.51,42.4)]:
    for side in [-1,1]:
        routes[f'Tier {tier} main gallery {side}']=[(0,y,end),(side*1.96,y,end),(side*1.96,y,-30)]
        routes[f'Tier {tier} outer gallery {side}']=[(side*1.96,y,end),(side*10.04,y,end),(side*10.04,y,-30)]
        routes[f'Tier {tier} A/D gallery {side}']=[(side*1.96,y,end),(side*13.96,y,end),(side*13.96,y,-30)]
        routes[f'Tier {tier} exterior A/D gallery {side}']=[(side*13.96,y,end),(side*22.04,y,end),(side*22.04,y,-30)]
for actor in actors:
    if actor.get('patrolEnabled') and len(actor.get('patrol',[]))>1:
        route=[xyz(p).tolist() for p in actor['patrol']]
        position=world(transform_for[actor['m_GameObject']['fileID']])[:3,3].tolist()
        routes['NPC patrol '+actor['displayName']]=[position]+route+[route[0]]
for profile in roster:
    p=ROOT/('Assets/Game/Resources/BlackstoneFoundation/Characters/'+profile['model']+'/'+profile['model']+'.fbx')
    check(p.is_file(),'Packaged character model for '+profile['actorName'])
    if profile.get('ambient') and not profile.get('route'):
        position=[profile['position'][axis] for axis in 'xyz']
        routes['Ambient station '+profile['actorName']]=[position,position]
for road in layout['roads']:
    points=np.array(road['points']);slopes=np.abs(np.diff(points[:,1]))/np.maximum(.001,np.linalg.norm(np.diff(points[:,[0,2]],axis=0),axis=1))
    check(float(np.degrees(np.arctan(slopes)).max())<46 and road['width']>=1.75, 'Controller-compatible road/stair dimensions: '+road['name'])
    if not road.get('steps') and road['name'] not in ['Dining Hall threshold','Shower entry threshold']:
        routes['Road '+road['name']]=(points+np.array([0,.01,0])).tolist()
route_results={name:route_hits(points) for name,points in routes.items()}
for name,hits in route_results.items():check(not hits,'Static route clearance: '+name+(' / '+', '.join(hits) if hits else ''))

# Check support using the native MeshCollider vertex/index buffers, independent
# of the authoring inventory. This catches disconnected galleries and road gaps.
from scipy.spatial import cKDTree
mesh_assets={guid(str(p.relative_to(ROOT))):p for p in (ROOT/'Assets').rglob('*.asset')}
floor_meshes=[]
for d in docs.values():
    if 'MeshCollider' not in d:continue
    c=d['MeshCollider'];go=c['m_GameObject']['fileID']
    if not c.get('m_Enabled',1) or c.get('m_IsTrigger') or not active(go):continue
    p=mesh_assets.get(c['m_Mesh']['guid'])
    if p is None:continue
    source=p.read_text();count=int(re.search(r'm_VertexCount: (\d+)',source)[1]);size=int(re.search(r'm_DataSize: (\d+)',source)[1])
    raw=bytes.fromhex(re.search(r'_typelessdata: ([0-9a-f]+)',source)[1]);vertices=np.ndarray((count,3),dtype='<f4',buffer=raw,strides=(size//count,4))
    fmt=int(re.search(r'm_IndexFormat: (\d+)',source)[1]);indices=np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: ([0-9a-f]+)',source)[1]),dtype='<u2' if fmt==0 else '<u4').reshape(-1,3)
    m=world(transform_for[go]);verts=vertices@m[:3,:3].T+m[:3,3];tri=verts[indices]
    normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);tri=tri[np.abs(normals[:,1])>.01]
    if not len(tri):continue
    centroid=tri[:,:,[0,2]].mean(axis=1);radius=np.linalg.norm(tri[:,:,[0,2]]-centroid[:,None,:],axis=2).max()+.01
    floor_meshes.append((objects[go]['m_Name'],tri,cKDTree(centroid),radius))
def support_check(points):
    pts=samples(points);supported=np.zeros(len(pts),bool);embedded=np.zeros(len(pts),bool)
    for _,c,half,axes,_ in boxes:
        if abs(axes[1,1])<.99:continue
        q=(pts-c)@axes;top=c[1]+half[1]
        inside=(np.abs(q[:,0])<=half[0]+.006)&(np.abs(q[:,2])<=half[2]+.006)
        supported|=inside&(top>=pts[:,1]-.35)&(top<=pts[:,1]+.301)
    for name,tri,tree,radius in floor_meshes:
        lo=tri.min(axis=(0,1));hi=tri.max(axis=(0,1));mask=(pts[:,0]>=lo[0])&(pts[:,0]<=hi[0])&(pts[:,2]>=lo[2])&(pts[:,2]<=hi[2])
        ids=np.flatnonzero(mask)
        if not len(ids):continue
        candidates=tree.query_ball_point(pts[ids][:,[0,2]],radius)
        rows=np.repeat(ids,[len(c) for c in candidates]);cols=np.array([i for c in candidates for i in c],int)
        if not len(rows):continue
        t=tri[cols];a=t[:,0][:,[0,2]];u=t[:,1][:,[0,2]]-a;v=t[:,2][:,[0,2]]-a;q=pts[rows][:,[0,2]]-a
        determinant=u[:,0]*v[:,1]-u[:,1]*v[:,0];valid=np.abs(determinant)>1e-7
        beta=np.divide(q[:,0]*v[:,1]-q[:,1]*v[:,0],determinant,out=np.zeros(len(rows)),where=valid)
        gamma=np.divide(u[:,0]*q[:,1]-u[:,1]*q[:,0],determinant,out=np.zeros(len(rows)),where=valid)
        inside=valid&(beta>=-.0001)&(gamma>=-.0001)&(beta+gamma<=1.0001)
        y=t[:,0,1]+beta*(t[:,1,1]-t[:,0,1])+gamma*(t[:,2,1]-t[:,0,1]);feet=pts[rows,1]
        supported[rows[inside&(y>=feet-.35)&(y<=feet+.301)]]=True
        if name in ['Alc_Terrain','Alc_Cliffs']:
            embedded[rows[inside&(y>feet+.31)&(y<feet+1.78)]]=True
    return int((~supported).sum()),int(embedded.sum()),len(pts)
floor_results={name:support_check(points) for name,points in routes.items()}
for name,(gaps,buried,total) in floor_results.items():
    check(gaps==0 and buried==0,f'Native floor support: {name} / {total} samples, {gaps} unsupported, {buried} inside terrain')

# Patrol routes alone miss stationary story characters. Check every actor's
# actual scene transform, including seated actors' underlying floor. Chairs
# intentionally intersect seated poses, so only standing poses need clearance.
station_results={}
for actor in actors:
    name=actor['displayName'];position=world(transform_for[actor['m_GameObject']['fileID']])[:3,3].tolist()
    gaps,buried,total=support_check([position,position])
    fixed_pose=actor.get('pose',0) in (4,8,9,10)
    blocked=[] if fixed_pose else route_hits([position,position])
    check(gaps==0 and buried==0,f'All actor station floors: {name} / {gaps} unsupported, {buried} inside terrain')
    if not fixed_pose:check(not blocked,'Standing actor capsule clearance: '+name+(' / '+', '.join(blocked) if blocked else ''))
    station_results[name]={'position':position,'fixed_pose':fixed_pose,'unsupported':gaps,'buried':buried,'obstructions':blocked}

baseline=json.loads((ROOT/'Validation/Revision04_PreservedFiles.json').read_text())
adapted={'Assets/Game/Scripts/Missions/PrisonStoryDirector.cs','Assets/Game/Scripts/Save/PrisonSave.cs',
         'Assets/Game/Scripts/AI/PrisonActor.cs',
         'Assets/Game/Scripts/UI/PrisonHUD.cs','Assets/Game/Scripts/Audio/PrisonAudio.cs',
         'Assets/_DesertShift/Scripts/Player/PlayerMovement.cs',
         'Assets/_DesertShift/Scripts/Camera/ThirdPersonCameraController.cs'}
changed={p for p,h in baseline.items() if not (ROOT/p).is_file() or digest(ROOT/p)!=h}
check(changed==(adapted&set(baseline)), 'Protected baseline changes are limited to the requested map, movement, camera, menu and player health integrations')
check(digest(ROOT/'Assets/Game/Scenes/SC_BlackstoneIsland.unity')==layout['original_scene_sha256'],'Classic source scene remains unchanged')
audio=json.loads((ROOT/'Documentation/Revision05_AudioProvenance.json').read_text())
check(all(digest(ROOT/r['path'])==r['sha256'] for r in audio['files']), 'All 44 foundation sound recordings unchanged')
for path in (ROOT/'Assets/Game/Alcatraz').rglob('*.cs'):
    check('MonoImporter:' in Path(str(path)+'.meta').read_text(),'MonoImporter metadata: '+path.name)
save=(ROOT/'Assets/Game/Scripts/Save/PrisonSave.cs').read_text()
check('AlcatrazMap.CheckpointFile' in save and 'p.y > 68' in save and 'p.x > 135' in save,'Separate Alcatraz checkpoint identity and expanded elevation bounds')
check((ROOT/'Assets/Game/Alcatraz/Resources/Alcatraz/IslandMap.png').is_file(),'Runtime island map image is packaged')
report={'status':'PASS' if not errors else 'FAIL','checks':len(passed)+len(errors),'errors':errors,
        'passed_checks':passed,'actor_stations':station_results,'counts':{'landmarks':len(landmarks),'cells':len(cells),'B_C_cells':len(bc),'actors':len(actors),
        'static_routes':len(routes),'static_boxes_checked':len(boxes),'unchanged_protected_files':len(baseline)-len(changed)},
        'scope':'Native YAML bindings, file hashes, route dimensions, discrete stationary obstacle samples and native mesh/box floor support only. Operable mission doors are assumed open on exit routes; stair treads and dynamic actor colliders are excluded from obstacle samples. Swept physics, NPC avoidance, Unity import, Play Mode and a player build are unverified.'}
(ROOT/'Validation/Revision08_AlcatrazChecks.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='passed_checks'},indent=2))
sys.exit(bool(errors))
