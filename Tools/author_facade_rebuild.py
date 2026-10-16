"""Rebuild surveyed scan facades with native modular geometry; retain original collision.

--check regenerates into memory and compares committed files without writing.
Layout.json contains inspected supported rectangles, rather than guessed world walls.
"""
import argparse,hashlib,json,re
from pathlib import Path
from collections import defaultdict
import numpy as np
import unity_writer as u
from geometry import Mesh

ROOT=Path(__file__).resolve().parents[1]
BASE='Assets/Game/Alcatraz/Resources/Alcatraz/FacadeRebuild'
KIT='Assets/Game/Alcatraz/Resources/Alcatraz/ArchitectureKit'
SCAN='Assets/Game/Supplied/Resources/AlcatrazSupplied/Baked/Meshes'
OFFSET=np.array([-63.,45.,12.])
DEPTH_BEHIND=.45
DEPTH_AHEAD=.8
PRESERVE_FLOOR_NORMAL_Y=.8

def depth_limits(patch):
    return float(patch.get('depth_behind',DEPTH_BEHIND)),float(patch.get('depth_ahead',DEPTH_AHEAD))

def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()

def read_mesh(path):
    text=(ROOT/path).read_text();count=int(re.search(r'm_VertexCount: (\d+)',text)[1])
    data=np.frombuffer(bytes.fromhex(re.search(r'_typelessdata: (\w+)',text)[1]),'<f4').reshape(count,12)
    triangles=np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: (\w+)',text)[1]),'<u4' if 'm_IndexFormat: 1' in text else '<u2').reshape(-1,3)
    mesh=Mesh();mesh.v=data[:,:3].astype(float).tolist();mesh.n=data[:,3:6].astype(float).tolist();mesh.uv=data[:,10:12].astype(float).tolist();mesh.t=triangles.flatten().tolist()
    return mesh

def clip(poly,axis,bound,sign):
    if not poly:return []
    result=[]
    for i,a in enumerate(poly):
        b=poly[(i+1)%len(poly)];da=np.dot(a[:3],axis)-bound;db=np.dot(b[:3],axis)-bound
        inside_a=sign*da>=-1e-9;inside_b=sign*db>=-1e-9
        if inside_a:result.append(a)
        if inside_a!=inside_b:result.append(a+(b-a)*(da/(da-db)))
    return result

def subtract_prism(poly,patch):
    """Remove only the intersection with the surveyed six-plane facade volume.

    Scan window ledges are often oblique or span a larger depth than the wall.
    Partitioning at every plane keeps their outside fragments instead of either
    retaining an occluding wedge or deleting the whole original triangle.
    XYZ, source normals and source UVs share the same edge interpolation.
    """
    right=np.array(patch['right']);normal=np.array(patch['normal']);remaining=poly;outside=[]
    behind,ahead=depth_limits(patch)
    for axis,bound,sign in [(right,patch['u_bounds'][0],1),(right,patch['u_bounds'][1],-1),
                            (np.array([0.,1.,0.]),patch['y_bounds'][0],1),(np.array([0.,1.,0.]),patch['y_bounds'][1],-1),
                            (normal,patch['plane_distance']-behind,1),
                            (normal,patch['plane_distance']+ahead,-1)]:
        piece=clip(remaining,axis,bound,-sign)
        if len(piece)>=3:outside.append(piece)
        remaining=clip(remaining,axis,bound,sign)
        if len(remaining)<3:break
    area=front_projected=surface_area=0.
    if len(remaining)>=3:
        for i in range(1,len(remaining)-1):
            cross=np.cross(remaining[i][:3]-remaining[0][:3],remaining[i+1][:3]-remaining[0][:3])*.5
            projected=float(np.dot(cross,normal))
            area+=abs(projected);front_projected+=max(0.,projected);surface_area+=float(np.linalg.norm(cross))
    return outside,area,front_projected,surface_area

