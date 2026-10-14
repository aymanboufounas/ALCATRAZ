using UnityEngine;
using DesertShift.Player;
using Blackstone.Actors;

namespace Blackstone.Foundation
{
    [DefaultExecutionOrder(150)]
    public sealed class FoundationBoxing : MonoBehaviour
    {
        public FoundationAvatar avatar;
        float health=100;
        public float Health { get {return !Sparring&&damageable!=null?damageable.Health:health;} private set {health=value;} }
        public float Stamina { get; private set; }=100;
        public bool Sparring { get; private set; }
        public bool Guarding { get; private set; }
        FoundationBoxing opponent;FoundationFall fall;FoundationAgent agent;PlayerInputHandler input;FoundationDamageable damageable;
        float started=-10, duration=.48f,nextAttack,stopAt,hitAt;int combo;bool connected;
        void Start(){avatar=GetComponent<FoundationAvatar>();fall=GetComponent<FoundationFall>();agent=GetComponent<FoundationAgent>();input=GetComponent<PlayerInputHandler>();damageable=GetComponent<FoundationDamageable>();}
        bool Available=>avatar!=null && avatar.animator!=null && avatar.animator.enabled && !avatar.seated
            && (input==null||input.CanControl) && (avatar.movement==null||avatar.movement.Grounded&&!avatar.movement.ExternalControl);
        bool FistsReady=>input==null||avatar.equipment!=null&&avatar.equipment.State.Equipped==Equipment.Unarmed;
        public void Punch()
        {
            if(!Available||!FistsReady||Time.time<nextAttack)return;
            int nextCombo=started<0||Time.time>nextAttack+1.1f?0:(combo+1)%3;
            float cost=CombatHealth.PunchStaminaCost(nextCombo);
            if(Stamina<cost)return;
            combo=nextCombo;
            duration=combo==0?.42f:combo==1?.55f:.64f;started=Time.time;nextAttack=Time.time+duration;hitAt=Time.time+duration*.43f;connected=false;
            Stamina-=cost;
            if(FoundationAudio.Instance!=null)FoundationAudio.Instance.Variation("Punch",transform.position+Vector3.up*1.3f,.4f);
        }
        void Update()
        {
            if(avatar==null)return;
            if(Time.deltaTime<=0)
            {if(input!=null&&!input.CanControl){Guarding=false;connected=true;started=-10;}return;}
            bool ready=Available&&FistsReady;
            if(!ready)Guarding=false;
            Stamina=Mathf.MoveTowards(Stamina,100,(Guarding?8:18)*Time.deltaTime);
            if(!ready){connected=true;started=-10;return;}
            if(fall!=null&&fall.Active)return;
            if(input!=null){Guarding=input.CanControl&&input.Aim&&avatar.equipment!=null&&avatar.equipment.State.Equipped==Equipment.Unarmed;}
            else if(Sparring&&opponent!=null)
            {
                avatar.agentSpeed=0;
                if(Time.time>stopAt||opponent.Health<=0){EndSpar();return;}
                Vector3 delta=opponent.transform.position-transform.position;delta.y=0;
                if(delta.sqrMagnitude>.1f)transform.rotation=Quaternion.Slerp(transform.rotation,Quaternion.LookRotation(delta),5*Time.deltaTime);
                Guarding=Stamina>25&&Mathf.Sin(Time.time*2.4f)>.05f;
                if(delta.magnitude>1.15f&&delta.magnitude<6 && !Physics.CapsuleCast(transform.position+Vector3.up*.4f,transform.position+Vector3.up*1.4f,.25f,delta.normalized,.2f,1,QueryTriggerInteraction.Ignore))
                {transform.position+=delta.normalized*.65f*Time.deltaTime;avatar.agentSpeed=.65f;}
                if(delta.magnitude<1.55f&&Time.time>nextAttack+.45f){Guarding=false;Punch();}
            }
            else if(input==null)
            {
                var actor=GetComponent<PrisonActor>();if(actor==null||actor.displayName!="Tomas")return;
                var player=FindFirstObjectByType<PlayerMovement>();
                if(player!=null&&Vector3.Distance(player.transform.position,transform.position)<2.1f&&player.GetComponent<PlayerInputHandler>().InteractPressed)
                {var boxer=player.GetComponent<FoundationBoxing>();if(boxer!=null&&avatar.storyActor==null)BeginSpar(boxer);}
            }
            if(!connected&&Time.time>=hitAt&&Time.time<started+duration){connected=true;Contact();}
            if(Sparring&&Health<=0){EndSpar();Health=100;}
        }
        void BeginSpar(FoundationBoxing other)
        {opponent=other;Sparring=other.Sparring=true;other.opponent=this;stopAt=Time.time+45;Health=other.Health=100;if(agent!=null)agent.enabled=false;}
        void EndSpar(){Sparring=false;Guarding=false;if(opponent!=null){opponent.Sparring=false;opponent.opponent=null;}opponent=null;if(agent!=null)agent.enabled=damageable==null||!damageable.Dead;}
        public void StopCombat(){connected=true;started=-10;EndSpar();enabled=false;}
        void Contact()
        {
            float crouch=avatar.movement!=null&&avatar.movement.IsCrouching?.32f:0;
            Vector3 origin=transform.position+Vector3.up*(1.25f-crouch);Vector3 direction=transform.forward;
            var hits=Physics.OverlapSphere(origin+direction*.65f,.58f,~(1<<10),QueryTriggerInteraction.Ignore);
            Collider chosen=null;float nearest=3;
            foreach(var shape in hits)
            {
                if(shape.transform.IsChildOf(transform))continue;
                var target=shape.GetComponentInParent<FoundationBoxing>();var bag=shape.GetComponentInParent<FoundationPunchingBag>();
                var victim=shape.GetComponentInParent<FoundationDamageable>();
                var practice=shape.GetComponentInParent<FoundationTarget>();
                if(target==null&&bag==null&&practice==null&&(victim==null||victim.Dead))continue;
                Vector3 point=shape.ClosestPoint(origin+direction*.9f);float distance=Vector3.Distance(origin,point);
                if(distance>1.2f||distance>=nearest||Vector3.Dot(direction,(shape.bounds.center-origin).normalized)<.25f)continue;
                if(Physics.Linecast(origin,point,out var wall,1,QueryTriggerInteraction.Ignore)&&wall.collider!=shape&&!wall.transform.IsChildOf(shape.transform))continue;
                chosen=shape;nearest=distance;
            }
            if(chosen==null)return;
            bool hit=false;
            var fighter=chosen.GetComponentInParent<FoundationBoxing>();if(fighter!=null)hit=fighter.Receive(this,combo==0?9:combo==1?17:21);
            else
            {
                var victim=chosen.GetComponentInParent<FoundationDamageable>();
                if(victim!=null)hit=victim.Damage(combo==0?9:combo==1?17:21,origin+direction*.8f,direction*3);
            }
            var punchingBag=chosen.GetComponentInParent<FoundationPunchingBag>();if(punchingBag!=null){punchingBag.Hit(direction*(combo==0?12:22),origin+direction);hit=true;}
            var practiceTarget=chosen.GetComponentInParent<FoundationTarget>();if(practiceTarget!=null){practiceTarget.Hit();hit=true;}
            if(!hit)return;
            if(avatar.equipment!=null)avatar.equipment.RegisterHit();
            if(FoundationAudio.Instance!=null)FoundationAudio.Instance.Variation("Impact",origin+direction*.8f,.55f);
        }
        bool Receive(FoundationBoxing attacker,float damage)
        {
            if(!Available)return false;
            bool blocked=Guarding&&Stamina>10&&Vector3.Dot(transform.forward,(attacker.transform.position-transform.position).normalized)>.25f;
            if(blocked){Stamina=Mathf.Max(0,Stamina-damage);damage*=.15f;}
            else{started=-10;nextAttack=Time.time+.35f;}
            if(!Sparring&&damageable!=null&&!damageable.Damage(damage,avatar.chest!=null?avatar.chest.position:transform.position+Vector3.up,attacker.transform.forward*3+Vector3.up*.4f))return false;
            if(Sparring||damageable==null)Health=Mathf.Max(0,Health-damage);
            if(Health<=0&&fall!=null)fall.KnockDown(attacker.transform.forward*3+Vector3.up*.4f);
            return true;
        }
        void LateUpdate()
        {
            if(!Available||avatar.seated)return;
            bool fists=input==null?Sparring:avatar.equipment!=null&&avatar.equipment.State.Equipped==Equipment.Unarmed;
            if(!fists||(!Guarding&&!Sparring&&Time.time>=started+duration))return;
            float t=Mathf.Clamp01((Time.time-started)/duration);float extension=Mathf.Sin(Mathf.Clamp01((t-.13f)/.68f)*Mathf.PI);
            if(Time.time>=started+duration)extension=0;
            bool left=combo!=1;
            float crouch=avatar.movement!=null&&avatar.movement.IsCrouching?.32f:0;
            Vector3 center=transform.position+Vector3.up*((Guarding?1.52f:1.36f)-crouch),forward=transform.forward,right=transform.right;
            Vector3 l=center-right*.2f+forward*.27f,r=center+right*.2f+forward*.27f;
            Vector3 punch=center+forward*(.32f+.5f*extension)+(combo==2?right*(.26f-.5f*extension):Vector3.zero);
            if(extension>0){if(left)l=punch;else r=punch;}
            FoundationAvatar.Solve(avatar.leftArm,avatar.leftForearm,avatar.leftHand,l,-right,.95f);
            FoundationAvatar.Solve(avatar.rightArm,avatar.rightForearm,avatar.rightHand,r,right,.95f);
            if(avatar.chest!=null)avatar.chest.rotation=Quaternion.AngleAxis((left?-1:1)*extension*12,Vector3.up)*avatar.chest.rotation;
        }
        void OnGUI()
        {
            if(input==null&&!Sparring&&avatar!=null&&avatar.storyActor==null)
            {var actor=GetComponent<PrisonActor>();var player=FindFirstObjectByType<PlayerMovement>();if(actor!=null&&actor.displayName=="Tomas"&&player!=null&&Vector3.Distance(player.transform.position,transform.position)<2.1f&&player.GetComponent<PlayerInputHandler>().CanControl)GUI.Box(new Rect(Screen.width/2-210,Screen.height-190,420,40),"E / X   BOXING PRACTICE WITH TOMAS");return;}
            if(!Sparring||input==null||!input.CanControl)return;
            GUI.Box(new Rect(Screen.width/2-210,95,420,60),"BOXING   Health "+Mathf.CeilToInt(Health)+"   Stamina "+Mathf.CeilToInt(Stamina)+"\nLMB: jab / cross / hook   RMB: guard");
        }
    }
}
