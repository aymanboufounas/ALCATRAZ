using UnityEngine;
using Blackstone.Actors;
using Blackstone.Story;
using DesertShift.Player;
using DesertShift.Interaction;

namespace Blackstone.Foundation
{
    [DefaultExecutionOrder(-400)]
    public sealed class FoundationBootstrap : MonoBehaviour
    {
        public bool storyMode;
        public string Status { get; private set; }
        public FoundationWeapons PlayerEquipment { get; private set; }
        public FoundationCamera CameraRig { get; private set; }
        public PlayerInputHandler Input { get; private set; }
        public PlayerMovement Player { get; private set; }
        // Finish the original scene's Awake callbacks before replacing its skeletons.
        // Disabling a behaviour does not suppress Awake on an active GameObject.
        void Start()
        {
            FoundationGraphics.Ensure(gameObject);
            Status="Preparing characters…";
            var supplied=GetComponent<Blackstone.Supplied.SuppliedIslandWorld>();
            if(supplied!=null&&!supplied.Ready){Status=supplied.Status??"Prepare the supplied Alcatraz assets before Play.";return;}
            Player=FindFirstObjectByType<PlayerMovement>();Input=FindFirstObjectByType<PlayerInputHandler>();
            var controller=Resources.Load<RuntimeAnimatorController>("BlackstoneFoundation/Locomotion");
            if(Player==null||Input==null)
            {Status="The scene needs an active prisoner and player input.";Debug.LogError(Status);return;}
            // A missing generated controller must not leave a moving invisible player
            // and an unowned camera. Keep the imported body and third-person preview
            // visible, and refuse gameplay until the animation setup is repaired.
            string setupFailure=controller==null
                ?"Character animation is unavailable. In Unity choose Alcatraz > Prepare Characters, then restart Play."
                :null;
            var story=FindFirstObjectByType<PrisonStoryDirector>();
            var roster=FindFirstObjectByType<Blackstone.Alcatraz.AlcatrazMap>()!=null
                ?Blackstone.Alcatraz.AlcatrazCharacterRoster.Load():null;
            var sound=gameObject.AddComponent<FoundationAudio>();sound.followStoryMixer=storyMode;
            if(!storyMode&&story!=null)story.enabled=false;
            FoundationAvatar hero=null;
            foreach(var actor in FindObjectsByType<PrisonActor>(FindObjectsSortMode.None))
            {
                bool isPlayer=actor.transform==Player.transform||actor.transform.IsChildOf(Player.transform);
                Transform parent=isPlayer&&story!=null&&story.playerVisual!=null?story.playerVisual:actor.transform;
                bool guard=actor.displayName!=null&&actor.displayName.StartsWith("Officer");
                string name=actor.displayName??"";
                bool black=name.StartsWith("Malik")||name=="Andre"||name=="Moses"||name=="Jamal";
                string profile=isPlayer?"Male_Adult_16":guard||name.StartsWith("Niko")?"Male_Adult_07":black?"Male_Adult_12":name.StartsWith("Samir")||name=="Yusef"?"Male_Adult_17":"Male_Adult_20";
                var identity=roster!=null?roster.Find(name):null;
                if(identity!=null&&!string.IsNullOrEmpty(identity.model))profile=identity.model;
                var prefab=Resources.Load<GameObject>("BlackstoneFoundation/Characters/"+profile+"/"+profile);
                if(prefab==null){setupFailure=setupFailure??"Missing character: "+profile;Debug.LogError("Missing character: "+profile+". Keeping the existing visible character.");continue;}
                // Keep the orientation correction outside the animated FBX root.
                // FBX axis conversion can leave the visible character facing -Z.
                Transform model=new GameObject("Imported "+actor.displayName).transform;
                model.SetParent(parent,false);
                Transform rig=Instantiate(prefab,model,false).transform;
                try
                {
                    if(isPlayer&&parent!=actor.transform)
                    {parent.gameObject.SetActive(true);if(ZeroScale(parent.localScale))parent.localScale=Vector3.one;}
                    foreach(var renderer in model.GetComponentsInChildren<Renderer>(true))
                    {
                        for(var node=renderer.transform;node!=null&&node!=model.parent;node=node.parent)node.gameObject.SetActive(true);
                        renderer.enabled=true;renderer.forceRenderingOff=false;
                        if(renderer is SkinnedMeshRenderer skin&&isPlayer)skin.updateWhenOffscreen=true;
                    }
                    Normalize(model);
                    FoundationAvatar.AlignForward(model,actor.transform.forward);
                }
                catch(System.Exception error) when(error is System.InvalidOperationException||error is UnityException)
                {Destroy(model.gameObject);setupFailure=setupFailure??"Character setup failed: "+profile;Debug.LogError("Character setup failed: "+profile+". "+error.Message+" Existing visuals retained.");continue;}
                if(identity!=null)
                {
                    float height=Mathf.Clamp(identity.height,1.55f,2.05f)/1.78f;
                    float build=Mathf.Clamp(identity.build,.85f,1.25f);
                    model.localScale=Vector3.Scale(model.localScale,new Vector3(height*build,height,height*build));
                    actor.walkingSpeed=identity.walkSpeed;
                }
                else
                {
                    if(actor.displayName=="Benny"||actor.displayName=="Owen"||actor.displayName=="Peter")model.localScale=Vector3.Scale(model.localScale,new Vector3(1.18f,1,1.18f));
                    if(actor.displayName=="Luis"||actor.displayName=="Eddie")model.localScale=Vector3.Scale(model.localScale,new Vector3(.94f,1,.94f));
                }
                if(guard)GuardMaterial(model,profile,name=="Officer Harrow");
                if(isPlayer)PrisonerMaterial(model,profile);
                var animator=rig.GetComponent<Animator>();if(animator==null)animator=rig.gameObject.AddComponent<Animator>();
                animator.runtimeAnimatorController=controller;animator.enabled=controller!=null;
                var avatar=actor.gameObject.AddComponent<FoundationAvatar>();avatar.model=model;avatar.animator=animator;
                avatar.movement=isPlayer?Player:null;
                avatar.seated=actor.pose==ActorPose.Cards||actor.pose==ActorPose.Read||actor.pose==ActorPose.SeatedTalk;
                try
                {
                    avatar.Bind();
                    if(identity!=null&&controller!=null){animator.Play(0,0,identity.idlePhase);animator.Update(0);}
                    if(isPlayer)
                    {
                        if(!HasDrawableGeometry(model))throw new System.InvalidOperationException("The imported prisoner has no drawable body mesh.");
                        // Measure after Rebind and the first animation evaluation.
                        // Keep this correction on the unanimated wrapper so an
                        // imported root transform cannot reset it on the next frame.
                        CalibratePlayerBody(model,Player.transform,identity!=null?Mathf.Clamp(identity.height,1.55f,2.05f):1.78f);
                        avatar.CalibrateFootClearance();
                    }
                }
                catch(System.Exception error) when(error is System.InvalidOperationException||error is UnityException)
                {
                    avatar.enabled=false;Destroy(avatar);Destroy(model.gameObject);
                    setupFailure=setupFailure??"Character setup failed: "+profile;
                    Debug.LogError("Character setup failed: "+profile+". "+error.Message+" Existing visuals retained.");continue;
                }
                // Retain the original body until the new animated geometry has
                // passed its startup measurements and player calibration.
                foreach(var oldAnimator in actor.GetComponentsInChildren<Animator>(true))
                    if(!oldAnimator.transform.IsChildOf(model))oldAnimator.enabled=false;
                foreach(var behaviour in actor.GetComponentsInChildren<MonoBehaviour>(true))
                    if(!behaviour.transform.IsChildOf(model)&&(behaviour is PrisonLocomotion||behaviour is Blackstone.Audio.PrisonFootsteps||behaviour is CharacterRig||behaviour is PlayerAnimator||behaviour is SurfaceFootsteps||behaviour.GetType().Name=="DistanceDetail"))behaviour.enabled=false;
                foreach(var lod in actor.GetComponentsInChildren<LODGroup>(true))if(!lod.transform.IsChildOf(model))lod.enabled=false;
                foreach(var renderer in actor.GetComponentsInChildren<Renderer>(true))
                    if(!renderer.transform.IsChildOf(model)&&!StoryProp(renderer.transform,story))renderer.enabled=false;
                var fall=actor.GetComponent<FoundationFall>();if(fall==null)fall=actor.gameObject.AddComponent<FoundationFall>();fall.avatar=avatar;
                if(isPlayer||(!guard&&!storyMode))actor.gameObject.AddComponent<FoundationBoxing>();
                var feet=actor.gameObject.AddComponent<FoundationFootsteps>();feet.avatar=avatar;
                var pose=actor.gameObject.AddComponent<FoundationActorPose>();pose.body=avatar;pose.actor=actor;
                bool ambient=identity!=null&&identity.ambient;
                if(storyMode&&!ambient)
                {
                    avatar.storyActor=actor;actor.driveLocomotion=false;actor.animator=animator;
                    // Native-rig gesture axes differ; the foundation overlay now owns gestures.
                    actor.head=actor.jaw=actor.chest=actor.rightArm=actor.rightForearm=actor.leftArm=actor.leftForearm=null;
                    if(isPlayer&&story!=null&&story.tattooMark!=null)pose.gangMark=story.tattooMark.transform;
                    if(isPlayer&&story!=null){pose.phone=story.phoneProp!=null?story.phoneProp.transform:null;pose.concealedKnife=story.concealKnifeProp!=null?story.concealKnifeProp.transform:null;}
                    if(story!=null&&actor==story.niko){story.nikoHand=avatar.rightHand;pose.heldKnife=story.nikoHeldKnife!=null?story.nikoHeldKnife.transform:null;}
                }
                else
                {
                    actor.enabled=false;
                    if(actor.patrolEnabled&&actor.patrol!=null&&actor.patrol.Length>0)
                    {var agent=actor.gameObject.AddComponent<FoundationAgent>();agent.route=actor.patrol;agent.avatar=avatar;agent.player=Player.transform;agent.speed=actor.walkingSpeed;}
                }
                if(isPlayer||!storyMode)actor.gameObject.AddComponent<FoundationDamageable>();
                if(isPlayer)hero=avatar;
            }
            if(hero==null)setupFailure=setupFailure??"The prisoner avatar could not be created. Prepare Characters before playing.";
            var camera=Camera.main;
            if(camera==null&&story!=null)camera=story.mainCamera;
            if(camera==null)
                foreach(var candidate in FindObjectsByType<Camera>(FindObjectsSortMode.None))
                    if(candidate.enabled&&!candidate.orthographic){camera=candidate;break;}
            if(camera==null){Status="No active gameplay camera. Keeping the existing camera driver.";Debug.LogError(Status);return;}
            camera.tag="MainCamera";camera.enabled=true;camera.cullingMask|=1<<Player.gameObject.layer;
            Transform playerVisual=hero!=null?hero.model:Player.transform;
            foreach(var renderer in playerVisual.GetComponentsInChildren<Renderer>(true))camera.cullingMask|=1<<renderer.gameObject.layer;
            foreach(var c in FindObjectsByType<DesertShift.Camera.ThirdPersonCameraController>(FindObjectsSortMode.None))c.SetExternalDriver(true);
            if(camera!=null)
            {
                foreach(var b in camera.GetComponents<Behaviour>())if(b.GetType().Name=="CinemachineBrain")b.enabled=false;
                CameraRig=camera.GetComponent<FoundationCamera>();if(CameraRig==null)CameraRig=camera.gameObject.AddComponent<FoundationCamera>();CameraRig.enabled=true;CameraRig.player=Player;CameraRig.input=Input;
                CameraRig.characterVisual=playerVisual;
                CameraRig.story=storyMode?story:null;CameraRig.RefreshBindings();
            }
            if(!storyMode&&hero!=null)
            {
                if(story!=null)
                {if(story.cellDoor!=null)story.cellDoor.gameObject.SetActive(false);if(story.solitaryDoor!=null)story.solitaryDoor.gameObject.SetActive(false);}
                PlayerEquipment=Player.gameObject.AddComponent<FoundationWeapons>();
                PlayerEquipment.avatar=hero;PlayerEquipment.input=Input;PlayerEquipment.cameraRig=CameraRig;hero.equipment=PlayerEquipment;
                foreach(var door in FindObjectsByType<DoorController>(FindObjectsSortMode.None))door.locked=false;
            }
            Player.gameObject.AddComponent<FoundationSwimming>();
            var vitals=Player.gameObject.AddComponent<FoundationPlayerVitals>();
            vitals.Configure(this,storyMode?story:null);
            if(setupFailure==null&&!ValidatePlayerPresentation(out var issue))setupFailure=issue;
            Status=setupFailure??"Ready";
            if(setupFailure!=null)
            {
                Input.SetGameplayBlocked(true);Input.PauseEnabled=false;
                Debug.LogError("Alcatraz cannot start gameplay: "+Status);
            }
        }
        public bool ValidatePlayerPresentation(out string issue)
        {
            issue=null;
            var avatar=Player!=null?Player.GetComponent<FoundationAvatar>():null;
            if(avatar==null||avatar.model==null||!avatar.model.gameObject.activeInHierarchy)
            {issue="The prisoner has no active character model. Prepare Characters before playing.";return false;}
            if(CameraRig==null||!CameraRig.isActiveAndEnabled||CameraRig.player!=Player)
            {issue="The third-person camera is not following the prisoner.";return false;}
            var camera=CameraRig.GetComponent<Camera>();
            if(camera==null||!camera.enabled||Camera.main!=camera)
            {issue="The active main camera is not the prisoner's third-person camera.";return false;}
            foreach(var behaviour in camera.GetComponents<Behaviour>())
                if(behaviour.GetType().Name=="CinemachineBrain"&&behaviour.enabled)
                {issue="Another camera driver is overriding the third-person camera.";return false;}
            if(!HasDrawableGeometry(avatar.model,camera))
            {issue="The prisoner mesh cannot be rendered by the gameplay camera.";return false;}
            try
            {
                Bounds body=PlayerBodyBounds(avatar.model);
                // These limits allow animated crouching and swimming. They catch
                // a tiny/oversized import or a body left away from its controller.
                if(body.size.y<.35f||body.size.y>2.75f||body.size.x>3.5f||body.size.z>3.5f)
                {issue="The prisoner's animated body has an invalid size: "+body.size;return false;}
                Vector3 offset=body.center-Player.transform.position;
                if(new Vector2(offset.x,offset.z).magnitude>1.5f||Mathf.Abs(offset.y)>2.5f)
                {issue="The prisoner body is displaced from its movement controller: "+offset;return false;}
            }
            catch(System.Exception error) when(error is System.InvalidOperationException||error is UnityException)
            {issue="The prisoner body cannot be measured: "+error.Message;return false;}
            return true;
        }
        static bool HasDrawableGeometry(Transform model,Camera camera=null)
        {
            foreach(var skin in model.GetComponentsInChildren<SkinnedMeshRenderer>(true))
            {
                if(DrawableSkin(skin)
                    &&(camera==null||camera.enabled&&(camera.cullingMask&(1<<skin.gameObject.layer))!=0))return true;
            }
            return false;
        }
        static bool DrawableSkin(SkinnedMeshRenderer skin)=>skin.sharedMesh!=null&&skin.sharedMesh.vertexCount>0
            &&skin.enabled&&!skin.forceRenderingOff&&skin.gameObject.activeInHierarchy
            &&skin.shadowCastingMode!=UnityEngine.Rendering.ShadowCastingMode.ShadowsOnly;
        static bool Finite(Vector3 point)=>!float.IsNaN(point.x)&&!float.IsNaN(point.y)&&!float.IsNaN(point.z)
            &&!float.IsInfinity(point.x)&&!float.IsInfinity(point.y)&&!float.IsInfinity(point.z);
        public static Bounds PlayerBodyBounds(Transform model)
        {
            // The imported character is skinned. Held guns and other MeshRenderer
            // props must not make a hidden body pass validation or change its fit.
            Bounds bounds=new Bounds();bool found=false;
            foreach(var skin in model.GetComponentsInChildren<SkinnedMeshRenderer>(true))
            {
                if(!DrawableSkin(skin))continue;
                var baked=new Mesh();
                try
                {
                    skin.BakeMesh(baked);
                    foreach(var vertex in baked.vertices)
                    {
                        Vector3 point=skin.transform.TransformPoint(vertex);
                        if(!Finite(point))throw new System.InvalidOperationException("The imported body contains a nonfinite vertex.");
                        if(!found){bounds=new Bounds(point,Vector3.zero);found=true;}
                        else bounds.Encapsulate(point);
                    }
                }
                finally
                {if(Application.isPlaying)Destroy(baked);else DestroyImmediate(baked);}
            }
            if(!found)throw new System.InvalidOperationException("The imported prisoner has no drawable skinned body geometry.");
            if(!Finite(bounds.center)||!Finite(bounds.extents)||bounds.size.x<.0001f||bounds.size.y<.0001f||bounds.size.z<.0001f)
                throw new System.InvalidOperationException("The imported model has no finite, usable body geometry.");
            return bounds;
        }
        static void CalibratePlayerBody(Transform model,Transform controller,float expectedHeight)
        {
            Bounds bounds=PlayerBodyBounds(model);
            model.localScale*=expectedHeight/bounds.size.y;
            bounds=PlayerBodyBounds(model);
            model.position+=controller.position-new Vector3(bounds.center.x,bounds.min.y,bounds.center.z);
            bounds=PlayerBodyBounds(model);
            Vector3 feet=new Vector3(bounds.center.x,bounds.min.y,bounds.center.z);
            if(Mathf.Abs(bounds.size.y-expectedHeight)>.025f||Vector3.Distance(feet,controller.position)>.025f)
                throw new System.InvalidOperationException("The animated prisoner could not be fitted to its movement controller.");
        }
        static bool StoryProp(Transform candidate,PrisonStoryDirector story)
        {
            if(story==null)return false;
            foreach(var prop in new[]{story.tattooMark,story.nikoHeldKnife,story.concealKnifeProp,story.phoneProp})
                if(prop!=null&&(candidate==prop.transform||candidate.IsChildOf(prop.transform)))return true;
            return false;
        }
        static bool ZeroScale(Vector3 scale)=>Mathf.Abs(scale.x)<.0001f||Mathf.Abs(scale.y)<.0001f||Mathf.Abs(scale.z)<.0001f;
        static void Normalize(Transform model)
        {
            // Imported skinned culling boxes can be much larger than the actual body.
            Bounds bounds=PlayerBodyBounds(model);
            if(bounds.size.y<.1f||float.IsNaN(bounds.size.y)||float.IsInfinity(bounds.size.y))
                throw new System.InvalidOperationException("The imported model has no usable body geometry or has zero scale.");
            model.localScale*=1.78f/bounds.size.y;
            bounds=PlayerBodyBounds(model);
            model.position+=Vector3.up*(model.parent.position.y-bounds.min.y);
        }
        static void GuardMaterial(Transform model,string profile,bool harrow)
        {
            string style=harrow?"m013_body_harrow08":"m013_body_guard";
            var blue=Resources.Load<Material>("BlackstoneFoundation/Characters/"+profile+"/"+style);if(blue==null)return;
            var head=harrow?Resources.Load<Material>("BlackstoneFoundation/Characters/"+profile+"/m013_head_harrow08"):null;
            foreach(var renderer in model.GetComponentsInChildren<SkinnedMeshRenderer>(true))
            {
                var mats=renderer.sharedMaterials;
                for(int i=0;i<mats.Length;i++)
                {
                    if(mats[i]==null)continue;
                    if(mats[i].name.Contains("_body"))mats[i]=blue;
                    else if(head!=null&&mats[i].name.Contains("_head"))mats[i]=head;
                }
                renderer.sharedMaterials=mats;
            }
        }
        static void PrisonerMaterial(Transform model,string profile)
        {
            if(profile!="Male_Adult_16")return;
            string path="BlackstoneFoundation/Characters/"+profile+"/";
            var head=Resources.Load<Material>(path+"m019_head_elias08");
            var body=Resources.Load<Material>(path+"m019_body_elias08");
            foreach(var renderer in model.GetComponentsInChildren<SkinnedMeshRenderer>(true))
            {
                var materials=renderer.sharedMaterials;
                for(int i=0;i<materials.Length;i++)
                {
                    if(materials[i]==null)continue;
                    if(head!=null&&materials[i].name.Contains("_head"))materials[i]=head;
                    else if(body!=null&&materials[i].name.Contains("_body"))materials[i]=body;
                }
                renderer.sharedMaterials=materials;
            }
        }
    }
}
