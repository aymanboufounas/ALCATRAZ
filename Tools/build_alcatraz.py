"""Original Alcatraz game environment. Deterministic Unity metres, Y-up, north +Z.

NPS landmark placement and user references guide a game adaptation, not a survey.
The original Blackstone scene is retained; its actor/mission bindings are reused.
No third-party island mesh or commercial game assets are copied.
"""
from pathlib import Path
import hashlib, json, math, re, gzip
import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial.transform import Rotation
import unity_writer as uw
from geometry import Mesh, box, cylinder, tube, ellipsoid, plane, lathe
from authoring_io import read_authoring
from world import light

ROOT = Path(__file__).resolve().parents[1]
BASE = 'Assets/Game/Alcatraz'
SCENES = ['Assets/Game/Scenes/SC_AlcatrazIsland.unity',
          'Assets/Game/Scenes/SC_AlcatrazChapter01.unity']
YARD = np.array([-48., 27.28, 22.])
LEVEL = 30.
CELL_Z = -31. + 3 * 2.03
POINTS = {
    'cellSpawn': (-4.25, 30.11, CELL_Z), 'yardSpawn': (-43,27.32,40),
    'solitarySpawn': (-17.2,30.08,CELL_Z), 'sleepPosition':(-18.1,30.05,CELL_Z-.2),
    'visitSpawn': (19,30.11,-38), 'guardIncident':(-42,27.30,54),
    'guardIsolation':(-13.3,30.04,CELL_Z), 'rivalIsolation':(-17.2,30.03,CELL_Z+4.06),
    'cellStash':(-5.04,30.57,CELL_Z-.15),
    'reflection':(-3.7,30.65,CELL_Z+.57), 'brother':(22.25,30.03,-38),
    'knife':(-41.75,27.305,42), 'phone':(-42.5,28.22,43),
}
COLLIDERS=[];CELLS=[];ROADS=[];LANDMARKS=[];BOXES={};BATCHES={};DETAIL_BOXES={}
OLD=None
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

def world_matrix(n):
    m=np.eye(4);m[:3,:3]=Rotation.from_euler('xyz',n.rot,degrees=True).as_matrix()@np.diag(n.scale);m[:3,3]=n.pos
    return world_matrix(n.parent)@m if n.parent else m

def collision(n,size,center=(0,0,0),kind='box'):
    if kind=='box':n.boxcollider(size,center)
    else:n.meshcollider(kind)
    m=world_matrix(n)
    COLLIDERS.append({'name':n.name,'id':n.id,'kind':'mesh' if kind!='box' else 'box',
       'position':(m[:3,:3]@np.array(center)+m[:3,3]).tolist(),
       'size':(np.abs(m[:3,:3])@np.array(size)).tolist(),
       'rotation':n.rot,'mesh':kind if kind!='box' else None})

def node(name,parent,pos,mesh,mat,rot=(0,0,0),scale=(1,1,1),solid=False):
    if mesh not in uw.PREVIEW['meshes'] and OLD is not None and mesh in OLD['meshes']:
        uw.PREVIEW['meshes'][mesh]=OLD['meshes'][mesh]
    n=uw.Node(name,parent,pos,rot,scale).render(mesh,mat,shadow=0 if mat=='Alc_Glass' else 1)
    if solid:collision(n,(1,1,1))
    return n

def slab(name,parent,pos,size,mat='Alc_Stone',solid=True,rot=(0,0,0)):
    key=tuple(round(float(v),5) for v in size)
    if key not in BOXES:
        mesh=box(key, min(.022,min(key)*.12))
        for i,(p,n) in enumerate(zip(mesh.v,mesh.n)):
            axis=int(np.argmax(np.abs(n)));mesh.uv[i]=[p[0],p[2]] if axis==1 else [p[2],p[1]] if axis==0 else [p[0],p[1]]
        name_key='Alc_Box_'+hashlib.md5(str(key).encode()).hexdigest()[:12]
        uw.save_mesh(name_key,mesh,'Architecture');BOXES[key]=name_key
    n=node(name,parent,pos,BOXES[key],mat,rot)
    if solid:collision(n,size)
    return n

def hidden_wall(name,parent,pos,size,rot=(0,0,0)):
    n=uw.Node(name,parent,pos,rot);collision(n,size);return n

def batched(group,mat,geometry,pos=(0,0,0),rot=(0,0,0),scale=(1,1,1)):
    key=(group,mat)
    if key not in BATCHES:BATCHES[key]=Mesh()
    BATCHES[key].merge(geometry,pos,scale,rot)

def b_box(group,mat,pos,size,bevel=.014,rot=(0,0,0)):
    # Repeated tiny fittings use 12 triangles, rather than 108 bevel triangles.
    # Large architecture and equipment retain true bevelled silhouettes.
    key=tuple(round(float(v),6) for v in size)
    if key not in DETAIL_BOXES:
        m=Mesh();half=np.array(key)/2
        for axis in range(3):
            axes=[a for a in range(3) if a!=axis]
            for s in [-1,1]:
                points=[]
                for u,v in [(-1,-1),(1,-1),(1,1),(-1,1)]:
                    p=np.zeros(3);p[axis]=s*half[axis];p[axes[0]]=u*half[axes[0]];p[axes[1]]=v*half[axes[1]];points.append(p)
                if np.cross(points[1]-points[0],points[2]-points[0])[axis]*s<0:points.reverse()
                m.quad(*points,uv=[(p[axes[0]],p[axes[1]]) for p in points])
        DETAIL_BOXES[key]=m
    batched(group,mat,DETAIL_BOXES[key],pos,rot)

def flush_batches(parent):
    for (group,mat),mesh in list(BATCHES.items()):
        key='Alc_Batch_'+group+'_'+mat
        if len(mesh.v) <= 100000:
            uw.save_mesh(key,mesh,'Details')
            node(group+' / '+mat,parent,(0,0,0),key,mat)
            continue
        # Preserve every triangle and attribute while keeping native assets small.
        triangles = np.asarray(mesh.t).reshape(-1,3)
        for first in range(0,len(triangles),8000):
            indices, remapped = np.unique(triangles[first:first+8000].reshape(-1),return_inverse=True)
            part=Mesh()
            part.v=[mesh.v[i] for i in indices]
            part.n=[mesh.n[i] for i in indices]
            part.uv=[mesh.uv[i] for i in indices]
            part.t=remapped.tolist()
            suffix=f'_Part_{first//8000+1:03d}'
            uw.save_mesh(key+suffix,part,'Details')
            node(group+' / '+mat+suffix,parent,(0,0,0),key+suffix,mat)
        old=ROOT/(BASE+'/Art/Details/'+key+'.asset')
        for obsolete in [old,Path(str(old)+'.meta')]:
            if obsolete.exists():obsolete.unlink()
    BATCHES.clear()

def remove_superseded_batches():
    """Remove unused whole batches after all scene and detail passes finish."""
    details=ROOT/(BASE+'/Art/Details')
    scenes=[(ROOT/path).read_text() for path in SCENES]
    whole_names={name.rsplit('_Part_',1)[0] for name in uw.PREVIEW['meshes']
                 if re.search(r'_Part_\d{3}$',name)}
    for name in whole_names:
        if name in uw.PREVIEW['meshes']:
            continue
        old=details/(name+'.asset')
        metadata=Path(str(old)+'.meta')
        if metadata.exists():
            match=re.search(r'^guid: (\w+)$',metadata.read_text(),re.M)
            if match and any(match[1] in scene for scene in scenes):
                raise RuntimeError('Superseded batch is still referenced: '+name)
        for obsolete in (old,metadata):
            if obsolete.exists():obsolete.unlink()

def sign(parent,name,pos,text,size=(2.5,.6),yaw=0):
    key='Alc_Sign_'+re.sub(r'[^a-zA-Z0-9]','_',name)
    path=BASE+'/Art/Textures/'+key+'.png';p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True)
    image=Image.new('RGB',(1024,256),(33,44,45));d=ImageDraw.Draw(image)
    d.rectangle((9,9,1014,246),outline=(176,165,128),width=4)
    f=ImageFont.truetype(FONT,50 if len(text)<36 else 38)
    d.multiline_text((512,128),text,font=f,fill=(224,219,198),anchor='mm',align='center',spacing=9)
    image.save(p);uw.meta(path,'TextureImporter','  serializedVersion: 13\n  mipmaps:\n    enableMipMap: 1\n    sRGBTexture: 1\n  textureType: 0\n  maxTextureSize: 1024\n  textureSettings:\n    filterMode: 1\n    aniso: 2\n    wrapU: 1\n    wrapV: 1\n')
    uw.material(key,[1,1,1,1],.90,texture=path)
    n=node(name,parent,pos,'Alc_SignPlane',key,(0,yaw,0),(size[0],size[1],1));return n

