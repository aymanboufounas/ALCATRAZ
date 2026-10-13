using UnityEngine;
using DesertShift.Player;
using UnityEngine.InputSystem;

namespace Blackstone.Foundation
{
    [RequireComponent(typeof(Rigidbody))]
    public sealed class FoundationVehicle : MonoBehaviour
    {
        public bool aircraft;
        public Transform rotor,tailRotor;
        public Vector3 seat=new Vector3(0,1.2f,0);
        public static FoundationVehicle Active { get; private set; }
        public string Notice { get; private set; }
        Rigidbody body; PlayerMovement player;PlayerInputHandler input;FoundationAvatar avatar;FoundationCamera cameraRig;
        Transform cameraFocus;
        Renderer[] passengerRenderers;bool[] previousVisibility;
        float targetHeight, rotorSpeed;Vector2 controls;float lift;
        const float Sea=-.15f;
        void Start()
        {
            body=GetComponent<Rigidbody>();body.mass=aircraft?1100:700;body.linearDamping=aircraft?.7f:1.4f;body.angularDamping=3;
            body.interpolation=RigidbodyInterpolation.Interpolate;body.collisionDetectionMode=CollisionDetectionMode.ContinuousDynamic;
            body.centerOfMass=new Vector3(0,aircraft?.45f:-.35f,0);
            player=FindFirstObjectByType<PlayerMovement>();if(player==null)return;
            input=player.GetComponent<PlayerInputHandler>();avatar=player.GetComponent<FoundationAvatar>();cameraRig=FindFirstObjectByType<FoundationCamera>();
            cameraFocus=new GameObject("Vehicle camera focus").transform;cameraFocus.SetParent(transform,false);cameraFocus.localPosition=Vector3.up*(aircraft?1.8f:1);
            foreach(var t in GetComponentsInChildren<Transform>())t.gameObject.layer=11;
        }
        void Update()
        {
            if(player==null||input==null||Time.deltaTime<=0)return;
            if(Active==this)
            {
                controls=input.CanControl?input.Move:Vector2.zero;
                lift=VehicleControlRules.Lift(input.CanControl,
                    Keyboard.current!=null&&Keyboard.current.spaceKey.isPressed,
                    Keyboard.current!=null&&Keyboard.current.leftCtrlKey.isPressed,
                    Gamepad.current!=null&&Gamepad.current.buttonSouth.isPressed,
                    Gamepad.current!=null&&Gamepad.current.buttonEast.isPressed);
                if(input.InteractPressed)TryExit();
            }
            else if(Active==null && !player.ExternalControl && input.CanControl && Vector3.Distance(player.transform.position,transform.position)<4 && input.InteractPressed)Board();
            rotorSpeed=Mathf.MoveTowards(rotorSpeed,Active==this?1400:0,400*Time.deltaTime);
            if(rotor!=null)rotor.Rotate(Vector3.up,rotorSpeed*Time.deltaTime,Space.Self);
            if(tailRotor!=null)tailRotor.Rotate(Vector3.right,rotorSpeed*1.5f*Time.deltaTime,Space.Self);
        }
        void Board()
        {
            Active=this;player.SetExternalControl(true);targetHeight=transform.position.y;
            passengerRenderers=avatar!=null?avatar.model.GetComponentsInChildren<Renderer>():new Renderer[0];previousVisibility=new bool[passengerRenderers.Length];
            for(int i=0;i<passengerRenderers.Length;i++){previousVisibility[i]=passengerRenderers[i].enabled;passengerRenderers[i].enabled=false;}
            if(avatar!=null)avatar.seated=true;
            if(cameraRig!=null){cameraRig.FollowOverride=cameraFocus;cameraRig.FollowDistance=aircraft?9:7;}
            Notice=aircraft?"W/S pitch · A/D yaw · Space rise · Ctrl descend · E exit after landing":"W/S throttle · A/D rudder · E leave at the dock";
        }
        void FixedUpdate()
        {
            if(body==null)return;
            if(aircraft)
            {
                if(Active!=this)return;
                targetHeight=Mathf.Clamp(targetHeight+lift*6*Time.fixedDeltaTime,Sea+.6f,180);
                // Spring-controlled collective counters gravity; pitch adds forward acceleration.
                float collective=Mathf.Clamp((targetHeight-transform.position.y)*3-body.linearVelocity.y*2.2f,-7,14);
                body.AddForce(Vector3.up*(9.81f+collective),ForceMode.Acceleration);
                body.AddForce(Vector3.ProjectOnPlane(transform.forward,Vector3.up).normalized*controls.y*7,ForceMode.Acceleration);
                body.AddTorque(Vector3.up*controls.x*2.4f,ForceMode.Acceleration);
                Quaternion wanted=Quaternion.Euler(controls.y*12,transform.eulerAngles.y,-controls.x*8);
                Stabilize(wanted,5);
            }
            else
            {
                Vector3[] floats={new Vector3(-.85f,0,1.6f),new Vector3(.85f,0,1.6f),new Vector3(-.85f,0,-1.6f),new Vector3(.85f,0,-1.6f)};
                foreach(var f in floats)
                {
                    Vector3 p=transform.TransformPoint(f);float wave=Mathf.Sin(Time.time*.7f+p.x*.04f)*.08f;
                    float depth=Sea+wave+.35f-p.y;
                    float force=Mathf.Clamp(depth*35-body.GetPointVelocity(p).y*6,0,25);
                    body.AddForceAtPosition(Vector3.up*force*body.mass/4,p);
                }
                if(Active==this){body.AddForce(transform.forward*controls.y*5,ForceMode.Acceleration);body.AddTorque(transform.up*controls.x*Mathf.Clamp(body.linearVelocity.magnitude,.5f,5)*.65f,ForceMode.Acceleration);}
                body.AddForce(-transform.right*Vector3.Dot(body.linearVelocity,transform.right)*2,ForceMode.Acceleration);
            }
        }
        void Stabilize(Quaternion target,float gain)
        {
            Quaternion delta=target*Quaternion.Inverse(transform.rotation);delta.ToAngleAxis(out float angle,out Vector3 axis);if(angle>180)angle-=360;
            if(axis.sqrMagnitude>.01f)body.AddTorque(axis*angle*Mathf.Deg2Rad*gain-body.angularVelocity*2,ForceMode.Acceleration);
        }
        void LateUpdate()
        {if(Active==this&&player!=null)player.transform.SetPositionAndRotation(transform.TransformPoint(seat),Quaternion.Euler(0,transform.eulerAngles.y,0));}
        void TryExit()
        {
            if(body.linearVelocity.magnitude>1.4f){Notice="Stop before leaving the vehicle.";return;}
            for(int spot=0;spot<4;spot++)
            {
                Vector3 offset=spot<2?transform.right*(spot==0?-1:1)*(aircraft?2.3f:2):transform.forward*(spot==2?1:-1)*(aircraft?4.5f:3.5f);
                Vector3 origin=transform.position+offset+Vector3.up*2.5f;
                if(!Physics.Raycast(origin,Vector3.down,out var hit,4,~((1<<8)|(1<<10)|(1<<11)),QueryTriggerInteraction.Ignore)||hit.normal.y<.6f||hit.point.y<Sea+.2f)continue;
                Vector3 exit=hit.point+Vector3.up*.06f;
                if(Physics.CheckCapsule(exit+Vector3.up*.32f,exit+Vector3.up*1.5f,.24f,~((1<<8)|(1<<10)),QueryTriggerInteraction.Ignore))continue;
                Release();player.Teleport(exit);return;
            }
            Notice=aircraft?"Land beside clear ground to leave.":"Bring the boat alongside the dock to leave.";
        }
        void Release()
        {
            Active=null;if(player!=null)player.SetExternalControl(false);if(avatar!=null)avatar.seated=false;
            if(passengerRenderers!=null)for(int i=0;i<passengerRenderers.Length;i++)if(passengerRenderers[i]!=null)passengerRenderers[i].enabled=previousVisibility[i];
            if(cameraRig!=null){cameraRig.FollowOverride=null;cameraRig.FollowDistance=3.15f;cameraRig.SnapToPlayer();}
        }
        void OnDisable(){if(Active==this)Release();}
        void OnGUI()
        {
            if(input==null||!input.CanControl)return;
            if(Active!=this&&(Active!=null||player.ExternalControl||Vector3.Distance(player.transform.position,transform.position)>=4))return;
            var r=new Rect(Screen.width*.25f,Screen.height-100,Screen.width*.5f,60);
            var style=new GUIStyle(GUI.skin.box){fontSize=18,wordWrap=true,alignment=TextAnchor.MiddleCenter};GUI.Box(r,Active==this?Notice:"E / X   BOARD "+(aircraft?"HELICOPTER":"PATROL BOAT"),style);
        }
    }
}
