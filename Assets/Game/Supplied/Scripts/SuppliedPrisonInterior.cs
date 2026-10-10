using System;
using UnityEngine;
using Blackstone.Actors;

namespace Blackstone.Supplied
{
    // The supplied scan has a closed roof. An isolated interior keeps that
    // exterior silhouette intact while providing enterable prison rooms.
    public sealed class SuppliedPrisonInterior : MonoBehaviour
    {
        public static readonly Vector3 Offset=new Vector3(1000,20,0);
        public static readonly Vector3 EntryLocal=new Vector3(0,30.12f,-39);
        public Transform Exit { get; private set; }
        public static Vector3 Local(Vector3 world){return world-Offset;}
        public void Create()
        {
            var prefab=Resources.Load<GameObject>("AlcatrazSupplied/Cellhouse/Interior");
            if(prefab==null)throw new InvalidOperationException("The cellhouse interior prefab is missing. Download the complete updated project.");
            var building=Instantiate(prefab,transform,false);building.name="Cellhouse interior";
            building.transform.position=Offset;
            Exit=new GameObject("Return to supplied Alcatraz exterior").transform;
            Exit.SetParent(transform);Exit.position=Offset+new Vector3(0,30,-42);
            // Close the old yard opening; the south entrance is the return route.
            var wall=GameObject.CreatePrimitive(PrimitiveType.Cube);wall.name="West yard security grille";
            wall.transform.SetParent(building.transform,false);wall.transform.localPosition=new Vector3(-26.5f,32,33);
            wall.transform.localScale=new Vector3(.3f,4,8);
            wall.GetComponent<Renderer>().sharedMaterial=Resources.Load<Material>("AlcatrazSupplied/Cellhouse/SecuritySteel");
            Actor("Officer Harrow",new Vector3(-.8f,30.03f,25),180,
                new[]{new Vector3(-.8f,30.03f,25),new Vector3(-.8f,30.03f,-25)});
            Actor("Samir",new Vector3(1,30.03f,-12),0,
                new[]{new Vector3(1,30.03f,-12),new Vector3(1,30.03f,20)});
            Actor("Malik",new Vector3(-12,30.03f,8),0,
                new[]{new Vector3(-12,30.03f,8),new Vector3(-12,30.03f,25)});
            Actor("Tomas",new Vector3(12,30.03f,12),180,null);
            Actor("Dining orderly",new Vector3(-3,30.03f,49),90,null);
            Actor("Luis",new Vector3(5,30.03f,63),270,null);
        }
        void Actor(string name,Vector3 position,float yaw,Vector3[] route)
        {
            var go=new GameObject(name);go.layer=8;go.transform.SetParent(transform);
            go.transform.SetPositionAndRotation(Offset+position,Quaternion.Euler(0,yaw,0));
            var actor=go.AddComponent<PrisonActor>();actor.displayName=name;actor.driveLocomotion=false;
            actor.patrolEnabled=route!=null;
            if(route!=null)
            {actor.patrol=new Vector3[route.Length];for(int i=0;i<route.Length;i++)actor.patrol[i]=Offset+route[i];}
            var body=go.AddComponent<CapsuleCollider>();body.height=1.78f;body.radius=.23f;body.center=Vector3.up*.89f;
        }
    }
}
