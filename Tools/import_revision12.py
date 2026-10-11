"""Convert the supplied October 11 archives into deterministic native Unity assets.
Original archives are unchanged; nested archives are safely unpacked outside Assets.
"""
from pathlib import Path
from types import SimpleNamespace
from io import BytesIO
import argparse, hashlib, json, re, shutil, subprocess
import numpy as np
from PIL import Image
import assimp_py as a
import unity_writer as u
import import_supplied_assets as old

BASE='Assets/Game/Supplied/Resources/AlcatrazExtras'
CATALOG=[('Warehouse','abandoned-warehouse-interior-scene(1).zip'),('AcidBarrel','acid-barrel(1).zip'),('ExplosiveBarrel','explosive-barrel(1).zip'),('BridgePack','bridge-pack-low-poly-3d-game-assets.zip'),('UtilityBuilding','industrial-utility-building-game-ready.zip'),('PrisonRoom','dp3-hw9-prison-room.zip'),('Hallway','prison-hallway.zip'),('Watchtower','gta-6-prison-tower-guard-tower-watchtower.zip'),('Shephard','ep4-adrian-shephard.zip'),('Forest','pine-forest-at-sunset.zip'),('Beach','small-beach-lowpoly.zip'),('PunchingBag','punching-bagboxing-bag.zip'),('PokerTable','poker-set.zip'),('PokerProps','poker-set (1).zip'),('SteelStairs','staircase-modular-frame-steel.zip'),('Machete','machete-farcry-3.zip'),('ColtM5','the-hardest-interview-2-free-download.zip'),('M9A3','lowpoly-m9a3-pistol.zip'),('PMX','beretta-pmx-pmxs-comune.zip'),('PX4','beretta-px4-full-size.zip'),('BRX1','beretta-brx1.zip'),('Workshop','alchemists-workshop-stylized-fantasy-scene.zip'),('Store','abandoned-store-for-free.zip')]

