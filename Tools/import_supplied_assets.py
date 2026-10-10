"""Import the user's nine ZIP assets without changing the originals.

Run: python Tools/import_supplied_assets.py --archives <zip-directory>
Requires Pillow, numpy and libarchive-c. Native glTF imports use Unity glTFast
6.14.1; FBX/OBJ files use Unity's model importer. Large buffers stay below 10 MiB.
"""
from pathlib import Path
from io import BytesIO
import argparse, copy, hashlib, json, shutil, struct, zipfile
from urllib.parse import unquote
import numpy as np
from PIL import Image, ImageChops
import libarchive
import unity_writer as uw
from prepare_dog_import import prepare as prepare_dog

ROOT=Path(__file__).resolve().parents[1]
BASE='Assets/Game/Supplied'
RES=BASE+'/Resources/AlcatrazSupplied'
MAX_BUFFER=10*1024*1024
Image.MAX_IMAGE_PIXELS=None

def sha(data):return hashlib.sha256(data).hexdigest()
def write(path,data):
    p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    return path
def metadata(path,kind='DefaultImporter',body=''):
    if 'folderAsset:' in body:
        write(str(path)+'.meta',('fileFormatVersion: 2\nguid: '+uw.guid(path)+'\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n').encode());return
    uw.meta(path,kind,body)
def texture(path,image,normal=False,max_size=2048,linear=False):
    image=image.copy();image.thumbnail((max_size,max_size),Image.Resampling.LANCZOS)
    out=BytesIO()
    if path.endswith('.jpg'):
        for quality in (90,84,78,72,66):
            out=BytesIO();image.convert('RGB').save(out,'JPEG',quality=quality,subsampling=2,optimize=True)
            if out.tell()<=MAX_BUFFER:break
        if out.tell()>MAX_BUFFER:raise ValueError('Texture exceeds publishing limit: '+path)
    else:image.save(out,'PNG',compress_level=6)
    write(path,out.getvalue())
    metadata(path,'TextureImporter',f'  serializedVersion: 13\n  mipmaps:\n    enableMipMap: 1\n    sRGBTexture: {0 if normal or linear else 1}\n  textureType: {1 if normal else 0}\n  maxTextureSize: {max_size}\n  isReadable: 0\n  textureSettings:\n    filterMode: 1\n    aniso: 4\n    wrapU: 0\n    wrapV: 0\n')
    return path
def unpack(source,target):
    target.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(source) as archive:
        for item in archive.infolist():
            if item.is_dir():continue
            p=target/item.filename
            if not p.resolve().is_relative_to(target.resolve()):raise ValueError('Unsafe archive path')
            p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(archive.read(item))
    for nested in list(target.rglob('*.zip')):
        unpack(nested,nested.parent/'unpacked')
    for nested in list(target.rglob('*.rar')):
        directory=nested.parent/'unpacked';directory.mkdir(exist_ok=True)
        with libarchive.file_reader(str(nested)) as archive:
            for item in archive:
                p=directory/item.pathname
                if not p.resolve().is_relative_to(directory.resolve()):raise ValueError('Unsafe RAR path')
                if item.isdir:p.mkdir(parents=True,exist_ok=True)
                else:
                    p.parent.mkdir(parents=True,exist_ok=True)
                    with p.open('wb') as output:
                        for block in item.get_blocks():output.write(block)
def glb(path):
    data=path.read_bytes();magic,version,size=struct.unpack_from('<III',data)
    if magic!=0x46546c67 or version!=2 or size!=len(data):raise ValueError('Invalid GLB')
    length,kind=struct.unpack_from('<II',data,12)
    if kind!=0x4e4f534a:raise ValueError('Missing GLB JSON')
    document=json.loads(data[20:20+length]);offset=20+length
    n,kind=struct.unpack_from('<II',data,offset)
    if kind!=0x004e4942:raise ValueError('Missing GLB binary')
    return document,data[offset+8:offset+8+n]
