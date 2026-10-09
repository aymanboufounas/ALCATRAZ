"""Offline sampling of the shipped FBX sources; this is not Unity playback."""
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from fbx_inspect import read

def props(model):
    block=model.child('Properties70')
    return {p.props[0]:p.props[4:] for p in block.children} if block else {}

def local_matrix(values,order='xyz'):
    p=values.get('Lcl Translation',[0,0,0]);r=values.get('Lcl Rotation',[0,0,0]);s=values.get('Lcl Scaling',[1,1,1])
    pre=values.get('PreRotation',[0,0,0]);post=values.get('PostRotation',[0,0,0])
    m=np.eye(4);m[:3,3]=p
    m[:3,:3]=Rotation.from_euler(order,pre,degrees=True).as_matrix() @ Rotation.from_euler(order,r,degrees=True).as_matrix() @ Rotation.from_euler(order,post,degrees=True).as_matrix().T @ np.diag(s)
    return m

class Rig:
    def __init__(self,path):
        root=read(path);objects=root.child('Objects');self.objects={n.props[0]:n for n in objects.children if n.props}
        self.models={i:n for i,n in self.objects.items() if n.name=='Model'}
        self.names={i:n.props[1].split('\x00')[0] for i,n in self.models.items()}
        self.links=[n.props for n in root.child('Connections').children if n.name=='C'];self.parents={}
        for c in self.links:
            if c[0]=='OO' and c[1] in self.models and c[2] in self.models:self.parents[c[1]]=c[2]
        self.base={i:props(n) for i,n in self.models.items()};self.channels={}
        for c in self.links:
            if c[0]=='OP' and c[1] in self.objects and self.objects[c[1]].name=='AnimationCurveNode' and c[2] in self.models:
                for curve in self.links:
                    if curve[0]=='OP' and curve[2]==c[1] and curve[1] in self.objects and self.objects[curve[1]].name=='AnimationCurve':
                        node=self.objects[curve[1]]
                        self.channels[(c[2],c[3],curve[3][-1])]=(node.array('KeyTime')/46186158000,node.array('KeyValueFloat'))
        self.duration=max((times[-1] for times,values in self.channels.values()),default=1)
    def sample(self,time=0,inplace=True,order='xyz'):
        result={};locals={i:{k:list(v) for k,v in p.items()} for i,p in self.base.items()}
        for (bone,property,axis),(times,values) in self.channels.items():
            v=locals[bone].setdefault(property,[0,0,0]);index='XYZ'.index(axis)
            anchor=inplace and self.names[bone]=='Bip01' and (property=='Lcl Translation' and axis in 'XZ' or property=='Lcl Rotation' and any(s in str(self.path) for s in ['TurnLeft','TurnRight']))
            v[index]=float(values[0] if anchor else np.interp(time,times,values))
        def world(i):
            if i not in result:
                m=local_matrix(locals[i],order)
                result[i]=world(self.parents[i])@m if i in self.parents else m
            return result[i]
        for i in self.models:world(i)
        return {self.names[i]:m for i,m in result.items()}
    @property
    def path(self):return getattr(self,'_path','')

class Character:
    def __init__(self,path):
        self.path=Path(path);self.rig=Rig(path);objects=self.rig.objects
        self.geometry=next(n for n in objects.values() if n.name=='Geometry' and n.props[2]=='Mesh')
        self.points=self.geometry.array('Vertices').reshape(-1,3);self.indices=self.geometry.array('PolygonVertexIndex')
        self.clusters=[];weight=np.zeros(len(self.points))
        for node in objects.values():
            if node.name!='Deformer' or node.props[2]!='Cluster':continue
            bone=next((c[1] for c in self.rig.links if c[0]=='OO' and c[2]==node.props[0] and c[1] in self.rig.models),None)
            if bone is None:continue
            ids=node.array('Indexes');weights=node.array('Weights');weight[ids]+=weights
            transform=node.array('Transform').reshape(4,4).T;link=node.array('TransformLink').reshape(4,4).T
            self.clusters.append((self.rig.names[bone],ids,weights,transform,link))
        if np.max(np.abs(weight-1))>.002:raise ValueError('Unnormalized skin weights')
        self.bind=self.clusters[0][4]@self.clusters[0][3]
        self.uv=self.geometry.child('LayerElementUV').array('UV').reshape(-1,2)
        self.uvindex=self.geometry.child('LayerElementUV').array('UVIndex')
        self.normals=self.geometry.child('LayerElementNormal').array('Normals').reshape(-1,3)
        self.materials=self.geometry.child('LayerElementMaterial').array('Materials')
        self.material_names=[n.props[1].split('\x00')[0] for n in objects.values() if n.name=='Material']
        corners=[];vertex=[];group=[];current=[];poly=0
        for i,index in enumerate(self.indices):
            current.append((i,int(-index-1 if index<0 else index)))
            if index>=0:continue
            for j in range(1,len(current)-1):
                for corner,v in [current[0],current[j],current[j+1]]:
                    corners.append(corner);vertex.append(v);group.append(int(self.materials[poly]))
            current=[];poly+=1
        self.corners=np.asarray(corners);self.vertex=np.asarray(vertex);self.groups=np.asarray(group)
        rest=(self.bind@np.c_[self.points,np.ones(len(self.points))].T).T[:,:3]*.01
        self.scale=1.78/(rest[:,1].max()-rest[:,1].min());self.bottom=rest[:,1].min()
    def meshes(self,clip=None,time=0):
        if clip is None:
            transforms=np.repeat(self.bind[None,:,:],len(self.points),axis=0)
        else:
            worlds=clip.sample(time);transforms=np.zeros((len(self.points),4,4))
            for name,ids,weights,transform,link in self.clusters:
                matrix=worlds.get(name,link)@transform
                transforms[ids]+=matrix[None,:,:]*weights[:,None,None]
        points=np.einsum('nij,nj->ni',transforms,np.c_[self.points,np.ones(len(self.points))])[:,:3]*.01
        points[:,1]-=self.bottom;points*=self.scale
        normals=np.einsum('nij,nj->ni',transforms[self.vertex,:3,:3],self.normals[self.corners]);normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-8)
        # FBX sources are right handed; Unity's baked import is left handed.
        # Reflect X and reverse winding together, preserving texture coordinates.
        vertices=points[self.vertex]*[-1,1,1];normals*=np.array([-1,1,1])
        uv=self.uv[self.uvindex[self.corners]];result=[]
        for group,name in enumerate(self.material_names):
            ids=np.flatnonzero(self.groups==group)
            texture=self.path.parent/(name+'_color.png')
            adapted=self.path.parent/(name+'_inmate.png')
            if adapted.exists():texture=adapted
            alcatraz=self.path.parent/(name+'_alcatraz.png')
            if alcatraz.exists():texture=alcatraz
            result.append({'v':vertices[ids],'n':normals[ids],'uv':uv[ids],'t':np.arange(len(ids)).reshape(-1,3)[:,[0,2,1]].ravel(), 'texture':texture,'name':name})
        return result

def animation(path):
    rig=Rig(path);rig._path=str(path);return rig
