"""Prepare original URP equipment, adapted inmate clothing and CC0 audio."""
from pathlib import Path
from io import BytesIO
import hashlib, json, os, subprocess, zipfile, wave
import numpy as np
from PIL import Image, ImageDraw
from scipy.signal import find_peaks
import unity_writer as uw
from fbx_inspect import read
from download_foundation_assets import atomic_bytes

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT.parents[1]/'rebuild-cache'
RESOURCE='Assets/Game/Resources/BlackstoneFoundation'

def png(path,image):
    out=BytesIO();image.save(out,format='PNG');atomic_bytes(ROOT/path,out.getvalue())

def inmate_texture():
    folder=RESOURCE+'/Characters/Male_Adult_16/'
    im=Image.open(ROOT/(folder+'m019_body_color.png')).convert('RGB')
    root=read(ROOT/(folder+'Male_Adult_16.fbx'))
    mesh=next(n for n in root.child('Objects').children if n.name=='Geometry' and n.props[2]=='Mesh')
    points=mesh.array('Vertices').reshape(-1,3);indices=mesh.array('PolygonVertexIndex')
    uvnode=mesh.child('LayerElementUV');uv=uvnode.array('UV').reshape(-1,2);uvid=uvnode.array('UVIndex')
    materials=mesh.child('LayerElementMaterial').array('Materials')
    mask=Image.new('L',im.size);draw=ImageDraw.Draw(mask);poly=[];corners=[];polygon=0
    for i,index in enumerate(indices):
        end=index<0;vertex=-index-1 if end else index;poly.append(vertex);corners.append(i)
        if not end:continue
        xyz=points[poly];center=xyz.mean(0)
        cloth=17<center[2]<147 and (abs(center[0])<20 or (abs(center[0])<33 and center[2]>130))
        if materials[polygon]==0 and cloth:
            coords=[(float(uv[uvid[c],0])*im.width,(1-float(uv[uvid[c],1]))*im.height) for c in corners]
            draw.polygon(coords,fill=255)
        polygon+=1;poly=[];corners=[]
    values=np.asarray(im,dtype=np.float32)/255
    hsv=np.asarray(im.convert('HSV'),dtype=np.uint8).copy()
    enabled=np.asarray(mask)>0
    # Preserve warm skin pixels at garment seams, while recoloring denim highlights.
    warm=(values[:,:,0]>values[:,:,1]*1.13)&(values[:,:,1]>values[:,:,2]*1.12)&(hsv[:,:,1]>45)
    enabled &= ~warm
    hsv[enabled,0]=17;hsv[enabled,1]=190
    hsv[enabled,2]=np.clip(hsv[enabled,2].astype(float)*1.10+8,0,245).astype('u1')
    result=Image.fromarray(hsv,'HSV').convert('RGB')
    png(folder+'m019_body_inmate.png',result)

def characters():
    inmate_texture();old_art=uw.ART;uw.ART='Assets/Game/Foundation/Art'
    for directory in sorted((ROOT/RESOURCE/'Characters').iterdir()):
        if not directory.is_dir():continue
        for color in directory.glob('*_color.png'):
            stem=color.stem[:-6]
            texture=directory/(stem+'_inmate.png') if directory.name=='Male_Adult_16' and stem.endswith('_body') else color
            normal=directory/(stem+'_normal.png')
            path=uw.material(stem,[1,1,1,1],rough=.58 if stem.endswith('_head') else .72,
                texture=str(texture.relative_to(ROOT)),normal=str(normal.relative_to(ROOT)) if normal.exists() else None)
            dst=str(directory.relative_to(ROOT))+'/'+stem+'.mat'
            material=(ROOT/path).read_text()
            if stem.endswith('_opacity'):
                material=material.replace('m_ValidKeywords: []','m_ValidKeywords: ["_ALPHATEST_ON"]')
                material=material.replace('m_CustomRenderQueue: -1','m_CustomRenderQueue: 2450')
                material=material.replace('RenderType: Opaque','RenderType: TransparentCutout')
                material=material.replace('_AlphaClip: 0','_AlphaClip: 1').replace('_Cutoff: 0.5','_Cutoff: 0.4')
                material=material.replace('_Cull: 2','_Cull: 0').replace('m_DoubleSidedGI: 0','m_DoubleSidedGI: 1')
            uw.write(dst,material);uw.meta(dst,'NativeFormatImporter','  mainObjectFileID: 2100000\n')
            (ROOT/path).unlink();(ROOT/(path+'.meta')).unlink()
        if directory.name=='Male_Adult_07':
            body=str(directory.relative_to(ROOT))+'/m013_body_color.png';normal=str(directory.relative_to(ROOT))+'/m013_body_normal.png'
            im=Image.open(ROOT/body).convert('RGB');values=np.asarray(im,dtype=float)/255
            hsv=np.asarray(im.convert('HSV')).copy()
            warm=(values[:,:,0]>values[:,:,1]*1.13)&(values[:,:,1]>values[:,:,2]*1.12)&(hsv[:,:,1]>45)
            cloth=~warm
            hsv[cloth,0]=148;hsv[cloth,1]=128;hsv[cloth,2]=(hsv[cloth,2]*.8).astype('u1')
            guard=str(directory.relative_to(ROOT))+'/m013_body_guard.png'
            png(guard,Image.fromarray(hsv,'HSV').convert('RGB'))
            path=uw.material('m013_body_guard',[1,1,1,1],rough=.72,texture=guard,normal=normal)
            dst=str(directory.relative_to(ROOT))+'/m013_body_guard.mat';uw.write(dst,(ROOT/path).read_text());uw.meta(dst,'NativeFormatImporter','  mainObjectFileID: 2100000\n')
            (ROOT/path).unlink();(ROOT/(path+'.meta')).unlink()
    uw.ART=old_art