def check_native_support(source_meshes,patches):
    """Sample original near-vertical wall support, including the buried base."""
    faces=np.concatenate([(np.asarray(mesh.v)+OFFSET)[np.asarray(mesh.t).reshape(-1,3)]for mesh in source_meshes])
    normals=np.cross(faces[:,1]-faces[:,0],faces[:,2]-faces[:,0]);normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-10)
    reports=[];step=.25
    for patch in patches:
        normal=np.array(patch['normal']);right=np.array(patch['right']);plane=patch['plane_distance']
        us=np.arange(patch['u_bounds'][0]+step/2,patch['u_bounds'][1],step)
        ys=np.arange(patch['y_bounds'][0]+step/2,patch['y_bounds'][1],step)
        yy,uu=np.meshgrid(ys,us,indexing='ij');points=np.dstack([uu,yy]);covered=np.zeros(uu.shape,bool)
        depth=faces@normal;use=(abs(normals[:,1])<.15)&(normals@normal>.94)&(depth.max(1)>plane-1.5)&(depth.min(1)<plane+1.5)
        selected=faces[use];depth=depth[use];projected=np.stack([selected@right,selected[:,:,1]],axis=-1)
        for triangle,distances in zip(projected,depth):
            a,b,c=triangle;matrix=np.stack([b-a,c-a],axis=1)
            if abs(np.linalg.det(matrix))<1e-10:continue
            bc=(points-a)@np.linalg.inv(matrix).T;bary=np.dstack([1-bc.sum(-1),bc]);distance=bary@distances
            covered|=(bary.min(-1)>=-1e-8)&(distance>=plane-1.5)&(distance<=plane+1.5)
        fraction=float(covered.mean());minimum=float(patch.get('minimum_native_support_fraction',.995))
        assert fraction>=minimum,('Insufficient original wall support',patch['id'],fraction,minimum)
        reports.append({'patch':patch['id'],'sample_spacing_metres':step,'sample_count':int(covered.size),
                        'covered_samples':int(covered.sum()),'coverage_fraction':fraction,'minimum_fraction':minimum,
                        'method':'Original front-facing wall triangles: absolute geometric normalY < .15, dot(normal, facadeNormal) > .94, depth within +/-1.5m of new plane; rectangle-centred .25m lattice.'})
    return reports

def check_window_apertures(visual_meshes,patches,pane_front_z):
    """Check old scan geometry cannot cover the actual recessed glass samples."""
    faces=[]
    for mesh in visual_meshes:
        vertices=np.asarray(mesh.v)+OFFSET
        faces.append(vertices[np.asarray(mesh.t).reshape(-1,3)])
    faces=np.concatenate(faces)
    geometric=np.cross(faces[:,1]-faces[:,0],faces[:,2]-faces[:,0])
    checks=[]
    for patch in patches:
        if patch['role']=='retaining':continue
        normal=np.array(patch['normal']);right=np.array(patch['right']);plane=patch['plane_distance'];behind,ahead=depth_limits(patch)
        depth=faces@normal
        # This is a ray through the local reconstruction volume. Other island
        # buildings outside that volume are not assumed to be transparent.
        use=((geometric@normal)>1e-10)&(depth.max(1)>=plane-pane_front_z-1e-6)&(depth.min(1)<=plane+ahead+1e-6)
        selected=faces[use];depth=depth[use]
        projected=np.stack([selected@right,selected[:,:,1]],axis=-1)
        low,high=projected.min(1),projected.max(1)
        rows=round(patch['height']/3.5);columns=round(patch['width']/3)
        for row in range(rows):
            for column in range(columns):
                origin=np.array(patch['bottom_center'])-right*((column-(columns-1)/2)*3)+np.array([0,row*3.5,0])
                for x,y in [(.18,1.4),(-.18,2.4),(.4,1.4),(-.4,2.4)]:
                    point=origin-right*x+np.array([0,y,0]);q=np.array([point@right,point[1]])
                    candidates=np.flatnonzero(np.all((low<=q+1e-7)&(high>=q-1e-7),axis=1));hits=[]
                    for index in candidates:
                        triangle=projected[index];a,b,c=triangle;matrix=np.stack([b-a,c-a],axis=1)
                        if abs(np.linalg.det(matrix))<1e-10:continue
                        bc=np.linalg.solve(matrix,q-a);bary=np.r_[1-bc.sum(),bc]
                        if bary.min()<-1e-7:continue
                        distance=float(bary@depth[index])
                        if plane-pane_front_z-1e-6<=distance<=plane+ahead+1e-6:hits.append(distance)
                    assert not hits,('Original scan covers recessed glass',patch['id'],row,column,x,y,hits)
                    checks.append({'patch':patch['id'],'row':row,'column':column,'local_xy':[x,y],
                                   'world_position':point.tolist(),'scan_occluders':0})
    return checks

