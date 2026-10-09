"""Manual, deterministic authoring of Chapter 01. Preserves all Desert Shift assets.
Run with Python + NumPy/SciPy/Pillow; not required to play the already-saved scene.
"""
import copy, json, math, re, wave, io, os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter
import unity_writer as uw
from unity_writer import *
from geometry import *
from prison_character import create_character, BONES, PROFILES
import prison_details
import coastal_art
import prison_facilities
from build_project import make_camera, reflection
from world import light

uw.ART = 'Assets/Game/Art'
BASE = 'Assets/Game/'
SCENE = BASE + 'Scenes/SC_BlackstoneIsland.unity'
SCRIPT = BASE + 'Scripts/'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
colliders=[]

def texture(name, array, normal=False):
    path=BASE+'Textures/'+name+'.png'
    p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True)
    pixels=array.astype(np.uint8);unchanged=False
    if p.exists():
        try:
            with Image.open(p) as previous:unchanged=np.array_equal(np.array(previous),pixels)
        except Exception:pass
    if not unchanged:
        encoded=io.BytesIO();Image.fromarray(pixels).save(encoded,format='PNG');raw=encoded.getvalue()
        tmp=p.with_name(p.name+'.pending')
        with tmp.open('wb',buffering=0) as file:
            for index in range(0,len(raw),32768):
                data=raw[index:index+32768];offset=0
                while offset<len(data):offset+=file.write(data[offset:])
        assert tmp.stat().st_size==len(raw)
        with Image.open(tmp) as image:image.load()
        os.replace(tmp,p)
    meta(path,'TextureImporter',f'''  serializedVersion: 13
  mipmaps:
    mipMapMode: 0
    enableMipMap: 1
    sRGBTexture: {0 if normal else 1}
  isReadable: 0
  textureType: {1 if normal else 0}
  textureShape: 1
  maxTextureSize: 2048
  textureSettings:
    serializedVersion: 2
    filterMode: 1
    aniso: 4
    mipBias: 0
    wrapU: 0
    wrapV: 0
    wrapW: 0
  alphaIsTransparency: 1
  alphaUsage: 1
''')
    return path

def materials():
    rng=np.random.default_rng(716)
    h=512;noise=rng.normal(0,1,(h,h));long=gaussian_filter(noise,24)
    long=long/max(np.std(long),.001)
    stain=gaussian_filter(rng.uniform(0,1,(h,h)),14)
    stain=(stain-np.min(stain))/max(np.ptp(stain),.01)
    value=np.clip(135+noise*6+long*9-stain**3*35,65,200)
    concrete=np.stack([value*.9,value*.94,value],axis=-1)
    tex=texture('WeatheredConcrete',concrete)
    gy,gx=np.gradient(gaussian_filter(noise,1.2));normal=np.stack([128-gx*8,128-gy*8,np.full_like(gx,253)],axis=-1)
    norm=texture('WeatheredConcrete_Normal',normal,True)
    material('M_Concrete',[.7,.75,.8,1],.88,texture=tex,normal=norm,tiling=2)
    material('M_Floor',[.59,.64,.67,1],.70,texture=tex,normal=norm,tiling=5)
    material('M_Yard',[.62,.64,.60,1],.89,texture=tex,normal=norm,tiling=12)
    material('M_WallPaint',[.28,.38,.38,1],.8,texture=tex,normal=norm)
    material('M_Metal',[.34,.37,.4,1],.46,.75,texture='Assets/_DesertShift/Art/Textures/Metal_Base.png',normal='Assets/_DesertShift/Art/Textures/Metal_Normal.png')
    material('M_DarkMetal',[.085,.10,.12,1],.43,.65)
    material('M_Rust',[.24,.15,.095,1],.78,.5,texture='Assets/_DesertShift/Art/Textures/Metal_Base.png')
    material('M_Wood',[.33,.24,.16,1],.82,texture='Assets/_DesertShift/Art/Textures/Wood_Base.png',normal='Assets/_DesertShift/Art/Textures/Wood_Normal.png')
    material('M_Cloth',[.29,.34,.3,1],.91,texture='Assets/_DesertShift/Art/Textures/Cloth_Base.png',normal='Assets/_DesertShift/Art/Textures/Cloth_Normal.png')
    material('M_Ceramic',[.7,.73,.69,1],.19)
    material('M_Lamp',[.75,.91,1,1],.3,emission=[2.5,3.8,4.2,1])
    material('M_WarmLamp',[1,.73,.4,1],.3,emission=[3.2,1.8,.65,1])
    material('M_Glass',[.25,.42,.48,.2],.1,.1,transparent=True)
    material('M_Water',[.065,.17,.21,1],.13,.4)
    material('M_Paper',[.68,.62,.48,1],.94)
    material('M_Chrome',[.65,.68,.72,1],.17,.9)
    material('M_RV_Rubber',[.045,.047,.05,1],.84)
    material('M_EyeWhite',[.85,.84,.77,1],.18)
    material('M_Iris',[.14,.18,.16,1],.25)
    material('M_Hair',[.07,.047,.032,1],.83)
    material('M_Stubble',[.22,.17,.14,1],.92)
    skin=texture('Skin',np.stack([np.clip(177+noise*2,0,255),np.clip(128+noise*2,0,255),np.clip(101+noise*2,0,255)],axis=-1))
    material('M_CharacterSkin',[.92,.9,.89,1],.71,texture=skin)
    material('M_CharacterClothes',[.58,.54,.43,1],.91,texture='Assets/_DesertShift/Art/Textures/Cloth_Base.png',normal='Assets/_DesertShift/Art/Textures/Cloth_Normal.png')
    material('M_Shirt',[.27,.30,.29,1],.91,normal='Assets/_DesertShift/Art/Textures/Cloth_Normal.png')
    material('M_Trousers',[.27,.29,.3,1],.91,texture='Assets/_DesertShift/Art/Textures/Cloth_Base.png',normal='Assets/_DesertShift/Art/Textures/Cloth_Normal.png')
    material('M_GuardUniform',[.12,.19,.27,1],.87,texture='Assets/_DesertShift/Art/Textures/Cloth_Base.png')
    material('M_RivalUniform',[.28,.23,.20,1],.91,texture='Assets/_DesertShift/Art/Textures/Cloth_Base.png')
    material('M_BrotherClothes',[.27,.38,.45,1],.89,texture='Assets/_DesertShift/Art/Textures/Cloth_Base.png')
    im=Image.new('RGBA',(256,256),(0,0,0,0));d=ImageDraw.Draw(im)
    for x in (62,114,166): d.rectangle((x,52,x+24,194),fill=(17,44,66,230))
    d.line([(35,190),(130,35),(220,190)],fill=(17,44,66,230),width=10)
    tt=texture('BlueMeridianTattoo',np.array(im))
    material('M_Tattoo',[1,1,1,1],.96,texture=tt,transparent=True)

