"""Offline asset integrity checks. Does not substitute for Unity compilation or Play Mode."""
from pathlib import Path
import re,json,sys,ast,struct
import numpy as np
import yaml
from PIL import Image
import wave
ROOT=Path(__file__).resolve().parents[1]
errors=[];warnings=[];counts={}
def fail(message):errors.append(message)
official={
 '933532a4fcc9baf4fa0491de14d08ed7':'URP/Lit shader',
 'bf2edee5c58d82540a51f03df9d42094':'UniversalRenderPipelineAsset script',
 'de640fe3d0db1804a85f9fc8f5cadab6':'UniversalRendererData script',
 '41439944d30ece34e96484bdb6645b55':'URP PostProcessData asset',
 'f62c9c65cf3354c93be831c8bc075510':'URP ScreenSpaceAmbientOcclusion script'}
assets={}
for p in (ROOT/'Assets').rglob('*.meta'):
    m=re.search(r'^guid: ([a-f0-9]{32})$',p.read_text(),re.M)
    if not m:fail('Missing GUID: '+str(p.relative_to(ROOT)));continue
    if m[1] in assets:fail('Duplicate GUID: '+str(p.relative_to(ROOT)))
    assets[m[1]]=Path(str(p)[:-5])
for p in (ROOT/'Assets').rglob('*'):
    if p.is_file() and p.suffix!='.meta' and not Path(str(p)+'.meta').exists():fail('Missing meta: '+str(p.relative_to(ROOT)))

native=[p for p in ROOT.rglob('*') if p.suffix in ['.unity','.prefab','.mat','.asset','.controller','.anim']]
yaml_docs=0;external=set();mesh_vertices=0;mesh_triangles=0;skinmesh=0
for p in native:
    rel=str(p.relative_to(ROOT));txt=p.read_text();anchors=re.findall(r'^--- !u!\d+ &(-?\d+)',txt,re.M)
    if len(set(anchors))!=len(anchors):fail('Duplicate local file ID: '+rel)
    ids=set(anchors)
    for fileid in re.findall(r'\{fileID: (-?\d+)\}',txt):
        if fileid!='0' and fileid not in ids:fail(f'Dangling local reference {fileid}: {rel}')
    for g in re.findall(r'guid: ([a-f0-9]{32})',txt):
        if g in assets:
            if not assets[g].exists():fail('Missing target '+str(assets[g]))
        elif g in official:external.add(official[g])
        elif g!='0'*32:fail(f'Unresolved GUID {g}: {rel}')
    clean=re.sub(r'^%.*\n','',txt,flags=re.M);clean=re.sub(r'^--- !u!\d+ &-?\d+','---',clean,flags=re.M)
    try:docs=list(yaml.load_all(clean,Loader=yaml.CSafeLoader));yaml_docs+=len(docs)
    except Exception as e:fail('YAML parse '+rel+': '+str(e)[:180]);continue
    for doc in docs:
        if not isinstance(doc,dict):fail('Empty native document '+rel);continue
        if 'Mesh' in doc:
            m=doc['Mesh'];vd=m['m_VertexData'];vcount=vd['m_VertexCount'];raw=bytes.fromhex(re.search(r'_typelessdata: ([0-9a-f]+)',txt)[1]);stride=vd['m_DataSize']//vcount
            if len(raw)!=vd['m_DataSize'] or len(raw)!=vcount*stride:fail('Vertex buffer length '+rel)
            verts=np.ndarray((vcount,3),dtype='<f4',buffer=raw,strides=(stride,4))
            normals=np.ndarray((vcount,3),dtype='<f4',buffer=raw,offset=12,strides=(stride,4))
            if not np.isfinite(verts).all() or not np.isfinite(normals).all():fail('Non-finite mesh attributes '+rel)
            indices=np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: ([0-9a-f]+)',txt)[1]),dtype='<u4' if m['m_IndexFormat'] else '<u2')
            if len(indices)%3 or len(indices)!=m['m_SubMeshes'][0]['indexCount'] or indices.max()>=vcount:fail('Invalid triangle buffer '+rel)
            if stride==80:
                skinmesh+=1;weights=np.ndarray((vcount,4),dtype='<f4',buffer=raw,offset=48,strides=(stride,4));bones=np.ndarray((vcount,4),dtype='<u4',buffer=raw,offset=64,strides=(stride,4))
                if not np.allclose(weights.sum(1),1,atol=1e-5) or np.any(weights<0):fail('Invalid skin weights '+rel)
                if bones.max()>=len(m['m_BindPose']):fail('Invalid bone index '+rel)
            mesh_vertices+=vcount;mesh_triangles+=len(indices)//3
        if 'SkinnedMeshRenderer' in doc:
            sm=doc['SkinnedMeshRenderer']
            if not sm.get('m_Bones') or not sm.get('m_Mesh',{}).get('guid'):fail('Incomplete skin renderer '+rel)
        if 'AnimationClip' in doc:
            ac=doc['AnimationClip']
            if not ac['m_RotationCurves'] or not ac['m_ClipBindingConstant']['genericBindings']:fail('Empty animation '+rel)

