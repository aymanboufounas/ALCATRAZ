"""Render actual rebuilt native assets with fixed offline lighting, never Unity.

Uses the packaged 8K island atlas unchanged. Before represents ff62e76's surface
profiles and corrected helipad; after substitutes the authored visual scan meshes
and adds the current courtyard, facade and LOD0 vegetation assets. Directional
shadows are calculated from those meshes; this is not a URP/shader/physics test.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re

import moderngl
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import render_current_previews as current
import render_environment_quality_preview as study
import render_supplied_previews as r

ROOT = r.ROOT
ART = ROOT / "Assets/Game/Alcatraz/Resources/Alcatraz"
OUT = ROOT / "Documentation/WorldRebuildPreviews"
KEY = np.asarray([-.48, .72, -.50], dtype=float)
KEY /= np.linalg.norm(KEY)
INPUTS = set()


def guid(path):
    return re.search(r"^guid: (\w+)", Path(str(path) + ".meta").read_text(), re.M).group(1)


def prefab(path, lod0=False):
    """Existing decoder, with explicit mesh identity and conservative LOD filter."""
    INPUTS.add(path)
    source = path.read_text()
    models = study.native_prefab(path)
    meshes = [re.search(r"m_Mesh: \{fileID: 4300000, guid: (\w+)", doc).group(1)
              for doc in source.split("--- !u!") if doc.startswith("33 ")]
    if len(meshes) != len(models):
        raise ValueError("Prefab decoder order/count changed: " + str(path))
    result = []
    for model, mesh_guid in zip(models, meshes):
        mesh_path = r.ASSETS[mesh_guid]
        INPUTS.update([mesh_path, r.ASSETS[model["material"]]])
        model["source_mesh"] = mesh_path.stem
        if lod0 and "_LOD1_" in mesh_path.stem:
            continue
        result.append(model)
    return result


def models_for_scene():
    island_prefab = r.RES / "Baked/Island.prefab"
    raw = prefab(island_prefab)
    # Replacement resources are authored in the native scan's local frame. Do
    # not silently use this shortcut if the packaged hierarchy later changes.
    island_text = island_prefab.read_text()
    for field, expected in [("m_LocalPosition", [0, 0, 0]),
                            ("m_LocalRotation", [0, 0, 0, 1]),
                            ("m_LocalScale", [1, 1, 1])]:
        for serialized in re.findall(field + r": \{([^}]+)\}", island_text):
            values = [float(value.split(":")[1]) for value in serialized.split(",")]
            if not np.allclose(values, expected, atol=1e-8):
                raise ValueError("Island hierarchy is no longer identity: " + field)
    source = (ROOT / "Assets/Game/Supplied/Scripts/SuppliedIslandWorld.cs").read_text()
    constants = dict(re.findall(r"(MapRoot[XYZ])\s*=\s*([\d.+-]+)f?", source))
    offset = [float(constants[name]) for name in ("MapRootX", "MapRootY", "MapRootZ")]
    visual = ART / "FacadeRebuild/Runtime.json"
    INPUTS.add(visual)
    # ART is .../Resources/Alcatraz; resolve every resource path against Resources.
    replacements = {item["sourceMesh"]: ART.parent / (item["resource"] + ".asset")
                    for item in json.loads(visual.read_text())["replacements"]}
    before, after = [], []
    replaced = []
    for original in raw:
        old = {**original, "detail": True}
        new = old
        if original["source_mesh"] in replacements:
            replacement = replacements[original["source_mesh"]]
            INPUTS.add(replacement)
            v, t, n, uv = current.native_mesh(guid(replacement))
            # The native Island children are identity, proved by source prefab;
            # runtime replacements share exactly the source mesh local frame.
            uv = uv.copy()
            uv[:, 1] = 1 - uv[:, 1]
            new = {**old, "v": v, "t": t, "n": n, "uv": uv}
            replaced.append(original["source_mesh"])
        before.append(r.transform(old, current.translated(offset)))
        after.append(r.transform(new, current.translated(offset)))
    if set(replaced) != set(replacements):
        raise ValueError("Not every runtime visual replacement was rendered")
    groundcover = prefab(ART / "EnvironmentDressing/SuppliedGroundCover.prefab")
    landing = study.helipad_landing(before, True)
    deck = current.cube("Current raised helipad", landing - (0, .16, 0), (12, .3, 12))
    deck_guid = guid(study.DECK_PROFILE)
    deck_color, _, _, _ = current.native_material(deck_guid)
    deck = {**deck, "deck": True, "color": deck_color}
    paint = study.helipad_paint(landing + (0, .002, 0))
    # Helicopter native baked prefab preserves source geometry/materials. The
    # existing size/ground helper duplicates the runtime placement math.
    heli_path = r.RES / "Baked/Helicopter.prefab"
    helicopter = current.placed(prefab(heli_path), 2.8, landing + (0, .02, 0), 110)
    common = groundcover + [deck] + paint + helicopter
    facades = prefab(ART / "FacadeRebuild/FacadeRebuild.prefab")
    courtyard = prefab(ART / "CourtyardSurfaces/CourtyardSurfaces.prefab")
    vegetation = prefab(ART / "CoastalVegetation/CoastalVegetation.prefab", lod0=True)
    return before + common, after + common + facades + courtyard + vegetation, {
        "visual_replacements": replaced, "scan_world_offset": offset,
        "current_helipad_landing": landing.tolist(),
        "new_facade_draws": len(facades), "new_courtyard_draws": len(courtyard),
        "new_vegetation_lod0_draws": len(vegetation), "before_draws": len(before + common),
        "after_draws": len(after + common + facades + courtyard + vegetation)}


PBR_DECLARATIONS = """
uniform bool pbr, hasNormal, hasSurface, hasAO;
uniform sampler2D nativeNormal, nativeSurface, nativeAO;
uniform float nativeBump, nativeSmoothness, nativeMetallic, nativeOcclusion, nativeCutoff;
uniform mat4 shadowVP;
uniform sampler2DShadow shadowMap;
vec3 mappedNormal(vec3 n){
 vec3 q1=dFdx(point),q2=dFdy(point);vec2 st1=dFdx(uv),st2=dFdy(uv);
 float determinant=st1.x*st2.y-st1.y*st2.x;
 if(abs(determinant)<.00000001)return n;
 vec3 tangent=(q1*st2.y-q2*st1.y)/determinant;
 tangent=normalize(tangent-n*dot(n,tangent));
 vec3 rawBitangent=(q2*st1.x-q1*st2.x)/determinant;
 vec3 bitangent=normalize(cross(n,tangent))*sign(dot(cross(n,tangent),rawBitangent));
 vec3 sampleNormal=texture(nativeNormal,uv).xyz*2-1;
 // Decoder converts Unity V to PIL/OpenGL image V; retain Unity's normal Y.
 sampleNormal.xy*=nativeBump;sampleNormal.y=-sampleNormal.y;
 return normalize(mat3(tangent,bitangent,n)*sampleNormal);
}
float visibility(vec3 n){
 vec4 projected=shadowVP*vec4(point,1);vec3 coord=projected.xyz/projected.w*.5+.5;
 if(any(lessThan(coord,vec3(0)))||any(greaterThan(coord,vec3(1))))return 1.;
 float bias=max(.00014,.00065*(1-max(dot(n,normalize(vec3(-.48,.72,-.50))),0)));
 float value=0;vec2 texel=1./vec2(textureSize(shadowMap,0));
 for(int x=-1;x<=1;x++)for(int y=-1;y<=1;y++)
  value+=texture(shadowMap,vec3(coord.xy+vec2(x,y)*texel,coord.z-bias));
 return value/9.;
}
"""


class WorldRenderer(study.StudyRenderer):
    """Source-study shader extended with native material maps and mesh shadows."""
    def __init__(self):
        super().__init__()
        self.program.release()
        fragment = study.FRAGMENT.replace("void main(){", PBR_DECLARATIONS + "\nvoid main(){")
        marker = " // Identical simple illumination"
        pbr_block = """
 if(pbr){
  albedo=linearColor(tex.rgb)*base.rgb;
  if(hasNormal)n=mappedNormal(n);
  ao=hasAO?mix(1,texture(nativeAO,uv).g,nativeOcclusion):1;
  smoothness=nativeSmoothness*(hasSurface?texture(nativeSurface,uv).a:1);
 }
