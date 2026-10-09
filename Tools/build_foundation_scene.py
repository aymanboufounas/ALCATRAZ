"""Add exploration and upgraded story scenes without overwriting the approved chapter."""
from pathlib import Path
import hashlib, json, re
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import unity_writer as uw
from geometry import box, cylinder, tube, Mesh
from prepare_foundation_assets import png, metas

ROOT=Path(__file__).resolve().parents[1]
BASE='Assets/Game/Foundation'
RESOURCE='Assets/Game/Resources/BlackstoneFoundation'

def equipment():
    uw.ART=BASE+'/Art'
    uw.material('EquipmentSteel',[.18,.20,.22,1],rough=.27,metal=.85)
    uw.material('EquipmentPolymer',[.035,.040,.043,1],rough=.72)
    uw.material('KnifeSteel',[.62,.65,.66,1],rough=.22,metal=.92)
    def part(root,name,mesh,mat,pos=(0,0,0),rot=(0,0,0),node_name=None):
        key=root.name+'_'+name;uw.save_mesh(key,mesh,'Equipment');uw.Node(node_name or name,root,pos=pos,rot=rot,static=False).render(key,mat)
    for name in ['Knife','Pistol','Rifle']:
        uw.Node.all=[];uw.Node.counter=20000000;root=uw.Node(name,static=False,layer=8)
        if name=='Knife':
            part(root,'Handle',cylinder(.016,.115,16),'EquipmentPolymer',pos=(0,0,-.015),rot=(90,0,0))
            blade=Mesh();a=(-.022,0,.055);b=(.022,0,.055);tip=(.003,0,.215)
            for sign in [-1,1]:
                ridge=(0,.004*sign,.1)
                for x,y in [(a,b),(b,tip),(tip,a)]:
                    if sign>0:blade.tri(x,y,ridge)
                    else:blade.tri(y,x,ridge)
            part(root,'Blade',blade,'KnifeSteel');part(root,'Guard',box((.064,.013,.014),.004),'EquipmentSteel',pos=(0,0,.048))
            muzzle=(0,0,.22)
        elif name=='Pistol':
            part(root,'Slide',box((.037,.040,.18),.005),'EquipmentSteel',pos=(0,.032,.056))
            part(root,'Frame',box((.032,.025,.145),.004),'EquipmentPolymer',pos=(0,.004,.045))
            part(root,'Grip',box((.035,.105,.036),.006),'EquipmentPolymer',pos=(0,-.048,-.009),rot=(12,0,0))
            part(root,'Barrel',cylinder(.0085,.030,16),'EquipmentSteel',pos=(0,.030,.152),rot=(90,0,0))
            part(root,'Trigger guard',tube([(-.015,-.01,.01),(-.015,-.037,.022),(-.015,-.037,.071),(-.015,-.007,.08)],.003,8),'EquipmentSteel')
            part(root,'Rear sight',box((.025,.010,.011),.002),'EquipmentSteel',pos=(0,.058,-.022))
            part(root,'Front sight',box((.007,.007,.009),.001),'EquipmentSteel',pos=(0,.057,.13));muzzle=(0,.03,.175)
        else:
            part(root,'Receiver',box((.052,.07,.19),.008),'EquipmentSteel',pos=(0,.023,.095))
            part(root,'Grip',box((.033,.10,.039),.005),'EquipmentPolymer',pos=(0,-.057,.02),rot=(15,0,0))
            part(root,'Magazine',box((.039,.13,.055),.007),'EquipmentPolymer',pos=(0,-.077,.16),rot=(-9,0,0))
            part(root,'Handguard',box((.051,.048,.22),.007),'EquipmentPolymer',pos=(0,.015,.30))
            part(root,'Barrel',cylinder(.009,.23,18),'EquipmentSteel',pos=(0,.026,.49),rot=(90,0,0))
            part(root,'Muzzle',cylinder(.013,.043,18),'EquipmentSteel',pos=(0,.026,.62),rot=(90,0,0),node_name='Muzzle shroud')
            part(root,'Stock tube',cylinder(.016,.15,16),'EquipmentSteel',pos=(0,.022,-.07),rot=(90,0,0))
            part(root,'Stock',box((.049,.102,.13),.012),'EquipmentPolymer',pos=(0,-.01,-.15))
            part(root,'Sight',box((.025,.025,.067),.007),'EquipmentSteel',pos=(0,.073,.10));muzzle=(0,.026,.65)
        uw.Node('Muzzle',root,pos=muzzle,static=False)
        path=RESOURCE+'/Weapons/'+name+'.prefab'
        uw.write(path,uw.HEAD+''.join(uw.node_yaml(n,n==root) for n in uw.Node.all));uw.meta(path,'PrefabImporter')

