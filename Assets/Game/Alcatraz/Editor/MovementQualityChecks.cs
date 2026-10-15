#if UNITY_EDITOR
using System;
using System.Reflection;
using UnityEditor;
using UnityEngine;
using DesertShift.Player;
using Blackstone.Foundation;

namespace Blackstone.Alcatraz.Editor
{
    // Runs the controller's real movement/contact methods against Unity boxes.
    // Source math tests do not certify these physics or animation interactions.
    public static class MovementQualityChecks
    {
        const BindingFlags Private=BindingFlags.Instance|BindingFlags.Static|BindingFlags.NonPublic;
        static int checks;
        static void Check(bool condition,string label)
        {checks++;if(!condition)throw new InvalidOperationException("Movement quality: "+label);}
        static object Invoke(object owner,string name,params object[] arguments)
        {return owner.GetType().GetMethod(name,Private).Invoke(owner,arguments);}
        static void Set(object owner,string field,object value)
        {owner.GetType().GetField(field,Private).SetValue(owner,value);}
        static Vector3 Momentum(PlayerMovement movement)=>(Vector3)typeof(PlayerMovement).GetField("velocity",Private).GetValue(movement);
        static void Grounded(PlayerMovement movement,bool value)
        {typeof(PlayerMovement).GetProperty("Grounded").GetSetMethod(true).Invoke(movement,new object[]{value});}
        static CollisionFlags Move(PlayerMovement movement,Vector3 displacement,bool snap)
        {
            Vector3 start=movement.transform.position;
            object[] arguments={displacement,snap,Vector3.zero};
            var flags=(CollisionFlags)Invoke(movement,"MoveWithStepSupport",arguments);
            Grounded(movement,(flags&CollisionFlags.Below)!=0);
            Invoke(movement,"MeasureMotion",start,(Vector3)arguments[2]);
            Invoke(movement,"RejectBlockedMomentum");
            return flags;
        }
        static GameObject Box(Transform parent,string name,Vector3 position,Vector3 size)
        {
            var box=GameObject.CreatePrimitive(PrimitiveType.Cube);box.name=name;box.transform.SetParent(parent);
            box.transform.position=position;box.transform.localScale=size;return box;
        }
        [MenuItem("Alcatraz/Validate Movement Response and Stairs (Play Mode)",priority=31)]
        public static void Run()
        {
            if(!EditorApplication.isPlaying||Time.deltaTime<=0||Time.deltaTime>.1f)
                throw new InvalidOperationException("Resume Play Mode at a stable frame time below 100 ms before checking movement. No tests ran.");
            float oldTime=Time.timeScale;CursorLockMode oldLock=Cursor.lockState;bool oldCursor=Cursor.visible;
            var root=new GameObject("Temporary movement quality checks");root.hideFlags=HideFlags.HideAndDontSave;
            // Outside the authored map/interiors, with enough float precision to
            // observe the first small acceleration frame at high refresh rates.
            Vector3 origin=new Vector3(400,0,400);checks=0;
            try
            {
                var floor=Box(root.transform,"Flat floor",origin-Vector3.up*.25f,new Vector3(12,.5f,12));
                var hero=new GameObject("Movement test prisoner");hero.layer=8;hero.transform.SetParent(root.transform);
                hero.transform.position=origin;
                var controller=hero.AddComponent<CharacterController>();controller.height=1.78f;controller.radius=.25f;
                controller.center=Vector3.up*.89f;controller.skinWidth=.035f;controller.minMoveDistance=0;controller.slopeLimit=46;
                var movement=hero.AddComponent<PlayerMovement>();
                var input=hero.GetComponent<PlayerInputHandler>();input.enabled=false;input.Capture(true);input.SetGameplayBlocked(false);
                // Keep movement enabled so Unity delivers actual controller-hit
                // callbacks; this synchronous fixture removes it before a frame.
                var wall=Box(root.transform,"Blocking wall",origin+new Vector3(0,1,.65f),new Vector3(4,2,.2f));
                Physics.SyncTransforms();controller.Move(Vector3.forward);controller.Move(Vector3.down*.1f);
                Set(movement,"velocity",Vector3.forward*5.5f);
                Move(movement,(Vector3.forward*5.5f-Vector3.up*3)*Time.deltaTime,false);
                Check(Mathf.Abs(Momentum(movement).z)<.05f,"a real wall contact removes stored forward sprint momentum");
                var away=MovementResponseRules.Approach(0,Momentum(movement).z,0,-2.15f,8.5f,12,Time.deltaTime);
                Set(movement,"velocity",new Vector3(away.X,0,away.Z));
                float beforeAway=hero.transform.position.z;
                Move(movement,(new Vector3(away.X,0,away.Z)-Vector3.up*3)*Time.deltaTime,false);
                Check(hero.transform.position.z<beforeAway,"movement away from the wall begins on the first acceleration frame");

                controller.Move(Vector3.forward);
                Set(movement,"velocity",new Vector3(2,0,5.5f));
                Move(movement,new Vector3(2,-3,5.5f)*Time.deltaTime,false);
                Check(Mathf.Abs(Momentum(movement).z)<.05f&&Mathf.Abs(Momentum(movement).x-2)<.05f,
                    "wall rejection preserves tangential sliding momentum");
                wall.SetActive(false);Physics.SyncTransforms();

                var curb=Box(root.transform,"Normal 20 cm step",origin+new Vector3(0,.1f,.6f),new Vector3(4,.2f,.8f));
                movement.Teleport(origin+Vector3.back*.06f);Physics.SyncTransforms();controller.Move(Vector3.down*.04f);
                controller.stepOffset=.3f;Grounded(movement,true);Set(movement,"velocity",Vector3.forward*2.15f);
                float beforeStep=hero.transform.position.z;
                var stepFlags=Move(movement,(Vector3.forward*2.15f-Vector3.up*3)*Time.deltaTime,true);
                Check((stepFlags&CollisionFlags.Below)!=0&&hero.transform.position.y>.1f,
                    "the real controller climbs a supported 20 cm step");
                Check(hero.transform.position.z>beforeStep&&Momentum(movement).z>2,
                    "a successful rising step retains its forward momentum after touching the riser");
                Check(movement.SurfaceSpeed<2.5f,"the step-up height cannot create an animation speed spike");
                curb.SetActive(false);Physics.SyncTransforms();

                movement.Teleport(origin+Vector3.right*5.8f);Physics.SyncTransforms();
                Set(movement,"velocity",Vector3.right*5.5f);
                Vector3 ledge=(Vector3)Invoke(movement,"ProtectLedge",Vector3.right*5.5f,Time.deltaTime);
                Check(ledge.sqrMagnitude<.0001f&&Momentum(movement).sqrMagnitude<.0001f,
                    "a protected ledge clears its blocked sprint momentum");
                Set(movement,"velocity",new Vector3(5.5f,0,2.15f));
                ledge=(Vector3)Invoke(movement,"ProtectLedge",new Vector3(5.5f,0,2.15f),Time.deltaTime);
                Check(Mathf.Abs(ledge.x)<.001f&&ledge.z>2&&Mathf.Abs(Momentum(movement).x)<.001f&&Momentum(movement).z>2,
                    "ledge protection preserves motion and momentum parallel to the edge");

                movement.Teleport(origin+Vector3.up*.28f);Grounded(movement,true);Physics.SyncTransforms();
                Set(movement,"velocity",Vector3.right*2.15f);
                var flags=Move(movement,Vector3.right*2.15f*Time.deltaTime-Vector3.up*.01f,true);
                Check((flags&CollisionFlags.Below)!=0&&movement.Grounded,"a normal 28 cm stair descent retains floor support");
                Check(hero.transform.position.y<.08f,"bounded ground snap settles the controller on the lower step");
                Check(movement.Speed>1.8f&&movement.Speed<2.4f,"the second snap Move does not erase horizontal motion");
                Check(movement.SurfaceSpeed>1.8f&&movement.SurfaceSpeed<2.4f,"vertical stair placement does not spike animation speed");
                Check(!movement.JumpedThisFrame&&!movement.LandedThisFrame,"ordinary step support does not invent a jump or landing event");

                movement.Teleport(origin+Vector3.up*.65f);Grounded(movement,true);Physics.SyncTransforms();
                flags=Move(movement,Vector3.down*.01f,true);
                Check((flags&CollisionFlags.Below)==0&&hero.transform.position.y>.55f,"ground snap cannot bridge a 65 cm ledge drop");
                movement.Teleport(origin+Vector3.up*.28f);Physics.SyncTransforms();
                float beforeRise=hero.transform.position.y;
                Move(movement,Vector3.up*.06f,false);
                Check(hero.transform.position.y>beforeRise+.04f,"an explicitly rising movement is not snapped to the floor");

                movement.Teleport(origin);Physics.SyncTransforms();controller.Move(Vector3.down*.02f);
                Grounded(movement,true);Set(movement,"lastGrounded",Time.time);Set(movement,"jumpAt",Time.time-.001f);
                Invoke(movement,"Update");
                Check(movement.JumpedThisFrame&&movement.VerticalSpeed>0&&!movement.Grounded,
                    "the real prepared-jump update remains airborne despite nearby step support");
                Check(hero.transform.position.y>origin.y+.01f,"the real jump moves the controller above its starting floor");

                foreach(float angle in new[]{15f,30f,44f})
                {
                    Vector3 normal=Quaternion.Euler(0,0,angle)*Vector3.up;
                    Vector3 tangent=(Vector3)Invoke(movement,"SurfaceMotion",Vector3.right*2.15f,normal);
                    Check(Mathf.Abs(tangent.magnitude-2.15f)<.0001f&&Mathf.Abs(Vector3.Dot(tangent,normal))<.0001f,
                        "walkable "+angle+" degree slope preserves requested speed along its surface");
                }
                floor.SetActive(false);
                var ramp=Box(root.transform,"Walkable slope",origin,new Vector3(6,.2f,6));
                ramp.transform.rotation=Quaternion.Euler(0,0,30);Physics.SyncTransforms();
                Check(Physics.Raycast(origin+new Vector3(.5f,3,0),Vector3.down,out var support,6,1),"real ramp has walkable floor support");
                movement.Teleport(support.point+Vector3.up*.01f);Physics.SyncTransforms();controller.Move(Vector3.down*.04f);
                Vector3 rampMotion=(Vector3)Invoke(movement,"SurfaceMotion",Vector3.right*2.15f,support.normal);
                Set(movement,"velocity",Vector3.right*2.15f);
                Move(movement,rampMotion*Time.deltaTime-Vector3.up*.002f,true);
                Check(movement.Grounded,"real slope travel keeps the controller supported");
                Check(movement.SurfaceSpeed>movement.Speed*1.05f&&movement.SurfaceSpeed<2.5f,
                    "surface gait speed measures the ramp travel instead of only its horizontal shadow");

                movement.SetExternalControl(true);
                Check(movement.Speed==0&&movement.SurfaceSpeed==0&&!movement.WantsMove&&!movement.WantsSprint,
                    "vehicle or seated ownership clears measured gait motion and intent");
                movement.SetExternalControl(false);movement.SetSwimming(true,0);
                Check(!movement.WantsMove&&!movement.WantsSprint&&movement.SurfaceSpeed==0,"swimming owns its separate movement response");
                movement.Teleport(origin);
                Check(movement.Speed==0&&movement.SurfaceSpeed==0,"checkpoint teleport cannot retain the previous gait speed");
                Debug.Log("Movement response and stairs passed: "+checks+" assertions using real Unity controller contacts. Animation and full traversal review remain required.");
            }
            catch(TargetInvocationException error){Debug.LogException(error.InnerException??error);throw;}
            finally
            {
                UnityEngine.Object.DestroyImmediate(root);Physics.SyncTransforms();Time.timeScale=oldTime;
                Cursor.lockState=oldLock;Cursor.visible=oldCursor;
            }
        }
    }
}
#endif
