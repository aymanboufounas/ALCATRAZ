#if UNITY_EDITOR
using System;
using UnityEditor;
using UnityEngine;
using Blackstone.Foundation;

namespace Blackstone.Alcatraz.Editor
{
    public static class HudLayoutChecks
    {
        static void Check(bool condition,string message)
        { if(!condition)throw new InvalidOperationException("Alcatraz HUD: "+message); }
        static bool Inside(Rect rect,FoundationViewport viewport)
        {return rect.xMin>=0&&rect.yMin>=0&&rect.xMax<=viewport.Width&&rect.yMax<=viewport.Height;}

        [MenuItem("Alcatraz/Validate HUD Layout",priority=21)]
        public static void Run()
        {
            int[,] sizes={{1280,720},{1308,734},{1920,1080},{2560,1080},{1280,1024},{1024,768},{3440,1440}};
            for(int i=0;i<sizes.GetLength(0);i++)
            {
                var viewport=new FoundationViewport(sizes[i,0],sizes[i,1]);
                Check(Mathf.Abs(viewport.Width*viewport.Scale-sizes[i,0])<.01f,"horizontal coverage");
                Check(Mathf.Abs(viewport.Height*viewport.Scale-sizes[i,1])<.01f,"vertical coverage");
                Check(Inside(viewport.Equipment,viewport),"equipment card inside viewport");
                foreach(bool supplied in new[]{false,true})
                {
                    Rect map=viewport.Map(supplied);
                    Check(Inside(map,viewport)&&!map.Overlaps(viewport.Equipment),"minimap and equipment remain separated");
                    Check(Mathf.Abs(map.width/map.height-(supplied?1.5f:2f/3))<.001f,"map aspect ratio");
                }
                for(int card=0;card<4;card++)
                    Check(Inside(viewport.InventoryCard(card),viewport)
                        &&!viewport.InventoryCard(card).Overlaps(viewport.Equipment),"inventory card bounds");
            }
            var skin=EditorGUIUtility.GetBuiltinSkin(EditorSkin.Game);
            var heading=new GUIStyle(skin.label){fontSize=24,fontStyle=FontStyle.Bold,wordWrap=false};
            Check(heading.CalcSize(new GUIContent("GOAL: ESCAPE THE PRISON")).x<=522,"goal fits its label");
            Check(heading.CalcSize(new GUIContent("ALCATRAZ EXTERIOR")).x<=286,"location fits its label");
            var small=new GUIStyle(skin.label){fontSize=14,wordWrap=false};
            foreach(string detail in new[]{"5.56 mm / Auto","10 mm / Semi-auto","6-round cylinder","Close combat","Reloading..."})
                Check(small.CalcSize(new GUIContent(detail)).x<=154,"weapon detail fits its label");
            Debug.Log("Alcatraz HUD layout checks passed for seven resolutions, including the recording, 4:3 and ultrawide. Live visual review is still required.");
        }
    }
}
#endif
