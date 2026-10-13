using UnityEngine;
using DesertShift.Player;
using Blackstone.Foundation;
using Blackstone.Activities;

namespace Blackstone.Supplied
{
    // The annex connects to the cellhouse. The map and the original island remain navigable.
    [DefaultExecutionOrder(-610)]
    public sealed class SuppliedExtrasWorld : MonoBehaviour
    {
        public static readonly Vector3 Origin=new Vector3(1200,50,0);
        public bool Visiting { get; private set; }
        PlayerMovement player;PlayerInputHandler input;SuppliedIslandWorld world;
        Vector3 previous;Material concrete,steel;Transform entrance,exit;
        void Awake()
        {
            world=GetComponent<SuppliedIslandWorld>();
            var shader=Shader.Find("Universal Render Pipeline/Lit");if(shader==null)return;
            concrete=new Material(shader){color=new Color(.43f,.46f,.45f)};steel=new Material(shader){color=new Color(.12f,.17f,.19f)};
            Box("Workshop annex floor",Origin-Vector3.up*.2f,new Vector3(100,.4f,110),concrete);
            Box("North perimeter west",Origin+new Vector3(-27,1.4f,55),new Vector3(46,2.8f,.3f),steel);
            Box("North perimeter east",Origin+new Vector3(27,1.4f,55),new Vector3(46,2.8f,.3f),steel);
            Box("East perimeter north",Origin+new Vector3(50,1.4f,29.5f),new Vector3(.3f,2.8f,51),steel);
            Box("East perimeter south",Origin+new Vector3(50,1.4f,-29.5f),new Vector3(.3f,2.8f,51),steel);
            Box("West perimeter",Origin+new Vector3(-50,1.4f,0),new Vector3(.3f,2.8f,110),steel);
            Box("South perimeter",Origin+new Vector3(0,1.4f,-55),new Vector3(100,2.8f,.3f),steel);
            Model("PrisonRoom",3.7f,new Vector3(-15,0,22));Model("Hallway",3.8f,new Vector3(13,0,24));
            Model("Store",4.5f,new Vector3(-18,0,-14));Model("Workshop",3.2f,new Vector3(-18,0,-31));
            Model("SteelStairs",5.8f,new Vector3(31,0,20));
            Model("BridgePack",2.5f,new Vector3(22,0,3));Model("UtilityBuilding",6,new Vector3(10,0,-28));Model("Watchtower",8,new Vector3(34,0,-25));
            Model("Forest",12,new Vector3(-35,0,38));Model("Beach",2,new Vector3(34,0,42));var guard=Model("Shephard",1.82f,new Vector3(-10,0,5));if(guard!=null){var cap=guard.AddComponent<CapsuleCollider>();cap.height=1.82f/guard.transform.lossyScale.y;cap.radius=.23f/guard.transform.lossyScale.x;cap.center=guard.transform.InverseTransformPoint(Origin+new Vector3(-10,.91f,5));}
            Box("Warehouse bay floor",Origin+new Vector3(72.5f,-.2f,0),new Vector3(47,.4f,50),concrete);
            Box("Warehouse bay north",Origin+new Vector3(73,1.4f,25),new Vector3(46,2.8f,.3f),steel);
            Box("Warehouse bay south",Origin+new Vector3(73,1.4f,-25),new Vector3(46,2.8f,.3f),steel);
            Box("Warehouse bay east",Origin+new Vector3(96,1.4f,0),new Vector3(.3f,2.8f,50),steel);
            var warehouse=Model("Warehouse",5.5f,new Vector3(72,0,0));if(warehouse!=null)warehouse.AddComponent<SuppliedWarehouse>();
            Model("AcidBarrel",1.1f,new Vector3(61.5f,0,10));Model("AcidBarrel",1.1f,new Vector3(62.6f,0,10));
            Model("ExplosiveBarrel",1.1f,new Vector3(82,0,10));Model("ExplosiveBarrel",1.1f,new Vector3(83.1f,0,10));
            // An overlapping north floor keeps the original annex connected to the new source models.
            Box("Factory yard floor",Origin+new Vector3(0,-.2f,99),new Vector3(100,.4f,90),concrete);
            Box("Factory yard north",Origin+new Vector3(0,1.4f,144),new Vector3(100,2.8f,.3f),steel);
            Box("Factory yard west",Origin+new Vector3(-50,1.4f,99),new Vector3(.3f,2.8f,90),steel);
            Box("Factory yard east",Origin+new Vector3(50,1.4f,99),new Vector3(.3f,2.8f,90),steel);
            Model("Factory",10,new Vector3(-20,0,103));
            Model("SpeakerArray",2.5f,new Vector3(20,0,96));
            Box("Radio table",Origin+new Vector3(20,.4f,90),new Vector3(1.5f,.8f,1),steel);
            Model("Radio",.35f,new Vector3(20,.8f,90));
            var table=Model("PokerTable",1.2f,new Vector3(0,0,14));
            if(table!=null)
            {
                var tableAnchor=new GameObject("Texas Holdem interaction");tableAnchor.transform.SetParent(transform);tableAnchor.transform.position=Origin+new Vector3(0,0,14);table.transform.SetParent(tableAnchor.transform,true);
                var poker=tableAnchor.AddComponent<PrisonPokerTable>();
                poker.playerSeat=new GameObject("Elias poker seat").transform;poker.playerSeat.SetParent(transform);poker.playerSeat.position=Origin+new Vector3(0,.03f,12.3f);
                Model("PokerProps",.32f,new Vector3(0,.85f,14));
            }
            var bag=Model("PunchingBag",1.4f,new Vector3(10,.7f,-3));
            if(bag!=null)
            {
                // Keep the pivot at the top so impulses swing the suspended bag.
                var pivot=new GameObject("Suspended boxing bag");pivot.transform.SetParent(transform);pivot.transform.position=Origin+new Vector3(10,2.1f,-3);bag.transform.SetParent(pivot.transform,true);
                var c=pivot.AddComponent<CapsuleCollider>();c.height=1.4f;c.radius=.24f;c.center=Vector3.down*.7f;
                var rb=pivot.AddComponent<Rigidbody>();rb.mass=35;rb.linearDamping=.4f;rb.angularDamping=1;rb.interpolation=RigidbodyInterpolation.Interpolate;
                var hinge=pivot.AddComponent<HingeJoint>();hinge.axis=Vector3.right;hinge.anchor=Vector3.zero;hinge.useLimits=true;hinge.limits=new JointLimits{min=-35,max=35};hinge.useSpring=true;hinge.spring=new JointSpring{spring=55,damper=4,targetPosition=0};
                pivot.AddComponent<FoundationPunchingBag>();
                Box("Bag hanger",Origin+new Vector3(10,2.2f,-3),new Vector3(.9f,.15f,.35f),steel);
            }
            exit=new GameObject("Annex return door").transform;exit.SetParent(transform);exit.position=Origin+new Vector3(0,0,-47);
            entrance=new GameObject("Workshop entrance").transform;entrance.SetParent(transform);entrance.position=SuppliedPrisonInterior.Offset+new Vector3(15,30.03f,60);
            Physics.SyncTransforms();
        }
        void Start()
        {
            player=FindFirstObjectByType<PlayerMovement>();input=player!=null?player.GetComponent<PlayerInputHandler>():null;
            var poker=GetComponentInChildren<PrisonPokerTable>();if(poker!=null){var actors=FindObjectsByType<Blackstone.Actors.PrisonActor>(FindObjectsSortMode.None);var people=new System.Collections.Generic.List<Blackstone.Actors.PrisonActor>();foreach(string n in new[]{"Samir","Tomas","Luis"})foreach(var a in actors)if(a.displayName==n){people.Add(a);break;}poker.players=people.ToArray();}
        }
        public void Visit()
        {
            if(player==null||player.ExternalControl)return;
            previous=player.transform.position;Visiting=true;player.Teleport(Origin+new Vector3(0,.05f,-44));
            var map=GetComponent<Blackstone.Alcatraz.AlcatrazMap>();if(map!=null)map.SetSafePosition(player.transform.position);
        }
        public void EndVisit(){Visiting=false;}
        public static bool ContainsPosition(Vector3 position)
        {
            var p=position-Origin;if(p.y<-1)return false;
            return Mathf.Abs(p.x)<49.5f&&p.z> -54.5f&&p.z<143.5f||p.x>=49&&p.x<95.5f&&Mathf.Abs(p.z)<24.5f;
        }
        void Leave(){Visiting=false;player.Teleport(previous);var map=GetComponent<Blackstone.Alcatraz.AlcatrazMap>();if(map!=null)map.SetSafePosition(previous);}
        void Update()
        {
            if(player==null||input==null||!input.CanControl||player.ExternalControl)return;
            if(Visiting&&Vector3.Distance(player.transform.position,exit.position)<3&&input.InteractPressed)Leave();
            else if(!Visiting&&world!=null&&world.InsidePrison&&Vector3.Distance(player.transform.position,entrance.position)<2.4f&&input.InteractPressed)Visit();
        }
        void OnGUI()
        {
            if(player==null||input==null||!input.CanControl)return;var door=Visiting?exit:entrance;
            if(door!=null&&Vector3.Distance(player.transform.position,door.position)<2.4f)GUI.Box(new Rect(Screen.width/2-210,Screen.height-150,420,45),Visiting?"E / X   RETURN TO CELLHOUSE":"E / X   ENTER WORKSHOP & RECREATION ANNEX");
        }
        GameObject Model(string name,float height,Vector3 position)
        {
            var prefab=Resources.Load<GameObject>("AlcatrazExtras/"+name+"/"+name);if(prefab==null){Debug.LogError("Missing supplied model: "+name);return null;}
            var model=Instantiate(prefab,transform,false);SuppliedModel.SizeAndGround(model,height,Origin+position);return model;
        }
        void Box(string name,Vector3 position,Vector3 size,Material material)
        {var go=GameObject.CreatePrimitive(PrimitiveType.Cube);go.name=name;go.transform.SetParent(transform);go.transform.position=position;go.transform.localScale=size;go.GetComponent<Renderer>().sharedMaterial=material;}
        void OnDestroy(){if(concrete!=null)Destroy(concrete);if(steel!=null)Destroy(steel);}
    }
}
