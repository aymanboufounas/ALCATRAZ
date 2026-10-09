"""Revision 03 scanned PBR materials, physical UVs and coastal prison setting."""
import math,hashlib,json,re
from pathlib import Path
import numpy as np
from PIL import Image
from geometry import Mesh,box,cylinder,tube,ellipsoid
from unity_writer import *
SOURCE=ROOT/'Tools/ArtSources'
PBR={}
def pbr_materials(texture):
    for asset in ['brushed_concrete','concrete_floor_worn_001','brick_wall_001','seaside_rock','wood_planks','forest_floor']:
        images={}
        for kind in ['Diffuse','nor_gl','Rough','AO']:
            with Image.open(SOURCE/(asset+'_'+kind+'.jpg')) as image:
                images[kind]=np.array(image.convert('RGB').resize((2048,2048),Image.Resampling.LANCZOS))
        diffuse=texture('PBR_'+asset+'_Base',images['Diffuse'])
        normal=texture('PBR_'+asset+'_Normal',images['nor_gl'],True)
        # URP Lit: metallic in R, AO in G, smoothness in A.
        packed=np.zeros((2048,2048,4),np.uint8);packed[:,:,1]=images['AO'][:,:,0];packed[:,:,3]=255-images['Rough'][:,:,0]
        surface=texture('PBR_'+asset+'_Surface',packed,False)
        path=ROOT/(surface+'.meta');path.write_text(path.read_text().replace('sRGBTexture: 1','sRGBTexture: 0').replace('alphaIsTransparency: 1','alphaIsTransparency: 0'))
        PBR[asset]=(diffuse,normal,surface)
    def use(name,asset,color=(1,1,1,1),density=1):
        d,n,s=PBR[asset];material(name,list(color),0,texture=d,normal=n,surface=s,occlusion=s,tiling=density)
    use('M_Concrete','brushed_concrete',(.89,.90,.88,1),.5)
    use('M_Plaster','brushed_concrete',(.95,.93,.86,1),.5)
    use('M_WallPaint','brushed_concrete',(.40,.48,.42,1),.5)
    use('M_Floor','concrete_floor_worn_001',(.81,.84,.83,1),.38)
    use('M_Yard','concrete_floor_worn_001',(.94,.91,.85,1),.35)
    use('M_Wood','wood_planks',(.65,.55,.43,1),.8)
    use('M_Brick','brick_wall_001',(.72,.68,.62,1),.45)
    use('M_CoastRock','seaside_rock',(.78,.76,.69,1),.35)
    use('M_CoastEarth','forest_floor',(.68,.64,.52,1),.35)
    for skin,file,tint in [('Light','SkinLight',(1,1,1,1)),('Olive','SkinTan',(.90,.90,.87,1)),('Tan','SkinTan',(1,1,1,1)),('Deep','SkinDeep',(1,1,1,1)),('Brown','SkinDeep',(1.24,1.19,1.12,1))]:
        with Image.open(SOURCE/(file+'.png')) as image:a=np.array(image.convert('RGB').resize((2048,2048),Image.Resampling.LANCZOS))
        base=texture('RealSkin_'+skin,a)
        normal_file='SkinDeep_Normal.png' if skin in ['Deep','Brown'] else 'SkinLight_Normal.png'
        with Image.open(SOURCE/normal_file) as image:normal=texture('RealSkin_'+skin+'_Normal',np.array(image.convert('RGB').resize((2048,2048),Image.Resampling.LANCZOS)),True)
        material('M_RealHead'+skin,list(tint),.62,texture=base,normal=normal)
        # Match exposed forearm color to the wrist in the same skin atlas.
        from realistic_characters import load_source
        v,uv,faces=load_source('african' if skin in ['Deep','Brown'] else 'caucasian')
        ids=list({i for g,f in faces if g=='joint-l-hand' for i,_ in f})
        direction=np.array([.50,-.65,1.18]);direction/=np.linalg.norm(direction)
        wrist=np.mean(v[ids],axis=0)-direction*.20
        coords=np.array([uv[t] for g,f in faces if g=='body' for i,t in f if 0<np.dot(v[i]-wrist,direction)<.30 and np.linalg.norm(v[i]-wrist)<.7])
        x=np.clip((coords[:,0]*2048).astype(int),0,2047);y=np.clip(((1-coords[:,1])*2048).astype(int),0,2047)
        color=np.median(a[y,x],axis=0)/255*np.array(tint[:3])/(237/255)
        material('M_Skin'+skin,[*color,1],.68,texture=PREVIEW['materials']['M_Skin'+skin]['texture'])
    material('M_RealIris',[.12,.065,.025,1],.12)
    rng=np.random.default_rng(392);y,x=np.mgrid[:1024,:1024]
    hair=np.clip(95+15*np.sin(x*.8+y*.03)+rng.normal(0,5,(1024,1024)),45,135)
    ht=texture('HairFiber',np.stack([hair,hair,hair],-1))
    material('M_RealHair',[.11,.077,.052,1],.84,texture=ht,tiling=10)
    material('M_RealHairGrey',[.37,.35,.31,1],.9,texture=ht,tiling=10)
    material('M_Bark',[.25,.22,.17,1],.94,texture=PBR['wood_planks'][0],normal=PBR['wood_planks'][1],tiling=2)
    material('M_PineNeedle',[.14,.22,.12,1],.92)
    material('M_OliveLeaf',[.28,.34,.20,1],.92)
    material('M_DryGrass',[.36,.37,.22,1],.98)
    material('M_Gravel',[.42,.41,.34,1],.96,texture=PBR['seaside_rock'][0],normal=PBR['seaside_rock'][1],tiling=2)
    material('M_CoastalWater',[.06,.18,.20,1],.12,.2,shader_guid=guid('Assets/Game/Shaders/CoastalWater.shader'))

