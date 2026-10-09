"""Deterministic native Unity YAML assets; no third-party importer required."""
from pathlib import Path
import hashlib,json,struct,math
import numpy as np
from scipy.spatial.transform import Rotation

ROOT=Path(__file__).resolve().parents[1]
ART='Assets/_DesertShift/Art'
HEAD='%YAML 1.1\n%TAG !u! tag:unity3d.com,2011:\n'
MESHES={}; MATERIALS={}; PREVIEW={'meshes':{},'materials':{},'nodes':[]}

def guid(path):return hashlib.md5(('DesertShift-2026/'+str(path)).encode()).hexdigest()
def write(path,text):
    import os
    p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True)
    temp=p.with_name(p.name+'.tmp');temp.write_text(text,encoding='utf-8');os.replace(temp,p);return p
def meta(path,kind='DefaultImporter',extra=''):
    write(str(path)+'.meta',f'fileFormatVersion: 2\nguid: {guid(path)}\n{kind}:\n  externalObjects: {{}}\n{extra}  userData: \n  assetBundleName: \n  assetBundleVariant: \n')
def ref(path,fid=4300000,typ=2):return f'{{fileID: {fid}, guid: {guid(path)}, type: {typ}}}'
def vec(v):return '{'+', '.join(f'{k}: {float(x):.8g}' for k,x in zip('xyzw',v))+'}'
def col(v):return '{'+', '.join(f'{k}: {float(x):.8g}' for k,x in zip('rgba',v))+'}'

def save_mesh(name,mesh,folder='Environment/Desert',bones=None):
    path=f'{ART}/{folder}/{name}.asset';v=np.array(mesh.v,dtype='<f4');n=np.array(mesh.n,dtype='<f4');uv=np.array(mesh.uv,dtype='<f4')
    count=len(v)
    # UV-derived tangent frames keep normal maps valid on every face and bevel.
    it=np.asarray(mesh.t,dtype=np.int64).reshape(-1,3);e1=v[it[:,1]]-v[it[:,0]];e2=v[it[:,2]]-v[it[:,0]]
    d1=uv[it[:,1]]-uv[it[:,0]];d2=uv[it[:,2]]-uv[it[:,0]];det=d1[:,0]*d2[:,1]-d1[:,1]*d2[:,0]
    inv=np.zeros_like(det);np.divide(1,det,out=inv,where=np.abs(det)>1e-8)
    t=(e1*d2[:,1,None]-e2*d1[:,1,None])*inv[:,None];b=(e2*d1[:,0,None]-e1*d2[:,0,None])*inv[:,None]
    tang=np.zeros_like(v);bitang=np.zeros_like(v)
    for k in range(3):np.add.at(tang,it[:,k],t);np.add.at(bitang,it[:,k],b)
    tang-=n*np.sum(n*tang,axis=1)[:,None];length=np.linalg.norm(tang,axis=1)
    missing=length<1e-7
    for index in np.nonzero(missing)[0]:
        axis=np.array([1,0,0]) if abs(n[index,0])<.8 else np.array([0,0,1]);tang[index]=axis-n[index]*np.dot(axis,n[index])
    tang/=np.maximum(np.linalg.norm(tang,axis=1)[:,None],1e-8)
    tangent=np.ones((count,4),dtype='<f4');tangent[:,:3]=tang
    tangent[:,3]=np.where(np.sum(np.cross(n,tang)*bitang,axis=1)<0,-1,1)
    data=np.hstack([v,n,tangent,uv]).astype('<f4')
    channels=[(0,0,3),(12,0,3),(24,0,4),(0,0,0),(40,0,2)]+[(0,0,0)]*7
    bind='[]';bw=None
    if bones:
        bw=np.array(mesh.weights,dtype=float)
        ids=bw[:,:2].astype('<u4');weights=bw[:,2:]
        packed=bytearray()
        for i,row in enumerate(data):
            packed.extend(row.tobytes());packed.extend(struct.pack('<4f',weights[i,0],weights[i,1],0,0));packed.extend(struct.pack('<4I',ids[i,0],ids[i,1],0,0))
        raw=bytes(packed);channels.extend([(48,0,4),(64,10,4)])
        bind='\n'
        for p in bones:
            mat=np.eye(4);mat[:3,3]=-np.array(p)
            bind+='  - '+ '\n    '.join(f'e{a}{b}: {mat[a,b]:.8g}' for a in range(4) for b in range(4))+'\n'
        bind=bind.rstrip()
    else:
        raw=data.tobytes();channels.extend([(0,0,0),(0,0,0)])
    idx=np.array(mesh.t,dtype='<u4' if count>65535 else '<u2')
    center=(v.min(0)+v.max(0))/2;extent=(v.max(0)-v.min(0))/2
    txt=HEAD+f'''--- !u!43 &4300000
Mesh:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name: {name}
  serializedVersion: 11
  m_SubMeshes:
  - serializedVersion: 2
    firstByte: 0
    indexCount: {len(idx)}
    topology: 0
    baseVertex: 0
    firstVertex: 0
    vertexCount: {count}
    localAABB:
      m_Center: {vec(center)}
      m_Extent: {vec(extent)}
  m_Shapes:
    vertices: []
    shapes: []
    channels: []
    fullWeights: []
  m_BindPose: {bind}
  m_BoneNameHashes: 
  m_RootBoneNameHash: 0
  m_BonesAABB: []
  m_VariableBoneCountWeights:
    m_Data: 
  m_MeshCompression: 0
  m_IsReadable: 1
  m_KeepVertices: 1
  m_KeepIndices: 1
  m_IndexFormat: {1 if count>65535 else 0}
  m_IndexBuffer: {idx.tobytes().hex()}
  m_VertexData:
    serializedVersion: 3
    m_VertexCount: {count}
    m_Channels:
'''
    for off,fmt,dim in channels:txt+=f'    - stream: 0\n      offset: {off}\n      format: {fmt}\n      dimension: {dim}\n'
    txt+=f'    m_DataSize: {len(raw)}\n    _typelessdata: {raw.hex()}\n'
    txt+='  m_CompressedMesh:\n'
    for key in ['m_Vertices','m_UV','m_Normals','m_Tangents','m_Weights','m_NormalSigns','m_TangentSigns','m_FloatColors','m_BoneIndices','m_Triangles']:
        txt+=f'    {key}:\n      m_NumItems: 0\n'
        if key in ['m_Vertices','m_UV','m_Normals','m_Tangents','m_FloatColors']:txt+='      m_Range: 0\n      m_Start: 0\n'
        txt+='      m_Data: \n      m_BitSize: 0\n'
    txt+=f'''    m_UVInfo: 0
  m_LocalAABB:
    m_Center: {vec(center)}
    m_Extent: {vec(extent)}
  m_MeshUsageFlags: 0
  m_CookingOptions: 30
  m_BakedConvexCollisionMesh: 
  m_BakedTriangleCollisionMesh: 
  m_MeshMetrics[0]: 1
  m_MeshMetrics[1]: 1
  m_MeshOptimizationFlags: -1
  m_StreamData:
    serializedVersion: 2
    offset: 0
    size: 0
    path: 
'''
    write(path,txt);meta(path,'NativeFormatImporter','  mainObjectFileID: 4300000\n');MESHES[name]=(path,mesh)
    PREVIEW['meshes'][name]={'v':np.round(v,5).tolist(),'n':np.round(n,5).tolist(),'uv':np.round(uv,5).tolist(),'t':mesh.t}
    if bones:PREVIEW['meshes'][name].update({'weights':mesh.weights,'bind':bones})
    return path

