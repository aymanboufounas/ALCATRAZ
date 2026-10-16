"""Reproducible offline studies of the actual environment changes, never Unity captures.

Run with Tools/requirements-supplied.txt installed. Uses the existing native mesh /
material decoder and EGL renderer. Geometry and atlas pixels come from this checkout;
the GLSL lighting approximates the source shader and does not validate URP execution.
"""
from functools import lru_cache
import json
import math
from pathlib import Path
import re

import moderngl
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial.transform import Rotation
import yaml

import render_current_previews as current
import render_supplied_previews as r

ROOT = r.ROOT
OUT = ROOT / 'Documentation/EnvironmentQualityPreviews'
PROFILE = ROOT / 'Assets/Game/Alcatraz/Resources/Alcatraz/SurfaceDetails/IslandSurface.mat'
DECK_PROFILE = PROFILE.parent / 'HelipadConcrete.mat'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
TEXTURES = {}


def texture(path):
    """Keep original resolution, including the scan's 8K atlas, in this study."""
    if path is None:
        return None
    path = Path(path)
    if path not in TEXTURES:
        with Image.open(path) as source:
            image = source.convert('RGBA')
        uploaded = r.C.texture(image.size, 4, image.tobytes())
        uploaded.build_mipmaps()
        TEXTURES[path] = uploaded
    return TEXTURES[path]


def properties(path):
    text = path.read_text()
    floats = {key: float(value) for key, value in re.findall(r'^    - (_\w+): ([\d.e+-]+)$', text, re.M)}
    textures = {key: r.ASSETS[guid] for key, guid in re.findall(
        r'- (_\w+):\s+m_Texture: \{fileID: \d+, guid: (\w+)', text)}
    return floats, textures


def native_prefab(path):
    text = re.sub(r'^%.*\n', '', path.read_text(), flags=re.M)
    text = re.sub(r'^--- !u!\d+ &(-?\d+)', r'---\nanchor: \1', text, flags=re.M)
    docs = {d['anchor']: d for d in yaml.load_all(text, Loader=yaml.CSafeLoader)}
    transforms = {i: d['Transform'] for i, d in docs.items() if 'Transform' in d}
    go_transform = {d['m_GameObject']['fileID']: i for i, d in transforms.items()}
    objects = {i: d['GameObject'] for i, d in docs.items() if 'GameObject' in d}
    renderers = {d['MeshRenderer']['m_GameObject']['fileID']: d['MeshRenderer']
                 for d in docs.values() if 'MeshRenderer' in d}

    @lru_cache(None)
    def world(i):
        data = transforms[i]
        matrix = np.eye(4)
        matrix[:3, :3] = Rotation.from_quat([data['m_LocalRotation'][k] for k in 'xyzw']).as_matrix()
        matrix[:3, :3] @= np.diag([data['m_LocalScale'][k] for k in 'xyz'])
        matrix[:3, 3] = [data['m_LocalPosition'][k] for k in 'xyz']
        parent = data['m_Father']['fileID']
        return world(parent) @ matrix if parent else matrix

    result = []
    for document in docs.values():
        if 'MeshFilter' not in document:
            continue
        data = document['MeshFilter']
        go = data['m_GameObject']['fileID']
        renderer = renderers.get(go)
        if not renderer or not renderer['m_Enabled'] or not objects[go]['m_IsActive']:
            continue
        if len(renderer['m_Materials']) != 1:
            raise ValueError('Expected one native material per study mesh')
        vertices, indices, normals, uv = current.native_mesh(data['m_Mesh']['guid'])
        material_guid = renderer['m_Materials'][0]['guid']
        color, texture, scale, offset = current.native_material(material_guid)
        uv = uv * scale + offset
        uv[:, 1] = 1 - uv[:, 1]
        model = r.mesh(vertices, indices, uv, normals, texture, color, objects[go]['m_Name'])
        model['material'] = material_guid
        result.append(r.transform(model, world(go_transform[go])))
    return result