def rewrite_gltf(document,binary,directory,name,island=False):
    """Keep geometry/rig/animation bytes unchanged; externalize and optimize images."""
    original=copy.deepcopy(document);old_views=original.get('bufferViews',[])
    image_views={im['bufferView'] for im in original.get('images',[]) if 'bufferView' in im}
    for index,image in enumerate(document.get('images',[])):
        if 'bufferView' in image:
            view=old_views[image['bufferView']];a=view.get('byteOffset',0)
            payload=binary[a:a+view['byteLength']]
        else:
            payload=(directory/unquote(image['uri'])).read_bytes()
        with Image.open(BytesIO(payload)) as im:
            suffix='.jpg' if im.mode=='RGB' and (island or im.format=='JPEG') else '.png'
            filename=f'{name}_Texture_{index:02d}'+suffix
            texture(RES+'/'+name+'/'+filename,im,max_size=8192 if island else 2048)
        image.clear();image['uri']=filename
    if island:
        for material in document.get('materials',[]):
            pbr=material.setdefault('pbrMetallicRoughness',{})
            pbr['metallicFactor']=0;pbr['roughnessFactor']=.92
    buffers=[];current=bytearray();views=[];remap={};checks=[]
    def flush():
        nonlocal current
        if not current:return
        filename=f'{name}_Buffer_{len(buffers):02d}.bin'
        write(RES+'/'+name+'/'+filename,current);metadata(RES+'/'+name+'/'+filename)
        buffers.append({'uri':filename,'byteLength':len(current)})
        current=bytearray()
    for i,old in enumerate(old_views):
        if i in image_views:continue
        if old['byteLength']>MAX_BUFFER:raise ValueError('One buffer view exceeds transport limit')
        padding=(-len(current))%4
        if current and len(current)+padding+old['byteLength']>MAX_BUFFER:flush();padding=0
        current.extend(b'\0'*padding)
        view=dict(old);view['buffer']=len(buffers);view['byteOffset']=len(current)
        start=old.get('byteOffset',0);payload=binary[start:start+old['byteLength']]
        current.extend(payload);remap[i]=len(views);views.append(view)
        checks.append(sha(payload))
    flush()
    def remap_views(item):
        if isinstance(item,dict):
            for key,value in item.items():
                if key=='bufferView':item[key]=remap[value]
                else:remap_views(value)
        elif isinstance(item,list):
            for child in item:remap_views(child)
    remap_views(document.get('accessors',[]))
    document['bufferViews']=views;document['buffers']=buffers
    path=RES+'/'+name+'/'+name+'.gltf'
    write(path,(json.dumps(document,ensure_ascii=False,separators=(',',':'))+'\n').encode())
    metadata(path,'ScriptedImporter',
      '  internalIDToNameTable: []\n  serializedVersion: 2\n'
      '  script: {fileID: 11500000, guid: 715df9372183c47e389bb6e19fbc3b52, type: 3}\n'
      '  editorImportSettings:\n    generateSecondaryUVSet: 0\n'
      '  importSettings:\n    nodeNameMethod: 1\n    animationMethod: 1\n'
      '    generateMipMaps: 1\n    texturesReadable: 0\n    anisotropicFilterLevel: 4\n'
      '  instantiationSettings:\n    mask: -1\n    layer: 0\n    skinUpdateWhenOffscreen: 0\n    lightIntensityFactor: 1\n    sceneObjectCreation: 1\n')
    # Prove every non-image source view survived the repack byte-for-byte.
    packed_buffers=[(ROOT/RES/name/b['uri']).read_bytes() for b in buffers]
    for index,view in enumerate(views):
        payload=packed_buffers[view['buffer']]
        start=view['byteOffset'];assert sha(payload[start:start+view['byteLength']])==checks[index]
    return {'resource':f'AlcatrazSupplied/{name}/{name}','format':'gltf',
            'source_views_preserved':len(checks),'geometry_rig_animation_bytes':'PASS',
            'buffers':len(buffers),'animations':[a.get('name','') for a in document.get('animations',[])],
            'meshes':len(document.get('meshes',[]))}
def material(path,base,normal=None,metal=None,rough=None,color=(1,1,1,1),transparent=False):
    name=Path(path).stem;uw.ART=str(Path(path).parent.parent)
    pack=None
    if metal and rough:
        m=Image.open(ROOT/metal).convert('L');r=Image.open(ROOT/rough).convert('L').resize(m.size)
        packed=Image.merge('RGBA',(m,Image.new('L',m.size,0),Image.new('L',m.size,0),ImageChops.invert(r)))
        pack=path.replace('.mat','_MetalSmooth.png');texture(pack,packed,linear=True)
    generated=uw.material(name,list(color),.82,1 if pack else 0,texture=base,normal=normal,surface=pack,transparent=transparent)
    # unity_writer stores materials in Art/Materials; move to the catalogued path.
    old=ROOT/generated;target=ROOT/path
    if old!=target:
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(old.read_bytes())
        old.unlink();Path(str(old)+'.meta').unlink(missing_ok=True)
        metadata(path,'NativeFormatImporter','  mainObjectFileID: 2100000\n')
    if base and Image.open(ROOT/base).mode in ('RGBA','P') and not transparent:
        text=target.read_text().replace('    - _AlphaClip: 0','    - _AlphaClip: 1').replace('    - _Cull: 2','    - _Cull: 0')
        text=text.replace('m_ValidKeywords: []','m_ValidKeywords: ["_ALPHATEST_ON"]').replace('RenderType: Opaque','RenderType: TransparentCutout')
        target.write_text(text)
    return path
