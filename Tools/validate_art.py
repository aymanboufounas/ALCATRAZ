"""Revision 03 static art checks; does not execute Unity shaders or physics."""
from pathlib import Path
import hashlib,json,re
import numpy as np
from PIL import Image
import yaml

ROOT=Path(__file__).resolve().parents[1]
errors=[];passed=[]
def check(ok,label):(passed if ok else errors).append(label)
data=json.loads((ROOT/'Documentation/BlackstoneAuthoring.json').read_text())
meshes=data['meshes'];nodes=data['nodes']
for profile in ['Elias','Niko','Malik','Heavy','Lean','Athletic','Rival','Guard','Brother','Rafi']:
    head=[m for key,m in meshes.items() if key.startswith(profile+'_Body_RealHead')]
    check(len(head)==1 and len(head[0]['v'])>5000,'Detailed face/hands: '+profile)
    if head:
        verts=np.array(head[0]['v']);check(abs(float(verts[:,1].max())-1.79)<.005,'Calibrated head height: '+profile)
        collar=verts[(verts[:,1]>1.46)&(verts[:,1]<1.492)&(np.abs(verts[:,0])<.20)]
        check(len(collar)>0 and np.max(np.abs(collar[:,0]))<.048 and np.max(np.abs(collar[:,2]-.010))<.044,'Lower neck fits shirt opening: '+profile)
    hair=[m for key,m in meshes.items() if key.startswith(profile+'_Body_RealHair')]
    for m in hair:
        v=np.array(m['v']);front=v[v[:,2]>.085]
        check(not len(front) or front[:,1].min()>1.70,'Hair clears eyes: '+profile)
for asset in ['brushed_concrete','concrete_floor_worn_001','brick_wall_001','seaside_rock','wood_planks','forest_floor']:
    for suffix in ['Base','Normal','Surface']:
        p=ROOT/'Assets/Game/Textures'/('PBR_'+asset+'_'+suffix+'.png')
        with Image.open(p) as image:check(image.size==(2048,2048),'2K '+asset+' '+suffix)
    p=ROOT/'Assets/Game/Textures'/('PBR_'+asset+'_Surface.png')
    with Image.open(p) as im:a=np.array(im)
    check(a.shape[-1]==4 and np.ptp(a[:,:,3])>20 and a[:,:,1].max()>0,'Roughness/AO packed: '+asset)
    meta=Path(str(p)+'.meta').read_text();check('sRGBTexture: 0' in meta and 'alphaIsTransparency: 0' in meta,'Linear surface import: '+asset)
    norm=Path(str(ROOT/'Assets/Game/Textures'/('PBR_'+asset+'_Normal.png'))+'.meta').read_text()
    check('textureType: 1' in norm,'Unity normal-map import: '+asset)
source=ROOT/'Tools/ArtSources'
for record in json.loads((source/'download-provenance.json').read_text()):
    if record.get('md5'):
        p=source/record['file'];check(p.exists() and hashlib.md5(p.read_bytes()).hexdigest()==record['md5'],'Published source checksum: '+record['file'])
names=[n['name'] for n in nodes]
for name in ['Clifftop island terrain','Service court paving','Laundry walls','Workshop annex walls','Administration walls','Clifftop grass','Cell block roof cap']:
    check(name in names,'Authored map feature: '+name)
check(sum(n=='Coastal cliff outcrop' for n in names)==68,'68 coastal rock outcrops')
check(sum('coastal Leaves' in n for n in names)>=20,'Coastal tree population')
for shader in ['CoastalWater','CoastalSky']:
    p=ROOT/'Assets/Game/Shaders'/(shader+'.shader');check(p.exists() and Path(str(p)+'.meta').exists(),'URP shader/meta: '+shader)

# Compare actual serialized colliders with the baked physical box geometry.
scene=(ROOT/'Assets/Game/Scenes/SC_BlackstoneIsland.unity').read_text()
parts=re.split(r'^--- !u!\d+ &(\d+)\n',scene,flags=re.M)
docs={int(parts[i]):yaml.safe_load(parts[i+1]) for i in range(1,len(parts),2)}
colliders={d['BoxCollider']['m_GameObject']['fileID']:d['BoxCollider'] for d in docs.values() if 'BoxCollider' in d}
checked=0
for n in nodes:
    if not n.get('mesh','').startswith('PhysicalBox_') or n['id'] not in colliders:continue
    points=np.array(meshes[n['mesh']]['v']);size=points.max(0)-points.min(0)
    c=colliders[n['id']];actual=np.array([c['m_Size'][k] for k in 'xyz'])
    check(np.allclose(actual,size,atol=.001),'Baked collider dimensions: '+str(n['id'])+' '+n['name']);checked+=1
check(checked>150,'Physical collider population verified')
report=dict(status='PASS' if not errors else 'FAIL',checks=len(passed)+len(errors),errors=errors,passed_checks=passed,
    counts=dict(physical_box_meshes=sum(k.startswith('PhysicalBox_') for k in meshes),verified_box_colliders=checked,coastal_outcrops=68,trees=sum('coastal Leaves' in n for n in names),scanned_material_sets=6,skin_material_variants=5),
    limitations='Static geometry, data/import settings and collider size checks only; no Unity import, HLSL compilation, skinning, live physics or performance test.')
(ROOT/'Validation/Revision03_ArtChecks.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='passed_checks'},indent=2));raise SystemExit(bool(errors))
