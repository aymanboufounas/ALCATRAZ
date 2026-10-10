"""Render the exact source-authored Alcatraz meshes and actual Rocketbox skins.
This uses Mesa/OpenGL offline. It is NOT a Unity capture or gameplay recording.
"""
from pathlib import Path
import json,math,ctypes as C,sys,gzip
import numpy as np
from scipy.spatial.transform import Rotation
from PIL import Image,ImageDraw,ImageFont
from fbx_pose import Character,animation
from authoring_io import read_authoring

ROOT=Path(__file__).resolve().parents[1]
code=(ROOT/'Tools/render_blackstone_preview.py').read_text().split('data=json.loads')[0]
code=code.replace('W,H=1440,810','W,H=1600,1000')
code=code.replace('length(eye-world)*.00165','length(eye-world)*.00032')
code=code.replace('uniform float roughness,metalness,tiling;','uniform int ocean;uniform float roughness,metalness,tiling;')
code=code.replace('frag=vec4(pow(aces(lit*1.20),vec3(1./2.2)),baseColor.a);',
    'if(ocean==1){float waves=sin(world.z*.95+sin(world.x*.09)*.8)*.15+sin(world.z*1.7+world.x*.12)*.09+sin(world.x*.18+world.z*.24)*.2;lit=vec3(.018,.065,.082)+vec3(.021,.030,.040)*(waves+.5);lit+=vec3(.025,.040,.045)*pow(max(0.,sin(world.z*.97+sin(world.x*.10))),12.);}frag=vec4(pow(aces(lit*1.20),vec3(1./2.2)),baseColor.a);')
code=code.replace('void main(){vec3 n=normalize(normal);','void main(){if(hasTexture==1&&texture(baseTex,uv*tiling).a<.4)discard;vec3 n=normalize(normal);')
backend={'__file__':str(ROOT/'Tools/render_blackstone_preview.py'),'__name__':'alcatraz_preview_backend'}
exec(compile(code,'mesa_alcatraz_helpers','exec'),backend)
G=backend['G'];U=backend['U'];PBR=backend['PBR'];DEPTH=backend['DEPTH'];SKY=backend['SKY']
uniform=backend['uniform'];mat4=backend['mat4'];lookat=backend['lookat'];perspective=backend['perspective'];ortho=backend['ortho'];buffer=backend['buffer'];texture=backend['texture']
W,H=1600,1000
raw=ROOT/'Documentation/AlcatrazAuthoring.json'
data=read_authoring(raw)
actors=json.loads((ROOT/'Documentation/AlcatrazActors.json').read_text())
roster={a['actorName']:a for a in json.loads((ROOT/'Assets/Game/Alcatraz/Resources/Alcatraz/CharacterRoster.json').read_text())['actors']}
nodes={n['id']:n for n in data['nodes']};transforms={};flip=np.diag([1,1,-1,1])
def world(n):
    if n['id'] in transforms:return transforms[n['id']]
    m=np.eye(4);m[:3,:3]=Rotation.from_euler('xyz',n['rot'],degrees=True).as_matrix()@np.diag(n['scale']);m[:3,3]=n['pos']
    if n['parent']:m=world(nodes[n['parent']])@m
    transforms[n['id']]=m;return m
buffers={};draws=[];used_materials={}
def draw_entry(mesh,mat,model,label,key):
    if key not in buffers:buffers[key]=buffer(mesh)
    draws.append((buffers[key],model,mat,label));used_materials[id(mat)]=mat
for n in data['nodes']:
    if not n.get('mesh') or not n.get('active',True) or not n.get('rendered',True):continue
    mesh=data['meshes'][n['mesh']];mat=data['materials'][n['mat']]
    draw_entry(mesh,mat,flip@world(n),n['name'],n['mesh'])