def materials():
    global OLD
    raw=ROOT/'Documentation/BlackstoneAuthoring.json'
    OLD=read_authoring(raw)
    for name,mat in OLD['materials'].items():
        uw.MATERIALS[name]='Assets/Game/Art/Materials/'+name+'.mat'
        uw.PREVIEW['materials'][name]=mat
    native_meshes={p.stem:str(p.relative_to(ROOT)) for p in (ROOT/'Assets/Game/Art').rglob('*.asset')}
    for key in OLD['meshes']:
        if key in native_meshes:uw.MESHES[key]=(native_meshes[key],None)
    def scanned(name,asset,tint,rough=.8,density=.45):
        base='Assets/Game/Textures/PBR_'+asset
        return uw.material(name,list(tint),rough,texture=base+'_Base.png',normal=base+'_Normal.png',
           surface=base+'_Surface.png',occlusion=base+'_Surface.png',tiling=density)
    scanned('Alc_Stone','brushed_concrete',(.98,.95,.85,1))
    scanned('Alc_Painted','brushed_concrete',(.68,.72,.63,1))
    scanned('Alc_Rock','seaside_rock',(.96,.94,.84,1),density=.36)
    scanned('Alc_Earth','forest_floor',(.70,.69,.56,1),density=.32)
    scanned('Alc_Floor','concrete_floor_worn_001',(.85,.88,.85,1),density=.37)
    scanned('Alc_Brick','brick_wall_001',(.70,.58,.48,1),density=.45)
    scanned('Alc_Wood','wood_planks',(.57,.48,.37,1),density=.8)
    uw.material('Alc_DarkSteel',[.13,.17,.17,1],.58,.7)
    uw.material('Alc_Iron',[.35,.40,.36,1],.54,.7)
    uw.material('Alc_Rust',[.35,.22,.12,1],.88,.34)
    uw.material('Alc_Roof',[.46,.49,.48,1],.88,.1,texture='Assets/Game/Textures/PBR_brushed_concrete_Base.png',tiling=.33)
    uw.material('Alc_Tile',[.39,.20,.13,1],.82,texture='Assets/Game/Textures/PBR_brick_wall_001_Base.png',tiling=.7)
    uw.material('Alc_Glass',[.10,.20,.22,.72],.18,.15,transparent=True)
    uw.material('Alc_Sea',[.045,.14,.17,1],.14,.25,shader_guid=uw.guid('Assets/Game/Shaders/CoastalWater.shader'))
    uw.material('Alc_Foam',[.79,.86,.84,.60],.72,transparent=True)
    uw.material('Alc_Grass',[.40,.42,.26,1],.97)
    uw.material('Alc_Agave',[.31,.42,.30,1],.88)
    uw.material('Alc_Blanket',[.46,.51,.45,1],.95,texture='Assets/_DesertShift/Art/Textures/Cloth_Base.png',tiling=2)
    uw.material('Alc_Light',[.95,.86,.65,1],.3,emission=[2.4,1.9,.9,1])
    uw.material('Alc_White',[.87,.86,.77,1],.85)
    uw.material('Alc_Asphalt',[.64,.66,.61,1],.95,texture='Assets/Game/Textures/PBR_concrete_floor_worn_001_Base.png',tiling=.5)
    uw.save_mesh('Alc_Cylinder',cylinder(.5,1,20),'Shared')
    uw.save_mesh('Alc_Plane',plane(1,1),'Shared')
    uw.save_mesh('Alc_Rock_0',ellipsoid((1,1,1),9,16,21),'Coast')
    uw.save_mesh('Alc_Rock_1',ellipsoid((1,1,1),9,16,22),'Coast')
    uw.save_mesh('Alc_Rock_2',ellipsoid((1,1,1),9,16,23),'Coast')
    m=Mesh();m.quad((-.5,-.5,0),(.5,-.5,0),(.5,.5,0),(-.5,.5,0),uv=[(1,0),(0,0),(0,1),(1,1)])
    uw.save_mesh('Alc_SignPlane',m,'Shared')

# Irregular long island, tapered southern point, broad northern industrial tip.
# The footprint is intentionally authored for game paths, rather than surveyed.
OUTLINE=np.array([[-13,-180],[19,-176],[38,-166],[56,-149],[71,-120],[82,-83],
 [88,-48],[91,-7],[88,27],[83,62],[86,93],[75,121],[58,143],[34,163],
 [6,172],[-27,174],[-46,162],[-59,139],[-66,108],[-73,77],[-77,42],
 [-76,4],[-70,-28],[-68,-59],[-67,-94],[-56,-124],[-39,-154]])

PATH_CUTS=[
 ([(85,5.01,-117),(90,5.01,-60),(85,5.01,-12),(82,5.01,31),(80,7.31,70),(80,7.31,130),(69,7.31,140),(44,9.31,144)],5.8),
 ([(84,5.03,-117),(65,8.5,-133),(40,13,-124),(40,16.2,-90),(58,21,-86),(45,25.2,-91),(18,30.03,-87),(-9,30.03,-87),(-12,30.03,-60),(-4,30.03,-59),(0,30.03,-43)],5.5),
 ([(30,15.86,-122),(-27,15.86,-122),(-58,18.4,-99),(-65,22.8,-61),(-66,26.2,-15),(-74,27.42,18),(-74,27.42,48),(-72,27.42,76),(-66,27.42,91),(-58,27.42,97),(-60,21,116),(-58,15.4,131),(-55,9.4,145.5)],5),
 ([(-57,9.4,145.5),(-40,9.4,145.5),(-13,9.4,145.5),(18,9.4,145.5),(44,9.4,144)],3),
 ([(29,30.04,-57),(30,30.04,-32),(30,30.04,0),(30,30.04,47),(24,30.04,47)],3.5),
 ([(-12,30.03,-80),(-8,30.03,-80),(-8,30.03,-60),(-2,30.03,-44)],3),
 ([(-30,15.90,-144),(-30,15.90,-152),(-40,15.90,-157),(-47,13.5,-152),(-57,10.2,-133),(-63,8.5,-109)],1.8),
 ([(0,30.03,-43),(0,30.03,-60),(12,30.03,-60),(12,30.03,-56)],3),
 ([(-56,9.4,97),(-38,9.4,97),(-38,9.4,105)],4),
 ([(18,30.03,-87),(26,30.03,-87),(26,30.03,-77)],3),
 ([(-8,30.03,-80),(3,30.03,-81),(3,30.03,-76)],3),
]

def terrain():
    from matplotlib.path import Path as Polygon
    from scipy.spatial import Delaunay
    inside=Polygon(OUTLINE)
    samples=[p for x in np.arange(-80,94,3.5) for z in np.arange(-181,175,3.5)
             if inside.contains_point(p:=(x,z))]
    edge=[]
    for a,b in zip(OUTLINE,np.roll(OUTLINE,-1,axis=0)):
        for t in np.linspace(0,1,int(np.linalg.norm(b-a)/2)+1,endpoint=False):edge.append(a+(b-a)*t)
    positions=np.array(samples+edge)
    def height(x,z):
        # Bedrock promontory supporting the real prison summit.
        summit=30.2*np.exp(-((x+4)/64)**4-((z+4)/111)**4)
        north=9.7*np.exp(-((x+13)/79)**6-((z-127)/52)**4)
        south=15.6*np.exp(-((x+5)/60)**6-((z+116)/42)**4)
        value=max(summit,north,south)+.9*math.sin(x*.13)*math.cos(z*.08)
        if -28<x<28 and -45<z<71:value=29.84
        if -72<x<-27 and 21<z<72:value=27.10
        if -58<x<35 and -150<z<-94:value=15.55
        if 52<x<92 and -120<z<36:value=4.75
        if -67<x<23 and 109<z<167:value=9.15
        if 40<x<81 and 64<z<138:value=7.15
        for path,width in PATH_CUTS:
            for a,b in zip(path,path[1:]):
                a=np.array(a);b=np.array(b);p=np.array([x,z]);v=b[[0,2]]-a[[0,2]]
                t=np.clip(np.dot(p-a[[0,2]],v)/np.dot(v,v),0,1)
                distance=np.linalg.norm(p-(a[[0,2]]+v*t))
                if distance<width/2+2.0:
                    surface=(a+(b-a)*t)[1]-.15
                    strength=np.clip((width/2+2.0-distance)/2,0,1)
                    value=min(value,value*(1-strength)+surface*strength)
        return value
    heights=np.array([height(x,z) for x,z in positions])
    # Shore drops outside a retaining ring. Coast face has a real mesh collider.
    for i,p in enumerate(positions):
        distance=min(np.linalg.norm(p-(a+np.clip(np.dot(p-a,b-a)/np.dot(b-a,b-a),0,1)*(b-a)))
                     for a,b in zip(OUTLINE,np.roll(OUTLINE,-1,axis=0)))
        heights[i]*=min(1,.25+distance/9)
    mesh=Mesh();steep=Mesh();tri=Delaunay(positions)
    for ids in tri.simplices:
        pts=positions[ids]
        if not inside.contains_point(pts.mean(axis=0)):continue
        p=[(x,heights[i],z) for i,(x,z) in zip(ids,pts)]
        if np.cross(np.array(p[1])-p[0],np.array(p[2])-p[0])[1]<0:p=[p[0],p[2],p[1]]
        normal=np.cross(np.array(p[1])-p[0],np.array(p[2])-p[0]);normal/=np.linalg.norm(normal)
        if normal[1]<.68:
            axis=int(np.argmax(np.abs(normal)))
            axes=[k for k in range(3) if k!=axis]
            steep.tri(*p,uvs=[[v[k] for k in axes] for v in p])
        else:mesh.tri(*p,uvs=[(v[0],v[2]) for v in p])
    shore=Mesh();foam=Mesh()
    for a,b in zip(edge,edge[1:]+edge[:1]):
        ay=height(*a)*.25;by=height(*b)*.25
        shore.quad((a[0],ay,a[1]),(b[0],by,b[1]),(b[0],-5,b[1]),(a[0],-5,a[1]),
          uv=[(a[0]+a[1],ay),(b[0]+b[1],by),(b[0]+b[1],-5),(a[0]+a[1],-5)])
        ca=np.array(a);cb=np.array(b);outa=ca/np.linalg.norm(ca);outb=cb/np.linalg.norm(cb)
        foam.quad((ca[0],.08,ca[1]),(cb[0],.08,cb[1]),(cb[0]+outb[0]*2.8,.08,cb[1]+outb[1]*2.8),
                  (ca[0]+outa[0]*2.8,.08,ca[1]+outa[1]*2.8))
    shore.merge(steep)
    return mesh,shore,foam,height