def read_audio(path,cleanup=False):
    cmd=['ffmpeg','-v','error','-i',str(path),'-ac','1','-ar','48000']
    if cleanup:cmd+=['-af','highpass=f=100,lowpass=f=11000,afftdn=nr=18:nf=-32']
    cmd+=['-f','f32le','pipe:1']
    return np.frombuffer(subprocess.check_output(cmd),dtype='<f4').copy()

def save_audio(group,name,array):
    a=np.asarray(array,dtype=np.float64).copy();a-=np.mean(a)
    peak=np.max(np.abs(a))
    if peak>.00001:a*=.76/peak
    fade=min(180,len(a)//8);a[:fade]*=np.linspace(0,1,fade);a[-fade:]*=np.linspace(1,0,fade)
    out=BytesIO()
    with wave.open(out,'wb') as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(48000);wav.writeframes((np.clip(a,-.99,.99)*32767).astype('<i2').tobytes())
    path=RESOURCE+'/Audio/'+group+'/'+name+'.wav';atomic_bytes(ROOT/path,out.getvalue())
    return {'path':path,'sha256':hashlib.sha256(out.getvalue()).hexdigest(),'seconds':len(a)/48000}

def audio():
    art=ROOT/'Tools/ArtSources/FoundationAudio';art.mkdir(parents=True,exist_ok=True)
    required=['KenneyImpact.zip','Gunshots.zip','PistolReload.wav','RifleReload.wav','Sources.json']
    source=art if all((art/name).is_file() for name in required) else CACHE/'audio'
    for p in source.iterdir():
        if p.is_file() and source.resolve()!=art.resolve():atomic_bytes(art/p.name,p.read_bytes())
    selected=CACHE/'audio-selected';selected.mkdir(parents=True,exist_ok=True);provenance=[]
    with zipfile.ZipFile(source/'KenneyImpact.zip') as archive:
        for group,prefix in [('Concrete','footstep_concrete'),('Wood','footstep_wood'),('Grass','footstep_grass'),('Impact','impactMetal_light'),('Punch','impactPunch_medium')]:
            for i in range(5):
                filename=f'{prefix}_{i:03d}.ogg';path=selected/filename;atomic_bytes(path,archive.read('Audio/'+filename))
                a=read_audio(path);provenance.append(save_audio(group,group+str(i),a))
        for i in range(5):
            filename=f'impactPlate_light_{i:03d}.ogg';p=selected/filename;atomic_bytes(p,archive.read('Audio/'+filename));ring=read_audio(p)
            step=read_audio(selected/f'footstep_concrete_{i:03d}.ogg');n=max(len(step),len(ring));mixed=np.zeros(n)
            mixed[:len(step)]+=step;mixed[:len(ring)]+=ring*.17
            provenance.append(save_audio('Metal','Metal'+str(i),mixed))
    with zipfile.ZipFile(source/'Gunshots.zip') as archive:
        for group,filename,requested in [('Pistol','cz.wav',5),('Rifle','sks.wav',4)]:
            path=selected/filename;atomic_bytes(path,archive.read('sounds/'+filename));raw=read_audio(path);clean=read_audio(path,True)
            window=480;blocks=len(raw)//window
            energy=np.sqrt(np.mean(raw[:blocks*window].reshape(blocks,window)**2,axis=1))
            peaks,_=find_peaks(energy,height=energy.max()*.32,distance=85)
            if len(peaks)==0:raise ValueError('No gunshot transients detected')
            for i in range(requested):
                peak=int(peaks[i%len(peaks)])*window;start=max(0,peak-1200);end=min(len(clean),peak+33000)
                clip=clean[start:end]
                if i>=len(peaks):
                    # A fifth variation from four pistol shots, with a small pitch change.
                    count=max(16,int(len(clip)/(1+.035*(i-len(peaks)+1))))
                    clip=np.interp(np.linspace(0,len(clip)-1,count),np.arange(len(clip)),clip)
                provenance.append(save_audio(group,group+str(i),clip))
    for name,filename in [('ReloadPistol','PistolReload.wav'),('ReloadRifle','RifleReload.wav')]:
        provenance.append(save_audio('Handling',name,read_audio(source/filename)))
    for name,original in [('Empty','PhoneClick'),('Draw','ClothHide'),('Swing','CardDeal')]:
        provenance.append(save_audio('Handling',name,read_audio(ROOT/('Assets/Game/Audio/'+original+'.wav'))))
    uw.write('Documentation/Revision05_AudioProvenance.json',json.dumps({'new_clips':len(provenance),'license':'CC0 / original Foley',
        'sources':json.loads((source/'Sources.json').read_text()),'files':provenance,'notes':'Metal footsteps combine CC0 concrete and plate recordings. Gunshots are trimmed, filtered and denoised CC0 recordings. Pistol4 is a small pitch variation of one of four recorded pistol shots. These are prototype sounds.'},indent=2))

def gait():
    rows=[];thresholds=[0]
    for name in ['WalkSlow','Walk','WalkFast','Run','RunFast']:
        root=read(ROOT/('Assets/Game/Foundation/Animations/Rocketbox/'+name+'.fbx'))
        objects={n.props[0]:n for n in root.child('Objects').children if n.props}
        links=[n.props for n in root.child('Connections').children if n.name=='C']
        model=next(n for n in objects.values() if n.name=='Model' and n.props[1].split('\x00')[0]=='Bip01')
        trans=[c[1] for c in links if c[0]=='OP' and c[2]==model.props[0] and c[3]=='Lcl Translation'];axes={}
        for c in links:
            if c[0]=='OP' and c[2] in trans:
                node=objects[c[1]];axes[c[3]]=(node.array('KeyTime'),node.array('KeyValueFloat'))
        duration=max(x[0][-1] for x in axes.values())/46186158000
        dx=float(axes['d|X'][1][-1]-axes['d|X'][1][0]);dz=float(axes['d|Z'][1][-1]-axes['d|Z'][1][0])
        travel=float(np.hypot(dx,dz))*.01;speed=travel/duration;thresholds.append(round(speed,6))
        rows.append({'clip':name,'seconds':duration,'source_root_travel_m':travel,'source_speed_m_s':speed})
    obj={'thresholds':thresholds,'measurements':rows,'method':'Source Root X/Z travel in centimetres divided by duration. Animator Speed is divided by visual scale; imported horizontal root curves are anchored.'}
    uw.write(RESOURCE+'/GaitSpeeds.json',json.dumps(obj,indent=2));uw.write('Documentation/Revision05_GaitMeasurements.json',json.dumps(obj,indent=2))

def metas():
    for base in ['Assets/Game/Foundation','Assets/Game/Resources/BlackstoneFoundation']:
        directory=ROOT/base
        for p in sorted(directory.rglob('*')):
            rel=str(p.relative_to(ROOT))
            if p.name.endswith('.meta') or (ROOT/(rel+'.meta')).exists():continue
            if p.is_dir():
                uw.write(rel+'.meta',f'fileFormatVersion: 2\nguid: {uw.guid(rel)}\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {{}}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n')
            elif p.suffix=='.cs':uw.meta(rel,'MonoImporter','  serializedVersion: 2\n  defaultReferences: []\n  executionOrder: 0\n  icon: {fileID: 0}\n')
            elif p.suffix=='.fbx':uw.meta(rel,'ModelImporter')
            elif p.suffix=='.png':uw.meta(rel,'TextureImporter','  maxTextureSize: 2048\n  textureType: '+('1' if '_normal' in p.name else '0')+'\n')
            elif p.suffix=='.wav':uw.meta(rel,'AudioImporter','  forceToMono: 1\n  loadInBackground: 0\n  preloadAudioData: 1\n')
            elif p.suffix=='.json':uw.meta(rel,'TextScriptImporter')
            else:uw.meta(rel)
        if not (ROOT/(base+'.meta')).exists():
            uw.write(base+'.meta',f'fileFormatVersion: 2\nguid: {uw.guid(base)}\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {{}}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n')

if __name__=='__main__':
    characters();audio();gait();metas();print('Prepared five characters, twelve source animations and 44 audio clips.')
