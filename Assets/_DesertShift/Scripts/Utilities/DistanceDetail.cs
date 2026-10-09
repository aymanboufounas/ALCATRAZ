using UnityEngine;
namespace DesertShift.Core
{
    public sealed class DistanceDetail : MonoBehaviour
    {
        [Tooltip("One shared LODGroup for a compound prop, configured once at runtime.")]
        public float farCullHeight = .012f;
        void Awake()
        {
            if (TryGetComponent<LODGroup>(out _)) return;
            var renderers = GetComponentsInChildren<Renderer>();
            if (renderers.Length == 0) return;
            var group = gameObject.AddComponent<LODGroup>();
            group.SetLODs(new[] { new LOD(farCullHeight, renderers) });
            group.RecalculateBounds();
        }
    }
}