def island(parent):
    ground,cliffs,foam,height=terrain()
    for name,mesh,mat in [('Alc_Terrain',ground,'Alc_Earth'),('Alc_Cliffs',cliffs,'Alc_Rock'),('Alc_ShoreFoam',foam,'Alc_Foam')]:
        uw.save_mesh(name,mesh,'Coast');n=node(name,parent,(0,0,0),name,mat)
        if name!='Alc_ShoreFoam':collision(n,(190,40,360),kind=name)
    node('San Francisco Bay',parent,(0,0,0),'Alc_Plane','Alc_Sea',scale=(2200,1,2200))
    rng=np.random.default_rng(606)
    from alcatraz_concept_pass import trail_distance
    for i in range(136):
        a=OUTLINE[i%len(OUTLINE)];b=OUTLINE[(i+1)%len(OUTLINE)];p=a+(b-a)*rng.uniform(0,1)
        if trail_distance(*p)<11:continue
        n=node('Coastal rock outcrop',parent,(p[0],height(*p)*.13,p[1]),'Alc_Rock_'+str(i%3),'Alc_Rock',
           rot=(rng.uniform(-20,20),rng.uniform(0,360),rng.uniform(-18,18)),scale=(rng.uniform(4,11),rng.uniform(5,14),rng.uniform(4,10)))
    vegetation=Mesh();agave=Mesh()
    from matplotlib.path import Path as Polygon
    outline=Polygon(OUTLINE)
    for i in range(1350):
        x=rng.uniform(-75,88);z=rng.uniform(-174,169)
        if not outline.contains_point((x,z)) or (-31<x<30 and -46<z<75) or (-73<x<-26 and 20<z<75) or (-58<x<35 and -152<z<-94) or (50<x and -120<z<145) or (-67<x<22 and z>108):continue
        y=height(x,z)
        for j in range(3):
            a=rng.uniform(0,math.tau);w=np.array([math.cos(a)*.04,0,math.sin(a)*.04]);p=np.array([x,y+.06,z]);tip=p+[.06,rng.uniform(.15,.55),-.07]
            vegetation.tri(p-w,tip,p+w);vegetation.tri(p+w,tip,p-w)
    for x,z in [(-57,-141),(-49,-146),(-45,-151),(-34,-157),(-39,-143),(-58,-135),(-48,-133),(50,-59),(43,-72),(40,-84),(-32,86),(-36,79)]:
        y=height(x,z)
        for j in range(14):
            a=j*math.tau/14;centre=np.array([x,y+.10,z]);dir=np.array([math.cos(a),0,math.sin(a)]);w=np.array([-math.sin(a),0,math.cos(a)])*.12
            tip=centre+dir*rng.uniform(.95,1.35)+[0,rng.uniform(.30,.85),0];middle=centre+dir*.42+[0,.53,0]
            agave.quad(centre-w,middle-w*.6,tip,middle+w*.6);agave.quad(middle+w*.6,tip,middle-w*.6,centre-w)
    for key,mesh,mat in [('Alc_Groundcover',vegetation,'Alc_Grass'),('Alc_AgaveBeds',agave,'Alc_Agave')]:
        uw.save_mesh(key,mesh,'Vegetation');node(key,parent,(0,0,0),key,mat)
    for x,z in [(35,-67),(35,-82),(18,-88),(30,-88),(-29,-62),(-37,-83),(-28,79),(-27,91),(43,42),(46,36),(-61,-107),(-55,-120),(41,-145),(25,-155),(24,84),(28,76),(49,151),(62,148)]:
        y=height(x,z);s=.55+rng.uniform(0,.20);yaw=rng.uniform(0,360)
        for part,mat in [('Trunk','M_Bark'),('Leaves','M_OliveLeaf')]:
            node('Island garden olive '+part,parent,(x,y,z),'olive'+part,mat,rot=(0,yaw,0),scale=(s,s,s))
    return height

def landmark(name,pos,size):LANDMARKS.append({'name':name,'position':list(pos),'size':list(size)})

def rail(parent,name,a,b,height=1.12):
    a=np.array(a,float);b=np.array(b,float)
    for t in np.linspace(0,1,max(2,int(np.linalg.norm(b-a)/1.7)+1)):
        p=a+(b-a)*t
        b_box('Railing','Alc_Iron',p+[0,height/2,0],(.045,height,.045))
    batched('Railing','Alc_Iron',tube([a+[0,height,0],b+[0,height,0]],.027,7))
    batched('Railing','Alc_Iron',tube([a+[0,.40,0],b+[0,.40,0]],.022,7))
    d=b-a;yaw=math.degrees(math.atan2(d[0],d[2]));count=max(1,math.ceil(abs(d[1])/.35))
    for i in range(count):
        aa=a+d*i/count;bb=a+d*(i+1)/count;midpoint=(aa+bb)/2
        hidden_wall(name+' safety collider',parent,midpoint+[0,height/2,0],
          (.09,height+abs(bb[1]-aa[1]),np.linalg.norm((bb-aa)[[0,2]])),(0,yaw,0))

def road(parent,name,points,width=5,mat='Alc_Asphalt',guards=False):
    roadmesh=Mesh()
    points=np.array(points,float);offsets=[]
    directions=np.diff(points,axis=0);directions[:,1]=0;directions/=np.linalg.norm(directions,axis=1)[:,None]
    normals=np.c_[-directions[:,2],np.zeros(len(directions)),directions[:,0]]
    for i in range(len(points)):
        side=normals[0] if i==0 else normals[-1] if i==len(points)-1 else normals[i-1]+normals[i]
        side=side/np.linalg.norm(side);denom=max(.56,np.dot(side,normals[min(i,len(normals)-1)]))
        offsets.append(side*width/(2*denom))
    for i,(a,b) in enumerate(zip(points,points[1:])):
        # Centreline vertices preserve the intended slope through mitered turns.
        for p in [[a-offsets[i],a,b,b-offsets[i+1]],[a,a+offsets[i],b+offsets[i+1],b]]:
            if np.cross(p[1]-p[0],p[2]-p[0])[1]<0:p.reverse()
            roadmesh.quad(*p,uv=[(v[0]*.12,v[2]*.12) for v in p])
        if guards:
            for s in [-1,1]:rail(parent,name,a+offsets[i]*s,b+offsets[i+1]*s)
    key='Alc_Road_'+re.sub(r'\W','_',name);uw.save_mesh(key,roadmesh,'Paths');n=node(name,parent,(0,0,0),key,mat)
    collision(n,(width,40,360),kind=key)
    # Shared miter vertices make continuous sloped turns, without raised flat pads.
    ROADS.append({'name':name,'points':points.tolist(),'width':width})

def steps(parent,name,start,end,width,steps_count):
    start=np.array(start,float);end=np.array(end,float);dy=end[1]-start[1];d=end-start;horizontal=np.linalg.norm(d[[0,2]]);yaw=math.degrees(math.atan2(d[0],d[2]))
    tread=horizontal/steps_count
    for i in range(steps_count):
        t=(i+.5)/steps_count;p=start+d*t;rise=dy*(i+1)/steps_count
        slab(name+' '+str(i+1).zfill(2),parent,(p[0],start[1]+rise/2-.01,p[2]),(width,rise+.02,tread+.012),'Alc_Floor',rot=(0,yaw,0))
    side=np.array([math.cos(math.radians(yaw)),0,-math.sin(math.radians(yaw))])*width*.53
    for s in [-1,1]:rail(parent,name,start+side*s,end+side*s)
    ROADS.append({'name':name,'points':[start.tolist(),end.tolist()],'width':width,'steps':steps_count,'rise':dy/steps_count})

def cell(parent,block,side,index,tier,cx,spacing=2.03,depth=2.8):
    z=-31+index*spacing;y=LEVEL+tier*2.75;front=cx+side*3.15;back=cx+side*.26
    number=tier*28+index+1;main=block=='B' and side==1 and tier==0 and index==3
    label=f'{block}-{number:02d}'+('E' if side==1 else 'W')
    CELLS.append({'block':block,'number':number,'tier':tier+1,'front':[front,y,z],'main':main,'label':label})
    centre=(front+back)/2
    # Cells use visible concrete partitions with collision; all occupied rows are enclosed.
    b_box('Cell partitions','Alc_Painted',(centre,y+1.30,z-spacing/2),(depth+.2,2.6,.115))
    hidden_wall('Cell partition '+label,parent,(centre,y+1.30,z-spacing/2),(depth+.2,2.6,.115))
    b_box('Cell lintels','Alc_Stone',(front,y+2.5,z),(.14,.20,spacing))
    b_box('Cell core','Alc_Painted',(back,y+1.3,z),(.12,2.6,spacing))
    hidden_wall('Cell back '+label,parent,(back,y+1.3,z),(.12,2.6,spacing))
    # B-04 has the mission's operable leaf; two cells per gallery stand open for exploration.
    open_cell=main or (index in (7,19) and tier==0)
    barzs=np.linspace(z-spacing*.47,z+spacing*.47,10)
    for bz in barzs:
        if open_cell and abs(bz-z)<.62:continue
        batched('Cell bars','Alc_Iron',cylinder(.013,2.4,6),(front,y+1.2,bz))
    for by in [.12,1.20,2.36]:
        if open_cell:
            for s in [-1,1]:b_box('Cell bars','Alc_Iron',(front,y+by,z+s*.81),(.05,.05,.42))
        else:b_box('Cell bars','Alc_Iron',(front,y+by,z),(.05,.05,spacing-.10))
    if open_cell:
        for s in [-1,1]:hidden_wall('Open cell frame '+label,parent,(front,y+1.2,z+s*.83),(.10,2.4,.40))
    else:hidden_wall('Locked cell front '+label,parent,(front,y+1.2,z),(.10,2.4,spacing-.10))
    bedx=back+side*.72
    b_box('Cell beds','Alc_Iron',(bedx,y+.34,z),(.77,.10,1.84))
    b_box('Cell blankets','Alc_Blanket',(bedx,y+.47,z),(.74,.17,1.80))
    b_box('Cell pillows','Alc_White',(bedx,y+.58,z+.61),(.61,.09,.42))
    for dx in [-.29,.29]:
        for dz in [-.76,.76]:b_box('Cell beds','Alc_Iron',(bedx+dx,y+.17,z+dz),(.036,.34,.036))
    hidden_wall('Bed '+label,parent,(bedx,y+.4,z),(.77,.52,1.84))
    # Plumbing, writing shelf and vent are original mesh details, batched by material.
    b_box('Cell shelf','Alc_Wood',(front-side*.47,y+.77,z+.65),(.53,.065,.41))
    batched('Cell plumbing','M_Ceramic',ellipsoid((.43,.28,.44),5,8),(back+side*.40,y+.33,z-.62))
    b_box('Cell plumbing','M_Ceramic',(back+side*.16,y+.65,z-.65),(.23,.36,.25))
    batched('Cell plumbing','M_Ceramic',ellipsoid((.34,.12,.33),4,8),(back+side*.24,y+.97,z+.65))
    b_box('Rear vents','Alc_DarkSteel',(back+side*.08,y+1.72,z),(.022,.24,.28))

def windows(parent,group,cx,cz,w,d,h,y,levels=2):
    # Wall envelope stays separate from recessed frames; new cellhouse uses real openings.
    for side in [-1,1]:
        for z in np.arange(cz-d/2+3,cz+d/2-1,4.8):
            for level in range(levels):
                sy=y+2.1+level*3.8
                b_box(group+' window frames','Alc_Stone',(cx+side*(w/2+.05),sy,z),(.18,2.05,1.33))
                b_box(group+' windows','Alc_Glass',(cx+side*(w/2+.155),sy,z),(.023,1.77,1.09))
                for yy in [-.55,0,.55]:b_box(group+' window grilles','Alc_DarkSteel',(cx+side*(w/2+.18),sy+yy,z),(.025,.033,1.12))
                b_box(group+' window grilles','Alc_DarkSteel',(cx+side*(w/2+.18),sy,z),(.025,1.8,.034))

