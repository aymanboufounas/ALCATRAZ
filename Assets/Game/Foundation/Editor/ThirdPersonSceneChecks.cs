#if UNITY_EDITOR
using System.Text;
using UnityEditor;
using UnityEngine;
using UnityEngine.SceneManagement;
using DesertShift.Player;

namespace Blackstone.Foundation.Editor
{
    public static class ThirdPersonSceneChecks
    {
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
            Debug.Log(report.ToString());EditorUtility.DisplayDialog("Alcatraz player and camera",report.ToString(),"Close");
        }
    }
}
#endif
