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
            var supplied=GetComponent<Blackstone.Supplied.SuppliedIslandWorld>();
            if(supplied!=null&&!supplied.Ready){Status=supplied.Status??"Prepare the supplied Alcatraz assets before Play.";return;}
            Player=FindFirstObjectByType<PlayerMovement>();Input=FindFirstObjectByType<PlayerInputHandler>();
            var controller=Resources.Load<RuntimeAnimatorController>("BlackstoneFoundation/Locomotion");
            if(Player==null||Input==null||controller==null)
            {Status="Finish Unity import, then choose Blackstone > Prepare Character Foundation.";Debug.LogError(Status);return;}
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
                if(prefab==null){Status="Missing character: "+profile;Debug.LogError(Status+". Keeping the existing visible character.");continue;}
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
                {Destroy(model.gameObject);Status="Character setup failed: "+profile;Debug.LogError(Status+". "+error.Message+" Existing visuals retained.");continue;}
                // Replace the old visuals only after the new model has been measured and aligned.
                foreach(var oldAnimator in actor.GetComponentsInChildren<Animator>(true))
                    if(!oldAnimator.transform.IsChildOf(model))oldAnimator.enabled=false;
                foreach(var behaviour in actor.GetComponentsInChildren<MonoBehaviour>(true))
                    if(!behaviour.transform.IsChildOf(model)&&(behaviour is PrisonLocomotion||behaviour is Blackstone.Audio.PrisonFootsteps||behaviour is CharacterRig||behaviour is PlayerAnimator||behaviour is SurfaceFootsteps||behaviour.GetType().Name=="DistanceDetail"))behaviour.enabled=false;
                foreach(var lod in actor.GetComponentsInChildren<LODGroup>(true))if(!lod.transform.IsChildOf(model))lod.enabled=false;
                foreach(var renderer in actor.GetComponentsInChildren<Renderer>(true))
                    if(!renderer.transform.IsChildOf(model)&&!StoryProp(renderer.transform,story))renderer.enabled=false;
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
                animator.enabled=true;animator.runtimeAnimatorController=controller;
                var avatar=actor.gameObject.AddComponent<FoundationAvatar>();avatar.model=model;avatar.animator=animator;
                avatar.movement=isPlayer?Player:null;
                avatar.seated=actor.pose==ActorPose.Cards||actor.pose==ActorPose.Read||actor.pose==ActorPose.SeatedTalk;
                avatar.Bind();
                var fall=actor.GetComponent<FoundationFall>();if(fall==null)fall=actor.gameObject.AddComponent<FoundationFall>();fall.avatar=avatar;
                if(isPlayer||(!guard&&!storyMode))actor.gameObject.AddComponent<FoundationBoxing>();
                if(identity!=null){animator.Play(0,0,identity.idlePhase);animator.Update(0);}
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
                if(!isPlayer&&!storyMode)actor.gameObject.AddComponent<FoundationDamageable>();
                if(isPlayer)hero=avatar;
            }
            if(hero==null){Status="The prisoner avatar could not be created.";return;}
            var camera=Camera.main;
            if(camera==null&&story!=null)camera=story.mainCamera;
            if(camera==null)
                foreach(var candidate in FindObjectsByType<Camera>(FindObjectsSortMode.None))
                    if(candidate.enabled&&!candidate.orthographic){camera=candidate;break;}
            if(camera==null){Status="No active gameplay camera. Keeping the existing camera driver.";Debug.LogError(Status);return;}
            camera.tag="MainCamera";camera.enabled=true;camera.cullingMask|=1<<Player.gameObject.layer;
            foreach(var renderer in hero.model.GetComponentsInChildren<Renderer>(true))camera.cullingMask|=1<<renderer.gameObject.layer;
            foreach(var c in FindObjectsByType<DesertShift.Camera.ThirdPersonCameraController>(FindObjectsSortMode.None))c.SetExternalDriver(true);
            if(camera!=null)
            {
                foreach(var b in camera.GetComponents<Behaviour>())if(b.GetType().Name=="CinemachineBrain")b.enabled=false;
                CameraRig=camera.GetComponent<FoundationCamera>();if(CameraRig==null)CameraRig=camera.gameObject.AddComponent<FoundationCamera>();CameraRig.enabled=true;CameraRig.player=Player;CameraRig.input=Input;
                CameraRig.characterVisual=hero.model;
                CameraRig.story=storyMode?story:null;CameraRig.RefreshBindings();
            }
            if(!storyMode)
            {
                if(story!=null)
                {if(story.cellDoor!=null)story.cellDoor.gameObject.SetActive(false);if(story.solitaryDoor!=null)story.solitaryDoor.gameObject.SetActive(false);}
                PlayerEquipment=Player.gameObject.AddComponent<FoundationWeapons>();
                PlayerEquipment.avatar=hero;PlayerEquipment.input=Input;PlayerEquipment.cameraRig=CameraRig;hero.equipment=PlayerEquipment;
                foreach(var door in FindObjectsByType<DoorController>(FindObjectsSortMode.None))door.locked=false;
            }
            Status="Ready";
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
            Bounds bounds=Blackstone.Supplied.SuppliedModel.Bounds(model.gameObject);
            if(bounds.size.y<.1f||float.IsNaN(bounds.size.y)||float.IsInfinity(bounds.size.y))
                throw new System.InvalidOperationException("The imported model has no usable body geometry or has zero scale.");
            model.localScale*=1.78f/bounds.size.y;
            bounds=Blackstone.Supplied.SuppliedModel.Bounds(model.gameObject);
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
