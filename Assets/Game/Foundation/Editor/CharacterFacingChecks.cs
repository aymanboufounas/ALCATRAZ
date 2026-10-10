#if UNITY_EDITOR
using System;
using UnityEditor;
using UnityEngine;

namespace Blackstone.Foundation.Editor
{
    public static class CharacterFacingChecks
    {
        [MenuItem("Alcatraz/Validate Character Facing",priority=21)]
        public static void Run()
        {
            FoundationPreparation.Prepare();
            int checks=0;
            foreach(string profile in new[]{"16","07","12","17","20"})
            {
                var prefab=AssetDatabase.LoadAssetAtPath<GameObject>(RocketboxImporter.Characters+"Male_Adult_"+profile+"/Male_Adult_"+profile+".fbx");
                if(prefab==null)throw new InvalidOperationException("Missing imported character "+profile);
                foreach(float yaw in new[]{0f,90f,180f,270f})
                {
                    var actor=new GameObject("Temporary facing check");
                    actor.hideFlags=HideFlags.HideAndDontSave;
                    try
                    {
                        actor.transform.rotation=Quaternion.Euler(0,yaw,0);
                        var visual=new GameObject("Unanimated orientation").transform;
                        visual.SetParent(actor.transform,false);
                        UnityEngine.Object.Instantiate(prefab,visual,false);
                        // Deliberately exercise the opposite-facing import as well.
                        foreach(float importedYaw in new[]{0f,180f})
                        {
                            visual.localRotation=Quaternion.Euler(0,importedYaw,0);
                            FoundationAvatar.AlignForward(visual,actor.transform.forward);
                            if(Vector3.Dot(FoundationAvatar.AnatomicalForward(visual),actor.transform.forward)<.999f)
                                throw new InvalidOperationException("Imported character faces away from movement: "+profile);
                            checks++;
                        }
                    }
                    finally{UnityEngine.Object.DestroyImmediate(actor);}
                }
            }
            Debug.Log("Character facing passed: "+checks+" imported-rig checks. Review walking and running in Play Mode as well.");
        }
    }
}
#endif