def sign(parent,name,position,text,size=(1.7,.6),rotation=(0,0,0)):
    key='Sign_'+name
    if key not in MATERIALS:
        im=Image.new('RGB',(768,256),(27,41,49));d=ImageDraw.Draw(im)
        d.rectangle((7,7,760,248),outline=(170,151,109),width=5)
        font=ImageFont.truetype(FONT,52 if len(text)<23 else 38)
        d.multiline_text((384,128),text,font=font,fill=(221,218,195),anchor='mm',align='center',spacing=12)
        tex=texture(key,np.array(im));material(key,[1,1,1,1],.82,texture=tex)
    return mesh_node(name,parent,position,(size[0],size[1],1),key,'SignPlane',rotation,False)

def mesh_node(name,parent,pos,size,mat,mesh='PrisonBox',rot=(0,0,0),collision=False,static=True):
    n=Node(name,parent,pos,rot,size,static=static).render(mesh,mat)
    if collision:
        n.boxcollider()
        if rot==(0,0,0):
            from scipy.spatial.transform import Rotation
            wm=np.eye(4);chain=[];parent_n=n
            while parent_n is not None:chain.append(parent_n);parent_n=parent_n.parent
            for node in reversed(chain):
                lm=np.eye(4);lm[:3,:3]=Rotation.from_euler('xyz',node.rot,degrees=True).as_matrix()@np.diag(node.scale);lm[:3,3]=node.pos;wm=wm@lm
            colliders.append((name,wm[:3,3],np.abs(wm[:3,:3])@np.ones(3)))
    return n

def box_node(name,parent,pos,size,mat='M_Concrete',collision=True,static=True):
    return mesh_node(name,parent,pos,size,mat,collision=collision,static=static)

def target(parent,kind,pos=(0,0,0),size=(.5,.6,.5),offset=(0,0,0)):
    n=Node('Interact_'+kind,parent,pos,static=False); n.boxcollider(size)
    enum=['CellDoor','Reader','Cook','Fixer','DroppedKnife','Niko','Leader','Tattooist','CellStash','Phone','Rival','SolitaryBed','SolitaryDoor','Brother','Reflection','Training'].index(kind)
    cid=n.script(SCRIPT+'Interaction/StoryInteractable.cs',f'  director: {{fileID: {DIRECTOR}}}\n  target: {enum}\n  promptOffset: {vec(offset)}\n')
    TARGETS.append(cid);return n

def barred_leaf(name,parent,position,main_target=None):
    hinge=Node(name,parent,position,static=False)
    leaf=Node('Welded barred leaf',hinge,(0,0,.575),static=False).render('DoorBars','M_Metal')
    leaf.boxcollider((.10,2.45,1.15),(0,1.22,0))
    box_node('Lock housing',leaf,(0,1.05,.41),(.18,.18,.16),'M_DarkMetal',False,False)
    if main_target: target(hinge,main_target,(0,1.1,.58),(.22,2.1,1.05))
    return hinge

def cell(parent,index,z,main=False):
    g=Node('Cell B-'+str(index).zfill(2),parent)
    box_node('Back wall',g,(-10.2,1.75,z),( .35,3.5,4.1))
    box_node('Partition',g,(-7.15,1.75,z-2),(6.3,3.5,.22))
    # Real front gap for the operable leaf; fixed bars do not cross that gap.
    for dz in [-1.31,1.31]:
        mesh_node('Fixed cell bars',g,(-4,0,z+dz),(1,1,1),'M_Metal','FixedBars',collision=False)
        box_node('Fixed bars collision',g,(-4,1.3,z+dz),(.11,2.6,1.42),'M_DarkMetal',True)
        # Only render rods, not the collision slab.
        Node.all[-1].parts=[p for p in Node.all[-1].parts if p[0]!=23 and p[0]!=33]
    door=barred_leaf('B-'+str(index).zfill(2)+' barred door',g,(-4,0,z-.575),'CellDoor' if main else None)
    box_node('Door lintel',g,(-4,2.88,z),(.38,.45,4),'M_WallPaint')
    for x in [-9.1,-8.1]:
        for dz in [-1,.95]: mesh_node('Bed leg',g,(x,.22,z+dz),(.035,.44,.035),'M_Metal',collision=False)
    box_node('Bed frame',g,(-8.6,.37,z),(1.2,.13,2.15),'M_Metal',False)
    box_node('Worn mattress',g,(-8.6,.5,z),(1.16,.19,2.07),'M_Cloth')
    box_node('Pillow',g,(-8.6,.64,z+.71),(.77,.13,.43),'M_Cloth',False)
    box_node('Folded blanket',g,(-8.6,.67,z-.65),(1.1,.13,.59),'M_WallPaint',False)
    box_node('Steel table',g,(-5.9,.73,z+1.4),(1.25,.1,.65),'M_Metal')
    box_node('Stool',g,(-5.9,.37,z+.9),(.4,.7,.4),'M_Wood')
    mesh_node('Toilet bowl',g,(-9.15,.29,z-1.35),(.63,.4,.74),'M_Ceramic','PrisonSphere',collision=False)
    box_node('Toilet tank',g,(-9.37,.63,z-1.56),(.23,.62,.47),'M_Ceramic',False)
    mesh_node('Sink',g,(-9.72,.87,z+1.2),(.49,.22,.56),'M_Ceramic','PrisonSphere',collision=False)
    box_node('Mirror',g,(-9.98,1.51,z+1.2),(.04,.48,.40),'M_Chrome',False)
    sign(g,'B'+str(index),(-3.77,2.6,z),f'B-{index:02d}',(.68,.25),(0,90,0))
    box_node('Letter',g,(-5.88,.80,z+1.39),(.25,.014,.18),'M_Paper',False)
    if main:
        target(g,'CellStash',(-8.55,.7,z-.2),(.45,.24,.6))
        target(g,'Reflection',(-5.9,.70,z+.89),(.4,.75,.4))
    return door