# Balanced token checks catch truncation, but are explicitly not a C# compiler.
for p in (ROOT/'Assets').rglob('*.cs'):
    s=p.read_text();s=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S);s=re.sub(r'@?"(?:""|\\.|[^"\\])*"','""',s);stack=[]
    for c in s:
        if c in '({[':stack.append(c)
        elif c in ')}]':
            if not stack or '({['[')}]'.index(c)]!=stack.pop():fail('C# delimiter mismatch '+str(p.relative_to(ROOT)));break
    if stack:fail('C# unclosed delimiter '+str(p.relative_to(ROOT)))
    if p.stem!='IInteractable' and not re.search(r'\b(class|struct|enum)\s+'+re.escape(p.stem)+r'\b',p.read_text()):fail('C# file/type mismatch '+p.name)
for p in (ROOT/'Tools').glob('*.py'):
    try:ast.parse(p.read_text())
    except SyntaxError as e:fail('Python syntax '+p.name+': '+str(e))
for p in ROOT.rglob('*.png'):
    try:
        with Image.open(p) as image:image.verify()
        with Image.open(p) as image:image.load()
    except Exception as e:fail('Invalid image '+str(p.relative_to(ROOT))+': '+str(e))
for p in (ROOT/'Assets').rglob('*.wav'):
    try:
        with wave.open(str(p),'rb') as sound:
            expected=sound.getnframes()*sound.getnchannels()*sound.getsampwidth()
            if len(sound.readframes(sound.getnframes()))!=expected:fail('Truncated audio '+str(p.relative_to(ROOT)))
    except Exception as e:fail('Invalid audio '+str(p.relative_to(ROOT))+': '+str(e))

scene=(ROOT/'Assets/_DesertShift/Scenes/SC_DesertTown.unity').read_text()
for name in ['Player','Sundowner_84_RV','Sunset_Splash_CarWash','Global Volume','Light probe layout','Main Camera']:
    if f'm_Name: "{name}"' not in scene:fail('Required scene object absent: '+name)
manifest=json.loads((ROOT/'Packages/manifest.json').read_text())
for package in ['com.unity.render-pipelines.universal','com.unity.inputsystem','com.unity.cinemachine']:
    if package not in manifest['dependencies']:fail('Missing official package '+package)

counts={'native_files':len(native),'yaml_documents':yaml_docs,'asset_guids':len(assets),
        'mesh_vertices':mesh_vertices,'mesh_triangles':mesh_triangles,'weighted_meshes':skinmesh,
        'csharp_files':len(list((ROOT/'Assets').rglob('*.cs'))),
        'animation_clips':len(list((ROOT/'Assets/_DesertShift/Animations/Character').glob('*.anim')))}
report={'offline_integrity':'PASS' if not errors else 'FAIL','counts':counts,'errors':errors,'warnings':warnings,
        'official_package_bindings_not_loaded_by_unity':sorted(external),
        'not_performed':['Unity editor import','C# compilation against Unity assemblies','Unity Play Mode','Humanoid Avatar validation inside Unity','Live movement and interaction tests','URP shader compilation','Windows player build','1080p FPS measurement','Lightmap / occlusion bake'],
        'visual_qa':'Separate Mesa geometry previews; not Unity render captures'}
(ROOT/'Validation').mkdir(exist_ok=True);(ROOT/'Validation/OfflineValidation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
