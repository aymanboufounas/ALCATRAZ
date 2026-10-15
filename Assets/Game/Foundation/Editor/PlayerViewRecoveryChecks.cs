#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.Reflection;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using DesertShift.Player;

namespace Blackstone.Foundation.Editor
{
    // Exercises recovery on the loaded imported prisoner. Every changed scene
    // flag and camera/movement state is restored, even when an assertion fails.
    public static class PlayerViewRecoveryChecks
    {
        static int checks;
        static void Check(bool condition,string label)
        {checks++;if(!condition)throw new InvalidOperationException("Player view recovery: "+label);}

        sealed class PrivateState
        {
            readonly object target;
            readonly Dictionary<FieldInfo,object> values=new Dictionary<FieldInfo,object>();
            public PrivateState(object owner)
            {
                target=owner;
                foreach(var field in owner.GetType().GetFields(BindingFlags.Instance|BindingFlags.NonPublic|BindingFlags.DeclaredOnly))
                {
                    if(field.IsInitOnly)continue;
                    object value=field.GetValue(owner);
                    values[field]=value is Array array?array.Clone():value;
                }
            }
            public void Restore(){foreach(var value in values)value.Key.SetValue(target,value.Value);}
        }
        sealed class TransformState
        {
            readonly Transform node;
            readonly Vector3 position,scale;
            readonly Quaternion rotation;
            readonly bool active;
            public TransformState(Transform value)
            {node=value;position=node.localPosition;rotation=node.localRotation;scale=node.localScale;active=node.gameObject.activeSelf;}
            public void Restore()
            {
                if(node==null)return;
                node.localPosition=position;node.localRotation=rotation;node.localScale=scale;
                node.gameObject.SetActive(active);
            }
        }
        sealed class RendererState
        {
            readonly Renderer renderer;
            readonly bool enabled,hidden,offscreen;
            readonly ShadowCastingMode shadows;
            public RendererState(Renderer value)
            {
                renderer=value;enabled=value.enabled;hidden=value.forceRenderingOff;shadows=value.shadowCastingMode;
                offscreen=value is SkinnedMeshRenderer skin&&skin.updateWhenOffscreen;
            }
            public void Restore()
            {
                if(renderer==null)return;
                renderer.enabled=enabled;renderer.forceRenderingOff=hidden;renderer.shadowCastingMode=shadows;
                if(renderer is SkinnedMeshRenderer skin)skin.updateWhenOffscreen=offscreen;
            }
            public bool Unchanged=>renderer!=null&&renderer.enabled==enabled&&renderer.forceRenderingOff==hidden
                &&renderer.shadowCastingMode==shadows;
        }

