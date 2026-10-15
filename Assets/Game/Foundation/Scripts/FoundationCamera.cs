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
        float avoidanceYaw;
        public float CurrentDistance { get; private set; }
        public bool UsingObstructionOrbit { get; private set; }
        public bool UsingElevatedOrbit { get; private set; }
        Renderer[] characterRenderers;
        bool[] originalRenderingOff;
        Vector3 previousPlayer;
        int teleportVersion;
        SphereCollider collisionProbe;
        readonly Collider[] overlaps = new Collider[24];
        readonly RaycastHit[] obstructionHits = new RaycastHit[32];
        static readonly float[] ElevatedPitches={35,55,70};
        const int ObstructionLayers = ~((1 << 8) | (1 << 2) | (1 << 10) | (1 << 11));
        void Start(){RefreshBindings();}
        public void RefreshBindings()
        {
            Visibility(false);
            view = GetComponent<Camera>();
            if (player == null) { enabled = false; return; }
            if(collisionProbe==null)
            {
                var probe=new GameObject("Camera collision probe");
                probe.hideFlags=HideFlags.HideInHierarchy;probe.layer=2;
                collisionProbe=probe.AddComponent<SphereCollider>();collisionProbe.radius=.23f;collisionProbe.enabled=false;
            }
            characterRenderers=null;originalRenderingOff=null;
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
            bool aiming=input!=null&&input.Aim&&!player.IsSwimming;
            float distance=FollowOverride!=null?FollowDistance:aiming?1.9f:3.15f;
            Vector3 anchor=Resolve(pivot,pivot+facing*new Vector3(.48f*shoulder,.08f,0));
            Vector3 wanted=Resolve(anchor,anchor-facing*Vector3.forward*distance);
            UsingObstructionOrbit=UsingElevatedOrbit=false;
            if(FollowOverride==null)ChooseVisibleOrbit(pivot,distance,aiming,ref wanted,ref facing);
            CurrentDistance=Vector3.Distance(wanted,pivot);
            Vector3 target=UsingObstructionOrbit?pivot:anchor;
            if((!aiming&&CurrentDistance<2.4f)||UsingElevatedOrbit)target-=Vector3.up*.4f;
            Vector3 direction=target-wanted;
            transform.SetPositionAndRotation(wanted,direction.sqrMagnitude>.00001f?Quaternion.LookRotation(direction,Vector3.up):facing);
            if(view!=null)
            {
                view.fieldOfView=UsingElevatedOrbit?72:CameraFramingRules.FieldOfView(aiming,CurrentDistance);
                view.nearClipPlane=CurrentDistance<.7f?.03f:.08f;
            }
            Visibility(false);
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
            bool aiming=input.Aim&&!player.IsSwimming;
            float distance=FollowOverride!=null?FollowDistance:aiming?1.9f:3.15f;
            Vector3 desired=anchor-facing*Vector3.forward*distance;
            Vector3 wanted = Resolve(anchor, desired);
            bool obstructed=(wanted-desired).sqrMagnitude>.0001f;
            if(FollowOverride==null)ChooseVisibleOrbit(pivot,distance,aiming,ref wanted,ref facing);
            else UsingObstructionOrbit=UsingElevatedOrbit=false;
            float dt = Mathf.Max(.0001f, Time.deltaTime);
            Vector3 smooth = Vector3.SmoothDamp(transform.position, wanted, ref velocity, .07f, 100, dt);
            // Contract immediately at an obstruction, then ease back into open space.
            if (obstructed && (wanted-pivot).sqrMagnitude < (smooth-pivot).sqrMagnitude)
            { smooth = wanted; velocity = Vector3.zero; }
            transform.position=Resolve(pivot,smooth);
            if(UsingObstructionOrbit&&Vector3.Distance(transform.position,pivot)<CameraFramingRules.MinimumDistance(aiming))
            {transform.position=wanted;velocity=Vector3.zero;}
            CurrentDistance=Vector3.Distance(transform.position,pivot);
            Vector3 lookTarget=UsingObstructionOrbit?pivot:anchor;
            if((!aiming&&CurrentDistance<2.4f)||UsingElevatedOrbit)lookTarget-=Vector3.up*.4f;
            Vector3 direction=lookTarget-transform.position;
            transform.rotation=direction.sqrMagnitude>.00001f?Quaternion.LookRotation(direction,Vector3.up):facing;
            // Keep the full prisoner mesh alive even if a narrow space prevents a long boom.
            Visibility(false);
            view.fieldOfView=Mathf.Lerp(view.fieldOfView,UsingElevatedOrbit?72:CameraFramingRules.FieldOfView(aiming,CurrentDistance),1-Mathf.Exp(-10*dt));
            view.nearClipPlane=CurrentDistance < .7f ? .03f : .08f;
        }
        void ChooseVisibleOrbit(Vector3 pivot,float distance,bool aiming,ref Vector3 wanted,ref Quaternion facing)
        {
            UsingObstructionOrbit=UsingElevatedOrbit=false;
            if(Vector3.Distance(pivot,wanted)>=CameraFramingRules.MinimumDistance(aiming)){avoidanceYaw=0;return;}
            float best=float.NegativeInfinity,previous=avoidanceYaw,chosen=avoidanceYaw;Vector3 selected=wanted;Quaternion rotation=facing;
            for(int i=0;i<CameraFramingRules.CandidateCount;i++)
            {
                float offset=CameraFramingRules.Offset(i);
                Quaternion candidateFacing=Quaternion.Euler(pitch-kick,yaw+offset,0);
                Vector3 candidateAnchor=Resolve(pivot,pivot+candidateFacing*new Vector3(.48f*shoulder,.08f,0));
                Vector3 candidate=Resolve(candidateAnchor,candidateAnchor-candidateFacing*Vector3.forward*distance);
                bool clear=(Clear(pivot,candidate,.23f)-candidate).sqrMagnitude<.0001f&&!BlockedAt(candidate,.22f);
                float score=CameraFramingRules.Score(offset,Vector3.Distance(pivot,candidate),clear,aiming);
                // Keep a chosen side stable when two candidates have nearly identical clearance.
                if(Mathf.Abs(Mathf.DeltaAngle(offset,previous))<10)score+=.08f;
                if(score<=best)continue;
                best=score;selected=candidate;rotation=candidateFacing;chosen=offset;
            }
            if(float.IsNegativeInfinity(best))
            {
                // A cell can obstruct every horizontal orbit while leaving room
                // above the prisoner's shoulders. Try a few higher views only
                // after the normal third-person pool has failed completely.
                float requestedPitch=pitch-kick;
                foreach(float raisedPitch in ElevatedPitches)
                {
                    if(raisedPitch<=requestedPitch+1)continue;
                    for(int i=-1;i<CameraFramingRules.CandidateCount;i++)
                    {
                        float offset=i<0?0:CameraFramingRules.Offset(i);
                        Quaternion candidateFacing=Quaternion.Euler(raisedPitch,yaw+offset,0);
                        Vector3 candidateAnchor=Resolve(pivot,pivot+candidateFacing*new Vector3(.15f*shoulder,.08f,0));
                        Vector3 candidate=Resolve(candidateAnchor,candidateAnchor-candidateFacing*Vector3.forward*distance);
                        bool clear=(Clear(pivot,candidate,.23f)-candidate).sqrMagnitude<.0001f&&!BlockedAt(candidate,.22f);
                        float score=CameraFramingRules.ElevatedScore(offset,raisedPitch-requestedPitch,
                            Vector3.Distance(pivot,candidate),clear,aiming);
                        if(Mathf.Abs(Mathf.DeltaAngle(offset,previous))<10)score+=.08f;
                        if(score<=best)continue;
                        best=score;selected=candidate;rotation=candidateFacing;chosen=offset;
                    }
                }
                if(float.IsNegativeInfinity(best))return;
                UsingElevatedOrbit=true;
            }
            wanted=selected;facing=rotation;avoidanceYaw=chosen;UsingObstructionOrbit=true;
        }
        Vector3 Resolve(Vector3 origin, Vector3 target)
        {
            // At an exposed edge there may be no terrain underneath the boom.
            // Keep grounded orbit views above the player's floor even there.
            if (player != null && player.Grounded)
                target.y = Mathf.Max(target.y, player.transform.position.y + .25f);
            if(player!=null&&(player.IsSwimming||FoundationVehicle.Active!=null&&!FoundationVehicle.Active.aircraft))
            {
                var swimming=player.GetComponent<FoundationSwimming>();
                if(swimming!=null)target.y=Mathf.Max(target.y,swimming.WaterLevel+.3f);
            }
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
                var contacts=count==overlaps.Length
                    ?Physics.OverlapSphere(position,.23f,ObstructionLayers,QueryTriggerInteraction.Ignore):overlaps;
                if(count==overlaps.Length)count=contacts.Length;
                for (int i = 0; i < count; i++)
                {
                    var other = contacts[i];
                    if (!BlocksCamera(other)) continue;
                    if (Physics.ComputePenetration(collisionProbe, position, Quaternion.identity,
                        other, other.transform.position, other.transform.rotation, out var direction, out float depth))
                    { position += direction * (depth + .02f); moved = true; }
                }
                if (!moved) break;
            }
            return position;
        }
        bool BlocksCamera(Collider other)
        {
            if(other==null||other==collisionProbe)return false;
            // Imported equipment or a customized model can have child colliders
            // on the default world layer. Their layer must not collapse the boom
            // into the prisoner's head or push the pivot away from their body.
            if(player!=null&&other.transform.IsChildOf(player.transform))return false;
            if(FollowOverride!=null&&other.transform.IsChildOf(FollowOverride))return false;
            return true;
        }
        bool BlockedAt(Vector3 position,float radius)
        {
            int count=Physics.OverlapSphereNonAlloc(position,radius,overlaps,ObstructionLayers,QueryTriggerInteraction.Ignore);
            if(count==overlaps.Length)
            {
                foreach(var other in Physics.OverlapSphere(position,radius,ObstructionLayers,QueryTriggerInteraction.Ignore))
                    if(BlocksCamera(other))return true;
            }
            else for(int i=0;i<count;i++)if(BlocksCamera(overlaps[i]))return true;
            return false;
        }
        Vector3 Clear(Vector3 origin, Vector3 target, float radius)
        {
            Vector3 delta = target-origin;
            if (delta.sqrMagnitude < .000001f) return origin;
            int count=Physics.SphereCastNonAlloc(origin,radius,delta.normalized,obstructionHits,delta.magnitude,
                ObstructionLayers,QueryTriggerInteraction.Ignore);
            float nearest=delta.magnitude;bool found=false;
            var contacts=count==obstructionHits.Length
                ?Physics.SphereCastAll(origin,radius,delta.normalized,delta.magnitude,ObstructionLayers,QueryTriggerInteraction.Ignore)
                :obstructionHits;
            if(count==obstructionHits.Length)count=contacts.Length;
            for(int i=0;i<count;i++)
            {
                var hit=contacts[i];
                if(!BlocksCamera(hit.collider)||hit.distance>nearest)continue;
                nearest=hit.distance;found=true;
            }
            return found?origin+delta.normalized*Mathf.Max(0,nearest-.04f):target;
        }
    }
}
