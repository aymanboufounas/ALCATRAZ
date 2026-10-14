using UnityEngine;
using UnityEngine.InputSystem;
using DesertShift.Player;
using Blackstone.Supplied;

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
        public bool MeleeActive => Time.time < meleeUntil;
        Transform held, muzzle;
        float emptyNext, meleeUntil, meleeHitAt;
        bool meleePending;
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
            bool active=input!=null&&input.CanControl&&Time.deltaTime>0&&avatar!=null&&!avatar.seated&&(avatar.movement==null||!avatar.movement.ExternalControl);
            State.Tick(Time.deltaTime,active);
            if(flash!=null)flash.intensity=Time.time<flashUntil?2.6f:0;
            if(tracer!=null)tracer.enabled=Time.time<flashUntil;
            if(!active){meleePending=false;meleeUntil=0;return;}
            var key=Keyboard.current;var pad=Gamepad.current;
            if(key!=null)
            {
                if(key.digit1Key.wasPressedThisFrame)Equip(Equipment.Unarmed);
                if(key.digit2Key.wasPressedThisFrame)Equip(Equipment.Knife);
                if(key.digit3Key.wasPressedThisFrame)Equip(Equipment.Pistol);
                if(key.digit4Key.wasPressedThisFrame)Equip(Equipment.Rifle);
                if(key.digit5Key.wasPressedThisFrame)Equip(Equipment.Revolver);
            }
            if(pad!=null&&pad.dpad.left.wasPressedThisFrame)Equip((Equipment)(((int)State.Equipped+1)%11));
            if(Mouse.current!=null&&Mathf.Abs(Mouse.current.scroll.ReadValue().y)>.1f)
                Equip((Equipment)(((int)State.Equipped+(Mouse.current.scroll.ReadValue().y>0?1:10))%11));
            bool reload=key!=null&&key.rKey.wasPressedThisFrame||pad!=null&&pad.buttonNorth.wasPressedThisFrame;
            if(reload&&State.TryReload())Sound(State.IsAutomatic||State.Equipped==Equipment.BRX1?"ReloadRifle":"ReloadPistol");
            bool heldTrigger=Mouse.current!=null&&Mouse.current.leftButton.isPressed||pad!=null&&pad.rightTrigger.isPressed;
            bool pressed=input.AttackPressed;
            if(pressed&&State.Equipped==Equipment.Unarmed)
            {var boxing=GetComponent<FoundationBoxing>();if(boxing!=null)boxing.Punch();}
            else if((State.IsAutomatic?heldTrigger:pressed)&&State.TryUse())
            {if(State.IsFirearm)Fire();else Melee();}
            else if(pressed&&State.IsFirearm&&State.Magazine==0&&!State.Reloading&&Time.time>emptyNext)
            {emptyNext=Time.time+.35f;Sound("Empty");}
            if(meleePending&&Time.time>=meleeHitAt)
            {meleePending=false;if(Time.time<meleeUntil&&(State.Equipped==Equipment.Knife||State.Equipped==Equipment.Machete))MeleeContact();}
        }
        public void Equip(Equipment value)
        {
            if(value!=Equipment.Unarmed)
            {
                if(avatar==null||avatar.rightHand==null)return;
                GameObject asset=value==Equipment.Pistol||value==Equipment.Revolver
                    ?SuppliedModel.Load(value==Equipment.Pistol?"Pistol10mm":"Revolver")
                    :Resources.Load<GameObject>((int)value>=5?"AlcatrazExtras/"+value+"/"+value:"BlackstoneFoundation/Weapons/"+value);
                if(asset==null){Debug.LogError("Missing weapon: "+value+". Keeping current equipment.");return;}
            }
            if(!State.Equip(value))return;
            meleePending=false;meleeUntil=0;
            if(held!=null)Destroy(held.gameObject);held=null;muzzle=null;
            if(value!=Equipment.Unarmed&&avatar.rightHand!=null)
            {
                if(value==Equipment.Pistol||value==Equipment.Revolver||(int)value>=5)EquipSupplied(value);
                else
                {
                    var asset=Resources.Load<GameObject>("BlackstoneFoundation/Weapons/"+value);
                    if(asset!=null){held=Instantiate(asset,avatar.rightHand,false).transform;muzzle=held.Find("Muzzle");}
                }
            }
            Sound("Draw");
        }
        void EquipSupplied(Equipment value)
        {
            held=new GameObject("Equipped "+value).transform;held.SetParent(avatar.rightHand,false);held.rotation=Quaternion.identity;
            GameObject model;
            if((int)value>=5){var asset=Resources.Load<GameObject>("AlcatrazExtras/"+value+"/"+value);if(asset==null){Debug.LogError("Missing weapon: "+value);Destroy(held.gameObject);held=null;return;}model=Instantiate(asset,held,false);}
            else model=SuppliedModel.Create(value==Equipment.Pistol?"Pistol10mm":"Revolver",held);
            var bounds=SuppliedModel.Bounds(model);Vector3 axis=bounds.size.y>Mathf.Max(bounds.size.x,bounds.size.z)?Vector3.up:bounds.size.z>=bounds.size.x?Vector3.forward:Vector3.right;
            Renderer barrel=null,gripPart=null;
            if(value==Equipment.Machete||value==Equipment.BRX1)foreach(var renderer in model.GetComponentsInChildren<Renderer>()){if(renderer.name.StartsWith(value+"_M"+(value==Equipment.Machete?0:2)+"_"))barrel=renderer;if(renderer.name.StartsWith(value+"_M"+(value==Equipment.Machete?1:0)+"_"))gripPart=renderer;}
            if(barrel!=null&&gripPart!=null)axis=(barrel.bounds.center-gripPart.bounds.center).normalized;
            foreach(var renderer in model.GetComponentsInChildren<Renderer>())
                if(renderer.name.ToLowerInvariant().Contains("barrel")||renderer.name=="Slide"){barrel=renderer;break;}
            if(gripPart==null&&barrel!=null&&Vector3.Dot(barrel.bounds.center-bounds.center,axis)<0)axis=-axis;
            model.transform.rotation=Quaternion.FromToRotation(axis,Vector3.forward);
            bounds=SuppliedModel.Bounds(model);model.transform.localScale*=(value==Equipment.Pistol||value==Equipment.M9A3||value==Equipment.PX4?.23f:value==Equipment.Revolver?.32f:value==Equipment.Machete?.58f:value==Equipment.PMX?.58f:1.0f)/Mathf.Max(.001f,bounds.size.z);
            bounds=SuppliedModel.Bounds(model);
            Vector3 grip=value==Equipment.Machete&&gripPart!=null?gripPart.bounds.center:new Vector3(bounds.center.x,bounds.min.y+bounds.size.y*.40f,bounds.min.z+bounds.size.z*.25f);
            model.transform.position+=held.position-grip;
            bounds=SuppliedModel.Bounds(model);muzzle=new GameObject("Muzzle").transform;muzzle.SetParent(held);
            muzzle.position=new Vector3(bounds.center.x,bounds.max.y-bounds.size.y*.15f,bounds.max.z);
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
            if(FoundationAudio.Instance!=null)FoundationAudio.Instance.Variation(State.IsAutomatic||State.Equipped==Equipment.BRX1?"Rifle":"Pistol",origin,.8f);
            if(cameraRig!=null)cameraRig.Recoil(State.Equipped==Equipment.Revolver?2.3f:State.Equipped==Equipment.Pistol?1.8f:.7f);
            if(flash!=null)flash.transform.position=origin;
            flashUntil=Time.time+.04f;
            if(tracer!=null){tracer.SetPosition(0,origin);tracer.SetPosition(1,end);}
        }
        void Melee()
        {
            meleeUntil=Time.time+.35f;
            meleeHitAt=Time.time+.16f;meleePending=true;
            if(FoundationAudio.Instance!=null)FoundationAudio.Instance.Named("Handling","Swing",transform.position+Vector3.up,.5f);
        }
        void MeleeContact()
        {
            var view=Camera.main;
            if(view==null)return;
            float crouch=avatar.movement!=null&&avatar.movement.IsCrouching?.32f:0;
            Vector3 origin=transform.position+Vector3.up*(1.2f-crouch);
            Collider closest=null;Vector3 point=origin;float distance=float.PositiveInfinity;
            foreach(var shape in Physics.OverlapSphere(origin,.18f,~(1<<8),QueryTriggerInteraction.Ignore))
            {
                if(shape.transform.IsChildOf(transform))continue;
                Vector3 p=shape.ClosestPoint(origin);float d=(p-origin).sqrMagnitude;
                if(d<distance){distance=d;closest=shape;point=p;}
            }
            if(closest!=null){Impact(closest,point);return;}
            if(Physics.SphereCast(origin,.18f,view.transform.forward,out var hit,1.7f,~(1<<8),QueryTriggerInteraction.Ignore))Impact(hit);
        }
        void Impact(RaycastHit hit)
        {Impact(hit.collider,hit.point);}
        void Impact(Collider collider,Vector3 point)
        {
            var target=collider.GetComponentInParent<FoundationTarget>();
            if(target!=null){target.Hit();RegisterHit();}
            var victim=collider.GetComponentInParent<FoundationDamageable>();
            var view=Camera.main;Vector3 direction=view!=null?view.transform.forward:transform.forward;
            if(victim!=null&&!victim.transform.IsChildOf(transform)&&victim.Damage(CombatHealth.WeaponDamage(State.Equipped),point,direction*3))
            {RegisterHit();}
            if(FoundationAudio.Instance!=null)FoundationAudio.Instance.Variation("Impact",point,.45f);
        }
        public void RegisterHit(){Hits++;HitMarkerUntil=Time.time+.18f;}
        public void PoseHands(FoundationAvatar body)
        {
            var view=Camera.main;if(view==null)return;
            if(State.IsFirearm&&held!=null)
            {
                Vector3 forward=view.transform.forward;
                float dip=State.Reloading?Mathf.Sin(State.ReloadProgress*Mathf.PI):0;
                float crouch=body.movement!=null&&body.movement.IsCrouching?.32f:0;
                Vector3 grip=transform.position+Vector3.up*(1.25f-.22f*dip-crouch)+transform.right*.23f+forward*.33f;
                FoundationAvatar.Solve(body.rightArm,body.rightForearm,body.rightHand,grip,-transform.right,.95f);
                held.position=body.rightHand.position;
                held.rotation=Quaternion.LookRotation(forward,Vector3.up)*Quaternion.Euler(22*dip,0,0);
                if(State.IsAutomatic||State.Equipped==Equipment.BRX1)
                    FoundationAvatar.Solve(body.leftArm,body.leftForearm,body.leftHand,held.TransformPoint(new Vector3(-.055f,-.02f,.26f)),transform.right,.95f);
            }
            else if(Time.time<meleeUntil&&body.rightArm!=null)
            {
                float t=1-(meleeUntil-Time.time)/.35f;
                float crouch=body.movement!=null&&body.movement.IsCrouching?.32f:0;
                Vector3 target=transform.position+Vector3.up*(1.3f-crouch)+view.transform.forward*(.35f+.38f*Mathf.Sin(t*Mathf.PI));
                FoundationAvatar.Solve(body.rightArm,body.rightForearm,body.rightHand,target,-transform.right,.95f);
            }
            if((State.Equipped==Equipment.Knife||State.Equipped==Equipment.Machete)&&held!=null)
            {held.localPosition=Vector3.zero;held.localRotation=Quaternion.Euler(90,0,0);}
        }
        void OnDestroy(){if(tracerMaterial!=null)Destroy(tracerMaterial);}
    }
}