def cellhouse(parent,lights):
    root=uw.Node('Alcatraz Cellhouse - three tiers',parent)
    landmark('Cellhouse',(0,LEVEL,1),(55,12,93))
    slab('Cellhouse main floor',root,(0,LEVEL-.075,0),(53,.15,87),'Alc_Floor')
    slab('Citadel stone retaining base',root,(.60,23,-.8),(53.8,13.6,90),'Alc_Rock')
    for z,d in [(-7.45,76.7),(39.65,9.1)]:
        slab('Citadel west retaining wall',root,(-26.9,23,z),(1.2,13.6,d),'Alc_Rock')
    # The retaining base reaches only to 29.8; it does not seal ground rooms.
    # Walls include functional west yard and south sally-port openings.
    for side in [-1,1]:
        for z in np.arange(-40,42,4):
            if side<0 and 29<z<37:continue
            slab('Cellhouse pilaster',root,(side*26.5,LEVEL+5.2,float(z)),(.45,10.4,.38),'Alc_Stone')
            for yc,height in [(1.02,2.04),(4.37,.48),(7.9,.55),(10.45,.65)]:
                slab('Cellhouse facade band',root,(side*26.5,LEVEL+yc,float(z)+2),(.36,height,3.64),'Alc_Stone')
            for yl in [3.06,6.0,9.1]:
                b_box('Cellhouse windows','Alc_Glass',(side*26.55,LEVEL+yl,float(z)+2),(.10,1.8,2.9))
                for zz in [.55,1.25,1.95,2.65,3.35]:
                    b_box('Cellhouse window grilles','Alc_DarkSteel',(side*26.59,LEVEL+yl,float(z)+zz),(.07,1.85,.033))
                for yy in [-.46,.46]:b_box('Cellhouse window grilles','Alc_DarkSteel',(side*26.59,LEVEL+yl+yy,float(z)+2),(.07,.035,3.0))
                # Window panes obstruct the player without opaque placeholder wall slabs.
                hidden_wall('Cellhouse sealed window',root,(side*26.5,LEVEL+yl,float(z)+2),(.14,1.85,3.05))
        slab('Cellhouse roof cornice',root,(side*26.7,LEVEL+11.0,1),(.62,.30,88),'Alc_Stone')
    # South entrance has a real 3.2 m opening to the security road.
    for cx,w in [(-14.05,24.9),(14.05,24.9)]:slab('Cellhouse south facade',root,(cx,LEVEL+5.2,-43.5),(w,10.4,.40),'Alc_Stone')
    slab('Cellhouse south entry arch',root,(0,LEVEL+7.1,-43.5),(3.2,6.2,.40),'Alc_Stone')
    # North end opens into the mess hall.
    for cx,w in [(-14.4,24.2),(14.4,24.2)]:slab('Cellhouse north cross wall',root,(cx,LEVEL+5.2,43.5),(w,10.4,.35),'Alc_Stone')
    slab('Cellhouse north portal lintel',root,(0,LEVEL+7.2,43.5),(4.6,6,.35),'Alc_Stone')
    # B/C contain 336 cells in 4 rows x 28 cells x 3 tiers. A/D use abbreviated rows.
    for block,cx in [('B',-6),('C',6)]:
        for tier in range(3):
            for side in [-1,1]:
                for i in range(28):cell(root,block,side,i,tier,cx)
                if tier>0:
                    x=cx+side*4.04;y=LEVEL+tier*2.75
                    slab('Tier '+str(tier+1)+' '+block+' gallery',root,(x,y-.075,-3.6),(1.77,.15,57),'Alc_Floor')
                    rail(root,'Gallery edge',(cx+side*4.99,y,-32),(cx+side*4.99,y,24.8))
            slab('Tier '+str(tier+1)+' '+block+' cell deck',root,(cx,LEVEL+tier*2.75-.085,-3.6),(6.5,.17,57),'Alc_Floor')
            slab(block+' north row end wall',root,(cx,LEVEL+tier*2.75+1.3,24.825),(6.5,2.6,.12),'Alc_Painted')
    for block,cx in [('A',18),('D',-18)]:
        for tier in range(3):
            for side in [-1,1]:
                for i in range(16):
                    # D ground reserved for functional solitary cells with wider chambers.
                    if block=='D' and tier==0 and i<8:continue
                    cell(root,block,side,i,tier,cx,spacing=3.5)
                if tier>0:
                    y=LEVEL+tier*2.75
                    slab(block+' upper gallery',root,(cx+side*4.04,y-.075,-3.75),(1.77,.15,57),'Alc_Floor')
                    rail(root,block+' gallery rail',(cx+side*4.99,y,-32),(cx+side*4.99,y,24.8))
            slab(block+' cell deck',root,(cx,LEVEL+tier*2.75-.085,-3.75),(6.5,.17,57),'Alc_Floor')
            slab(block+' north row end wall',root,(cx,LEVEL+tier*2.75+1.3,23.25),(6.5,2.6,.12),'Alc_Painted')
    # End bridges and gallery stairs permit all three tiers without teleporting.
    for tier in [1,2]:
        y=LEVEL+tier*2.75;z=35.8 if tier==1 else 42.4
        slab('Tier '+str(tier+1)+' cross bridge',root,(0,y-.075,z),(49,.15,2.6 if tier==1 else 2.4),'Alc_Floor')
        for sign_ in [-1,1]:
            edges=[-24.5,-23.10,-20.98,-15.02,-12.90,-11.10,-8.98,-3.02,3.02,8.98,11.10,12.90,15.02,20.98,23.10,24.5]
            for a,b in zip(edges[::2],edges[1::2]):rail(root,'Bridge rail',(a,y,z+sign_*1.20),(b,y,z+sign_*1.20))
    steps(root,'First gallery stair',(0,LEVEL,29.1),(0,LEVEL+2.75,34.5),1.75,17)
    steps(root,'Second gallery stair',(0,LEVEL+2.75,35.8),(0,LEVEL+5.5,41.2),1.75,17)
    # Far-end walkways join row galleries to bridge ends.
    for tier in [1,2]:
        for x in [-22.04,-13.96,-10.04,-1.96,1.96,10.04,13.96,22.04]:
            end=35.8 if tier==1 else 42.4;start=24.6
            slab('Gallery end connector',root,(x,LEVEL+tier*2.75-.075,(start+end)/2),(1.77,.15,end-start),'Alc_Floor')
    # Roof bays and raised skylights give the exterior its recognisable long cellhouse profile.
    for x in [-19,-6,6,19]:
        # Roof strips leave true apertures below the glazed roof lanterns.
        # Revision 06 placed an opaque slab below every skylight.
        for side in [-1,1]:
            slab('Cellhouse roof side strip',root,(x+side*3.875,LEVEL+10.8,1),(4.25,.20,87),'Alc_Roof')
        for start,end in [(-42.5,-29.7),(-22.3,-11.7),(-4.3,6.3),(13.7,24.3),(31.7,44.5)]:
            slab('Cellhouse roof between skylights',root,(x,LEVEL+10.8,(start+end)/2),(3.5,.20,end-start),'Alc_Roof')
        for z in [-26,-8,10,28]:
            for side in [-1,1]:
                slab('Skylight open curb side',root,(x+side*1.82,LEVEL+11.1,z),(.14,.55,7.68),'Alc_Stone',False)
                slab('Skylight open curb end',root,(x,LEVEL+11.1,z+side*3.77),(3.5,.55,.14),'Alc_Stone',False)
            for s in [-1,1]:
                slab('Skylight sloped glass',root,(x+s*.90,LEVEL+11.65,z),(1.95,.06,7.3),'Alc_Glass',False,rot=(0,0,-s*23))
                for dz in np.arange(-3.5,3.6,1.1):b_box('Skylight ribs','Alc_DarkSteel',(x+s*.9,LEVEL+11.73,z+float(dz)),(1.95,.04,.04),rot=(0,0,-s*23))
            b_box('Skylight ribs','Alc_DarkSteel',(x,LEVEL+12.07,z),(.075,.06,7.4))
    slab('Cellhouse north roof parapet',root,(0,LEVEL+11.07,44),(54,.55,.40),'Alc_Stone')
    slab('Cellhouse south roof parapet',root,(0,LEVEL+11.07,-44),(54,.55,.40),'Alc_Stone')
    for x,z in [(-26,-43),(26,-43),(-26,43),(26,43)]:
        slab('Cellhouse corner tower',root,(x,LEVEL+5.8,z),(2.0,11.6,2),'Alc_Stone')
        slab('Corner tower coping',root,(x,LEVEL+11.8,z),(2.6,.35,2.6),'Alc_Stone')
    sign(root,'Alcatraz cellhouse identity',(0,LEVEL+5.6,-43.75),'UNITED STATES PENITENTIARY\nALCATRAZ',(10,1.15),180)
    sign(root,'Broadway gallery',(0,LEVEL+2.25,28.5),'BROADWAY  /  B & C BLOCK',(4.5,.54),180)
    sign(root,'D block direction',(-12.7,LEVEL+2.2,30),'D BLOCK  /  ISOLATION',(3.4,.54),180)
    for x in [-11,0,11]:
        for z in [-26,-10,6,23,37]:
            slab('Cellhouse suspended fixture',root,(x,LEVEL+9.2,z),(.26,.09,1.8),'Alc_DarkSteel',False)
            slab('Cellhouse diffuser',root,(x,LEVEL+9.14,z),(.20,.055,1.64),'Alc_Light',False)
            light(lights,'Cellhouse soft lamp',(x,LEVEL+7.5,z),3.5,12,(.95,.95,.88))
    for i in range(7):
        z=CELL_Z+i*4.06
        slab('D block isolation partition',root,(-17.65,LEVEL+1.45,z-2.03),(6.5,2.9,.15),'Alc_Stone')
        slab('D block isolation back',root,(-20.85,LEVEL+1.45,z),(.20,2.9,4.06),'Alc_Stone')
        for dz in [-1.43,1.43]:slab('D block isolation front',root,(-14.8,LEVEL+1.45,z+dz),(.16,2.9,1.20),'Alc_Painted')
        slab('D block doorway lintel',root,(-14.8,LEVEL+2.7,z),(.18,.40,1.66),'Alc_Stone')
        if i>0:slab('D block locked isolation door',root,(-14.8,LEVEL+1.22,z),(.12,2.44,1.46),'Alc_DarkSteel')
        slab('Isolation cot frame',root,(-18.1,LEVEL+.35,z-.2),(.93,.12,2.03),'Alc_Iron',False)
        slab('Isolation cot mattress',root,(-18.1,LEVEL+.49,z-.2),(.90,.16,1.97),'Alc_Blanket')
        slab('Isolation cell ceiling',root,(-17.8,LEVEL+2.9,z),(6,.15,4.06),'Alc_Stone')
        sign(root,'D isolation '+str(i+1),(-14.67,LEVEL+2.40,z),'D-'+str(i+1).zfill(2),(.54,.22),90)
    # Visitation is inside the south administration zone, separated by glass.
    for z in [-34.7,-41.6]:slab('Visitation partition',root,(20,LEVEL+1.6,z),(11,3.2,.15),'Alc_Stone')
    slab('Visitation back',root,(25.5,LEVEL+1.6,-38.1),(.16,3.2,7),'Alc_Painted')
    slab('Visitation counter',root,(20.7,LEVEL+1.0,-38),(.5,.12,5.5),'Alc_Wood')
    slab('Visitation glass partition',root,(20.7,LEVEL+2.0,-38),(.06,1.90,5.5),'Alc_Glass')
    for z in [-36.5,-38,-39.5]:
        slab('Visitor booth divider',root,(20.7,LEVEL+1.6,z),(.90,1.35,.04),'Alc_Iron',False)
        for x in [19.4,22.0]:
            slab('Visitation seat',root,(x,LEVEL+.46,z),(.50,.10,.5),'Alc_Wood')
            slab('Visitation seat support',root,(x,LEVEL+.22,z),(.07,.44,.35),'Alc_Iron',False)
        slab('Visitation receiver',root,(20.32,LEVEL+1.1,z),(.10,.065,.25),'Alc_DarkSteel',False)
    sign(root,'Visitation rules',(25.35,LEVEL+2.2,-38),'VISITATION\nNO PHYSICAL CONTACT',(2.6,.8),-90)
    light(lights,'Visitation task lamp',(19.6,LEVEL+2.85,-38),4,7,(.89,.94,.96))
    return root