def actor_fields(anim,bones,name,drive=True):
    txt=f'  displayName: {name}\n  animator: {{fileID: {anim}}}\n  driveLocomotion: {int(drive)}\n'
    for field,bone in [('head','Head'),('jaw','Jaw'),('chest','Chest'),('rightArm','RightUpperArm'),('rightForearm','RightLowerArm'),('leftArm','LeftUpperArm'),('leftForearm','LeftLowerArm')]:
        txt+=f'  {field}: {{fileID: {bones[bone].tid}}}\n'
    return txt

def clone_model(root,parent,name,uniform=None):
    old_nodes=[]
    def visit(n):
        old_nodes.append(n)
        for c in n.children:visit(c)
    visit(root)
    copies={};ids={}
    for old in old_nodes:
        new=Node(name if old==root else old.name,copies.get(old.parent,parent),old.pos,old.rot,old.scale,layer=0,static=False)
        new.mesh=old.mesh;new.mat=old.mat;copies[old]=new
        ids[old.id]=new.id;ids[old.tid]=new.tid
        for cls,cid,body in old.parts:
            if cls==114 and guid('Assets/_DesertShift/Scripts/Player/PlayerAnimator.cs') in body: continue
            new_cid=new.component(cls,body);ids[cid]=new_cid
    for old,new in copies.items():
        fresh=[]
        for cls,cid,body in new.parts:
            body=re.sub(r'\{fileID: (\d+)\}',lambda m:'{fileID: '+str(ids.get(int(m[1]),int(m[1])))+'}',body)
            if uniform and cls==137:
                body=body.replace(ref(MATERIALS['M_CharacterClothes'],2100000),ref(MATERIALS[uniform],2100000))
            fresh.append((cls,cid,body))
        new.parts=fresh
        if hasattr(old,'skinBones'):new.skinBones=[ids[x] for x in old.skinBones]
        if uniform and new.mat=='M_CharacterClothes':new.mat=uniform
    bones={n.name:n for n in copies.values() if n.name in [b[0] for b in BONES]}
    visual=copies[root]; anim=next(cid for cls,cid,body in visual.parts if cls==95)
    return visual,bones,anim

def npc(parent,name,position,yaw,kind=None,uniform=None,scale=1,profile='Niko',pose=0,route=None):
    root=Node(name,parent,position,(0,yaw,0),layer=9,static=False)
    w=PROFILES[profile][0];root.boxcollider((.43*min(w,1.25),1.76,.42*min(w,1.25)),(0,.88,0))
    visual,bones=create_character(root,0,profile)
    anim=next(cid for cls,cid,body in visual.parts if cls==95)
    fields=actor_fields(anim,bones,name)+f'  pose: {pose}\n'
    if route:fields+='  patrolEnabled: 1\n  patrol:\n'+''.join('  - '+vec(p)+'\n' for p in route)
    aid=root.script(SCRIPT+'AI/PrisonActor.cs',fields)
    foot_fields='  locomotion: {fileID: '+str(next(cid for cls,cid,body in visual.parts if guid(SCRIPT+'Actors/PrisonLocomotion.cs') in body))+'}\n'
    for category in ['concrete','metal']:
        foot_fields+='  '+category+':\n'+''.join('  - '+ref(BASE+'Audio/Footstep_'+category+'_'+str(i)+'.wav',8300000,3)+'\n' for i in range(4))
    root.script(SCRIPT+'Audio/PrisonFootsteps.cs',foot_fields)
    if kind:
        enum=['CellDoor','Reader','Cook','Fixer','DroppedKnife','Niko','Leader','Tattooist','CellStash','Phone','Rival','SolitaryBed','SolitaryDoor','Brother','Reflection','Training'].index(kind)
        tid=root.script(SCRIPT+'Interaction/StoryInteractable.cs',f'  director: {{fileID: {DIRECTOR}}}\n  target: {enum}\n  promptOffset: {{x: 0, y: 1, z: 0}}\n')
        TARGETS.append(tid)
    if profile=='Guard':
        mesh_node('Guard cap',bones['Head'],(0,.13,0),(.21,.04,.21),'M_GuardUniform','PrisonSphere',collision=False,static=False)
        box_node('Guard brim',bones['Head'],(0,.115,.08),(.17,.012,.13),'M_GuardUniform',False,False)
        box_node('Badge',bones['Chest'],(-.10,0,.12),(.027,.045,.008),'M_Chrome',False,False)
    return root,aid,bones

