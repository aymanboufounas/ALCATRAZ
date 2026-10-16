"""Verify committed environment resources and the deterministic ground-cover bake.

This is source/native validation, not a Unity shader compiler or rendering test.
"""
from pathlib import Path
import hashlib,json,re
import numpy as np
import yaml
from PIL import Image
import author_environment_dressing as dressing

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'Assets/Game/Alcatraz/Resources/Alcatraz/SurfaceDetails'

def native(path):
    text=path.read_text()
    text=re.sub(r'^%.*\n','',text,flags=re.M)
    text=re.sub(r'^--- !u!\d+ &-?\d+','---',text,flags=re.M)
    return list(yaml.safe_load_all(text))[0]['Material']

def helipad_support():
    # Clip the unchanged source triangles to the complete pad footprint. This
    # catches a ridge between ray samples rather than just repeating the probes.
    faces=[]
    folder=ROOT/'Assets/Game/Supplied/Resources/AlcatrazSupplied/Baked/Meshes'
    for path in sorted(folder.glob('Island_*.asset')):
        vertices,_,indices=dressing.native_mesh(str(path.relative_to(ROOT)))
        triangles=vertices[indices]
        keep=(triangles[:,:,0].min(1)<=-145)&(triangles[:,:,0].max(1)>=-157)&(triangles[:,:,2].min(1)<=1)&(triangles[:,:,2].max(1)>=-11)
        faces.extend(triangles[keep])
    def clip(poly,axis,bound,sign):
        out=[]
        for i,a in enumerate(poly):
            b=poly[(i+1)%len(poly)]
            inside_a=sign*(a[axis]-bound)>=0;inside_b=sign*(b[axis]-bound)>=0
            if inside_a:out.append(a)
            if inside_a!=inside_b:out.append(a+(b-a)*((bound-a[axis])/(b[axis]-a[axis])))
        return out
    highest=-float('inf')
    for face in faces:
        polygon=list(face)
        for axis,bound,sign in ((0,-157,1),(0,-145,-1),(2,-11,1),(2,1,-1)):
            if polygon:polygon=clip(polygon,axis,bound,sign)
        if polygon:highest=max(highest,max(float(p[1]) for p in polygon))
    faces=np.asarray(faces);a,b,c=faces[:,0],faces[:,1],faces[:,2];e=b-a;f=c-a
    determinant=e[:,0]*f[:,2]-e[:,2]*f[:,0];valid=np.abs(determinant)>1e-9
    determinant=np.where(valid,determinant,1)
    def height(x,z):
        u=((x-a[:,0])*f[:,2]-(z-a[:,2])*f[:,0])/determinant
        v=(e[:,0]*(z-a[:,2])-e[:,2]*(x-a[:,0]))/determinant
        selected=valid&(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7)
        return float((a[:,1]+u*e[:,1]+v*f[:,1])[selected].max(initial=-float('inf')))
    old=max(height(-151+x,-5+z) for x in (-5,0,5) for z in (-5,0,5))+.07
    new=max(height(-151+x*.5,-5+z*.5) for x in range(-12,13) for z in range(-12,13))+.11
    return {'exact_source_peak_y':highest,'old_pad_top_y':old,'new_pad_top_y':new,
            'old_scan_intrusion_metres':max(0,highest-old),'new_clearance_metres':new-highest,'startup_ray_samples':625}