def hall(parent,lights,name,pos,size,roof=5.5,mat='Alc_Stone',entry='south'):
    x,y,z=pos;w,d=size;g=uw.Node(name,parent);landmark(name,pos,(w,roof,d))
    slab(name+' floor',g,(x,y-.075,z),(w,.15,d),'Alc_Floor')
    slab(name+' north wall',g,(x,y+roof/2,z+d/2),(w,roof,.20),mat)
    for side in [-1,1]:slab(name+' side wall',g,(x+side*w/2,y+roof/2,z),(.20,roof,d),mat)
    for side in [-1,1]:slab(name+' entrance wall',g,(x+side*(w/4+1),y+roof/2,z-d/2),(w/2-2,roof,.20),mat)
    slab(name+' entry lintel',g,(x,y+(roof+2.7)/2,z-d/2),(4,roof-2.7,.20),mat)
    slab(name+' roof',g,(x,y+roof,z),(w+.7,.20,d+.7),'Alc_Roof')
    windows(g,name,x,z,w,d,roof,y,1 if roof<7 else 2)
    sign(g,name+' sign',(x,y+3.6,z-d/2-.16),name.upper(),(min(7,w*.65),.75),180)
    light(lights,name+' lamp',(x,y+roof-.45,z),4,14,(.95,.91,.80))
    return g

def yard_facilities(parent,lights):
    yard=uw.Node('Alcatraz Recreation Yard',parent);landmark('Recreation Yard',(-48,27.28,46),(44,5,50))
    slab('Recreation yard slab',yard,(-48,27.13,46),(44,.30,50),'Alc_Floor')
    slab('Yard retaining foundation',yard,(-48,22.7,46),(45,8.55,51),'Alc_Rock')
    for x in [-70,-26]:
        # East gap is the stair leading to the cellhouse cross corridor.
        segments=[(46,50)] if x==-70 else [(25.5,9),(54,34)]
        for z,length in segments:slab('Recreation perimeter wall',yard,(x,29.3,z),(.35,4.0,length),'Alc_Stone')
    for z in [21,71]:slab('Recreation end wall',yard,(-48,29.3,z),(44,4,.35),'Alc_Stone')
    # Low bleachers sit clear of the retained mission actor paths.
    for i in range(4):slab('Yard concrete bleacher',yard,(-66.6+i*.70,27.28+(i+1)*.22/2,54),(1.3,(i+1)*.22,20),'Alc_Stone')
    for x,z in [(-68,39),(-56,33),(-36,31),(-60,57),(-48,65)]:
        slab('Yard timber bench',yard,(x,27.72,z),(2.3,.10,.45),'Alc_Wood')
        for dx in [-.8,.8]:slab('Yard bench support',yard,(x+dx,27.48,z),(.09,.40,.34),'Alc_Iron',False)
    slab('Gang meeting table',yard,(-58,28.02,48.2),(2,.14,1.10),'Alc_Wood')
    for x in [-58.7,-57.3]:slab('Gang table support',yard,(x,27.64,48.2),(.09,.70,.90),'Alc_Iron',False)
    slab('Tattoo work table',yard,(-60,28.03,33.3),(1.3,.12,.65),'Alc_Wood')
    slab('Meal cart',yard,(-36,27.91,32.3),(1.4,.65,.70),'Alc_Iron')
    slab('Meal tray stack',yard,(-36,28.27,32.3),(.8,.06,.45),'M_Chrome',False)
    for dx in [-.5,.5]:
        for dz in [-.25,.25]:node('Meal cart wheel',yard,(-36+dx,27.47,32.3+dz),'Alc_Cylinder','Alc_DarkSteel',(90,0,0),(.18,.10,.18))
    # Workshop awning, training bag and basketball markings are original game additions.
    slab('Inmate workshop floor',yard,(-35,27.22,54.6),(6.5,.12,5.8),'Alc_Floor')
    for x in [-38.2,-31.8]:slab('Workshop side wall',yard,(x,28.8,54.6),(.17,3.1,5.6),'Alc_Painted')
    slab('Workshop back wall',yard,(-35,28.8,57.4),(6.5,3.1,.17),'Alc_Brick')
    slab('Workshop awning',yard,(-35,30.5,54.6),(6.8,.14,6),'Alc_Roof')
    slab('Workshop bench',yard,(-35,28.10,55.4),(1.8,.14,.75),'Alc_Wood')
    node('Training punch bag',yard,(-50,28.78,52),'Alc_Cylinder','Alc_Blanket',scale=(.48,1.45,.48))
    for x in [-51,-49]:slab('Training bag frame',yard,(x,28.6,52),(.10,2.65,.10),'Alc_Iron')
    slab('Training bag overhead',yard,(-50,30.1,52),(2.2,.10,.10),'Alc_Iron',False)
    sign(yard,'Yard identity',(-69.75,30.1,45),'ALCATRAZ\nRECREATION YARD',(6,1.0),90)
    sign(yard,'Blue Meridian',(-60,29.10,33.8),'BLUE MERIDIAN',(2.4,.45),180)
    steps(parent,'Yard to cellhouse steps',(-29.6,27.28,33),(-26.5,30.,33),3.2,16)
    # North mess/kitchen wing; broad ground route opens at the cellhouse north portal.
    mess=hall(parent,lights,'Dining Hall',(0,30.,55.5),(44,21),6.8)
    road(parent,'Dining Hall threshold',[(0,30.01,42),(0,30.01,46)],4.5,'Alc_Floor')
    for x in [-15,-7,1,9,17]:
        for z in [51,58]:
            slab('Mess hall table',mess,(x,30.77,z),(4.4,.10,1.0),'Alc_Iron')
            for dz in [-.9,.9]:slab('Mess hall bench',mess,(x,30.44,z+dz),(4.4,.08,.38),'Alc_Wood')
            for dx in [-1.6,1.6]:slab('Mess table support',mess,(x+dx,30.35,z),(.06,.7,.7),'Alc_Iron',False)
    slab('Kitchen serving counter',mess,(0,30.96,64),(30,.14,1),'Alc_Iron')
    for x in [-8,0,8]:node('Kitchen serving pot',mess,(x,31.24,64),'Alc_Cylinder','M_Chrome',scale=(.65,.40,.65))
    shower=hall(parent,lights,'Shower Room',(12,30,-51),(20,11),4.8)
    road(parent,'Shower entry threshold',PATH_CUTS[7][0],3,'Alc_Floor')
    for x in [5,8,11,14,17]:
        slab('Shower cubicle',shower,(x-1.15,31.0,-48),(.08,2,2.8),'M_Ceramic')
        b_box('Shower pipes','M_Chrome',(x,31.4,-46.35),(.055,2.5,.055))
        batched('Shower heads','M_Chrome',ellipsoid((.19,.07,.24),4,8),(x,32.6,-46.65))
        slab('Shower drain',shower,(x,30.04,-48),(.24,.01,.24),'Alc_DarkSteel',False)

def scenery_building(parent,lights,name,pos,size,h=7,mat='Alc_Stone',gable=False):
    g=hall(parent,lights,name,pos,size,h,mat);x,y,z=pos;w,d=size
    if gable:
        roof=Mesh();roof.quad((-w/2,0,-d/2),(0,3,-d/2),(0,3,d/2),(-w/2,0,d/2));roof.quad((0,3,-d/2),(w/2,0,-d/2),(w/2,0,d/2),(0,3,d/2))
        for s in [-1,1]:roof.tri((-w/2,0,s*d/2),(w/2,0,s*d/2),(0,3,s*d/2))
        key='Alc_Roof_'+name.replace(' ','_');uw.save_mesh(key,roof,'Landmarks');node(name+' pitched roof',g,(x,y+h+.12,z),key,'Alc_Tile')
    return g