def authored_scene():
    global DIRECTOR,TARGETS,PLAYER_VISUAL
    Node.all=[];Node.counter=1000;TARGETS=[];colliders.clear()
    game=Node('_BlackstoneChapter01',static=False);env=Node('_PrisonArchitecture');lights=Node('_Lighting',static=False)
    mission=Node('Chapter 01 Story Director',game,static=False)
    DIRECTOR=mission.script(SCRIPT+'Missions/PrisonStoryDirector.cs')
    box_node('Island playable ground',env,(8,-.2,6),(76,.4,94),'M_Yard')
    mesh_node('Ocean',env,(0,-7,0),(1300,1,1300),'M_Water','PrisonPlane',collision=False)
    mesh_node('Island rock foundation',env,(8,-9.7,6),(93,19,115),'M_Concrete','PrisonSphere',collision=False)
    box_node('Cell block floor',env,(0,.02,-13),(23,.15,34),'M_Floor')
    box_node('Cell block east wall',env,(11.5,1.8,-13),(.42,3.6,34))
    box_node('Cell block south wall',env,(0,1.8,-30),(23,3.6,.42))
    box_node('Cell block roof',env,(0,3.5,-13),(23,.3,34),'M_Concrete')
    for i in range(8):
        door=cell(env,i+1,-27+i*4,i==3)
        if i==3:cell_door=door
        # Right-hand locked cell fronts and depth partitions.
        mesh_node('Opposite cell bars',env,(4,0,-27+i*4),(1,1,2.8),'M_Metal','FixedBars',collision=False)
        box_node('Locked opposite cell collision',env,(4,1.3,-27+i*4),(.1,2.6,4),'M_Concrete')
        Node.all[-1].parts=[p for p in Node.all[-1].parts if p[0]!=23 and p[0]!=33]
        box_node('Opposite cell partition',env,(7.7,1.8,-29+i*4),(7.5,3.5,.24))
        box_node('Opposite mattress',env,(9,.52,-27+i*4),(1.2,.23,2),'M_Cloth')
    for z in [-26,-18,-10,-2]:
        box_node('Fluorescent fixture',env,(0,3.22,z),(2.2,.1,.2),'M_DarkMetal',False)
        box_node('Fluorescent diffuser',env,(0,3.15,z),(1.9,.06,.14),'M_Lamp',False)
        light(lights,'Cell corridor lamp',(0,2.9,z),3.0,10,(.93,.94,.90))
        mesh_node('Overhead conduit',env,(3.45,3.1,z),( .06,.06,7.8),'M_DarkMetal',collision=False)
    sign(env,'BBlock',(0,2.7,3),'CELL BLOCK B\nYARD ACCESS', (3.2,.95),(0,180,0))
    # Keep the main access opening unobstructed.
    for x in [-8,8]:box_node('Cell block north wall',env,(x,1.8,4),(8,3.6,.3))
    box_node('Yard surface',env,(0,-.03,23),(36,.12,34),'M_Yard')
    for x in [-18.2,18.2]:box_node('Perimeter side wall',env,(x,2.3,23),(.5,4.6,35))
    box_node('North perimeter wall',env,(0,2.3,40.3),(37,4.6,.5))
    for x in [-11,11]:box_node('South perimeter wall',env,(x,2.3,6),(14,4.6,.5))
    # Connection to eastern visitation and solitary corridor through a real opening.
    for index,(name,pos,size) in enumerate(colliders):
        if name=='Perimeter side wall' and pos[0]>0:
            # Replace the east collider/wall with two pieces around z=7..12.
            for n in Node.all:
                if n.name==name and n.pos==list(pos):n.active=False
    colliders[:]=[(name,pos,size) for name,pos,size in colliders if not (name=='Perimeter side wall' and pos[0]>0)]
    box_node('East yard wall north',env,(18.2,2.3,26.5),(.5,4.6,28))
    box_node('East yard wall south',env,(18.2,2.3,6.2),(.5,4.6,.4))
    box_node('Eastern corridor floor',env,(22,.0,-9),(10,.16,43),'M_Floor')
    box_node('Eastern corridor west wall',env,(18,1.8,-12),(.3,3.6,36))
    box_node('Eastern corridor roof',env,(23,3.6,-9),(10,.2,43))
    sign(env,'Isolation',(22,2.4,-7),'SEGREGATION\nVISITS BY ORDER',(2.9,.8),(0,180,0))
    # Both combatants have separate, physically enclosed solitary cells.
    for centre in [-22.5,-14.5]:
        box_node('Solitary back wall',env,(36.2,1.8,centre),(.35,3.6,8))
        for dz in [-4,4]:box_node('Solitary partition',env,(32,1.8,centre+dz),(8,3.6,.28))
        for dz in [-2.3,2.3]:box_node('Solitary front wall',env,(28,1.8,centre+dz),(.3,3.6,3.1))
        sd=barred_leaf('Solitary door',env,(28,0,centre-.575),'SolitaryDoor' if centre==-22.5 else None)
        box_node('Solitary lintel',env,(28,3.03,centre),(.35,1,1.3))
        box_node('Solitary bed frame',env,(33.4,.34,centre-.9),(1.2,.18,2.2),'M_Metal')
        box_node('Solitary mattress',env,(33.4,.5,centre-.9),(1.18,.17,2.1),'M_Cloth',False)
        box_node('Solitary roof',env,(32,3.65,centre),(8,.2,8))
        light(lights,'Solitary recessed lamp',(32,3.1,centre),2.4,8,(1,.92,.78))
        if centre==-22.5:
            solitary_door=sd;target(env,'SolitaryBed',(33.4,.68,centre-.9),(1,.4,2))
    # Visitation booth: interact with the near-side receiver, not through the glass.
    box_node('Visitation floor',env,(30,.02,-1),(14,.15,9),'M_Floor')
    box_node('Visitation roof',env,(30,3.6,-1),(14,.22,9))
    box_node('Visit back wall',env,(37,1.8,-1),(.3,3.6,9))
    for z in [-5.5,3.5]:box_node('Visit partition',env,(30,1.8,z),(14,3.6,.3))
    box_node('Visitation counter',env,(29,1,-1.5),(.5,.12,3),'M_Wood')
    mesh_node('Visitation glass',env,(29,1.97,-1.5),(.08,1.88,3),'M_Glass',collision=True)
    for x in [27.6,30.5]:box_node('Visitation chair',env,(x,.47,-1.5),(.6,.75,.57),'M_Metal')
    box_node('Telephone receiver',env,(28.5,1.12,-1.5),(.11,.09,.34),'M_DarkMetal',False)
    target(env,'Brother',(28.4,1.17,-1.5),(.3,.23,.55))
    light(lights,'Visitation fluorescent',(28,3,-1),3.4,12,(.93,.96,1))
    sign(env,'VisitRules',(36.76,2,-1),'VISITATION\nNO PHYSICAL CONTACT',(2.5,.8),(0,-90,0))
    # Yard props: recognizable social landmarks, tables, benches, vents and cameras.
    for x,z in [(-10,24),(-8,12),(12,9),(13,32),(-12,10)]:
        box_node('Yard bench',env,(x,.47,z-1), (2,.14,.46),'M_Wood')
        for dx in [-.7,.7]:box_node('Bench support',env,(x+dx,.25,z-1),(.13,.5,.3),'M_Metal')
    box_node('Gang table',env,(-10,.74,26.2),(2,.14,1.1),'M_Wood')
    for x in [-10.7,-9.3]:box_node('Table support',env,(x,.38,26.2),(.09,.7,.9),'M_Metal')
    box_node('Meal cart',env,(12,.64,10.3),(1.4,.65,.7),'M_Metal')
    for x in [11.5,12.5]:
        for z in [10.05,10.55]:mesh_node('Cart wheel',env,(x,.19,z),(.16,.16,.12),'M_RV_Rubber','PrisonSphere',collision=False)
    box_node('Tray stack',env,(12,.99,10.3),(.8,.06,.45),'M_Chrome',False)
    box_node('Workshop bench',env,(13,.8,33.4),(1.8,.16,.7),'M_Wood')
    box_node('Tool cabinet',env,(14.2,.5,33.5),(.6,1,.65),'M_WallPaint')
    box_node('Tattoo table',env,(-12,.75,11.3),(1.3,.12,.65),'M_Wood')
    sign(env,'BlueMeridian',(-12,1.8,11.7),'BLUE MERIDIAN',(1.5,.4),(0,180,0))
    mesh_node('Training bag',env,(-2,1.5,30),(.47,1.4,.47),'M_Cloth','PrisonCylinder',collision=False)
    target(env,'Training',(-2,1.5,30),(.5,1.4,.5))
    box_node('Training frame',env,(-2,2.85,30),(2,.12,.12),'M_Metal')
    for x in [-3,-1]:box_node('Training upright',env,(x,1.4,30),(.12,2.8,.12),'M_Metal')
    for x in [-17,17]:
        box_node('Tower support',env,(x,2.6,39),(2.4,5.2,2.4),'M_WallPaint')
        box_node('Tower platform',env,(x,5.4,39),(4,.35,4),'M_Concrete')
        box_node('Tower roof',env,(x,7.45,39),(4,.25,4),'M_Metal')
        for dx in [-1.6,1.6]:
            for dz in [-1.6,1.6]:box_node('Tower post',env,(x+dx,6.4,39+dz),(.12,2,.12),'M_Metal')
        light(lights,'Yard floodlight',(x,6.8,36),7.5,32,(.68,.8,1),0,(45,0,0),0)
    for z in [11,29]:
        mesh_node('Camera housing',env,(17.7,3.4,z),(.24,.18,.44),'M_Ceramic',rot=(0,-90,0),collision=False)
        mesh_node('Camera lens',env,(17.43,3.4,z),(.08,.08,.04),'M_DarkMetal','PrisonSphere',collision=False)
    # Rebuilt prisoner model and procedural locomotion; old demo is not the main scene.
    player=Node('Player',game,(-7,.11,-15),(0,90,0),layer=8,static=False)
    player.component(143,collider_base()+'''  serializedVersion: 3
  m_Height: 1.78
  m_Radius: 0.25
  m_SlopeLimit: 46
  m_StepOffset: 0.3
  m_SkinWidth: 0.035
  m_MinMoveDistance: 0
  m_Center: {x: 0, y: 0.89, z: 0}
''')
    inp=player.script('PlayerInputHandler');ct=Node('CameraTarget',player,(0,1.45,0),layer=8,static=False)
    movement=player.script('PlayerMovement',f'  cameraTarget: {{fileID: {ct.tid}}}\n')
    interaction=player.script('PlayerInteractor')
    PLAYER_VISUAL,bones=create_character(player,movement)
    anim=next(cid for cls,cid,body in PLAYER_VISUAL.parts if cls==95)
    foot_fields='  locomotion: {fileID: '+str(next(cid for cls,cid,body in PLAYER_VISUAL.parts if guid(SCRIPT+'Actors/PrisonLocomotion.cs') in body))+'}\n'
    for category in ['concrete','metal']:
        foot_fields+='  '+category+':\n'+''.join('  - '+ref(BASE+'Audio/Footstep_'+category+'_'+str(i)+'.wav',8300000,3)+'\n' for i in range(4))
    player.script(SCRIPT+'Audio/PrisonFootsteps.cs',foot_fields)
    player_actor=player.script(SCRIPT+'AI/PrisonActor.cs',actor_fields(anim,bones,'Elias Vale',False))
    # Tattoo follows the forearm bone and survives all locomotion and save/load.
    tattoo=mesh_node('Blue Meridian forearm tattoo',bones['LeftLowerArm'],(-.10,.045,.027),(.12,.043,1),'M_Tattoo','SignPlane',rot=(0,0,90),collision=False,static=False)
    tattoo.active=False
    conceal_prop=mesh_node('Knife concealment prop',bones['RightHand'],(0,0,.09),(1,1,1),'M_Chrome','Knife',collision=False,static=False)
    conceal_prop.active=False
    # Export native player and model prefabs with local file references.
    model_path=save_prefab(PLAYER_VISUAL,'Characters','PF_EliasVale_Model')
    player_path=save_prefab(player,'Characters','PF_EliasVale_Player')
    for src in [model_path,player_path]:
        content=(ROOT/src).read_text()
        if 'Model' in src:content=content.replace(f'  movement: {{fileID: {movement}}}', '  movement: {fileID: 0}')
        dst=BASE+'Prefabs/Characters/'+Path(src).name;write(dst,content);meta(dst,'PrefabImporter')
        (ROOT/src).unlink();(ROOT/(src+'.meta')).unlink()
    actors=Node('_PrisonPopulation',static=False)
    niko,ni,niko_bones=npc(actors,'Niko Serrin',(6,.02,21),185,'Niko',profile='Niko')
    held_knife=mesh_node('Niko held knife',niko_bones['RightHand'],(0,0,.09),(1,1,1),'M_Chrome','Knife',collision=False,static=False)
    held_knife.active=False
    leader,le,_=npc(actors,'Malik Reed',(-10,.02,24.5),160,'Leader',profile='Malik')
    rival,ri,_=npc(actors,'Iron Rooks rival',(7.7,.02,21.5),225,'Rival',profile='Rival')
    guard,gu,_=npc(actors,'Officer Harrow',(6,.02,33),180,profile='Guard')
    for idx,(cls,cid,body) in enumerate(guard.parts):
        if cid==gu:
            body+='  patrolEnabled: 1\n  patrol:\n'+''.join('  - '+vec(p)+'\n' for p in [(6,.02,33),(-9,.02,33),(-9,.02,8),(10,.02,8)])
            guard.parts[idx]=(cls,cid,body)
    bro,br,_=npc(actors,'Theo Vale',(31,.02,-1.5),270,profile='Brother')
    rafi,ta,_=npc(actors,'Rafi',(-12,.02,10),155,'Tattooist',profile='Rafi')
    tomas,tomas_id,_=npc(actors,'Tomas',(-8,.02,12),150,'Reader',profile='Lean')
    samir,samir_id,_=npc(actors,'Samir',(12,.02,9),210,'Cook',profile='Heavy')
    jonah,jonah_id,_=npc(actors,'Workshop contact',(13,.02,32),225,'Fixer',profile='Athletic')
    for name,profile,p,yaw,route in [
        ('Luis','Lean',(-15,.02,27),180,[(-15,.02,27),(-15,.02,18),(-12,.02,18),(-12,.02,27)]),
        ('Andre','Athletic',(3,.02,12),20,[(3,.02,12),(3,.02,29),(0,.02,29),(0,.02,12)]),
        ('Benny','Heavy',(13,.02,25),90,[(13,.02,25),(13,.02,17),(10,.02,17),(10,.02,25)]),
        ('Yusef','Rafi',(-3,.02,36),95,[(-3,.02,36),(4,.02,36),(4,.02,33),(-3,.02,33)])]:
        npc(actors,name,p,yaw,profile=profile,route=route)
    npc(actors,'Leon',(-12,.02,32),170,profile='Athletic',pose=11)
    npc(actors,'Dario',(13,.02,29),265,profile='Heavy')
    poker,talk=prison_details.tables(env,box_node,mesh_node,sign)
    players=[]
    for name,profile,p,yaw in [('Samir table friend','Heavy',(-6.59,.02,18.93),0),('Moses','Athletic',(-5.41,.02,21.07),180),('Owen','Lean',(-6.59,.02,21.07),180)]:
        _,a,_=npc(actors,name,p,yaw,profile=profile,pose=9);players.append(a)
    poker_seat=Node('Player poker seat',env,(-5.41,.02,18.93),(0,0,0),static=False)
    talk_seat=Node('Player conversation seat',env,(-6.48,.02,13.59),(0,0,0),static=False)
    poker.script(SCRIPT+'Activities/PrisonPokerTable.cs',f'  director: {{fileID: {DIRECTOR}}}\n  playerSeat: {{fileID: {poker_seat.tid}}}\n  players:\n'+''.join(f'  - {{fileID: {a}}}\n' for a in players))
    talk.script(SCRIPT+'Activities/PrisonConversationTable.cs',f'  director: {{fileID: {DIRECTOR}}}\n  playerSeat: {{fileID: {talk_seat.tid}}}\n')
    npc(actors,'Eddie',(-7.52,.02,15.41),180,profile='Lean',pose=8)
    npc(actors,'Jamal',(-6.48,.02,15.41),180,profile='Athletic',pose=8)
    npc(actors,'Peter',(-7.52,.02,13.59),0,profile='Heavy',pose=10)
    prison_details.decorate(env,lights,box_node,mesh_node,sign,light)
    coastal_art.enrich(env,lights,box_node,mesh_node,sign,light)
    prison_facilities.expand(env,lights,box_node,mesh_node,sign,light,colliders)
    coastal_art.physical_uvs()
    actors.script(SCRIPT+'AI/PrisonPopulation.cs',f'  director: {{fileID: {DIRECTOR}}}\n  contacts:\n'+''.join(f'  - {{fileID: {i}}}\n' for i in [tomas_id,samir_id,jonah_id,ni,le])+'  lineIds:\n'+''.join('  - '+i+'\n' for i in ['ambient_tomas_01','ambient_samir_01','ambient_jonah_01','ambient_niko_01','ambient_malik_01']))
    knife=mesh_node('Dropped knife',env,(6.25,.025,20.0),(1,1,1),'M_Chrome','Knife',rot=(0,23,0),collision=False,static=False)
    target(knife,'DroppedKnife',(0,.15,0),(.55,.4,.65));knife.active=False
    stash=mesh_node('Knife stored under mattress',env,(-8.55,.38,-15.2),(1,1,1),'M_Chrome','Knife',collision=False,static=False);stash.active=False
    phone=mesh_node('Gang phone',env,(5.5,.94,21),(.09,.16,.022),'M_DarkMetal',collision=False,static=False);phone.active=False
    target(env,'Phone',(5.5,.94,21),(.45,.55,.45))
    cam,camid=make_camera(game);cam.pos=[-4.8,2,-13.8];cam.rot=[10,230,0]
    rig=Node('Cinemachine Camera Rig',game,static=False)
    rig_id=rig.script('ThirdPersonCameraController',f'  followTarget: {{fileID: {ct.tid}}}\n  input: {{fileID: {inp}}}\n  initialYaw: 90\n  initialPitch: 12\n  fieldOfView: 58\n')
    anchors=Node('_StoryAnchors',static=False)
    spawns={}
    for key,pos,yaw in [('cellSpawn',(-7,.11,-15),90),('yardSpawn',(5,.04,18),25),('solitarySpawn',(30,.03,-22.5),270),('visitSpawn',(26.5,.11,-1.5),90),('sleepPosition',(33.4,.05,-23.4),0)]:
        spawns[key]=Node(key,anchors,pos,(0,yaw,0),static=False)
    shot_data=[]
    for key,pos,focus in [
        ('cell',(-4.8,2,-13.75),(-7.5,1.1,-15)),('yard',(3,2.6,16.5),(6.6,1.1,21)),
        ('niko',(3.5,1.85,19),(6,1.25,21)),('leader',(-7,1.85,22),(-10,1.25,24.5)),
        ('tattoo',(-9.6,1.85,8.7),(-12,1.15,10)),('cook',(9.5,1.8,7),(12,1.2,9)),
        ('reader',(-5.6,1.85,10),(-8,1.2,12)),
        ('fixer',(10.8,1.8,30),(13,1.2,32)),('solitary',(28.7,2.1,-20),(32,1,-22.6)),
        ('door',(31.1,1.7,-22.4),(26.5,1.2,-22.5)),
        ('visit',(26,1.8,-3.1),(31,1.3,-1.5))]:
        c=Node('Shot_'+key,anchors,pos,static=False);f=Node('Focus_'+key,anchors,focus,static=False)
        shot_data.append((key,c,f))
    aud=Node('Chapter audio',game,static=False)
    fields={'success':'MissionComplete','missed':'Missed','knifeDrop':'KnifeDrop','clothHide':'ClothHide','tattooBuzz':'TattooBuzz','phoneRing':'PhoneRing','phoneClick':'PhoneClick','punch':'Punch','whistle':'Whistle','metalDoor':'MetalDoor','doorKnock':'DoorKnock','sob':'Sob','cellAmbience':'CellAmbience','yardAmbience':'YardAmbience','tension':'Tension','cardShuffle':'CardShuffle','cardDeal':'CardDeal'}
    audio_id=aud.script(SCRIPT+'Audio/PrisonAudio.cs',''.join(f'  {key}: {ref(BASE+"Audio/"+name+".wav",8300000,3)}\n' for key,name in fields.items()))
    sun,sun_id=light(lights,'Late afternoon sun',(0,70,0),2.0,1000,(1,.94,.82),1,(43,-28,0),2)
    volume=Node('Prison cinematic grade',lights,static=False);volume.script('DesertAtmosphere','  prisonNight: 1\n')
    reflection(lights,'Cell reflection',(0,1.8,-14),(20,4,32));reflection(lights,'Yard reflection',(0,2,23),(36,7,34))
    bootstrap=Node('GameBootstrap',game,static=False)
    night_mat=BASE+'Art/Materials/M_BlackstoneSky.mat'
    sky_text=(ROOT/'Assets/_DesertShift/Art/Materials/M_DesertSky.mat').read_text().replace('M_DesertSky','M_BlackstoneSky')
    sky_text=sky_text.replace(guid('Assets/_DesertShift/Art/Materials/DesertSky.shader'),guid('Assets/Game/Shaders/CoastalSky.shader'))
    sky_text=sky_text.replace('{r: 0.18, g: 0.40, b: 0.59, a: 1}', '{r: 0.24, g: 0.43, b: 0.62, a: 1}').replace('{r: 0.70, g: 0.76, b: 0.69, a: 1}', '{r: 0.77, g: 0.80, b: 0.78, a: 1}')
    write(night_mat,sky_text);meta(night_mat,'NativeFormatImporter','  mainObjectFileID: 2100000\n')
    bootstrap.script('GameBootstrap',f'''  renderPipeline: {ref('Assets/_DesertShift/Settings/DesertShift_URP.asset',11400000)}
  rendererData: {ref('Assets/_DesertShift/Settings/DesertShift_Renderer.asset',11400000)}
  skyMaterial: {ref(night_mat,2100000)}
  sun: {{fileID: {sun_id}}}
  playerInput: {{fileID: {inp}}}
  prisonNight: 1
''')
    refs={'player':movement,'input':inp,'interactor':interaction,'cameraRig':rig_id,'mainCamera':camid,'audioBus':audio_id,
          'playerActor':player_actor,'niko':ni,'leader':le,'rival':ri,'guard':gu,'brother':br,'tattooist':ta,
          'cellDoor':cell_door.tid,'solitaryDoor':solitary_door.tid,'playerVisual':PLAYER_VISUAL.tid,
          'droppedKnife':knife.id,'stashedKnife':stash.id,'tattooMark':tattoo.id,'phoneProp':phone.id}
    refs.update(nikoHeldKnife=held_knife.id,concealKnifeProp=conceal_prop.id,nikoHand=niko_bones['RightHand'].tid)
    refs.update({k:v.tid for k,v in spawns.items()})
    body=''.join(f'  {k}: {{fileID: {v}}}\n' for k,v in refs.items())+'  fightAtSeconds: 240\n  targets:\n'+''.join(f'  - {{fileID: {t}}}\n' for t in TARGETS)
    body+='  shots:\n'+''.join(f'  - id: {key}\n    camera: {{fileID: {c.tid}}}\n    focus: {{fileID: {f.tid}}}\n' for key,c,f in shot_data)
    cls,cid,initial=mission.parts[0];mission.parts[0]=(cls,cid,initial+body)
    Node('Chapter HUD',game,static=False).script(SCRIPT+'UI/PrisonHUD.cs',f'  director: {{fileID: {DIRECTOR}}}\n')
    old=(ROOT/'Assets/_DesertShift/Scenes/SC_DesertTown.unity').read_text()
    settings=old[len(HEAD):old.index('--- !u!1 &')]
    settings=re.sub(r'm_Sun: \{fileID: \d+\}',f'm_Sun: {{fileID: {sun_id}}}',settings)
    settings=re.sub(r'm_SkyboxMaterial: \{[^}]+\}',f'm_SkyboxMaterial: {ref(night_mat,2100000)}',settings)
    for field,color in [('m_AmbientSkyColor',[.43,.50,.58,1]),('m_AmbientEquatorColor',[.30,.29,.25,1]),('m_AmbientGroundColor',[.18,.18,.16,1]),('m_FogColor',[.65,.69,.68,1])]:
        settings=re.sub(field+r': \{[^}]+\}',field+': '+col(color),settings)
    # Existing settings block is preserved; runtime bootstrap supplies the prison grade.
    text=HEAD+settings+''.join(node_yaml(n) for n in Node.all)
    text+='--- !u!1660057539 &9223372036854775807\nSceneRoots:\n  m_ObjectHideFlags: 0\n  m_Roots:\n'+''.join(f'  - {{fileID: {n.tid}}}\n' for n in Node.all if not n.parent)
    write(SCENE,text);meta(SCENE)
    for n in Node.all:
        data={'name':n.name,'id':n.id,'parent':n.parent.id if n.parent else 0,'pos':n.pos,'rot':n.rot,'scale':n.scale,'active':n.active}
        if n.mesh:data.update(mesh=n.mesh,mat=n.mat,rendered=any(p[0] in [23,137] for p in n.parts))
        if hasattr(n,'skinBones'):data['skinBones']=n.skinBones
        PREVIEW['nodes'].append(data)
    write('Documentation/BlackstoneAuthoring.json',json.dumps(PREVIEW,separators=(',',':')))
    write('Documentation/BlackstoneColliders.json',json.dumps([(n,p.tolist(),s.tolist()) for n,p,s in colliders]))
    write('ProjectSettings/EditorBuildSettings.asset',HEAD+f'''--- !u!1045 &1
EditorBuildSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 2
  m_Scenes:
  - enabled: 1
    path: {SCENE}
    guid: {guid(SCENE)}
  - enabled: 0
    path: Assets/_DesertShift/Scenes/SC_DesertTown.unity
    guid: {guid('Assets/_DesertShift/Scenes/SC_DesertTown.unity')}
  m_configObjects: {{}}
''')
    settings_file=ROOT/'ProjectSettings/ProjectSettings.asset';s=settings_file.read_text();s=s.replace('productName: Desert Shift','productName: The Silent Blueprint - Blackstone Island');s=re.sub(r'(?m)^(\s*bundleVersion:) .*$',r'\1 0.4.1',s);settings_file.write_text(s)
    manifest_file=ROOT/'Packages/manifest.json';manifest=json.loads(manifest_file.read_text());manifest['dependencies']['com.unity.modules.vehicles']='1.0.0';manifest_file.write_text(json.dumps(manifest,indent=2)+'\n')
    for p in (ROOT/'Assets/Game').rglob('*'):
        if p.is_dir():meta(str(p.relative_to(ROOT)),'DefaultImporter','  folderAsset: yes\n')
        elif not p.name.endswith('.meta') and not Path(str(p)+'.meta').exists():meta(str(p.relative_to(ROOT)))
    meta('Assets/Game','DefaultImporter','  folderAsset: yes\n')
    create_character_test(settings,player,ct,inp,movement,interaction)
    print(f'Authored {SCENE}: {len(Node.all)} objects, {len(TARGETS)} story interaction targets.')