def copy_model(source,name):
    path=RES+'/'+name+'/'+name+source.suffix.lower()
    write(path,source.read_bytes());metadata(path,'ModelImporter','  serializedVersion: 22200\n')
    return {'resource':f'AlcatrazSupplied/{name}/{name}','format':source.suffix[1:]}
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--archives',type=Path,required=True)
    parser.add_argument('--work',type=Path,default=ROOT/'SourceAssets/Supplied09');args=parser.parse_args()
    catalog={'revision':'09','importer':'com.unity.cloud.gltfast@6.14.1','assets':{},'materials':{}}
    names=['alcatraz','gun-10mm','high-poly-pbr-revolvergun','tactical-helmet-with-headset-game-ready',
      'tactical-plate-carrier-vest-game-ready','police','police-dog','helicopters-mh-6-little-bird','the-house-lost-at-sea']
    extracted={}
    for name in names:
        archive=args.archives/(name+'.zip');directory=args.work/name;unpack(archive,directory);extracted[name]=directory
        catalog['assets'][name]={'archive_sha256':sha(archive.read_bytes()),'uploaded_name':archive.name}
    for original,name in [('alcatraz','Island'),('police-dog','Dog'),
      ('tactical-helmet-with-headset-game-ready','Helmet'),('tactical-plate-carrier-vest-game-ready','Vest')]:
        source=next(extracted[original].rglob('*.glb'));document,binary=glb(source)
        entry=rewrite_gltf(document,binary,source.parent,name,island=name=='Island')
        entry['model_sha256']=sha(source.read_bytes());catalog['assets'][original].update(entry)
        print('Imported',name,entry['source_views_preserved'],'preserved views',flush=True)
        if name=='Dog':
            report=prepare_dog(ROOT/RES/name)
            (ROOT/'Validation/Revision09_DogImportChecks.json').write_text(json.dumps(report,indent=2)+'\n')
            catalog['assets'][original]['import_compatibility']={
                'skin_joints':report['skin_joints_after'],'nodes':report['nodes_after'],
                'clips':report['clips'],'weighted_deformation':'PASS',
                'packaged_model_sha256':report['model_sha256']}
            catalog['assets'][original]['source_views_preserved_before_rig_compaction']=entry['source_views_preserved']
            del catalog['assets'][original]['source_views_preserved']
            catalog['assets'][original]['geometry_rig_animation_bytes']='PASS: mesh and retained animation payloads unchanged; unused joints removed and skin indices remapped'
    source=next(extracted['helicopters-mh-6-little-bird'].rglob('*.gltf'))
    document=json.loads(source.read_text());binary=(source.parent/unquote(document['buffers'][0]['uri'])).read_bytes()
    catalog['assets']['helicopters-mh-6-little-bird'].update(rewrite_gltf(document,binary,source.parent,'Helicopter'))
    for original,name in [('gun-10mm','Pistol10mm'),('high-poly-pbr-revolvergun','Revolver'),('police','Police')]:
        extension='*.obj' if name=='Police' else '*.fbx';source=next(extracted[original].rglob(extension))
        catalog['assets'][original].update(copy_model(source,name))
        if name=='Police':
            for source in source.parent.glob('*.jpg'):texture(RES+'/'+name+'/'+source.name,Image.open(source))
            shutil.copyfile(source.parent/'policeman.mtl',ROOT/RES/name/'policeman.mtl');metadata(RES+'/'+name+'/policeman.mtl')
            bases={'policeman_head':'policeman_head_d.jpg','policeman_body':'policeman_body_d.jpg','policeman_gun':'policeman_gun_d.jpg'}
            # Keep original names: Unity calls OnAssignMaterialModel with these names.
            for key,filename in bases.items():
                path=BASE+'/Materials/Police_'+key+'.mat'
                material(path,RES+'/'+name+'/'+filename);catalog['materials'][key]=path
        else:
            folder=extracted[original]/('source/unpacked/Textures' if name=='Pistol10mm' else 'textures')
            sources=['Gun_BaseColor.png','Gun_Normal.png','Gun_Metallic.png','Gun_Roughness.png'] if name=='Pistol10mm' else ['gun_BC.png','None_normal.jpg','gun_M.png','gun_R.png']
            imported=[]
            for i,filename in enumerate(sources):
                path=RES+'/'+name+'/'+filename;texture(path,Image.open(folder/filename),normal=i==1,linear=i>=2);imported.append(path)
            path=BASE+'/Materials/'+name+'.mat';material(path,*imported)
            catalog['materials']['Gun' if name=='Pistol10mm' else 'Material.002']=path
    # FBX remains native, with byte-exact parts to fit publishing limits.
    source=next(extracted['the-house-lost-at-sea'].rglob('*.fbx'));payload=source.read_bytes();parts=[]
    for i,start in enumerate(range(0,len(payload),8*1024*1024)):
        path=BASE+f'/HouseSource/House.part{i+1:03d}.bytes';write(path,payload[start:start+8*1024*1024]);metadata(path);parts.append(path)
    spec={'destination':'Assets/GeneratedSupplied/Resources/AlcatrazSupplied/House/House.fbx','parts':parts,
      'sha256':sha(payload),'bytes':len(payload)}
    write(BASE+'/HouseSource/HouseParts.json',(json.dumps(spec,indent=2)+'\n').encode());metadata(BASE+'/HouseSource/HouseParts.json','TextScriptImporter')
    assert b''.join((ROOT/p).read_bytes() for p in parts)==payload
    catalog['assets']['the-house-lost-at-sea'].update(resource='AlcatrazSupplied/House/House',format='fbx-parts',reconstruction='PASS')
    texture_sources={}
    for source in (extracted['the-house-lost-at-sea']/'textures').iterdir():
        stem=source.stem.replace('-1','_Alpha');path=BASE+'/HouseSource/Textures/'+stem+('.png' if source.suffix=='.png' else '.jpg')
        texture(path,Image.open(source),max_size=4096);texture_sources[stem]=path
    from fbx_inspect import read
    fbx=read(source if source.suffix=='.fbx' else next(extracted['the-house-lost-at-sea'].rglob('*.fbx')))
    objects={n.props[0]:n for n in fbx.child('Objects').children}
    links=fbx.child('Connections').children
    for node in objects.values():
        if node.name!='Material':continue
        name=node.props[1].split('\x00')[0];base=None
        for connection in links:
            if len(connection.props)<4 or connection.props[2]!=node.props[0]:continue
            connected=objects.get(connection.props[1])
            if connected is None or connected.name!='Texture':continue
            filename=connected.child('RelativeFilename')
            if filename and connection.props[3] in ['DiffuseColor','Diffuse','TransparencyFactor']:
                key=Path(str(filename.props[0]).replace('\\','/')).stem
                base=texture_sources.get(key)
                if key=='Pack02' and name in ['WindowGlassShdr','WindowLightGlow','Debris']:
                    base=texture_sources.get('Pack02_Alpha',base)
        if base is None:
            base=texture_sources.get('VegetHH_SD' if 'Shrub' in name or 'Grass' in name or name=='Branch' else 'Bush01' if 'Bush' in name else '')
        values=node.child('Properties70');color=(1,1,1,1)
        if base is None and values:
            diffuse=next((p for p in values.children if p.props[0]=='DiffuseColor'),None)
            if diffuse:color=tuple(diffuse.props[-3:])+(1,)
        path=BASE+'/Materials/House_'+name+'.mat';material(path,base,color=color,transparent='Glass' in name)
        catalog['materials'][name]=path
    manifest=ROOT/'Packages/manifest.json';data=json.loads(manifest.read_text())
    data['dependencies']['com.unity.cloud.gltfast']='6.14.1';manifest.write_text(json.dumps(data,indent=2)+'\n')
    output=RES+'/Catalog.json';write(output,(json.dumps(catalog,indent=2)+'\n').encode());metadata(output,'TextScriptImporter')
    # All files and folders receive deterministic metadata.
    for p in sorted((ROOT/BASE).rglob('*')):
        rel=str(p.relative_to(ROOT))
        if p.is_dir():metadata(rel,'DefaultImporter','  folderAsset: yes\n')
        elif p.suffix!='.meta' and not Path(str(p)+'.meta').exists():metadata(rel)
    metadata(BASE,'DefaultImporter','  folderAsset: yes\n')
    proof={'status':'PASS','assets':len(catalog['assets']),'geometry_rig_animation_views_preserved_before_compaction':
      sum(e.get('source_views_preserved',e.get('source_views_preserved_before_rig_compaction',0)) for e in catalog['assets'].values()),
      'house_parts':'byte-exact','max_file_bytes':max(p.stat().st_size for p in (ROOT/BASE).rglob('*') if p.is_file()),
      'scope':'Archive extraction, native file integrity and glTF buffer repacking; Unity import and rendering unverified'}
    (ROOT/'Validation/Revision09_SuppliedAssets.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2))
if __name__=='__main__':main()
