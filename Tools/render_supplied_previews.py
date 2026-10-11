"""Render the packaged meshes as labelled offline previews, not Unity screenshots.
Uses native FBX transforms, OBJ/glTF geometry and the packaged color textures.
"""
from pathlib import Path
import re,json,math
import numpy as np,moderngl,yaml
from scipy.spatial.transform import Rotation
from PIL import Image,ImageDraw,ImageFont
from fbx_pose import Rig
from fbx_pose import Character,animation
ROOT=Path(__file__).resolve().parents[1];RES=ROOT/'Assets/Game/Supplied/Resources/AlcatrazSupplied'
C=moderngl.create_standalone_context(backend='egl')
PROGRAM=C.program(vertex_shader='''#version 330
in vec3 position;in vec3 normal;in vec2 texcoord;uniform mat4 vp;out vec2 uv;out vec3 norm;out vec3 point;void main(){uv=texcoord;norm=normal;point=position;gl_Position=vp*vec4(position,1);}''',fragment_shader='''#version 330
in vec2 uv;in vec3 norm;in vec3 point;uniform sampler2D image;uniform vec4 base;uniform bool textured;uniform vec3 eye;out vec4 color;
void main(){vec4 t=textured?texture(image,uv):vec4(1);if(t.a<.4)discard;vec3 n=normalize(norm);if(!gl_FrontFacing)n=-n;vec3 l=normalize(vec3(-.4,.9,.5));vec3 rgb=pow(t.rgb*base.rgb,vec3(2.2));float sun=max(dot(n,l),0);vec3 lit=rgb*(.58+sun*.92);vec3 h=normalize(l+normalize(eye-point));lit+=vec3(.04)*pow(max(dot(n,h),0),35);lit=clamp((lit*(2.51*lit+.03))/(lit*(2.43*lit+.59)+.14),0,1);color=vec4(pow(lit,vec3(1./2.2)),t.a*base.a);}''')
TEXTURES={}
def texture(p):
 if p is None:return None
 p=Path(p)
 if p not in TEXTURES:
  im=Image.open(p).convert('RGBA');im.thumbnail((4096,4096));tx=C.texture(im.size,4,im.tobytes());tx.build_mipmaps();TEXTURES[p]=tx
 return TEXTURES[p]
def mesh(v,t,uv=None,normal=None,path=None,color=(1,1,1,1),name=''):
 v=np.asarray(v,dtype='f4');t=np.asarray(t,dtype='u4').reshape(-1,3)
 if normal is None:
  n=np.cross(v[t[:,1]]-v[t[:,0]],v[t[:,2]]-v[t[:,0]]);normal=np.zeros_like(v)
  for k in range(3):np.add.at(normal,t[:,k],n)
  normal/=np.maximum(1e-9,np.linalg.norm(normal,axis=1))[:,None]
 return {'v':v,'t':t,'uv':np.asarray(uv if uv is not None else np.zeros((len(v),2)),dtype='f4'),'n':np.asarray(normal,dtype='f4'),'texture':path,'color':color,'name':name}
def transform(m,matrix):
 out={**m};out['v']=m['v']@matrix[:3,:3].T+matrix[:3,3];out['n']=m['n']@np.linalg.inv(matrix[:3,:3]);out['n']/=np.maximum(1e-8,np.linalg.norm(out['n'],axis=1))[:,None];return out
def bounds(meshes):
 v=np.concatenate([m['v'] for m in meshes]);return v.min(0),v.max(0)
def fit(meshes,height=1,position=(0,0,0),bottom=True):
 lo,hi=bounds(meshes);s=height/max(1e-6,hi[1]-lo[1]);matrix=np.diag([s,s,s,1]);matrix[:3,3]=np.array(position)-np.array([(hi[0]+lo[0])/2,lo[1] if bottom else (hi[1]+lo[1])/2,(hi[2]+lo[2])/2])*s
 return [transform(m,matrix) for m in meshes]
