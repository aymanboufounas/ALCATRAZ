"""Offline geometry QA renderer. These images are NOT Unity screenshots.
Uses the same generated meshes, materials and transforms through Mesa OpenGL.
"""
import ctypes as C,sys,math,json,gzip,pickle
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
G=C.CDLL('libGL.so.1');E=C.CDLL('libEGL.so.1')
def bind(lib,name,restype,*args):
    f=getattr(lib,name);f.restype=restype;f.argtypes=list(args);return f
P=C.c_void_p;I=C.c_int;U=C.c_uint;F=C.c_float
bind(E,'eglGetProcAddress',P,C.c_char_p)
platform=C.CFUNCTYPE(P,U,P,C.POINTER(I))(E.eglGetProcAddress(b'eglGetPlatformDisplayEXT'))
display=platform(0x31DD,None,None)
bind(E,'eglInitialize',U,P,C.POINTER(I),C.POINTER(I))(display,C.byref(I()),C.byref(I()))
E.eglBindAPI(0x30A2);config=P();num=I()
bind(E,'eglChooseConfig',U,P,C.POINTER(I),C.POINTER(P),I,C.POINTER(I))(display,(I*13)(0x3033,1,0x3040,8,0x3024,8,0x3023,8,0x3022,8,0x3025,24,0x3038),C.byref(config),1,C.byref(num))
W,H=1440,810
surface=bind(E,'eglCreatePbufferSurface',P,P,P,C.POINTER(I))(display,config,(I*5)(0x3057,W,0x3056,H,0x3038))
ctx=bind(E,'eglCreateContext',P,P,P,P,C.POINTER(I))(display,config,None,(I*5)(0x3098,3,0x30FB,3,0x3038))
assert bind(E,'eglMakeCurrent',U,P,P,P,P)(display,surface,surface,ctx)
for name,ret,args in [('glCreateShader',U,[U]),('glShaderSource',None,[U,I,C.POINTER(C.c_char_p),C.POINTER(I)]),('glCompileShader',None,[U]),('glGetShaderiv',None,[U,U,C.POINTER(I)]),('glGetShaderInfoLog',None,[U,I,C.POINTER(I),P]),('glCreateProgram',U,[]),('glAttachShader',None,[U,U]),('glLinkProgram',None,[U]),('glGetProgramiv',None,[U,U,C.POINTER(I)]),('glGetProgramInfoLog',None,[U,I,C.POINTER(I),P]),('glUseProgram',None,[U]),('glGenVertexArrays',None,[I,C.POINTER(U)]),('glBindVertexArray',None,[U]),('glGenBuffers',None,[I,C.POINTER(U)]),('glBindBuffer',None,[U,U]),('glBufferData',None,[U,C.c_ssize_t,P,U]),('glVertexAttribPointer',None,[U,I,U,C.c_ubyte,I,P]),('glEnableVertexAttribArray',None,[U]),('glGetUniformLocation',I,[U,C.c_char_p]),('glUniformMatrix4fv',None,[I,I,C.c_ubyte,P]),('glUniform3f',None,[I,F,F,F]),('glUniform4f',None,[I,F,F,F,F]),('glUniform1f',None,[I,F]),('glUniform1i',None,[I,I]),('glDrawElements',None,[U,I,U,P]),('glGenTextures',None,[I,C.POINTER(U)]),('glBindTexture',None,[U,U]),('glTexImage2D',None,[U,I,I,I,I,I,U,U,P]),('glTexParameteri',None,[U,U,I]),('glGenerateMipmap',None,[U]),('glActiveTexture',None,[U]),('glGenFramebuffers',None,[I,C.POINTER(U)]),('glBindFramebuffer',None,[U,U]),('glFramebufferTexture2D',None,[U,U,U,U,I]),('glCheckFramebufferStatus',U,[U]),('glDrawBuffer',None,[U]),('glReadBuffer',None,[U]),('glViewport',None,[I,I,I,I]),('glClearColor',None,[F,F,F,F]),('glClear',None,[U]),('glEnable',None,[U]),('glDisable',None,[U]),('glCullFace',None,[U]),('glFrontFace',None,[U]),('glBlendFunc',None,[U,U]),('glDepthMask',None,[C.c_ubyte]),('glReadPixels',None,[I,I,I,I,U,U,P]),('glFinish',None,[])]:bind(G,name,ret,*args)

