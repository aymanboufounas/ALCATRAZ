using System;
using UnityEngine;
using DesertShift.Player;
using Blackstone.Foundation;

namespace Blackstone.Supplied
{
    [DefaultExecutionOrder(-650)]
    public sealed class SuppliedIslandWorld : MonoBehaviour
    {
        public bool Ready { get; private set; }
        public string Status { get; private set; }
        public Transform ChapterGate { get; private set; }
        public Transform Helipad { get; private set; }
        public Transform CoastalHouse { get; private set; }
        public bool InsidePrison { get; private set; }
        public Transform Objective=>InsidePrison?interior.Exit:ChapterGate;
        SuppliedPrisonInterior interior;
        public const float MapRootX=-63,MapRootY=45,MapRootZ=12;
        public static readonly Vector3 SpawnXZ=new Vector3(-147,0,6);
        public static readonly Vector3 HelipadXZ=new Vector3(-151,0,-5);
        PlayerMovement player;
        PlayerInputHandler input;
        Vector3 safe;
        Material water,deck,boatHullMaterial;Mesh boatHullMesh;
        void Awake()
        {
            try
            {
                var island=SuppliedModel.Create("Island",transform);island.transform.localPosition=new Vector3(MapRootX,MapRootY,MapRootZ);
                var shader=Shader.Find("Universal Render Pipeline/Lit");if(shader==null)throw new InvalidOperationException("URP Lit shader is unavailable.");
                var bayWater=Resources.Load<Material>("AlcatrazSupplied/Island/CoastalWater");
                if(bayWater==null)throw new InvalidOperationException("The coastal water material is missing from the updated project.");
                water=new Material(bayWater);
                deck=new Material(shader){color=new Color(.48f,.43f,.34f)};deck.SetFloat("_Smoothness",.12f);
                Cube("Pacific Ocean",new Vector3(0,-.65f,0),new Vector3(4000,1,4000),water,false);
                Physics.SyncTransforms();
                Vector3 gate=Ground(new Vector3(-113.33f,0,22.5f));
                ChapterGate=new GameObject("Cellhouse entrance").transform;ChapterGate.SetParent(transform);ChapterGate.position=gate;
                Vector3 guardPosition=Ground(new Vector3(-118,0,21));
                var guard=SuppliedModel.Create("Police",transform);guard.transform.rotation=Quaternion.Euler(0,180,0);SuppliedModel.SizeAndGround(guard,1.82f,guardPosition);
                var head=NamedRenderer(guard,"policeman_head");
                if(head==null)throw new InvalidOperationException("The supplied police head mesh is missing.");
                var headBounds=head.bounds;
                var helmetAnchor=Anchor("Helmet socket",guard.transform,new Vector3(headBounds.center.x,headBounds.max.y-.065f,headBounds.center.z));
                var vestAnchor=Anchor("Vest socket",guard.transform,new Vector3(headBounds.center.x,guardPosition.y+1.27f,headBounds.center.z)-guard.transform.forward*.025f);
                // The supplied wearables face opposite the OBJ officer's source forward.
                helmetAnchor.localRotation=vestAnchor.localRotation=Quaternion.Euler(0,180,0);
                SuppliedModel.Attach("Helmet",helmetAnchor,.32f,Vector3.zero);SuppliedModel.Attach("Vest",vestAnchor,.56f,Vector3.zero);
                var guardBody=guard.AddComponent<CapsuleCollider>();guardBody.height=1.8f/guard.transform.lossyScale.y;guardBody.radius=.25f/guard.transform.lossyScale.x;
                guardBody.center=guard.transform.InverseTransformPoint(guardPosition+Vector3.up*.9f);
                Vector3 dogPosition=Ground(new Vector3(-105,0,25));var dogRoot=new GameObject("Police dog patrol");dogRoot.transform.SetParent(transform);dogRoot.transform.position=dogPosition;
                var dog=SuppliedModel.Create("Dog",dogRoot.transform);SuppliedModel.SizeAndGround(dog,.82f,dogPosition);
                var patrol=dogRoot.AddComponent<SuppliedDogPatrol>();patrol.world=this;
                patrol.route=new[]{Ground(new Vector3(-105,0,25)),Ground(new Vector3(-112,0,25))};
                var helicopter=SuppliedModel.Create("Helicopter",transform);
                Vector3 landing=Ground(HelipadXZ);
                // Level the pad above every sampled corner, avoiding buried skids.
                for(int x=-5;x<=5;x+=5)for(int z=-5;z<=5;z+=5)
                    landing.y=Mathf.Max(landing.y,Ground(HelipadXZ+new Vector3(x,0,z)).y);
                landing.y+=.08f;
                Helipad=new GameObject("Little Bird helipad").transform;Helipad.SetParent(transform);Helipad.position=landing;
                Cube("Helicopter landing deck",landing-Vector3.up*.16f,new Vector3(12,.3f,12),deck,true);
                for(int i=0;i<3;i++)
                    Cube("Dock practice target "+(i+1),landing+new Vector3(-3+i*3,1.35f,-4),new Vector3(.7f,1.1f,.12f),deck,true).AddComponent<FoundationTarget>();
                helicopter.transform.rotation=Quaternion.Euler(0,110,0);SuppliedModel.SizeAndGround(helicopter,2.8f,landing+Vector3.up*.02f);
                var aircraftBounds=SuppliedModel.Bounds(helicopter);
                var cockpit=NamedRenderer(helicopter,"vidrio");
                if(cockpit==null)throw new InvalidOperationException("The supplied helicopter cockpit mesh is missing.");
                var craft=new GameObject("Flyable Little Bird");craft.transform.SetParent(transform);craft.transform.position=new Vector3(cockpit.bounds.center.x,aircraftBounds.min.y,cockpit.bounds.center.z);craft.transform.rotation=helicopter.transform.rotation;
                helicopter.transform.SetParent(craft.transform,true);
                var aircraftBody=craft.AddComponent<BoxCollider>();aircraftBody.center=new Vector3(0,.85f,0);aircraftBody.size=new Vector3(1.7f,1.7f,3.4f);
                var tail=craft.AddComponent<BoxCollider>();tail.center=new Vector3(0,1.25f,-4.1f);tail.size=new Vector3(.45f,.55f,4.8f);
                craft.AddComponent<Rigidbody>();var flight=craft.AddComponent<FoundationVehicle>();flight.aircraft=true;
                Renderer mainRotor=null,tailRotor=null;
                foreach(var r in helicopter.GetComponentsInChildren<Renderer>())
                {string n=r.name.ToLowerInvariant();if(!n.Contains("helice")&&!n.Contains("rotor"))continue;if(mainRotor==null||r.bounds.size.magnitude>mainRotor.bounds.size.magnitude){tailRotor=mainRotor;mainRotor=r;}else tailRotor=r;}
                if(mainRotor!=null)flight.rotor=RotorPivot(mainRotor,helicopter.transform);
                if(tailRotor!=null)flight.tailRotor=RotorPivot(tailRotor,helicopter.transform);
                var house=SuppliedModel.Create("House",transform);Vector3 housePosition=new Vector3(-165,2,162);
                SuppliedModel.SizeAndGround(house,14,housePosition);
                CoastalHouse=new GameObject("Coastal house dock").transform;CoastalHouse.SetParent(transform);CoastalHouse.position=new Vector3(-184,2.08f,148);
                Cube("House dock platform",new Vector3(-165,1.85f,162),new Vector3(42,.3f,34),deck,true);
                Vector3 shore=Ground(new Vector3(-173,0,80));BuildPier(shore+Vector3.up*.15f,new Vector3(-165,2,147));
                BuildBoat(new Vector3(-184,.2f,142));
                interior=gameObject.AddComponent<SuppliedPrisonInterior>();interior.Create();gameObject.AddComponent<SuppliedExtrasWorld>();Physics.SyncTransforms();
                Status="Ready";Ready=true;
            }
            catch(Exception e){Status=e.Message;Debug.LogError("Alcatraz supplied world: "+Status);}
        }
        void Start()
        {
            player=FindFirstObjectByType<PlayerMovement>();input=player!=null?player.GetComponent<PlayerInputHandler>():null;
            if(!Ready||player==null)return;
            safe=Ground(SpawnXZ)+Vector3.up*.12f;player.Teleport(safe);player.transform.rotation=Quaternion.Euler(0,200,0);
            // AlcatrazPresentation applies the shared daylight after world setup.
        }
        public Vector3 Ground(Vector3 point)
        {
            if(!Physics.Raycast(new Vector3(point.x,140,point.z),Vector3.down,out var hit,200,1,QueryTriggerInteraction.Ignore))
                throw new InvalidOperationException("No island floor at "+point+". Prepare the supplied coastline mesh.");
            return hit.point;
        }
        public void VisitCellhouse()
        {if(player==null||player.ExternalControl)return;InsidePrison=false;Travel(Ground(new Vector3(-107,0,23))+Vector3.up*.12f,250);}
        public void VisitHelipad()
        {if(player==null||player.ExternalControl)return;InsidePrison=false;Travel(safe,200);}
        public void VisitCoastalHouse()
        {if(player==null||player.ExternalControl)return;InsidePrison=false;Travel(CoastalHouse.position,0);}
        public void EnterCellhouse()
        {if(!Ready||player==null||player.ExternalControl)return;InsidePrison=true;Travel(SuppliedPrisonInterior.Offset+SuppliedPrisonInterior.EntryLocal,0);}
        void Travel(Vector3 position,float yaw)
        {
            if(!Ready||player==null||player.ExternalControl)return;
            if(Blackstone.Activities.PrisonPokerTable.Active!=null)Blackstone.Activities.PrisonPokerTable.Active.Close();
            var annex=GetComponent<SuppliedExtrasWorld>();if(annex!=null)annex.EndVisit();
            player.Teleport(position);player.transform.rotation=Quaternion.Euler(0,yaw,0);
            var map=GetComponent<Blackstone.Alcatraz.AlcatrazMap>();if(map!=null)map.SetSafePosition(position);
        }
        void Update()
        {
            if(GetComponent<SuppliedExtrasWorld>()!=null&&GetComponent<SuppliedExtrasWorld>().Visiting)return;
            if(!Ready||player==null||player.ExternalControl||input==null||!input.CanControl)return;
            // AlcatrazMap owns ledge protection and recovery for both island layouts.
            if(InsidePrison)
            {
                // Walking across the exit returns safely, too.
                Vector3 local=SuppliedPrisonInterior.Local(player.transform.position);
                if(local.z < -42.8f || (Vector3.Distance(player.transform.position,interior.Exit.position)<3.4f&&input.InteractPressed))
                    VisitCellhouse();
            }
            else if(ChapterGate!=null&&Vector3.Distance(player.transform.position,ChapterGate.position)<3.4f&&input.InteractPressed)
                EnterCellhouse();
        }
        static Transform RotorPivot(Renderer blade,Transform model)
        {
            var filter=blade.GetComponent<MeshFilter>();
            Vector3 center=filter!=null&&filter.sharedMesh!=null?blade.transform.TransformPoint(filter.sharedMesh.bounds.center):blade.bounds.center;
            var pivot=new GameObject("Rotor axle").transform;pivot.SetParent(model,true);pivot.position=center;pivot.rotation=model.rotation;blade.transform.SetParent(pivot,true);return pivot;
        }
        static Renderer NamedRenderer(GameObject model,string name)
        {foreach(var renderer in model.GetComponentsInChildren<Renderer>())if(renderer.name==name)return renderer;return null;}
        void BuildBoat(Vector3 position)
        {
            var root=new GameObject("Alcatraz coastal patrol boat");root.transform.SetParent(transform);root.transform.position=position;
            var hull=boatHullMaterial=new Material(deck){color=new Color(.12f,.2f,.24f)};
            var keel=BoatPart(root.transform,"Hull keel",new Vector3(0,-.15f,0),new Vector3(1.9f,.65f,4.6f),hull,true);keel.GetComponent<Renderer>().enabled=false;
            boatHullMesh=BoatHull(root.transform,hull);
            BoatPart(root.transform,"Port gunwale",new Vector3(-.92f,.36f,0),new Vector3(.14f,.45f,4.2f),deck,true);
            BoatPart(root.transform,"Starboard gunwale",new Vector3(.92f,.36f,0),new Vector3(.14f,.45f,4.2f),deck,true);
            BoatPart(root.transform,"Bow",new Vector3(0,.2f,2.05f),new Vector3(1.75f,.35f,.5f),deck,true);
            BoatPart(root.transform,"Pilot console",new Vector3(0,.65f,.25f),new Vector3(.9f,.9f,.55f),deck,true);
            BoatPart(root.transform,"Bench",new Vector3(0,.4f,-1.2f),new Vector3(1.6f,.25f,.6f),deck,true);
            BoatPart(root.transform,"Outboard motor",new Vector3(0,.2f,-2.35f),new Vector3(.5f,.85f,.45f),hull,true);
            root.AddComponent<Rigidbody>();var vessel=root.AddComponent<FoundationVehicle>();vessel.seat=new Vector3(0,.55f,-.45f);
        }
        GameObject BoatPart(Transform parent,string name,Vector3 p,Vector3 size,Material mat,bool collision)
        {var go=Cube(name,Vector3.zero,size,mat,collision);go.transform.SetParent(parent,false);go.transform.localPosition=p;return go;}
        static Mesh BoatHull(Transform root,Material material)
        {
            Vector2[] ring={new Vector2(-.85f,-2.2f),new Vector2(.85f,-2.2f),new Vector2(1,-1.2f),new Vector2(.85f,1.5f),new Vector2(.4f,2.3f),new Vector2(0,2.75f),new Vector2(-.4f,2.3f),new Vector2(-.85f,1.5f)};
            var vertices=new System.Collections.Generic.List<Vector3>();var triangles=new System.Collections.Generic.List<int>();
            for(int i=0;i<8;i++){var a=ring[i];vertices.Add(new Vector3(a.x,.35f,a.y));vertices.Add(new Vector3(a.x*.6f,-.45f,a.y*.82f));}
            for(int i=0;i<8;i++){int j=(i+1)%8;triangles.AddRange(new[]{i*2,j*2,i*2+1,j*2,j*2+1,i*2+1});}
            vertices.Add(new Vector3(0,.35f,0));vertices.Add(new Vector3(0,-.45f,0));
            for(int i=0;i<8;i++){int j=(i+1)%8;triangles.AddRange(new[]{16,j*2,i*2,17,i*2+1,j*2+1});}
            var mesh=new Mesh{name="Patrol boat hull"};mesh.SetVertices(vertices);mesh.SetTriangles(triangles,0);mesh.RecalculateNormals();mesh.RecalculateBounds();
            var go=new GameObject("V hull");go.transform.SetParent(root,false);go.AddComponent<MeshFilter>().sharedMesh=mesh;go.AddComponent<MeshRenderer>().sharedMaterial=material;return mesh;
        }
        static Transform Anchor(string name,Transform parent,Vector3 position)
        {var node=new GameObject(name).transform;node.SetParent(parent);node.localRotation=Quaternion.identity;node.position=position;return node;}
        void BuildPier(Vector3 start,Vector3 end)
        {
            Vector3 delta=end-start;var pier=Cube("Coastal service pier",(start+end)/2-Vector3.up*.12f,new Vector3(3.2f,.24f,delta.magnitude),deck,true);
            pier.transform.rotation=Quaternion.LookRotation(delta.normalized,Vector3.up);
            for(int i=0;i<=8;i++)
            {
                Vector3 p=Vector3.Lerp(start,end,i/8f);float h=Mathf.Max(1,p.y+1);
                Cube("Pier support",new Vector3(p.x,(p.y-1)/2,p.z),new Vector3(.24f,h,.24f),deck,false);
            }
        }
        GameObject Cube(string name,Vector3 position,Vector3 scale,Material material,bool collision)
        {
            var go=GameObject.CreatePrimitive(PrimitiveType.Cube);go.name=name;go.transform.SetParent(transform);go.transform.position=position;go.transform.localScale=scale;
            go.GetComponent<Renderer>().sharedMaterial=material;go.GetComponent<Collider>().enabled=collision;return go;
        }
        void OnDestroy(){if(water!=null)Destroy(water);if(deck!=null)Destroy(deck);if(boatHullMaterial!=null)Destroy(boatHullMaterial);if(boatHullMesh!=null)Destroy(boatHullMesh);}
    }
}
