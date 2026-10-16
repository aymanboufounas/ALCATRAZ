"""Author a small physical facade kit from the project's existing CC0 PBR maps.

Run normally to write deterministic Unity-native assets.  --check constructs the
same assets in a temporary directory and compares every byte; it never updates
the checked-in kit.  Geometry is in metres, +Y up, facade front toward -Z.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import tempfile

import numpy as np

import geometry as g
import unity_writer as u


PROJECT = Path(__file__).resolve().parents[1]
BASE = "Assets/Game/Alcatraz/Resources/Alcatraz/ArchitectureKit"
PBR = "Assets/Game/Textures/PBR_"
OWNED = ["CoastalConcrete", "WeatheredBrick", "LimestoneTrim", "PaintedSteel",
         "OxidizedSteel", "RecessedGlass", "OldTimber"]


def clean_write(path: str, content: str) -> None:
    u.write(path, "\n".join(row.rstrip() for row in content.splitlines()) + "\n")


def folder(path: str) -> None:
    clean_write(path + ".meta", "fileFormatVersion: 2\nguid: " + u.guid(path) +
                "\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n")


def quad(mesh: g.Mesh, points, facing, uv=None) -> None:
    points = [np.asarray(point, dtype=float) for point in points]
    if np.dot(np.cross(points[1] - points[0], points[2] - points[0]), facing) < 0:
        points = list(reversed(points))
        if uv is not None:
            uv = list(reversed(uv))
    if uv is None:
        axis = int(np.argmax(np.abs(facing)))
        other = [value for value in range(3) if value != axis]
        uv = [(point[other[0]], point[other[1]]) for point in points]
    mesh.quad(*points, uv=uv)


def rect_points(rect, z):
    x0, y0, x1, y1 = rect
    return [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]


def rect_shell(mesh, outer, inner, z, facing=(0, 0, -1)):
    outside, inside = rect_points(outer, z), rect_points(inner, z)
    for index in range(4):
        following = (index + 1) % 4
        quad(mesh, [outside[index], outside[following], inside[following], inside[index]], facing)


def ring_profile(sections):
    """Closed rectangular molding: [(rectangle,depth)] follows its cross-section."""
    mesh = g.Mesh()
    for section in range(len(sections)):
        first, z1 = sections[section]
        second, z2 = sections[(section + 1) % len(sections)]
        a, b = rect_points(first, z1), rect_points(second, z2)
        for index in range(4):
            following = (index + 1) % 4
            # Cross-section winds from outer back, round front, to inner back.
            points = [a[index], a[following], b[following], b[index]]
            normal = -np.cross(np.subtract(points[1], points[0]), np.subtract(points[2], points[0]))
            if np.linalg.norm(normal) < 1e-10:
                continue
            # Winding for frame ring sections follows the same perimeter.
            quad(mesh, points, normal)
    return mesh


def wall(opening=None):
    """One continuous facade face with a genuine window/door opening."""
    mesh = g.Mesh()
    bounds = (-1.5, 0, 1.5, 3.5)
    if opening is None:
        return beveled_box((3, 3.5, .28), (0, 1.75, .14), bevel=.012)
    rect_shell(mesh, bounds, opening, 0)
    rect_shell(mesh, bounds, opening, .28, (0, 0, 1))
    a, b = rect_points(bounds, 0), rect_points(bounds, .28)
    for index, normal in enumerate([(0, -1, 0), (1, 0, 0), (0, 1, 0), (-1, 0, 0)]):
        following = (index + 1) % 4
        quad(mesh, [a[index], b[index], b[following], a[following]], normal)
    return mesh


def beveled_box(size, position, bevel=.015):
    return g.Mesh().merge(g.box(size, bevel), pos=position)


def cylinder(radius, height, segments=12, top_radius=None):
    """Smooth metal cylinder with circumferential/length UVs measured in metres."""
    top_radius = radius if top_radius is None else top_radius
    mesh = g.Mesh()
    for index in range(segments):
        a, b = math.tau * index / segments, math.tau * (index + 1) / segments
        points = [(radius * math.cos(a), -height / 2, radius * math.sin(a)),
                  (top_radius * math.cos(a), height / 2, top_radius * math.sin(a)),
                  (top_radius * math.cos(b), height / 2, top_radius * math.sin(b)),
                  (radius * math.cos(b), -height / 2, radius * math.sin(b))]
        normals = [(math.cos(angle), (radius - top_radius) / height, math.sin(angle))
                   for angle in [a, a, b, b]]
        normals = [np.asarray(normal) / np.linalg.norm(normal) for normal in normals]
        uv = [(radius * a, 0), (radius * a, height), (radius * b, height), (radius * b, 0)]
        for indices in [(0, 1, 2), (0, 2, 3)]:
            mesh.tri(*(points[value] for value in indices),
                     uvs=[uv[value] for value in indices],
                     normals=[normals[value].tolist() for value in indices])
        mesh.tri((0, height / 2, 0), points[2], points[1],
                 uvs=[(0, 0), (points[2][0], points[2][2]), (points[1][0], points[1][2])])
        mesh.tri((0, -height / 2, 0), points[0], points[3],
                 uvs=[(0, 0), (points[0][0], points[0][2]), (points[3][0], points[3][2])])
    return mesh


def extruded_profile(points, width=3):
    """Profile in (height,depth); stepped cornice is capped by horizontal strips."""
    mesh = g.Mesh()
    for index in range(len(points)):
        first, second = points[index], points[(index + 1) % len(points)]
        corners = [(-width / 2, *first), (width / 2, *first),
                   (width / 2, *second), (-width / 2, *second)]
        normal = -np.cross(np.subtract(corners[1], corners[0]), np.subtract(corners[2], corners[0]))
        quad(mesh, corners, normal,
             uv=[(-width / 2, first[0]), (width / 2, first[0]),
                 (width / 2, second[0]), (-width / 2, second[0])])
    # Outer surface increases monotonically in Y; back edge is at the final Z.
    front = points[:-2] if points[-2][0] == points[-3][0] else points[:-1]
    back = max(point[1] for point in points)
    for index in range(len(front) - 1):
        y0, z0 = front[index]
        y1, z1 = front[index + 1]
        if abs(y1 - y0) < 1e-9:
            continue
        for side in [-1, 1]:
            x = side * width / 2
            quad(mesh, [(x, y0, back), (x, y0, z0), (x, y1, z1), (x, y1, back)],
                 (side, 0, 0))
    return mesh


def materials(source: Path):
    descriptions = {}
    for name, color, roughness, metallic, stem in [
            ("CoastalConcrete", (.73, .71, .64, 1), .85, 0, "concrete_floor_worn_001"),
            ("WeatheredBrick", (.72, .65, .55, 1), .88, 0, "brick_wall_001"),
            ("LimestoneTrim", (.86, .83, .74, 1), .76, 0, "concrete_floor_worn_001"),
            ("PaintedSteel", (.105, .145, .139, 1), .62, .5, "concrete_floor_worn_001"),
            ("OxidizedSteel", (.19, .15, .105, 1), .7, .73, "concrete_floor_worn_001"),
            ("RecessedGlass", (.025, .044, .045, 1), .18, .1, None),
            ("OldTimber", (.52, .44, .33, 1), .86, 0, "wood_planks")]:
        is_metal = "Steel" in name
        maps = {} if stem is None else {
            "base": PBR + stem + "_Base.png", "normal": PBR + stem + "_Normal.png",
            "surface": PBR + stem + "_Surface.png"}
        path = u.material(name, color, rough=roughness, metal=metallic,
                          texture=maps.get("base"), normal=maps.get("normal"),
                          surface=None if is_metal else maps.get("surface"),
                          occlusion=maps.get("surface"), tiling=.5 if name == "WeatheredBrick" else 1)
        # Metal stays a measured constant because the reused nonmetal surface map's
        # red channel is zero. Its green AO is still sampled separately.
        text = (u.ROOT / path).read_text()
        if is_metal:
            text = text.replace("    - _BumpScale: 0.65", "    - _BumpScale: 0.18")
        for texture in maps.values():
            meta = (source / (texture + ".meta")).read_text()
            actual = re.search(r"^guid: (\w+)", meta, re.M).group(1)
            text = text.replace(u.guid(texture), actual)
        clean_write(path, text)
        descriptions[name] = {"path": path, "base_color": list(color),
                              "roughness": roughness, "metallic": metallic,
                              "maps": maps, "surface_map_drives_metallic": bool(stem and not is_metal),
                              "opaque": True, "emission": False}
    return descriptions


def author(destination: Path, source: Path):
    u.ROOT = destination
    u.ART = BASE
    u.MESHES.clear()
    u.MATERIALS.clear()
    u.Node.all.clear()
    u.Node.counter = 1000
    u.PREVIEW = {"meshes": {}, "materials": {}, "nodes": []}
    material_manifest = materials(source)
    modules = []

    def module(name, parts, use, nominal=(3, 3.5), notes=""):
        root = u.Node(name)
        components = []
        total_vertices = total_triangles = 0
        all_vertices = []
        for index, (part_name, mesh, material) in enumerate(parts):
            mesh_name = name + "_" + part_name
            mesh_path = u.save_mesh(mesh_name, mesh, "Meshes")
            node = u.Node(part_name, root, layer=0).render(mesh_name, material)
            total_vertices += len(mesh.v)
            total_triangles += len(mesh.t) // 3
            all_vertices.extend(mesh.v)
            components.append({"name": part_name, "mesh": mesh_path,
                               "material": u.MATERIALS[material],
                               "vertices": len(mesh.v), "triangles": len(mesh.t) // 3})
        vertices = np.asarray(all_vertices)
        prefab = BASE + "/Prefabs/" + name + ".prefab"
        clean_write(prefab, u.HEAD + u.node_yaml(root, True) +
                    "".join(u.node_yaml(child) for child in root.children))
        u.meta(prefab, "PrefabImporter")
        modules.append({"name": name, "prefab": prefab,
                        "resources_path": "Alcatraz/ArchitectureKit/Prefabs/" + name,
                        "anchor": [0, 0, 0], "nominal_width_height_m": list(nominal),
                        "bounds_min_m": np.round(vertices.min(axis=0), 6).tolist(),
                        "bounds_max_m": np.round(vertices.max(axis=0), 6).tolist(),
                        "triangles": total_triangles, "vertices": total_vertices,
                        "use": use, "notes": notes, "parts": components,
                        "colliders": 0})

    opening = (-.72, .96, .72, 2.98)
    frame = ring_profile([
        ((-.705, .975, .705, 2.965), .17),
        ((-.705, .975, .705, 2.965), .055),
        ((-.685, .995, .685, 2.945), .035),
        ((-.565, 1.115, .565, 2.825), .035),
        ((-.55, 1.13, .55, 2.81), .055),
        ((-.55, 1.13, .55, 2.81), .17)])
    reveal = ring_profile([
        (opening, .0), ((-.67, 1.01, .67, 2.93), .055),
        ((-.67, 1.01, .67, 2.93), .225), (opening, .28)])
    glass = beveled_box((1.1, 1.68, .014), (0, 1.97, .195), .003)
    mullions = g.Mesh()
    mullions.merge(g.box((.045, 1.70, .045), .006), pos=(0, 1.97, .138))
    for y in [1.69, 2.25]:
        mullions.merge(g.box((1.12, .04, .045), .006), pos=(0, y, .138))
    sill = extruded_profile([(.86, .16), (.86, -.16), (.89, -.205),
                             (.94, -.205), (1.0, -.14), (1.0, .16)], width=1.64)
    common = [("ChamferedReveal", reveal, "LimestoneTrim"),
              ("SteelFrame", frame, "PaintedSteel"),
              ("RecessedGlass", glass, "RecessedGlass"),
              ("Mullions", mullions, "PaintedSteel"),
              ("SlopedSill", sill, "LimestoneTrim")]
    module("FacadeWindow", [("ConcreteWall", wall(opening), "CoastalConcrete")] + common,
           "Windowed concrete service/prison facade", notes="Glass is recessed 0.195m; no emission. Wall has a physical opening.")
    bars = g.Mesh()
    for x in [-.50, -.30, -.10, .10, .30, .50]:
        bars.merge(cylinder(.016, 1.9, 10), pos=(x, 1.97, -.065))
    for y in [1.14, 2.03, 2.80]:
        bars.merge(g.box((1.30, .042, .046), .007), pos=(0, y, -.065))
    mounts = g.Mesh()
    for x in [-.63, .63]:
        for y in [1.14, 2.80]:
            mounts.merge(g.box((.10, .12, .07), .009), pos=(x, y, -.025))
            mounts.merge(cylinder(.018, .012, 6), pos=(x, y, -.069), rot=(90, 0, 0))
    module("FacadeBarredWindow", [("BrickWall", wall(opening), "WeatheredBrick")] + common +
           [("PrisonBars", bars, "OxidizedSteel"), ("BoltedBarMounts", mounts, "PaintedSteel")],
           "Barred brick service/prison facade", notes="Six cylindrical steel bars, three cross rails and bolted mounts.")
    boards = g.Mesh()
    for index, y in enumerate([1.26, 1.61, 1.96, 2.31, 2.66]):
        boards.merge(g.box((1.42, .30, .047), .008), pos=(.015 * (index % 2), y, -.038),
                     rot=(0, 0, (-1 if index % 2 else 1) * 1.8))
    nails = g.Mesh()
    for x in [-.49, .49]:
        for y in [1.26, 1.61, 1.96, 2.31, 2.66]:
            nails.merge(cylinder(.01, .008, 6), pos=(x, y, -.067), rot=(90, 0, 0))
    module("FacadeBoardedWindow", [("ConcreteWall", wall(opening), "CoastalConcrete")] + common +
           [("OldTimberBoards", boards, "OldTimber"), ("BoardFixings", nails, "OxidizedSteel")],
           "Boarded closed window for abandoned service buildings")
    blank = beveled_box((3, 3.5, .28), (0, 1.75, .14), .012)
    plinth = beveled_box((3, .28, .11), (0, .14, -.045), .016)
    module("FacadeBlank", [("ConcreteWall", blank, "CoastalConcrete"),
                           ("WeatheredPlinth", plinth, "LimestoneTrim")],
           "Continuous solid wall bay; do not cover a playable doorway")

    door_opening = (-.68, .06, .68, 2.68)
    jamb = ring_profile([(door_opening, .21), (door_opening, -.025),
                         ((-.65, .09, .65, 2.65), -.055),
                         ((-.56, .16, .56, 2.55), -.055),
                         ((-.54, .18, .54, 2.53), -.025),
                         ((-.54, .18, .54, 2.53), .21)])
    door = beveled_box((1.075, 2.345, .055), (0, 1.355, .073), .014)
    door_panels = g.Mesh()
    for y, height in [(.73, .96), (1.94, .94)]:
        door_panels.merge(g.box((.87, height, .025), .016), pos=(0, y, .035))
    hardware = g.Mesh()
    for y in [.49, 1.32, 2.24]:
        hardware.merge(cylinder(.027, .14, 10), pos=(-.52, y, .016))
        hardware.merge(g.box((.14, .09, .018), .004), pos=(-.44, y, .018))
    hardware.merge(g.box((.09, .26, .018), .01), pos=(.37, 1.32, .018))
    hardware.merge(g.box((.17, .033, .055), .012), pos=(.32, 1.34, -.02))
    kick = beveled_box((.94, .22, .022), (0, .34, .018), .007)
    module("AccessDoor", [("ConcreteWall", wall(door_opening), "CoastalConcrete"),
                          ("ChamferedDoorJamb", jamb, "LimestoneTrim"),
                          ("SteelDoorLeaf", door, "PaintedSteel"),
                          ("InsetPanels", door_panels, "PaintedSteel"),
                          ("HingesAndHandle", hardware, "OxidizedSteel"),
                          ("KickPlate", kick, "OxidizedSteel")],
           "Closed decorative metal service door", notes="Noninteractive visual module. Never place across a required gameplay entrance.")

    cornice = extruded_profile([(0, .12), (0, -.035), (.07, -.035), (.10, -.085),
                                (.16, -.085), (.23, -.165), (.27, -.165),
                                (.31, -.25), (.37, -.25), (.41, -.20), (.41, .12)])
    module("RoofCornice", [("SteppedCoping", cornice, "LimestoneTrim")],
           "Continuous roof-edge coping/cornice; snap adjacent segments at 3m", nominal=(3, .41),
           notes="Anchor at bottom of coping, not bottom of storey. Front projects 0.25m.")

    pipe = g.Mesh()
    pipe.merge(cylinder(.054, 3.27, 12), pos=(0, 1.695, -.15))
    pipe.merge(cylinder(.066, .17, 12, top_radius=.054), pos=(0, 3.415, -.15))
    rings = g.Mesh()
    brackets = g.Mesh()
    for y in [.32, 1.72, 3.10]:
        rings.merge(cylinder(.069, .052, 12), pos=(0, y, -.15))
        for x in [-.085, .085]:
            brackets.merge(g.box((.04, .13, .18), .006), pos=(x, y, -.078))
            brackets.merge(cylinder(.014, .012, 6), pos=(x, y, -.174), rot=(90, 0, 0))
    module("Drainpipe", [("MetalDownpipe", pipe, "OxidizedSteel"),
                         ("PipeCollars", rings, "PaintedSteel"),
                         ("WallBrackets", brackets, "PaintedSteel")],
           "Narrow vertical facade accent; place away from window and door openings",
           nominal=(.21, 3.5), notes="Pipe is 108mm diameter with flared upper socket and three metal mounts.")

    for path in [BASE, BASE + "/Meshes", BASE + "/Materials", BASE + "/Prefabs"]:
        folder(path)
    for path in (destination / BASE).rglob("*"):
        if path.is_file():
            clean_write(str(path.relative_to(destination)), path.read_text())
    for path in (destination / BASE).rglob("*"):
        if path.is_file() and not path.name.endswith(".meta"):
            meta = str(path.relative_to(destination)) + ".meta"
            if not (destination / meta).exists():
                u.meta(str(path.relative_to(destination)))
    manifest = {
        "schema_version": 1,
        "description": "Original physical modular prison/service-building kit; not a rendered quality claim.",
        "authoring_command": "python Tools/author_prison_architecture.py",
        "check_command": "python Tools/author_prison_architecture.py --check",
        "coordinate_system": {"units": "metres", "up": "+Y", "front": "-Z",
                              "facade_anchor": "Bottom centre of the 3m x 3.5m bay; front wall plane z=0.",
                              "facade_core_depth_m": [0, .28]},
        "geometry_policy": {"colliders": 0, "runtime_scripts": 0,
                            "uvs": "Planar material coordinates in metres, cylindrical arc/height in metres; brick profile repeats every2m.",
                            "window_detail": "Real opening, chamfered reveal, recessed opaque dark glass, molded metal frame, 6 panes, sloped sill.",
                            "placement": "Root owns placements and scan-surface masking. Do not cover gates, required entrances or collision routes."},
        "material_provenance": {"license": "Existing Poly Haven CC0 maps, unchanged and referenced in place.",
                                "credits": "Documentation/ThirdParty_Art_Credits.md"},
        "materials": material_manifest,
        "module_count": len(modules),
        "triangles_all_modules": sum(item["triangles"] for item in modules),
        "vertices_all_modules": sum(item["vertices"] for item in modules),
        "modules": modules,
        "unity_runtime_verified": False,
        "files_sha256": {str(path.relative_to(destination)): hashlib.sha256(path.read_bytes()).hexdigest()
                         for path in sorted((destination / BASE).rglob("*"))
                         if path.is_file() and path.name != "Manifest.json" and path.name != "Manifest.json.meta"},
    }
    if manifest["triangles_all_modules"] > 15000:
        raise ValueError("Architecture kit exceeds 15,000-triangle authoring budget")
    clean_write(BASE + "/Manifest.json", json.dumps(manifest, indent=2, sort_keys=True))
    u.meta(BASE + "/Manifest.json")
    clean_write(BASE + "/Manifest.json.meta", (destination / (BASE + "/Manifest.json.meta")).read_text())
    return manifest


def files(root):
    result = {str(path.relative_to(root)): path.read_bytes()
              for path in (root / BASE).rglob("*") if path.is_file()}
    result[BASE + ".meta"] = (root / (BASE + ".meta")).read_bytes()
    return result


def validate(manifest, generated):
    for mesh_name, (_, mesh) in u.MESHES.items():
        vertices, normals, uv = np.asarray(mesh.v), np.asarray(mesh.n), np.asarray(mesh.uv)
        triangles = np.asarray(mesh.t).reshape(-1, 3)
        if not all(np.isfinite(values).all() for values in [vertices, normals, uv]):
            raise ValueError("Nonfinite geometry in " + mesh_name)
        if triangles.min() < 0 or triangles.max() >= len(vertices):
            raise ValueError("Invalid indices in " + mesh_name)
        area = np.linalg.norm(np.cross(vertices[triangles[:, 1]] - vertices[triangles[:, 0]],
                                       vertices[triangles[:, 2]] - vertices[triangles[:, 0]]), axis=1)
        if (area < 1e-10).any():
            raise ValueError("Degenerate geometry in " + mesh_name)
        if not np.allclose(np.linalg.norm(normals, axis=1), 1, atol=2e-5):
            raise ValueError("Nonunit normals in " + mesh_name)
    for path, payload in generated.items():
        if path.endswith(".prefab") and re.search(rb"^--- !u!(?:64|65|135|136|143)\s", payload, re.M):
            raise ValueError("Unexpected collider in " + path)
    assert manifest["module_count"] == 7
    assert manifest["triangles_all_modules"] < 15000


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare deterministic output without modifying project")
    args = parser.parse_args()
    if args.check:
        with tempfile.TemporaryDirectory(prefix="alcatraz-architecture-") as directory:
            manifest = author(Path(directory), PROJECT)
            generated = files(Path(directory))
            validate(manifest, generated)
            existing = files(PROJECT)
            missing = sorted(set(generated) - set(existing))
            extra = sorted(set(existing) - set(generated))
            changed = sorted(path for path in set(generated) & set(existing)
                             if generated[path] != existing[path])
            if missing or extra or changed:
                raise SystemExit(json.dumps({"status": "FAIL", "missing": missing, "extra": extra,
                                             "changed": changed}, indent=2))
    else:
        manifest = author(PROJECT, PROJECT)
        validate(manifest, files(PROJECT))
    print(json.dumps({"status": "PASS", "check_only": args.check,
                      "module_count": manifest["module_count"],
                      "triangles_all_modules": manifest["triangles_all_modules"],
                      "vertices_all_modules": manifest["vertices_all_modules"],
                      "files": len(files(PROJECT)), "colliders": 0,
                      "unity_runtime_verified": False}, indent=2))


if __name__ == "__main__":
    main()
