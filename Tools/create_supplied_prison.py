"""Package the native cellhouse interior without the obsolete exterior island.
Reuse native materials/meshes and colliders; crop mixed rail batches to the rooms.
"""
from pathlib import Path
import re,json
import numpy as np
import yaml
from scipy.spatial.transform import Rotation
from PIL import Image,ImageDraw
import unity_writer as u
from geometry import Mesh

ROOT=u.ROOT
BASE='Assets/Game/Supplied/Resources/AlcatrazSupplied/Cellhouse'

def main():
    source=(ROOT/'Assets/Game/Scenes/SC_AlcatrazIsland.unity').read_text()
    raw={int(m[2]):(int(m[1]),b) for b in re.split(r'(?=--- !u!)',source) if (m:=re.match(r'--- !u!(\d+) &(\d+)',b))}
    docs={i:yaml.load(b.split('\n',1)[1],Loader=yaml.CSafeLoader) for i,(kind,b) in raw.items() if kind not in [29,104,157,196,1660057539]}
    gos={i:d['GameObject'] for i,d in docs.items() if 'GameObject' in d}
    ts={i:d['Transform'] for i,d in docs.items() if 'Transform' in d}
    tid={i:g['m_Component'][0]['component']['fileID'] for i,g in gos.items()}
    go_for={t['m_GameObject']['fileID']:i for i,t in ts.items()}
    matrices={}
    def world(i):
        if i not in matrices:
            t=ts[i];m=np.eye(4);m[:3,:3]=Rotation.from_quat([t['m_LocalRotation'][k] for k in 'xyzw']).as_matrix()@np.diag([t['m_LocalScale'][k] for k in 'xyz']);m[:3,3]=[t['m_LocalPosition'][k] for k in 'xyz']
            matrices[i]=world(t['m_Father']['fileID'])@m if t['m_Father']['fileID'] else m
        return matrices[i]
    def descendants(go):
        result={go}
        for child in ts[tid[go]]['m_Children']:result.update(descendants(ts[child['fileID']]['m_GameObject']['fileID']))
        return result
    keep=set()
    for name in ['Alcatraz Cellhouse - three tiers','Dining Hall']:
        go=next(i for i,g in gos.items() if g['m_Name']==name);keep.update(descendants(go))
    assets={}
    for p in (ROOT/'Assets').rglob('*.meta'):
        match=re.search(r'^guid: (\w+)',p.read_text(),re.M)
        if match:assets[match[1]]=Path(str(p)[:-5])
    def inside(v):
        cell=(np.abs(v[:,0])<27.5)&(v[:,1]>29.7)&(v[:,1]<42.6)&(v[:,2]>-45)&(v[:,2]<44.7)
        dining=(np.abs(v[:,0])<22.5)&(v[:,1]>29.7)&(v[:,1]<37.5)&(v[:,2]>=44.7)&(v[:,2]<67)
        return cell|dining
    crops={}
    # Batched fixtures sit outside the cellhouse hierarchy. Select their
    # semantic groups, never the legacy island terrain or other buildings.
    groups=('Cellhouse ','Cell partitions /','Cell lintels /','Cell core /',
        'Cell bars /','Cell beds /','Cell blankets /','Cell pillows /',
        'Cell shelf /','Cell plumbing /','Rear vents /','Railing /',
        'Skylight ribs /','Dining ','Overhead gallery beams /',
        'Mess hall direction','Waste station lids /')
    for i,d in docs.items():
        if 'MeshFilter' not in d:continue
        f=d['MeshFilter'];go=f['m_GameObject']['fileID']
        if go in keep:continue
        if not gos[go]['m_Name'].startswith(groups):continue
        mesh_path=assets[f['m_Mesh']['guid']]
        if mesh_path.suffix!='.asset':continue
        text=mesh_path.read_text();count=int(re.search(r'm_VertexCount: (\d+)',text)[1]);size=int(re.search(r'm_DataSize: (\d+)',text)[1]);data=bytes.fromhex(re.search(r'_typelessdata: (\w+)',text)[1]);stride=size//count
        v=np.ndarray((count,3),'<f4',buffer=data,strides=(stride,4)).copy()
        triangles=np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: (\w+)',text)[1]),dtype='<u4' if 'm_IndexFormat: 1' in text else '<u2').reshape(-1,3)
        m=world(tid[go]);vertices=v@m[:3,:3].T+m[:3,3];selected=inside(vertices[triangles].mean(1))
        if not selected.any():continue
        keep.update(descendants(go))
        if selected.all():continue
        # Preserve the source node transform and material; crop only its geometry.
        ids,indices=np.unique(triangles[selected].ravel(),return_inverse=True)
        result=Mesh();result.v=v[ids].tolist();result.n=np.ndarray((count,3),'<f4',buffer=data,offset=12,strides=(stride,4))[ids].tolist();result.uv=np.ndarray((count,2),'<f4',buffer=data,offset=40,strides=(stride,4))[ids].tolist();result.t=indices.tolist()
        old=u.ART;u.ART=BASE
        key='Interior_'+str(go);path=u.save_mesh(key,result,'Cropped');u.ART=old
        crops[i]=(f['m_Mesh']['guid'],u.guid(path));
    for i,d in docs.items():
        if 'Light' not in d:continue
        go=d['Light']['m_GameObject']['fileID']
        if inside(world(tid[go])[:3,3][None,:]).any():keep.update(descendants(go))
    # Keep only static native components. Gameplay uses the supplied world's
    # player and equipment, so no old story director or old player is copied.
    allowed={1,4,23,33,64,65,108,114}
    selected_ids=set()
    for go in keep:
        selected_ids.add(go)
        selected_ids.update(c['component']['fileID'] for c in gos[go]['m_Component'] if raw[c['component']['fileID']][0] in allowed)
    u.Node.all=[];u.Node.counter=42000000
    root=u.Node('Alcatraz enterable cellhouse',static=False)
    roots=[go for go in sorted(keep) if ts[tid[go]]['m_Father']['fileID'] not in {tid[g] for g in keep}]
    root_yaml=u.node_yaml(root,True)
    root_yaml=root_yaml.replace('  m_Children: []','  m_Children:\n'+''.join('  - {fileID: '+str(tid[g])+'}\n' for g in roots).rstrip())
    output=u.HEAD+root_yaml
    for i,(kind,b) in raw.items():
        if i not in selected_ids:continue
        if kind==1:
            b=re.sub(r'  - component: \{fileID: (\d+)\}\n',lambda m:m[0] if int(m[1]) in selected_ids else '',b)
        if kind==4:
            go=ts[i]['m_GameObject']['fileID']
            if go in roots:
                matrix=world(i);scale=np.linalg.norm(matrix[:3,:3],axis=0);rotation=Rotation.from_matrix(matrix[:3,:3]/scale).as_quat()
                b=re.sub(r'  m_Father: .*','  m_Father: {fileID: '+str(root.tid)+'}',b)
                b=re.sub(r'  m_LocalPosition: .*','  m_LocalPosition: '+u.vec(matrix[:3,3]),b)
                b=re.sub(r'  m_LocalRotation: .*','  m_LocalRotation: '+u.vec(rotation),b)
                b=re.sub(r'  m_LocalScale: .*','  m_LocalScale: '+u.vec(scale),b)
            b=re.sub(r'  - \{fileID: (\d+)\}\n',lambda m:m[0] if int(m[1]) in selected_ids else '',b)
        if kind in [33,64]:
            go=docs[i]['MeshFilter' if kind==33 else 'MeshCollider']['m_GameObject']['fileID']
            for filter_id,(old_guid,new_guid) in crops.items():
                if docs[filter_id]['MeshFilter']['m_GameObject']['fileID']==go:b=b.replace(old_guid,new_guid)
        output+=b
    path=BASE+'/Interior.prefab';u.write(path,'\n'.join(l.rstrip() for l in output.splitlines())+'\n');u.meta(path,'PrefabImporter')
    for folder in [BASE,BASE+'/Cropped']:
        u.meta(folder);p=ROOT/(folder+'.meta');s=p.read_text().replace('DefaultImporter:','folderAsset: yes\nDefaultImporter:');p.write_text(s)
    floorplan()
    for p in [ROOT/(BASE+'.meta'),*(ROOT/BASE).rglob('*')]:
        if p.is_file() and p.suffix in ['.meta','.asset','.mat']:
            p.write_text('\n'.join(l.rstrip() for l in p.read_text().splitlines())+'\n')
    result={'source':'SC_AlcatrazIsland native interior only','prefab':path,'game_objects':len(keep)+1,'mixed_meshes_cropped':len(crops),'bytes':len(output),'legacy_exterior_included':False}
    (ROOT/'Documentation/Revision11_Cellhouse.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

def floorplan():
    im=Image.new('RGB',(512,768),'#14252c');d=ImageDraw.Draw(im)
    def p(x,z):return ((x+28)/56*512,(68-z)/113*768)
    def rect(x,z,w,depth,color):
        a=p(x-w/2,z+depth/2);b=p(x+w/2,z-depth/2);d.rectangle((*a,*b),fill=color,outline='#809ba2',width=2)
    rect(0,0,53,87,'#53696d');rect(0,55.5,44,21,'#677778')
    for x in [-18,-6,6,18]:
        rect(x,-3.6,6.5,57,'#bcc0ac')
        for z in np.arange(-31,25,2.03):
            a=p(x-3.25,z);b=p(x+3.25,z);d.line((*a,*b),fill='#3a4a4d',width=1)
    for tier,z in [(2,35.8),(3,42.4)]:
        a=p(-24.5,z);b=p(24.5,z);d.line((*a,*b),fill='#dbc991',width=3)
    for x,name in [(-18,'D'),(-6,'B'),(6,'C'),(18,'A')]:d.text(p(x-1,0),name,fill='#111c21')
    d.text(p(-10,56),'DINING HALL',fill='white');d.text(p(-5,-38),'EXIT',fill='#efd49a')
    path=BASE+'/Floorplan.png';im.save(ROOT/path);u.meta(path,'TextureImporter','  textureType: 0\n  sRGBTexture: 1\n  maxTextureSize: 1024\n  mipmapEnabled: 0\n')

if __name__=='__main__':main()
