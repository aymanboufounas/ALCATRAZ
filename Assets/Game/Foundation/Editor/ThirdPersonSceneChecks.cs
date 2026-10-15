#if UNITY_EDITOR
using System.Text;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using UnityEngine.SceneManagement;
using DesertShift.Player;

namespace Blackstone.Foundation.Editor
{
    public static class ThirdPersonSceneChecks
    {
        // Checks the actual loaded scene and imported player, rather than a
        // stand-in cube. Used by the automatic post-startup scene audit too.
        public static string[] ValidateCurrentScene()
        {
            var errors=new List<string>();
            var foundation=Object.FindFirstObjectByType<FoundationBootstrap>();
            if(foundation==null)return new[]{"No active FoundationBootstrap in the loaded scene."};
            if(foundation.Status!="Ready")errors.Add("Character foundation is not Ready: "+foundation.Status);
            var rig=foundation.CameraRig;
            bool normalCamera=rig!=null&&!rig.ActivityCamera&&rig.FollowOverride==null&&FoundationVehicle.Active==null
                &&Blackstone.Activities.PrisonPokerTable.Active==null
                &&(foundation.Player==null||foundation.Player.GetComponent<FoundationPlayerVitals>()?.Failed!=true)
                &&(rig.story==null||!rig.story.Letterbox);
            if(normalCamera&&!foundation.ValidatePlayerPresentation(out string presentation))errors.Add(presentation);
            var player=foundation.Player;
            if(player==null)return errors.ToArray();
            var avatar=player.GetComponent<FoundationAvatar>();
            var camera=Camera.main;
            if(camera==null||rig==null||camera!=rig.GetComponent<Camera>())
            {errors.Add("The active MainCamera is not the prepared third-person camera.");return errors.ToArray();}
            if(rig.player!=player||rig.characterVisual!=(avatar!=null?avatar.model:null))
                errors.Add("The third-person driver does not target the prepared prisoner model.");
            foreach(var behaviour in camera.GetComponents<Behaviour>())
                if(behaviour.GetType().Name=="CinemachineBrain"&&behaviour.enabled)
                    errors.Add("A CinemachineBrain competes with the third-person driver.");
            foreach(var legacy in Object.FindObjectsByType<DesertShift.Camera.ThirdPersonCameraController>(FindObjectsSortMode.None))
                if(legacy.enabled&&!legacy.ExternalDriver)
                    errors.Add("A legacy third-person camera driver is still enabled.");
            int listeners=0;
            foreach(var listener in Object.FindObjectsByType<AudioListener>(FindObjectsSortMode.None))
                if(listener.enabled&&listener.gameObject.activeInHierarchy)listeners++;
            if(listeners!=1||camera.GetComponent<AudioListener>()==null||!camera.GetComponent<AudioListener>().enabled)
                errors.Add("The MainCamera must own exactly one active AudioListener.");
            // Vehicle, activity and story cameras deliberately use another frame.
            // Their renderer visibility is controlled by their owning activity.
            if(normalCamera&&avatar!=null&&avatar.model!=null)
            {
                int visible=0;
                foreach(var renderer in avatar.model.GetComponentsInChildren<Renderer>(true))
                    if(renderer.enabled&&!renderer.forceRenderingOff&&renderer.gameObject.activeInHierarchy)
                    {
                        visible++;
                        if((camera.cullingMask&(1<<renderer.gameObject.layer))==0)
                            errors.Add("The MainCamera culls the prisoner renderer "+renderer.name+".");
                    }
                if(visible==0)errors.Add("No prisoner renderer is active in the gameplay view.");
                try
                {
                    Bounds body=FoundationBootstrap.PlayerBodyBounds(avatar.model);
                    if(body.size.y<.5f||float.IsNaN(body.size.y)||float.IsInfinity(body.size.y))
                        errors.Add("The imported prisoner has no usable body geometry.");
                    else if(!GeometryUtility.TestPlanesAABB(GeometryUtility.CalculateFrustumPlanes(camera),body)
                        ||camera.WorldToViewportPoint(body.center).z<=camera.nearClipPlane)
                        errors.Add("The prepared prisoner is outside the gameplay camera view.");
                }
                catch(System.Exception error)
                {errors.Add("Cannot inspect the prepared prisoner geometry: "+error.Message);}
                if(rig.CurrentDistance<.7f)
                    errors.Add("The gameplay camera is too close to the prisoner for a third-person view ("+rig.CurrentDistance.ToString("F2")+" m).");
            }
            return errors.ToArray();
        }

        [MenuItem("Alcatraz/Inspect Player and Camera",priority=22)]
        public static void Run()
        {
            var report=new StringBuilder();report.AppendLine("Scene: "+SceneManager.GetActiveScene().name);
            var player=Object.FindFirstObjectByType<PlayerMovement>();var camera=Camera.main;
            if(player==null)report.AppendLine("ERROR: No active PlayerMovement object.");
            else
            {
                report.AppendLine("Player active: "+player.gameObject.activeInHierarchy+" / scale: "+player.transform.lossyScale);
                var avatar=player.GetComponent<FoundationAvatar>();
                var visual=avatar!=null&&avatar.model!=null?avatar.model:player.transform;
                int visible=0,hidden=0;
                foreach(var renderer in visual.GetComponentsInChildren<Renderer>(true))
                {
                    bool enabled=renderer.enabled&&!renderer.forceRenderingOff&&renderer.gameObject.activeInHierarchy;
                    if(enabled)visible++;else hidden++;
                    if(enabled&&camera!=null&&(camera.cullingMask&(1<<renderer.gameObject.layer))==0)
                        report.AppendLine("ERROR: Camera excludes renderer layer: "+renderer.name);
                }
                report.AppendLine("Player renderers available: "+visible+" / hidden: "+hidden);
                if(visible==0)report.AppendLine("ERROR: No enabled visible player mesh. Inspect model imports and parent activation.");
            }
            if(camera==null)report.AppendLine("ERROR: No enabled camera tagged MainCamera.");
            else
            {
                var rig=camera.GetComponent<FoundationCamera>();
                report.AppendLine("Camera: "+camera.name+" / third-person driver: "+(rig!=null&&rig.enabled));
                if(rig!=null)report.AppendLine("Boom distance: "+rig.CurrentDistance.ToString("F2")+" m / alternate orbit: "+rig.UsingObstructionOrbit);
                foreach(var behaviour in camera.GetComponents<Behaviour>())
                    if(behaviour.GetType().Name=="CinemachineBrain"&&behaviour.enabled&&rig!=null&&rig.enabled)
                        report.AppendLine("ERROR: Two enabled gameplay camera drivers.");
            }
            report.AppendLine("Expected pause UI on this revision: ten sections. An older four-action pause UI indicates older loaded scripts.");
            report.AppendLine("Inspect in Play Mode after character setup to check the imported prisoner.");
            if(EditorApplication.isPlaying)
            {
                var errors=ValidateCurrentScene();
                if(errors.Length==0)report.AppendLine("Loaded player/camera startup checks passed.");
                else foreach(string error in errors)report.AppendLine("ERROR: "+error);
            }
            Debug.Log(report.ToString());EditorUtility.DisplayDialog("Alcatraz player and camera",report.ToString(),"Close");
        }
    }
}
#endif
