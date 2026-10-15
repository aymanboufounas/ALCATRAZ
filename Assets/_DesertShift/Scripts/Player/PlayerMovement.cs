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
        public bool IsAiming => !IsSwimming && input != null && input.Aim;
        public bool WantsSprint => input!=null&&input.CanControl&&input.Sprint&&!input.Aim&&!input.Walk
            &&!IsCrouching&&!IsSwimming&&!ExternalControl;
        public bool WantsMove => input!=null&&input.CanControl&&input.Move.sqrMagnitude>.001f&&!ExternalControl&&!IsSwimming;
        // Exploration worlds can protect exposed cliffs without changing story movement.
        public bool GuardUnsafeLedges { get; set; }
        public int TeleportVersion { get; private set; }
        public float Speed => ExternalControl||input!=null&&!input.CanControl?0:
            new Vector3(measuredVelocity.x,0,measuredVelocity.z).magnitude;
        public float SurfaceSpeed => ExternalControl||input!=null&&!input.CanControl?0:surfaceSpeed;
        public float VerticalSpeed => velocityY;
        public bool ExternalControl { get; private set; }
        public bool IsSwimming { get; private set; }
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
        Vector3 measuredVelocity;
        float surfaceSpeed;
        float velocityY, lastGrounded = -10, lastJumpPressed = -10;
        float standingHeight = 1.78f;
        float waterSurface, swimBoostUntil;
        Vector3 start;
        readonly Collider[] overhead = new Collider[12];
        readonly Vector3[] wallNormals=new Vector3[8];
        int wallCount;
        bool collectingWalls;

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
            if (ExternalControl || !controller.enabled)
            {LocalMotion=Vector2.zero;measuredVelocity=Vector3.zero;surfaceSpeed=0;return;}
            if (IsSwimming) { Swim(); return; }
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
            float control=Grounded?1:.25f;
            var response=Blackstone.Foundation.MovementResponseRules.Approach(velocity.x,velocity.z,targetVelocity.x,targetVelocity.z,
                acceleration*control,deceleration*control,Time.deltaTime);
            velocity=new Vector3(response.X,0,response.Z);
            float oldYaw = transform.eulerAngles.y;
            if (input.CanControl && (axis.sqrMagnitude > .001f || input.Aim))
            {
                Vector3 travel = velocity.sqrMagnitude > .04f ? velocity : wantedDirection;
                transform.rotation = Quaternion.Slerp(transform.rotation,
                    input.Aim ? heading : Quaternion.LookRotation(travel),
                    1f - Mathf.Exp(-rotationSharpness * Time.deltaTime));
            }
            TurnRate = Mathf.DeltaAngle(oldYaw, transform.eulerAngles.y) / Time.deltaTime;
            float incomingDownSpeed=Mathf.Max(0,-velocityY);
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
            float impactSpeed = Mathf.Max(incomingDownSpeed,-velocityY);
            Vector3 horizontal = velocity;
            if (Grounded && Physics.Raycast(transform.position + Vector3.up * .3f, Vector3.down,
                out RaycastHit slope, .7f, groundLayers, QueryTriggerInteraction.Ignore))
            {
                float angle = Vector3.Angle(slope.normal, Vector3.up);
                if (angle < controller.slopeLimit)
                    horizontal=SurfaceMotion(horizontal,slope.normal);
                else horizontal += Vector3.ProjectOnPlane(Vector3.down, slope.normal) * 4f;
            }
            if (GuardUnsafeLedges && Grounded && velocityY <= 0)
                horizontal = ProtectLedge(horizontal, Time.deltaTime);
            Vector3 frameStart=transform.position,snapCorrection=Vector3.zero;
            bool maySnap=(wasGrounded||Grounded)&&velocityY<=0&&jumpAt<=0&&!JumpedThisFrame;
            CollisionFlags flags=MoveWithStepSupport((horizontal+Vector3.up*velocityY)*Time.deltaTime,maySnap,out snapCorrection);
            Grounded=velocityY<=0&&(flags&CollisionFlags.Below)!=0;
            if (Grounded)
            {
                if(!wasGrounded && AirTime>.08f)
                { LandedThisFrame=true; LandingSpeed=impactSpeed; LandingRecovery=Mathf.Clamp((impactSpeed-3)/18,.08f,.7f); }
                AirTime=0; velocityY=-3;
                LastSupportedPosition=transform.position;
            }
            else AirTime+=Time.deltaTime;
            if ((flags & CollisionFlags.Above) != 0 && velocityY > 0) velocityY = 0;
            MeasureMotion(frameStart,snapCorrection);
            RejectBlockedMomentum();
            if (cameraTarget != null)
            {
                var p = cameraTarget.localPosition;
                p.y = Mathf.Lerp(p.y, IsCrouching ? .98f : 1.45f, 1 - Mathf.Exp(-14 * Time.deltaTime));
                cameraTarget.localPosition = p;
            }
            if (transform.position.y < -40) Teleport(LastSupportedPosition);
        }
        static Vector3 SurfaceMotion(Vector3 planar,Vector3 normal)
        {
            Vector3 tangent=Vector3.ProjectOnPlane(planar,normal);
            return tangent.sqrMagnitude>.000001f?tangent.normalized*planar.magnitude:Vector3.zero;
        }
        CollisionFlags MoveWithStepSupport(Vector3 motion,bool maySnap,out Vector3 snapCorrection)
        {
            snapCorrection=Vector3.zero;
            CollisionFlags flags;
            wallCount=0;collectingWalls=true;
            try
            {
                flags=controller.Move(motion);
                if(maySnap&&(flags&CollisionFlags.Below)==0)
                {
                    Vector3 beforeSnap=transform.position;
                    flags|=SnapToSupportingStep();
                    snapCorrection=transform.position-beforeSnap;
                }
            }
            finally{collectingWalls=false;}
            return flags;
        }
        CollisionFlags SnapToSupportingStep()
        {
            // Keep ordinary downward stairs grounded. Never bridge a large drop,
            // snap a rising jump, or replace the controller's collision sweep.
            float reach=(IsCrouching?.18f:.3f)+controller.skinWidth+.02f;
            if(!Physics.Raycast(transform.position+Vector3.up*.08f,Vector3.down,out var floor,reach+.08f,
                groundLayers,QueryTriggerInteraction.Ignore)||floor.normal.y<Mathf.Cos(controller.slopeLimit*Mathf.Deg2Rad))return CollisionFlags.None;
            float drop=transform.position.y-floor.point.y;
            if(drop<.001f||drop>reach)return CollisionFlags.None;
            return controller.Move(Vector3.down*(drop+controller.skinWidth+.005f));
        }
        void OnControllerColliderHit(ControllerColliderHit hit)
        {
            if(!collectingWalls||wallCount==wallNormals.Length
                ||hit.normal.y>=Mathf.Cos(controller.slopeLimit*Mathf.Deg2Rad))return;
            Vector3 normal=Vector3.ProjectOnPlane(hit.normal,Vector3.up);
            if(normal.sqrMagnitude>.001f)wallNormals[wallCount++]=normal.normalized;
        }
        void RejectBlockedMomentum()
        {
            Vector3 actual=new Vector3(measuredVelocity.x,0,measuredVelocity.z);
            for(int i=0;i<wallCount;i++)
            {
                Vector3 normal=wallNormals[i];
                // A step riser may be touched during a successful step-up. Only
                // reject its inward momentum when actual progress was blocked.
                if(Grounded&&measuredVelocity.y>.05f&&-Vector3.Dot(actual,normal)>.05f)continue;
                if(Vector3.Dot(actual-velocity,normal)<.05f)continue;
                var accepted=Blackstone.Foundation.MovementResponseRules.RejectIntoWall(velocity.x,velocity.z,normal.x,normal.z);
                velocity=new Vector3(accepted.X,0,accepted.Z);
            }
        }
        void MeasureMotion(Vector3 frameStart,Vector3 snapCorrection)
        {
            measuredVelocity=(transform.position-frameStart)/Time.deltaTime;
            Vector3 planar=new Vector3(measuredVelocity.x,0,measuredVelocity.z);
            Vector3 local=transform.InverseTransformDirection(planar);
            LocalMotion=new Vector2(local.x,local.z);
            surfaceSpeed=planar.magnitude;
            if(Grounded&&Physics.Raycast(transform.position+Vector3.up*.3f,Vector3.down,out var floor,.7f,
                groundLayers,QueryTriggerInteraction.Ignore)&&floor.normal.y>=Mathf.Cos(controller.slopeLimit*Mathf.Deg2Rad))
            {
                // Corrective downward snaps are placement, not locomotion. Do
                // not turn a 20 cm stair drop into a 12 m/s animation sample.
                Vector3 travel=measuredVelocity-snapCorrection/Time.deltaTime;
                surfaceSpeed=Vector3.ProjectOnPlane(travel,floor.normal).magnitude;
            }
        }
        Vector3 ProtectLedge(Vector3 motion, float deltaTime)
        {
            if (motion.sqrMagnitude < .001f) return motion;
            if (SupportedPath(motion, deltaTime)) return motion;
            // Keep movement parallel to a ledge possible instead of stopping diagonal input.
            Vector3 x = new Vector3(motion.x, 0, 0), z = new Vector3(0, 0, motion.z);
            bool safeX = SupportedPath(x, deltaTime), safeZ = SupportedPath(z, deltaTime);
            Vector3 allowed=safeX&&(!safeZ||x.sqrMagnitude>=z.sqrMagnitude)?x:safeZ?z:Vector3.zero;
            // A protected edge is a blocked direction too. Do not retain hidden
            // sprint momentum that delays the player's first step away from it.
            velocity=new Vector3(allowed.x,0,allowed.z);
            return allowed;
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
        // Water keeps the CharacterController active, so the swimmer cannot pass
        // through the coast, piers or boats. Seats and ragdolls still own ExternalControl.
        public void SetSwimming(bool active, float surface)
        {
            waterSurface=surface;
            if(active==IsSwimming)return;
            IsSwimming=active;velocity=measuredVelocity=Vector3.zero;surfaceSpeed=0;velocityY=0;LocalMotion=Vector2.zero;
            lastGrounded=lastJumpPressed=-10;jumpAt=0;swimBoostUntil=0;
            Grounded=JumpedThisFrame=LandedThisFrame=false;
            AirTime=LandingSpeed=LandingRecovery=0;
            if(active)
            {
                IsCrouching=false;controller.height=standingHeight;
                controller.center=Vector3.up*standingHeight*.5f;
            }
        }
        void Swim()
        {
            Grounded=JumpedThisFrame=LandedThisFrame=false;AirTime=LandingSpeed=LandingRecovery=0;
            IsCrouching=false;controller.stepOffset=.3f;
            var cam=UnityEngine.Camera.main;
            float yaw=cam!=null?cam.transform.eulerAngles.y:transform.eulerAngles.y;
            Vector2 axis=Vector2.ClampMagnitude(input.CanControl?input.Move:Vector2.zero,1);
            Vector3 direction=Quaternion.Euler(0,yaw,0)*new Vector3(axis.x,0,axis.y);
            velocity=Vector3.MoveTowards(velocity,direction*(input.Sprint?2.45f:1.6f),6*Time.deltaTime);
            if(!input.CanControl)velocity=Vector3.zero;
            float oldYaw=transform.eulerAngles.y;
            if(direction.sqrMagnitude>.001f)
                transform.rotation=Quaternion.Slerp(transform.rotation,Quaternion.LookRotation(direction),1-Mathf.Exp(-6*Time.deltaTime));
            TurnRate=Mathf.DeltaAngle(oldYaw,transform.eulerAngles.y)/Time.deltaTime;
            // Keep the head above water. A short surface stroke helps step onto
            // shallow banks; it never enables underwater flight or wall climbing.
            if(input.JumpPressed&&Time.time>=swimBoostUntil){velocityY=2.2f;swimBoostUntil=Time.time+.65f;}
            velocityY=Blackstone.Foundation.SwimmingRules.BuoyancyVelocity(velocityY,transform.position.y,waterSurface,Time.deltaTime);
            Vector3 frameStart=transform.position;
            CollisionFlags flags=controller.Move((velocity+Vector3.up*velocityY)*Time.deltaTime);
            if((flags&CollisionFlags.Above)!=0&&velocityY>0)velocityY=0;
            MeasureMotion(frameStart,Vector3.zero);
            if(cameraTarget!=null)
            {
                Vector3 target=cameraTarget.localPosition;target.y=Mathf.Lerp(target.y,1.45f,1-Mathf.Exp(-14*Time.deltaTime));
                cameraTarget.localPosition=target;
            }
        }
        public void SetExternalControl(bool active)
        {
            if(active)SetSwimming(false,waterSurface);
            ExternalControl=active; controller.enabled=!active;
            velocity=measuredVelocity=Vector3.zero;surfaceSpeed=0; velocityY=0; LocalMotion=Vector2.zero; TurnRate=0;
            jumpAt=0; lastGrounded=lastJumpPressed=-10;
            Grounded=JumpedThisFrame=LandedThisFrame=false;
            AirTime=LandingSpeed=LandingRecovery=0;
        }
        public void Teleport(Vector3 position)
        {
            SetSwimming(false,waterSurface);
            controller.enabled = false; transform.position = position;
            velocity=measuredVelocity=Vector3.zero;surfaceSpeed=0; velocityY = 0; LocalMotion = Vector2.zero; TurnRate = 0;
            Grounded = JumpedThisFrame = LandedThisFrame = false;
            lastGrounded = lastJumpPressed = -10;
            controller.enabled = !ExternalControl; AirTime=LandingRecovery=0; jumpAt=0; TeleportVersion++;
        }
    }
}