def create_character_test(settings,player,ct,inp,movement,interaction):
    chapter_nodes=Node.all[:];chapter_counter=Node.counter
    Node.all=[];Node.counter=1000000
    env=Node('_ControllerTestEnvironment')
    box_node('Controller test floor',env,(0,-.1,5),(24,.2,30),'M_Floor')
    for i in range(1,8):
        box_node('Stair '+str(i),env,(4,.18*i/2,3+i*.52),(3,.18*i,.52),'M_Concrete')
    mesh_node('Gentle slope',env,(-4,.48,7),(3,.22,5),'M_Concrete',rot=(-12,0,0),collision=True)
    for x in [-2,2]:box_node('Low corridor side',env,(x,1,13),(.25,2,5),'M_Concrete')
    box_node('Low ceiling',env,(0,1.4,13),(4,.25,5),'M_Metal')
    sign(env,'ControllerTest',(0,2.5,18),'CHARACTER TEST\nSTAIRS / SLOPE / CROUCH',(5,1),(0,180,0))
    camera,cid=make_camera(None);camera.pos=[-2,2,-3];camera.rot=[12,20,0]
    rig=Node('Character test camera',static=False)
    rig.script('ThirdPersonCameraController',f'  followTarget: {{fileID: {ct.tid}}}\n  input: {{fileID: {inp}}}\n  initialYaw: 0\n')
    Node('Test HUD',static=False).script('ExplorationHUD',f'  player: {{fileID: {movement}}}\n  input: {{fileID: {inp}}}\n  interactor: {{fileID: {interaction}}}\n')
    sun,sid=light(env,'Test sun',(0,20,0),2,1000,(1,.95,.87),1,(50,-30,0),2)
    Node('Test bootstrap',static=False).script('GameBootstrap',f'  renderPipeline: {ref("Assets/_DesertShift/Settings/DesertShift_URP.asset",11400000)}\n  rendererData: {ref("Assets/_DesertShift/Settings/DesertShift_Renderer.asset",11400000)}\n  skyMaterial: {ref("Assets/_DesertShift/Art/Materials/M_DesertSky.mat",2100000)}\n  sun: {{fileID: {sid}}}\n  playerInput: {{fileID: {inp}}}\n')
    prefab=(ROOT/(BASE+'Prefabs/Characters/PF_EliasVale_Player.prefab')).read_text()[len(HEAD):]
    text=HEAD+re.sub(r'm_Sun: \{fileID: \d+\}',f'm_Sun: {{fileID: {sid}}}',settings)+prefab+''.join(node_yaml(n) for n in Node.all)
    text+='--- !u!1660057539 &9223372036854775807\nSceneRoots:\n  m_ObjectHideFlags: 0\n  m_Roots:\n'+f'  - {{fileID: {player.tid}}}\n'+''.join(f'  - {{fileID: {n.tid}}}\n' for n in Node.all if not n.parent)
    path=BASE+'Scenes/CharacterTest.unity';write(path,text);meta(path)
    Node.all=chapter_nodes;Node.counter=chapter_counter