        [MenuItem("Alcatraz/Validate Loaded Player View Recovery (Play Mode)",priority=27)]
        public static void Run()
        {
            var foundation=UnityEngine.Object.FindFirstObjectByType<FoundationBootstrap>();
            var player=foundation!=null?foundation.Player:null;
            var rig=foundation!=null?foundation.CameraRig:null;
            var input=foundation!=null?foundation.Input:null;
            var avatar=player!=null?player.GetComponent<FoundationAvatar>():null;
            var fall=player!=null?player.GetComponent<FoundationFall>():null;
            var boxer=player!=null?player.GetComponent<FoundationBoxing>():null;
            var vitals=player!=null?player.GetComponent<FoundationPlayerVitals>():null;
            if(!EditorApplication.isPlaying||Time.deltaTime<=0||foundation==null||foundation.Status!="Ready"
                ||player==null||input==null||!input.CanControl||!player.Grounded||player.ExternalControl||player.IsSwimming
                ||avatar==null||avatar.model==null||avatar.seated||rig==null||rig.ActivityCamera||rig.FollowOverride!=null
                ||FoundationVehicle.Active!=null||Blackstone.Activities.PrisonPokerTable.Active!=null
                ||fall!=null&&fall.Recovering||boxer!=null&&boxer.Sparring||vitals!=null&&vitals.Failed
                ||rig.story!=null&&(rig.story.Busy||rig.story.Letterbox||rig.story.PhoneOpen))
                throw new InvalidOperationException("Resume normal on-foot gameplay with the prepared prisoner before checking view recovery. No tests ran.");
            if(!foundation.ValidatePlayerPresentation(out string initialProblem))
                throw new InvalidOperationException("Begin this recovery fixture from a visible, prepared prisoner: "+initialProblem);
            var camera=rig.GetComponent<Camera>();
            var controller=player.GetComponent<CharacterController>();
            // Held weapons can be children of the imported hand. Recovery owns
            // the skinned body; activity-controlled weapon props stay untouched.
            var bodyRenderers=new List<Renderer>();
            foreach(var skin in avatar.model.GetComponentsInChildren<SkinnedMeshRenderer>(true))
                if(skin.sharedMesh!=null&&skin.sharedMesh.vertexCount>0)bodyRenderers.Add(skin);
            var renderers=bodyRenderers.ToArray();
            var transforms=new List<TransformState>();
            foreach(var node in player.GetComponentsInChildren<Transform>(true))transforms.Add(new TransformState(node));
            var rendererStates=new List<RendererState>();
            foreach(var renderer in renderers)rendererStates.Add(new RendererState(renderer));
            var propStates=new List<RendererState>();
            foreach(var renderer in avatar.model.GetComponentsInChildren<Renderer>(true))
                if(!(renderer is SkinnedMeshRenderer))propStates.Add(new RendererState(renderer));
            var movementState=new PrivateState(player);var orbitState=new PrivateState(rig);
            bool oldExternal=player.ExternalControl,oldController=controller.enabled,oldSeated=avatar.seated;
            bool oldCaptured=input.IsCaptured,oldBlocked=input.GameplayBlocked;
            bool oldPause=input.PauseEnabled,oldResume=input.ResumeOnClick;
            float oldTime=Time.timeScale;CursorLockMode oldLock=Cursor.lockState;bool oldCursor=Cursor.visible;
            Vector3 oldCameraPosition=camera.transform.position;Quaternion oldCameraRotation=camera.transform.rotation;
            int oldMask=camera.cullingMask;bool oldCameraEnabled=camera.enabled,oldRigEnabled=rig.enabled;
            float oldFieldOfView=camera.fieldOfView,oldNearClip=camera.nearClipPlane,oldDistance=rig.FollowDistance;
            string oldTag=camera.tag;
            Transform oldVisual=rig.characterVisual,oldFollow=rig.FollowOverride;
            bool oldActivity=rig.ActivityCamera;PlayerMovement oldPlayer=rig.player;PlayerInputHandler oldInput=rig.input;
            var oldStory=rig.story;
            Vector3 originalPlayerPosition=player.transform.position,originalModelScale=avatar.model.localScale;
            var sentinel=new GameObject("Temporary stale player-view target");sentinel.hideFlags=HideFlags.HideAndDontSave;
            sentinel.transform.position=player.transform.position+Vector3.up*4;
            Transform wrapper=avatar.model;
            while(wrapper.parent!=null&&wrapper.parent!=player.transform)wrapper=wrapper.parent;
            checks=0;
            try
            {
                Check(renderers.Length>0&&avatar.model.gameObject.activeInHierarchy,"fixture uses the actual loaded prisoner renderers");
                var calibration=typeof(FoundationBootstrap).GetMethod("CalibratePlayerBody",BindingFlags.Static|BindingFlags.NonPublic);
                Check(calibration!=null,"startup exposes the imported-body calibration path to this editor fixture");
                var originalModel=new TransformState(avatar.model);
                float originalHeight=FoundationBootstrap.PlayerBodyBounds(avatar.model).size.y;
                avatar.model.position+=new Vector3(8,4,0);
                Check(!foundation.ValidatePlayerPresentation(out string displacedProblem)&&!string.IsNullOrEmpty(displacedProblem),
                    "presentation validation detects an imported body displaced from its controller");
                CalibrateAndCheck(calibration,foundation,avatar.model,originalHeight,"displaced imported body");
                originalModel.Restore();

                avatar.model.localScale*=3;
                Check(!foundation.ValidatePlayerPresentation(out string oversizedProblem)&&!string.IsNullOrEmpty(oversizedProblem),
                    "presentation validation detects an oversized imported body");
                CalibrateAndCheck(calibration,foundation,avatar.model,originalHeight,"oversized imported body");
                originalModel.Restore();

                foreach(var renderer in renderers)renderer.enabled=false;
                bool visibleEquipment=false;
                foreach(var renderer in avatar.model.GetComponentsInChildren<Renderer>(true))
                {
                    var mesh=renderer.GetComponent<MeshFilter>();
                    if(!(renderer is SkinnedMeshRenderer)&&renderer.enabled&&!renderer.forceRenderingOff
                        &&renderer.gameObject.activeInHierarchy&&renderer.shadowCastingMode!=ShadowCastingMode.ShadowsOnly
                        &&mesh!=null&&mesh.sharedMesh!=null&&mesh.sharedMesh.vertexCount>0)visibleEquipment=true;
                }
                Check(!foundation.ValidatePlayerPresentation(out string hiddenBodyProblem)&&!string.IsNullOrEmpty(hiddenBodyProblem),
                    visibleEquipment?"a visible equipped weapon cannot conceal missing prisoner body geometry":"disabled prisoner body geometry is rejected");
                RestoreAndCheck(rig,foundation,renderers,"disabled body renderers");

                wrapper.gameObject.SetActive(false);
                Check(!avatar.model.gameObject.activeInHierarchy,"visual wrapper is deliberately inactive");
                RestoreAndCheck(rig,foundation,renderers,"inactive visual wrapper");
                Check(wrapper.gameObject.activeInHierarchy,"recovery reactivates the real character wrapper");

                int modelLayers=0;
                foreach(var renderer in renderers)modelLayers|=1<<renderer.gameObject.layer;
                camera.cullingMask&=~modelLayers;
                Check((camera.cullingMask&modelLayers)==0,"fixture excludes every real prisoner renderer layer");
                RestoreAndCheck(rig,foundation,renderers,"excluded camera layers");
                Check((camera.cullingMask&modelLayers)==modelLayers,"recovery restores all prisoner renderer layers");

                foreach(var renderer in renderers)
                {renderer.forceRenderingOff=true;renderer.shadowCastingMode=ShadowCastingMode.ShadowsOnly;}
                RestoreAndCheck(rig,foundation,renderers,"forced-hidden and shadow-only body renderers");
                foreach(var renderer in renderers)
                    Check(!renderer.forceRenderingOff&&renderer.shadowCastingMode!=ShadowCastingMode.ShadowsOnly,
                        "recovery restores colour rendering for "+renderer.name);

                rig.ActivityCamera=true;rig.FollowOverride=sentinel.transform;
                RestoreAndCheck(rig,foundation,renderers,"stale activity camera state");
                Check(!rig.ActivityCamera&&rig.FollowOverride==null,"recovery clears an unowned activity camera override");
                Check(player.transform.position==originalPlayerPosition&&avatar.model.localScale==originalModelScale,
                    "view recovery does not move or resize the prisoner");
                foreach(var prop in propStates)Check(prop.Unchanged,"body view recovery preserves weapon and story prop visibility");

                // A legitimate seated/external owner must keep its hidden body
                // and camera target. This does not board a real vehicle or table.
                player.SetExternalControl(true);avatar.seated=true;
                rig.ActivityCamera=true;rig.FollowOverride=sentinel.transform;
                foreach(var renderer in renderers)renderer.enabled=false;
                bool recovered=rig.TryRestorePlayerView(out string activityMessage);
                Check(!recovered&&!string.IsNullOrEmpty(activityMessage),"active external control rejects view recovery with a reason");
                Check(player.ExternalControl&&!controller.enabled&&avatar.seated,
                    "rejected recovery preserves the seated owner's movement control");
                Check(rig.ActivityCamera&&rig.FollowOverride==sentinel.transform,
                    "rejected recovery preserves the activity camera override");
                foreach(var renderer in renderers)Check(!renderer.enabled,"rejected recovery preserves the hidden activity body");
                Debug.Log("Loaded player view recovery passed: "+checks+" assertions using the actual imported prisoner. Live rendering review is still required.");
            }
            finally
            {
                // SetExternalControl resets jump/ground state; restore the saved
                // movement fields after releasing the simulated owner.
                player.SetExternalControl(oldExternal);avatar.seated=oldSeated;
                foreach(var state in transforms)state.Restore();
                foreach(var state in rendererStates)state.Restore();
                foreach(var state in propStates)state.Restore();
                rig.player=oldPlayer;rig.input=oldInput;rig.story=oldStory;rig.characterVisual=oldVisual;
                rig.FollowOverride=oldFollow;rig.ActivityCamera=oldActivity;rig.FollowDistance=oldDistance;
                rig.enabled=oldRigEnabled;
                orbitState.Restore();movementState.Restore();controller.enabled=oldController;
                camera.cullingMask=oldMask;camera.enabled=oldCameraEnabled;camera.fieldOfView=oldFieldOfView;
                camera.nearClipPlane=oldNearClip;camera.tag=oldTag;
                camera.transform.SetPositionAndRotation(oldCameraPosition,oldCameraRotation);
                input.PauseEnabled=oldPause;input.ResumeOnClick=oldResume;input.SetGameplayBlocked(oldBlocked);input.Capture(oldCaptured);
                UnityEngine.Object.DestroyImmediate(sentinel);Physics.SyncTransforms();
                Time.timeScale=oldTime;Cursor.lockState=oldLock;Cursor.visible=oldCursor;
            }
        }
        static void RestoreAndCheck(FoundationCamera rig,FoundationBootstrap foundation,Renderer[] renderers,string scenario)
        {
            Check(rig.TryRestorePlayerView(out string message),scenario+": "+message);
            Check(foundation.ValidatePlayerPresentation(out string issue),scenario+" keeps a renderable prepared player: "+issue);
            foreach(var renderer in renderers)
                Check(renderer.enabled&&!renderer.forceRenderingOff&&renderer.gameObject.activeInHierarchy,
                    scenario+" restores "+renderer.name);
            Bounds body=FoundationBootstrap.PlayerBodyBounds(foundation.Player.GetComponent<FoundationAvatar>().model);
            var camera=rig.GetComponent<Camera>();
            Check(GeometryUtility.TestPlanesAABB(GeometryUtility.CalculateFrustumPlanes(camera),body)
                &&camera.WorldToViewportPoint(body.center).z>camera.nearClipPlane,scenario+" frames the real body in the gameplay view");
        }
        static void CalibrateAndCheck(MethodInfo calibration,FoundationBootstrap foundation,Transform model,float height,string scenario)
        {
            // Exercise the startup method explicitly in this editor fixture.
            // Normal gameplay recovery never resizes or normalizes the body.
            calibration.Invoke(null,new object[]{model,foundation.Player.transform,height});
            Bounds body=FoundationBootstrap.PlayerBodyBounds(model);
            var feet=new Vector3(body.center.x,body.min.y,body.center.z);
            Check(Mathf.Abs(body.size.y-height)<.025f,scenario+" calibration restores the measured body height");
            Check(Vector3.Distance(feet,foundation.Player.transform.position)<.025f,
                scenario+" calibration centers the real body with its feet at the controller");
            Check(foundation.ValidatePlayerPresentation(out string problem),scenario+" calibration restores a valid presentation: "+problem);
        }
    }
}
#endif