VERTEX = '''#version 330
in vec3 position; in vec3 normal; in vec2 texcoord;
uniform mat4 vp; out vec2 uv; out vec3 norm; out vec3 point;
void main(){uv=texcoord;norm=normal;point=position;gl_Position=vp*vec4(position,1);}
'''

FRAGMENT = '''#version 330
in vec2 uv; in vec3 norm; in vec3 point;
uniform sampler2D atlas, groundMap, wallMap, groundNormal, wallNormal, groundSurface, wallSurface;
uniform bool textured, detail, deck; uniform vec4 base; uniform vec3 eye;
uniform float groundScale,wallScale,colorStrength,groundReplacement,normalStrength,occlusionStrength,surfaceVariation;
uniform float groundSmoothness,wallSmoothness,sharpness,slopeStart,slopeEnd,fadeStart,fadeEnd;
uniform bool after; out vec4 color;
vec3 linearColor(vec3 c){return pow(max(c,vec3(0)),vec3(2.2));}
vec2 imageUV(vec2 p){return vec2(p.x,-p.y);}
vec3 normalAt(sampler2D image,vec2 p,float strength){vec3 n=texture(image,imageUV(p)).xyz*2-1;n.xy*=strength;return normalize(n);}
void main(){
 vec4 tex=textured?texture(atlas,uv):vec4(1); if(tex.a*base.a<.4)discard;
 vec3 n=normalize(norm); if(!gl_FrontFacing)n=-n;
 vec3 albedo=linearColor(tex.rgb*base.rgb); vec3 originalAlbedo=albedo; float ao=1,smoothness=.15;
 if(after && (detail || deck)){
  vec3 w=pow(abs(n),vec3(sharpness));w/=max(dot(w,vec3(1)),.0001);
  vec3 s=vec3(n.x<0?-1:1,n.y<0?-1:1,n.z<0?-1:1);
  vec2 px=vec2(-s.x*point.z,point.y)*wallScale;
  vec2 pz=vec2(s.z*point.x,point.y)*wallScale;
  vec2 py=vec2(point.x,-s.y*point.z);
  float g=smoothstep(slopeStart,slopeEnd,n.y);
  float f=1-clamp((distance(eye,point)-fadeStart)/max(.001,fadeEnd-fadeStart),0,1);
  vec3 cx=linearColor(texture(wallMap,imageUV(px)).rgb);
  vec3 cz=linearColor(texture(wallMap,imageUV(pz)).rgb);
  vec3 cy=mix(linearColor(texture(wallMap,imageUV(py*wallScale)).rgb),linearColor(texture(groundMap,imageUV(py*groundScale)).rgb),g);
  vec3 tx=normalAt(wallNormal,px,normalStrength*f),tz=normalAt(wallNormal,pz,normalStrength*f);
  vec3 ty=normalize(mix(normalAt(wallNormal,py*wallScale,normalStrength*f),normalAt(groundNormal,py*groundScale,normalStrength*f),g));
  vec3 nx=normalize(vec3(n.x*tx.z,n.y+tx.y,n.z-s.x*tx.x));
  vec3 ny=normalize(vec3(n.x+ty.x,n.y*ty.z,n.z-s.y*ty.y));
  vec3 nz=normalize(vec3(n.x+s.z*tz.x,n.y+tz.y,n.z*tz.z));
  vec2 sx=texture(wallSurface,imageUV(px)).ga,sz=texture(wallSurface,imageUV(pz)).ga;
  vec2 sy=mix(texture(wallSurface,imageUV(py*wallScale)).ga,texture(groundSurface,imageUV(py*groundScale)).ga,g);
  vec2 surface=sx*w.x+sy*w.y+sz*w.z;
  vec3 sampled=cx*w.x+cy*w.y+cz*w.z;
  if(deck) albedo=sampled*linearColor(base.rgb);
  else {
   albedo*=mix(vec3(1),clamp(sampled*2,vec3(.5),vec3(1.5)),colorStrength*f);
   float luminance=dot(originalAlbedo,vec3(.2126,.7152,.0722));
   vec3 perceptualAtlas=sqrt(max(originalAlbedo,vec3(0)));
   float maximum=max(perceptualAtlas.r,max(perceptualAtlas.g,perceptualAtlas.b));
   float minimum=min(perceptualAtlas.r,min(perceptualAtlas.g,perceptualAtlas.b));
   float chroma=(maximum-minimum)/max(maximum,.001);
   float groundMask=smoothstep(.85,.95,n.y)*smoothstep(.28,.60,luminance)*(1-smoothstep(.20,.45,chroma));
   vec3 macroTint=clamp(originalAlbedo/max(luminance,.1),vec3(.75),vec3(1.25));
   albedo=mix(albedo,cy*macroTint,groundMask*groundReplacement*f);
  }
  ao=mix(1,surface.x,occlusionStrength*f);
  smoothness=deck ? groundSmoothness*surface.y : clamp(mix(wallSmoothness,groundSmoothness,g)*mix(1,.5+surface.y,surfaceVariation*f),0,1);
  n=normalize(nx*w.x+ny*w.y+nz*w.z);
 }
 // Identical simple illumination on both sides isolates surface changes. This
 // is deliberately not a substitute for URP shadows, indirect light or exposure.
 vec3 l=normalize(vec3(.398,.530,-.748));
 vec3 sun=linearColor(vec3(1,.91,.77));
 float diffuse=max(dot(n,l),0);
 vec3 ambient=mix(linearColor(vec3(.43,.39,.30)),linearColor(vec3(.68,.81,.96)),n.y*.5+.5);
 vec3 rgb=albedo*(ambient*.55*ao+sun*diffuse*1.7);
 vec3 h=normalize(l+normalize(eye-point));
 rgb+=sun*.04*pow(max(dot(n,h),0),mix(12,180,smoothness))*diffuse;
 rgb=clamp((rgb*(2.51*rgb+.03))/(rgb*(2.43*rgb+.59)+.14),0,1);
 color=vec4(pow(rgb,vec3(1./2.2)),1);
}
'''