def material(name,color,rough=.75,metal=0,texture=None,normal=None,emission=None,transparent=False,tiling=1,shader_guid=None,surface=None,occlusion=None):
    path=f'{ART}/Materials/{name}.mat';shader_guid=shader_guid or '933532a4fcc9baf4fa0491de14d08ed7'
    keywords=[]
    if normal:keywords.append('_NORMALMAP')
    if surface:keywords.append('_METALLICSPECGLOSSMAP')
    if occlusion:keywords.append('_OCCLUSIONMAP')
    if emission:keywords.append('_EMISSION')
    if transparent:keywords.extend(['_SURFACE_TYPE_TRANSPARENT','_ALPHAPREMULTIPLY_ON'])
    txt=HEAD+f'''--- !u!21 &2100000
Material:
  serializedVersion: 8
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name: {name}
  m_Shader: {{fileID: 4800000, guid: {shader_guid}, type: 3}}
  m_Parent: {{fileID: 0}}
  m_ModifiedSerializedProperties: 0
  m_ValidKeywords: {json.dumps(keywords)}
  m_InvalidKeywords: []
  m_LightmapFlags: 2
  m_EnableInstancingVariants: 1
  m_DoubleSidedGI: 0
  m_CustomRenderQueue: {3000 if transparent else -1}
  stringTagMap: {{RenderType: {'Transparent' if transparent else 'Opaque'}}}
  disabledShaderPasses: []
  m_LockedProperties: 
  m_SavedProperties:
    serializedVersion: 3
    m_TexEnvs:
'''
    for key,p in [('_BaseMap',texture),('_MainTex',texture),('_BumpMap',normal),('_EmissionMap',None),('_MetallicGlossMap',surface),('_OcclusionMap',occlusion)]:
        txt+=f'    - {key}:\n        m_Texture: {ref(p,2800000,3) if p else "{fileID: 0}"}\n        m_Scale: {{x: {tiling}, y: {tiling}}}\n        m_Offset: {{x: 0, y: 0}}\n'
    txt+='    m_Ints: []\n    m_Floats:\n'
    for k,v in {'_WorkflowMode':1,'_Surface':int(transparent),'_Blend':1 if transparent else 0,'_Cull':2,'_SrcBlend':1,'_DstBlend':10 if transparent else 0,'_SrcBlendAlpha':1,'_DstBlendAlpha':10 if transparent else 0,'_ZWrite':0 if transparent else 1,'_AlphaClip':0,'_Cutoff':.5,'_Metallic':metal,'_Smoothness':1-rough,'_BumpScale':.65,'_OcclusionStrength':1,'_ReceiveShadows':1,'_SpecularHighlights':1,'_EnvironmentReflections':1,'_QueueOffset':0}.items():txt+=f'    - {k}: {v}\n'
    txt+='    m_Colors:\n'
    txt+=f'    - _BaseColor: {col(color)}\n    - _Color: {col(color)}\n    - _EmissionColor: {col(emission or [0,0,0,1])}\n    - _SpecColor: {{r: 0.2, g: 0.2, b: 0.2, a: 1}}\n  m_BuildTextureStacks: []\n'
    write(path,txt);meta(path,'NativeFormatImporter','  mainObjectFileID: 2100000\n');MATERIALS[name]=path
    PREVIEW['materials'][name]={'color':color,'roughness':rough,'metalness':metal,'texture':texture,'normal':normal,'surface':surface,'occlusion':occlusion,'emission':emission,'transparent':transparent,'tiling':tiling}
    return path

