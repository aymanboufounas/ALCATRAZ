"""Run in Blender with --disable-autoexec; export a copy without changing the blend."""
import json
import os
import sys
from pathlib import Path
for directory in os.environ.get('ALCATRAZ_BLENDER_EXTRA_PYTHON', '').split(os.pathsep):
    if directory:sys.path.insert(0,directory)
import bpy
source=Path(bpy.data.filepath);root=source.parent.parent
textures={p.name.lower():p for p in root.rglob('*') if p.is_file() and p.suffix.lower() in ('.png','.jpg','.jpeg','.tga','.bmp')}
stems={p.stem.lower():p for p in textures.values()}
aliases={'poutre-seule':'poutres-main','poutre-toit-droite':'poutres-main','poutre-toit-gauche':'poutres-main','panda-gun':'pandagun_1280'}
resolved={}
for image in bpy.data.images:
    if image.packed_file:continue
    key=Path(image.filepath.replace('\\','/')).name.lower()
    path=textures.get(key) or textures.get(image.name.lower())
    for candidate in (Path(key).stem,Path(image.name.lower()).stem):
        if path:break
        candidate=candidate.replace('_alphamasked_s','_alphamask');path=stems.get(aliases.get(candidate,candidate))
    if path:
        image.filepath=str(path.resolve());image.source='FILE';image.reload();resolved[image.name]=path.name
converted=[]
if root.name=='Warehouse':
    for material in bpy.data.materials:
        if not material.use_nodes:continue
        nodes=material.node_tree.nodes
        images=[n for n in nodes if n.type=='TEX_IMAGE' and n.image and (n.image.name in resolved or n.image.packed_file or n.image.source=='GENERATED')]
        selected=None;queue=[n for n in nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output];visited=set()
        while queue:
            node=queue.pop(0)
            if node.name in visited:continue
            visited.add(node.name)
            if node in images:selected=node.image;break
            queue.extend(link.from_node for link in material.node_tree.links if link.to_node==node)
        if selected is None and nodes.active in images:selected=nodes.active.image
        if selected is None and images:selected=images[-1].image
        color=tuple(material.diffuse_color)
        for node in nodes:
            if node.type in ('BSDF_DIFFUSE','BSDF_PRINCIPLED'):
                color=tuple(node.inputs['Color' if node.type=='BSDF_DIFFUSE' else 'Base Color'].default_value);break
        nodes.clear();output=nodes.new('ShaderNodeOutputMaterial');shader=nodes.new('ShaderNodeBsdfPrincipled')
        shader.inputs['Base Color'].default_value=color;shader.inputs['Roughness'].default_value=.78
        material.node_tree.links.new(shader.outputs['BSDF'],output.inputs['Surface']);material.use_backface_culling=False
        if selected:
            texture=nodes.new('ShaderNodeTexImage');texture.image=selected;material.node_tree.links.new(texture.outputs['Color'],shader.inputs['Base Color'])
            if 'alphamask' in selected.name.lower() or 'graffiti' in material.name.lower() or material.name=='pandagun_1280':
                material.blend_method='CLIP';material.node_tree.links.new(texture.outputs['Alpha'],shader.inputs['Alpha'])
        converted.append({'material':material.name,'color_texture':selected.name if selected else None})
bpy.ops.export_scene.gltf(filepath=str(source.with_suffix('.glb')),export_format='GLB',export_animations=False,export_cameras=False,export_lights=False,use_visible=True)
source.with_suffix('.conversion.json').write_text(json.dumps({'resolved_images':resolved,'converted_materials':converted,'hidden_templates_excluded':True},indent=2)+'\n')
print('Exported native conversion source:',source.with_suffix('.glb'))
