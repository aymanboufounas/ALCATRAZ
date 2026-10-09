using UnityEngine;
using DesertShift.Environment;
namespace DesertShift.Player
{
    [RequireComponent(typeof(PlayerMovement))]
    public sealed class SurfaceFootsteps : MonoBehaviour
    {
        [Tooltip("Sand, Concrete, Metal, Wood, WetConcrete, Asphalt")]
        public AudioClip[] clips;
        PlayerMovement movement;
        AudioSource source;
        float distance;
        void Awake()
        {
            movement = GetComponent<PlayerMovement>(); source = gameObject.AddComponent<AudioSource>();
            source.spatialBlend = .35f; source.minDistance = 1; source.maxDistance = 12;
        }
        void Update()
        {
            if (!movement.Grounded || movement.Speed < .15f) { distance = .5f; return; }
            distance += movement.Speed * Time.deltaTime;
            float stride = movement.IsCrouching ? .65f : Mathf.Lerp(.95f, 1.5f, movement.Speed / 6.4f);
            if (distance < stride && !movement.LandedThisFrame) return;
            distance = 0; int kind = 0;
            if (Physics.Raycast(transform.position + Vector3.up * .2f, Vector3.down, out var hit,
                .65f, ~(1 << 8), QueryTriggerInteraction.Ignore))
            {
                var tag = hit.collider.GetComponentInParent<SurfaceTag>();
                if (tag != null) kind = (int)tag.surface;
            }
            if (clips == null || kind >= clips.Length || clips[kind] == null) return;
            source.pitch = Random.Range(.92f, 1.08f);
            source.PlayOneShot(clips[kind], movement.IsCrouching ? .16f : .29f);
        }
    }
}
