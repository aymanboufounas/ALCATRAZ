using UnityEngine;
using DesertShift.Player;

namespace Blackstone.Foundation
{
    [DefaultExecutionOrder(50)]
    public sealed class FoundationCamera : MonoBehaviour
    {
        public PlayerMovement player;
        public PlayerInputHandler input;
        public float sensitivity = .09f;
        public bool invertY;
        public Transform FollowOverride;
        public float FollowDistance=3.15f;
        public bool ActivityCamera;
        public Blackstone.Story.PrisonStoryDirector story;
        public Transform characterVisual;
        float yaw, pitch = 12, shoulder = 1, kick;
        Vector3 velocity;
        Camera view;
        bool wasCinematic;
        Renderer[] characterRenderers;
        bool[] originalRenderingOff;
        Vector3 previousPlayer;
        int teleportVersion;
        SphereCollider collisionProbe;
        readonly Collider[] overlaps = new Collider[24];
        const int ObstructionLayers = ~((1 << 8) | (1 << 2) | (1 << 10) | (1 << 11));
        void Start()
        {
            view = GetComponent<Camera>();
            if (player == null) { enabled = false; return; }
            var probe = new GameObject("Camera collision probe");
            probe.hideFlags = HideFlags.HideInHierarchy; probe.layer = 2;
            collisionProbe = probe.AddComponent<SphereCollider>(); collisionProbe.radius = .23f;
            collisionProbe.enabled = false;
            if (characterVisual != null)
            {
                characterRenderers = characterVisual.GetComponentsInChildren<Renderer>(true);
                originalRenderingOff = new bool[characterRenderers.Length];
                for (int i = 0; i < characterRenderers.Length; i++)
                    originalRenderingOff[i] = characterRenderers[i].forceRenderingOff;
            }
            SnapToPlayer();
        }
        public void SnapToPlayer()
        {
            if (player == null) return;
            yaw = player.transform.eulerAngles.y; pitch = 12; velocity = Vector3.zero;
            previousPlayer = player.transform.position;
            teleportVersion = player.TeleportVersion;
            Quaternion facing = Quaternion.Euler(pitch, yaw, 0);
            Vector3 pivot = FollowOverride != null ? FollowOverride.position : player.cameraTarget != null ? player.cameraTarget.position : player.transform.position + Vector3.up * 1.45f;
            pivot = Separate(pivot);
            transform.SetPositionAndRotation(Resolve(pivot, pivot - facing * Vector3.forward * 3.15f), facing);
        }
        void Visibility(bool hidden)
        {
            if (characterRenderers == null) return;
            for (int i = 0; i < characterRenderers.Length; i++)
                if (characterRenderers[i] != null)
                    characterRenderers[i].forceRenderingOff = originalRenderingOff[i] || hidden;
        }
        void OnDisable() { Visibility(false); }
        void OnDestroy() { if (collisionProbe != null) Destroy(collisionProbe.gameObject); }
        public void Recoil(float value) { kick = Mathf.Min(kick + value, 7); }
        void LateUpdate()
        {
            if (player == null || input == null || view == null || ActivityCamera) return;
            if (story != null)
            {
                if (story.Letterbox) { Visibility(false); wasCinematic = true; return; }
                if (wasCinematic) { yaw = player.transform.eulerAngles.y; pitch = 12; velocity = Vector3.zero; wasCinematic = false; }
                if (story.cameraRig != null) { sensitivity = story.cameraRig.sensitivity; invertY = story.cameraRig.invertY; }
            }
            if (player.TeleportVersion != teleportVersion
                || (player.transform.position - previousPlayer).sqrMagnitude > 100) SnapToPlayer();
            previousPlayer = player.transform.position;
            if (Time.deltaTime > 0 && input.CanControl)
            {
                Vector2 look = input.Look;
                yaw += look.x * sensitivity;
                pitch = Mathf.Clamp(pitch + look.y * sensitivity * (invertY ? 1 : -1), -30, 67);
                if (input.ShoulderPressed) shoulder *= -1;
                kick = Mathf.MoveTowards(kick, 0, 8 * Time.deltaTime);
            }
            Quaternion facing = Quaternion.Euler(pitch-kick, yaw, 0);
            Vector3 pivot = FollowOverride != null ? FollowOverride.position : player.cameraTarget != null ? player.cameraTarget.position : player.transform.position + Vector3.up*1.45f;
            pivot = Separate(pivot);
            Vector3 anchor = pivot + facing * new Vector3(.48f*shoulder, .08f, 0);
            anchor = Resolve(pivot, anchor);
            Vector3 desired = anchor - facing * Vector3.forward * (FollowOverride != null ? FollowDistance : input.Aim ? 1.9f : 3.15f);
            Vector3 wanted = Resolve(anchor, desired);
            bool obstructed = (wanted-desired).sqrMagnitude > .0001f;
            float dt = Mathf.Max(.0001f, Time.deltaTime);
            Vector3 smooth = Vector3.SmoothDamp(transform.position, wanted, ref velocity, .07f, 100, dt);
            // Contract immediately at an obstruction, then ease back into open space.
            if (obstructed && (wanted-pivot).sqrMagnitude < (smooth-pivot).sqrMagnitude)
            { smooth = wanted; velocity = Vector3.zero; }
            transform.position = Resolve(pivot, smooth);
            transform.rotation = facing;
            Visibility((transform.position - pivot).sqrMagnitude < .68f * .68f);
            view.fieldOfView = Mathf.Lerp(view.fieldOfView, input.Aim ? 48 : 58, 1-Mathf.Exp(-10*dt));
            view.nearClipPlane = .08f;
        }
        Vector3 Resolve(Vector3 origin, Vector3 target)
        {
            // At an exposed edge there may be no terrain underneath the boom.
            // Keep grounded orbit views above the player's floor even there.
            if (player != null && player.Grounded)
                target.y = Mathf.Max(target.y, player.transform.position.y + .25f);
            Vector3 result = Clear(origin, target, .23f);
            result = Separate(result);
            return Clear(origin, result, .23f);
        }
        Vector3 Separate(Vector3 position)
        {
            if (collisionProbe == null) return position;
            // Sweeps miss colliders already overlapping their starting sphere.
            for (int pass = 0; pass < 4; pass++)
            {
                bool moved = false;
                int count = Physics.OverlapSphereNonAlloc(position, .23f, overlaps,
                    ObstructionLayers, QueryTriggerInteraction.Ignore);
                for (int i = 0; i < count; i++)
                {
                    var other = overlaps[i];
                    if (other == null || other == collisionProbe) continue;
                    if (Physics.ComputePenetration(collisionProbe, position, Quaternion.identity,
                        other, other.transform.position, other.transform.rotation, out var direction, out float depth))
                    { position += direction * (depth + .02f); moved = true; }
                }
                if (!moved) break;
            }
            return position;
        }
        static Vector3 Clear(Vector3 origin, Vector3 target, float radius)
        {
            Vector3 delta = target-origin;
            if (delta.sqrMagnitude < .000001f) return origin;
            if (Physics.SphereCast(origin, radius, delta.normalized, out var hit, delta.magnitude,
                ObstructionLayers, QueryTriggerInteraction.Ignore))
                return origin + delta.normalized * Mathf.Max(0, hit.distance-.04f);
            return target;
        }
    }
}