def gltf(name):
 folder=RES/name;d=json.loads((folder/(name+'.gltf')).read_text());bs=[(folder/b['uri']).read_bytes() for b in d['buffers']];world={};parents={child:i for i,node in enumerate(d['nodes']) for child in node.get('children',[])}
 def accessor(i):
  a=d['accessors'][i];v=d['bufferViews'][a['bufferView']];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1',5122:'<i2',5120:'i1'}[a['componentType']];stride=v.get('byteStride',n*np.dtype(dt).itemsize)
  out=np.ndarray((a['count'],n),dt,buffer=bs[v['buffer']],offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(stride,np.dtype(dt).itemsize)).copy()
  if a.get('normalized'):out=out/np.iinfo(dt).max
  return out
 def matrix(i):
  if i not in world:
   node=d['nodes'][i]
   if 'matrix' in node:m=np.array(node['matrix']).reshape(4,4).T
   else:
    m=np.eye(4);m[:3,:3]=Rotation.from_quat(node.get('rotation',[0,0,0,1])).as_matrix()@np.diag(node.get('scale',[1,1,1]));m[:3,3]=node.get('translation',[0,0,0])
   world[i]=matrix(parents[i])@m if i in parents else m
  return world[i]
 result=[];flip=np.diag([-1,1,1,1])
 for i,node in enumerate(d['nodes']):
  if 'mesh' not in node:continue
  for primitive in d['meshes'][node['mesh']]['primitives']:
   att=primitive['attributes'];v=accessor(att['POSITION']);n=accessor(att['NORMAL']) if 'NORMAL' in att else None;uv=accessor(att['TEXCOORD_0']) if 'TEXCOORD_0' in att else None;t=accessor(primitive['indices']).reshape(-1,3);mat=d.get('materials',[{}])[primitive.get('material',0)];pbr=mat.get('pbrMetallicRoughness',{});path=None
   if 'baseColorTexture' in pbr:
    tex=d['textures'][pbr['baseColorTexture']['index']];path=folder/d['images'][tex['source']]['uri']
   if 'skin' in node:
    skin=d['skins'][node['skin']];ib=accessor(skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1);joint=accessor(att['JOINTS_0']).astype(int);weight=accessor(att['WEIGHTS_0']);matrices=np.array([matrix(j)@b for j,b in zip(skin['joints'],ib)]);pv=np.c_[v,np.ones(len(v))];outv=np.zeros_like(v);outn=np.zeros_like(n)
    for k in range(4):
     ms=matrices[joint[:,k]];outv+=np.einsum('nij,nj->ni',ms,pv)[:,:3]*weight[:,k,None];outn+=np.einsum('nij,nj->ni',ms[:,:3,:3],n)*weight[:,k,None]
    m=mesh(outv,t,uv,outn,path,pbr.get('baseColorFactor',[1,1,1,1]),node.get('name',''));m=transform(m,flip)
   else:m=transform(mesh(v,t,uv,n,path,pbr.get('baseColorFactor',[1,1,1,1]),node.get('name','')),flip@matrix(i))
   m['t']=m['t'][:,[0,2,1]];result.append(m)
 return result
