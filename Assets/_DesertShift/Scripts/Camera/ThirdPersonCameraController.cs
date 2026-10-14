using UnityEngine;
using Unity.Cinemachine;
using DesertShift.Player;

namespace DesertShift.Camera
{
    [DefaultExecutionOrder(-50)]
    public sealed class ThirdPersonCameraController : MonoBehaviour
    {
        public Transform followTarget;
        public PlayerInputHandler input;
        public CinemachineCamera virtualCamera;
        [Range(.01f, .35f)] public float sensitivity = .105f;
        public float distance = 3.2f;
        public float minPitch = -32, maxPitch = 68;
        public float initialYaw = 10, initialPitch = 12;
        public bool invertY;
        public bool IsCinematic { get; private set; }
        public bool ExternalDriver { get; private set; }
        public float fieldOfView = 58;
        bool rightShoulder = true;
        CinemachineBrain brain;
        Transform orbit;
        CinemachineThirdPersonFollow body;
        float yaw, pitch;
        void Start()
        {
            if (ExternalDriver)return;
            if (followTarget == null || input == null) { enabled = false; return; }
            orbit = new GameObject("Camera Orbit Target").transform;
            orbit.SetParent(transform, false); orbit.position = followTarget.position;
            yaw = initialYaw; pitch = initialPitch;
            orbit.rotation = Quaternion.Euler(pitch, yaw, 0);
            var main = UnityEngine.Camera.main;
            if (main != null && !main.TryGetComponent<CinemachineBrain>(out _))
                main.gameObject.AddComponent<CinemachineBrain>();
            if (main != null) brain = main.GetComponent<CinemachineBrain>();
            if (virtualCamera == null)
            {
                var go = new GameObject("CM_Exploration"); go.transform.SetParent(transform);
                virtualCamera = go.AddComponent<CinemachineCamera>();
            }
            virtualCamera.Follow = orbit;
            var lens = virtualCamera.Lens; lens.FieldOfView = fieldOfView;
            lens.NearClipPlane = .055f; lens.FarClipPlane = 1500; virtualCamera.Lens = lens;
            body = virtualCamera.GetComponent<CinemachineThirdPersonFollow>();
            if (body == null) body = virtualCamera.gameObject.AddComponent<CinemachineThirdPersonFollow>();
            body.Damping = new Vector3(.13f, .16f, .12f);
            body.ShoulderOffset = new Vector3(.34f, .06f, 0);
            body.VerticalArmLength = .12f; body.CameraSide = 1; body.CameraDistance = distance;
            body.AvoidObstacles = new CinemachineThirdPersonFollow.ObstacleSettings {
                Enabled = true, CollisionFilter = ~(1 << 8), IgnoreTag = "Player",
                CameraRadius = .18f, DampingIntoCollision = 0, DampingFromCollision = .35f
            };
        }
        void Update()
        {
            if (orbit == null || Time.deltaTime <= 0 || IsCinematic) return;
            // Mouse delta is already per-frame: multiplying it by deltaTime is incorrect.
            Vector2 delta = input.Look * sensitivity;
            yaw = Mathf.Repeat(yaw + delta.x, 360f);
            pitch = Mathf.Clamp(pitch + delta.y * (invertY ? 1 : -1), minPitch, maxPitch);
            if (input.ShoulderPressed) rightShoulder = !rightShoulder;
            body.CameraSide = Mathf.Lerp(body.CameraSide, rightShoulder ? 1 : 0, 10 * Time.deltaTime);
            body.CameraDistance = Mathf.Lerp(body.CameraDistance, input.Aim ? 2.15f : distance, 8 * Time.deltaTime);
            var lens = virtualCamera.Lens;
            lens.FieldOfView = Mathf.Lerp(lens.FieldOfView, input.Aim ? fieldOfView - 8 : fieldOfView, 8 * Time.deltaTime);
            virtualCamera.Lens = lens;
            orbit.position = followTarget.position;
            orbit.rotation = Quaternion.Euler(pitch, yaw, 0);
        }
        public void SetExternalDriver(bool active)
        {
            ExternalDriver=active;
            var main=UnityEngine.Camera.main;if(brain==null&&main!=null)brain=main.GetComponent<CinemachineBrain>();
            if(brain!=null)brain.enabled=!active&&!IsCinematic;
            if(virtualCamera!=null)virtualCamera.enabled=!active&&!IsCinematic;
            enabled=!active;
        }
        public void SetCinematic(bool cinematic)
        {
            IsCinematic = cinematic;
            if (brain != null) brain.enabled = !cinematic&&!ExternalDriver;
            if (virtualCamera != null) virtualCamera.enabled = !cinematic&&!ExternalDriver;
        }
        public void SnapBehind(float heading)
        {
            yaw = heading; pitch = initialPitch;
            if (orbit != null)
            { orbit.position = followTarget.position; orbit.rotation = Quaternion.Euler(pitch, yaw, 0); }
        }
        void OnDestroy() { if (orbit != null) Destroy(orbit.gameObject); }
    }
}