def landmarks(parent,lights):
    # Named geographic positions follow the NPS map: industry north, residential south,
    # prison summit, water tower/yard west, ferry landing east.
    new=scenery_building(parent,lights,'New Industries',(-38,9.3,122),(29,42),9,'Alc_Brick')
    model=scenery_building(parent,lights,'Model Industries',(-16,9.3,157),(28,18),10,'Alc_Stone')
    plant=scenery_building(parent,lights,'Power House',(62,7.3,113),(28,34),9,'Alc_Stone')
    node('Power House chimney',parent,(73,24.3,119),'Alc_Cylinder','Alc_Brick',scale=(2.7,34,2.7),solid=True)
    store=scenery_building(parent,lights,'Storehouse',(70,5,-30),(28,39),7,'Alc_Stone')
    barracks=scenery_building(parent,lights,'Building 64 - Barracks',(65,5,-91),(32,39),12,'Alc_Stone',True)
    club=scenery_building(parent,lights,"Officers Club",(64,7.3,58),(22,19),6,'Alc_Stone',True)
    warden=scenery_building(parent,lights,"Wardens House",(26,30.,-69),(16,19),8,'Alc_Stone',True)
    # A lighthouse on the south summit is distinct from the northern water tower.
    lighthouse=uw.Node('Alcatraz Lighthouse',parent,(3,30.,-72));landmark('Lighthouse',(3,30.,-72),(7,26,7))
    house=scenery_building(parent,lights,'Lighthouse Keeper',(3,30.,-72),(13,12),4.2,'Alc_Stone')
    uw.save_mesh('Alc_Lighthouse',cylinder(2.1,20,8,top_radius=1.55),'Landmarks')
    shaft=node('Octagonal lighthouse shaft',lighthouse,(0,14.2,0),'Alc_Lighthouse','Alc_White')
    collision(shaft,(4.2,20,4.2))
    node('Lighthouse lantern glass',lighthouse,(0,25,0),'Alc_Cylinder','Alc_Glass',scale=(4.1,2.5,4.1))
    node('Lighthouse gallery platform',lighthouse,(0,23.45,0),'Alc_Cylinder','Alc_Stone',scale=(5.3,.3,5.3))
    node('Lighthouse roof',lighthouse,(0,26.55,0),'Alc_Cylinder','Alc_DarkSteel',scale=(4.6,.35,4.6))
    for a in np.linspace(0,math.tau,8,endpoint=False):
        slab('Lantern column',lighthouse,(2*math.cos(a),25.,2*math.sin(a)),(.065,2.5,.065),'Alc_DarkSteel',False)
    light(lights,'Lighthouse lantern',(3,55.,-72),1.8,20,(1,.81,.48))
    tower=uw.Node('Alcatraz Water Tower',parent,(-57,27.28,80));landmark('Water Tower',(-57,27.28,80),(12,25,12))
    slab('Water tower terrace',tower,(0,-.12,0),(18,.25,18),'Alc_Floor')
    for x in [-4.4,4.4]:
        for z in [-4.4,4.4]:
            slab('Water tower steel leg',tower,(x,9,z),(.32,18,.32),'Alc_Iron',False)
            slab('Water tower concrete foot',tower,(x,.45,z),(1.1,.90,1.1),'Alc_Stone')
    for y in [3,8,13,17]:
        for z in [-4.4,4.4]:
            b_box('Water tower braces','Alc_Iron',(0,y,z),(9.2,.16,.18))
            batched('Water tower braces','Alc_Iron',tube([(-4.4,y-3,z),(4.4,y+2,z)],.075,6))
            batched('Water tower braces','Alc_Iron',tube([(-4.4,y+2,z),(4.4,y-3,z)],.075,6))
        for x in [-4.4,4.4]:batched('Water tower braces','Alc_Iron',tube([(x,y-3,-4.4),(x,y+2,4.4)],.075,6))
    tank=lathe([(-3,0),(-3,5.35),(-2.6,5.60),(2.6,5.60),(3,5.35),(3.15,0)],40)
    uw.save_mesh('Alc_WaterTank',tank,'Landmarks');node('Water tower riveted tank',tower,(0,20,0),'Alc_WaterTank','Alc_TankBlue')
    for yy in [17.5,19,20.5,22]:
        ring=lathe([(yy-.04,5.64),(yy+.04,5.64)],40);batched('Tank rings','Alc_DarkSteel',ring,(-57,27.28,80))
    for i in range(38):b_box('Tower ladder','Alc_Rust',(-52.15,27.8+i*.46,80),(.9,.045,.05))
    sign(parent,'Water tower sign',(-57,48.5,74.38),'ALCATRAZ',(8,1.15),180)
    guard=scenery_building(parent,lights,'Guardhouse - Sally Port',(50,16.2,-100),(14,15),7,'Alc_Stone')
    # Parade ground and low ruined residence foundations south of the prison summit.
    landmark('Parade Ground',(-6,15.8,-123),(83,.3,52))
    slab('Parade ground paving',parent,(-6,15.65,-123),(83,.3,52),'Alc_Floor')
    slab('Parade ground retaining wall',parent,(-6,8.1,-149),(84,15,.45),'Alc_Rock')
    for x in [-43,32]:rail(parent,'Parade ground boundary',(x,15.8,-148),(x,15.8,-99))
    for i in range(4):
        x=-23+i*12
        slab('Former officers housing foundation',parent,(x,16.15,-106),(9,.7,8),'Alc_Brick')
        for dz in [-3.9,3.9]:slab('Residential ruin wall',parent,(x,16.95,-106+dz),(9,1.8,.24),'Alc_Stone')
    # Landing, piles, bollards and timber ferry wharf are actual connected geometry.
    landmark('Dock',(105,5.0,-63),(43,1,15))
    slab('Ferry dock concrete landing',parent,(96,4.85,-62),(23,.3,23),'Alc_Floor')
    slab('Ferry wharf deck',parent,(116,4.82,-62),(21,.24,14),'Alc_Wood')
    for x in [107,113,120,126]:
        for z in [-68,-56]:node('Wharf timber pile',parent,(x,1.4,z),'Alc_Cylinder','Alc_Wood',scale=(.45,9,.45),solid=True)
    for z in [-68.5,-55.5]:rail(parent,'Ferry wharf edge',(105,5,-0+z),(126,5,z))
    for x in [108,117,124]:node('Mooring bollard',parent,(x,5.24,-57),'Alc_Cylinder','Alc_DarkSteel',scale=(.40,.50,.40))
    sign(parent,'Landing rules',(92,7.4,-53.8),'ALCATRAZ ISLAND\nRESTRICTED LANDING',(6.5,1.1),0)
    # Non-interactive hull: exterior prop, not a promised escape mission.
    hull=Mesh();sections=[(-8,1.5),(-5,3),(5,3),(8,0.2)]
    for (z,w),(zz,ww) in zip(sections,sections[1:]):
        hull.quad((-w,.1,z),(-ww,.1,zz),(-ww,.9,zz),(-w,.9,z));hull.quad((w,.9,z),(ww,.9,zz),(ww,.1,zz),(w,.1,z))
        hull.quad((-w,.9,z),(-ww,.9,zz),(ww,.9,zz),(w,.9,z))
    uw.save_mesh('Alc_ServiceBoat',hull,'Props');node('Moored service launch',parent,(119,1.0,-80),'Alc_ServiceBoat','Alc_Iron')
    slab('Service launch cabin',parent,(119,2.55,-80),(3.4,2.1,4.6),'Alc_White')

def paths(parent):
    road(parent,'East shore road',PATH_CUTS[0][0],5.8)
    road(parent,'Dock connection',[(85,5.02,-62),(103,5.02,-62),(107,5.02,-62)],6)
    # Main route rises through three turns; every grade stays below 17 degrees.
    road(parent,'Cellhouse switchback road',PATH_CUTS[1][0],5.5)
    road(parent,'West road',PATH_CUTS[2][0],5.0)
    road(parent,'North industries road',PATH_CUTS[3][0],3.0)
    road(parent,'New Industries entrance',PATH_CUTS[8][0],4.0,'Alc_Floor')
    road(parent,'Cellhouse east walk',PATH_CUTS[4][0],3.5,'Alc_Floor')
    road(parent,'Lighthouse terrace path',PATH_CUTS[5][0],3.0,'Alc_Floor')
    road(parent,'Warden entry path',PATH_CUTS[9][0],3.0,'Alc_Floor')
    road(parent,'Lighthouse keeper entry',PATH_CUTS[10][0],3.0,'Alc_Floor')
    road(parent,'Water tower service path',[(-65,27.42,76),(-57,27.42,80)],3,'Alc_Floor')
    road(parent,'Agave trail',PATH_CUTS[6][0],1.8,'Alc_Floor')
    road(parent,'Parade east connection',[(33,15.87,-120),(40,16.20,-119)],4,'Alc_Floor')
    for x,z,y in [(45,-113,16.2),(60,-70,21.9),(95,-75,5),(89,8,5),(86,82,7.3),(-66,112,21),(-67,-109,17.3)]:
        slab('Island lamp post',parent,(x,y+2.5,z),(.09,5,.09),'Alc_DarkSteel')
        slab('Island lamp lantern',parent,(x,y+4.95,z),(.37,.40,.37),'Alc_Light',False)

def split_scene(text):
    parts=re.split(r'^--- !u!(\d+) &(-?\d+)\n',text,flags=re.M)
    return {int(parts[i+1]):(int(parts[i]),parts[i+2]) for i in range(1,len(parts),3)}

