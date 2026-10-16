"""Validate the additive world-rebuild assets and their source/native contracts.

The four deterministic author checks run in separate processes, sequentially.
This tool does not import Unity, compile shaders or certify rendered quality.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys

import numpy as np
from PIL import Image

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RESOURCE_ROOT = 'Assets/Game/Alcatraz/Resources'
BASE = RESOURCE_ROOT+'/Alcatraz/'
SETS = ['ArchitectureKit', 'CoastalVegetation', 'CourtyardSurfaces', 'FacadeRebuild']
AUTHORS = ['author_prison_architecture.py', 'author_coastal_vegetation.py',
           'author_courtyard_surfaces.py', 'author_facade_rebuild.py']
SCAN_OFFSET = np.array([-63., 45., 12.])
URP_LIT = '933532a4fcc9baf4fa0491de14d08ed7'
PHYSICS_CLASSES = {54, 64, 65, 135, 136, 143}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def native_documents(text):
    return {int(m[2]): (int(m[1]), m[3]) for m in re.finditer(
        r'^--- !u!(\d+) &(-?\d+)\n(.*?)(?=^--- !u!|\Z)', text, re.M | re.S)}


def decode_mesh(path):
    text = path.read_text()
    count = int(re.search(r'm_VertexCount: (\d+)', text)[1])
    size = int(re.search(r'm_DataSize: (\d+)', text)[1])
    raw = bytes.fromhex(re.search(r'_typelessdata: ([0-9a-f]+)', text)[1])
    if count <= 0 or size != len(raw) or size != count*48:
        raise ValueError('Unexpected static native vertex layout: '+str(path))
    data = np.frombuffer(raw, '<f4').reshape(count, 12).astype(float)
    index_type = '<u4' if 'm_IndexFormat: 1' in text else '<u2'
    indices = np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: ([0-9a-f]+)', text)[1]), index_type)
    if len(indices)%3 or not len(indices) or int(indices.max()) >= count:
        raise ValueError('Invalid native index range: '+str(path))
    return data, indices.reshape(-1, 3)


class Verification:
    def __init__(self, root):
        self.root = root
        self.errors, self.checks, self.meshes = [], 0, {}
        self.guids = {}
        for path in (root/'Assets').rglob('*.meta'):
            match = re.search(r'^guid: (\w+)', path.read_text(), re.M)
            if match:
                self.guids[match[1]] = Path(str(path)[:-5])

    def check(self, value, description):
        self.checks += 1
        if not value:
            self.errors.append(description)

    def mesh(self, relative):
        if relative not in self.meshes:
            self.meshes[relative] = decode_mesh(self.root/relative)
        return self.meshes[relative]

    def source_hashes(self, label, values):
        self.check(bool(values), label+' records source/output provenance.')
        for path, expected in values.items():
            file = self.root/path
            self.check(file.is_file() and digest(file) == expected,
                       label+' recorded file bytes changed: '+path)

    def prefab(self, path):
        text = (self.root/path).read_text()
        docs = native_documents(text)
        self.check(bool(docs), path+' contains native Unity objects.')
        self.check(not any(kind in PHYSICS_CLASSES for kind, _ in docs.values()),
                   path+' introduces no collider or rigid body.')
        for guid in set(re.findall(r'guid: (\w+)', text)):
            self.check(guid in self.guids and self.guids[guid].exists(),
                       path+' dependency resolves: '+guid)
        for file_id in re.findall(r'\{fileID: (-?\d+)\}', text):
            self.check(int(file_id) == 0 or int(file_id) in docs,
                       path+' local native reference resolves: '+file_id)
        return docs

    def material(self, path):
        text = (self.root/path).read_text()
        shader = re.search(r'm_Shader: \{fileID: 4800000, guid: (\w+)', text)
        self.check(bool(shader) and (shader[1] == URP_LIT or shader[1] in self.guids),
                   path+' has a known shader binding.')
        for property_name, guid in re.findall(r'- (_\w+):\s+m_Texture: \{fileID: \d+, guid: (\w+)', text):
            texture = self.guids.get(guid)
            self.check(texture is not None and texture.is_file(), path+' resolves '+property_name)
            if texture is None or not texture.is_file():
                continue
            metadata = Path(str(texture)+'.meta').read_text()
            self.check('enableMipMap: 1' in metadata, str(texture)+' has mipmaps.')
            if property_name == '_BumpMap':
                self.check('textureType: 1' in metadata and 'sRGBTexture: 0' in metadata,
                           str(texture)+' uses a linear normal-map importer.')
            if property_name in ('_MetallicGlossMap', '_OcclusionMap'):
                self.check('sRGBTexture: 0' in metadata, str(texture)+' retains linear packed data.')

    def native_assets(self):
        result = {}
        for name in SETS:
            folder = self.root/(BASE+name)
            meshes, vertices, triangles, prefabs, materials = 0, 0, 0, 0, 0
            for path in folder.rglob('*.asset'):
                relative = str(path.relative_to(self.root))
                data, indices = self.mesh(relative)
                self.check(np.isfinite(data).all(), relative+' native vertex data is finite.')
                self.check(np.allclose(np.linalg.norm(data[:, 3:6], axis=1), 1, atol=3e-5),
                           relative+' native normals have unit length.')
                meshes += 1
                vertices += len(data)
                triangles += len(indices)
            for path in folder.rglob('*.prefab'):
                self.prefab(str(path.relative_to(self.root)))
                prefabs += 1
            for path in folder.rglob('*.mat'):
                self.material(str(path.relative_to(self.root)))
                materials += 1
            result[name] = {'native_meshes': meshes, 'vertices': vertices, 'stored_triangles': triangles,
                            'prefabs': prefabs, 'materials': materials, 'colliders_added': 0}
        return result

    def architecture(self, manifest, native):
        self.source_hashes('Architecture kit', manifest['files_sha256'])
        expected_modules = {'FacadeWindow', 'FacadeBarredWindow', 'FacadeBoardedWindow', 'FacadeBlank',
                            'AccessDoor', 'RoofCornice', 'Drainpipe', 'RoofDeck', 'RoofCoping', 'RoofChimney'}
        self.check(manifest['module_count'] == len(manifest['modules']) == 10
                   and {m['name'] for m in manifest['modules']} == expected_modules,
                   'Architecture kit contains its seven facade modules and three explicit roof modules.')
        self.check(native['stored_triangles'] == manifest['triangles_all_modules'] < 15000,
                   'Architecture native module triangle total respects the 15,000-triangle budget.')
        self.check(native['vertices'] == manifest['vertices_all_modules'],
                   'Architecture native vertex total matches the manifest.')
        self.check(manifest['geometry_policy']['colliders'] == 0,
                   'Architecture policy adds no collision.')
        for module in manifest['modules']:
            self.check((self.root/(RESOURCE_ROOT+'/'+module['resources_path']+'.prefab')).is_file(),
                       'Architecture Resources binding exists: '+module['name'])
            self.check(module['colliders'] == 0, module['name']+' has no new collision.')
        maps = set()
        for material in manifest['materials'].values():
            for path in material['maps'].values():
                maps.add(path)
        for path in maps:
            with Image.open(self.root/path) as image:
                self.check(image.size == (2048, 2048), path+' retains original licensed 2K dimensions.')

    def vegetation(self, manifest, native):
        self.source_hashes('Coastal vegetation', manifest['source_hashes'])
        placements = manifest['placements']
        self.check(len(placements) == 44 and Counter(p['species'] for p in placements)
                   == {'cypress': 8, 'scrub': 36}, 'Vegetation contains 8 trees and 36 supported shrubs.')
        self.check(native['stored_triangles'] == manifest['stored_triangles'] <= 70000,
                   'Vegetation stored native geometry respects its 70,000-triangle budget.')
        self.check(native['vertices'] == manifest['vertices'], 'Vegetation native vertex count matches.')
        self.check(sum(p['lod0_triangles'] for p in placements) == manifest['lod0_triangles'] <= 60000,
                   'Vegetation active LOD0 geometry respects its 60,000-triangle budget.')
        docs = native_documents((self.root/(BASE+'CoastalVegetation/CoastalVegetation.prefab')).read_text())
        renderers = {i for i, (kind, _) in docs.items() if kind == 23}
        groups = [body for kind, body in docs.values() if kind == 205]
        self.check(len(groups) == manifest['chunk_count'] == 25, 'Vegetation has 25 spatial native LOD groups.')
        referenced = []
        for body in groups:
            heights = [float(v) for v in re.findall(r'screenRelativeHeight: ([\d.e+-]+)', body)]
            references = [int(v) for v in re.findall(r'- renderer: \{fileID: (\d+)\}', body)]
            self.check(len(heights) == 2 and heights[0] > heights[1] > 0,
                       'A vegetation chunk has two descending positive LOD thresholds.')
            self.check(bool(references) and all(i in renderers for i in references),
                       'A vegetation LOD group references real MeshRenderers.')
            referenced.extend(references)
        self.check(len(referenced) == len(set(referenced)) == len(renderers)
                   and set(referenced) == renderers, 'Every vegetation renderer belongs to exactly one LOD.')
        atlas_path = 'Assets/Game/Supplied/Resources/AlcatrazSupplied/Island/Island_Texture_00.jpg'
        atlas = np.asarray(Image.open(self.root/atlas_path).convert('RGB'))
        anchors = json.loads((self.root/(BASE+'EnvironmentDressing/Manifest.json')).read_text())['placements']
        for p in placements:
            anchor = anchors[p['anchor_index']]
            self.check(p['position'] == anchor['position'] and p['source_mesh'] == anchor['source_mesh']
                       and p['source_triangle'] == anchor['source_triangle'],
                       'Vegetation placement retains an existing supported ground-cover anchor.')
            data, indices = self.mesh(p['source_mesh'])
            triangle = indices[p['source_triangle']]
            face, uv = data[triangle, :3]+SCAN_OFFSET, data[triangle, 10:12]
            point = np.asarray(p['position'])
            self.check(np.linalg.norm(np.asarray(p['barycentric']) @ face-point) < 1e-7,
                       'Vegetation anchor lies on its original source triangle.')
            contacts = np.asarray(p['root_contacts'])
            basis = (face[1:]-face[0]).T
            pair = np.linalg.lstsq(basis, (contacts-face[0]).T, rcond=None)[0].T
            bary = np.c_[1-pair.sum(1), pair]
            self.check(len(contacts) == 12 and bary.min() >= .015-1e-7
                       and np.max(np.linalg.norm(bary @ face-contacts, axis=1)) < 1e-7,
                       'All twelve vegetation root contacts remain inside the recorded source face.')
            texture_uv = bary @ uv
            x = np.clip(np.rint(texture_uv[:, 0]*(atlas.shape[1]-1)).astype(int), 0, atlas.shape[1]-1)
            y = np.clip(np.rint((1-texture_uv[:, 1])*(atlas.shape[0]-1)).astype(int), 0, atlas.shape[0]-1)
            rgb = atlas[y, x].astype(float)/255
            r, g, b = rgb.T
            green = ((g > r*1.045) & (g > b*1.08) & (g-r > .025) & (g > .15) & (g < .70))
            self.check(green.all(), 'Every vegetation root contact passes the original strict green mask.')
            for other in placements:
                if other is p:
                    continue
                distance = np.linalg.norm((point-np.asarray(other['position']))[[0, 2]])
                self.check(distance+.00001 >= p['crown_radius_metres']+other['crown_radius_metres']+.40,
                           'Vegetation crowns keep their authored spacing.')
        spray = (self.root/(BASE+'CoastalVegetation/Materials/Sprays.mat')).read_text()
        self.check('_ALPHATEST_ON' in spray and '_AlphaClip: 1' in spray
                   and 'TransparentCutout' in spray, 'Dense needle sprays use explicit URP alpha clipping.')
        self.check(manifest['colliders'] == 0, 'Vegetation adds no collision or floor geometry.')

    def courtyard(self, manifest, native):
        self.source_hashes('Courtyard surfaces', manifest['source_hashes'])
        self.check(manifest['colliders'] == 0 and not manifest['source_geometry_or_collision_modified'],
                   'Courtyard skins retain authoritative source collision.')
        self.check(len(manifest['regions']) == 2 and manifest['triangles'] == native['stored_triangles'] < 10000,
                   'Two confirmed courtyard surfaces remain inside a 10,000-triangle budget.')
        self.check(manifest['vertices'] == native['vertices'], 'Courtyard native vertex count matches.')
        self.check(manifest['maximum_quantized_vertex_distance_from_source_metres'] < .01,
                   'Reported quantized court contacts remain within one centimetre.')
        maximum = 0.
        vertices_checked = 0
        for region in manifest['regions']:
            surface, _ = self.mesh(region['surface_mesh'])
            joints, _ = self.mesh(region['joint_mesh']) if region['joint_mesh'] else (np.empty((0, 12)), None)
            records = [r for r in manifest['source_faces'] if r['region'] == region['name']]
            offsets = {'surface': 0, 'joint': 0}
            for record in records:
                original, indices = self.mesh(record['source_mesh'])
                face = original[indices[record['source_triangle']], :3]+SCAN_OFFSET
                normal = np.cross(face[1]-face[0], face[2]-face[0])
                normal /= np.linalg.norm(normal)
                self.check(normal[1] >= .80 and np.allclose(normal, record['source_normal'], atol=1e-8),
                           'A courtyard source face retains its confirmed upward normal.')
                for label, mesh, expected_offset in [('surface', surface, .006), ('joint', joints, .0066)]:
                    count = record[label+'_triangles']*3
                    points = mesh[offsets[label]:offsets[label]+count, :3]
                    offsets[label] += count
                    if not len(points):
                        continue
                    distance = (points-face[0]) @ normal
                    projected = points-distance[:, None]*normal
                    pair = np.linalg.lstsq((face[1:]-face[0]).T, (projected-face[0]).T, rcond=None)[0].T
                    bary = np.c_[1-pair.sum(1), pair]
                    maximum = max(maximum, float(np.abs(distance).max()))
                    self.check(len(points) == count and np.abs(distance).max() < .01
                               and np.allclose(distance, expected_offset, atol=.00003),
                               'Courtyard '+label+' vertices stay within one centimetre of their own source plane.')
                    self.check(bary.min() >= -.0001 and bary.max() <= 1.0001,
                               'Courtyard '+label+' projection stays inside its own source triangle.')
                    x0, x1, z0, z1 = manifest['excluded_helipad_bounds_x0_x1_z0_z1']
                    inside_pad = ((projected[:, 0] > x0+.0001) & (projected[:, 0] < x1-.0001)
                                  & (projected[:, 2] > z0+.0001) & (projected[:, 2] < z1-.0001))
                    self.check(not inside_pad.any(), 'Courtyard '+label+' preserves the helipad footprint and access margin.')
                    vertices_checked += len(points)
            self.check(offsets['surface'] == len(surface) and offsets['joint'] == len(joints),
                       region['name']+' source contacts account for every native skin and joint vertex.')
        self.check(vertices_checked == native['vertices'], 'Every courtyard native vertex was independently source-projected.')
        return {'source_contact_vertices_checked': vertices_checked,
                'maximum_independent_source_plane_distance_metres': maximum,
                'surface_area_m2': manifest['surface_area_m2']}

    def facades(self, manifest, native):
        self.source_hashes('Facade reconstruction', manifest['source_hashes'])
        layout = json.loads((self.root/(BASE+'FacadeRebuild/Layout.json')).read_text())
        declared = {p['id']: p for p in layout['patches']}
        baked = {p['id']: p for p in manifest['patches']}
        self.check(bool(baked) and set(baked) == set(declared)
                   and all(all(baked[key].get(k) == value for k, value in row.items())
                           and set(baked[key])-set(row) <= {'blank_bays'} for key, row in declared.items()),
                   'Facade reconstruction retains every declared layout field and only adds derived blank-bay masks.')
        self.check(manifest.get('cleanup_volumes', []) == layout.get('cleanup_volumes', []),
                   'Elevated visual cleanup uses only its explicitly declared source-clipping volumes.')
        self.check(manifest['native_prefab_colliders'] == 0
                   and manifest['runtime_roof_box_colliders'] == manifest['colliders_added'] == 1,
                   'Rebuild adds exactly one runtime roof BoxCollider while all native prefabs remain collider-free.')
        # The interaction gate is at the upper level. XZ clearance is stricter
        # than height-only clearance and protects the complete approach volume.
        gate = np.array([-113.33, 22.5])
        clearances = {}
        for patch in manifest['patches']:
            center = np.asarray(patch['bottom_center'])[[0, 2]]
            right = np.asarray(patch['right'])[[0, 2]]
            delta = center-gate
            along = np.clip(-np.dot(delta, right), -patch['width']/2, patch['width']/2)
            clearance = float(np.linalg.norm(delta+right*along))
            clearances[patch['id']] = clearance
            self.check(clearance > 5, patch['id']+' keeps five metres clear of the gate approach in XZ.')
            normal = np.asarray(patch['normal'])
            right3 = np.asarray(patch['right'])
            self.check(np.isclose(np.linalg.norm(normal), 1, atol=1e-6)
                       and np.isclose(np.linalg.norm(right3), 1, atol=1e-6)
                       and abs(np.dot(normal, right3)) < 1e-6,
                       patch['id']+' has an orthonormal surveyed facade basis.')
            self.check(np.isclose(np.dot(np.asarray(patch['bottom_center']), normal),
                                 patch['plane_distance'], atol=.0001)
                       and np.isclose(np.dot(np.asarray(patch['bottom_center']), right3),
                                      np.mean(patch['u_bounds']), atol=.0001),
                       patch['id']+' placement agrees with its surveyed U/depth rectangle.')
            front = manifest['front_projected_removed_area_by_patch'][patch['id']]
            total = manifest['removed_area_by_patch'][patch['id']]
            surface = manifest['removed_surface_area_by_patch'][patch['id']]
            self.check(surface+1e-6 >= total >= front-1e-6 >= -1e-6,
                       patch['id']+' records nonnegative front, multilayer projection and actual surface-area totals.')
        self.check(math.isclose(manifest['footprint_area_m2'],
                              sum(p['width']*p['height'] for p in manifest['patches']), abs_tol=1e-6),
                   'Facade footprint counts each surveyed rectangle once.')
        runtime_index = json.loads((self.root/(BASE+'FacadeRebuild/Runtime.json')).read_text())
        runtime = runtime_index['replacements']
        rows = manifest['replacement_scan_chunks']
        self.check(bool(runtime) and runtime == [{'sourceMesh': row['sourceMesh'], 'resource': row['resource']} for row in rows],
                   'Runtime facade index matches every committed visual replacement.')
        prefab = native_documents((self.root/(BASE+'FacadeRebuild/FacadeRebuild.prefab')).read_text())
        renderer_count = sum(kind == 23 for kind, _ in prefab.values())
        self.check(renderer_count == runtime_index['facadeRenderers'] == manifest['facade_renderers'] > 0,
                   'Runtime facade renderer count matches the actual native prefab.')
        visual_triangles = 0
        for row in rows:
            resource_path = RESOURCE_ROOT+'/'+row['resource']+'.asset'
            self.check(resource_path == row['asset'] and (self.root/resource_path).is_file(),
                       'Visual mesh Resources path resolves: '+row['resource'])
            source_data, source_indices = self.mesh(row['source_asset'])
            output_data, output_indices = self.mesh(row['asset'])
            self.check(len(source_indices) == row['source_triangles']
                       and len(output_indices) == row['result_triangles'],
                       row['sourceMesh']+' records accurate original/replacement native triangle counts.')
            prefix = output_data[:len(source_data)]
            self.check(np.array_equal(prefix[:, :6], source_data[:, :6])
                       and np.array_equal(prefix[:, 10:12], source_data[:, 10:12]),
                       row['sourceMesh']+' retains every original position, normal and UV before appended clipped fragments.')
            visual_triangles += len(output_indices)
        self.check(native['stored_triangles']-visual_triangles == manifest['facade_triangles'] < 60000,
                   'Instantiated facade modules stay inside the 60,000-triangle budget.')
        support = self.native_wall_support(manifest)
        aperture = self.aperture_rays(manifest)
        sightlines = self.oblique_sightlines(manifest)
        roof = self.roof_support(manifest, runtime_index)
        fragments = self.outside_fragment_preservation(manifest)
        return {'patches': len(manifest['patches']), 'replaced_projected_area_m2': manifest['replaced_projected_area_m2'],
                'footprint_area_m2': manifest['footprint_area_m2'],
                'visual_replacement_chunks': len(rows), 'facade_triangles': manifest['facade_triangles'],
                'gate_clearance_xz_metres': clearances, 'independent_native_wall_support': support,
                **aperture, 'oblique_sightlines': sightlines, 'roof_support': roof,
                'visual_source_fragment_preservation': fragments}

    def outside_fragment_preservation(self, manifest):
        """Require all untouched original faces and sample clipped outside fragments."""
        volumes = {p['id']: p for p in manifest['patches']+manifest.get('cleanup_volumes', [])}
        references = manifest['clipped_source_references_by_volume']
        self.check(set(references) == set(volumes), 'Every owned facade/cleanup volume records its source triangles.')
        source_folder = self.root/'Assets/Game/Supplied/Resources/AlcatrazSupplied/Baked/Meshes'
        sources = {p.stem: str(p.relative_to(self.root)) for p in source_folder.glob('Island_*.asset')}
        touched = {}
        for volume_id, records in references.items():
            volume = volumes[volume_id]
            for record in records:
                source = sources[record['source_mesh']]
                data, indices = self.mesh(source)
                face_id = record['source_triangle']
                self.check(0 <= face_id < len(indices) and record['removed_surface_area_m2'] > 0,
                           'Clipped source reference identifies a real triangle and positive removed area.')
                face = data[indices[face_id], :3]+SCAN_OFFSET
                n, r = np.asarray(volume['normal']), np.asarray(volume['right'])
                depth, lateral = face @ n, face @ r
                behind = volume.get('depth_behind', manifest['clipping_depth_metres']['behind_plane'])
                ahead = volume.get('depth_ahead', manifest['clipping_depth_metres']['ahead_of_plane'])
                self.check(depth.max() >= volume['plane_distance']-behind-1e-6
                           and depth.min() <= volume['plane_distance']+ahead+1e-6
                           and lateral.max() >= volume['u_bounds'][0]-1e-6
                           and lateral.min() <= volume['u_bounds'][1]+1e-6
                           and face[:, 1].max() >= volume['y_bounds'][0]-1e-6
                           and face[:, 1].min() <= volume['y_bounds'][1]+1e-6,
                           'A clipped source face intersects its declared owned volume bounds.')
                touched.setdefault(source, set()).add(face_id)
        retained, missing, samples = 0, 0, 0
        for row in manifest['replacement_scan_chunks']:
            source = row['source_asset']
            original, original_indices = self.mesh(source)
            result, result_indices = self.mesh(row['asset'])
            result_counts = Counter(map(tuple, result_indices.tolist()))
            unowned = Counter(tuple(tri) for i, tri in enumerate(original_indices.tolist())
                              if i not in touched.get(source, set()))
            self.check(all(result_counts[key] >= count for key, count in unowned.items()),
                       row['sourceMesh']+' retains every original face outside the explicitly owned source references.')
            retained += sum(unowned.values())
            for i, triangle in enumerate(original_indices):
                if tuple(triangle) not in result_counts:
                    missing += 1
                    self.check(i in touched.get(source, set()), 'No original scan face disappears without an owned clipping reference.')
            native_faces = result[result_indices, :3]+SCAN_OFFSET
            bounds_low, bounds_high = native_faces.min(1), native_faces.max(1)
            for face_id in touched.get(source, set()):
                face = original[original_indices[face_id], :3]+SCAN_OFFSET
                for bary in ([1/3, 1/3, 1/3], [.90, .05, .05], [.05, .90, .05], [.05, .05, .90]):
                    point = np.asarray(bary) @ face
                    owned = False
                    for volume in volumes.values():
                        depth, lateral = float(point @ np.asarray(volume['normal'])), float(point @ np.asarray(volume['right']))
                        behind = volume.get('depth_behind', manifest['clipping_depth_metres']['behind_plane'])
                        ahead = volume.get('depth_ahead', manifest['clipping_depth_metres']['ahead_of_plane'])
                        owned |= (volume['plane_distance']-behind-.0001 <= depth <= volume['plane_distance']+ahead+.0001
                                  and volume['u_bounds'][0]-.0001 <= lateral <= volume['u_bounds'][1]+.0001
                                  and volume['y_bounds'][0]-.0001 <= point[1] <= volume['y_bounds'][1]+.0001)
                    if owned:
                        continue
                    candidates = native_faces[np.all((bounds_low <= point+.00005) & (bounds_high >= point-.00005), axis=1)]
                    covered = False
                    if len(candidates):
                        a = candidates[:, 0]
                        e1, e2 = candidates[:, 1]-a, candidates[:, 2]-a
                        diff = point-a
                        d00 = np.einsum('ij,ij->i', e1, e1)
                        d01 = np.einsum('ij,ij->i', e1, e2)
                        d11 = np.einsum('ij,ij->i', e2, e2)
                        d20 = np.einsum('ij,ij->i', diff, e1)
                        d21 = np.einsum('ij,ij->i', diff, e2)
                        denominator = d00*d11-d01*d01
                        valid = denominator > 1e-14
                        denominator = np.where(valid, denominator, 1)
                        u = (d11*d20-d01*d21)/denominator
                        v = (d00*d21-d01*d20)/denominator
                        n = np.cross(e1, e2)
                        n /= np.maximum(np.linalg.norm(n, axis=1)[:, None], 1e-12)
                        covered = bool(np.any(valid & (u >= -.0001) & (v >= -.0001) & (u+v <= 1.0001)
                                              & (np.abs(np.einsum('ij,ij->i', diff, n)) < .00005)))
                    self.check(covered, 'An original source-face sample outside all facade/cleanup prisms remains rendered.')
                    samples += 1
        self.check(missing == manifest['original_source_triangles_clipped'],
                   'Independently counted replaced original faces match the declared clipping total.')
        return {'unmodified_original_faces_retained': retained, 'replaced_original_faces': missing,
                'outside_fragment_samples_checked': samples, 'owned_volumes': len(volumes),
                'scope': 'Exact original triangle indices for unowned faces plus four barycentric samples per clipped face outside the declared volume union; not an exhaustive image proof.'}

    def native_wall_support(self, manifest):
        """Ray-test original wall support in 3-D, independently of the author's rasterizer."""
        all_faces = []
        source_folder = self.root/'Assets/Game/Supplied/Resources/AlcatrazSupplied/Baked/Meshes'
        for path in sorted(source_folder.glob('Island_*.asset')):
            data, indices = self.mesh(str(path.relative_to(self.root)))
            all_faces.append(data[indices, :3]+SCAN_OFFSET)
        faces = np.concatenate(all_faces)
        geometric = np.cross(faces[:, 1]-faces[:, 0], faces[:, 2]-faces[:, 0])
        geometric /= np.maximum(np.linalg.norm(geometric, axis=1)[:, None], 1e-12)
        recorded = {row['patch']: row for row in manifest['native_wall_support']}
        self.check(set(recorded) == {p['id'] for p in manifest['patches']},
                   'Every facade patch records its native source-wall support sample results.')
        reports = []
        for patch in manifest['patches']:
            normal, right = np.asarray(patch['normal']), np.asarray(patch['right'])
            plane, step = patch['plane_distance'], .25
            depth = faces @ normal
            selected = ((np.abs(geometric[:, 1]) < .15) & (geometric @ normal > .94)
                        & (depth.max(1) > plane-1.5) & (depth.min(1) < plane+1.5))
            triangles = faces[selected]
            a = triangles[:, 0]
            edge1, edge2 = triangles[:, 1]-a, triangles[:, 2]-a
            direction = -normal
            p_vector = np.cross(direction, edge2)
            determinant = np.einsum('ij,ij->i', edge1, p_vector)
            inverse = np.zeros_like(determinant)
            np.divide(1, determinant, out=inverse, where=determinant > 1e-10)
            samples = covered = 0
            sampled_y = patch.get('support_y_bounds', patch['y_bounds'])
            for y in np.arange(sampled_y[0]+step/2, sampled_y[1], step):
                for u_position in np.arange(patch['u_bounds'][0]+step/2, patch['u_bounds'][1], step):
                    origin = normal*(plane+1.5)+right*u_position+[0, y, 0]
                    t_vector = origin-a
                    u = np.einsum('ij,ij->i', t_vector, p_vector)*inverse
                    q_vector = np.cross(t_vector, edge1)
                    v = (q_vector @ direction)*inverse
                    distance = np.einsum('ij,ij->i', edge2, q_vector)*inverse
                    hits = ((determinant > 1e-10) & (u >= -1e-8) & (v >= -1e-8)
                            & (u+v <= 1+1e-8) & (distance >= -1e-8) & (distance <= 3+1e-8))
                    covered += int(hits.any())
                    samples += 1
            fraction = covered/max(samples, 1)
            minimum = patch.get('minimum_native_support_fraction', .995)
            self.check(samples > 0 and fraction >= minimum,
                       patch['id']+' independent original-wall support meets its declared minimum fraction.')
            row = recorded[patch['id']]
            self.check(row['sample_count'] == samples and row['covered_samples'] == covered
                       and math.isclose(row['coverage_fraction'], fraction, abs_tol=1e-10)
                       and row['minimum_fraction'] == minimum and row['sample_spacing_metres'] == step
                       and row.get('sampled_y_bounds', sampled_y) == sampled_y,
                       patch['id']+' recorded native support matches independent ray/triangle intersection.')
            reports.append({'patch': patch['id'], 'samples': samples, 'covered_samples': covered,
                            'coverage_fraction': fraction, 'minimum_fraction': minimum,
                            'scope': 'Original front-facing near-vertical wall triangles within +/-1.5 m of the new plane; this measures background support, not exact visual/collider alignment.'})
        return reports

    def window_instances(self, manifest):
        """Resolve actual glass-bearing instances, including variable-width bays."""
        if hasattr(self, '_resolved_windows'):
            return self._resolved_windows
        kit = json.loads((self.root/(BASE+'ArchitectureKit/Manifest.json')).read_text())
        modules = {m['name']: m for m in kit['modules']}
        patches = {p['id']: p for p in manifest['patches']}
        docs = native_documents((self.root/(BASE+'FacadeRebuild/FacadeRebuild.prefab')).read_text())
        mesh_by_game = {}
        for kind, body in docs.values():
            if kind == 33:
                game = re.search(r'm_GameObject: \{fileID: (\d+)\}', body)
                mesh = re.search(r'm_Mesh: \{fileID: \d+, guid: (\w+)', body)
                if game and mesh:
                    mesh_by_game[int(game[1])] = self.guids[mesh[1]]
        native_glass = []
        for kind, body in docs.values():
            if kind != 23:
                continue
            material = re.search(r'm_Materials:\s*\n\s*-\s*\{fileID: \d+, guid: (\w+)', body)
            game = re.search(r'm_GameObject: \{fileID: (\d+)\}', body)
            if material and game and self.guids[material[1]].name == 'RecessedGlass.mat':
                data, _ = self.mesh(str(mesh_by_game[int(game[1])].relative_to(self.root)))
                native_glass.extend(data[:, :3])
        native_glass = np.asarray(native_glass)
        self.check(native_glass.ndim == 2 and native_glass.shape[1] == 3,
                   'Native facade assembly contains rendered recessed-glass geometry.')
        native_keys = {tuple(p) for p in np.round(native_glass, 4)}
        windows, expected_vertices = [], 0
        for index, instance in enumerate(manifest['module_instances']):
            if instance.get('type') != 'window':
                continue
            patch = patches[instance['patch']]
            module = modules[instance['module']]
            glass_part = next(p for p in module['parts'] if p['name'] == 'RecessedGlass')
            data, _ = self.mesh(glass_part['mesh'])
            lower, upper = data[:, :3].min(0), data[:, :3].max(0)
            bounds = instance['glass_bounds_local']
            self.check(np.allclose(bounds['min'], lower, atol=.00001)
                       and np.allclose(bounds['max'], upper, atol=.00001),
                       'A window instance records the real native glass bounds.')
            aperture = instance['aperture_bounds_local']
            self.check(instance['width'] > 2*max(abs(lower[0]), abs(upper[0]))
                       and instance['height'] > upper[1]
                       and aperture['min'][0] < lower[0] < upper[0] < aperture['max'][0]
                       and aperture['min'][1] < lower[1] < upper[1] < aperture['max'][1],
                       'Variable-width wall bays keep the fixed native glass inside their real openings.')
            normal, right = np.asarray(patch['normal']), np.asarray(patch['right'])
            origin = np.asarray(instance['position'])
            expected = data[:, 0, None]*(-right)+data[:, 1, None]*[0, 1, 0]+data[:, 2, None]*(-normal)+origin
            missing = [point for point in expected if tuple(np.round(point, 4)) not in native_keys]
            self.check(not missing or all(np.linalg.norm(native_glass-point, axis=1).min() < .00005 for point in missing),
                       'Every declared window pane exists at its actual world position in the native assembly.')
            self.check(abs(float(origin @ normal)-patch['plane_distance']) < .0001,
                       'Window instance origin matches its own surveyed facade plane.')
            expected_vertices += len(data)
            row = round((origin[1]-patch['bottom_center'][1])/3.5)
            column = round((np.mean(patch['u_bounds'])+patch['width']*.5-float(origin @ right))
                           /instance['width']-.5)
            windows.append({'patch': patch, 'origin': origin, 'lower': lower, 'upper': upper,
                            'row': int(row), 'column': int(column), 'instance_index': index})
        self.check(bool(windows) and expected_vertices == len(native_glass),
                   'Exactly the declared glass-bearing instances account for all native window vertices.')
        self._resolved_windows = windows
        return windows

    def aperture_rays(self, manifest):
        """Independent 3-D ray/triangle checks, not the author's 2-D projected test."""
        windows = self.window_instances(manifest)
        replaced = {row['source_asset']: row['asset'] for row in manifest['replacement_scan_chunks']}
        all_faces = []
        source_folder = self.root/'Assets/Game/Supplied/Resources/AlcatrazSupplied/Baked/Meshes'
        for path in sorted(source_folder.glob('Island_*.asset')):
            source = str(path.relative_to(self.root))
            data, indices = self.mesh(replaced.get(source, source))
            all_faces.append(data[indices, :3]+SCAN_OFFSET)
        faces = np.concatenate(all_faces)
        geometric = np.cross(faces[:, 1]-faces[:, 0], faces[:, 2]-faces[:, 0])
        default_front = manifest['clipping_depth_metres']['ahead_of_plane']
        probes, occluders = 0, 0
        patch_counts = {}
        for patch in manifest['patches']:
            instances = [window for window in windows if window['patch']['id'] == patch['id']]
            if not instances:
                continue
            pane_depth = max(float(window['lower'][2]) for window in instances)
            normal, right = np.asarray(patch['normal']), np.asarray(patch['right'])
            plane = patch['plane_distance']
            front = patch.get('depth_ahead', default_front)
            depth = faces @ normal
            sideways = faces @ right
            selected = ((geometric @ normal > 1e-10)
                        & (depth.max(1) >= plane-pane_depth-1e-6)
                        & (depth.min(1) <= plane+front+1e-6)
                        & (sideways.max(1) >= patch['u_bounds'][0])
                        & (sideways.min(1) <= patch['u_bounds'][1])
                        & (faces[:, :, 1].max(1) >= patch['y_bounds'][0])
                        & (faces[:, :, 1].min(1) <= patch['y_bounds'][1]))
            triangles = faces[selected]
            a = triangles[:, 0]
            edge1, edge2 = triangles[:, 1]-a, triangles[:, 2]-a
            direction = -normal
            p_vector = np.cross(direction, edge2)
            determinant = np.einsum('ij,ij->i', edge1, p_vector)
            inverse = np.zeros_like(determinant)
            np.divide(1, determinant, out=inverse, where=determinant > 1e-10)
            patch_probes = 0
            for window in instances:
                bay, lower, upper = window['origin'], window['lower'], window['upper']
                row, column = window['row'], window['column']
                for x_fraction in (.2, .5, .8):
                    for y_fraction in (.2, .5, .8):
                        x = lower[0]+(upper[0]-lower[0])*x_fraction
                        y = lower[1]+(upper[1]-lower[1])*y_fraction
                        origin = bay-right*x+[0, y, 0]+normal*front
                        t_vector = origin-a
                        u = np.einsum('ij,ij->i', t_vector, p_vector)*inverse
                        q_vector = np.cross(t_vector, edge1)
                        v = (q_vector @ direction)*inverse
                        distance = np.einsum('ij,ij->i', edge2, q_vector)*inverse
                        hits = ((determinant > 1e-10) & (u >= -1e-7) & (v >= -1e-7)
                                & (u+v <= 1+1e-7) & (distance >= -1e-6)
                                & (distance <= front+pane_depth+1e-6))
                        hit_count = int(hits.sum())
                        self.check(hit_count == 0, patch['id']+f' bay {row},{column} actual pane ray remains free of old scan wedges.')
                        occluders += hit_count
                        probes += 1
                        patch_probes += 1
            patch_counts[patch['id']] = patch_probes
        self.check(probes > 0, 'Facade aperture verification fired independent rays through real pane bounds.')
        return {'independent_native_aperture_rays': probes, 'old_scan_aperture_occluders': occluders,
                'aperture_rays_by_patch': patch_counts,
                'aperture_ray_scope': 'Front-facing scan triangles between the actual glass pane and each patch\'s declared ahead clipping depth; native structures beyond that local volume remain authoritative.'}

    def oblique_sightlines(self, manifest):
        """Report retained foreground separately from aperture failures, up to 4 m."""
        windows = self.window_instances(manifest)
        replacements = {row['source_asset']: row['asset'] for row in manifest['replacement_scan_chunks']}
        all_faces, labels = [], []
        source_folder = self.root/'Assets/Game/Supplied/Resources/AlcatrazSupplied/Baked/Meshes'
        for path in sorted(source_folder.glob('Island_*.asset')):
            source = str(path.relative_to(self.root))
            data, indices = self.mesh(replacements.get(source, source))
            all_faces.append(data[indices, :3]+SCAN_OFFSET)
            labels.extend((path.stem, i) for i in range(len(indices)))
        faces = np.concatenate(all_faces)
        edge1, edge2 = faces[:, 1]-faces[:, 0], faces[:, 2]-faces[:, 0]
        normals = np.cross(edge1, edge2)
        normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-10)
        low, high = faces.min(1), faces.max(1)
        rays = local_count = foreground_count = 0
        blocked_rays, by_patch = [], {}
        for patch in manifest['patches']:
            instances = [window for window in windows if window['patch']['id'] == patch['id']]
            if not instances:
                continue
            normal, right = np.asarray(patch['normal']), np.asarray(patch['right'])
            plane = patch['plane_distance']
            ahead = patch.get('depth_ahead', manifest['clipping_depth_metres']['ahead_of_plane'])
            behind = patch.get('depth_behind', manifest['clipping_depth_metres']['behind_plane'])
            by_row = {}
            for row in sorted({window['row'] for window in instances}):
                counts = {'rays': 0, 'locally_occluded': 0, 'foreground_occluded': 0}
                for window in (w for w in instances if w['row'] == row):
                    bay, column = window['origin'], window['column']
                    pane_depth = float(window['lower'][2])
                    for x in (-.4, .2, .4):
                        for y in (1.3, 1.97, 2.6):
                            pane = bay-right*x+[0, y, 0]-normal*pane_depth
                            for slope in (0, .35, .7):
                                direction = normal+[0, slope, 0]
                                direction /= np.linalg.norm(direction)
                                end = pane+4*direction
                                ray_low, ray_high = np.minimum(pane, end)-1e-5, np.maximum(pane, end)+1e-5
                                selected = np.flatnonzero(np.all((low <= ray_high) & (high >= ray_low), axis=1)
                                                          & (normals @ direction > 1e-7))
                                hits = []
                                if len(selected):
                                    e1, e2 = edge1[selected], edge2[selected]
                                    p_vector = np.cross(direction, e2)
                                    determinant = np.einsum('ij,ij->i', e1, p_vector)
                                    valid = np.abs(determinant) > 1e-9
                                    selected, e1, e2, p_vector, determinant = (
                                        values[valid] for values in (selected, e1, e2, p_vector, determinant))
                                    t_vector = pane-faces[selected, 0]
                                    u = np.einsum('ij,ij->i', t_vector, p_vector)/determinant
                                    q_vector = np.cross(t_vector, e1)
                                    v = (q_vector @ direction)/determinant
                                    distance = np.einsum('ij,ij->i', e2, q_vector)/determinant
                                    hit = ((u >= -1e-6) & (v >= -1e-6) & (u+v <= 1+1e-6)
                                           & (distance >= 1e-5) & (distance <= 4))
                                    for index, length in zip(selected[hit], distance[hit]):
                                        point = pane+direction*length
                                        depth, lateral = float(point @ normal), float(point @ right)
                                        inside = (patch['u_bounds'][0]-1e-5 <= lateral <= patch['u_bounds'][1]+1e-5
                                                  and patch['y_bounds'][0]-1e-5 <= point[1] <= patch['y_bounds'][1]+1e-5
                                                  and plane-behind-1e-5 <= depth <= plane+ahead+1e-5)
                                        hits.append({'source_mesh': labels[index][0],
                                                     'native_triangle': int(labels[index][1]),
                                                     'distance_metres': float(length), 'point': point.tolist(),
                                                     'inside_rebuild_prism': bool(inside),
                                                     'near_horizontal_surface': bool(abs(normals[index, 1]) >= .8)})
                                local = any(h['inside_rebuild_prism'] for h in hits)
                                foreground = any(not h['inside_rebuild_prism'] for h in hits)
                                self.check(not local, patch['id']+f' bay {row},{column} at elevation slope {slope} has no old scan occluder inside its prism.')
                                rays += 1
                                local_count += int(local)
                                foreground_count += int(foreground)
                                counts['rays'] += 1
                                counts['locally_occluded'] += int(local)
                                counts['foreground_occluded'] += int(foreground)
                                if hits:
                                    blocked_rays.append({'patch': patch['id'], 'row': row, 'column': column,
                                                         'local_xy': [x, y], 'camera_elevation_slope': slope,
                                                         'ray_start_world': pane.tolist(),
                                                         'scan_hits_within_4m': sorted(hits, key=lambda h: h['distance_metres'])})
                by_row[str(row)] = counts
            by_patch[patch['id']] = by_row
        self.check(rays > 0, 'Oblique 4 m visibility review sampled the actual surveyed window bays.')
        return {'rays': rays, 'elevation_slopes': [0, .35, .7], 'range_metres': 4,
                'local_prism_occluded': local_count, 'foreground_occluded_within_4m': foreground_count,
                'by_patch_and_row': by_patch, 'blocked_rays': blocked_rays,
                'scope': 'Native scan geometry only: retained surfaces outside the declared reconstruction prisms are reported, not deleted or treated as local aperture failures.',
                'limitation': 'Preserved foreground terrain can still obscure upper windows from some views. These rays do not prove full facade visibility or reproduce Unity rendering.'}

    def roof_support(self, manifest, runtime_index):
        """Measure the native slab/membrane and the one intentional new solid."""
        roof, support = manifest['roof'], runtime_index['roofSupport']
        def vector(value):
            result = np.asarray([value[k] for k in 'xyz'] if isinstance(value, dict) else value, dtype=float)
            if result.shape != (3,) or not np.isfinite(result).all():
                raise ValueError('Roof support vectors must contain three finite coordinates')
            return result
        center, size, forward = (vector(support[key]) for key in ('center', 'size', 'forward'))
        up = np.array([0., 1., 0.])
        self.check(np.all(size > 0) and 1 < size[0] < 50 and 1 < size[2] < 50
                   and .05 < size[1] < 1 and 5 < center[1] < 120,
                   'Roof support is a finite, positive and bounded physical box.')
        self.check(abs(forward[1]) < .000001 and np.isclose(np.linalg.norm(forward), 1, atol=1e-6),
                   'Roof support forward is a horizontal unit direction.')
        right = np.cross(up, forward)
        basis = np.column_stack([right, up, forward])
        self.check(np.allclose(basis.T @ basis, np.eye(3), atol=1e-6)
                   and np.isclose(np.linalg.det(basis), 1, atol=1e-6),
                   'Roof support has orthonormal right/up/forward axes without mirroring.')
        self.check(roof['original_floor_changed'] is False and roof['new_roof_solid'] is True,
                   'The new roof solid is explicit and original native floors are retained.')
        self.check(np.allclose(vector(roof['center_world'])[[0, 2]], center[[0, 2]], atol=.00005)
                   and np.isclose(roof['width'], size[0], atol=.00005)
                   and np.isclose(roof['depth'], size[2], atol=.00005),
                   'Native roof placement and runtime box footprint share measured dimensions.')
        if 'support' in roof:
            self.check(all(np.allclose(vector(roof['support'][key]), vector(support[key]), atol=.000001)
                           for key in ('center', 'size', 'forward')),
                       'Manifest roof support agrees with the runtime Vector3 metadata.')
        self.check(np.allclose(vector(roof['forward']), forward, atol=1e-6)
                   and np.allclose(vector(roof['right']), right, atol=1e-6),
                   'Authored roof geometry uses the same yaw axes as the runtime box.')
        top = center[1]+size[1]*.5
        self.check(np.isclose(top, roof['finished_height'], atol=.00005),
                   'Runtime roof collider top matches the finished native membrane plane.')

        def faces(paths):
            values = []
            self.check(bool(paths) and len(paths) == len(set(paths)), 'Roof part paths are nonempty and unique.')
            for path in paths:
                data, indices = self.mesh(path)
                values.append(data[indices, :3])
            return np.concatenate(values)
        core = faces(roof['solid_meshes'])
        membrane_parts = faces(roof['membrane_meshes'])
        core_local = (core-center) @ basis
        low, high = core_local.min(axis=(0, 1)), core_local.max(axis=(0, 1))
        self.check(np.allclose(low[[0, 2]], -size[[0, 2]]*.5, atol=.00005)
                   and np.allclose(high[[0, 2]], size[[0, 2]]*.5, atol=.00005),
                   'Closed native roof core footprint matches the support box, including yaw.')
        self.check(np.isclose(low[1], -size[1]*.5, atol=.00005)
                   and -.00005 <= size[1]*.5-high[1] <= .01,
                   'Roof box bottom matches the slab and its top is within one centimetre of the closed core.')
        geometric = np.cross(core[:, 1]-core[:, 0], core[:, 2]-core[:, 0])
        self.check(np.all(np.linalg.norm(geometric, axis=1) > 1e-10),
                   'Structural roof solid contains no degenerate triangles.')
        # Weld native positions, independently of UV/normal splits, then require
        # two opposite directed uses of every physical boundary edge.
        _, welded = np.unique(np.round(core.reshape(-1, 3), 5), axis=0, return_inverse=True)
        triangles = welded.reshape(-1, 3)
        edges = Counter()
        directed = Counter()
        for triangle in triangles:
            for a, b in zip(triangle, np.roll(triangle, -1)):
                a, b = int(a), int(b)
                edges[tuple(sorted((a, b)))] += 1
                directed[(a, b)] += 1
        closed = bool(edges) and all(count == 2 for count in edges.values())
        winding = all(directed[(a, b)] == directed[(b, a)] for a, b in edges)
        self.check(closed and winding, 'Structural roof mesh is a closed consistently wound volume, not an unsupported plane.')
        centered = core-center
        signed_volume = float(np.einsum('ij,ij->i', centered[:, 0],
                                       np.cross(centered[:, 1], centered[:, 2])).sum()/6)
        box_volume = float(np.prod(size))
        self.check(.94*box_volume < signed_volume <= box_volume*1.001,
                   'Measured native roof volume fills the support box within the designed bevel/membrane tolerance.')

        membrane_normal = np.cross(membrane_parts[:, 1]-membrane_parts[:, 0],
                                   membrane_parts[:, 2]-membrane_parts[:, 0])
        on_plane = ((membrane_normal[:, 1] > 1e-10)
                    & (np.abs(membrane_parts[:, :, 1]-top).max(1) < .00005))
        membrane = membrane_parts[on_plane]
        self.check(len(membrane) >= 2, 'Roof has a real upward membrane surface at the collider top.')
        if not len(membrane):
            raise ValueError('No native roof membrane triangles at the runtime support top')
        membrane_local = (membrane-center) @ basis
        membrane_low = membrane_local.min(axis=(0, 1))
        membrane_high = membrane_local.max(axis=(0, 1))
        self.check(np.all(membrane_low[[0, 2]] >= -size[[0, 2]]*.5-.00005)
                   and np.all(membrane_high[[0, 2]] <= size[[0, 2]]*.5+.00005)
                   and np.all(membrane_high[[0, 2]]-membrane_low[[0, 2]] >= size[[0, 2]]-.05),
                   'Rendered membrane footprint lies on the support box with only the authored edge inset.')
        membrane_area = float(np.linalg.norm(np.cross(membrane[:, 1]-membrane[:, 0],
                                                     membrane[:, 2]-membrane[:, 0]), axis=1).sum()*.5)
        self.check(.98*size[0]*size[2] <= membrane_area <= size[0]*size[2]*1.001,
                   'The finished roof surface closes essentially the full rectangular footprint.')

        source_faces = []
        source_folder = self.root/'Assets/Game/Supplied/Resources/AlcatrazSupplied/Baked/Meshes'
        for path in sorted(source_folder.glob('Island_*.asset')):
            data, indices = self.mesh(str(path.relative_to(self.root)))
            source_faces.append(data[indices, :3]+SCAN_OFFSET)
        original = np.concatenate(source_faces)
        def highest_upward(mesh_faces, x, z):
            a = mesh_faces[:, 0]
            e1, e2 = mesh_faces[:, 1]-a, mesh_faces[:, 2]-a
            determinant = e1[:, 0]*e2[:, 2]-e1[:, 2]*e2[:, 0]
            valid = determinant < -1e-10  # negative XZ determinant is +Y winding
            denominator = np.where(valid, determinant, 1)
            u = ((x-a[:, 0])*e2[:, 2]-(z-a[:, 2])*e2[:, 0])/denominator
            v = (e1[:, 0]*(z-a[:, 2])-e1[:, 2]*(x-a[:, 0]))/denominator
            valid &= (u >= -1e-7) & (v >= -1e-7) & (u+v <= 1+1e-7)
            if not valid.any():
                return None
            return float((a[:, 1]+u*e1[:, 1]+v*e2[:, 1])[valid].max())
        samples = roof['floor_void_samples']
        self.check(bool(samples), 'Roof records known original floor-void samples for independent verification.')
        reports = []
        for sample in samples:
            position = sample.get('position', sample.get('world_position', sample.get('world_xz', sample.get('xz'))))
            if position is None:
                raise ValueError('Roof void samples require world position or world_xz coordinates')
            position = np.asarray(position, dtype=float)
            x, z = (position[0], position[2]) if len(position) == 3 else position
            local = (np.array([x, top, z])-center) @ basis
            source_height = highest_upward(original, x, z)
            roof_height = highest_upward(membrane, x, z)
            self.check(np.all(np.abs(local[[0, 2]]) < size[[0, 2]]*.5)
                       and roof_height is not None and abs(roof_height-top) < .00005,
                       'The rendered roof and support collider both cover a known source floor void.')
            self.check(source_height is not None and source_height < top-.01,
                       'The original scan floor is independently below the new roof at a known void sample.')
            expected = sample.get('source_height', sample.get('source_floor_y', sample.get('highest_source_y')))
            if expected is not None:
                self.check(source_height is not None and abs(source_height-expected) < .0001,
                           'Recorded original-floor height agrees with the untouched native source triangles.')
            reports.append({'world_xz': [float(x), float(z)], 'original_highest_upward_y': source_height,
                            'native_membrane_y': roof_height, 'runtime_box_top_y': float(top),
                            'original_floor_below_roof_metres': None if source_height is None else float(top-source_height)})
        self.check(any(np.linalg.norm(np.asarray(r['world_xz'])-center[[0, 2]]) < .05 for r in reports),
                   'Known floor-void checks include the actual roof center, not only supported edges.')
        return {'runtime_box_colliders_added': 1, 'native_prefab_colliders_added': 0,
                'center': center.tolist(), 'size': size.tolist(), 'forward': forward.tolist(),
                'finished_top_y': float(top), 'native_closed_core_volume_m3': signed_volume,
                'runtime_box_volume_m3': box_volume, 'core_closed_edge_count': len(edges),
                'core_to_finished_top_gap_metres': float(size[1]*.5-high[1]),
                'membrane_area_m2': membrane_area, 'original_floor_void_samples': reports,
                'scope': 'Native roof geometry and static runtime support metadata; no Unity physics or character landing test.'}

    def runtime(self, manifests):
        source = (self.root/'Assets/Game/Alcatraz/Scripts/AlcatrazEnvironmentDetails.cs').read_text()
        for name in ('CoastalVegetation', 'CourtyardSurfaces', 'FacadeRebuild'):
            resource = manifests[name]['resource']
            self.check('"'+resource+'"' in source and (self.root/(RESOURCE_ROOT+'/'+resource+'.prefab')).is_file(),
                       name+' runtime resource binding matches its committed prefab.')
        self.check('"Alcatraz/FacadeRebuild/Runtime"' in source,
                   'Runtime service loads the committed facade replacement index.')
        swap = source.index('item.Key.sharedMesh = item.Value')
        self.check('collider.sharedMesh != target.sharedMesh' in source
                   and source.index('var facade = AddWorldPrefab') < swap,
                   'Facade runtime resolves original collider bindings and facade resources before visual swaps.')
        self.check('index.replacements.Length == 0' in source and 'index.facadeRenderers <= 0' in source
                   and source.index('!UsableWorldPrefab(prefab, index.facadeRenderers)') < swap
                   and 'pending.ContainsKey(target)' in source and 'visual.vertexCount == 0' in source,
                   'Facade runtime preflights nonempty indices, renderer counts, prefab usability, unique targets and nonempty meshes.')
        self.check('prefab.GetComponentsInChildren<Collider>(true).Length != 0' in source
                   and 'filter.sharedMesh.vertexCount == 0' in source
                   and '!material.shader.isSupported' in source,
                   'World prefab preflight rejects added collision and missing/unsupported render dependencies.')
        self.check(source.count('AddComponent<BoxCollider>()') == 1
                   and re.findall(r'AddComponent<(\w*Collider)>\(', source) == ['BoxCollider'],
                   'The environment service creates exactly one new collider type: the owned roof box.')
        self.check('Finite(roof.center) && Finite(roof.size) && Finite(roof.forward)' in source
                   and source.index('!UsableRoof(index.roofSupport)') < source.index('var facade = AddWorldPrefab'),
                   'Finite bounded roof metadata is preflighted before facade instantiation and mesh replacement.')
        allocation = source.index('RoofCollider = roof.AddComponent<BoxCollider>()')
        disabled = source.index('RoofCollider.enabled = false;', allocation)
        enabled = source.index('RoofCollider.enabled = true;', disabled)
        synced = source.index('Physics.SyncTransforms()', enabled)
        self.check(source.index('var facade = AddWorldPrefab') < allocation < disabled < swap < enabled < synced,
                   'The owned roof box stays disabled until the complete visual mesh set is swapped, then physics is synchronized.')
        self.check('Quaternion.LookRotation(index.roofSupport.forward, Vector3.up)' in source
                   and 'RoofCollider.size = index.roofSupport.size' in source
                   and 'SetPositionAndRotation(index.roofSupport.center' in source,
                   'Runtime roof position, size and horizontal orientation come directly from the measured support metadata.')
        teardown = source[source.index('void OnDestroy()'):]
        self.check('RoofCollider.enabled = false' in teardown,
                   'Teardown disables the owned new roof solid before discarding the additive world.')
        self.check(not re.search(r'collider\.sharedMesh\s*=(?!=)', source),
                   'Facade runtime does not assign new collision meshes.')
        self.check('foreach (var item in originalMeshes)' in source
                   and 'OriginalScanMesh(MeshFilter filter)' in source,
                   'Runtime retains access to original scan meshes and restores visual references on teardown.')
        self.check('instance.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity)' in source
                   and 'instance.transform.localScale = Vector3.one' in source,
                   'World-space additive prefab transforms are explicitly set to identity.')


