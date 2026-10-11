using UnityEngine;

namespace Blackstone.Foundation
{
    public static class PrisonMenuTheme
    {
        public static readonly Color Gold=new Color(.83f,.68f,.39f);
        public static readonly Color Paper=new Color(.93f,.91f,.85f);
        static GUIStyle title,subtitle,body,button;
        static Texture2D line;
        static void Styles()
        {
            if(title!=null)return;
            title=new GUIStyle(GUI.skin.label){fontSize=68,fontStyle=FontStyle.Bold,alignment=TextAnchor.MiddleLeft};title.normal.textColor=Paper;
            subtitle=new GUIStyle(title){fontSize=15,fontStyle=FontStyle.Normal};subtitle.normal.textColor=Gold;
            body=new GUIStyle(subtitle){fontSize=21,wordWrap=true};body.normal.textColor=Paper;
            line=new Texture2D(1,1);line.SetPixel(0,0,new Color(.12f,.15f,.17f,1));line.Apply();
            button=new GUIStyle(GUI.skin.button){fontSize=23,alignment=TextAnchor.MiddleLeft,padding=new RectOffset(22,20,0,0),border=new RectOffset()};
            button.normal.background=line;button.normal.textColor=Paper;button.hover.textColor=Gold;button.active.textColor=Gold;button.focused.textColor=Gold;
        }
        public static void Panel(Rect r,Color color)
        {Color old=GUI.color;GUI.color=color;GUI.DrawTexture(r,Texture2D.whiteTexture);GUI.color=old;}
        public static void Frame(float width,float height,string heading,string location,bool paused)
        {
            Styles();
            Panel(new Rect(0,0,width,height),new Color(.025f,.033f,.042f,.86f));
            Panel(new Rect(0,0,620,height),new Color(.027f,.036f,.043f,.96f));
            Panel(new Rect(620,0,1,height),new Color(.83f,.68f,.39f,.28f));
            Text(new Rect(70,64,480,28),"THE SILENT BLUEPRINT",true);
            GUI.Label(new Rect(64,118,530,176),heading,title);
            Text(new Rect(70,308,470,32),paused?"SESSION PAUSED  /  "+location:location,true);
            Panel(new Rect(70,357,470,1),new Color(.83f,.68f,.39f,.4f));
            Text(new Rect(70,height-78,470,28),"ELIAS VALE  ·  INMATE B-04",true);
            Text(new Rect(width-360,height-78,290,28),"ALCATRAZ  /  CHAPTER 01",true);
        }
        public static void Text(Rect r,string value,bool caption=false)
        {Styles();GUI.Label(r,value,caption?subtitle:body);}
        public static bool Button(Rect r,string value,bool enabled=true)
        {Styles();bool old=GUI.enabled;GUI.enabled=enabled;bool pressed=GUI.Button(r,value,button);GUI.enabled=old;return pressed;}
        public static bool Navigation(int index,string value,bool enabled=true)
        {return Button(new Rect(70,410+index*76,470,60),value,enabled);}
    }
}
