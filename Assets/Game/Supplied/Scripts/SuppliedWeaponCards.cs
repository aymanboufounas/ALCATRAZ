using UnityEngine;
using Blackstone.Foundation;

namespace Blackstone.Supplied
{
    public sealed class SuppliedWeaponCards
    {
        readonly Equipment[] slots={Equipment.Rifle,Equipment.Pistol,Equipment.Revolver,Equipment.Knife};
        readonly string[] names={"SERVICE RIFLE","10MM PISTOL","PBR REVOLVER","COMBAT KNIFE"};
        readonly string[] detail={"5.56 mm / Auto","10 mm / Semi-auto","6-round cylinder","Close combat"};
        readonly string[] keys={"4","3","5","2"};
        readonly Texture2D[] icons=new Texture2D[4];
        GUIStyle nameStyle,small;
        void Styles()
        {
            if(nameStyle!=null)return;
            nameStyle=new GUIStyle(GUI.skin.label){fontSize=19,fontStyle=FontStyle.Bold,wordWrap=false};
            small=new GUIStyle(GUI.skin.label){fontSize=14,wordWrap=false};
            nameStyle.normal.textColor=small.normal.textColor=Color.white;
            for(int i=0;i<slots.Length;i++)icons[i]=Resources.Load<Texture2D>("AlcatrazSupplied/Icons/"+slots[i]);
        }
        public void DrawInventory(FoundationWeapons equipment,FoundationViewport viewport)
        {
            if(equipment==null)return;Styles();
            for(int i=0;i<slots.Length;i++)DrawCard(equipment,viewport.InventoryCard(i),i);
        }
        public void DrawEquipped(FoundationWeapons equipment,Rect bounds)
        {
            if(equipment==null)return;Styles();
            int slot=System.Array.IndexOf(slots,equipment.State.Equipped);
            if(slot>=0){DrawCard(equipment,bounds,slot);return;}
            Panel(bounds,new Color(.015f,.03f,.035f,.88f));
            GUI.Label(new Rect(bounds.x+15,bounds.y+12,bounds.width-30,30),"UNARMED",nameStyle);
            GUI.Label(new Rect(bounds.x+15,bounds.y+47,bounds.width-30,25),"1 Unarmed   ·   2–5 Equip   ·   R Reload",small);
            GUI.Label(new Rect(bounds.x+15,bounds.y+78,bounds.width-30,22),"Hold Tab / LB for inventory",small);
        }
        void DrawCard(FoundationWeapons equipment,Rect bounds,int index)
        {
            var state=equipment.State;bool active=slots[index]==state.Equipped;
            Color before=GUI.color;GUI.color=Color.white;
            Panel(bounds,new Color(.015f,.03f,.035f,.94f));
            Panel(new Rect(bounds.x,bounds.y,3,bounds.height),active?new Color(.96f,.80f,.44f):new Color(.34f,.40f,.42f));
            GUI.Label(new Rect(bounds.x+15,bounds.y+9,bounds.width-52,27),names[index],nameStyle);
            GUI.Label(new Rect(bounds.x+bounds.width-28,bounds.y+9,22,25),keys[index],small);
            Rect icon=new Rect(bounds.x+12,bounds.y+38,126,52);
            Panel(icon,new Color(.62f,.67f,.68f));
            if(icons[index]!=null)GUI.DrawTexture(icon,icons[index],ScaleMode.ScaleToFit,true);
            GUI.Label(new Rect(bounds.x+151,bounds.y+39,bounds.width-162,22),active&&state.Reloading?"Reloading...":detail[index],small);
            string ammo=slots[index]==Equipment.Knife?"READY":state.LoadedFor(slots[index])+" / "+state.ReserveFor(slots[index]);
            GUI.Label(new Rect(bounds.x+151,bounds.y+64,bounds.width-162,28),ammo,nameStyle);
            if(active&&state.Reloading)
            {
                Panel(new Rect(bounds.x+15,bounds.y+bounds.height-7,bounds.width-30,3),new Color(.22f,.26f,.26f));
                Panel(new Rect(bounds.x+15,bounds.y+bounds.height-7,(bounds.width-30)*state.ReloadProgress,3),new Color(.96f,.80f,.44f));
            }
            GUI.color=before;
        }
        static void Panel(Rect rect,Color color)
        {Color before=GUI.color;GUI.color=color;GUI.DrawTexture(rect,Texture2D.whiteTexture);GUI.color=before;}
    }
}