def program(vs,fs):
    p=G.glCreateProgram()
    for typ,src in [(0x8B31,vs),(0x8B30,fs)]:
        sh=G.glCreateShader(typ);b=C.c_char_p(src.encode());G.glShaderSource(sh,1,C.byref(b),None);G.glCompileShader(sh);ok=I();G.glGetShaderiv(sh,0x8B81,C.byref(ok))
        if not ok.value:
            buf=C.create_string_buffer(8192);G.glGetShaderInfoLog(sh,8192,None,buf);raise RuntimeError(buf.value)
        G.glAttachShader(p,sh)
    G.glLinkProgram(p);ok=I();G.glGetProgramiv(p,0x8B82,C.byref(ok))
    if not ok.value:raise RuntimeError('GL shader linking failed')
    return p
VS='''#version 330 core
layout(location=0) in vec3 aPos; layout(location=1) in vec3 aNormal; layout(location=2) in vec2 aUV;
uniform mat4 model, vp, lightVP;
out vec3 world,normal;out vec2 uv;out vec4 shadowPos;
void main(){vec4 w=model*vec4(aPos,1);world=w.xyz;normal=normalize(transpose(inverse(mat3(model)))*aNormal);uv=aUV;shadowPos=lightVP*w;gl_Position=vp*w;}
'''
FS='''#version 330 core
in vec3 world,normal;in vec2 uv;in vec4 shadowPos;out vec4 frag;
uniform vec4 baseColor;uniform vec3 eye;uniform vec3 emission;
uniform float roughness,metalness,tiling;uniform int hasTexture;
uniform sampler2D baseTex,shadowMap;
float visibility(){vec3 p=shadowPos.xyz/shadowPos.w*.5+.5;if(p.x<0||p.x>1||p.y<0||p.y>1)return 1.;float sum=0.;
for(int i=-1;i<=1;i++)for(int j=-1;j<=1;j++){float d=texture(shadowMap,p.xy+vec2(i,j)/2048.).r;sum+=(p.z-.0011<d)?1.:.0;}return sum/9.;}
vec3 aces(vec3 x){return clamp((x*(2.51*x+.03))/(x*(2.43*x+.59)+.14),0.,1.);}
void main(){vec3 n=normalize(normal);if(!gl_FrontFacing)n=-n;vec3 v=normalize(eye-world),l=normalize(vec3(.53,.57,.63));
vec3 tex=hasTexture==1?pow(texture(baseTex,uv*tiling).rgb,vec3(2.2)):vec3(1);vec3 c=pow(baseColor.rgb,vec3(2.2))*tex;
float ndl=max(dot(n,l),0.),shadow=visibility();vec3 amb=mix(vec3(.18,.14,.085),vec3(.29,.38,.45),n.y*.5+.5);
vec3 lit=c*(amb+vec3(1.42,1.26,1.00)*ndl*(.12+.88*shadow));
vec3 halfv=normalize(l+v);float spec=pow(max(dot(n,halfv),0.),mix(180.,8.,roughness));
lit+=mix(vec3(.035),c,metalness)*spec*(1.-roughness)*shadow*2.8+emission*.15;
float fres=pow(1.-max(dot(n,v),0.),5.);lit+=vec3(.28,.38,.43)*fres*(1.-roughness)*.35;
float fog=1.-exp(-pow(length(eye-world)*.00165,2.));lit=mix(lit,vec3(.38,.46,.42),fog);
frag=vec4(pow(aces(lit*1.20),vec3(1./2.2)),baseColor.a);}
'''
PBR=program(VS,FS);DEPTH=program('''#version 330 core
layout(location=0)in vec3 aPos;uniform mat4 model,vp;void main(){gl_Position=vp*model*vec4(aPos,1);}
''','''#version 330 core
void main(){}
''')
SKY=program('''#version 330 core
out vec2 uv;void main(){vec2 p=vec2((gl_VertexID<<1)&2,gl_VertexID&2);uv=p;gl_Position=vec4(p*2.-1.,1,1);}
''','''#version 330 core
in vec2 uv;out vec4 frag;void main(){float h=clamp(uv.y,0.,1.);frag=vec4(mix(vec3(.77,.78,.69),vec3(.33,.57,.71),pow(h,.7)),1);}
''')
# Sky uses a tiny index buffer just like the geometry.