def target_art():
    im=Image.new('RGB',(768,1024),'#e4e0d3');d=ImageDraw.Draw(im)
    for radius in [245,200,155,110,65,24]:
        d.ellipse((384-radius,500-radius,384+radius,500+radius),outline='#253430',width=4)
    d.line((100,500,668,500),fill='#324d43',width=2);d.line((384,180,384,820),fill='#324d43',width=2)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',46)
    d.text((185,62),'BLACKSTONE',font=font,fill='#253430');d.text((180,880),'YARD RANGE',font=font,fill='#253430')
    png(BASE+'/Art/Textures/TargetPaper.png',im)
    rng=np.random.default_rng(405);a=rng.integers(0,35,(256,256,1));rgb=np.clip(np.array([57,76,44])+a,0,255).astype('u1');png(BASE+'/Art/Textures/TestTurf.png',Image.fromarray(rgb))

def scene():
    original='Assets/Game/Scenes/SC_BlackstoneIsland.unity';source=(ROOT/original).read_text()
    baseline=hashlib.sha256((ROOT/original).read_bytes()).hexdigest()
    blocks=re.split(r'(?=^--- !u!)',source,flags=re.M)
    script_paths={uw.guid(str(p.relative_to(ROOT))):p.stem for p in (ROOT/'Assets').rglob('*.cs')}
    off={'PrisonStoryDirector','PrisonHUD','StoryInteractable','PrisonPokerTable','PrisonConversationTable','PrisonPopulation','CinematicView','ExplorationHUD'}
    free=[]
    props={9600,47180,10480,9620}
    for block in blocks:
        match=re.search(r'm_Script: \{fileID: 11500000, guid: ([a-f0-9]+)',block)
        name=script_paths.get(match.group(1)) if match else None
        if name in off:
            block=block.replace('  m_Enabled: 1','  m_Enabled: 0',1)
            if name in {'StoryInteractable','PrisonPokerTable','PrisonConversationTable'}:
                block=re.sub(r'^  director: .*$', '  director: {fileID: 0}',block,flags=re.M)
        if name=='DoorController':block=re.sub(r'^  locked: .*$', '  locked: 0',block,flags=re.M)
        if name=='PlayerMovement':
            for field,value in [('walkSpeed','1.05'),('jogSpeed','1.55'),('sprintSpeed','4.9'),('crouchSpeed','.85'),('acceleration','7.5'),('deceleration','10'),('rotationSharpness','9')]:
                block=re.sub(r'^  '+field+r': .*$', '  '+field+': '+value,block,flags=re.M)
        identity=re.search(r'^--- !u!1 &(\d+)',block)
        if identity and int(identity.group(1)) in props:block=block.replace('  m_IsActive: 1','  m_IsActive: 0')
        free.append(block)
    free=''.join(free)
    # Preserve B-04 geometry; spawn outdoors so all equipment can be tried immediately.
    player_block=next(b for b in blocks if '  m_Name: "Player"\n' in b)
    player_tid=int(re.search(r'component: \{fileID: (\d+)\}',player_block).group(1))
    def relocate(m):
        b=m.group(0)
        b=re.sub(r'^  m_LocalPosition: .*$', '  m_LocalPosition: {x: 0, y: .11, z: 11}',b,flags=re.M)
        b=re.sub(r'^  m_LocalRotation: .*$', '  m_LocalRotation: {x: 0, y: 0, z: 0, w: 1}',b,flags=re.M)
        return b
    free=re.sub(r'^--- !u!4 &'+str(player_tid)+r'\n.*?(?=^--- !u!|\Z)',relocate,free,flags=re.M|re.S)
    uw.Node.all=[];uw.Node.counter=21000000;uw.ART=BASE+'/Art'
    root=uw.Node('Character foundation',static=False)
    root.script(BASE+'/Scripts/FoundationBootstrap.cs','  storyMode: 0\n');root.script(BASE+'/Scripts/FoundationHUD.cs');root.script(BASE+'/Scripts/FoundationConversations.cs')
    uw.material('TargetPaper',[1,1,1,1],rough=.92,texture=BASE+'/Art/Textures/TargetPaper.png')
    uw.material('RangeStand',[.12,.14,.13,1],rough=.72,metal=.5)
    uw.material('TestMetal',[.35,.38,.40,1],rough=.4,metal=.85)
    uw.material('TestWood',[.29,.16,.08,1],rough=.82)
    uw.material('TestTurf',[1,1,1,1],rough=.97,texture=BASE+'/Art/Textures/TestTurf.png',tiling=6)
    uw.save_mesh('TargetPaper',box((.94,1.25,.035),.002),'Range');uw.save_mesh('Stand',box((.055,1.6,.06),.005),'Range')
    uw.save_mesh('SurfacePad',box((2.5,.055,3),.003),'Range')
    for i,x in enumerate([-13,-10,-7]):
        target=uw.Node('Training target '+str(i+1),pos=(x,1.65,28),rot=(0,180,0));target.render('TargetPaper','TargetPaper');target.boxcollider((.94,1.25,.05));target.script(BASE+'/Scripts/FoundationTarget.cs')
        uw.Node('Target stand '+str(i+1),pos=(x,.8,28.02)).render('Stand','RangeStand')
    for x,name,kind in [(-14,'Metal',2),(-10,'Wood',3),(-6,'Turf',0)]:
        pad=uw.Node(name+' footstep pad',pos=(x,.06,20.5));pad.render('SurfacePad','Test'+name);pad.boxcollider((2.5,.055,3));pad.script('SurfaceTag','  surface: '+str(kind)+'\n')
    def append(text,nodes,path):
        position=text.index('--- !u!1660057539 ')
        body=text[:position]+''.join(uw.node_yaml(n) for n in nodes)+text[position:]
        for n in nodes:
            if n.parent is None:body+='  - {fileID: '+str(n.tid)+'}\n'
        uw.write(path,body);uw.meta(path)
    append(free,uw.Node.all,'Assets/Game/Scenes/SC_BlackstoneFoundation.unity')
    uw.Node.all=[];uw.Node.counter=22000000
    upgrade=uw.Node('Story character upgrade',static=False);upgrade.script(BASE+'/Scripts/FoundationBootstrap.cs','  storyMode: 1\n')
    append(source,uw.Node.all,'Assets/Game/Scenes/SC_BlackstoneStory_Upgraded.unity')
    settings=uw.HEAD+'--- !u!1045 &1\nEditorBuildSettings:\n  m_ObjectHideFlags: 0\n  serializedVersion: 2\n  m_Scenes:\n'
    for enabled,path in [(1,'Assets/Game/Scenes/SC_BlackstoneFoundation.unity'),(1,'Assets/Game/Scenes/SC_BlackstoneStory_Upgraded.unity'),(0,original),(0,'Assets/_DesertShift/Scenes/SC_DesertTown.unity')]:
        settings+='  - enabled: '+str(enabled)+'\n    path: '+path+'\n    guid: '+uw.guid(path)+'\n'
    settings+='  m_configObjects: {}\n  m_UseUCBPForAssetBundles: 0\n';uw.write('ProjectSettings/EditorBuildSettings.asset',settings)
    uw.write('Documentation/Revision05_Scenes.json',json.dumps({'original_scene':original,'original_scene_sha256':baseline,
        'default_scene':'SC_BlackstoneFoundation','story_scene':'SC_BlackstoneStory_Upgraded','models':5,'source_animation_clips':12,
        'targets':3,'footstep_pads':3,'status':'Source-authored; Unity import and Play Mode verification required.'},indent=2))

if __name__=='__main__':
    equipment();target_art();scene();metas();print('Prepared original equipment prefabs and two new scenes; original chapter preserved.')