def validate():
    errors=[];checks=0
    def check(value,message):
        nonlocal checks
        checks+=1
        if not value:errors.append(message)
    guids={}
    for path in (ROOT/'Assets').rglob('*.meta'):
        match=re.search(r'^guid: (\w+)',path.read_text(),re.M)
        if match:guids[match[1]]=Path(str(path)[:-5])
    source=ROOT/'Assets/Game/Supplied/Resources/AlcatrazSupplied/Baked/Materials/Island_0.mat'
    scan=native(source)
    check(scan['m_Shader']['guid']=='933532a4fcc9baf4fa0491de14d08ed7','Original scan material remains standard URP Lit.')
    profile=native(BASE/'IslandSurface.mat')
    check(profile['m_Shader']['guid']=='2c3ca6401f684c1caac06a2213adeb4c','Resource profile binds the committed detail shader.')
    floats={key:value for row in profile['m_SavedProperties']['m_Floats'] for key,value in row.items()}
    check(0<float(floats['_GroundAlbedoReplacement'])<1,'Selective ground resurfacing has a bounded blend.')
    tex={key:value for row in profile['m_SavedProperties']['m_TexEnvs'] for key,value in row.items()}
    for property in ('_GroundMap','_GroundNormal','_GroundSurface','_WallMap','_WallNormal','_WallSurface'):
        path=guids.get(tex[property]['m_Texture'].get('guid'))
        check(path is not None and path.is_file(),property+' resolves an existing PBR input.')
        if path:
            check(Image.open(path).size==(2048,2048),property+' retains its real 2K source dimensions.')
            metadata=Path(str(path)+'.meta').read_text()
            if property.endswith('Normal'):check('textureType: 1' in metadata,property+' is imported as a normal map.')
            elif property.endswith('Surface'):check('sRGBTexture: 0' in metadata,property+' remains linear packed data.')
    for filename in ('HelipadConcrete.mat','DockTimber.mat'):
        mat=native(BASE/filename)
        properties={key:value for row in mat['m_SavedProperties']['m_TexEnvs'] for key,value in row.items()}
        for key in ('_BaseMap','_BumpMap','_MetallicGlossMap','_OcclusionMap'):
            check(properties[key]['m_Texture'].get('guid') in guids,filename+' resolves '+key)
        check('_NORMALMAP' in mat['m_ValidKeywords'] and '_METALLICSPECGLOSSMAP' in mat['m_ValidKeywords'],filename+' enables its real normal/surface maps.')
    generated,manifest=dressing.author()
    for path,payload in generated.items():check((ROOT/path).read_bytes()==payload,'Ground-cover regeneration differs: '+path)
    for path,digest in manifest['source_hashes'].items():
        check(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,'Ground-cover source changed: '+path)
    check(manifest['vertices']<=manifest['vertex_budget'],'Ground cover remains inside its explicit geometry budget.')
    prefab=(ROOT/'Assets/Game/Alcatraz/Resources/Alcatraz/EnvironmentDressing/SuppliedGroundCover.prefab').read_text()
    check('MeshCollider:' not in prefab and 'BoxCollider:' not in prefab and 'CapsuleCollider:' not in prefab,'Detail prefab has no physics components.')
    vertices=triangles=0
    for chunk in manifest['chunks']:
        text=(ROOT/chunk['path']).read_text()
        count=int(re.search(r'm_VertexCount: (\d+)',text)[1]);raw=bytes.fromhex(re.search(r'_typelessdata: (\w+)',text)[1])
        floats=np.frombuffer(raw,'<f4').reshape(count,-1)
        indices=np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: (\w+)',text)[1]),'<u4' if 'm_IndexFormat: 1' in text else '<u2')
        check(np.isfinite(floats).all() and len(indices)%3==0 and indices.max()<count,'Invalid native chunk buffer: '+chunk['path'])
        vertices+=count;triangles+=len(indices)//3
    check(vertices==manifest['vertices'] and triangles==manifest['triangles'],'Native geometry totals match the placement manifest.')
    pad=helipad_support()
    check(pad['new_clearance_metres']>.05,'The complete clipped scan stays below the new helipad, including between sampled points.')
    return {'status':'FAIL' if errors else 'PASS','checks':checks,'errors':errors,
      'scan_renderers':11,'helipad_support':pad,'ground_cover':{'tufts':manifest['tufts'],'clusters':manifest['accepted_clusters'],'chunks':len(manifest['chunks']),'vertices':vertices,'triangles':triangles,'colliders':0},
      'scope':'PBR resource dependencies, original input identity, deterministic supported placement and native mesh buffers.',
      'unity_shader_compilation_verified':False,'unity_rendered_quality_verified':False,'gpu_performance_verified':False}

if __name__=='__main__':
    result=validate();print(json.dumps(result,indent=2));raise SystemExit(result['status']!='PASS')
