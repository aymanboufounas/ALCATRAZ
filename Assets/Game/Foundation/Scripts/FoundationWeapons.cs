using UnityEngine;
using UnityEngine.InputSystem;
using DesertShift.Player;

namespace Blackstone.Foundation
{
    public sealed class FoundationWeapons : MonoBehaviour
    {
        public PlayerInputHandler input;
        public FoundationCamera cameraRig;
        public FoundationAvatar avatar;
        public readonly WeaponState State=new WeaponState();
        public int Hits { get; private set; }
        public float HitMarkerUntil { get; private set; }
        Transform held, muzzle;
        float emptyNext, meleeUntil;
        Light flash;
        LineRenderer tracer;
        Material tracerMaterial;
        float flashUntil;

        void Start()
        {
            var go=new GameObject("Muzzle light");go.transform.SetParent(transform,false);flash=go.AddComponent<Light>();
            flash.type=LightType.Point;flash.color=new Color(1,.64f,.25f);flash.range=2.8f;flash.intensity=0;
            tracer=go.AddComponent<LineRenderer>();tracer.positionCount=2;tracer.startWidth=.008f;tracer.endWidth=.003f;
            var shader=Shader.Find("Universal Render Pipeline/Unlit");
            if(shader!=null){tracerMaterial=new Material(shader);tracerMaterial.color=new Color(1,.72f,.28f);tracer.sharedMaterial=tracerMaterial;}
            tracer.enabled=false;
        }
        void Update()
        {
            bool active=input!=null&&input.CanControl&&Time.deltaTime>0;
            State.Tick(Time.deltaTime,active);
            if(flash!=null)flash.intensity=Time.time<flashUntil?2.6f:0;
            if(tracer!=null)tracer.enabled=Time.time<flashUntil;
            if(!active)return;
            var key=Keyboard.current;var pad=Gamepad.current;
            if(key!=null)
            {
                if(key.digit1Key.wasPressedThisFrame)Equip(Equipment.Unarmed);
                if(key.digit2Key.wasPressedThisFrame)Equip(Equipment.Knife);
                if(key.digit3Key.wasPressedThisFrame)Equip(Equipment.Pistol);
                if(key.digit4Key.wasPressedThisFrame)Equip(Equipment.Rifle);
            }
            if(pad!=null&&pad.dpad.left.wasPressedThisFrame)Equip((Equipment)(((int)State.Equipped+1)%4));
            bool reload=key!=null&&key.rKey.wasPressedThisFrame||pad!=null&&pad.buttonNorth.wasPressedThisFrame;
            if(reload&&State.TryReload())Sound(State.Equipped==Equipment.Pistol?"ReloadPistol":"ReloadRifle");
            bool heldTrigger=Mouse.current!=null&&Mouse.current.leftButton.isPressed||pad!=null&&pad.rightTrigger.isPressed;
            bool pressed=input.AttackPressed;
            if((State.Equipped==Equipment.Rifle?heldTrigger:pressed)&&State.TryUse())
            {if(State.IsFirearm)Fire();else Melee();}
            else if(pressed&&State.IsFirearm&&State.Magazine==0&&!State.Reloading&&Time.time>emptyNext)
            {emptyNext=Time.time+.35f;Sound("Empty");}
        }
        void Equip(Equipment value)
        {
            if(!State.Equip(value))return;
            if(held!=null)Destroy(held.gameObject);held=null;muzzle=null;
            if(value!=Equipment.Unarmed&&avatar.rightHand!=null)
            {
                var asset=Resources.Load<GameObject>("BlackstoneFoundation/Weapons/"+value);
                if(asset!=null){held=Instantiate(asset,avatar.rightHand,false).transform;muzzle=held.Find("Muzzle");}
            }
            Sound("Draw");
        }
        void Sound(string name)
        {if(FoundationAudio.Instance!=null)FoundationAudio.Instance.Named("Handling",name,transform.position+Vector3.up*1.2f,.6f);}
        void Fire()
        {
            var view=Camera.main;if(view==null)return;
            Ray aim=view.ViewportPointToRay(new Vector3(.5f,.5f,0));Vector3 end=aim.origin+aim.direction*90;
            if(Physics.Raycast(aim,out var aimed,90,~(1<<8),QueryTriggerInteraction.Ignore))end=aimed.point;
            Vector3 origin=muzzle!=null?muzzle.position:transform.position+Vector3.up*1.2f;
            RaycastHit hit;bool struck;
            Vector3 chest=transform.position+Vector3.up*1.15f;
            if(Physics.Linecast(chest,origin,out var barrier,~(1<<8),QueryTriggerInteraction.Ignore))
            {hit=barrier;struck=true;end=barrier.point;origin=chest;}
            else
            {
                Vector3 delta=end-origin;struck=Physics.Raycast(origin,delta.normalized,out hit,delta.magnitude+.05f,~(1<<8),QueryTriggerInteraction.Ignore);
                if(struck)end=hit.point;
            }
            if(struck)Impact(hit);
            if(FoundationAudio.Instance!=null)FoundationAudio.Instance.Variation(State.Equipped==Equipment.Pistol?"Pistol":"Rifle",origin,.8f);
            if(cameraRig!=null)cameraRig.Recoil(State.Equipped==Equipment.Pistol?1.8f:.7f);
            if(flash!=null)flash.transform.position=origin;
            flashUntil=Time.time+.04f;
            if(tracer!=null){tracer.SetPosition(0,origin);tracer.SetPosition(1,end);}
        }
        void Melee()
        {
            meleeUntil=Time.time+.35f;
            if(FoundationAudio.Instance!=null)FoundationAudio.Instance.Variation("Punch",transform.position+Vector3.up,.5f);
            var view=Camera.main;
            if(view!=null&&Physics.SphereCast(transform.position+Vector3.up*1.2f,.18f,view.transform.forward,out var hit,1.7f,~(1<<8),QueryTriggerInteraction.Ignore))Impact(hit);
        }
        void Impact(RaycastHit hit)
        {
            var target=hit.collider.GetComponentInParent<FoundationTarget>();
            if(target!=null){target.Hit();Hits++;HitMarkerUntil=Time.time+.18f;}
            if(FoundationAudio.Instance!=null)FoundationAudio.Instance.Variation("Impact",hit.point,.45f);
        }
        public void PoseHands(FoundationAvatar body)
        {
            var view=Camera.main;if(view==null)return;
            if(State.IsFirearm&&held!=null)
            {
                Vector3 forward=view.transform.forward;
                float dip=State.Reloading?Mathf.Sin(State.ReloadProgress*Mathf.PI):0;
                Vector3 grip=transform.position+Vector3.up*(1.25f-.22f*dip)+transform.right*.23f+forward*.33f;
                FoundationAvatar.Solve(body.rightArm,body.rightForearm,body.rightHand,grip,-transform.right,.95f);
                held.position=body.rightHand.position;
                held.rotation=Quaternion.LookRotation(forward,Vector3.up)*Quaternion.Euler(22*dip,0,0);
                if(State.Equipped==Equipment.Rifle)
                    FoundationAvatar.Solve(body.leftArm,body.leftForearm,body.leftHand,held.TransformPoint(new Vector3(-.055f,-.02f,.26f)),transform.right,.95f);
            }
            else if(Time.time<meleeUntil&&body.rightArm!=null)
            {
                float t=1-(meleeUntil-Time.time)/.35f;
                Vector3 target=transform.position+Vector3.up*1.3f+view.transform.forward*(.35f+.38f*Mathf.Sin(t*Mathf.PI));
                FoundationAvatar.Solve(body.rightArm,body.rightForearm,body.rightHand,target,-transform.right,.95f);
            }
            if(State.Equipped==Equipment.Knife&&held!=null)
            {held.localPosition=Vector3.zero;held.localRotation=Quaternion.Euler(90,0,0);}
        }
        void OnDestroy(){if(tracerMaterial!=null)Destroy(tracerMaterial);}
    }
}
