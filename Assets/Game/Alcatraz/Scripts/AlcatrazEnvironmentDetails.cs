using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;
using Blackstone.Supplied;

namespace Blackstone.Alcatraz
{
    // Presentation only: original scan assets, colliders and travel points
    // remain authoritative. Selected visual meshes are reversible runtime copies.
    [DefaultExecutionOrder(150), DisallowMultipleComponent]
    public sealed class AlcatrazEnvironmentDetails : MonoBehaviour
    {
        public int DetailedScanRenderers { get; private set; }
        public int GroundCoverRenderers { get; private set; }
        public bool HelipadDetailed { get; private set; }
        public int RebuiltScanChunks { get; private set; }
        public int FacadeRenderers { get; private set; }
        public int CourtyardRenderers { get; private set; }
        public int VegetationRenderers { get; private set; }
        public string Status { get; private set; }
        readonly List<Material> materials = new List<Material>();
        readonly Dictionary<Renderer, Material[]> originals = new Dictionary<Renderer, Material[]>();
        readonly Dictionary<MeshFilter, Mesh> originalMeshes = new Dictionary<MeshFilter, Mesh>();
        GameObject dressing;
        Mesh markings;

        public static AlcatrazEnvironmentDetails Ensure(GameObject owner)
        {
            if (owner == null) return null;
            var detail = owner.GetComponent<AlcatrazEnvironmentDetails>();
            return detail != null ? detail : owner.AddComponent<AlcatrazEnvironmentDetails>();
        }

        void Start()
        {
            var supplied = FindFirstObjectByType<SuppliedIslandWorld>();
            if (supplied == null)
            {
                Status = "Authored PBR surfaces retained; shared afternoon lighting active.";
                return;
            }
            if (!supplied.Ready) { Status = "Waiting for a usable supplied island."; return; }
            dressing = new GameObject("Alcatraz environment detail");
            dressing.transform.SetParent(transform, false);
            dressing.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
            dressing.transform.localScale = Vector3.one;
            ApplyScan(supplied);
            ApplyDecks(supplied);
            AddGroundCover();
            AddWorldRebuild(supplied);
            Status = DetailedScanRenderers + " scan surfaces detailed; " + GroundCoverRenderers
                + " ground-cover chunks; helipad " + (HelipadDetailed ? "marked" : "unavailable") + ".";
            Status += " Rebuilt " + RebuiltScanChunks + " visual chunks; " + FacadeRenderers
                + " facade, " + CourtyardRenderers + " courtyard and " + VegetationRenderers + " vegetation renderers.";
        }

        public Mesh OriginalScanMesh(MeshFilter filter)
        { return filter != null && originalMeshes.TryGetValue(filter, out var source) ? source : filter != null ? filter.sharedMesh : null; }

        [System.Serializable] sealed class RebuildIndex { public int facadeRenderers; public VisualReplacement[] replacements; }
        [System.Serializable] sealed class VisualReplacement { public string sourceMesh, resource; }

        static bool UsableWorldPrefab(GameObject prefab, int expectedRenderers = 0)
        {
            if (prefab == null || prefab.GetComponentsInChildren<Collider>(true).Length != 0) return false;
            var renderers = prefab.GetComponentsInChildren<MeshRenderer>(true);
            if (renderers.Length == 0 || (expectedRenderers > 0 && renderers.Length != expectedRenderers)) return false;
            var filters = prefab.GetComponentsInChildren<MeshFilter>(true);
            if (filters.Length != renderers.Length) return false;
            foreach (var renderer in renderers)
            {
                var filter = renderer.GetComponent<MeshFilter>();
                if (filter == null || filter.sharedMesh == null || filter.sharedMesh.vertexCount == 0) return false;
                var slots = renderer.sharedMaterials;
                if (slots.Length < filter.sharedMesh.subMeshCount) return false;
                foreach (var material in slots)
                    if (material == null || material.shader == null || !material.shader.isSupported) return false;
            }
            return true;
        }

        GameObject AddWorldPrefab(string resource, int expectedRenderers = 0)
        {
            var prefab = Resources.Load<GameObject>(resource);
            if (!UsableWorldPrefab(prefab, expectedRenderers))
            {
                Debug.LogWarning("Environment resource incomplete or unsupported; skipped " + resource + ".");
                return null;
            }
            var instance = Instantiate(prefab, dressing.transform, false);
            instance.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
            instance.transform.localScale = Vector3.one;
            return instance;
        }