# Source skin preview matches FoundationBootstrap profile assignment and body scales.
idle=animation(ROOT/'Assets/Game/Foundation/Animations/Rocketbox/Idle.fbx')
seated=animation(ROOT/'Assets/Game/Foundation/Animations/Rocketbox/Seated.fbx')
walk=animation(ROOT/'Assets/Game/Foundation/Animations/Rocketbox/Walk.fbx')
characters={};skinned={}
for actor in actors:
    name=actor['name'];guard=name.startswith('Officer');black=name.startswith('Malik') or name in ['Andre','Moses','Jamal']
    profile='16' if name=='Elias Vale' else '07' if guard or name.startswith('Niko') else '12' if black else '17' if name.startswith('Samir') or name=='Yusef' else '20'
    identity=roster.get(name)
    if identity:profile=identity['model'].rsplit('_',1)[-1]
    if profile not in characters:characters[profile]=Character(ROOT/('Assets/Game/Resources/BlackstoneFoundation/Characters/Male_Adult_'+profile+'/Male_Adult_'+profile+'.fbx'))
    pose='seated' if actor['pose'] in [8,9,10] else 'idle'
    key=(profile,pose)
    if key not in skinned:skinned[key]=characters[profile].meshes(seated if pose=='seated' else idle,.4)
    model=np.eye(4);scale=np.array([1.18,1,1.18]) if name in ['Benny','Owen','Peter'] else np.array([.94,1,.94]) if name in ['Luis','Eddie'] else np.ones(3)
    if identity:scale=np.array([identity['build'],1,identity['build']])*identity['height']/1.78
    model[:3,:3]=Rotation.from_euler('y',actor['yaw'],degrees=True).as_matrix()@np.diag(scale);model[:3,3]=actor['position']
    for j,mesh in enumerate(skinned[key]):
        path=str(mesh['texture'].relative_to(ROOT))
        if guard and '_body' in path:path='Assets/Game/Resources/BlackstoneFoundation/Characters/Male_Adult_07/m013_body_guard.png'
        if name=='Officer Harrow' and '_body' in path:path='Assets/Game/Resources/BlackstoneFoundation/Characters/Male_Adult_07/m013_body_harrow.png'
        if name=='Elias Vale' and '_head' in path:path='Assets/Game/Resources/BlackstoneFoundation/Characters/Male_Adult_16/m019_head_elias08.png'
        if name=='Officer Harrow' and '_head' in path:path='Assets/Game/Resources/BlackstoneFoundation/Characters/Male_Adult_07/m013_head_harrow08.png'
        color=[.74,.78,.72,1] if name=='Elias Vale' and '_body' in path else [1,1,1,1]
        if name=='Officer Harrow' and '_body' in path:color=[.93,.96,1,1]
        mat={'color':color,'roughness':.75,'metalness':0,'texture':path,'tiling':1,'transparent':False}
        draw_entry(mesh,mat,flip@model,name,'Skin_'+profile+'_'+pose+'_'+str(j))
textures={}
for mat in used_materials.values():
    for key in ['texture','normal','surface']:
        path=mat.get(key)
        if path and path not in textures:textures[path]=texture(path)