def physical_uvs():
    # Bake actual box dimensions so UVs represent metres, even on a long wall.
    cache={}
    for node in list(Node.all):
        if node.mesh!='PrisonBox':continue
        size=tuple(round(abs(s),5) for s in node.scale)
        if min(size)<=0:continue
        if size not in cache:
            name='PhysicalBox_'+hashlib.md5(str(size).encode()).hexdigest()[:12]
            geometry=box(size,.018)
            for i,(p,n) in enumerate(zip(geometry.v,geometry.n)):
                axis=int(np.argmax(np.abs(n)))
                geometry.uv[i]=[p[0],p[2]] if axis==1 else [p[2],p[1]] if axis==0 else [p[0],p[1]]
            save_mesh(name,geometry,'Environment/PhysicalBoxes');cache[size]=name
        original_scale=np.array(node.scale)
        for child in node.children:
            child.pos=(np.array(child.pos)*original_scale).tolist()
            child.scale=(np.array(child.scale)*original_scale).tolist()
        for i,(cls,cid,body) in enumerate(node.parts):
            if cls==65:
                for field in ['m_Size','m_Center']:
                    match=re.search(field+r': \{x: ([^,]+), y: ([^,]+), z: ([^}]+)\}',body)
                    if match:
                        value=np.array([float(x) for x in match.groups()])*original_scale
                        body=body[:match.start()]+field+': '+vec(value)+body[match.end():]
                node.parts[i]=(cls,cid,body)
        node.mesh=cache[size];node.scale=[1,1,1]
        path=MESHES[node.mesh][0]
        # Match renderer/filter references without changing physical colliders.
        for i,(cls,cid,body) in enumerate(node.parts):
            if cls==33:node.parts[i]=(cls,cid,body.replace(ref(MESHES['PrisonBox'][0]),ref(path)))

def terrain():
    mesh=Mesh();xs=np.arange(-111,128,3.5);zs=np.arange(-108,125,3.5)
    def point(x,z):
        r=math.sqrt(((x-8)/109)**2+((z-6)/104)**2)
        h=-.28 if r<.57 else -.28-(r-.57)*24
        h+=max(0,min(1,(r-.56)*5))*(.5*math.sin(x*.13+z*.1)+.38*math.cos(z*.17-x*.05))
        return (x,h,z)
    for x in xs[:-1]:
        for z in zs[:-1]:
            p=[point(x,z),point(x,z+3.5),point(x+3.5,z+3.5),point(x+3.5,z)]
            mesh.quad(*p,uv=[(q[0],q[2]) for q in p])
    return mesh

