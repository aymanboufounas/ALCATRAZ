using UnityEngine;

namespace Blackstone.Foundation
{
    public static class PrisonMenuTheme
    {
        public static readonly Color Gold=new Color(.83f,.68f,.39f);
        public static readonly Color Paper=new Color(.93f,.91f,.85f);
        static GUIStyle title,subtitle,body,button,number,arrow;
        static Texture2D background;
        static readonly string[] navigationIcons={"play","book","map","settings","controls","exit"};
        public static Matrix4x4 MenuMatrix
        {
            get
            {
                float scale=Mathf.Min(Screen.width/1920f,Screen.height/1080f);
                return Matrix4x4.TRS(new Vector3((Screen.width-1920*scale)/2,(Screen.height-1080*scale)/2,0),Quaternion.identity,new Vector3(scale,scale,1));
            }
        }
        static void Styles()
        {
            if(title!=null)return;
            var font=Resources.Load<Font>("BlackstoneFoundation/Menu/Heading");
            background=Resources.Load<Texture2D>("BlackstoneFoundation/Menu/Background");
            title=new GUIStyle(GUI.skin.label){font=font,fontSize=108,fontStyle=FontStyle.Normal,alignment=TextAnchor.MiddleLeft};title.normal.textColor=Paper;
            subtitle=new GUIStyle(GUI.skin.label){fontSize=16,fontStyle=FontStyle.Normal};subtitle.normal.textColor=Gold;
            body=new GUIStyle(subtitle){fontSize=24,wordWrap=true};body.normal.textColor=Paper;
            button=new GUIStyle(GUI.skin.label){fontSize=24,alignment=TextAnchor.MiddleLeft};button.normal.textColor=Paper;
            number=new GUIStyle(button){fontSize=22};number.normal.textColor=Gold;
            arrow=new GUIStyle(button){alignment=TextAnchor.MiddleCenter,fontSize=30};arrow.normal.textColor=Gold;
        }
        public static void Panel(Rect r,Color color)
        {Color old=GUI.color;GUI.color=color;GUI.DrawTexture(r,Texture2D.whiteTexture);GUI.color=old;}
        static void Border(Rect r,Color color,float thickness=1)
        {
            Panel(new Rect(r.x,r.y,r.width,thickness),color);Panel(new Rect(r.x,r.yMax-thickness,r.width,thickness),color);
            Panel(new Rect(r.x,r.y,thickness,r.height),color);Panel(new Rect(r.xMax-thickness,r.y,thickness,r.height),color);
        }
        public static void Frame(float width,float height,string heading,string location,bool paused)
        {
            Styles();
            // The caller uses a uniformly scaled 1920 x 1080 menu canvas.
            float scale=Mathf.Min(Screen.width/1920f,Screen.height/1080f);
            Panel(new Rect(-(Screen.width/scale-1920)/2,-(Screen.height/scale-1080)/2,Screen.width/scale,Screen.height/scale),Color.black);
            if(background!=null)GUI.DrawTexture(new Rect(0,0,width,height),background,ScaleMode.ScaleAndCrop);
            else Panel(new Rect(0,0,width,height),new Color(.025f,.033f,.042f,1));
            Panel(new Rect(0,0,590,height),new Color(.015f,.019f,.022f,.82f));
            Panel(new Rect(590,0,width-590,height),new Color(.01f,.018f,.025f,.3f));
            Panel(new Rect(57,0,1,height),new Color(.83f,.68f,.39f,.3f));
            Panel(new Rect(588,0,2,height),new Color(.83f,.68f,.39f,.35f));
            Text(new Rect(100,54,450,30),"THE SILENT BLUEPRINT",true);
            Panel(new Rect(100,91,450,1),Gold);
            var headingStyle=new GUIStyle(title){fontSize=heading.Contains("\n")?78:124};
            GUI.Label(new Rect(94,110,466,165),heading,headingStyle);
            Text(new Rect(100,274,450,32),paused?"SESSION PAUSED  /  "+location:location,true);
            Panel(new Rect(100,313,450,1),new Color(.83f,.68f,.39f,.65f));
            Text(new Rect(100,height-82,460,28),"ELIAS VALE  ·  INMATE B-04",true);
            Panel(new Rect(100,height-53,450,1),Gold);
            Text(new Rect(width-425,54,370,28),"ALCATRAZ  /  CHAPTER 01",true);
        }
        public static void Text(Rect r,string value,bool caption=false)
        {Styles();GUI.Label(r,value,caption?subtitle:body);}
        public static void Hero(Rect r,string value,int size=76)
        {Styles();var style=new GUIStyle(title){fontSize=size,wordWrap=true};GUI.Label(r,value.ToUpperInvariant(),style);}
        public static bool Button(Rect r,string value,bool enabled=true)
        {
            Styles();bool old=GUI.enabled;GUI.enabled=old&&enabled;
            bool hover=GUI.enabled&&r.Contains(Event.current.mousePosition);
            Panel(r,hover?new Color(.26f,.18f,.075f,.85f):new Color(.045f,.055f,.06f,.9f));
            Border(r,hover?Gold:new Color(.5f,.5f,.45f,.3f),hover?2:1);
            bool pressed=GUI.Button(r,GUIContent.none,GUIStyle.none);
            Color color=GUI.color;if(!GUI.enabled)GUI.color=new Color(1,1,1,.4f);
            GUI.Label(new Rect(r.x+22,r.y,r.width-50,r.height),value,button);
            GUI.color=color;GUI.enabled=old;return pressed;
        }
        public static bool Navigation(int index,string value,bool enabled=true,bool selected=false)
        {
            return NavigationAt(new Rect(95,344+index*82,460,72),index,value,enabled,selected);
        }
        public static bool SectionNavigation(int index,string value,bool selected)
        {return NavigationAt(new Rect(95,330+index*63,460,55),index,(index+1).ToString("00")+"   "+value,true,selected,true);}
        static bool NavigationAt(Rect r,int index,string value,bool enabled,bool selected,bool compact=false)
        {
            Styles();
            bool old=GUI.enabled;GUI.enabled=old&&enabled;
            bool highlighted=GUI.enabled&&(selected||r.Contains(Event.current.mousePosition));
            Panel(r,highlighted?(compact?new Color(.52f,.045f,.045f,.94f):new Color(.28f,.19f,.075f,.83f)):new Color(.035f,.045f,.05f,.9f));
            if(highlighted)for(int i=5;i>0;i--)Border(new Rect(r.x-i,r.y-i,r.width+2*i,r.height+2*i),new Color(Gold.r,Gold.g,Gold.b,.025f*(6-i)),1);
            Border(r,highlighted?Gold:new Color(.5f,.5f,.45f,.35f),highlighted?2:1);
            bool pressed=GUI.Button(r,GUIContent.none,GUIStyle.none);
            Color color=GUI.color;if(!GUI.enabled)GUI.color=new Color(1,1,1,.35f);
            string icon=index>=0&&index<navigationIcons.Length?navigationIcons[index]:"play";
            string label=value.Length>=5?value.Substring(5).Trim():value;
            int shortcut=label.IndexOf("  [");if(shortcut>=0)label=label.Substring(0,shortcut);
            if(label.Contains("Settings"))icon="settings";
            else if(label=="Map")icon="map";
            else if(label=="Inventory"||label=="Weapons")icon="cards";
            else if(label=="Character")icon="inmate";
            else if(label=="Mission"||label=="Journal"||label.Contains("Game"))icon="book";else if(label.Contains("Quit")||label.Contains("Return")||label.Contains("Exit"))icon="exit";
            Icon(new Rect(r.x+25,r.center.y-17,34,34),icon);
            GUI.Label(new Rect(r.x+91,r.y,50,r.height),(index+1).ToString("00"),number);
            GUI.Label(new Rect(r.x+149,r.y,r.width-184,r.height),compact?label.ToUpperInvariant():label,compact?new GUIStyle(button){fontSize=20,fontStyle=FontStyle.Bold}:button);
            GUI.Label(new Rect(r.xMax-36,r.y,25,r.height),"›",arrow);
            GUI.color=color;GUI.enabled=old;return pressed;
        }
        static readonly System.Collections.Generic.Dictionary<string,Texture2D> icons=new System.Collections.Generic.Dictionary<string,Texture2D>();
        public static void Icon(Rect r,string name)
        {
            if(!icons.TryGetValue(name,out var image)){image=Resources.Load<Texture2D>("BlackstoneFoundation/Menu/"+name);icons[name]=image;}
            if(image!=null)GUI.DrawTexture(r,image,ScaleMode.ScaleToFit);
        }
        public static void Features(float x,float y,float width)
        {
            Styles();string[] names={"cell","boat","helicopter","boxing","cards"};
            string[] labels={"Cellhouse &\ngalleries","Coastal\npatrol boat","Helicopter\nflight","Boxing\ntraining","Texas\nHold’em"};
            float slot=Mathf.Min(width/5,170);
            for(int i=0;i<5;i++)
            {
                float left=x+i*slot;Icon(new Rect(left+8,y,56,48),names[i]);
                Text(new Rect(left+8,y+62,slot-16,80),labels[i]);
                if(i<4)Panel(new Rect(left+slot-8,y,1,146),new Color(Gold.r,Gold.g,Gold.b,.45f));
            }
        }
    }
}
