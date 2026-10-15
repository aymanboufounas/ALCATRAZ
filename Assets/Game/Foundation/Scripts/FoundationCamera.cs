using UnityEngine;
using UnityEngine.InputSystem;
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
        public string ViewStatus { get; private set; }
        public float ViewStatusUntil { get; private set; }
        bool automaticRestoreAttempted;
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
        void Update()
        {
            // Wait for the title, cinematics and activities to release control.
            // A failed first attempt is reported once; V / R3 can retry later.
            bool requested=Keyboard.current!=null&&Keyboard.current.vKey.wasPressedThisFrame
                ||Gamepad.current!=null&&Gamepad.current.rightStickButton.wasPressedThisFrame;
            if(automaticRestoreAttempted&&!requested)return;
            if(!CanRestorePlayerView(out _))return;
            TryRestorePlayerView(out _);
        }
        bool CanRestorePlayerView(out string message)
        {
            message=null;
            if(player==null||!player.gameObject.activeInHierarchy)
            {message="The active prisoner is unavailable. Check the player diagnostic report.";return false;}
            if(input==null)input=player.GetComponent<PlayerInputHandler>();
            if(input==null||!input.CanControl)
            {message="Resume normal gameplay before resetting the player view.";return false;}
            var fall=player.GetComponent<FoundationFall>();
            var vitals=player.GetComponent<FoundationPlayerVitals>();
            var health=player.GetComponent<FoundationDamageable>();
            if(player.ExternalControl||FoundationVehicle.Active!=null||Blackstone.Activities.PrisonPokerTable.Active!=null
                ||fall!=null&&fall.Recovering||vitals!=null&&vitals.Failed||health!=null&&health.Dead
                ||story!=null&&story.enabled&&(story.MainMenu||story.Busy||story.Letterbox||story.PhoneOpen))
            {message="Leave the activity or cinematic before resetting the player view.";return false;}
            return true;
        }
        bool ViewResult(bool success,string value,out string message)
        {
            ViewStatus=message=value;ViewStatusUntil=Time.unscaledTime+5;
            return success;
        }
        public bool TryRestorePlayerView(out string message)
        {
            if(!CanRestorePlayerView(out string unavailable))return ViewResult(false,unavailable,out message);
            automaticRestoreAttempted=true;
            var avatar=player.GetComponent<FoundationAvatar>();
            var camera=GetComponent<Camera>();
            if(camera==null||!gameObject.activeInHierarchy||avatar==null||avatar.model==null
                ||!avatar.model.IsChildOf(player.transform))
                return ViewResult(false,"The imported prisoner or gameplay camera is unavailable. Check the player diagnostic report.",out message);
            foreach(var other in FindObjectsByType<Camera>(FindObjectsSortMode.None))
                if(other!=camera&&other.enabled&&other.CompareTag("MainCamera"))
                    return ViewResult(false,"Another MainCamera is active. Check the player diagnostic report before resetting it.",out message);
            var body=avatar.model.GetComponentsInChildren<SkinnedMeshRenderer>(true);
            bool geometry=false;
            foreach(var renderer in body)
                if(renderer.sharedMesh!=null&&renderer.sharedMesh.vertexCount>0){geometry=true;break;}
            if(!geometry)return ViewResult(false,"The prisoner has no imported body geometry. Prepare Characters before playing.",out message);
            // Restore the body and its parents, never the disabled legacy model
            // or held props that swimming and story activities hide deliberately.
            foreach(var renderer in body)
            {
                if(renderer.sharedMesh==null||renderer.sharedMesh.vertexCount==0)continue;
                for(var node=renderer.transform;node!=null&&node!=player.transform;node=node.parent)
                    node.gameObject.SetActive(true);
                renderer.enabled=true;renderer.forceRenderingOff=false;renderer.updateWhenOffscreen=true;
                if(renderer.shadowCastingMode==UnityEngine.Rendering.ShadowCastingMode.ShadowsOnly)
                    renderer.shadowCastingMode=UnityEngine.Rendering.ShadowCastingMode.On;
                camera.cullingMask|=1<<renderer.gameObject.layer;
            }
            camera.tag="MainCamera";camera.enabled=true;camera.cullingMask|=1<<player.gameObject.layer;
            foreach(var legacy in FindObjectsByType<DesertShift.Camera.ThirdPersonCameraController>(FindObjectsSortMode.None))
                legacy.SetExternalDriver(true);
            foreach(var behaviour in camera.GetComponents<Behaviour>())
                if(behaviour.GetType().Name=="CinemachineBrain")behaviour.enabled=false;
            // Only reach this point when no vehicle, poker, ragdoll or cinematic
            // owns the view. These overrides can now be cleared as stale state.
            ActivityCamera=false;FollowOverride=null;FollowDistance=3.15f;
            characterVisual=avatar.model;characterRenderers=null;originalRenderingOff=null;
            kick=avoidanceYaw=0;shoulder=1;wasCinematic=false;enabled=true;
            Physics.SyncTransforms();RefreshBindings();
            foreach(var foundation in FindObjectsByType<FoundationBootstrap>(FindObjectsSortMode.None))
                if(foundation.Player==player&&foundation.CameraRig==this&&!foundation.ValidatePlayerPresentation(out string issue))
                    return ViewResult(false,"Camera reset, but player presentation still needs repair: "+issue,out message);
            try
            {
                Bounds bounds=FoundationBootstrap.PlayerBodyBounds(avatar.model);
                if(!Finite(bounds.center)||!Finite(bounds.size)||bounds.size.y<.3f
                    ||Vector3.Distance(bounds.center,player.transform.position+Vector3.up*.9f)>3)
                    return ViewResult(false,"Camera reset, but the prisoner geometry is misplaced or collapsed. Check the player diagnostic report.",out message);
                if(CurrentDistance<.7f||camera.WorldToViewportPoint(bounds.center).z<=camera.nearClipPlane
                    ||!GeometryUtility.TestPlanesAABB(GeometryUtility.CalculateFrustumPlanes(camera),bounds))
                    return ViewResult(false,"Camera reset, but the prisoner is still outside a clear third-person frame. Move into open space and press V / R3.",out message);
            }
            catch(System.Exception error) when(error is System.InvalidOperationException||error is UnityException)
            {return ViewResult(false,"Camera reset, but the prisoner geometry could not be checked. Check the player diagnostic report.",out message);}
            return ViewResult(true,"Third-person view reset. V / R3 resets the view again.",out message);
        }
        static bool Finite(Vector3 value)=>!float.IsNaN(value.x)&&!float.IsInfinity(value.x)
            &&!float.IsNaN(value.y)&&!float.IsInfinity(value.y)&&!float.IsNaN(value.z)&&!float.IsInfinity(value.z);
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