def uniform(p,k):return G.glGetUniformLocation(p,k.encode())
def mat4(p,k,v):
    a=np.asarray(v,dtype=np.float32).T.copy();G.glUniformMatrix4fv(uniform(p,k),1,0,a.ctypes.data)
def lookat(eye,at):
    eye=np.array(eye,float);f=np.array(at,float)-eye;f/=np.linalg.norm(f);s=np.cross(f,[0,1,0]);s/=np.linalg.norm(s);u=np.cross(s,f)
    v=np.eye(4);v[0,:3]=s;v[1,:3]=u;v[2,:3]=-f;v[:3,3]=-v[:3,:3]@eye;return v
def perspective(fov,aspect,near=.07,far=1700):
    q=1/math.tan(math.radians(fov)/2);v=np.zeros((4,4));v[0,0]=q/aspect;v[1,1]=q;v[2,2]=(far+near)/(near-far);v[2,3]=2*far*near/(near-far);v[3,2]=-1;return v
def ortho(s,n,f):
    m=np.diag([1/s,1/s,-2/(f-n),1]);m[2,3]=-(f+n)/(f-n);return m
def buffer(mesh):
    arr=np.concatenate([np.array(mesh['v']),np.array(mesh['n']),np.array(mesh['uv'])],axis=1).astype('float32');idx=np.array(mesh['t'],dtype=np.uint32)
    vao=U();G.glGenVertexArrays(1,C.byref(vao));G.glBindVertexArray(vao)
    vbo=U();G.glGenBuffers(1,C.byref(vbo));G.glBindBuffer(0x8892,vbo);G.glBufferData(0x8892,arr.nbytes,arr.ctypes.data,0x88E4)
    ebo=U();G.glGenBuffers(1,C.byref(ebo));G.glBindBuffer(0x8893,ebo);G.glBufferData(0x8893,idx.nbytes,idx.ctypes.data,0x88E4)
    for i,num,off in [(0,3,0),(1,3,12),(2,2,24)]:G.glVertexAttribPointer(i,num,0x1406,0,32,P(off));G.glEnableVertexAttribArray(i)
    return vao.value,len(idx)
def texture(path):
    im=Image.open(ROOT/path).convert('RGBA').transpose(Image.Transpose.FLIP_TOP_BOTTOM);a=np.array(im);tex=U();G.glGenTextures(1,C.byref(tex));G.glBindTexture(0x0DE1,tex)
    G.glTexImage2D(0x0DE1,0,0x8058,im.width,im.height,0,0x1908,0x1401,a.ctypes.data)
    G.glTexParameteri(0x0DE1,0x2801,0x2703);G.glTexParameteri(0x0DE1,0x2800,0x2601);G.glGenerateMipmap(0x0DE1);return tex.value