        void AddWorldRebuild(SuppliedIslandWorld supplied)
        {
            var court = AddWorldPrefab("Alcatraz/CourtyardSurfaces/CourtyardSurfaces");
            if (court != null) CourtyardRenderers = court.GetComponentsInChildren<MeshRenderer>(true).Length;
            var vegetation = AddWorldPrefab("Alcatraz/CoastalVegetation/CoastalVegetation");
            if (vegetation != null) VegetationRenderers = vegetation.GetComponentsInChildren<MeshRenderer>(true).Length;
            var prefab = Resources.Load<GameObject>("Alcatraz/FacadeRebuild/FacadeRebuild");
            var data = Resources.Load<TextAsset>("Alcatraz/FacadeRebuild/Runtime");
            var scan = supplied.transform.Find("Supplied Island");
            if (prefab == null || data == null || scan == null) return;
            RebuildIndex index;
            try { index = JsonUtility.FromJson<RebuildIndex>(data.text); }
            catch (System.ArgumentException) { Debug.LogWarning("Facade index unreadable; original visual meshes retained."); return; }
            if (index == null || index.replacements == null || index.replacements.Length == 0
                || index.facadeRenderers <= 0 || !UsableWorldPrefab(prefab, index.facadeRenderers))
            {
                Debug.LogWarning("Facade prefab incomplete or unsupported; original visual meshes retained.");
                return;
            }
            var pending = new Dictionary<MeshFilter, Mesh>();
            // Resolve every replacement and the facade prefab before removing any
            // old wall pixels. A partial import keeps the original closed scan.
            foreach (var replacement in index.replacements)
            {
                if (replacement == null || string.IsNullOrEmpty(replacement.sourceMesh) || string.IsNullOrEmpty(replacement.resource)) return;
                var visual = Resources.Load<Mesh>(replacement.resource);
                MeshFilter target = null;
                foreach (var filter in scan.GetComponentsInChildren<MeshFilter>(true))
                    if (filter.sharedMesh != null && filter.sharedMesh.name == replacement.sourceMesh) { target = filter; break; }
                var collider = target != null ? target.GetComponent<MeshCollider>() : null;
                if (visual == null || visual.vertexCount == 0 || target == null || pending.ContainsKey(target)
                    || collider == null || collider.sharedMesh != target.sharedMesh
                    || visual.subMeshCount != target.sharedMesh.subMeshCount)
                {
                    Debug.LogWarning("Facade rebuild incomplete; original visual meshes retained.");
                    return;
                }
                pending.Add(target, visual);
            }
            var facade = AddWorldPrefab("Alcatraz/FacadeRebuild/FacadeRebuild", index.facadeRenderers);
            if (facade == null) return;
            foreach (var item in pending)
            {
                originalMeshes.Add(item.Key, item.Key.sharedMesh);
                item.Key.sharedMesh = item.Value;
            }
            RebuiltScanChunks = pending.Count;
            FacadeRenderers = facade.GetComponentsInChildren<MeshRenderer>(true).Length;
        }

        void Replace(Renderer renderer, Material[] replacements)
        {
            if (!originals.ContainsKey(renderer)) originals.Add(renderer, renderer.sharedMaterials);
            renderer.sharedMaterials = replacements;
        }

        void ApplyScan(SuppliedIslandWorld supplied)
        {
            var scan = supplied.transform.Find("Supplied Island");
            var profile = Resources.Load<Material>("Alcatraz/SurfaceDetails/IslandSurface");
            if (scan == null || profile == null || profile.shader == null || !profile.shader.isSupported)
            {
                Debug.LogWarning("Island surface detail unavailable; original scan materials retained.");
                return;
            }
            var clones = new Dictionary<Material, Material>();
            foreach (var renderer in scan.GetComponentsInChildren<MeshRenderer>(true))
            {
                var slots = renderer.sharedMaterials;
                for (int i = 0; i < slots.Length; i++)
                {
                    var source = slots[i];
                    if (source == null || !source.HasProperty("_BaseMap")) continue;
                    if (!clones.TryGetValue(source, out var detailed))
                    {
                        detailed = new Material(profile) { name = source.name + " (world surface detail)" };
                        detailed.SetTexture("_BaseMap", source.GetTexture("_BaseMap"));
                        detailed.SetTextureScale("_BaseMap", source.GetTextureScale("_BaseMap"));
                        detailed.SetTextureOffset("_BaseMap", source.GetTextureOffset("_BaseMap"));
                        if (source.HasProperty("_BaseColor")) detailed.SetColor("_BaseColor", source.GetColor("_BaseColor"));
                        clones.Add(source, detailed); materials.Add(detailed);
                    }
                    slots[i] = detailed;
                }
                Replace(renderer, slots); DetailedScanRenderers++;
            }
        }