def main():
    args=argparse.ArgumentParser();args.add_argument('--archives',type=Path,required=True);args.add_argument('--only');args.add_argument('--blender',default='blender');options=args.parse_args()
    catalog=[]
    for name,archive in CATALOG:
        if options.only and name not in options.only.split(','):continue
        root=u.ROOT/'SourceAssets/Revision12'/name;source=options.archives/archive
        if not root.exists():old.unpack(source,root)
        candidates=[p for p in root.rglob('*') if p.suffix.lower() in ('.fbx','.glb','.dae','.obj','.3ds')]
        if not candidates:
            blend=next(root.rglob('*.blend')); candidates=[blend.with_suffix('.glb')]
            if not candidates[0].exists():
                subprocess.run([options.blender,'--background','--disable-autoexec','--threads','2',str(blend),'--python-exit-code','1','--python',str(Path(__file__).with_name('export_supplied_blend.py'))],check=True)
            if not candidates[0].exists():raise ValueError('Blender did not export '+str(blend))
        model=max(candidates,key=lambda p:p.stat().st_size)
        for folder in ('Meshes','Materials','Textures'):
            generated=u.ROOT/BASE/name/folder
            if generated.exists():
                for stale in sorted(generated.rglob('*'),key=lambda p:len(p.parts),reverse=True):
                    if stale.is_file():stale.unlink()
                    elif stale.is_dir():stale.rmdir()
                generated.rmdir()
        if model.suffix=='.dae':
            import xml.etree.ElementTree as ET
            ET.register_namespace('', 'http://www.collada.org/2005/11/COLLADASchema')
            tree=ET.parse(model)
            for parent_xml in tree.iter():
                for element in list(parent_xml):
                    if element.tag.split('}')[-1] in ('lines','linestrips','points'):parent_xml.remove(element)
            clean=model.with_name('triangles.dae');tree.write(clean);model=clean
        scene=a.import_file(str(model),a.Process_Triangulate|a.Process_JoinIdenticalVertices|a.Process_GenSmoothNormals|a.Process_SortByPType)
        embedded={};gltf_materials={}
        if model.suffix=='.glb':
            doc,binary=old.glb(model)
            gltf_materials={m.get('name',''):m for m in doc.get('materials',[])}
            for index,image in enumerate(doc.get('images',[])):
                if 'bufferView' in image:
                    view=doc['bufferViews'][image['bufferView']];off=view.get('byteOffset',0);embedded['*'+str(index)]=binary[off:off+view['byteLength']]
        images={p.name.lower():p for p in root.rglob('*') if p.suffix.lower() in ('.jpg','.jpeg','.png','.tga','.bmp')}
        u.ART=BASE+'/'+name;u.Node.all=[];u.Node.counter=44000000
        parent=u.Node(name,static=False);materials={};texture_cache={}; material_cache={};solid_materials=set()
        def texture(key,normal=False):
            if isinstance(key,bytes):key=key.decode()
            key=str(key).replace('\\','/');file=images.get(Path(key).name.lower())
            if file is None:file=next((p for n,p in images.items() if Path(n).stem==Path(key).stem.lower()),None)
            if file is None and len(Path(key).stem)>=5:file=next((p for n,p in images.items() if Path(n).stem.startswith(Path(key).stem.lower())),None)
            if file is None and len(Path(key).stem)>=12:file=next((p for n,p in images.items() if len(Path(n).stem)>=12 and Path(key).stem.lower().startswith(Path(n).stem)),None)
            cache=(key,normal)
            if cache in texture_cache:return texture_cache[cache]
            payload=embedded.get(key)
            if file is None and payload is None:return None
            image=Image.open(BytesIO(payload)) if payload else Image.open(file)
            path=u.ART+'/Textures/T'+str(len(texture_cache))+('.png' if normal or image.mode in ('RGBA','P') else '.jpg')
            result=old.texture(path,image,normal=normal,max_size=2048);texture_cache[cache]=result;return result
        for index,mat in enumerate(scene.materials):
            source_material=gltf_materials.get(mat.get('NAME',''),{});two_sided=bool(source_material.get('doubleSided',mat.get('TWOSIDED',False)));masked=source_material.get('alphaMode')=='MASK'
            maps=mat.get('TEXTURES',{})
            diffuse=maps.get(12,maps.get(1,[]));normal=maps.get(6,maps.get(5,[]))
            base=texture(diffuse[0]) if diffuse else None
            if base is None:
                token=str(mat.get('NAME','')).lower().replace('material','').strip('_. ')
                choices=[key for key in images if not any(x in key for x in ('normal','rough','height','metal','ao.','2n.','bump')) and (token and token in key or 'basecolor' in key or 'albedo' in key or 'diffuse' in key or 'color' in key or name=='M9A3' and key=='1.png')]
                if choices:base=texture(choices[0])
            norm=texture(normal[0],True) if normal else None
            if norm is None and name=='AcidBarrel':norm=texture('AcidBarrel.normal2.png',True)
            color=list(mat.get('COLOR_DIFFUSE',(1,1,1,1)));color=(color+[1]*4)[:4]
            if base:color=[1,1,1,1]
            signature=(base,norm,tuple(round(float(c),5) for c in color),two_sided,masked)
            if signature in material_cache:materials[index]=material_cache[signature];continue
            u.ART=BASE+'/'+name
            path=u.material(name+'_M'+str(index),color,rough=.72,texture=base,normal=norm)
            text=(u.ROOT/path).read_text()
            if two_sided:text=text.replace('- _Cull: 2','- _Cull: 0')
            if masked:
                keywords=json.loads(re.search(r'm_ValidKeywords: (.*)',text)[1]);keywords.append('_ALPHATEST_ON')
                text=re.sub(r'm_ValidKeywords: .*','m_ValidKeywords: '+json.dumps(keywords),text).replace('- _AlphaClip: 0','- _AlphaClip: 1').replace('m_CustomRenderQueue: -1','m_CustomRenderQueue: 2450').replace('RenderType: Opaque','RenderType: TransparentCutout')
            u.write(path,text)
            materials[index]=name+'_M'+str(index);material_cache[signature]=materials[index]
            if not masked:solid_materials.add(materials[index])
        triangles=0;bounds=[]; batches={}
        def instance_triangles(node):return sum(scene.meshes[i].num_indices//3 for i in node.mesh_indices)+sum(instance_triangles(c) for c in node.children)
        source_triangles=instance_triangles(scene.root_node)
        def visit(node,world):
            nonlocal triangles
            world=world@np.asarray(node.transformation,dtype=float)
            for mi in node.mesh_indices:
                mesh=scene.meshes[mi];v=np.asarray(mesh.vertices).reshape(-1,3);v=(world@np.c_[v,np.ones(len(v))].T).T[:,:3];v[:,0]*=-1
                n=np.asarray(mesh.normals).reshape(-1,3)@np.linalg.pinv(world[:3,:3]);n[:,0]*=-1;n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-8)
                uv=np.asarray(mesh.texcoords[0]).reshape(len(v),-1)[:,:2] if mesh.texcoords else np.zeros((len(v),2))
                t=np.asarray(mesh.indices).reshape(-1,3)[:,[0,2,1]]
                budget=max(500,int(120000*len(t)/max(1,source_triangles)))
                keep_floor=name=='Warehouse' and scene.materials[mesh.material_index].get('NAME')=='sol'
                if len(t)>budget and not keep_floor and name not in ('Machete','M9A3','PX4','BRX1'):
                    import fast_simplification
                    from scipy.spatial import cKDTree
                    simplified,faces=fast_simplification.simplify(v,t,target_count=budget)
                    nearest=cKDTree(v).query(simplified)[1]
                    v,t,n,uv=simplified,faces,n[nearest],uv[nearest]
                triangles+=len(t);bounds.append((v.min(0),v.max(0)))
                batches.setdefault(materials[mesh.material_index],[]).append((v,n,uv,t))
            for child in node.children:visit(child,world)
        visit(scene.root_node,np.eye(4))
        # Batch static geometry by material. Preserve all transformed triangles
        # while avoiding thousands of tiny renderers and repeated mesh assets.
        for mi,parts in batches.items():
            vs=[];ns=[];uvs=[];faces=[];offset=0
            for v,n,uv,t in parts:
                vs.append(v);ns.append(n);uvs.append(uv);faces.append(t+offset);offset+=len(v)
            v=np.concatenate(vs);n=np.concatenate(ns);uv=np.concatenate(uvs);t=np.concatenate(faces)
            for start in range(0,len(t),20000):
                used,mapped=np.unique(t[start:start+20000],return_inverse=True);key=mi+'_'+str(start//20000)
                u.ART=BASE+'/'+name
                u.save_mesh(key,SimpleNamespace(v=v[used],n=n[used],uv=uv[used],t=mapped.reshape(-1).tolist()),folder='Meshes');u.PREVIEW['meshes'].pop(key,None)
                child=u.Node(key,parent,static=False).render(key,mi)
                if name not in ('Shephard','PokerProps','PunchingBag','Machete','M9A3','PMX','PX4','BRX1','ColtM5') and (name!='Warehouse' or mi in solid_materials):child.meshcollider(key)

        path=BASE+'/'+name+'/'+name+'.prefab';u.write(path,u.HEAD+''.join(u.node_yaml(n,n is parent) for n in u.Node.all));u.meta(path,'PrefabImporter')
        entry={'name':name,'archive':archive,'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'resource':'AlcatrazExtras/'+name+'/'+name,'triangles':triangles,'materials':len(materials),'textures':len(texture_cache),'bounds':[np.min([b[0] for b in bounds],axis=0).tolist(),np.max([b[1] for b in bounds],axis=0).tolist()]}
        conversion=model.with_suffix('.conversion.json')
        if conversion.exists():entry['conversion']=json.loads(conversion.read_text())
        if name=='Warehouse':entry['conversion']['textured_floor_geometry_preserved']=True
        u.write(BASE+'/'+name+'/Source.json',json.dumps(entry,indent=2)+'\n');catalog.append(entry);print(name,triangles,'triangles',len(texture_cache),'textures',flush=True)
    entries=[json.loads(p.read_text()) for p in (u.ROOT/BASE).glob('*/Source.json')]
    u.write(BASE+'/Catalog.json',json.dumps(sorted(entries,key=lambda e:e['name']),indent=2)+'\n')
    for p in sorted((u.ROOT/BASE).rglob('*')):
        rel=str(p.relative_to(u.ROOT))
        if p.is_dir() and not Path(str(p)+'.meta').exists():u.write(rel+'.meta','fileFormatVersion: 2\nguid: '+u.guid(rel)+'\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n')
        elif p.suffix!='.meta' and not Path(str(p)+'.meta').exists():u.meta(rel,'TextScriptImporter' if p.suffix=='.json' else 'DefaultImporter')
    u.write(BASE+'.meta','fileFormatVersion: 2\nguid: '+u.guid(BASE)+'\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n')
    for entry in catalog:
        for p in (u.ROOT/BASE/entry['name']).rglob('*'):
            if p.is_file() and p.suffix in ('.meta','.asset','.mat','.prefab','.json'):
                text=p.read_text();clean='\n'.join(line.rstrip() for line in text.splitlines())+'\n'
                if clean!=text:u.write(str(p.relative_to(u.ROOT)),clean)
if __name__=='__main__':main()
