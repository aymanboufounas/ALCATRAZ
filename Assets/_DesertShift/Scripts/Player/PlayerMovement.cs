using UnityEngine;

namespace DesertShift.Player
{
    [RequireComponent(typeof(CharacterController), typeof(PlayerInputHandler))]
    [DefaultExecutionOrder(-100), DisallowMultipleComponent]
    public sealed class PlayerMovement : MonoBehaviour
    {
        [Header("Movement in metres / second")]
        [SerializeField] float walkSpeed = 1.45f;
        [SerializeField] float jogSpeed = 2.15f;
        [SerializeField] float sprintSpeed = 5.5f;
        [SerializeField] float crouchSpeed = 1.15f;
        [SerializeField] float acceleration = 8.5f;
        [SerializeField] float deceleration = 12f;
        [SerializeField] float gravity = -27f;
        [SerializeField] float jumpHeight = 1.05f;
        [SerializeField] float rotationSharpness = 10f;
        [SerializeField] LayerMask groundLayers = ~(1 << 8);
        public Transform cameraTarget;
        public bool Grounded { get; private set; }
        public bool IsCrouching { get; private set; }
        public bool IsAiming => input != null && input.Aim;
        public float Speed => input != null && !input.CanControl ? 0 :
            new Vector3(controller.velocity.x, 0, controller.velocity.z).magnitude;
        public float VerticalSpeed => velocityY;
        public Vector2 LocalMotion { get; private set; }
        public float TurnRate { get; private set; }
        public bool JumpedThisFrame { get; private set; }
        public bool LandedThisFrame { get; private set; }
        CharacterController controller;
        PlayerInputHandler input;
        Vector3 velocity;
        float velocityY, lastGrounded = -10, lastJumpPressed = -10;
        float standingHeight = 1.78f;
        Vector3 start;
        readonly Collider[] overhead = new Collider[12];

        void Awake()
        {
            controller = GetComponent<CharacterController>(); input = GetComponent<PlayerInputHandler>();
            standingHeight = controller.height; start = transform.position;
        }
        void Update()
        {
            if (Time.deltaTime <= 0) return;
            JumpedThisFrame = LandedThisFrame = false;
            if (!input.CanControl) { velocity = Vector3.zero; velocityY = 0; LocalMotion = Vector2.zero; return; }
            bool wasGrounded = Grounded;
            Grounded = controller.isGrounded || (velocityY <= 0 && Physics.SphereCast(
                transform.position + Vector3.up * .26f, .20f, Vector3.down, out _, .31f,
                groundLayers, QueryTriggerInteraction.Ignore));
            LandedThisFrame = Grounded && !wasGrounded && velocityY < -2;
            if (Grounded) lastGrounded = Time.time;
            if (input.JumpPressed) lastJumpPressed = Time.time;
            UpdateCrouch();
            var cam = UnityEngine.Camera.main;
            float yaw = cam != null ? cam.transform.eulerAngles.y : transform.eulerAngles.y;
            Vector2 axis = Vector2.ClampMagnitude(input.Move, 1);
            Quaternion heading = Quaternion.Euler(0, yaw, 0);
            Vector3 wantedDirection = heading * new Vector3(axis.x, 0, axis.y);
            // Free movement follows actual travel; aiming keeps camera-relative strafing.
            float maxSpeed = IsCrouching ? crouchSpeed : input.Aim || input.Walk ? walkSpeed
                : input.Sprint ? sprintSpeed : jogSpeed;
            var targetVelocity = wantedDirection * maxSpeed;
            velocity = Vector3.MoveTowards(velocity, targetVelocity,
                (axis.sqrMagnitude > .001f ? acceleration : deceleration) * Time.deltaTime);
            float oldYaw = transform.eulerAngles.y;
            if (axis.sqrMagnitude > .001f || input.Aim)
            {
                Vector3 travel = velocity.sqrMagnitude > .04f ? velocity : wantedDirection;
                transform.rotation = Quaternion.Slerp(transform.rotation,
                    input.Aim ? heading : Quaternion.LookRotation(travel),
                    1f - Mathf.Exp(-rotationSharpness * Time.deltaTime));
            }
            TurnRate = Mathf.DeltaAngle(oldYaw, transform.eulerAngles.y) / Time.deltaTime;
            if (Grounded && velocityY < 0) velocityY = -3f;
            if (!IsCrouching && Time.time - lastJumpPressed < .12f && Time.time - lastGrounded < .12f)
            {
                velocityY = Mathf.Sqrt(jumpHeight * -2f * gravity); Grounded = false;
                JumpedThisFrame = true; lastJumpPressed = lastGrounded = -10;
            }
            velocityY = Mathf.Max(velocityY + gravity * Time.deltaTime, -45f);
            Vector3 horizontal = velocity;
            if (Grounded && Physics.Raycast(transform.position + Vector3.up * .3f, Vector3.down,
                out RaycastHit slope, .7f, groundLayers, QueryTriggerInteraction.Ignore))
            {
                float angle = Vector3.Angle(slope.normal, Vector3.up);
                if (angle < controller.slopeLimit)
                    horizontal = Vector3.ProjectOnPlane(horizontal, slope.normal);
                else horizontal += Vector3.ProjectOnPlane(Vector3.down, slope.normal) * 4f;
            }
            CollisionFlags flags = controller.Move((horizontal + Vector3.up * velocityY) * Time.deltaTime);
            if ((flags & CollisionFlags.Above) != 0 && velocityY > 0) velocityY = 0;
            var local = transform.InverseTransformDirection(new Vector3(controller.velocity.x, 0, controller.velocity.z));
            LocalMotion = new Vector2(local.x, local.z);
            if (cameraTarget != null)
            {
                var p = cameraTarget.localPosition;
                p.y = Mathf.Lerp(p.y, IsCrouching ? .98f : 1.45f, 1 - Mathf.Exp(-14 * Time.deltaTime));
                cameraTarget.localPosition = p;
            }
            if (transform.position.y < -25) Teleport(start);
        }
        void UpdateCrouch()
        {
            bool shouldCrouch = input.Crouch;
            if (!shouldCrouch && IsCrouching)
            {
                var bottom = transform.position + Vector3.up * (controller.height - .24f);
                var top = transform.position + Vector3.up * (standingHeight - .24f);
                shouldCrouch = Physics.OverlapCapsuleNonAlloc(bottom, top, .23f, overhead,
                    groundLayers, QueryTriggerInteraction.Ignore) > 0;
            }
            IsCrouching = shouldCrouch;
            float height = Mathf.MoveTowards(controller.height, shouldCrouch ? 1.13f : standingHeight, 5f * Time.deltaTime);
            controller.height = height; controller.center = Vector3.up * height * .5f;
            controller.stepOffset = Grounded ? (shouldCrouch ? .18f : .3f) : 0;
        }
        public void Teleport(Vector3 position)
        {
            controller.enabled = false; transform.position = position;
            velocity = Vector3.zero; velocityY = 0; controller.enabled = true;
        }
    }
}
