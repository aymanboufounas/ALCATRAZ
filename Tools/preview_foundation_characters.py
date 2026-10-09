"""Render actual FBX textures/skin samples with Mesa, explicitly outside Unity."""
from pathlib import Path
from io import BytesIO
import ctypes as C, numpy as np, subprocess
from PIL import Image,ImageDraw,ImageFont
from fbx_pose import Character,animation
from download_foundation_assets import atomic_bytes

ROOT=Path(__file__).resolve().parents[1]
code=(ROOT/'Tools/render_preview.py').read_text().split("with gzip.open")[0].replace('W,H=1440,810','W,H=640,640')
code=code.replace('void main(){vec3 n=normalize(normal);','void main(){if(hasTexture==1&&texture(baseTex,uv*tiling).a<.4)discard;vec3 n=normalize(normal);')
backend={'__file__':str(ROOT/'Tools/render_preview.py'),'__name__':'foundation_preview_backend'}
exec(compile(code,'mesa_preview_helpers','exec'),backend)
G=backend['G'];U=backend['U'];PBR=backend['PBR'];uniform=backend['uniform'];mat4=backend['mat4']
lookat=backend['lookat'];perspective=backend['perspective'];buffer=backend['buffer'];texture=backend['texture']
white=U();G.glGenTextures(1,C.byref(white));G.glActiveTexture(0x84C1);G.glBindTexture(0x0DE1,white)
a=np.full((1,1,4),255,dtype='u1');G.glTexImage2D(0x0DE1,0,0x8058,1,1,0,0x1908,0x1401,a.ctypes.data)
G.glTexParameteri(0x0DE1,0x2801,0x2601);G.glTexParameteri(0x0DE1,0x2800,0x2601)
textures={}
G.glEnable(0x0B71);G.glDisable(0x0B44)

def frame(character,clip,t,portrait=False):
    G.glViewport(0,0,640,640);G.glClearColor(.027,.037,.044,1);G.glClear(0x4000|0x0100)
    eye=np.array([.2,1.28,3.05]) if not portrait else np.array([.1,1.58,1.1])
    center=[0,1,0] if not portrait else [0,1.55,.03]
    vp=perspective(42,1,near=.06,far=15)@lookat(eye,center)
    G.glUseProgram(PBR);mat4(PBR,'vp',vp);mat4(PBR,'model',np.eye(4));mat4(PBR,'lightVP',np.eye(4))
    G.glUniform3f(uniform(PBR,'eye'),*eye);G.glUniform3f(uniform(PBR,'emission'),0,0,0)
    G.glUniform1f(uniform(PBR,'roughness'),.67);G.glUniform1f(uniform(PBR,'metalness'),0);G.glUniform1f(uniform(PBR,'tiling'),1)
    G.glUniform4f(uniform(PBR,'baseColor'),1,1,1,1);G.glUniform1i(uniform(PBR,'baseTex'),0);G.glUniform1i(uniform(PBR,'shadowMap'),1)
    G.glActiveTexture(0x84C1);G.glBindTexture(0x0DE1,white)
    for mesh in character.meshes(clip,t):
        vao,count=buffer(mesh);path=str(mesh['texture'].relative_to(ROOT))
        if path not in textures:textures[path]=texture(path)
        G.glActiveTexture(0x84C0);G.glBindTexture(0x0DE1,textures[path]);G.glUniform1i(uniform(PBR,'hasTexture'),1)
        G.glBindVertexArray(vao);G.glDrawElements(0x0004,count,0x1405,None)
    G.glFinish();data=np.empty((640,640,4),dtype='u1');G.glReadPixels(0,0,640,640,0x1908,0x1401,data.ctypes.data)
    return Image.fromarray(data[::-1,:,:3].copy())

def save(path,im):
    output=BytesIO();im.save(output,format='PNG');atomic_bytes(path,output.getvalue())

def main():
    destination=ROOT/'Documentation/FoundationPreviews';destination.mkdir(parents=True,exist_ok=True)
    profiles=['16','07','12','17','20'];idle=animation(ROOT/'Assets/Game/Foundation/Animations/Rocketbox/Idle.fbx')
    characters=[Character(ROOT/('Assets/Game/Resources/BlackstoneFoundation/Characters/Male_Adult_'+p+'/Male_Adult_'+p+'.fbx')) for p in profiles]
    canvas=Image.new('RGB',(1500,770),'#111a20');draw=ImageDraw.Draw(canvas)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',19)
    draw.text((32,24),'ACTUAL SOURCE ASSETS · OFFLINE PREVIEW · NOT A UNITY CAPTURE',font=font,fill='#ccd8d8')
    for i,char in enumerate(characters):
        im=frame(char,idle,.4);im.thumbnail((296,360));canvas.paste(im,(i*300,80))
        face=frame(char,idle,.4,True);face.thumbnail((245,245));canvas.paste(face,(i*300+28,453))
        draw.text((i*300+30,725),['ELIAS / INMATE','JACKET','BLACK INMATE','HOODIE','BODY VARIANTS'][i],font=font,fill='#dfc89a')
    save(destination/'Characters.png',canvas)
    walk=animation(ROOT/'Assets/Game/Foundation/Animations/Rocketbox/Walk.fbx');samples=Image.new('RGB',(1280,405),'#111a20');d=ImageDraw.Draw(samples)
    for i,t in enumerate([0,.3,.6,.9]):
        im=frame(characters[0],walk,t);im.thumbnail((320,640));samples.paste(im,(i*320,60))
    d.text((25,16),'SOURCE WALK CYCLE · ROOT ANCHORED · NOT UNITY PLAY MODE',font=font,fill='#ccd8d8')
    save(destination/'WalkingSamples.png',samples)
    output=destination/'Walking.mp4'
    cmd=['ffmpeg','-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size','640x640','-framerate','25','-i','pipe:0','-an','-c:v','libx264','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(output)]
    process=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    for i in range(60):
        im=frame(characters[0],walk,(i/25)%walk.duration);d=ImageDraw.Draw(im)
        d.rectangle((0,0,640,47),fill='#111a20');d.text((16,13),'OFFLINE SOURCE PREVIEW · NOT UNITY',font=font,fill='white')
        process.stdin.write(np.asarray(im,dtype='u1').tobytes())
    process.stdin.close()
    if process.wait()!=0:raise RuntimeError('Preview video encoding failed')
    print('Rendered Characters.png, WalkingSamples.png and labelled source Walking.mp4.')

if __name__=='__main__':main()
