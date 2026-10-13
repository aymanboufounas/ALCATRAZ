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
        [SerializeField] float gravity = -19.6f;
        [SerializeField] float jumpHeight = 1.05f;
        [SerializeField] float rotationSharpness = 10f;
        [SerializeField] LayerMask groundLayers = ~(1 << 8);
        public Transform cameraTarget;
        public bool Grounded { get; private set; }
        public bool IsCrouching { get; private set; }
        public bool IsAiming => input != null && input.Aim;
        // Exploration worlds can protect exposed cliffs without changing story movement.
        public bool GuardUnsafeLedges { get; set; }
        public int TeleportVersion { get; private set; }
        public float Speed => ExternalControl ? 0 : input != null && !input.CanControl ? 0 :
            new Vector3(controller.velocity.x, 0, controller.velocity.z).magnitude;
        public float VerticalSpeed => velocityY;
        public bool ExternalControl { get; private set; }
        public float AirTime { get; private set; }
        public float LandingSpeed { get; private set; }
        public float LandingRecovery { get; private set; }
        public float JumpPreparation => jumpAt > 0 ? Mathf.Clamp01((jumpAt-Time.time)/.09f) : 0;
        public Vector3 LastSupportedPosition { get; private set; }
        float jumpAt;
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
            groundLayers &= ~(1 << 10);
            standingHeight = controller.height; start = LastSupportedPosition = transform.position;
        }
        void Update()
        {
            if (Time.deltaTime <= 0) return;
            JumpedThisFrame = LandedThisFrame = false;
            if (ExternalControl || !controller.enabled) { LocalMotion=Vector2.zero; return; }
            if (!input.CanControl)
            {
                velocity = Vector3.zero; jumpAt = 0; lastJumpPressed = -10;
            }
            bool wasGrounded = Grounded;
            Grounded = velocityY <= .1f && (controller.isGrounded || Physics.SphereCast(
                transform.position + Vector3.up * .24f, .18f, Vector3.down, out var support, .12f,
                groundLayers, QueryTriggerInteraction.Ignore) && support.normal.y > .55f);
            LandingRecovery = Mathf.MoveTowards(LandingRecovery, 0, Time.deltaTime);
            if (Grounded) { lastGrounded=Time.time; LastSupportedPosition=transform.position; }
            if (input.JumpPressed) lastJumpPressed = Time.time;
            UpdateCrouch();
            var cam = UnityEngine.Camera.main;
            float yaw = cam != null ? cam.transform.eulerAngles.y : transform.eulerAngles.y;
            Vector2 axis = Vector2.ClampMagnitude(input.CanControl ? input.Move : Vector2.zero, 1);
            Quaternion heading = Quaternion.Euler(0, yaw, 0);
            Vector3 wantedDirection = heading * new Vector3(axis.x, 0, axis.y);
            // Free movement follows actual travel; aiming keeps camera-relative strafing.
            float maxSpeed = IsCrouching ? crouchSpeed : input.Aim || input.Walk ? walkSpeed
                : input.Sprint ? sprintSpeed : jogSpeed;
            var targetVelocity = wantedDirection * maxSpeed * (LandingRecovery > 0 ? .4f : 1) * (jumpAt > 0 ? .65f : 1);
            velocity = Vector3.MoveTowards(velocity, targetVelocity,
                (axis.sqrMagnitude > .001f ? acceleration : deceleration) * (Grounded ? 1 : .25f) * Time.deltaTime);
            float oldYaw = transform.eulerAngles.y;
            if (input.CanControl && (axis.sqrMagnitude > .001f || input.Aim))
            {
                Vector3 travel = velocity.sqrMagnitude > .04f ? velocity : wantedDirection;
                transform.rotation = Quaternion.Slerp(transform.rotation,
                    input.Aim ? heading : Quaternion.LookRotation(travel),
                    1f - Mathf.Exp(-rotationSharpness * Time.deltaTime));
            }
            TurnRate = Mathf.DeltaAngle(oldYaw, transform.eulerAngles.y) / Time.deltaTime;
            if (Grounded && velocityY < 0) velocityY = -3f;
            if (input.CanControl && !IsCrouching && LandingRecovery<=0 && jumpAt<=0 && Time.time-lastJumpPressed<.12f && Time.time-lastGrounded<.12f)
            { jumpAt=Time.time+.09f; lastJumpPressed=-10; }
            if(jumpAt>0 && Time.time>=jumpAt)
            {
                if(Time.time-lastGrounded<.22f) { velocityY=Mathf.Sqrt(jumpHeight*-2f*gravity); Grounded=false; JumpedThisFrame=true; lastGrounded=-10; }
                jumpAt=0;
            }
            float fallingGravity = velocityY < 0 ? gravity*1.25f : gravity;
            velocityY = Mathf.Max(velocityY + fallingGravity * Time.deltaTime, -45f);
            float impactSpeed = -velocityY;
            Vector3 horizontal = velocity;
            if (Grounded && Physics.Raycast(transform.position + Vector3.up * .3f, Vector3.down,
                out RaycastHit slope, .7f, groundLayers, QueryTriggerInteraction.Ignore))
            {
                float angle = Vector3.Angle(slope.normal, Vector3.up);
                if (angle < controller.slopeLimit)
                    horizontal = Vector3.ProjectOnPlane(horizontal, slope.normal);
                else horizontal += Vector3.ProjectOnPlane(Vector3.down, slope.normal) * 4f;
            }
            if (GuardUnsafeLedges && Grounded && velocityY <= 0)
                horizontal = ProtectLedge(horizontal, Time.deltaTime);
            CollisionFlags flags = controller.Move((horizontal + Vector3.up * velocityY) * Time.deltaTime);
            Grounded = velocityY<=0 && (flags & CollisionFlags.Below)!=0;
            if (Grounded)
            {
                if(!wasGrounded && AirTime>.08f)
                { LandedThisFrame=true; LandingSpeed=impactSpeed; LandingRecovery=Mathf.Clamp((impactSpeed-3)/18,.08f,.7f); }
                AirTime=0; velocityY=-3;
            }
            else AirTime+=Time.deltaTime;
            if ((flags & CollisionFlags.Above) != 0 && velocityY > 0) velocityY = 0;
            var local = transform.InverseTransformDirection(new Vector3(controller.velocity.x, 0, controller.velocity.z));
            LocalMotion = new Vector2(local.x, local.z);
            if (cameraTarget != null)
            {
                var p = cameraTarget.localPosition;
                p.y = Mathf.Lerp(p.y, IsCrouching ? .98f : 1.45f, 1 - Mathf.Exp(-14 * Time.deltaTime));
                cameraTarget.localPosition = p;
            }
            if (transform.position.y < -40) Teleport(LastSupportedPosition);
        }
        Vector3 ProtectLedge(Vector3 motion, float deltaTime)
        {
            if (motion.sqrMagnitude < .001f) return motion;
            if (SupportedPath(motion, deltaTime)) return motion;
            // Keep movement parallel to a ledge possible instead of stopping diagonal input.
            Vector3 x = new Vector3(motion.x, 0, 0), z = new Vector3(0, 0, motion.z);
            bool safeX = SupportedPath(x, deltaTime), safeZ = SupportedPath(z, deltaTime);
            if (safeX && (!safeZ || x.sqrMagnitude >= z.sqrMagnitude)) return x;
            return safeZ ? z : Vector3.zero;
        }
        bool SupportedPath(Vector3 motion, float deltaTime)
        {
            Vector3 flat = new Vector3(motion.x, 0, motion.z);
            float length = flat.magnitude;
            if (length < .01f) return false;
            Vector3 direction = flat / length;
            float distance = length * deltaTime + controller.radius + .08f;
            int samples = Mathf.Max(1, Mathf.CeilToInt(distance / .2f));
            for (int i = 1; i <= samples; i++)
            {
                Vector3 point = transform.position + direction * (distance * i / samples);
                if (!Physics.Raycast(point + Vector3.up * .45f, Vector3.down, out var floor,
                    2.45f, groundLayers, QueryTriggerInteraction.Ignore) || floor.normal.y < .35f)
                    return false;
            }
            return true;
        }
        void UpdateCrouch()
        {
            bool shouldCrouch = input.CanControl ? input.Crouch : IsCrouching;
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
        public void SetExternalControl(bool active)
        {
            ExternalControl=active; controller.enabled=!active;
            velocity=Vector3.zero; velocityY=0; LocalMotion=Vector2.zero; TurnRate=0;
            jumpAt=0; lastGrounded=lastJumpPressed=-10;
            Grounded=JumpedThisFrame=LandedThisFrame=false;
            AirTime=LandingSpeed=LandingRecovery=0;
        }
        public void Teleport(Vector3 position)
        {
            controller.enabled = false; transform.position = position;
            velocity = Vector3.zero; velocityY = 0; LocalMotion = Vector2.zero; TurnRate = 0;
            Grounded = JumpedThisFrame = LandedThisFrame = false;
            lastGrounded = lastJumpPressed = -10;
            controller.enabled = !ExternalControl; AirTime=LandingRecovery=0; jumpAt=0; TeleportVersion++;
        }
    }
}