shadow=U();G.glGenTextures(1,C.byref(shadow));G.glBindTexture(0x0DE1,shadow)
G.glTexImage2D(0x0DE1,0,0x81A6,2048,2048,0,0x1902,0x1405,None)
for k,v in [(0x2801,0x2601),(0x2800,0x2601),(0x2802,0x812F),(0x2803,0x812F)]:G.glTexParameteri(0x0DE1,k,v)
fb=U();G.glGenFramebuffers(1,C.byref(fb));G.glBindFramebuffer(0x8D40,fb);G.glFramebufferTexture2D(0x8D40,0x8D00,0x0DE1,shadow,0);G.glDrawBuffer(0);G.glReadBuffer(0)
assert G.glCheckFramebufferStatus(0x8D40)==0x8CD5
skyvao=U();G.glGenVertexArrays(1,C.byref(skyvao));G.glBindVertexArray(skyvao)
skyebo=U();G.glGenBuffers(1,C.byref(skyebo));G.glBindBuffer(0x8893,skyebo);skyidx=np.array([0,1,2],dtype='u4');G.glBufferData(0x8893,12,skyidx.ctypes.data,0x88E4)
views=[
 ('A01_Island',(254,220,-285),(0,14,0),44,210),
 ('A02_CellhouseYard',(-112,82,113),(-7,35,22),58,100),
 ('A03_Broadway',(0,32.1,-25),(0,34.8,17),68,52),
 ('A04_Recreation',(-43,29.2,33),(-49,28.7,49),70,42),
 ('A05_Prisoner',(-2.1,31.7,-24.1),(-4.25,31.1,-24.91),42,35),
 ('A06_Dock',(160,34,-126),(82,10,-62),60,95),
 ('A07_Visitation',(18.4,31.8,-39.5),(22.25,31.25,-38),60,35),
 ('A08_Gallery',(1.3,36.9,38),(2.9,35.5,-5),70,50),
 ('A09_DiningHall',(0,31.7,46),(3,31.2,57),68,45),
 ('A10_Poker',(-52,29.2,39),(-54,28.3,42),58,40),
    ('A11_Industries',(-38,12.1,104.5),(-41,10.8,124),68,48),
    ('A12_Storehouse',(70,7,-46),(73,6.6,-24),70,45),
    ('A13_Shower',(12,32,-54.5),(11,31.3,-48),72,38),
    ('A14_Officer',(-28.6,28.95,46),(-30.5,28.45,49),40,36),
    ('A15_CoastalPath',(-70.2,12.4,-59),(-77.5,15.6,-3),66,95),
    ('A16_PrisonerPortrait',(-2.5,31.7,-24.1),(-4.25,31.55,-24.91),38,34),
]
only=sys.argv[1:] or [v[0] for v in views]
out=ROOT/'Documentation/AlcatrazPreviews';out.mkdir(parents=True,exist_ok=True)
def frame(eye,at,fov,shadow_size):
    eye=np.array(eye)*[1,1,-1];at=np.array(at)*[1,1,-1]
    lp=at+np.array([.53,.57,.63])*500;lvp=ortho(shadow_size,1,1100)@lookat(lp,at)
    G.glBindFramebuffer(0x8D40,fb);G.glViewport(0,0,2048,2048);G.glClear(0x100);G.glEnable(0x0B71);G.glEnable(0x0B44);G.glFrontFace(0x0900);G.glCullFace(0x0405)
    G.glUseProgram(DEPTH);mat4(DEPTH,'vp',lvp)
    for (vao,count),model,mat,label in draws:
        if mat.get('transparent'):continue
        mat4(DEPTH,'model',model);G.glBindVertexArray(vao);G.glDrawElements(4,count,0x1405,None)
    G.glBindFramebuffer(0x8D40,0);G.glViewport(0,0,W,H);G.glClearColor(.65,.7,.69,1);G.glClear(0x4100)
    G.glDisable(0x0B71);G.glDisable(0x0B44);G.glUseProgram(SKY);G.glBindVertexArray(skyvao);G.glDrawElements(4,3,0x1405,None)
    G.glEnable(0x0B71);G.glEnable(0x0B44);G.glUseProgram(PBR)
    mat4(PBR,'vp',perspective(fov,W/H)@lookat(eye,at));mat4(PBR,'lightVP',lvp);G.glUniform3f(uniform(PBR,'eye'),*eye)
    G.glActiveTexture(0x84C1);G.glBindTexture(0x0DE1,shadow);G.glUniform1i(uniform(PBR,'shadowMap'),1)
    opaque=[d for d in draws if not d[2].get('transparent')];transparent=[d for d in draws if d[2].get('transparent')]
    transparent.sort(key=lambda d:-np.linalg.norm(d[1][:3,3]-eye))
    for batch,alpha in [(opaque,False),(transparent,True)]:
        if alpha:G.glEnable(0x0BE2);G.glBlendFunc(0x0302,0x0303);G.glDepthMask(0)
        for (vao,count),model,mat,label in batch:
            G.glUniform1i(uniform(PBR,'ocean'),int(label=='San Francisco Bay'))
            mat4(PBR,'model',model);G.glUniform4f(uniform(PBR,'baseColor'),*mat['color'])
            G.glUniform3f(uniform(PBR,'emission'),*(mat.get('emission') or [0,0,0])[:3]);G.glUniform1f(uniform(PBR,'roughness'),mat['roughness']);G.glUniform1f(uniform(PBR,'metalness'),mat['metalness']);G.glUniform1f(uniform(PBR,'tiling'),mat['tiling'])
            path=mat.get('texture');G.glUniform1i(uniform(PBR,'hasTexture'),int(path is not None));G.glActiveTexture(0x84C0);G.glBindTexture(0x0DE1,textures.get(path,0));G.glUniform1i(uniform(PBR,'baseTex'),0)
            for unit,key,sampler,flag in [(2,'normal','normalTex','hasNormal'),(3,'surface','surfaceTex','hasSurface')]:
                path=mat.get(key);G.glUniform1i(uniform(PBR,flag),int(path is not None));G.glActiveTexture(0x84C0+unit);G.glBindTexture(0x0DE1,textures.get(path,0));G.glUniform1i(uniform(PBR,sampler),unit)
            G.glBindVertexArray(vao);G.glDrawElements(4,count,0x1405,None)
        if alpha:G.glDisable(0x0BE2);G.glDepthMask(1)
    G.glFinish();pixels=np.zeros((H,W,4),np.uint8);G.glReadPixels(0,0,W,H,0x1908,0x1401,pixels.ctypes.data)
    return Image.fromarray(pixels[::-1,:,:3])

for name,eye,at,fov,size in views:
    if name not in only:continue
    image=frame(eye,at,fov,size);d=ImageDraw.Draw(image);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
    d.rectangle((0,H-37,W,H),fill='#111e24')
    d.text((20,H-29),'ALCATRAZ  /  '+name.replace('_',' ')+'  ·  ACTUAL SOURCE GEOMETRY  ·  OFFLINE RENDER, NOT UNITY',font=font,fill='#ded8bf')
    target=out/(name+'.png');pending=out/(name+'.png.pending')
    image.save(pending,format='PNG')
    with Image.open(pending) as verified:verified.verify()
    pending.replace(target);print('Rendered '+name,flush=True)
