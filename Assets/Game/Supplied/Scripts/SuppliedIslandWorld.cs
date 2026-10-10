using System;
using UnityEngine;
using UnityEngine.SceneManagement;
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
        PlayerMovement player;
        PlayerInputHandler input;
        Vector3 safe;
        Material water,deck;
        void Awake()
        {
            try
            {
                var island=SuppliedModel.Create("Island",transform);island.transform.localPosition=new Vector3(-63,45,12);
                var shader=Shader.Find("Universal Render Pipeline/Lit");if(shader==null)throw new InvalidOperationException("URP Lit shader is unavailable.");
                water=new Material(shader){color=new Color(.065f,.20f,.25f)};water.SetFloat("_Smoothness",.78f);water.SetFloat("_Metallic",.1f);
                deck=new Material(shader){color=new Color(.48f,.43f,.34f)};deck.SetFloat("_Smoothness",.12f);
                Cube("Pacific Ocean",new Vector3(0,-.65f,0),new Vector3(4000,1,4000),water,false);
                Physics.SyncTransforms();
                Vector3 gate=Ground(new Vector3(-113.33f,0,22.5f));
                ChapterGate=new GameObject("Cellhouse entrance / Chapter 01").transform;ChapterGate.SetParent(transform);ChapterGate.position=gate;
                Vector3 guardPosition=Ground(new Vector3(-118,0,21));
                var guard=SuppliedModel.Create("Police",transform);guard.transform.rotation=Quaternion.Euler(0,180,0);SuppliedModel.SizeAndGround(guard,1.82f,guardPosition);
                var guardBounds=SuppliedModel.Bounds(guard);
                var helmetAnchor=Anchor("Helmet socket",guard.transform,new Vector3(guardBounds.center.x,guardBounds.max.y-.12f,guardBounds.center.z));
                var vestAnchor=Anchor("Vest socket",guard.transform,new Vector3(guardBounds.center.x,guardBounds.min.y+1.27f,guardBounds.center.z));
                SuppliedModel.Attach("Helmet",helmetAnchor,.32f,Vector3.zero);SuppliedModel.Attach("Vest",vestAnchor,.58f,Vector3.zero);
                var guardBody=guard.AddComponent<CapsuleCollider>();guardBody.height=1.8f/guard.transform.lossyScale.y;guardBody.radius=.25f/guard.transform.lossyScale.x;
                guardBody.center=guard.transform.InverseTransformPoint(guardPosition+Vector3.up*.9f);
                Vector3 dogPosition=Ground(new Vector3(-105,0,25));var dogRoot=new GameObject("Police dog patrol");dogRoot.transform.SetParent(transform);dogRoot.transform.position=dogPosition;
                var dog=SuppliedModel.Create("Dog",dogRoot.transform);SuppliedModel.SizeAndGround(dog,.82f,dogPosition);
                var patrol=dogRoot.AddComponent<SuppliedDogPatrol>();patrol.world=this;
                patrol.route=new[]{Ground(new Vector3(-105,0,25)),Ground(new Vector3(-112,0,25))};
                var helicopter=SuppliedModel.Create("Helicopter",transform);Vector3 landing=Ground(new Vector3(-170,0,-90));
                Cube("Helicopter landing deck",landing-Vector3.up*.16f,new Vector3(12,.3f,12),deck,true);
                for(int i=0;i<3;i++)
                    Cube("Dock practice target "+(i+1),landing+new Vector3(-3+i*3,1.35f,-4),new Vector3(.7f,1.1f,.12f),deck,true).AddComponent<FoundationTarget>();
                helicopter.transform.rotation=Quaternion.Euler(0,110,0);SuppliedModel.SizeAndGround(helicopter,2.8f,landing+Vector3.up*.02f);
                var aircraftCollider=helicopter.AddComponent<BoxCollider>();var aircraftBounds=SuppliedModel.Bounds(helicopter);
                aircraftCollider.center=helicopter.transform.InverseTransformPoint(aircraftBounds.center);
                aircraftCollider.size=new Vector3(aircraftBounds.size.x/helicopter.transform.lossyScale.x,aircraftBounds.size.y/helicopter.transform.lossyScale.y,aircraftBounds.size.z/helicopter.transform.lossyScale.z);
                var house=SuppliedModel.Create("House",transform);Vector3 housePosition=new Vector3(-165,2,162);
                SuppliedModel.SizeAndGround(house,14,housePosition);
                Cube("House dock platform",new Vector3(-165,1.85f,162),new Vector3(42,.3f,34),deck,true);
                Vector3 shore=Ground(new Vector3(-173,0,80));BuildPier(shore+Vector3.up*.15f,new Vector3(-165,2,147));
                Status="Ready";Ready=true;
            }
            catch(Exception e){Status=e.Message;Debug.LogError("Alcatraz supplied world: "+Status);}
        }
        void Start()
        {
            player=FindFirstObjectByType<PlayerMovement>();input=player!=null?player.GetComponent<PlayerInputHandler>():null;
            if(!Ready||player==null)return;
            safe=Ground(new Vector3(-107,0,23))+Vector3.up*.12f;player.Teleport(safe);player.transform.rotation=Quaternion.Euler(0,250,0);
            // AlcatrazPresentation applies the shared daylight after world setup.
        }
        public Vector3 Ground(Vector3 point)
        {
            if(!Physics.Raycast(new Vector3(point.x,140,point.z),Vector3.down,out var hit,200,1,QueryTriggerInteraction.Ignore))
                throw new InvalidOperationException("No island floor at "+point+". Prepare the supplied coastline mesh.");
            return hit.point;
        }
        void Update()
        {
            if(!Ready||player==null||input==null||!input.CanControl)return;
            // AlcatrazMap owns ledge protection and recovery for both island layouts.
            if(ChapterGate!=null&&Vector3.Distance(player.transform.position,ChapterGate.position)<3.4f&&input.InteractPressed)
            {Time.timeScale=1;SceneManager.LoadScene("SC_AlcatrazChapter01");}
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
        void OnDestroy(){if(water!=null)Destroy(water);if(deck!=null)Destroy(deck);}
    }
}
