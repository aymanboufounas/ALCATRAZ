using UnityEngine;
namespace DesertShift.Core
{
    public sealed class CinematicView : MonoBehaviour
    {
        [Range(20, 90)] public float fieldOfView = 58;
        public bool stagePlayer;
        public Vector3 playerPosition;
        public float playerYaw;
        void OnDrawGizmosSelected()
        {
            Gizmos.color = new Color(1f, .7f, .3f);
            var old = Gizmos.matrix; Gizmos.matrix = transform.localToWorldMatrix;
            Gizmos.DrawFrustum(Vector3.zero, fieldOfView, 5f, .2f, 16f / 9f); Gizmos.matrix = old;
        }
    }
}