        void ApplyDecks(SuppliedIslandWorld supplied)
        {
            var concrete = Resources.Load<Material>("Alcatraz/SurfaceDetails/HelipadConcrete");
            var timber = Resources.Load<Material>("Alcatraz/SurfaceDetails/DockTimber");
            Renderer helipad = null;
            foreach (var renderer in supplied.GetComponentsInChildren<MeshRenderer>(true))
            {
                if (renderer.name == "Helicopter landing deck")
                {
                    helipad = renderer;
                    if (concrete != null) Replace(renderer, new[] { Tiled(concrete, renderer) });
                }
                else if (timber != null && (renderer.name == "Coastal service pier" || renderer.name == "House dock platform"))
                    Replace(renderer, new[] { Tiled(timber, renderer) });
            }
            if (helipad == null || supplied.Helipad == null || concrete == null) return;
            var paint = new Material(concrete) { name = "Weathered helipad paint" };
            paint.SetTexture("_BaseMap", null); paint.SetTexture("_BumpMap", null);
            paint.SetTexture("_MetallicGlossMap", null); paint.SetTexture("_OcclusionMap", null);
            paint.DisableKeyword("_NORMALMAP"); paint.DisableKeyword("_METALLICSPECGLOSSMAP"); paint.DisableKeyword("_OCCLUSIONMAP");
            paint.color = new Color(.88f, .77f, .39f); paint.SetFloat("_Smoothness", .1f); materials.Add(paint);
            var vertices = new List<Vector3>(); var indices = new List<int>();
            float y = helipad.bounds.max.y + .012f;
            Vector3 center = new Vector3(supplied.Helipad.position.x, y, supplied.Helipad.position.z);
            // Thin opaque, non-colliding paint geometry avoids decal/renderer-feature dependencies.
            for (int side = 0; side < 4; side++)
            {
                var rotation = Quaternion.Euler(0, side * 90, 0);
                Quad(vertices, indices, center + rotation * new Vector3(-5.3f, 0, 5.3f),
                    center + rotation * new Vector3(5.3f, 0, 5.3f),
                    center + rotation * new Vector3(5.3f, 0, 5.08f),
                    center + rotation * new Vector3(-5.3f, 0, 5.08f));
            }
            Rect(vertices, indices, center, -1.5f, -2, -.95f, 2);
            Rect(vertices, indices, center, .95f, -2, 1.5f, 2);
            Rect(vertices, indices, center, -.95f, -.3f, .95f, .3f);
            markings = new Mesh { name = "Helipad perimeter and H paint" };
            markings.SetVertices(vertices); markings.SetTriangles(indices, 0); markings.RecalculateNormals(); markings.RecalculateBounds();
            var go = new GameObject("Helipad painted perimeter and H"); go.transform.SetParent(dressing.transform, false);
            go.AddComponent<MeshFilter>().sharedMesh = markings;
            var surface = go.AddComponent<MeshRenderer>(); surface.sharedMaterial = paint;
            surface.shadowCastingMode = ShadowCastingMode.Off; surface.receiveShadows = true;
            HelipadDetailed = true;
        }

        Material Tiled(Material source, Renderer renderer)
        {
            var material = new Material(source) { name = source.name + " (metre scale)" };
            var size = renderer.transform.lossyScale;
            var repeat = new Vector2(Mathf.Max(1, Mathf.Abs(size.x) * .5f), Mathf.Max(1, Mathf.Abs(size.z) * .5f));
            foreach (string property in new[] { "_BaseMap", "_MainTex", "_BumpMap", "_MetallicGlossMap", "_OcclusionMap" })
                if (material.HasProperty(property)) material.SetTextureScale(property, repeat);
            materials.Add(material); return material;
        }

        static void Rect(List<Vector3> vertices, List<int> indices, Vector3 center, float x0, float z0, float x1, float z1)
        { Quad(vertices, indices, center + new Vector3(x0, 0, z0), center + new Vector3(x0, 0, z1), center + new Vector3(x1, 0, z1), center + new Vector3(x1, 0, z0)); }

        static void Quad(List<Vector3> vertices, List<int> indices, Vector3 a, Vector3 b, Vector3 c, Vector3 d)
        {
            int first = vertices.Count; vertices.Add(a); vertices.Add(b); vertices.Add(c); vertices.Add(d);
            indices.AddRange(new[] { first, first + 1, first + 2, first, first + 2, first + 3 });
        }

        void AddGroundCover()
        {
            var prefab = Resources.Load<GameObject>("Alcatraz/EnvironmentDressing/SuppliedGroundCover");
            if (prefab == null) return;
            var cover = Instantiate(prefab, dressing.transform, false);
            cover.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity); cover.transform.localScale = Vector3.one;
            GroundCoverRenderers = cover.GetComponentsInChildren<MeshRenderer>(true).Length;
        }

        void OnDestroy()
        {
            foreach (var item in originalMeshes) if (item.Key != null) item.Key.sharedMesh = item.Value;
            foreach (var item in originals) if (item.Key != null) item.Key.sharedMaterials = item.Value;
            if (dressing != null) Destroy(dressing);
            foreach (var material in materials) if (material != null) Destroy(material);
            if (markings != null) Destroy(markings);
        }
    }
}