with gzip.open(ROOT.parent/'.checks/scene_preview.pkl.gz','rb') as f:data=pickle.load(f)
nodes={n['id']:n for n in data['nodes']};transforms={};flip=np.diag([1,1,-1,1])
def world(n):
    if n['id'] in transforms:return transforms[n['id']]
    m=np.eye(4);m[:3,:3]=Rotation.from_euler('xyz',n['rot'],degrees=True).as_matrix()@np.diag(n['scale']);m[:3,3]=n['pos']
    if n['parent']:m=world(nodes[n['parent']])@m
    transforms[n['id']]=m;return m
buffers={};draws=[]
for n in data['nodes']:
    if not n.get('mesh'):continue
    name=n['mesh'];m=data['meshes'][name];model=world(n)
    if n.get('skinBones'):
        v=np.array(m['v']);norm=np.array(m['n']);w=np.array(m['weights']);posed=np.zeros_like(v);pn=np.zeros_like(norm)
        for j,bid in enumerate(n['skinBones']):
            weight=np.where(w[:,0]==j,w[:,2],0)+np.where(w[:,1]==j,w[:,3],0)
            if not np.any(weight):continue
            bindm=np.eye(4);bindm[:3,3]=-np.array(m['bind'][j]);matrix=world(nodes[bid])@bindm
            posed+=(v@matrix[:3,:3].T+matrix[:3,3])*weight[:,None];pn+=(norm@matrix[:3,:3].T)*weight[:,None]
        m={**m,'v':posed.tolist(),'n':pn.tolist()};model=np.eye(4);name=name+'_posed'
    if name not in buffers:buffers[name]=buffer(m)
    draws.append((buffers[name],flip@model,data['materials'][n['mat']],n['name']))
textures={}
for m in data['materials'].values():
    p=m.get('texture')
    if p and p not in textures:textures[p]=texture(p)