"""
        if marker not in fragment:
            raise ValueError("Existing study shader integration marker changed")
        fragment = fragment.replace(marker, pbr_block + marker)
        fragment = fragment.replace("vec3(.398,.530,-.748)", "vec3(-.48,.72,-.50)")
        fragment = fragment.replace("if(tex.a*base.a<.4)discard;", "if(tex.a*base.a<(pbr?nativeCutoff:.4))discard;")
        fragment = fragment.replace("float diffuse=max(dot(n,l),0);", "float diffuse=max(dot(n,l),0)*visibility(n);")
        fragment = fragment.replace("rgb+=sun*.04*pow", "rgb+=sun*(pbr?mix(.04,.20,nativeMetallic):.04)*pow")
        self.program = r.C.program(vertex_shader=study.VERTEX, fragment_shader=fragment)
        for unit, name in enumerate(["atlas", "groundMap", "wallMap", "groundNormal", "wallNormal", "groundSurface", "wallSurface", "nativeNormal", "nativeSurface", "nativeAO", "shadowMap"]):
            self.program[name].value = unit
        self.shadow_program = r.C.program(vertex_shader="""#version 330
in vec3 position;in vec2 texcoord;uniform mat4 vp;out vec2 uv;
void main(){uv=texcoord;gl_Position=vp*vec4(position,1);}
""", fragment_shader="""#version 330
in vec2 uv;uniform sampler2D image;uniform bool textured;uniform float alpha,cutoff;
void main(){if((textured?texture(image,uv).a:1)*alpha<cutoff)discard;}
""")
        self.shadow_program["image"].value = 0
        self.shadow_buffers = {}
        self.materials = {}

    def material(self, model):
        material_guid = model.get("material")
        if material_guid is None:
            return {}, {}
        if material_guid not in self.materials:
            self.materials[material_guid] = study.properties(r.ASSETS[material_guid])
        return self.materials[material_guid]

    def shadow(self, scene, center, radius):
        eye = np.asarray(center) + KEY * 160
        projection = np.eye(4)
        projection[0, 0] = projection[1, 1] = 1 / radius
        projection[2, 2] = -2 / 360
        projection[2, 3] = -1
        vp = projection @ r.view(eye, center)
        depth = r.C.depth_texture((4096, 4096))
        depth.compare_func = "<="
        depth.repeat_x = depth.repeat_y = False
        framebuffer = r.C.framebuffer(depth_attachment=depth)
        framebuffer.use()
        framebuffer.clear(depth=1)
        r.C.enable(moderngl.DEPTH_TEST)
        self.shadow_program["vp"].write(vp.astype("f4").T.tobytes())
        for model in scene:
            key = id(model)
            if key not in self.shadow_buffers:
                packed = np.c_[model["v"], model["uv"]].astype("f4")
                self.shadow_buffers[key] = (model, r.C.vertex_array(self.shadow_program,
                    [(r.C.buffer(packed.tobytes()), "3f 2f", "position", "texcoord")],
                    r.C.buffer(model["t"].astype("u4").tobytes())))
            atlas = study.texture(model["texture"])
            if atlas:
                atlas.use(0)
            self.shadow_program["textured"].value = atlas is not None
            self.shadow_program["alpha"].value = model["color"][3]
            values, _ = self.material(model)
            self.shadow_program["cutoff"].value = values.get("_Cutoff", .5) if values.get("_AlphaClip", 0) else .4
            self.shadow_buffers[key][1].render()
        framebuffer.release()
        return depth, vp

    def render(self, scene, eye, center, size=(1280, 800), fov=58, shadow_radius=55):
        shadow, shadow_vp = self.shadow(scene, center, shadow_radius)
        self.program["shadowVP"].write(shadow_vp.astype("f4").T.tobytes())
        shadow.use(10)
        w, h = size
        q, near, far = 1 / math.tan(math.radians(fov) / 2), .08, 3000
        projection = np.zeros((4, 4))
        projection[0, 0], projection[1, 1] = q * h / w, q
        projection[2, 2], projection[2, 3] = (far + near) / (near - far), 2 * far * near / (near - far)
        projection[3, 2] = -1
        self.program["vp"].write((projection @ r.view(eye, center)).astype("f4").T.tobytes())
        self.program["eye"].value = tuple(eye)
        self.program["after"].value = True  # ff62e76 surface treatment on BOTH sides.
        framebuffer = r.C.simple_framebuffer(size, components=4)
        framebuffer.use()
        framebuffer.clear(.60, .70, .70, 1)
        r.C.enable(moderngl.DEPTH_TEST)
        for model in scene:
            key = id(model)
            if key not in self.buffers:
                packed = np.c_[model["v"], model["n"], model["uv"]].astype("f4")
                self.buffers[key] = (model, r.C.vertex_array(self.program,
                    [(r.C.buffer(packed.tobytes()), "3f 3f 2f", "position", "normal", "texcoord")],
                    r.C.buffer(model["t"].astype("u4").tobytes())))
            atlas = study.texture(model["texture"])
            if atlas:
                atlas.use(0)
            self.program["textured"].value = atlas is not None
            self.program["detail"].value = model.get("detail", False)
            self.program["deck"].value = model.get("deck", False)
            self.program["base"].value = tuple(model["color"])
            maps = self.deck_maps if model.get("deck") else self.maps
            for unit, (_, source) in enumerate(self.bindings, 1):
                study.texture(maps[source]).use(unit)
            for name, source in self.pairs.items():
                value = self.values[source]
                if model.get("deck"):
                    if name in ("groundScale", "wallScale"): value = .5
                    elif name == "normalStrength": value = self.deck_values["_BumpScale"]
                    elif name in ("groundSmoothness", "wallSmoothness"): value = self.deck_values["_Smoothness"]
                    elif name == "occlusionStrength": value = self.deck_values["_OcclusionStrength"]
                self.program[name].value = value
            values, native_maps = self.material(model)
            pbr = bool(model.get("material") and not model.get("detail") and not model.get("deck"))
            self.program["pbr"].value = pbr
            self.program["nativeCutoff"].value = values.get("_Cutoff", .5) if values.get("_AlphaClip", 0) else 0
            for unit, (flag, prop) in enumerate([("hasNormal", "_BumpMap"), ("hasSurface", "_MetallicGlossMap"), ("hasAO", "_OcclusionMap")], 7):
                native = study.texture(native_maps.get(prop))
                self.program[flag].value = native is not None
                if native:
                    native.use(unit)
            for uniform, prop, default in [("nativeBump", "_BumpScale", .65), ("nativeSmoothness", "_Smoothness", .15), ("nativeMetallic", "_Metallic", 0), ("nativeOcclusion", "_OcclusionStrength", 1)]:
                self.program[uniform].value = values.get(prop, default)
            self.buffers[key][1].render()
        image = Image.frombytes("RGBA", size, framebuffer.read(components=4)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        framebuffer.release()
        shadow.release()
        return image


def label(before, after, title, filename):
    width, height = before.size
    image = Image.new("RGB", (width * 2, height + 142), "#101b21")
    image.paste(before, (0, 52))
    image.paste(after, (width, 52))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(study.FONT, 23)
    small = ImageFont.truetype(study.FONT, 18)
    draw.text((20, 13), "BEFORE / ff62e76 SURFACES", font=font, fill="#efe4ce")
    draw.text((width + 20, 13), "AFTER / AUTHORED NATIVE GEOMETRY", font=font, fill="#efe4ce")
    draw.text((20, height + 63), title, font=font, fill="#efe4ce")
    draw.text((20, height + 101), "OFFLINE SOURCE-ASSET RENDER / NOT UNITY / SAME CAMERA AND LIGHT / NO AI-GENERATED SCENERY", font=small, fill="#bacad0")
    draw.line((width, 0, width, height + 52), fill="#e0b861", width=3)
    image.save(OUT / filename)
    standalone = Image.new("RGB", (width, height + 50), "#101b21")
    standalone.paste(after, (0, 0))
    ImageDraw.Draw(standalone).text((16, height + 15), "ACTUAL SOURCE ASSETS / OFFLINE RENDER — NOT UNITY", font=small, fill="#efe4ce")
    standalone.save(OUT / filename.replace("BeforeAfter", "After"))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    before, after, metadata = models_for_scene()
    print("Decoded native scene", json.dumps(metadata), flush=True)
    renderer = WorldRenderer()
    views = [
        {"name": "ArrivalCourt", "eye": [-168, 35.5, 15], "center": [-144, 32.3, 1],
         "fov": 57, "shadow_radius": 58,
         "title": "ARRIVAL COURT / ACTUAL REPLACEMENT WALL, PROJECTED PAVING, EXISTING HELIPAD"},
        {"name": "PrisonWindows", "eye": [-111.83, 55, -33.98], "center": [-108.887, 53.75, -20.293],
         "fov": 50, "shadow_radius": 36,
         "title": "EXPOSED PRISON TOWER / PHYSICAL WINDOW REVEALS, BARS, SILLS AND CORNICES"},
        {"name": "CoastalPlanting", "eye": [14, 18, 110], "center": [22, 16.5, 92],
         "fov": 53, "shadow_radius": 36,
         "title": "COASTAL GREEN PATCH / ACTUAL BRANCHED TREE MESHES AND NATIVE CUTOUT FOLIAGE"},
    ]
    for view in views:
        settings = {key: view[key] for key in ["eye", "center", "fov", "shadow_radius"]}
        print("Rendering", view["name"], flush=True)
        old = renderer.render(before, **settings)
        new = renderer.render(after, **settings)
        difference = np.abs(np.asarray(old, dtype=np.int16)[:, :, :3] -
                            np.asarray(new, dtype=np.int16)[:, :, :3])
        view["changed_pixel_fraction_gt_2_255"] = float(np.mean(np.max(difference, axis=2) > 2))
        view["mean_absolute_rgb_change_255"] = float(np.mean(difference))
        label(old, new, view["title"], view["name"] + "BeforeAfter.png")
    INPUTS.add(Path(__file__).resolve())
    INPUTS.update([Path(study.__file__).resolve(), Path(current.__file__).resolve(),
                   Path(r.__file__).resolve(), ROOT / "Assets/Game/Supplied/Scripts/SuppliedIslandWorld.cs"])
    INPUTS.update([study.PROFILE, study.DECK_PROFILE])
    INPUTS.update(study.TEXTURES)
    for name in ["FacadeRebuild", "ArchitectureKit", "CourtyardSurfaces", "CoastalVegetation"]:
        INPUTS.add(ART / name / "Manifest.json")
    metadata.update({"scope": "Actual native source geometry; offline GLSL material and lighting approximation",
                     "baseline": "ff62e7661a05070616f8f8ab35d8377ef4348d76", "views": views,
                     "fixed_key_direction": KEY.tolist(), "shadow_map_size": [4096, 4096],
                     "vegetation_lod": 0, "duplicate_lod1_rendered": False,
                     "unity_capture": False, "ai_generated_scenery": False,
                     "unity_shader_compilation_verified": False,
                     "physics_or_gpu_performance_verified": False,
                     "known_geometry_limits": [
                         "The two lowest tower windows are partly behind unchanged original foreground geometry; the upper four windows are clear in the documented view.",
                         "The 6 by 10.5 metre tower skin meets the existing terrain; it is a local exposed facade replacement, not a full building or island rebuild.",
                         "Unreconstructed scan wedges, coarse cliffs and sparse planting remain visible; commercial reference quality is not demonstrated.",
                         "The offline coast view does not execute the runtime ocean or sky shaders."],
                     "uploaded_texture_dimensions": {str(path.relative_to(ROOT)): list(texture.size)
                                                       for path, texture in study.TEXTURES.items()},
                     "output_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                       for path in sorted(OUT.glob("*.png"))},
                     "input_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                                       for path in sorted(INPUTS)}})
    (OUT / "Manifest.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (OUT / "README.md").write_text("""# Actual source geometry: offline comparison