def fbx(name):
 if name!='House':path=RES/name/(name+'.fbx')
 else:
  path=next((ROOT/'SourceAssets/Supplied09/the-house-lost-at-sea').rglob('*.fbx'),None)
  if path is None:
   import hashlib
   spec=json.loads((ROOT/'Assets/Game/Supplied/HouseSource/HouseParts.json').read_text());payload=b''.join((ROOT/p).read_bytes() for p in spec['parts'])
   if hashlib.sha256(payload).hexdigest()!=spec['sha256']:raise ValueError('House parts do not match their source hash')
   path=ROOT/'SourceAssets/Supplied09/Reconstructed/House.fbx';path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(payload)
 rig=Rig(path);rig.channels={};worlds=rig.sample(0);result=[];catalog=json.loads((RES/'Catalog.json').read_text())['materials']
 for geometry in rig.objects.values():
  if geometry.name!='Geometry' or geometry.props[2]!='Mesh':continue
  model=next((c[2] for c in rig.links if c[0]=='OO' and c[1]==geometry.props[0] and c[2] in rig.models),None)
  if model is None:continue
  if name=='House' and rig.names[model] in ('TreeBranches.001','WindowLightRefl'):continue
  source=geometry.array('Vertices').reshape(-1,3);indices=geometry.array('PolygonVertexIndex');norm=geometry.child('LayerElementNormal');uv=geometry.child('LayerElementUV');mats=geometry.child('LayerElementMaterial');source_mats=[rig.objects[c[1]].props[1].split('\x00')[0] for c in rig.links if c[0]=='OO' and c[2]==model and c[1] in rig.objects and rig.objects[c[1]].name=='Material']
  if not source_mats:source_mats=['Gun' if name=='Pistol10mm' else 'Material.002']
  corners=[];control=[];groups=[];polygon=[];poly=0;mat_ids=mats.array('Materials') if mats else np.array([0])
  for corner,index in enumerate(indices):
   polygon.append((corner,int(-index-1 if index<0 else index)))
   if index>=0:continue
   for j in range(1,len(polygon)-1):
    for c,v in [polygon[0],polygon[j],polygon[j+1]]:corners.append(c);control.append(v);groups.append(mat_ids[0 if len(mat_ids)==1 else poly])
   polygon=[];poly+=1
  corners=np.array(corners);control=np.array(control);groups=np.array(groups)
  def layer(n,array,index):
   if n is None:return None
   data=n.array(array).reshape(-1,2 if array=='UV' else 3);mapping=n.child('MappingInformationType').props[0];ids=control if mapping in ('ByVertice','ByControlPoint') else corners
   reference=n.child('ReferenceInformationType').props[0];ind=n.array(index)
   if reference=='IndexToDirect' and ind is not None:ids=ind[ids]
   return data[ids]
  normals=layer(norm,'Normals','NormalsIndex');tex=layer(uv,'UV','UVIndex');matrix=worlds[rig.names[model]].copy();matrix[:3,:]*=.01;matrix=np.diag([-1,1,1,1])@matrix
  if tex is not None:tex[:,1]=1-tex[:,1]
  if abs(np.linalg.det(matrix[:3,:3]))<1e-15:continue
  for group,key in enumerate(source_mats):
   if name=='House' and key in ['Sea','Sky','Mist','Waves','ParticleDustShdr','ReflShdr','BushesRefl','ShrubsRefl','TreeTrunkRefl']:continue
   ids=np.flatnonzero(groups==group)
   if len(ids)==0:continue
   mat_path=ROOT/catalog[key];text=mat_path.read_text();guid=re.search(r'- _BaseMap:\s+m_Texture: \{fileID: \d+, guid: (\w+)',text);texture_path=ASSETS[guid[1]] if guid else None
   color=re.search(r'- _BaseColor: \{r: ([\d.e+-]+), g: ([\d.e+-]+), b: ([\d.e+-]+), a: ([\d.e+-]+)',text)
   m=mesh(source[control[ids]],np.arange(len(ids)).reshape(-1,3)[:,[0,2,1]],tex[ids] if tex is not None else None,normals[ids] if normals is not None else None,texture_path,color=[float(x) for x in color.groups()] if color else [1,1,1,1],name=rig.names[model]);result.append(transform(m,matrix))
 return result