class StudyRenderer:
    def __init__(self):
        self.program = r.C.program(vertex_shader=VERTEX, fragment_shader=FRAGMENT)
        self.buffers = {}
        self.values, self.maps = properties(PROFILE)
        self.deck_values, deck_maps = properties(DECK_PROFILE)
        self.deck_maps = {'_GroundMap': deck_maps['_BaseMap'], '_WallMap': deck_maps['_BaseMap'],
                          '_GroundNormal': deck_maps['_BumpMap'], '_WallNormal': deck_maps['_BumpMap'],
                          '_GroundSurface': deck_maps['_MetallicGlossMap'], '_WallSurface': deck_maps['_OcclusionMap']}
        self.pairs = {'groundScale': '_GroundWorldScale', 'wallScale': '_WallWorldScale',
                 'colorStrength': '_DetailColorStrength', 'groundReplacement': '_GroundAlbedoReplacement',
                 'normalStrength': '_DetailNormalStrength',
                 'occlusionStrength': '_DetailOcclusionStrength', 'surfaceVariation': '_SurfaceVariation',
                 'groundSmoothness': '_GroundSmoothness', 'wallSmoothness': '_WallSmoothness',
                 'sharpness': '_TriplanarSharpness', 'slopeStart': '_GroundSlopeStart',
                 'slopeEnd': '_GroundSlopeEnd', 'fadeStart': '_DetailFadeStart', 'fadeEnd': '_DetailFadeEnd'}
        for name, source in self.pairs.items():
            self.program[name].value = self.values[source]
        self.bindings = [('groundMap', '_GroundMap'), ('wallMap', '_WallMap'),
                         ('groundNormal', '_GroundNormal'), ('wallNormal', '_WallNormal'),
                         ('groundSurface', '_GroundSurface'), ('wallSurface', '_WallSurface')]
        for unit, (name, _) in enumerate(self.bindings, 1):
            self.program[name].value = unit
        self.program['atlas'].value = 0

    def render(self, scene, eye, center, after, size=(1440, 900), fov=58):
        w, h = size
        q, near, far = 1 / math.tan(math.radians(fov) / 2), .08, 3000
        projection = np.zeros((4, 4))
        projection[0, 0], projection[1, 1] = q * h / w, q
        projection[2, 2], projection[2, 3] = (far + near) / (near - far), 2 * far * near / (near - far)
        projection[3, 2] = -1
        self.program['vp'].write((projection @ r.view(eye, center)).astype('f4').T.tobytes())
        self.program['eye'].value = tuple(eye)
        self.program['after'].value = after
        framebuffer = r.C.simple_framebuffer(size, components=4)
        framebuffer.use()
        framebuffer.clear(.60, .70, .70, 1)
        r.C.enable(moderngl.DEPTH_TEST)
        for model in scene:
            key = id(model)
            if key not in self.buffers:
                packed = np.c_[model['v'], model['n'], model['uv']].astype('f4')
                self.buffers[key] = (model, r.C.vertex_array(self.program,
                    [(r.C.buffer(packed.tobytes()), '3f 3f 2f', 'position', 'normal', 'texcoord')],
                    r.C.buffer(model['t'].astype('u4').tobytes())))
            atlas = texture(model['texture'])
            if atlas:
                atlas.use(0)
            self.program['textured'].value = atlas is not None
            self.program['detail'].value = model.get('detail', False)
            self.program['deck'].value = model.get('deck', False)
            self.program['base'].value = tuple(model['color'])
            maps = self.deck_maps if model.get('deck') else self.maps
            for unit, (_, source) in enumerate(self.bindings, 1):
                texture(maps[source]).use(unit)
            for name, source in self.pairs.items():
                value = self.values[source]
                if model.get('deck'):
                    if name in ('groundScale', 'wallScale'): value = .5  # Runtime Tiled() repeats per metre.
                    elif name == 'normalStrength': value = self.deck_values['_BumpScale']
                    elif name in ('groundSmoothness', 'wallSmoothness'): value = self.deck_values['_Smoothness']
                    elif name == 'occlusionStrength': value = self.deck_values['_OcclusionStrength']
                self.program[name].value = value
            self.buffers[key][1].render()
        image = Image.frombytes('RGBA', size, framebuffer.read(components=4)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        framebuffer.release()
        return image


def label_pair(before, after, title, filename, subtitle):
    w, h = before.size
    canvas = Image.new('RGB', (w * 2, h + 150), '#101b21')
    canvas.paste(before, (0, 58))
    canvas.paste(after, (w, 58))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(FONT, 24)
    small = ImageFont.truetype(FONT, 19)
    draw.text((24, 16), 'BEFORE / ORIGINAL SURFACES', font=font, fill='#efe4ce')
    draw.text((w + 24, 16), 'AFTER / CURRENT SOURCE MATERIALS', font=font, fill='#efe4ce')
    draw.text((24, h + 70), title + ' / ' + subtitle, font=font, fill='#efe4ce')
    draw.text((24, h + 108), 'OFFLINE MATERIAL STUDY — NOT UNITY / SHADOWS, GI AND PERFORMANCE UNVERIFIED', font=small, fill='#bacad0')
    draw.line((w, 0, w, h + 58), fill='#e0b861', width=3)
    OUT.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT / filename)
    print('Saved', OUT / filename, flush=True)