class Node:
    all=[];counter=1000
    def __init__(self,name,parent=None,pos=(0,0,0),rot=(0,0,0),scale=(1,1,1),layer=0,static=True):
        self.name=name;self.parent=parent;self.pos=list(pos);self.rot=list(rot);self.scale=list(scale);self.layer=layer;self.static=static
        self.id=Node.counter;Node.counter+=20;self.tid=self.id+1;self.parts=[];self.children=[];self.mesh=None;self.mat=None;self.active=True
        if parent:parent.children.append(self)
        Node.all.append(self)
    def component(self,cls,body):
        cid=self.id+2+len(self.parts);self.parts.append((cls,cid,body));return cid
    def script(self,file,body=''):
        if '/' not in file:
            paths=list((ROOT/'Assets/_DesertShift/Scripts').rglob(file+'.cs'));assert len(paths)==1,(file,paths);file=str(paths[0].relative_to(ROOT))
        return self.component(114,f'  m_Enabled: 1\n  m_EditorHideFlags: 0\n  m_Script: {ref(file,11500000,3)}\n  m_Name: \n  m_EditorClassIdentifier: \n'+body)
    def render(self,mesh,mat,shadow=1):
        self.mesh=mesh;self.mat=mat
        self.component(33,f'  m_Mesh: {ref(MESHES[mesh][0])}\n')
        self.component(23,renderer_body(MATERIALS[mat],shadow));return self
    def boxcollider(self,size=(1,1,1),center=(0,0,0),trigger=False):
        self.component(65,collider_base(trigger)+f'  serializedVersion: 3\n  m_Size: {vec(size)}\n  m_Center: {vec(center)}\n');return self
    def meshcollider(self,mesh):
        self.component(64,collider_base(False)+f'  serializedVersion: 5\n  m_Convex: 0\n  m_CookingOptions: 30\n  m_Mesh: {ref(MESHES[mesh][0])}\n');return self

def collider_base(trigger=False):
    return f'''  m_Material: {{fileID: 0}}
  m_IncludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_ExcludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_LayerOverridePriority: 0
  m_IsTrigger: {int(trigger)}
  m_ProvidesContacts: 0
  m_Enabled: 1
'''