def tree(kind,seed):
    rng=np.random.default_rng(seed);trunk=Mesh();leaves=Mesh()
    height=9.5 if kind=='pine' else 7.0
    trunk.merge(cylinder(.18,height,14,top_radius=.065),(0,height/2,0))
    for level in range(9 if kind=='pine' else 7):
        y=height*(.27+level*.075);radius=(height-y)*.45 if kind=='pine' else 2.0+level*.12
        for j in range(5):
            angle=j*math.tau/5+level*.9;end=np.array([math.cos(angle)*radius,y+.4,math.sin(angle)*radius])
            points=[(0,y,0),end*.65+np.array([0,y*.35-.12,0]),end]
            trunk.merge(tube(points,.034 if kind=='pine' else .046,6))
            for k in range(24 if kind=='pine' else 32):
                t=rng.uniform(.28,1);centre=end*t+np.array([0,y*(1-t),0])+rng.normal(0,.15,3)
                a=angle+rng.uniform(-1.4,1.4);length=rng.uniform(.25,.65) if kind=='pine' else rng.uniform(.14,.30)
                direction=np.array([math.cos(a),rng.uniform(-.2,.4),math.sin(a)])*length
                width=np.array([-math.sin(a),.12,math.cos(a)])*(.11 if kind=='pine' else .065)
                leaves.tri(centre-width,centre+direction,centre+width)
                leaves.tri(centre+width,centre+direction,centre-width)
    return trunk,leaves