def main():
    meta('Assets/Game/Shaders/CoastalWater.shader','ShaderImporter')
    meta('Assets/Game/Shaders/CoastalSky.shader','ShaderImporter')
    for p in (ROOT/'Assets/Game').rglob('*.cs'):
        meta(str(p.relative_to(ROOT)),'MonoImporter','  serializedVersion: 2\n  defaultReferences: []\n  executionOrder: 0\n  icon: {instanceID: 0}\n')
    materials()
    prison_details.make_materials(texture)
    coastal_art.pbr_materials(texture)
    save_mesh('PrisonBox',box(bevel=.018),'Environment')
    save_mesh('PrisonSphere',ellipsoid((1,1,1),16,28),'Environment')
    save_mesh('PrisonCylinder',cylinder(.5,1,24),'Environment')
    save_mesh('PrisonPlane',plane(1,1),'Environment')
    m=Mesh();m.quad((-.5,-.5,0),(.5,-.5,0),(.5,.5,0),(-.5,.5,0),uv=[(1,0),(0,0),(0,1),(1,1)]);save_mesh('SignPlane',m,'Props')
    bars=Mesh()
    for z in np.linspace(-.575,.575,8):bars.merge(cylinder(.018,2.45,10),(0,1.225,z))
    for y in [.15,1.2,2.35]:bars.merge(box((.065,.065,1.2),.008),(0,y,0))
    save_mesh('DoorBars',bars,'Props')
    fixed=Mesh()
    for z in np.linspace(-.7,.7,10):fixed.merge(cylinder(.015,2.55,8),(0,1.275,z))
    for y in [.12,1.18,2.45]:fixed.merge(box((.06,.06,1.44),.006),(0,y,0))
    save_mesh('FixedBars',fixed,'Props')
    knife=Mesh();knife.merge(box((.027,.017,.15),.005),(0,.016,-.045));
    knife.tri((-.014,.024,.025),(.014,.024,.025),(0,.024,.18));knife.tri((0,.02,.18),(.014,.02,.025),(-.014,.02,.025))
    save_mesh('Knife',knife,'Props')
    authored_scene()

if __name__=='__main__':main()
