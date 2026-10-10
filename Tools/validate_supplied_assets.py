"""Validate packaged source dependencies and supplied island floor samples.
This does not run Unity or emulate CharacterController physics.
"""
from pathlib import Path
import json,hashlib,re,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'Assets/Game/Supplied';RES=BASE/'Resources/AlcatrazSupplied'
checks=[]
def check(ok,label):checks.append({'pass':bool(ok),'check':label})
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 catalog=json.loads((RES/'Catalog.json').read_text());check(len(catalog['assets'])==9,'All nine supplied archives catalogued')
 for name in ('Island','Dog','Helmet','Vest','Helicopter'):
  folder=RES/name;d=json.loads((folder/(name+'.gltf')).read_text());buffers=[]
  for i,b in enumerate(d['buffers']):
   data=(folder/b['uri']).read_bytes();check(len(data)==b['byteLength'],name+' buffer length '+str(i));buffers.append(data)
  for v in d.get('bufferViews',[]):
   check(0<=v.get('byteOffset',0) and v.get('byteOffset',0)+v['byteLength']<=len(buffers[v['buffer']]),name+' buffer view bounds')
  for image in d.get('images',[]):check((folder/image['uri']).is_file(),name+' image dependency')
  for animation in d.get('animations',[]):
   check(all(0<=c['target']['node']<len(d['nodes']) and 0<=c['sampler']<len(animation['samplers']) for c in animation['channels']),name+' animation targets '+animation.get('name',''))
   check(all(0<=s['input']<len(d['accessors']) and 0<=s['output']<len(d['accessors']) for s in animation['samplers']),name+' animation accessors')
  meta=(folder/(name+'.gltf.meta')).read_text();check(meta.count('externalObjects:')==1,name+' importer metadata has unique keys')
  if name=='Dog':
   check(len(d['animations'])==17 and 'animationMethod: 1' in meta,'Dog retains all 17 clips as Legacy animations')
   check(len(d['skins'])==1 and len(d['skins'][0]['joints'])==200,'Dog skin contains only the 200 weighted joints')
   check(len(d['nodes'])==344,'Dog retains the mesh nodes and every weighted joint ancestor')
   from prepare_dog_import import accessor_array
   for mesh in d['meshes']:
    for primitive in mesh['primitives']:
     attrs=primitive['attributes'];joints=accessor_array(d,buffers,attrs['JOINTS_0']);weights=accessor_array(d,buffers,attrs['WEIGHTS_0'])
     check(int(joints.max())<len(d['skins'][0]['joints']),'Dog remapped joint indices are in bounds')
     check(np.isfinite(weights).all() and np.allclose(weights.sum(axis=1),1,atol=1e-5),'Dog skin weights are finite and normalized')
   check(catalog['assets']['police-dog']['import_compatibility']['packaged_model_sha256']==sha(folder/'Dog.gltf'),'Dog optimized model matches the import catalog')
 for original,name in [('gun-10mm','Pistol10mm'),('high-poly-pbr-revolvergun','Revolver')]:
  p=RES/name/(name+'.fbx');check(p.read_bytes().startswith(b'Kaydara FBX Binary'),'Native FBX '+name)
 parts=json.loads((BASE/'HouseSource/HouseParts.json').read_text());data=b''.join((ROOT/p).read_bytes() for p in parts['parts'])
 check(len(data)==parts['bytes'] and hashlib.sha256(data).hexdigest()==parts['sha256'],'House FBX reconstructs byte-exactly')
 material_files=list((BASE/'Materials').glob('*.mat'));check(len(material_files)>=28,'Weapon, police and house PBR materials packaged')
 for p in material_files:
  text=p.read_text();check(text.count('- _MetallicGlossMap:')==1,'Single metallic/smoothness mapping '+p.name)
 for p in BASE.rglob('*'):
  if p.is_file() and p.suffix!='.meta':check(Path(str(p)+'.meta').is_file(),'Unity metadata '+str(p.relative_to(BASE)))
 # glTFast reflects X and reverses triangle winding; translate by the scene root.
 d=json.loads((RES/'Island/Island.gltf').read_text());buffers=[(RES/'Island'/b['uri']).read_bytes() for b in d['buffers']]
 def accessor(index):
  a=d['accessors'][index];v=d['bufferViews'][a['bufferView']];n={'VEC3':3,'VEC2':2,'SCALAR':1}[a['type']];dtype={5126:'<f4',5125:'<u4'}[a['componentType']]
  return np.frombuffer(buffers[v['buffer']],dtype=dtype,count=a['count']*n,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,n)
 p=accessor(0).copy();p[:,0]=-p[:,0]-63;p[:,1]+=45;p[:,2]+=12;t=accessor(3).reshape(-1,3)
 check(t.max()<len(p),'Island triangle indices are in bounds')
 tri=p[t];centers=tri.mean(axis=1);coast=json.loads((RES/'Island/Coastline.json').read_text())['points'];keep=np.zeros(len(tri),bool)
 for i,a in enumerate(coast):
  b=coast[i-1];cross=(a['z']>centers[:,2])!=(b['z']>centers[:,2]);x=(b['x']-a['x'])*(centers[:,2]-a['z'])/(b['z']-a['z']+1e-20)+a['x'];keep^=cross&(centers[:,0]<x)
 check(3000<keep.sum()*3<len(t)*3,'Coastline keeps the island and removes surrounding water')
 tri=tri[keep];a,b,c=tri[:,0][:,[0,2]],tri[:,1][:,[0,2]],tri[:,2][:,[0,2]];v0=b-a;v1=c-a;den=v0[:,0]*v1[:,1]-v1[:,0]*v0[:,1]
 normal=np.cross(tri[:,2]-tri[:,0],tri[:,1]-tri[:,0]);normal/=np.maximum(1e-9,np.linalg.norm(normal,axis=1))[:,None]
 def hit(x,z):
  v2=np.array([x,z])-a;u=np.divide(v2[:,0]*v1[:,1]-v1[:,0]*v2[:,1],den,out=np.full(len(den),-99.),where=abs(den)>1e-8);v=np.divide(v0[:,0]*v2[:,1]-v2[:,0]*v0[:,1],den,out=np.full(len(den),-99.),where=abs(den)>1e-8)
  ok=np.flatnonzero((u>=0)&(v>=0)&(u+v<=1)&(normal[:,1]>0));y=tri[:,0,1]+u*(tri[:,1,1]-tri[:,0,1])+v*(tri[:,2,1]-tri[:,0,1])
  if not len(ok):return None
  index=ok[np.argmax(y[ok])];return float(y[index]),float(np.degrees(np.arccos(np.clip(normal[index,1],-1,1))))
 floors={}
 for name,(x,z) in {'player':(-107,23),'chapter entrance':(-113.33,22.5),'police':(-118,21),'dog':(-105,25),'helipad':(-170,-90),'pier shore':(-173,80)}.items():
  h=hit(x,z);floors[name]=h;check(h is not None and h[0]>1 and h[1]<46,'Grounded walkable placement: '+name)
 route=[hit(x,25) for x in np.linspace(-112,-105,61)]
 check(all(h is not None and h[1]<46 for h in route),'Dog route has sampled walkable floor')
 check(max(abs(a[0]-b[0]) for a,b in zip(route[:-1],route[1:]))<.3,'Dog route avoids abrupt floor jumps')
 scene=(ROOT/'Assets/Game/Scenes/SC_AlcatrazSuppliedIsland.unity').read_text();ids=set(re.findall(r'--- !u!\d+ &(\d+)',scene));local=re.findall(r'\{fileID: (\d+)\}',scene)
 check(all(i=='0' or i in ids for i in local),'Supplied scene internal file IDs resolve')
 check('SC_AlcatrazSuppliedIsland.unity' in (ROOT/'ProjectSettings/EditorBuildSettings.asset').read_text(),'Supplied scene is in build settings')
 result={'status':'PASS' if all(x['pass'] for x in checks) else 'FAIL','checks':len(checks),'errors':[x['check'] for x in checks if not x['pass']],'island_triangles_kept':int(keep.sum()),'floor_samples':floors,'scope':'Native source references, glTF dependencies, byte hashes and static triangle floor samples; Unity import, physics and Play Mode unverified'}
 (ROOT/'Validation/Revision09_IntegrationChecks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return not all(x['pass'] for x in checks)
if __name__=='__main__':sys.exit(main())