shadow=U();G.glGenTextures(1,C.byref(shadow));G.glBindTexture(0x0DE1,shadow)
G.glTexImage2D(0x0DE1,0,0x81A6,2048,2048,0,0x1902,0x1405,None)
for k,v in [(0x2801,0x2601),(0x2800,0x2601),(0x2802,0x812F),(0x2803,0x812F)]:G.glTexParameteri(0x0DE1,k,v)
fb=U();G.glGenFramebuffers(1,C.byref(fb));G.glBindFramebuffer(0x8D40,fb);G.glFramebufferTexture2D(0x8D40,0x8D00,0x0DE1,shadow,0);G.glDrawBuffer(0);G.glReadBuffer(0)
assert G.glCheckFramebufferStatus(0x8D40)==0x8CD5
skyvao=U();G.glGenVertexArrays(1,C.byref(skyvao));G.glBindVertexArray(skyvao)
skyebo=U();G.glGenBuffers(1,C.byref(skyebo));G.glBindBuffer(0x8893,skyebo);skyidx=np.array([0,1,2],dtype=np.uint32);G.glBufferData(0x8893,12,skyidx.ctypes.data,0x88E4)
views=json.load(open(ROOT/'Documentation/CinematicViews.json'))
player_y=next(n['pos'][1] for n in data['nodes'] if n['name']=='Player')
views.append(['07_Character_close',[-72.1,player_y+1.5,-30],[-73,player_y+.95,-33],43])
only=sys.argv[1:] or [v[0] for v in views]
out=ROOT/'Documentation/Previews';out.mkdir(parents=True,exist_ok=True)
for name,eye,at,fov in views:
    if name not in only:continue
    eye=np.array(eye)*[1,1,-1];at=np.array(at)*[1,1,-1]
    staging={'01_Calder_and_Sundowner':([-73,.08,-13],40),'04_Wet_bay':([89,.25,-16],0)}
    current_draws=draws
    if name in staging:
        player_node=next(n for n in data['nodes'] if n['name']=='Player')
        dest,angle=staging[name];st=np.eye(4);st[:3,:3]=Rotation.from_euler('y',angle,degrees=True).as_matrix();st[:3,3]=np.array(dest)-st[:3,:3]@np.array(player_node['pos'])
        current_draws=[(buf,flip@st if label.startswith('EliasCalder_') else model,mat,label) for buf,model,mat,label in draws]
    lp=at+np.array([.53,.57,.63])*150;lvp=ortho(50,.1,330)@lookat(lp,at)
    G.glBindFramebuffer(0x8D40,fb);G.glViewport(0,0,2048,2048);G.glClear(0x100);G.glEnable(0x0B71);G.glEnable(0x0B44);G.glFrontFace(0x0900);G.glCullFace(0x0405)
    G.glUseProgram(DEPTH);mat4(DEPTH,'vp',lvp)
    for (vao,count),model,mat,label in current_draws:
        if mat.get('transparent'):continue
        mat4(DEPTH,'model',model);G.glBindVertexArray(vao);G.glDrawElements(4,count,0x1405,None)
    G.glBindFramebuffer(0x8D40,0);G.glViewport(0,0,W,H);G.glClearColor(.65,.7,.69,1);G.glClear(0x4100)
    G.glDisable(0x0B71);G.glDisable(0x0B44);G.glUseProgram(SKY);G.glBindVertexArray(skyvao);G.glDrawElements(4,3,0x1405,None)
    G.glEnable(0x0B71);G.glEnable(0x0B44);G.glUseProgram(PBR)
    mat4(PBR,'vp',perspective(fov,W/H)@lookat(eye,at));mat4(PBR,'lightVP',lvp);G.glUniform3f(uniform(PBR,'eye'),*eye)
    G.glActiveTexture(0x84C1);G.glBindTexture(0x0DE1,shadow);G.glUniform1i(uniform(PBR,'shadowMap'),1)
    opaque=[d for d in current_draws if not d[2].get('transparent')];transparent=[d for d in current_draws if d[2].get('transparent')]
    transparent.sort(key=lambda d:-np.linalg.norm(d[1][:3,3]-eye))
    for passes,alpha in [(opaque,False),(transparent,True)]:
        if alpha:G.glEnable(0x0BE2);G.glBlendFunc(0x0302,0x0303);G.glDepthMask(0)
        for (vao,count),model,mat,label in passes:
            mat4(PBR,'model',model);G.glUniform4f(uniform(PBR,'baseColor'),*mat['color'])
            G.glUniform3f(uniform(PBR,'emission'),*(mat.get('emission') or [0,0,0])[:3]);G.glUniform1f(uniform(PBR,'roughness'),mat['roughness']);G.glUniform1f(uniform(PBR,'metalness'),mat['metalness']);G.glUniform1f(uniform(PBR,'tiling'),mat['tiling'])
            p=mat.get('texture');G.glUniform1i(uniform(PBR,'hasTexture'),int(p is not None));G.glActiveTexture(0x84C0);G.glBindTexture(0x0DE1,textures.get(p,0));G.glUniform1i(uniform(PBR,'baseTex'),0)
            G.glBindVertexArray(vao);G.glDrawElements(4,count,0x1405,None)
        if alpha:G.glDisable(0x0BE2);G.glDepthMask(1)
    G.glFinish();pixels=np.zeros((H,W,4),np.uint8);G.glReadPixels(0,0,W,H,0x1908,0x1401,pixels.ctypes.data)
    im=Image.fromarray(pixels[::-1,:,:3]);draw=ImageDraw.Draw(im);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
    draw.rectangle((0,H-30,W,H),fill='#1e2626');draw.text((18,H-25),'DESERT SHIFT  /  '+name.replace('_',' ')+'   ·   GEOMETRY PREVIEW — NOT A UNITY CAPTURE',font=font,fill='#dfd7bf')
    import io,os
    encoded=io.BytesIO();im.save(encoded,format='PNG');temp=out/(name+'.tmp');temp.write_bytes(encoded.getvalue());os.replace(temp,out/(name+'.png'));print('Rendered',name,flush=True)