def enrich(env,lights,box_node,mesh_node,sign,light):
    for node in Node.all:
        if node.name=='Island rock foundation':node.active=False
        if node.name=='Ocean':
            node.mat='M_CoastalWater'
            node.parts=[(c,i,b.replace(ref(MATERIALS['M_Water'],2100000),ref(MATERIALS['M_CoastalWater'],2100000))) for c,i,b in node.parts]
    coast=Node('_CoastalSetting',static=True)
    save_mesh('CoastalTerrain',terrain(),'Environment/Coast')
    mesh_node('Clifftop island terrain',coast,(0,0,0),(1,1,1),'M_CoastEarth','CoastalTerrain',collision=False)
    for k in range(4):save_mesh('CoastalBoulder'+str(k),ellipsoid((1,1,1),18,30,seed=21+k),'Environment/Coast')
    rng=np.random.default_rng(468)
    for i in range(68):
        angle=i*math.tau/68;r=rng.uniform(.73,.86);x=8+109*r*math.cos(angle);z=6+104*r*math.sin(angle)
        mesh_node('Coastal cliff outcrop',coast,(x,-5.9+rng.uniform(-.8,.3),z),(rng.uniform(9,16),rng.uniform(8,13),rng.uniform(8,15)),
                  'M_CoastRock','CoastalBoulder'+str(i%4),rot=(rng.uniform(-18,18),rng.uniform(0,360),rng.uniform(-18,18)),collision=False)
    for kind in ['pine','olive']:
        trunk,leaves=tree(kind,22 if kind=='pine' else 88)
        save_mesh(kind+'Trunk',trunk,'Environment/Vegetation');save_mesh(kind+'Leaves',leaves,'Environment/Vegetation')
    for i in range(34):
        angle=rng.uniform(0,math.tau);radius=rng.uniform(.48,.64);x=8+107*radius*math.cos(angle);z=6+102*radius*math.sin(angle)
        if -25<x<46 and -36<z<46:continue
        kind='pine' if i%3 else 'olive';s=rng.uniform(.8,1.3);r=rng.uniform(0,360)
        for part,mat in [('Trunk','M_Bark'),('Leaves','M_PineNeedle' if kind=='pine' else 'M_OliveLeaf')]:
            mesh_node(kind+' coastal '+part,coast,(x,-.25,z),(s,s,s),mat,kind+part,rot=(0,r,0),collision=False)
    # Groundcover is one combined mesh rather than hundreds of objects.
    grass=Mesh()
    for i in range(850):
        x=rng.uniform(-53,69);z=rng.uniform(-52,67)
        if -26<x<46 and -35<z<46:continue
        for j in range(6):
            a=rng.uniform(0,math.tau);p=np.array([x+rng.normal(0,.12),-.27,z+rng.normal(0,.12)]);h=rng.uniform(.18,.47)
            w=np.array([math.cos(a),0,math.sin(a)])*.025;tip=p+np.array([.05,h,.02])
            grass.tri(p-w,tip,p+w);grass.tri(p+w,tip,p-w)
    save_mesh('CoastalGroundCover',grass,'Environment/Vegetation');mesh_node('Clifftop grass',coast,(0,0,0),(1,1,1),'M_DryGrass','CoastalGroundCover',collision=False)
    # An accessible service court connects through the existing east opening.
    yard=Node('_ServiceCourtyard',static=True)
    box_node('Service court paving',yard,(32,-.06,25),(24,.12,30),'M_Floor')
    for x in [22,27,32,37,42]:
        box_node('Court curb',yard,(x,.08,40),(4.7,.16,.30),'M_CoastRock')
    # Closed buildings are architectural scenery, with visible doors/windows.
    for label,x,z,sx,sz,h in [('Laundry',31,32,12,8,6.5),('Workshop annex',36,17,9,7,4.7),('Administration',-18,-17,8,18,5.2)]:
        box_node(label+' walls',yard,(x,h/2,z),(sx,h,sz),'M_Brick')
        box_node(label+' stone foundation',yard,(x,.37,z),(sx+.18,.74,sz+.18),'M_CoastRock')
        box_node(label+' roof',yard,(x,h+.08,z),(sx+.5,.18,sz+.5),'M_DarkMetal')
        for offset in [-sx*.31,sx*.31]:
            box_node(label+' window frame',yard,(x+offset,2.7,z-sz/2-.04),(1.55,1.8,.14),'M_Trim',False)
            box_node(label+' window',yard,(x+offset,2.7,z-sz/2-.13),(1.3,1.52,.025),'M_Glass',False)
            for q in [-.40,0,.40]:box_node(label+' security grille',yard,(x+offset+q,2.7,z-sz/2-.16),(.025,1.55,.035),'M_Metal',False)
        box_node(label+' door',yard,(x,.99,z-sz/2-.10),(1.13,1.98,.12),'M_Wood',False)
        sign(yard,label+' sign',(x,3.9,z-sz/2-.18),label.upper(),(3,.58),(0,180,0))
        mesh_node(label+' drain',yard,(x+sx/2-.25,h/2,z-sz/2-.17),(.085,h,.085),'M_Rust','PrisonCylinder',collision=False)
    for x,z in [(25,20),(25,27),(43,26)]:
        box_node('Service lamp post',yard,(x,2.8,z),(.09,5.6,.09),'M_DarkMetal')
        box_node('Service lamp head',yard,(x,5.5,z),(.35,.12,.22),'M_WarmLamp',False)
        light(lights,'Warm service lamp',(x,5.25,z),1.5,10,(1,.74,.48))
    for x in [24,39]:
        box_node('Laundry cart',yard,(x,.62,25),(1.1,.95,.72),'M_Metal')
        box_node('Laundry cloth pile',yard,(x,1.14,25),(.93,.25,.64),'M_Cloth',False)
    for i in range(9):box_node('Stacked service crate',yard,(40+(i%3)*.8,.4+(i//3)*.68,21),(.72,.64,.72),'M_Wood')
    sign(yard,'Service courtyard wayfinding',(21,1.6,12.6),'SERVICE COURT\nLAUNDRY · WORKSHOP',(3.6,.95),(0,270,0))
    # Perimeter barriers keep the expanded court within this chapter.
    for x,z,sx,sz in [(45,9,.25,70),(9,44,72,.25),(-27,4,.25,80),(9,-36,72,.25)]:
        box_node('Outer security wall',yard,(x,1.25,z),(sx,2.5,sz),'M_CoastRock')
    for x in range(-26,46,4):
        box_node('North fence post',yard,(x,3.4,44),(.08,1.8,.08),'M_Metal',False)
    for y in [2.8,3.6,4.15]:box_node('North fence wire',yard,(9,y,44),(72,.025,.025),'M_Rust',False)
    # Exterior roof and chimney silhouettes, plus rain-worn yard coping.
    box_node('Cell block roof cap',env,(0,3.74,-13),(23.7,.22,34.5),'M_DarkMetal',False)
    for z in [-22,-5]:box_node('Cell chimney',env,(7,4.5,z),(1.1,1.5,1.1),'M_Brick',False)
    for x in [-18.2,18.2]:box_node('Yard wall stone coping',env,(x,4.64,26),(.69,.18,28),'M_CoastRock',False)
    for z in [12,20,28,36]:
        box_node('West yard buttress',env,(-17.7,2.2,z),(.42,4.4,.65),'M_Brick',False)
    for x in [-12,-6,0,6,12]:box_node('North yard buttress',env,(x,2.2,39.94),(.65,4.4,.42),'M_Brick',False)