def native_prefab(name):
 text=(ROOT/'Assets/Game/Resources/BlackstoneFoundation/Weapons'/f'{name}.prefab').read_text();clean=re.sub(r'^%.*\n','',text,flags=re.M);clean=re.sub(r'^--- !u!\d+ &(-?\d+)',r'---\nanchor: \1',clean,flags=re.M);documents={d['anchor']:d for d in yaml.load_all(clean,Loader=yaml.CSafeLoader)};ts={i:d['Transform'] for i,d in documents.items() if 'Transform' in d};go_t={d['m_GameObject']['fileID']:i for i,d in ts.items()};world={}
 def transform_for(i):
  if i not in world:
   t=ts[i];m=np.eye(4);q=t['m_LocalRotation'];m[:3,:3]=Rotation.from_quat([q[k] for k in 'xyzw']).as_matrix()@np.diag([t['m_LocalScale'][k] for k in 'xyz']);m[:3,3]=[t['m_LocalPosition'][k] for k in 'xyz'];parent=t['m_Father']['fileID'];world[i]=transform_for(parent)@m if parent else m
  return world[i]
 result=[]
 for d in documents.values():
  if 'MeshFilter' not in d:continue
  f=d['MeshFilter'];source=ASSETS[f['m_Mesh']['guid']].read_text();count=int(re.search(r'm_VertexCount: (\d+)',source)[1]);size=int(re.search(r'm_DataSize: (\d+)',source)[1]);raw=bytes.fromhex(re.search(r'_typelessdata: ([0-9a-f]+)',source)[1]);v=np.ndarray((count,3),'<f4',raw,strides=(size//count,4));n=np.ndarray((count,3),'<f4',raw,offset=12,strides=(size//count,4));uv=np.ndarray((count,2),'<f4',raw,offset=40,strides=(size//count,4));t=np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: ([0-9a-f]+)',source)[1]),dtype='<u4' if 'm_IndexFormat: 1' in source else '<u2').reshape(-1,3)
  renderer=next(x['MeshRenderer'] for x in documents.values() if 'MeshRenderer' in x and x['MeshRenderer']['m_GameObject']==f['m_GameObject']);mat=ASSETS[renderer['m_Materials'][0]['guid']].read_text();color=re.search(r'- _BaseColor: \{r: ([\d.]+), g: ([\d.]+), b: ([\d.]+), a: ([\d.]+)',mat);result.append(transform(mesh(v,t,uv,n,color=[float(x) for x in color.groups()]),transform_for(go_t[f['m_GameObject']['fileID']])))
 return result
def police():
 path=RES/'Police';vertices=[];normals=[];uv=[];groups={};key=None
 for line in (path/'Police.obj').read_text().splitlines():
  fields=line.split()
  if not fields:continue
  if fields[0]=='v':vertices.append([float(x) for x in fields[1:4]])
  elif fields[0]=='vn':normals.append([float(x) for x in fields[1:4]])
  elif fields[0]=='vt':uv.append([float(x) for x in fields[1:3]])
  elif fields[0]=='usemtl':key=fields[1];groups.setdefault(key,[])
  elif fields[0]=='f':
   corners=[tuple(int(x) if x else 0 for x in token.split('/')) for token in fields[1:]]
   for i in range(1,len(corners)-1):groups[key].extend([corners[0],corners[i],corners[i+1]])
 result=[];v=np.array(vertices);n=np.array(normals);tex=np.array(uv);tex[:,1]=1-tex[:,1]
 for key,corners in groups.items():
  corners=np.array(corners);m=mesh(v[corners[:,0]-1],np.arange(len(corners)).reshape(-1,3)[:,[0,2,1]],tex[corners[:,1]-1],n[corners[:,2]-1],path/(key+'_d.jpg'),name=key);result.append(transform(m,np.diag([-1,1,1,1])))
 return result
ASSETS={}
for meta in (ROOT/'Assets').rglob('*.meta'):
 guid=re.search(r'^guid: (\w+)',meta.read_text(),re.M)
 if guid:ASSETS[guid[1]]=Path(str(meta)[:-5])
def view(eye,center,up=(0,1,0)):
 eye=np.array(eye,float);f=np.array(center,float)-eye;f/=np.linalg.norm(f);s=np.cross(f,up);s/=np.linalg.norm(s);u=np.cross(s,f);m=np.eye(4);m[0,:3]=s;m[1,:3]=u;m[2,:3]=-f;m[:3,3]=-m[:3,:3]@eye;return m
GPU={}
def render(meshes,size=(1280,720),eye=None,center=None,transparent=False,orthographic=False,fov=42,near_clip=.005,background=(.025,.07,.085)):
 lo,hi=bounds(meshes);center=np.array(center if center is not None else (lo+hi)/2);radius=np.linalg.norm(hi-lo)/2;eye=np.array(eye if eye is not None else center+np.array([1.4,.65,1.8])*max(.01,radius)*1.8);w,h=size;camera=view(eye,center)
 if orthographic:
  v=np.concatenate([m['v'] for m in meshes]);project=v@camera[:3,:3].T+camera[:3,3];x,y=project[:,:2].min(0),project[:,:2].max(0);sy=max((y[1]-x[1])*.58,(y[0]-x[0])*.58*h/w);sx=sy*w/h;projection=np.diag([1/sx,1/sy,-1/10000,1])
 else:
  q=1/math.tan(math.radians(fov)/2);near=near_clip;far=5000;projection=np.zeros((4,4));projection[0,0]=q*h/w;projection[1,1]=q;projection[2,2]=(far+near)/(near-far);projection[2,3]=2*far*near/(near-far);projection[3,2]=-1
 fbo=C.simple_framebuffer(size,components=4);fbo.use();C.enable(moderngl.DEPTH_TEST);fbo.clear(*background,0 if transparent else 1);PROGRAM['vp'].write((projection@camera).astype('f4').T.tobytes());PROGRAM['eye'].value=tuple(eye)
 for m in meshes:
  key=id(m)
  if key not in GPU:
   arr=np.c_[m['v'],m['n'],m['uv']].astype('f4');GPU[key]=(m,C.vertex_array(PROGRAM,[(C.buffer(arr.tobytes()),'3f 3f 2f','position','normal','texcoord')],C.buffer(m['t'].astype('u4').tobytes())))
  tx=texture(m['texture']);PROGRAM['textured'].value=tx is not None;PROGRAM['base'].value=tuple(m['color'])
  if tx:tx.use(0)
  GPU[key][1].render()
 im=Image.frombytes('RGBA',size,fbo.read(components=4)).transpose(Image.Transpose.FLIP_TOP_BOTTOM);fbo.release();return im

def weapon_icons():
 destination=RES/'Icons';destination.mkdir(exist_ok=True)
 for enum,name in [('Pistol','Pistol10mm'),('Revolver','Revolver'),('Rifle','Rifle'),('Knife','Knife')]:
  meshes=fbx(name) if enum in ('Pistol','Revolver') else native_prefab(name);lo,hi=bounds(meshes);center=(lo+hi)/2;radius=max(hi-lo)
  im=render(meshes,(640,300),eye=center+np.array([2.5,.7,.45])*radius,center=center,transparent=True,orthographic=True);im.save(destination/(enum+'.png'));print('Rendered actual weapon icon',enum,flush=True)
  import unity_writer as u;u.meta(str((destination/(enum+'.png')).relative_to(ROOT)),'TextureImporter','  textureType: 0\n  alphaIsTransparency: 1\n  mipmaps:\n    enableMipMap: 0\n  maxTextureSize: 1024\n')
 folder=str(destination.relative_to(ROOT));Path(str(destination)+'.meta').write_text('fileFormatVersion: 2\nguid: '+u.guid(folder)+'\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n')
def main():
 weapon_icons();folder=ROOT/'Documentation/Revision09Previews';folder.mkdir(exist_ok=True)
 island=gltf('Island');offset=np.eye(4);offset[:3,3]=[-63,45,12];island=[transform(m,offset) for m in island];coast=json.loads((RES/'Island/Coastline.json').read_text())['points']
 for m in island:
  centers=m['v'][m['t']].mean(1);inside=np.zeros(len(centers),bool)
  for i,a in enumerate(coast):
   b=coast[i-1];inside^=((a['z']>centers[:,2])!=(b['z']>centers[:,2]))&(centers[:,0]<(b['x']-a['x'])*(centers[:,2]-a['z'])/(b['z']-a['z']+1e-20)+a['x'])
  m['t']=m['t'][inside]
 im=render(island,eye=[350,285,410],center=[0,30,0]);d=ImageDraw.Draw(im);d.rectangle((0,675,1280,720),fill='#111e24');d.text((22,688),'SUPPLIED ALCATRAZ ISLAND / ACTUAL MESH / OFFLINE PREVIEW — NOT A UNITY CAPTURE',font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17),fill='#e1d4b8');im.convert('RGB').save(folder/'Island.png')
 print('Rendered island preview',flush=True)
 model=fit(police(),1.82,(-1.15,0,0));model+=fit(gltf('Helmet'),.32,(-1.15,1.55,0));model+=fit(gltf('Vest'),.58,(-1.15,.98,-.08));model+=fit(gltf('Dog'),.82,(1,0,.2))
 im=render(model,(1280,720),eye=[4,2,7],center=[0,.95,0],orthographic=True);d=ImageDraw.Draw(im);d.rectangle((0,675,1280,720),fill='#111e24');d.text((22,688),'SUPPLIED POLICE + TACTICAL GEAR + DOG / OFFLINE ASSET PREVIEW',font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',19),fill='#e1d4b8');im.convert('RGB').save(folder/'Characters.png')
 print('Rendered equipped police and dog',flush=True)
 model=fit(fbx('House'),14,(-16,0,0))+fit(gltf('Helicopter'),2.8,(16,0,0));im=render(model,(1280,720),eye=[55,25,65],center=[0,5,0],orthographic=True);d=ImageDraw.Draw(im);d.rectangle((0,675,1280,720),fill='#111e24');d.text((22,688),'SUPPLIED COASTAL HOUSE + LITTLE BIRD / OFFLINE ASSET PREVIEW',font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',19),fill='#e1d4b8');im.convert('RGB').save(folder/'Environment.png')
 print('Rendered house and helicopter',flush=True)
 # A source-geometry view of the authored spawn; labels reproduce the starter inventory.
 character=Character(ROOT/'Assets/Game/Resources/BlackstoneFoundation/Characters/Male_Adult_16/Male_Adult_16.fbx');clip=animation(ROOT/'Assets/Game/Foundation/Animations/Rocketbox/Run.fbx');hero=[]
 rotation=np.eye(4);rotation[:3,:3]=Rotation.from_euler('y',250,degrees=True).as_matrix();rotation[:3,3]=[-107,49.4443,23]
 for data in character.meshes(clip,.3):
  texture_path=data['texture'];adapted=texture_path.parent/('m019_body_elias08.png' if 'body' in data['name'] else 'm019_head_elias08.png')
  if adapted.exists():texture_path=adapted
  uv=data['uv'].copy();uv[:,1]=1-uv[:,1]
  hero.append(transform(mesh(data['v'],data['t'],uv,data['n'],texture_path),rotation))
 scene=island+hero+fit(police(),1.82,(-118,49.366,21))+fit(gltf('Dog'),.82,(-105,49.199,25))
 facing=Rotation.from_euler('yx',[250,12],degrees=True).apply([0,0,1]);pivot=np.array([-107,50.8943,23]);eye=pivot-facing*3.15
 im=render(scene,(1600,900),eye=eye,center=eye+facing*8);draw_hud(im);im.convert('RGB').save(folder/'GameplayLayout.png')
 print('Rendered labelled gameplay layout',flush=True)

def draw_hud(im):
 d=ImageDraw.Draw(im,'RGBA');font=lambda size:ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',size);bold=lambda size:ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',size)
 d.rectangle((25,22,480,142),fill=(4,11,14,225));d.text((43,35),'GOAL: ESCAPE THE PRISON',font=bold(22),fill='#e1c180');d.text((43,73),'Find the cellhouse entrance',font=font(21),fill='#f1f1ed');d.text((43,110),'Prepare your route · Play Chapter 01',font=font(16),fill='#bdcbcc')
 d.rectangle((1195,22,1575,127),fill=(4,11,14,225));d.text((1212,35),'INMATE ELIAS VALE / B-04',font=font(18),fill='#e7ede9');d.text((1212,72),'ALCATRAZ ISLAND',font=bold(24),fill='#e1c180')
 names=[('Rifle','SERVICE RIFLE','5.56 mm / automatic','30 / 120','4'),('Pistol','10MM PISTOL','10 mm / semi-auto','15 / 75','3'),('Revolver','PBR REVOLVER','6-round cylinder','6 / 36','5'),('Knife','COMBAT KNIFE','Close combat','READY','2')]
 for i,(key,title,detail,ammo,hotkey) in enumerate(names):
  y=177+i*127;d.rectangle((1210,y,1574,y+113),fill=(5,15,18,236),outline='#4a5c60',width=2);d.text((1225,y+10),title,font=bold(18),fill='#eef0e9');d.text((1538,y+10),hotkey,font=font(17),fill='#dfc28a');d.text((1410,y+40),detail,font=font(14),fill='#c4ced0');d.text((1410,y+69),ammo,font=bold(20),fill='#dfc28a');icon=Image.open(RES/'Icons'/(key+'.png'));icon.thumbnail((176,67));im.alpha_composite(icon,(1223,y+37+(67-icon.height)//2))
 map_image=Image.open(RES/'Island/Minimap.png').resize((240,160));d.rectangle((26,690,266,850),fill=(6,22,29,240));im.alpha_composite(map_image,(26,690));px=26+(1-(-107+340)/680)*240;py=690+(23+225)/450*160;d.ellipse((px-4,py-4,px+4,py+4),fill='white');d.text((26,854),'ALCATRAZ · HOLD M FOR MAP',font=font(14),fill='#dce9e5')
 d.rectangle((1200,790,1575,870),fill=(5,15,18,230));d.text((1220,806),'UNARMED',font=bold(24),fill='#e4ddc5');d.text((1220,844),'Starter inventory / source layout',font=font(15),fill='#bac7c9');d.text((391,865),'WASD Move   Shift Run   RMB Aim   LMB Use   R Reload   1–5 Equipment',font=font(16),fill='#eeeee8')
 d.rectangle((330,0,1170,25),fill=(10,20,24,240));d.text((346,5),'OFFLINE SOURCE PREVIEW / NOT A UNITY SCREENSHOT / PLAY MODE UNVERIFIED',font=bold(13),fill='#e8cb8a')
if __name__=='__main__':main()