def renderer_body(material,shadow=1):
    return f'''  m_Enabled: 1
  m_CastShadows: {shadow}
  m_ReceiveShadows: 1
  m_DynamicOccludee: 1
  m_StaticShadowCaster: 0
  m_MotionVectors: 1
  m_LightProbeUsage: 1
  m_ReflectionProbeUsage: 1
  m_RayTracingMode: 2
  m_RayTraceProcedural: 0
  m_RayTracingAccelStructBuildFlagsOverride: 0
  m_RayTracingAccelStructBuildFlags: 1
  m_SmallMeshCulling: 1
  m_RenderingLayerMask: 1
  m_RendererPriority: 0
  m_Materials:
  - {ref(material,2100000)}
  m_StaticBatchInfo:
    firstSubMesh: 0
    subMeshCount: 0
  m_StaticBatchRoot: {{fileID: 0}}
  m_ProbeAnchor: {{fileID: 0}}
  m_LightProbeVolumeOverride: {{fileID: 0}}
  m_ScaleInLightmap: 1
  m_ReceiveGI: 1
  m_PreserveUVs: 0
  m_IgnoreNormalsForChartDetection: 0
  m_ImportantGI: 0
  m_StitchLightmapSeams: 1
  m_SelectedEditorRenderState: 3
  m_MinimumChartSize: 4
  m_AutoUVMaxDistance: 0.5
  m_AutoUVMaxAngle: 89
  m_LightmapParameters: {{fileID: 0}}
  m_SortingLayerID: 0
  m_SortingLayer: 0
  m_SortingOrder: 0
  m_AdditionalVertexStreams: {{fileID: 0}}
'''

CLASSES={23:'MeshRenderer',33:'MeshFilter',65:'BoxCollider',64:'MeshCollider',114:'MonoBehaviour',108:'Light',20:'Camera',81:'AudioListener',143:'CharacterController',95:'Animator',137:'SkinnedMeshRenderer',54:'Rigidbody',215:'ReflectionProbe',120:'LineRenderer',205:'LODGroup',50:'Rigidbody2D'}
def node_yaml(n,root_override=False):
    q=Rotation.from_euler('xyz',n.rot,degrees=True).as_quat()
    txt=f'''--- !u!1 &{n.id}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: {n.tid}}}
'''
    for _,cid,_ in n.parts:txt+=f'  - component: {{fileID: {cid}}}\n'
    txt+=f'''  m_Layer: {n.layer}
  m_Name: {json.dumps(n.name)}
  m_TagString: {'Player' if n.name=='Player' else 'MainCamera' if n.name=='Main Camera' else 'Untagged'}
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: {8 if n.static else 0}
  m_IsActive: {int(n.active)}
--- !u!4 &{n.tid}
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {n.id}}}
  serializedVersion: 2
  m_LocalRotation: {vec(q)}
  m_LocalPosition: {vec((0,0,0) if root_override else n.pos)}
  m_LocalScale: {vec(n.scale)}
  m_ConstrainProportionsScale: 0
  m_Children:{'' if n.children else ' []'}
'''
    for c in n.children:txt+=f'  - {{fileID: {c.tid}}}\n'
    txt+=f'  m_Father: {{fileID: {n.parent.tid if n.parent and not root_override else 0}}}\n  m_LocalEulerAnglesHint: {vec(n.rot)}\n'
    for cls,cid,body in n.parts:
        txt+=f'''--- !u!{cls} &{cid}
{CLASSES[cls]}:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {n.id}}}
'''+body
    return txt

def save_prefab(root,category,name=None):
    def walk(n):return [n]+[v for c in n.children for v in walk(c)]
    path=f'Assets/_DesertShift/Prefabs/{category}/{name or root.name}.prefab'
    write(path,HEAD+''.join(node_yaml(n,n==root) for n in walk(root)));meta(path,'PrefabImporter');return path

def save_scene(settings):
    path='Assets/_DesertShift/Scenes/SC_DesertTown.unity'
    txt=HEAD+settings+''.join(node_yaml(n) for n in Node.all)
    txt+='--- !u!1660057539 &9223372036854775807\nSceneRoots:\n  m_ObjectHideFlags: 0\n  m_Roots:\n'
    for n in Node.all:
        if not n.parent:txt+=f'  - {{fileID: {n.tid}}}\n'
    write(path,txt);meta(path)
    for n in Node.all:
        if n.mesh:
            obj={'name':n.name,'id':n.id,'parent':n.parent.id if n.parent else 0,'mesh':n.mesh,'mat':n.mat,'pos':n.pos,'rot':n.rot,'scale':n.scale}
            if hasattr(n,'skinBones'):obj['skinBones']=n.skinBones
            PREVIEW['nodes'].append(obj)
        else:PREVIEW['nodes'].append({'name':n.name,'id':n.id,'parent':n.parent.id if n.parent else 0,'pos':n.pos,'rot':n.rot,'scale':n.scale})
    return path