def splice_old(source):
    """Retain complete live actors, equipment props, activity tables and story logic.
    Delete the old island and architecture rather than hiding a second map behind it.
    """
    blocks=split_scene(source);docs={i:yaml.load(b,Loader=yaml.CSafeLoader) for i,(_,b) in blocks.items()}
    gos={i:d['GameObject'] for i,d in docs.items() if 'GameObject' in d}
    trs={i:d['Transform'] for i,d in docs.items() if 'Transform' in d}
    tid_for={d['m_GameObject']['fileID']:i for i,d in trs.items()}
    go_for={i:d['m_GameObject']['fileID'] for i,d in trs.items()}
    names={i:d['m_Name'] for i,d in gos.items()}
    def descend(go):
        result={go}
        for c in trs[tid_for[go]]['m_Children']:result |= descend(go_for[c['fileID']])
        return result
    keep_roots=['_BlackstoneChapter01','_PrisonPopulation','_StoryAnchors','Five-card draw table','Conversation table',
       'Player poker seat','Player conversation seat','Dropped knife','Knife stored under mattress','Gang phone',
       'Interact_CellStash','Interact_Reflection','Interact_SolitaryBed','Interact_Brother','Interact_Phone','Interact_Training',
       'B-04 barred door','Solitary door','Late afternoon sun','Prison cinematic grade']
    keep=set()
    for name in keep_roots:
        choices=[i for i,n in names.items() if n==name]
        if name=='Solitary door':choices=choices[:1]
        for i in choices:keep|=descend(i)
    # Main game object has the authoring camera/controller/bus; old environment is a separate root.
    keep_ids=set()
    for go in keep:keep_ids.update([go]+[c['component']['fileID'] for c in gos[go]['m_Component']])
    for i,(kind,b) in blocks.items():
        if kind in [29,104,157,196,1660057539]:keep_ids.add(i)
    new={i:[kind,b] for i,(kind,b) in blocks.items() if i in keep_ids}
    oldpositions={i:np.array([t['m_LocalPosition'][k] for k in 'xyz']) for i,t in trs.items()}
    actor_guid=uw.guid('Assets/Game/Scripts/AI/PrisonActor.cs')
    director_guid=uw.guid('Assets/Game/Scripts/Missions/PrisonStoryDirector.cs')
    positions={};rotations={}
    def setpos(go,pos):positions[tid_for[go]]=list(pos)
    def setname(name,pos):
        for go,n in names.items():
            if n==name and go in keep:setpos(go,pos)
    actors=[]
    for i,d in docs.items():
        c=d.get('MonoBehaviour')
        if not c or c.get('m_Script',{}).get('guid')!=actor_guid:continue
        go=c['m_GameObject']['fileID'];name=c['displayName'];p=oldpositions[tid_for[go]]
        dest=POINTS['cellSpawn'] if name=='Elias Vale' else POINTS['brother'] if name=='Theo Vale' else p+YARD
        if name=='Officer Harrow':dest=(-30.5,27.30,49)
        setpos(go,dest);actors.append({'id':go,'name':name,'position':list(dest),'yaw':float(trs[tid_for[go]]['m_LocalEulerAnglesHint']['y']),'pose':c.get('pose',0)})
        if c.get('patrol'):
            body=new[i][1]
            oldroute=c['patrol'];route=[np.array([p[k] for k in 'xyz'])+YARD for p in oldroute]
            if name=='Officer Harrow':route=[(-30.5,27.30,49),(-30.5,27.30,25),(-33,27.30,25),(-33,27.30,49)]
            body=re.sub(r'(?ms)^  patrol:\n(?:  - \{[^\n]+\}\n)+','  patrol:\n'+''.join('  - '+uw.vec(p)+'\n' for p in route),body)
            new[i][1]=body
    for name in ['Five-card draw table','Conversation table','Player poker seat','Player conversation seat']:
        go=next(i for i,n in names.items() if n==name);setpos(go,oldpositions[tid_for[go]]+YARD)
    setname('Dropped knife',POINTS['knife']);setname('Knife stored under mattress',(-5.04,30.37,CELL_Z-.15));setname('Gang phone',POINTS['phone'])
    for name,pos in [('Interact_CellStash',POINTS['cellStash']),('Interact_Reflection',POINTS['reflection']),('Interact_SolitaryBed',(-18.1,30.68,CELL_Z-.2)),
                     ('Interact_Brother',(20.22,31.14,-38)),('Interact_Phone',POINTS['phone']),('Interact_Training',(-50,28.78,52)),
                     ('B-04 barred door',(-2.85,30,CELL_Z-.575)),('Solitary door',(-14.8,30,CELL_Z-.575))]:setname(name,pos)
    for key in ['cellSpawn','yardSpawn','solitarySpawn','sleepPosition','visitSpawn']:setname(key,POINTS[key])
    for go in keep:
        name=names[go]
        if name.startswith(('Shot_','Focus_')):
            shot=name.split('_',1)[1];p=oldpositions[tid_for[go]]
            if shot=='cell':pos=np.array(POINTS['cellSpawn'])+(p-np.array([-7,.11,-15]))
            elif shot in ['yard','niko','leader','tattoo','cook','reader','fixer']:pos=p+YARD
            elif shot=='visit':pos=np.array(POINTS['visitSpawn'])+(p-np.array([26.5,.11,-1.5]))
            elif shot=='door':pos=np.array(POINTS['solitarySpawn'])+(p-np.array([30,.03,-22.5]))
            else:pos=np.array(POINTS['solitarySpawn'])+(p-np.array([30,.03,-22.5]))
            setpos(go,pos)
    # Reframe the tight new cells and D-block so shots are inside their walls.
    for name,pos in [('Shot_cell',(-3.4,31.8,CELL_Z+.76)),('Focus_cell',(-4.55,31.15,CELL_Z)),
        ('Shot_solitary',(-15.5,32.1,CELL_Z+1.3)),('Focus_solitary',(-18,31.1,CELL_Z)),
        ('Shot_door',(-16.5,31.7,CELL_Z)),('Focus_door',(-13.6,31.2,CELL_Z)),
        ('Shot_visit',(18.4,31.8,-39.5)),('Focus_visit',(22.25,31.3,-38))]:setname(name,pos)
    setname('Main Camera',(-2,32.1,CELL_Z+2))
    roots=[]
    for i,(kind,body) in new.items():
        if kind==4:
            t=trs[i];father=t['m_Father']['fileID']
            if father not in keep_ids:
                body=re.sub(r'^  m_Father: .*$', '  m_Father: {fileID: 0}',body,flags=re.M);roots.append(i)
            elif father==0:roots.append(i)
            children=[c['fileID'] for c in t['m_Children'] if c['fileID'] in keep_ids]
            body=re.sub(r'(?ms)^  m_Children:.*?(?=^  m_Father:)', '  m_Children:'+(' []\n' if not children else '\n'+''.join('  - {fileID: '+str(c)+'}\n' for c in children)),body)
            if i in positions:body=re.sub(r'^  m_LocalPosition: .*$', '  m_LocalPosition: '+uw.vec(positions[i]),body,flags=re.M)
        if kind==114 and director_guid in body:
            # Map-specific scripted placements have authored Transform references.
            body+='  guardIncidentPoint: {fileID: '+str(MAP_ANCHORS['guardIncident'].tid)+'}\n'
            body+='  guardIsolationPoint: {fileID: '+str(MAP_ANCHORS['guardIsolation'].tid)+'}\n'
            body+='  rivalIsolationPoint: {fileID: '+str(MAP_ANCHORS['rivalIsolation'].tid)+'}\n'
        if kind==108 and 'Late afternoon sun' in names.get(docs[i]['Light']['m_GameObject']['fileID'],''):
            body=re.sub(r'^  m_Intensity: .*$', '  m_Intensity: 2.2',body,flags=re.M)
        new[i][1]=body
    # SceneRoots will be rebuilt once, with retained and newly authored roots.
    new={i:v for i,v in new.items() if v[0]!=1660057539}
    # Detect accidental retained local references to geometry we removed.
    for i,(_,b) in new.items():
        for match in re.finditer(r'\{fileID: (-?\d+)\}',b):
            target=int(match[1])
            if target!=0 and target not in new and target not in {n.id for n in uw.Node.all}|{n.tid for n in uw.Node.all}:
                # B-04's player interaction is kept. No allowed dangling reference.
                raise RuntimeError('Dangling old scene reference: '+str(i)+' -> '+str(target))
    return new,roots,actors,names,keep,positions,oldpositions,tid_for

def map_texture():
    path=BASE+'/Resources/Alcatraz/IslandMap.png';image=Image.new('RGB',(1024,1536),(22,42,49));d=ImageDraw.Draw(image)
    def p(x,z):return ((x+130)/260*1024,(190-z)/390*1536)
    d.polygon([p(*v) for v in OUTLINE],fill=(76,82,65),outline=(134,135,101),width=4)
    for r in ROADS:d.line([p(v[0],v[2]) for v in r['points']],fill=(155,151,130),width=max(3,int(r['width']/260*1024)))
    for land in LANDMARKS:
        x,y,z=land['position'];w,h,dep=land['size'];x0,y0=p(x-w/2,z+dep/2);x1,y1=p(x+w/2,z-dep/2)
        if land['name'] in ['Water Tower','Lighthouse']:d.ellipse((x0,y0,x1,y1),fill=(165,160,137),outline=(213,206,178),width=2)
        else:d.rectangle((x0,y0,x1,y1),fill=(143,145,128),outline=(213,206,178),width=2)
    (ROOT/path).parent.mkdir(parents=True,exist_ok=True);image.save(ROOT/path)
    uw.meta(path,'TextureImporter','  serializedVersion: 13\n  mipmaps:\n    enableMipMap: 0\n    sRGBTexture: 1\n  textureType: 0\n  maxTextureSize: 2048\n  textureSettings:\n    filterMode: 1\n    wrapU: 1\n    wrapV: 1\n')

def record_nodes():
    for n in uw.Node.all:
        obj={'name':n.name,'id':n.id,'parent':n.parent.id if n.parent else 0,'pos':n.pos,'rot':n.rot,'scale':n.scale,'active':n.active}
        if n.mesh:obj.update(mesh=n.mesh,mat=n.mat,rendered=True)
        uw.PREVIEW['nodes'].append(obj)

