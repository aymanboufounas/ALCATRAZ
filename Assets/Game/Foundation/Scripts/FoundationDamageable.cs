using UnityEngine;
using Blackstone.Actors;

namespace Blackstone.Foundation
{
    public sealed class FoundationDamageable : MonoBehaviour
    {
        readonly CombatHealth state = new CombatHealth();
        public float Health => state.Health;
        public bool Dead => state.Dead;
        Renderer[] renderers;
        MaterialPropertyBlock[] original, flash;
        float flashUntil;
        bool flashing;
        void Awake()
        {
            renderers=GetComponentsInChildren<Renderer>();
            original=new MaterialPropertyBlock[renderers.Length];flash=new MaterialPropertyBlock[renderers.Length];
            for(int i=0;i<renderers.Length;i++){original[i]=new MaterialPropertyBlock();flash[i]=new MaterialPropertyBlock();}
        }
        public bool Damage(float amount,Vector3 point,Vector3 impulse)
        {
            var player=GetComponent<FoundationPlayerVitals>();
            if(player!=null&&!player.CanTakeDamage)return false;
            if(!state.Damage(amount))return false;
            for(int i=0;i<renderers.Length;i++)
            {
                if(renderers[i]==null)continue;
                if(!flashing)renderers[i].GetPropertyBlock(original[i]);
                renderers[i].GetPropertyBlock(flash[i]);
                flash[i].SetColor("_BaseColor",new Color(1,.45f,.35f,1));renderers[i].SetPropertyBlock(flash[i]);
            }
            flashing=true;flashUntil=Time.time+.12f;
            if(Dead)
            {
                if(player!=null){player.Die(impulse);return true;}
                var actor=GetComponent<PrisonActor>();if(actor!=null){actor.Suspended=true;actor.enabled=false;}
                var agent=GetComponent<FoundationAgent>();if(agent!=null)agent.enabled=false;
                var footsteps=GetComponent<FoundationFootsteps>();if(footsteps!=null)footsteps.enabled=false;
                var pose=GetComponent<FoundationActorPose>();if(pose!=null)pose.enabled=false;
                var boxing=GetComponent<FoundationBoxing>();if(boxing!=null)boxing.StopCombat();
                var fall=GetComponent<FoundationFall>();
                if(fall!=null)
                {
                    foreach(var shape in GetComponents<Collider>())shape.enabled=false;
                    fall.StayDown=true;fall.KnockDown(impulse);
                }
                else
                {
                    var body=GetComponent<Rigidbody>();if(body==null)body=gameObject.AddComponent<Rigidbody>();
                    body.mass=75;body.isKinematic=false;body.collisionDetectionMode=CollisionDetectionMode.ContinuousDynamic;
                    body.AddForceAtPosition(impulse,point,ForceMode.Impulse);body.AddTorque(transform.right*8,ForceMode.Impulse);
                }
            }
            return true;
        }
        public bool Restore(float health)=>state.Restore(health);
        void Update()
        {
            if(!flashing||Time.time<flashUntil)return;
            for(int i=0;i<renderers.Length;i++)if(renderers[i]!=null)renderers[i].SetPropertyBlock(original[i]);
            flashing=false;
        }
    }
}