def author():
    layout=json.loads((ROOT/BASE/'Layout.json').read_text());patches=layout['patches']
    kit=json.loads((ROOT/KIT/'Manifest.json').read_text());modules={m['name']:m for m in kit['modules']}
    outputs={};old_write,old_art=u.write,u.ART
    def capture(path,text):outputs[str(path)]=text.encode();return ROOT/path
    u.write=capture;u.ART=BASE;u.Node.all=[];u.Node.counter=81000000
    inputs={BASE+'/Layout.json':sha(BASE+'/Layout.json'),KIT+'/Manifest.json':sha(KIT+'/Manifest.json'),
      'Tools/author_facade_rebuild.py':sha('Tools/author_facade_rebuild.py'),'Tools/unity_writer.py':sha('Tools/unity_writer.py')}
    replacements=[];removed_by_patch={p['id']:0. for p in patches};clipped_faces=0
    front_by_patch={p['id']:0. for p in patches};surface_by_patch={p['id']:0. for p in patches};visual_meshes=[];source_meshes=[]
    try:
        for path in sorted((ROOT/SCAN).glob('Island_*.asset')):
            relative=str(path.relative_to(ROOT));source=read_mesh(relative);v=np.array(source.v);n=np.array(source.n);uv=np.array(source.uv);tris=np.array(source.t).reshape(-1,3)
            source_meshes.append(source)
            world=v+OFFSET;attrs=np.c_[world,n,uv];faces=world[tris];centers=faces.mean(1)
            geometric=np.cross(faces[:,1]-faces[:,0],faces[:,2]-faces[:,0]);geometric/=np.maximum(np.linalg.norm(geometric,axis=1)[:,None],1e-10)
            candidates={}
            for patch in patches:
                normal=np.array(patch['normal']);right=np.array(patch['right']);depth=faces@normal;ranges=faces@right;behind,ahead=depth_limits(patch)
                mask=(depth.max(1)>patch['plane_distance']-behind)&(depth.min(1)<patch['plane_distance']+ahead)
                # The retaining wall crosses the walkable courtyard elevation;
                # keep its floor. Elevated window patches replace old horizontal
                # ledges too, so those cannot poke through the new window recess.
                if patch['role']=='retaining':mask&=abs(geometric[:,1])<PRESERVE_FLOOR_NORMAL_Y
                mask&=(ranges.max(1)>patch['u_bounds'][0])&(ranges.min(1)<patch['u_bounds'][1])&(faces[:,:,1].max(1)>patch['y_bounds'][0])&(faces[:,:,1].min(1)<patch['y_bounds'][1])
                for index in np.flatnonzero(mask):
                    effective=patch
                    if patch['role']!='retaining' and abs(geometric[index,1])>=PRESERVE_FLOOR_NORMAL_Y:
                        # Preserve the ground-contact floor even when a large
                        # source triangle also crosses a higher window ledge.
                        effective=dict(patch,y_bounds=[max(patch['y_bounds'][0],patch['bottom_center'][1]+.9),patch['y_bounds'][1]])
                        if faces[index,:,1].max()<=effective['y_bounds'][0]:continue
                    candidates.setdefault(int(index),[]).append(effective)
            if not candidates:visual_meshes.append(source);continue
            rebuilt=Mesh();rebuilt.v=list(source.v);rebuilt.n=list(source.n);rebuilt.uv=list(source.uv);rebuilt.t=[];changed=0
            for index,triangle in enumerate(tris):
                if index not in candidates:rebuilt.t.extend(triangle.tolist());continue
                polygons=[[row.copy() for row in attrs[triangle]]];removed=0.
                for patch in candidates[index]:
                    kept=[]
                    for polygon in polygons:
                        outside,area,front,surface=subtract_prism(polygon,patch);kept.extend(outside);removed+=surface;removed_by_patch[patch['id']]+=area
                        front_by_patch[patch['id']]+=front;surface_by_patch[patch['id']]+=surface
                    polygons=kept
                if removed<1e-8:rebuilt.t.extend(triangle.tolist());continue
                changed+=1
                for polygon in polygons:
                    for j in range(1,len(polygon)-1):
                        selected=[polygon[0],polygon[j],polygon[j+1]]
                        if np.linalg.norm(np.cross(selected[1][:3]-selected[0][:3],selected[2][:3]-selected[0][:3]))<1e-9:continue
                        normals=[(row[3:6]/max(np.linalg.norm(row[3:6]),1e-10)).tolist() for row in selected]
                        rebuilt.tri(*(row[:3]-OFFSET for row in selected),uvs=[row[6:8].tolist() for row in selected],normals=normals)
            if not changed:visual_meshes.append(source);continue
            visual_meshes.append(rebuilt)
            name='Visual_'+path.stem;output=u.save_mesh(name,rebuilt,folder='Meshes')
            inputs[relative]=sha(relative);clipped_faces+=changed
            replacements.append({'sourceMesh':path.stem,'resource':'Alcatraz/FacadeRebuild/Meshes/'+name,
              'asset':output,'source_asset':relative,'source_triangles':len(tris),'result_triangles':len(rebuilt.t)//3,
              'clipped_source_faces':changed,'bounds_min':np.min(rebuilt.v,axis=0).tolist(),'bounds_max':np.max(rebuilt.v,axis=0).tolist()})
        groups=defaultdict(Mesh);instances=[];module_cache={}
        def add(name,position,matrix,group):
            module=modules[name]
            for part in module['parts']:
                key=part['mesh']
                if key not in module_cache:module_cache[key]=read_mesh(key);inputs[key]=sha(key)
                material=part['material']
                if name=='FacadeBarredWindow' and part['name']=='BrickWall':
                    material=next(row['material']for row in modules['FacadeWindow']['parts']if row['name']=='ConcreteWall')
                mesh=module_cache[key];out=groups[(group,material)];start=len(out.v)
                out.v.extend((np.array(mesh.v)@matrix.T+position).tolist());out.n.extend((np.array(mesh.n)@matrix.T).tolist());out.uv.extend(mesh.uv);out.t.extend((np.array(mesh.t)+start).tolist())
            instances.append({'module':name,'position':[float(x) for x in position],'group':group})
        for patch in patches:
            normal=np.array(patch['normal']);right=-np.array(patch['right']);matrix=np.column_stack([right,[0,1,0],-normal])
            assert abs(np.linalg.det(matrix)-1)<1e-6
            columns=round(patch['width']/3);rows=round(patch['height']/3.5);bottom=np.array(patch['bottom_center'])
            for row in range(rows):
                for column in range(columns):
                    position=bottom+right*((column-(columns-1)/2)*3)+np.array([0,row*3.5,0])
                    module='FacadeBlank' if patch['role']=='retaining' else 'FacadeBarredWindow' if row==0 else 'FacadeWindow'
                    add(module,position,matrix,patch['group'])
                    if row==rows-1:add('RoofCornice',position+[0,3.5,0],matrix,patch['group'])
            if patch['role']!='retaining':
                add('Drainpipe',bottom+right*(patch['width']/2-.2),matrix,patch['group'])
        root=u.Node('Surveyed prison facade reconstruction',static=False);triangles=0
        for index,((group,material),mesh) in enumerate(sorted(groups.items())):
            name='Facade_'+group+'_'+str(index);u.save_mesh(name,mesh,folder='Meshes');key='FacadeMaterial_'+str(index);u.MATERIALS[key]=material
            u.Node(name,root,static=False).render(name,key);triangles+=len(mesh.t)//3;inputs[material]=sha(material)
        prefab=BASE+'/FacadeRebuild.prefab';u.write(prefab,u.HEAD+''.join(u.node_yaml(node,node is root) for node in u.Node.all));u.meta(prefab,'PrefabImporter')
        for directory in [BASE,BASE+'/Meshes']:
            u.write(directory+'.meta','fileFormatVersion: 2\nguid: '+u.guid(directory)+'\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n')
        for patch in patches:
            expected=patch['width']*patch['height'];actual=front_by_patch[patch['id']]
            # Layered scan triangles and window ledges can project onto the same
            # pixel. Count them honestly, rather than mistaking their summed area
            # for the rebuilt footprint or requiring exactly one old wall layer.
            if patch['role']=='retaining':assert actual>=expected*.995,(patch['id'],actual,expected)
        native_support=check_native_support(source_meshes,patches)
        glass_part=next(part for part in modules['FacadeWindow']['parts']if part['name']=='RecessedGlass')
        pane_front_z=float(np.min(np.asarray(module_cache[glass_part['mesh']].v)[:,2]))
        aperture_checks=check_window_apertures(visual_meshes,patches,pane_front_z)
        runtime={'facadeRenderers':len(groups),'replacements':[{'sourceMesh':row['sourceMesh'],'resource':row['resource']} for row in replacements]}
        u.write(BASE+'/Runtime.json',json.dumps(runtime,indent=2)+'\n');u.meta(BASE+'/Runtime.json','TextScriptImporter')
        manifest={'schema':1,'baseline':'ff62e7661a05070616f8f8ab35d8377ef4348d76','resource':'Alcatraz/FacadeRebuild/FacadeRebuild',
         'source_hashes':inputs,'patches':patches,'footprint_area_m2':sum(p['width']*p['height']for p in patches),
         'replaced_projected_area_m2':sum(removed_by_patch.values()),'removed_area_by_patch':removed_by_patch,
         'front_projected_removed_area_by_patch':front_by_patch,'removed_surface_area_by_patch':surface_by_patch,
         'clipping_depth_metres':{'behind_plane':DEPTH_BEHIND,'ahead_of_plane':DEPTH_AHEAD},
         'retaining_preserved_floor_absolute_normal_y_minimum':PRESERVE_FLOOR_NORMAL_Y,
         'area_note':'Footprint counts each surveyed rectangle once. Removed projected/surface areas count all old scan layers, ledges and both windings, so they can exceed the footprint.',
         'window_aperture_checks':aperture_checks,
         'native_wall_support':native_support,
         'wall_material_policy':'All storeys use the same coastal concrete, including the barred ground-floor module; the source kit remains unchanged.',
         'original_source_triangles_clipped':clipped_faces,'replacement_scan_chunks':replacements,'module_instances':instances,
         'facade_renderers':len(groups),'facade_triangles':triangles,'colliders_added':0,
         'geometry_policy':'Only visual fragments inside surveyed R/Y/depth prisms are replaced, including oblique window ledges. At retaining walls near-horizontal courtyard floors (absolute normalY >= .8) are preserved. All fragments outside the six planes are retained. Original scan asset bytes and MeshColliders remain unchanged; source UVs and normals outside the prisms are interpolated without remapping.',
         'limits':['Reconstruction covers inspected facade patches, not the whole island.','Opaque recessed window panes remain sealed by original wall collision. No new enterable room is implied.','Unity rendering, collision/camera interaction and performance remain unverified.']}
        u.write(BASE+'/Manifest.json',json.dumps(manifest,indent=2)+'\n');u.meta(BASE+'/Manifest.json','TextScriptImporter')
        for path,text in list(outputs.items()):outputs[path]=('\n'.join(line.rstrip() for line in text.decode().splitlines())+'\n').encode()
        return outputs,manifest
    finally:u.write,u.ART=old_write,old_art

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();outputs,manifest=author()
    # This directory is owned by this generator except its inspected layout.
    # Remove obsolete visual chunks/modules after changing the selected facade
    # layout so unused old native assets do not remain in Resources or builds.
    expected=set(outputs)
    def owned(path):
        relative=path.relative_to(ROOT/BASE).as_posix()
        if relative in {'Manifest.json','Manifest.json.meta','Runtime.json','Runtime.json.meta',
                        'FacadeRebuild.prefab','FacadeRebuild.prefab.meta','Meshes.meta'}:return True
        return bool(re.fullmatch(r'Meshes/(?:Facade_[A-Za-z0-9_]+|Visual_Island_[0-9]+_[0-9]+)\.asset(?:\.meta)?',relative))
    obsolete=[path for path in (ROOT/BASE).rglob('*')if path.is_file()and owned(path)and str(path.relative_to(ROOT))not in expected]
    if args.check:assert not obsolete,'Obsolete generated facade files: '+', '.join(str(path)for path in obsolete)
    else:
        for path in obsolete:path.unlink()
    for path,data in outputs.items():
        file=ROOT/path
        if args.check:assert file.read_bytes()==data,'Regeneration differs: '+path
        else:file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(data)
    print(json.dumps({'status':'PASS','mode':'check' if args.check else 'author','patches':len(manifest['patches']),
      'replaced_area_m2':manifest['replaced_projected_area_m2'],'visual_chunks':len(manifest['replacement_scan_chunks']),
      'facade_triangles':manifest['facade_triangles'],'facade_renderers':manifest['facade_renderers'],'colliders_added':0,'output_files':len(outputs)},indent=2))

if __name__=='__main__':main()