def make_scenes():
    global MAP_ANCHORS
    source=(ROOT/'Assets/Game/Scenes/SC_BlackstoneIsland.unity').read_text()
    anchor_parent=uw.Node('Alcatraz scripted actor positions',static=False)
    MAP_ANCHORS={name:uw.Node(name,anchor_parent,pos=POINTS[name],static=False) for name in ['guardIncident','guardIsolation','rivalIsolation']}
    retained,roots,actors,names,keep,positions,oldpositions,tid_for=splice_old(source)
    # Additional local routines use authored native scene objects and the same
    # roster as runtime character selection and offline source previews.
    roster=json.loads((ROOT/(BASE+'/Resources/Alcatraz/CharacterRoster.json')).read_text())
    population=uw.Node('Alcatraz additional prison population',static=False)
    for profile in roster['actors']:
        if not profile.get('ambient'):continue
        position=[profile['position'][axis] for axis in 'xyz']
        actor=uw.Node(profile['actorName'],population,position,(0,profile['yaw'],0),layer=8,static=False)
        actor.boxcollider((.45,profile['height'],.45),(0,profile['height']/2,0))
        route=profile.get('route',[])
        body='  displayName: '+profile['actorName']+'\n  pose: 0\n  patrolEnabled: '+str(int(bool(route)))+'\n  driveLocomotion: 0\n  walkingSpeed: '+str(profile['walkSpeed'])+'\n'
        body+='  patrol:\n'+''.join('  - '+uw.vec([p[axis] for axis in 'xyz'])+'\n' for p in route) if route else '  patrol: []\n'
        actor.script('Assets/Game/Scripts/AI/PrisonActor.cs',body)
        actors.append({'id':actor.id,'name':profile['actorName'],'position':position,'yaw':profile['yaw'],'pose':0})
    layout=uw.Node('Alcatraz map identity',static=False)
    layout.script(BASE+'/Scripts/AlcatrazMap.cs','  baseElevation: 30\n')
    layout.script(BASE+'/Scripts/AlcatrazPresentation.cs')
    docs={i:yaml.load(b,Loader=yaml.CSafeLoader) for i,(_,b) in retained.items()}
    sun=next(i for i,d in docs.items() if 'Light' in d)
    settings=uw.HEAD+''.join('--- !u!'+str(k)+' &'+str(i)+'\n'+b for i,(k,b) in retained.items() if k in [29,104,157,196])
    settings=re.sub(r'm_FogDensity: [\d.]+','m_FogDensity: 0.0035',settings)
    for index,path in enumerate(SCENES):
        story=index==1;bs={i:[k,b] for i,(k,b) in retained.items() if k not in [29,104,157,196]}
        disabled={'PrisonStoryDirector','PrisonHUD','StoryInteractable','PrisonPokerTable','PrisonConversationTable','PrisonPopulation','CinematicView','ExplorationHUD'}
        scripts={uw.guid(str(p.relative_to(ROOT))):p.stem for p in (ROOT/'Assets').rglob('*.cs')}
        if not story:
            for i,(kind,b) in bs.items():
                script=re.search(r'm_Script: \{fileID: 11500000, guid: (\w+)',b)
                name=scripts.get(script[1]) if script else None
                if name in disabled:b=b.replace('  m_Enabled: 1','  m_Enabled: 0',1)
                if name=='PlayerMovement':
                    for f,v in [('walkSpeed','1.05'),('jogSpeed','1.55'),('sprintSpeed','4.9'),('crouchSpeed','.85'),('acceleration','7.5'),('deceleration','10'),('rotationSharpness','9')]:b=re.sub(r'^  '+f+r': .*$', '  '+f+': '+v,b,flags=re.M)
                bs[i][1]=b
            playergo=next(i for i,n in names.items() if n=='Player');tid=tid_for[playergo]
            bs[tid][1]=re.sub(r'^  m_LocalPosition: .*$', '  m_LocalPosition: '+uw.vec((-43,27.40,34)),bs[tid][1],flags=re.M)
        start=len(uw.Node.all)
        setup=uw.Node('Alcatraz character foundation',static=False)
        setup.script('Assets/Game/Foundation/Scripts/FoundationBootstrap.cs','  storyMode: '+str(int(story))+'\n')
        if not story:
            setup.script('Assets/Game/Foundation/Scripts/FoundationHUD.cs','  worldTitle: "ALCATRAZ'+r'\n'+'ISLAND"\n  storyScene: SC_AlcatrazChapter01\n')
            setup.script('Assets/Game/Foundation/Scripts/FoundationConversations.cs')
        # Both scenes share map coordinates. Exploration has three practice targets.
        shared=list(uw.Node.all[:start]);extras=uw.Node.all[start:]
        base=settings+''.join('--- !u!'+str(kind)+' &'+str(i)+'\n'+b for i,(kind,b) in bs.items())
        base+=''.join(uw.node_yaml(n) for n in shared+extras)
        rootids=roots+[n.tid for n in shared+extras if n.parent is None]
        assert len(rootids)==len(set(rootids))
        base+='--- !u!1660057539 &9223372036854775807\nSceneRoots:\n  m_ObjectHideFlags: 0\n  m_Roots:\n'+''.join('  - {fileID: '+str(i)+'}\n' for i in rootids)
        uw.write(path,base);uw.meta(path)
        uw.Node.all=uw.Node.all[:start]
    # Copy only retained non-character art for preview, with its new root transforms.
    oldnodes={n['id']:n for n in OLD['nodes']};actors_go={a['id'] for a in actors}
    def has_actor_ancestor(n):
        while n:
            if n['id'] in actors_go:return True
            n=oldnodes.get(n.get('parent'))
        return False
    used=set()
    for old in OLD['nodes']:
        if old['id'] not in keep or has_actor_ancestor(old):continue
        n=dict(old);tid=tid_for.get(n['id'])
        if tid in positions:n['pos']=positions[tid]
        if n.get('parent') not in keep:n['parent']=0
        uw.PREVIEW['nodes'].append(n)
        if n.get('mesh'):used.add(n['mesh'])
    for key in used:uw.PREVIEW['meshes'][key]=OLD['meshes'][key]
    uw.write('Documentation/AlcatrazActors.json',json.dumps(actors,indent=2))
    uw.write('Documentation/AlcatrazLayout.json',json.dumps({'revision':'08','coordinates':'Unity metres; north +Z; game adaptation, not measured restoration',
      'source_urls':['https://www.nps.gov/goga/planyourvisit/upload/Alcatraz-map-Access-508.pdf',
                     'https://discussions.unity.com/t/alcatraz-breakout-concept-wip/606269'],
      'outline':OUTLINE.tolist(),'landmarks':LANDMARKS,'roads':ROADS,'cells':CELLS,'chapter_points':POINTS,
      'scene_paths':SCENES,'original_scene_sha256':hashlib.sha256(source.encode()).hexdigest()},indent=2))

def range_targets(parent):
    for i,x in enumerate([-57,-54,-51]):
        n=slab('Alcatraz practice target '+str(i+1),parent,(x,29.0,62),(.94,1.25,.045),'TargetPaper')
        n.script('Assets/Game/Foundation/Scripts/FoundationTarget.cs')
        slab('Practice target support',parent,(x,28.08,62.06),(.08,1.6,.08),'Alc_Iron',False)
    for x,mat,kind in [(-60,'TestMetal',2),(-57,'TestWood',3),(-54,'TestTurf',0)]:
        p=slab('Alcatraz '+mat+' footstep pad',parent,(x,27.335,38),(2.5,.055,3),mat)
        p.script('SurfaceTag','  surface: '+str(kind)+'\n')

def load_range_materials():
    paths={'TargetPaper':'Assets/Game/Foundation/Art/Textures/TargetPaper.png','TestTurf':'Assets/Game/Foundation/Art/Textures/TestTurf.png'}
    for n,c,r,m in [('TargetPaper',[1,1,1,1],.9,0),('TestMetal',[.35,.38,.40,1],.4,.85),('TestWood',[.29,.16,.08,1],.82,0),('TestTurf',[1,1,1,1],.97,0)]:
        uw.material(n,c,r,m,texture=paths.get(n),tiling=1 if n!='TestTurf' else 2)

def main():
    uw.ART=BASE+'/Art';uw.Node.all=[];uw.Node.counter=30000000
    uw.PREVIEW={'meshes':{},'materials':{},'nodes':[]}
    from alcatraz_concept_pass import prepare_materials, add_details as concept_details, COASTAL_TRAIL
    import sys
    materials();load_range_materials();prepare_materials(sys.modules[__name__])
    PATH_CUTS.append((COASTAL_TRAIL,2.3))
    root=uw.Node('Alcatraz Island Environment');lights=uw.Node('Alcatraz interior lamps',static=False)
    height=island(root);cellhouse(root,lights);yard_facilities(root,lights);landmarks(root,lights);paths(root);range_targets(root);flush_batches(root)
    from alcatraz_detail_pass import add_details
    import sys
    add_details(sys.modules[__name__],root,lights)
    concept_details(sys.modules[__name__],root,lights,height)
    map_texture();make_scenes();record_nodes()
    remove_superseded_batches()
    uw.write('Documentation/AlcatrazAuthoring.json',json.dumps(uw.PREVIEW,separators=(',',':')))
    uw.write('Documentation/AlcatrazColliders.json',json.dumps(COLLIDERS,separators=(',',':')))
    setting=uw.HEAD+'--- !u!1045 &1\nEditorBuildSettings:\n  m_ObjectHideFlags: 0\n  serializedVersion: 2\n  m_Scenes:\n'
    for enable,path in [(1,SCENES[0]),(1,SCENES[1]),(0,'Assets/Game/Scenes/SC_BlackstoneFoundation.unity'),(0,'Assets/Game/Scenes/SC_BlackstoneStory_Upgraded.unity'),(0,'Assets/Game/Scenes/SC_BlackstoneIsland.unity'),(0,'Assets/_DesertShift/Scenes/SC_DesertTown.unity')]:
        setting+='  - enabled: '+str(enable)+'\n    path: '+path+'\n    guid: '+uw.guid(path)+'\n'
    setting+='  m_configObjects: {}\n  m_UseUCBPForAssetBundles: 0\n';uw.write('ProjectSettings/EditorBuildSettings.asset',setting)
    for path in (ROOT/BASE).rglob('*'):
        if path.is_dir():uw.meta(str(path.relative_to(ROOT)),'DefaultImporter','  folderAsset: yes\n')
        elif path.suffix=='.cs':uw.meta(str(path.relative_to(ROOT)),'MonoImporter','  serializedVersion: 2\n  defaultReferences: []\n  executionOrder: 0\n  icon: {instanceID: 0}\n')
        elif not path.name.endswith('.meta') and not Path(str(path)+'.meta').exists():uw.meta(str(path.relative_to(ROOT)))
    uw.meta(BASE,'DefaultImporter','  folderAsset: yes\n')
    print(json.dumps({'map':'Alcatraz','native_objects':len(uw.Node.all),'cells':len(CELLS),'B_C_cells':sum(c['block'] in ['B','C'] for c in CELLS),'landmarks':len(LANDMARKS),'roads':len(ROADS),'colliders':len(COLLIDERS),'scenes':SCENES}))

if __name__=='__main__':main()