def validate(root, run_author_checks=True):
    verifier = Verification(root)
    regeneration = []
    if run_author_checks:
        for name in AUTHORS:
            try:
                completed = subprocess.run([sys.executable, str(root/'Tools'/name), '--check'],
                    cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
                verifier.check(completed.returncode == 0, name+' deterministic --check passes.')
                regeneration.append({'script': 'Tools/'+name, 'exit_code': completed.returncode,
                                     'output': completed.stdout[-6000:]})
            except (OSError, subprocess.TimeoutExpired) as error:
                verifier.check(False, name+' deterministic --check could not complete: '+str(error))
                regeneration.append({'script': 'Tools/'+name, 'error': str(error)})
    manifests = {name: json.loads((root/(BASE+name+'/Manifest.json')).read_text()) for name in SETS}
    native, summary = {}, {}
    for name, task in [('native_assets', lambda: verifier.native_assets())]:
        try:
            native = task()
        except (ValueError, KeyError, OSError, AssertionError) as error:
            verifier.check(False, name+': '+str(error))
    for label, task in [
            ('architecture', lambda: verifier.architecture(manifests['ArchitectureKit'], native['ArchitectureKit'])),
            ('vegetation', lambda: verifier.vegetation(manifests['CoastalVegetation'], native['CoastalVegetation'])),
            ('courtyard', lambda: verifier.courtyard(manifests['CourtyardSurfaces'], native['CourtyardSurfaces'])),
            ('facades', lambda: verifier.facades(manifests['FacadeRebuild'], native['FacadeRebuild'])),
            ('runtime', lambda: verifier.runtime(manifests))]:
        try:
            value = task()
            if value is not None:
                summary[label] = value
        except (ValueError, KeyError, OSError, AssertionError) as error:
            verifier.check(False, label+': '+str(error))
    return {'status': 'FAIL' if verifier.errors else ('PASS' if run_author_checks else 'NATIVE_ONLY'),
            'checks': verifier.checks, 'errors': verifier.errors,
            'scope': 'Sequential deterministic author checks, native buffers/materials, source provenance and retained fragments, court contacts, actual window-instance rays, closed roof volume/membrane and its one declared runtime support box.',
            'regeneration': regeneration, 'native_assets': native, **summary,
            'vegetation': {'trees': manifests['CoastalVegetation']['trees'],
                           'shrubs': manifests['CoastalVegetation']['shrubs'],
                           'placements': len(manifests['CoastalVegetation']['placements']),
                           'lod_groups': manifests['CoastalVegetation']['chunk_count'],
                           'lod0_triangles': manifests['CoastalVegetation']['lod0_triangles'],
                           'stored_triangles': manifests['CoastalVegetation']['stored_triangles']},
            'unity_import_verified': False, 'unity_api_compilation_verified': False,
            'unity_shader_compilation_verified': False, 'unity_rendered_quality_verified': False,
            'unity_gameplay_verified': False, 'gpu_performance_verified': False,
            'limitations': ['The rebuilt floor/facade areas and confirmed green patches cover part of the supplied island, not the entire map.',
                            'Source color and elevation masks are conservative placement heuristics, not proof that every surface is natural ground.',
                            'Preserved native terrain outside facade reconstruction prisms can obscure upper windows; the 4 m oblique sightline report records that remaining visibility gap.',
                            'The new roof BoxCollider is checked as a source/geometry contract; Unity physics, landing and teardown still need Play Mode verification.',
                            'Native source checks do not execute Unity, test alpha overdraw, certify collision/camera behavior or establish reference-game visual parity.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        result = validate(root)
    except (ValueError, KeyError, OSError, AssertionError) as error:
        result = {'status': 'FAIL', 'checks': 0, 'errors': [str(error)], 'scope': __doc__}
    target = root/'Validation/WorldRebuildSource.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(result, indent=2)+'\n')
    temporary.replace(target)
    print(json.dumps(result, indent=2))
    raise SystemExit(result['status'] != 'PASS')


if __name__ == '__main__':
    main()
