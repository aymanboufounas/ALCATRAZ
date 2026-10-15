#if UNITY_EDITOR
using System;
using System.Reflection;
using UnityEditor;
using UnityEngine;
using Blackstone.Actors;
using Blackstone.Foundation;
using DesertShift.Player;

namespace Blackstone.Alcatraz.Editor
{
    // Uses real colliders and both NPC movement drivers in an isolated fixture.
    public static class NPCGroundingChecks
    {
        const BindingFlags Private=BindingFlags.Instance|BindingFlags.NonPublic;
        static int checks;
        static void Check(bool value,string label)
        {checks++;if(!value)throw new InvalidOperationException("NPC floor regression: "+label);}
        static object Invoke(object target,string method)
        {return target.GetType().GetMethod(method,Private).Invoke(target,null);}
        static void Set(object target,string field,object value)
        {target.GetType().GetField(field,Private).SetValue(target,value);}
        static GameObject Box(Transform root,string name,Vector3 position,Vector3 size)
        {
            var go=GameObject.CreatePrimitive(PrimitiveType.Cube);go.name=name;
            go.transform.SetParent(root);go.transform.position=position;go.transform.localScale=size;return go;
        }
        [MenuItem("Alcatraz/Validate NPC Floor Placement (Play Mode)",priority=27)]
        public static void Run()
        {
            if(!EditorApplication.isPlaying||Time.deltaTime<=0)
            {Debug.LogError("Resume Play Mode before checking NPC floor placement.");return;}
            float oldTime=Time.timeScale;var oldLock=Cursor.lockState;bool oldCursor=Cursor.visible;
            var root=new GameObject("Temporary NPC floor fixture");root.hideFlags=HideFlags.HideAndDontSave;
            Vector3 origin=new Vector3(15000,0,15000);checks=0;
            try
            {
                var floor=Box(root.transform,"Street",origin-Vector3.up*.25f,new Vector3(20,.5f,20));
                var person=new GameObject("Standing NPC");person.layer=8;person.transform.SetParent(root.transform);person.transform.position=origin;
                var actor=person.AddComponent<PrisonActor>();actor.enabled=false;
                var ground=person.GetComponent<ActorGrounding>();ground.enabled=false;
                Physics.SyncTransforms();
                Check(ground!=null&&ground.ShouldStandOnFloor&&ground.IsSupported,"every standing PrisonActor receives floor support");
                person.transform.position=origin-Vector3.up*.6f;
                Check(ground.GroundNow()&&Mathf.Abs(person.transform.position.y-.025f)<.001f,"buried root is raised to the street");
                person.transform.position=origin+Vector3.up*.9f;
                Check(ground.GroundNow()&&Mathf.Abs(person.transform.position.y-.025f)<.001f,"floating root is lowered to the street");
                var gallery=Box(root.transform,"Upper gallery",origin+Vector3.up*2.9f,new Vector3(5,.2f,5));
                Physics.SyncTransforms();
                Check(ground.GroundNow()&&ground.IsSupported&&person.transform.position.y<.1f,"local floor wins over the upper gallery");
                person.transform.position=origin+Vector3.up*1.5f;
                Check(!ground.GroundNow()&&person.transform.position.y==1.5f,"recovery cannot jump between gallery tiers");
                person.transform.position=origin+Vector3.up*.6f;actor.SetPose(ActorPose.Cards);
                Check(!ground.ShouldStandOnFloor&&!ground.GroundNow()&&person.transform.position.y==.6f,"card-table seating is preserved");
                actor.SetPose(ActorPose.Sleep);
                Check(!ground.ShouldStandOnFloor&&!ground.GroundNow(),"sleeping poses are preserved");
                actor.SetPose(ActorPose.Idle);actor.Suspended=true;
                Check(!ground.ShouldStandOnFloor&&!ground.GroundNow(),"scripted cinematic placement is preserved");
                actor.Suspended=false;person.transform.position=origin;
                var table=Box(root.transform,"Bench blocking standing position",origin+Vector3.up*.45f,new Vector3(1,.2f,1));
                Physics.SyncTransforms();
                Check(!ground.GroundNow()&&person.transform.position==origin,"blocked floor cannot lift an NPC onto a bench");
                Check(!ActorGrounding.TryStep(person.transform,origin,out _),"walking cannot enter occupied bench space");
                UnityEngine.Object.DestroyImmediate(table);UnityEngine.Object.DestroyImmediate(gallery);Physics.SyncTransforms();
                Check(!ActorGrounding.TryStep(person.transform,origin+Vector3.forward*10.2f,out _),"unsupported street edge blocks movement");
                Check(!ActorGrounding.TryStep(person.transform,origin+Vector3.up*.8f,out _),"movement rejects a large drop");
                var ramp=Box(root.transform,"Small ramp",origin+new Vector3(5,.15f,5),new Vector3(3,.2f,3));
                ramp.transform.rotation=Quaternion.Euler(12,0,0);Physics.SyncTransforms();
                Check(ActorGrounding.TryStep(person.transform,origin+new Vector3(5,.2f,5),out var rampPosition)
                    &&rampPosition.y>.2f,"a supported slope updates NPC height");
                UnityEngine.Object.DestroyImmediate(ramp);Physics.SyncTransforms();

                person.transform.position=origin+Vector3.forward*9.98f;actor.patrolEnabled=true;
                actor.patrol=new[]{origin+Vector3.forward*12};Set(actor,"waitUntil",Time.time-1);
                for(int i=0;i<200;i++)Invoke(actor,"Update");
                Check(person.transform.position.z<=origin.z+10.001f,"legacy story patrol cannot walk off the street");
                Check(ground.IsSupported,"legacy patrol retains supporting floor");
                person.transform.position=origin+Vector3.forward*9.98f;
                var avatar=person.AddComponent<FoundationAvatar>();avatar.enabled=false;avatar.animator=person.AddComponent<Animator>();
                var agent=person.AddComponent<FoundationAgent>();agent.enabled=false;agent.avatar=avatar;agent.route=actor.patrol;
                Invoke(agent,"Start");Set(agent,"wait",Time.time-1);
                for(int i=0;i<200;i++)Invoke(agent,"Update");
                Check(person.transform.position.z<=origin.z+10.001f,"imported-avatar patrol cannot walk off the street");
                Check(ground.IsSupported,"imported-avatar patrol retains supporting floor");

                // Supplied police roots have a scaled mesh origin above their feet.
                var police=new GameObject("Imported police origin");police.transform.SetParent(root.transform);
                police.transform.position=origin+new Vector3(-4,4,0);police.transform.localScale=Vector3.one*.2f;
                var policeGround=police.AddComponent<ActorGrounding>();policeGround.enabled=false;
                policeGround.SetFeetPosition(origin+Vector3.left*4);
                Check(policeGround.GroundNow()&&policeGround.IsSupported,"static police grounds its mesh feet rather than source origin");
                Check(Mathf.Abs(police.transform.position.y-4.025f)<.001f,"police grounding preserves the imported root offset and scale");
                var lowRoof=Box(root.transform,"Dog-height overhang",origin+new Vector3(5,.9f,0),new Vector3(2,.15f,2));Physics.SyncTransforms();
                Check(ActorGrounding.TrySupport(police.transform,origin+Vector3.right*5,.3f,.3f,false,out _),"dog support does not require human-height clearance");
                Check(!ActorGrounding.TrySupport(police.transform,origin+Vector3.right*5,.3f,.3f,true,out _),"human support rejects the same low overhang");
                UnityEngine.Object.DestroyImmediate(lowRoof);

                var player=new GameObject("Player exclusion");player.layer=8;player.transform.SetParent(root.transform);
                player.transform.position=origin+Vector3.left*7;var movement=player.AddComponent<PlayerMovement>();movement.enabled=false;
                player.GetComponent<PlayerInputHandler>().enabled=false;player.AddComponent<PrisonActor>().enabled=false;
                Check(player.GetComponent<ActorGrounding>()==null,"automatic NPC grounding never attaches to the player");
                var playerGround=player.AddComponent<ActorGrounding>();playerGround.enabled=false;
                Check(!playerGround.ShouldStandOnFloor&&!playerGround.GroundNow(),"NPC grounding cannot move a jumping or swimming player");
                person.transform.position=origin;var health=person.AddComponent<FoundationDamageable>();
                Check(health.Damage(100,origin,Vector3.zero)&&!ground.ShouldStandOnFloor&&!ground.GroundNow(),"dead NPCs retain ragdoll placement");
                Debug.Log("NPC floor fixture passed: "+checks+" Unity collider and patrol assertions.");
            }
            catch(TargetInvocationException error){Debug.LogException(error.InnerException??error);throw;}
            finally
            {
                UnityEngine.Object.DestroyImmediate(root);Physics.SyncTransforms();
                Time.timeScale=oldTime;Cursor.lockState=oldLock;Cursor.visible=oldCursor;
            }
        }
    }
}
#endif