def helipad_paint(center):
    result = []
    for side in range(4):
        matrix = current.translated(center, side * 90)
        rectangle = r.mesh([[-5.3, 0, 5.3], [5.3, 0, 5.3], [5.3, 0, 5.08], [-5.3, 0, 5.08]],
                           [[0, 1, 2], [0, 2, 3]], normal=[[0, 1, 0]] * 4,
                           color=(.88, .77, .39, 1), name='Helipad perimeter paint')
        result.append(r.transform(rectangle, matrix))
    for x0, z0, x1, z1 in [(-1.5, -2, -.95, 2), (.95, -2, 1.5, 2), (-.95, -.3, .95, .3)]:
        vertices = np.array([[x0, 0, z0], [x0, 0, z1], [x1, 0, z1], [x1, 0, z0]]) + center
        result.append(r.mesh(vertices, [[0, 1, 2], [0, 2, 3]], normal=[[0, 1, 0]] * 4,
                             color=(.88, .77, .39, 1), name='Helipad H paint'))
    return result


def helipad_landing(scan, full_footprint):
    """Same world rays as the runtime footprint check, batched over nearby triangles."""
    triangles = np.concatenate([m['v'][m['t']] for m in scan]).astype('f8')
    inside = ((triangles[:, :, 0].max(1) >= -157) & (triangles[:, :, 0].min(1) <= -145)
              & (triangles[:, :, 2].max(1) >= -11) & (triangles[:, :, 2].min(1) <= 1))
    triangles = triangles[inside]
    a, b, c = triangles[:, 0], triangles[:, 1], triangles[:, 2]
    bx, bz, cx, cz = b[:, 0] - a[:, 0], b[:, 2] - a[:, 2], c[:, 0] - a[:, 0], c[:, 2] - a[:, 2]
    determinant = bx * cz - bz * cx
    valid_area = abs(determinant) > 1e-10
    determinant = np.where(valid_area, determinant, 1)
    offsets = np.arange(-6, 6.01, .5) if full_footprint else np.array([-5, 0, 5])
    highest = -np.inf
    for x in -151 + offsets:
        for z in -5 + offsets:
            u = ((x - a[:, 0]) * cz - (z - a[:, 2]) * cx) / determinant
            v = (bx * (z - a[:, 2]) - bz * (x - a[:, 0])) / determinant
            valid = valid_area & (u >= -1e-7) & (v >= -1e-7) & (u + v <= 1 + 1e-7)
            if valid.any():
                heights = a[:, 1] + u * (b[:, 1] - a[:, 1]) + v * (c[:, 1] - a[:, 1])
                highest = max(highest, heights[valid].max())
    if not np.isfinite(highest):
        raise ValueError('Helipad footprint does not intersect the actual scan')
    return np.array([-151, highest + (.12 if full_footprint else .08), -5])


