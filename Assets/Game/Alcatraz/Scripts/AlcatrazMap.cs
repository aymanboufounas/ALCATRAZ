using UnityEngine;
using UnityEngine.InputSystem;
using DesertShift.Player;
using Blackstone.Story;

namespace Blackstone.Alcatraz
{
    // A single world coordinate system is used by map art, routes and checkpoints.
    [DefaultExecutionOrder(-600)]
    public sealed class AlcatrazMap : MonoBehaviour
    {
        public float baseElevation=30;
        public bool suppliedLayout;
        PlayerMovement player;
        PrisonStoryDirector story;
        Texture2D image;
        Texture2D prisonImage;
        Blackstone.Supplied.SuppliedIslandWorld suppliedWorld;
        public bool SuppliedExterior=>suppliedLayout&&(suppliedWorld==null||!suppliedWorld.InsidePrison);
        GUIStyle label, heading;
        Vector3 safePosition;
        bool validSafePosition;
        static readonly Vector3[] Footprint={Vector3.zero,Vector3.right*.22f,Vector3.left*.22f,
            Vector3.forward*.22f,Vector3.back*.22f};
        public float RecoveryMessageUntil { get; private set; }
        public bool ExplorationHudOwnsMap { get; set; }
        public void SetSafePosition(Vector3 position)
        {safePosition=position;validSafePosition=true;}
        public const string CheckpointFile="alcatraz-chapter01.json";
        static readonly string[] Names={"Cellhouse","Recreation Yard","Water Tower","Lighthouse",
            "Warden's House","New Industries","Model Industries","Power House","Storehouse",
            "Barracks","Parade Ground","Sally Port","Dock"};
        static readonly Vector2[] Places={new Vector2(0,1),new Vector2(-48,46),new Vector2(-57,80),
            new Vector2(3,-72),new Vector2(26,-69),new Vector2(-38,122),new Vector2(-16,157),
            new Vector2(62,113),new Vector2(70,-30),new Vector2(65,-91),new Vector2(-6,-123),
            new Vector2(50,-100),new Vector2(105,-63)};
        void Start()
        {
            player=FindFirstObjectByType<PlayerMovement>();story=FindFirstObjectByType<PrisonStoryDirector>();
            image=Resources.Load<Texture2D>(suppliedLayout?"AlcatrazSupplied/Island/Minimap":"Alcatraz/IslandMap");
            suppliedWorld=GetComponent<Blackstone.Supplied.SuppliedIslandWorld>();
            prisonImage=Resources.Load<Texture2D>("AlcatrazSupplied/Cellhouse/Floorplan");
            if(player!=null)
            {
                safePosition=player.transform.position;validSafePosition=true;
                player.GuardUnsafeLedges=story==null||!story.enabled;
            }
        }
        void LateUpdate()
        {
            if(player==null||Time.deltaTime<=0)return;
            Vector3 position=player.transform.position;
            if(player.Grounded&&position.y>1.5f&&SafeFooting(position))
            {safePosition=position;validSafePosition=true;}
            if(!validSafePosition)return;
            bool prison=suppliedWorld!=null&&suppliedWorld.InsidePrison;
            Vector3 local=prison?Blackstone.Supplied.SuppliedPrisonInterior.Local(position):position;
            bool outside=prison?(Mathf.Abs(local.x)>27.4f||local.z>66.8f||local.z<-43.4f||local.y<29.6f)
                :Mathf.Abs(position.x)>(suppliedLayout?350:135)||Mathf.Abs(position.z)>(suppliedLayout?225:220);
            // Recover before the falling camera reaches the underside of the island.
            // Ordinary jumps, stairs and drops onto a nearby floor remain available.
            bool unsupportedFall=player.VerticalSpeed < -3 && position.y<safePosition.y-1.25f
                &&!Physics.Raycast(position+Vector3.up*.3f,Vector3.down,8,~(1<<8),QueryTriggerInteraction.Ignore);
            if(position.y<1.2f||outside||unsupportedFall)
            {
                player.Teleport(safePosition);RecoveryMessageUntil=Time.unscaledTime+3;
            }
        }
        static bool SafeFooting(Vector3 position)
        {
            foreach(var offset in Footprint)
            {
                if(!Physics.Raycast(position+offset+Vector3.up*.4f,Vector3.down,out var hit,
                    .65f,~(1<<8),QueryTriggerInteraction.Ignore)||hit.normal.y<.65f)return false;
            }
            return !Physics.CheckCapsule(position+Vector3.up*.35f,position+Vector3.up*1.5f,
                .23f,~(1<<8),QueryTriggerInteraction.Ignore);
        }
        void Styles()
        {
            if(label!=null)return;
            label=new GUIStyle(GUI.skin.label){fontSize=13,alignment=TextAnchor.MiddleCenter,wordWrap=true};
            label.normal.textColor=Color.white;
            heading=new GUIStyle(label){fontSize=18,fontStyle=FontStyle.Bold};
        }
        public static Vector2 Project(Rect bounds,Vector3 position)
        {
            return new Vector2(bounds.x+Mathf.InverseLerp(-130,130,position.x)*bounds.width,
                bounds.y+(1-Mathf.InverseLerp(-200,190,position.z))*bounds.height);
        }
        static void Panel(Rect rect,Color color)
        {var before=GUI.color;GUI.color=color;GUI.DrawTexture(rect,Texture2D.whiteTexture);GUI.color=before;}
        public bool IsInterior(Vector3 position)
        {
            if(suppliedLayout)return suppliedWorld!=null&&suppliedWorld.InsidePrison;
            return Room(position,0,30,0,53,11,87)||Room(position,0,30,55.5f,44,7,21)
                ||Room(position,12,30,-51,20,5,11)||Room(position,-38,9.3f,122,29,9,42)
                ||Room(position,-16,9.3f,157,28,10,18)||Room(position,62,7.3f,113,28,9,34)
                ||Room(position,70,5,-30,28,7,39)||Room(position,65,5,-91,32,12,39);
        }
        static bool Room(Vector3 p,float x,float y,float z,float width,float height,float depth)
        {return Mathf.Abs(p.x-x)<width/2&&Mathf.Abs(p.z-z)<depth/2&&p.y>y-.3f&&p.y<y+height;}
        public void DrawMap(Rect bounds,Vector3 position,Transform objective,bool names)
        {
            Styles();Panel(bounds,new Color(.06f,.11f,.13f,.94f));
            var art=suppliedWorld!=null&&suppliedWorld.InsidePrison?prisonImage:image;
            if(art!=null)GUI.DrawTexture(bounds,art);
            if(names&&!suppliedLayout)
            {
                for(int i=0;i<Names.Length;i++)
                {
                    var p=Project(bounds,new Vector3(Places[i].x,0,Places[i].y));
                    Panel(new Rect(p.x-49,p.y-10,98,20),new Color(.02f,.03f,.04f,.87f));
                    GUI.Label(new Rect(p.x-49,p.y-10,98,20),Names[i],label);
                }
            }
            Dot(bounds,position,Color.white,7);
            if(objective!=null)Dot(bounds,objective.position,new Color(.97f,.77f,.37f),9);
            if(SuppliedExterior)
            {
                var world=GetComponent<Blackstone.Supplied.SuppliedIslandWorld>();
                if(world!=null)
                {
                    Marker(bounds,world.Helipad,"H",new Color(.35f,.9f,1));
                    Marker(bounds,world.CoastalHouse,"D",new Color(.6f,1,.65f));
                    if(names)
                    {
                        var legend=new Rect(bounds.x+35,bounds.y+12,180,78);
                        Panel(legend,new Color(.02f,.04f,.05f,.95f));
                        GUI.Label(legend,"Gold: cellhouse\nH: Little Bird helipad\nD: coastal house",label);
                    }
                }
            }
            GUI.Label(new Rect(bounds.x+8,bounds.y+5,22,25),"N",heading);
        }
        void Marker(Rect bounds,Transform place,string name,Color color)
        {
            if(place==null)return;var p=Locate(bounds,place.position);
            Panel(new Rect(p.x-10,p.y-10,20,20),new Color(.02f,.04f,.05f,.95f));
            var before=GUI.color;GUI.color=color;GUI.Label(new Rect(p.x-10,p.y-11,20,22),name,label);GUI.color=before;
        }
        Vector2 Locate(Rect bounds,Vector3 point)
        {
            if(!suppliedLayout)return Project(bounds,point);
            if(suppliedWorld!=null&&suppliedWorld.InsidePrison)
            {
                Vector3 local=Blackstone.Supplied.SuppliedPrisonInterior.Local(point);
                return new Vector2(bounds.x+Mathf.InverseLerp(-28,28,local.x)*bounds.width,
                    bounds.y+(1-Mathf.InverseLerp(-45,68,local.z))*bounds.height);
            }
            // The top-down source image has the glTF X axis to the right.
            return new Vector2(bounds.x+(1-Mathf.InverseLerp(-340,340,point.x))*bounds.width,
                bounds.y+Mathf.InverseLerp(-225,225,point.z)*bounds.height);
        }
        void Dot(Rect bounds,Vector3 point,Color color,float size)
        {var p=Locate(bounds,point);Panel(new Rect(p.x-size/2,p.y-size/2,size,size),color);}
        void OnGUI()
        {
            if(player==null||ExplorationHudOwnsMap)return;
            var input=player.GetComponent<PlayerInputHandler>();
            if(input==null||!input.IsCaptured||input.GameplayBlocked)return;
            Styles();var before=GUI.matrix;
            GUI.matrix=Matrix4x4.TRS(Vector3.zero,Quaternion.identity,new Vector3(Screen.width/1600f,Screen.height/900f,1));
            bool large=Keyboard.current!=null&&Keyboard.current.mKey.isPressed;
            if(large)
            {
                Panel(new Rect(0,0,1600,900),new Color(.015f,.024f,.03f,.94f));
                GUI.Label(new Rect(595,24,410,36),"ALCATRAZ ISLAND",heading);
                DrawMap(SuppliedExterior?new Rect(310,115,975,650):new Rect(533,74,534,780),player.transform.position,
                    suppliedWorld!=null?suppliedWorld.Objective:story!=null?story.ObjectiveTarget:null,true);
            }
            else if(story==null||!story.enabled)
            {
                var world=FindFirstObjectByType<Blackstone.Supplied.SuppliedIslandWorld>();
                DrawMap(SuppliedExterior?new Rect(26,690,240,160):new Rect(26,590,172,258),player.transform.position,world!=null?world.Objective:null,false);
                GUI.Label(new Rect(25,850,215,28),"ALCATRAZ  ·  HOLD M FOR MAP",label);
            }
            GUI.matrix=before;
        }
    }
}
