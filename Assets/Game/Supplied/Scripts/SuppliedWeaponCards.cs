using UnityEngine;
using Blackstone.Foundation;

namespace Blackstone.Supplied
{
    // Labels and ammunition come from the real equipment state, including inactive slots.
    public sealed class SuppliedWeaponCards
    {
        readonly Equipment[] slots={Equipment.Rifle,Equipment.Pistol,Equipment.Revolver,Equipment.Knife};
        readonly string[] names={"SERVICE RIFLE","10MM PISTOL","PBR REVOLVER","COMBAT KNIFE"};
        readonly string[] detail={"5.56 mm / automatic","10 mm / semi-auto","6-round cylinder","Close combat"};
        readonly string[] keys={"4","3","5","2"};
        readonly Texture2D[] icons=new Texture2D[4];
        GUIStyle nameStyle,small;
        public void Draw(FoundationWeapons equipment)
        {
            if(equipment==null)return;
            if(nameStyle==null)
            {
                nameStyle=new GUIStyle(GUI.skin.label){fontSize=19,fontStyle=FontStyle.Bold};small=new GUIStyle(GUI.skin.label){fontSize=15};
                for(int i=0;i<slots.Length;i++)icons[i]=Resources.Load<Texture2D>("AlcatrazSupplied/Icons/"+slots[i]);
            }
            var state=equipment.State;Color before=GUI.color;
            for(int i=0;i<slots.Length;i++)
            {
                bool active=slots[i]==state.Equipped;float y=177+i*127;
                Panel(new Rect(1210,y,364,113),active?new Color(.72f,.55f,.24f,.94f):new Color(.17f,.22f,.24f,.8f));
                Panel(new Rect(1212,y+2,360,109),new Color(.035f,.06f,.07f,.94f));
                GUI.color=active?new Color(.96f,.80f,.44f):new Color(.90f,.93f,.92f);
                GUI.Label(new Rect(1225,y+9,310,27),names[i],nameStyle);
                GUI.Label(new Rect(1535,y+8,27,25),keys[i],small);
                GUI.color=Color.white;
                if(icons[i]!=null)GUI.DrawTexture(new Rect(1222,y+35,179,68),icons[i],ScaleMode.ScaleToFit,true);
                GUI.Label(new Rect(1410,y+38,160,23),detail[i],small);
                string ammo=slots[i]==Equipment.Knife?"READY":state.LoadedFor(slots[i])+" / "+state.ReserveFor(slots[i]);
                GUI.Label(new Rect(1410,y+63,150,29),ammo,nameStyle);
                if(active&&state.Reloading)
                {
                    Panel(new Rect(1225,y+105,335,3),new Color(.22f,.26f,.26f));
                    Panel(new Rect(1225,y+105,335*state.ReloadProgress,3),new Color(.96f,.80f,.44f));
                }
            }
            GUI.color=before;
        }
        static void Panel(Rect rect,Color color)
        {Color before=GUI.color;GUI.color=color;GUI.DrawTexture(rect,Texture2D.whiteTexture);GUI.color=before;}
    }
}