These are **offline source-asset renders, not Unity captures or AI concept art**.
Both sides use identical cameras, material decoding, key light, shadow method,
exposure and the current helipad height. Before includes the ff62e76 world-scale
surface profiles and existing ground cover. After replaces exactly the scan
mesh resources listed by FacadeRebuild/Runtime.json before applying the source
island world offset, then adds the current world-space facade, courtyard and
vegetation prefabs. Only LOD0 vegetation is drawn; duplicate LOD1 meshes are omitted.

The unchanged packaged helicopter is rendered from its native baked prefab and
placed with the same runtime height/yaw/grounding rule. No models, sky artwork,
buildings or plant instances are invented for the images. Source textures retain
their original dimensions, including the island's 8192×8192 atlas. Native PBR
normal/AO/smoothness maps and fixed directional geometry shadows are approximated
by this study's GLSL shader. The flat background is a clear color, not a sky asset.

- [Arrival court before/after](ArrivalCourtBeforeAfter.png)
- [Exposed prison tower before/after](PrisonWindowsBeforeAfter.png)
- [Coastal planting before/after](CoastalPlantingBeforeAfter.png)
- [Arrival court after](ArrivalCourtAfter.png)
- [Exposed prison tower after](PrisonWindowsAfter.png)
- [Coastal planting after](CoastalPlantingAfter.png)
- [Inputs, dimensions and camera/light metadata](Manifest.json)

Only the explicitly surveyed facade patches are replaced. Much of the scanned
island still has coarse silhouettes, inconsistent baked detail and sparse
vegetation. On the 6 × 10.5 m tower face, the upper four windows are clear while
the two lowest windows remain partly behind unchanged foreground scan geometry.
The replacement wall continues down to the existing terrain; no foreground ridge
was removed or hidden to expose it. These comparisons show local progress, not the requested commercial
reference quality across the full map. The offline renderer does not execute URP,
the custom Unity shaders, ocean rendering, reflection probes, SSAO, baked/global
illumination, Unity sky/exposure/fog, physics, animation or gameplay UI. The coast
view therefore shows the cropped scan edge against the clear background; this
does not show how the runtime ocean covers that edge. Native shader/API
compilation, Unity appearance and target-PC performance remain unverified.

Reproduce with `python Tools/render_world_rebuild_preview.py` after installing
`Tools/requirements-supplied.txt`. The tool reads runtime assets and writes only
this documentation directory.
""")
    print("Saved", OUT, flush=True)


if __name__ == "__main__":
    main()
