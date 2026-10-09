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
        public Blackstone.Story.PrisonStoryDirector story;
        float yaw, pitch = 12, shoulder = 1, kick;
        Vector3 velocity;
        Camera view;
        bool wasCinematic;
        void Start() { view = GetComponent<Camera>(); yaw = player.transform.eulerAngles.y; }
        public void Recoil(float value) { kick = Mathf.Min(kick + value, 7); }
        void LateUpdate()
        {
            if (player == null || input == null || view == null) return;
            if (story != null)
            {
                if (story.Letterbox) { wasCinematic = true; return; }
                if (wasCinematic) { yaw = player.transform.eulerAngles.y; pitch = 12; velocity = Vector3.zero; wasCinematic = false; }
                if (story.cameraRig != null) { sensitivity = story.cameraRig.sensitivity; invertY = story.cameraRig.invertY; }
            }
            if (Time.deltaTime > 0 && input.CanControl)
            {
                Vector2 look = input.Look;
                yaw += look.x * sensitivity;
                pitch = Mathf.Clamp(pitch + look.y * sensitivity * (invertY ? 1 : -1), -30, 67);
                if (input.ShoulderPressed) shoulder *= -1;
                kick = Mathf.MoveTowards(kick, 0, 8 * Time.deltaTime);
            }
            Quaternion facing = Quaternion.Euler(pitch-kick, yaw, 0);
            Vector3 pivot = player.cameraTarget != null ? player.cameraTarget.position : player.transform.position + Vector3.up*1.45f;
            Vector3 anchor = pivot + facing * new Vector3(.48f*shoulder, .08f, 0);
            anchor = Clear(pivot, anchor, .19f);
            Vector3 wanted = anchor - facing * Vector3.forward * (input.Aim ? 1.9f : 3.15f);
            wanted = Clear(anchor, wanted, .22f);
            float dt = Mathf.Max(.0001f, Time.deltaTime);
            Vector3 smooth = Vector3.SmoothDamp(transform.position, wanted, ref velocity, .07f, 100, dt);
            transform.position = Clear(pivot, smooth, .2f);
            transform.rotation = facing;
            view.fieldOfView = Mathf.Lerp(view.fieldOfView, input.Aim ? 48 : 58, 1-Mathf.Exp(-10*dt));
            view.nearClipPlane = .08f;
        }
        static Vector3 Clear(Vector3 origin, Vector3 target, float radius)
        {
            Vector3 delta = target-origin;
            if (Physics.SphereCast(origin, radius, delta.normalized, out var hit, delta.magnitude, ~(1<<8), QueryTriggerInteraction.Ignore))
                return origin + delta.normalized * Mathf.Max(.08f, hit.distance-.04f);
            return target;
        }
    }
}
