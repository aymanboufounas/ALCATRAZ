#if UNITY_EDITOR
using System;
using UnityEditor;
using UnityEngine;
using Blackstone.Supplied;

namespace Blackstone.Alcatraz.Editor
{
    // Resource/geometry integration checks; rendered quality is a separate review.
    public static class EnvironmentDetailGameplayChecks
    {
        static int checks;
        static void Check(bool value, string message)
        { checks++; if (!value) throw new InvalidOperationException("Environment detail: " + message); }

        [MenuItem("Alcatraz/Validate Map Surface Detail (Play Mode)", priority = 33)]
        public static void Run()
        {
            if (!EditorApplication.isPlaying) throw new InvalidOperationException("Enter Play Mode before validating map surfaces. No checks ran.");
            checks = 0;
            var details = UnityEngine.Object.FindFirstObjectByType<AlcatrazEnvironmentDetails>();
            Check(details != null, "the active Alcatraz presentation owns its detail pass");
            var world = UnityEngine.Object.FindFirstObjectByType<SuppliedIslandWorld>();
            if (world == null)
            {
                Check(details.DetailedScanRenderers == 0 && !details.HelipadDetailed,
                    "authored scenes retain their own PBR material and collision layout");
                Debug.Log("Map surface integration: " + checks + " checks passed for authored scene. Supplied-only checks not applicable.");
                return;
            }
            Check(world.Ready, "supplied world completed setup");
            var scan = world.transform.Find("Supplied Island");
            Check(scan != null, "original scan root exists");
            var source = Resources.Load<GameObject>("AlcatrazSupplied/Baked/Island");
            Check(source != null, "original scan prefab remains available");
            var expected = source.GetComponentsInChildren<MeshFilter>(true);
            var actual = scan.GetComponentsInChildren<MeshFilter>(true);
            Check(actual.Length == expected.Length && details.DetailedScanRenderers == actual.Length,
                "all original scan chunks use the detail profile");
            var atlas = source.GetComponentInChildren<MeshRenderer>(true).sharedMaterial.GetTexture("_BaseMap");
            for (int i = 0; i < actual.Length; i++)
            {
                Check(details.OriginalScanMesh(actual[i]) == expected[i].sharedMesh, "scan chunk " + i + " retains its original collision/restore mesh");
                var collider = actual[i].GetComponent<MeshCollider>();
                Check(collider != null && collider.sharedMesh == expected[i].sharedMesh, "scan collision remains unchanged at chunk " + i);
                var material = actual[i].GetComponent<MeshRenderer>().sharedMaterial;
                Check(material.shader.name == "Blackstone/Island Surface Detail" && material.shader.isSupported,
                    "surface shader is supported on the current graphics backend");
                Check(material.GetTexture("_BaseMap") == atlas, "source atlas is preserved at chunk " + i);
                foreach (string property in new[] { "_GroundMap", "_GroundNormal", "_GroundSurface", "_WallMap", "_WallNormal", "_WallSurface" })
                    Check(material.GetTexture(property) != null, property + " is bound");
            }
            var dressing = details.transform.Find("Alcatraz environment detail");
            Check(dressing != null && dressing.GetComponentsInChildren<Collider>(true).Length == 0,
                "paint and ground cover add no collision");
            Check(details.GroundCoverRenderers > 0, "sampled ground-cover chunks are present");
            Check(details.RebuiltScanChunks > 0 && details.FacadeRenderers > 0, "surveyed facade visual replacements are installed");
            Check(details.CourtyardRenderers > 0 && details.VegetationRenderers > 0, "courtyard surfaces and coastal vegetation are installed");
            foreach (var renderer in dressing.GetComponentsInChildren<MeshRenderer>(true))
            {
                var filter = renderer.GetComponent<MeshFilter>();
                Check(filter != null && filter.sharedMesh != null && filter.sharedMesh.vertexCount > 0,
                    renderer.name + " has a usable imported mesh");
                foreach (var material in renderer.sharedMaterials)
                    Check(material != null && material.shader != null && material.shader.isSupported,
                        renderer.name + " has a supported imported material");
            }
            Check(details.HelipadDetailed, "textured helipad and visible markings were created");
            var paint = dressing.Find("Helipad painted perimeter and H");
            Check(paint != null, "helipad paint object exists");
            var normals = paint.GetComponent<MeshFilter>().sharedMesh.normals;
            foreach (var normal in normals) Check(normal.y > .99f, "paint faces upward");
            Check(Physics.Raycast(world.Helipad.position + Vector3.up, Vector3.down, out var floor, 2, 1, QueryTriggerInteraction.Ignore)
                && floor.collider.name == "Helicopter landing deck", "original solid landing deck still supports the helipad");
            Debug.Log("Map surface integration: " + checks + " checks passed. Visual fidelity, shader rendering and performance require review.");
        }
    }
}
#endif