def main():
    scan = native_prefab(r.RES / 'Baked/Island.prefab')
    if len(scan) != 11:
        raise ValueError(f'Expected 11 native island chunks, got {len(scan)}')
    source = (ROOT / 'Assets/Game/Supplied/Scripts/SuppliedIslandWorld.cs').read_text()
    constants = dict(re.findall(r'(MapRoot[XYZ])\s*=\s*([\d.+-]+)f?', source))
    offset = [float(constants[name]) for name in ('MapRootX', 'MapRootY', 'MapRootZ')]
    scan = [r.transform(m, current.translated(offset)) for m in scan]
    for model in scan:
        model['detail'] = True
    print('Decoded actual native island chunks:', len(scan), flush=True)
    renderer = StudyRenderer()
    landing = helipad_landing(scan, False)
    raised_landing = helipad_landing(scan, True)
    deck = current.cube('Helicopter landing deck', landing - (0, .16, 0), (12, .3, 12))
    raised_deck = current.cube('Helicopter landing deck', raised_landing - (0, .16, 0), (12, .3, 12))
    deck_guid = re.search(r'^guid: (\w+)', DECK_PROFILE.with_suffix('.mat.meta').read_text(), re.M)[1]
    deck_color, _, _, _ = current.native_material(deck_guid)
    after_deck = {**raised_deck, 'deck': True, 'color': deck_color}
    helicopter_source = r.gltf('Helicopter')
    helicopter = current.placed(helicopter_source, 2.8, landing + (0, .02, 0), 110)
    raised_helicopter = current.placed(helicopter_source, 2.8, raised_landing + (0, .02, 0), 110)
    paint = helipad_paint(raised_landing + (0, .002, 0))
    before_scene = scan + [deck] + helicopter
    after_scene = scan + [after_deck] + raised_helicopter + paint
    eye, center = landing + (13, 6.2, 14), landing + (0, 1.1, 0)
    before = renderer.render(before_scene, eye, center, False)
    after = renderer.render(after_scene, eye, center, True)
    label_pair(before, after, 'EXISTING HELIPAD / SAME CAMERA AND DECK DIMENSIONS', 'HelipadBeforeAfter.png', 'Footprint clearance fix + texture detail + paint')
    # Ground close-up keeps the original scan, including its existing geometric limits.
    ground = current.ground(scan, -147, 6)
    eye, center = ground + (0, 2.4, 2.7), ground + (0, .05, 0)
    before = renderer.render(scan, eye, center, False, fov=52)
    after = renderer.render(scan, eye, center, True, fov=52)
    label_pair(before, after, 'EXISTING SCANNED SURFACE / SAME ATLAS AND CAMERA', 'SurfaceBeforeAfter.png',
               'Pale ground resurfacing + world-scale normals / no added geometry')
    (OUT / 'README.md').write_text('''# Offline environment material studies

These images are **offline material studies, not Unity captures**. They show the actual native island chunks, packaged helicopter geometry, original atlas pixels and current surface-profile textures at identical before/after camera positions. Textures retain their original resolution in this study, including the scan's 8K atlas; the existing generic preview helper's 4K texture limit is not used. Pale neutral upward-facing ground selectively blends toward the packaged concrete texture, matching the source shader's mask, distance fade and current replacement strength. The helipad keeps its original dimensions, gains the same perimeter/H paint rectangles authored by the runtime component, and rises to the actual runtime fix's full-footprint clearance level. Before uses the previous nine height probes and .08 m margin; after uses the current 25 by 25 probes at .5 m spacing across the full 12 m deck and .12 m margin. The helicopter moves with the raised landing level, and the camera stays fixed. No new buildings, foliage, terrain detail or character assets were invented for these pictures.

The lighting is a simple GLSL approximation of the current warm key light. Both sides use identical lighting so the material changes remain visible. It does not reproduce URP shadows, sky illumination, baked/global illumination, reflection probes, SSAO, exposure, fog, animation, UI, physics or GPU performance. Native Unity shader compilation and appearance remain unverified. These modest surface changes do not demonstrate the supplied commercial-game reference quality.

- [Helipad before/after](HelipadBeforeAfter.png)
- [Scanned surface before/after](SurfaceBeforeAfter.png)

Reproduce from the repository root with `python Tools/render_environment_quality_preview.py` using `Tools/requirements-supplied.txt`. The tool reads the current `IslandSurface.mat` parameters and actual texture pixels; it does not modify runtime assets.
''')
    print(json.dumps({'scope': 'offline material approximation only', 'nativeIslandChunks': len(scan),
                      'surfaceProfile': str(PROFILE.relative_to(ROOT)), 'profileParameters': renderer.values,
                      'uploadedTextureDimensions': {str(p.relative_to(ROOT)): list(t.size) for p, t in TEXTURES.items()},
                      'helipadOldLandingY': float(landing[1]), 'helipadCurrentLandingY': float(raised_landing[1]),
                      'unityCapture': False, 'shadowsGIandPerformanceVerified': False}, indent=2))


if __name__ == '__main__':
    main()
