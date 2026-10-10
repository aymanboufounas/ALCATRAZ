using UnityEngine;
using DesertShift.Player;

namespace Blackstone.Supplied
{
    public sealed class SuppliedDogPatrol : MonoBehaviour
    {
        public SuppliedIslandWorld world;
        public Vector3[] route;
        Animation animationPlayer;
        string idle,walk,bark,current;
        PlayerMovement player;
        PlayerInputHandler input;
        int index;
        float wait,nextBark;
        void Start()
        {
            player=FindFirstObjectByType<PlayerMovement>();input=player!=null?player.GetComponent<PlayerInputHandler>():null;
            animationPlayer=GetComponentInChildren<Animation>();if(animationPlayer==null){enabled=false;return;}
            foreach(AnimationState clip in animationPlayer)
            {
                string name=clip.name.ToLowerInvariant();clip.wrapMode=WrapMode.Loop;
                if(name.Contains("idle 0_30"))idle=clip.name;
                if(name.Contains("dog walk 1_55"))walk=clip.name;
                if(name.Contains("dog bark 0_52")){bark=clip.name;clip.wrapMode=WrapMode.Once;}
            }
            Play(idle);
        }
        void Play(string name)
        {if(string.IsNullOrEmpty(name)||current==name)return;current=name;animationPlayer.CrossFade(name,.2f);}
        void Update()
        {
            if(world==null||!world.Ready||input==null||!input.CanControl||Time.deltaTime<=0){Play(idle);return;}
            if(Time.time<wait)return;
            if(player!=null&&Vector3.Distance(transform.position,player.transform.position)<2.4f&&Time.time>nextBark)
            {Play(bark);wait=Time.time+2;nextBark=Time.time+12;return;}
            if(route==null||route.Length==0){Play(idle);return;}
            Vector3 delta=route[index]-transform.position;delta.y=0;
            if(delta.magnitude<.3f){index=(index+1)%route.Length;wait=Time.time+1.8f;Play(idle);return;}
            Vector3 direction=delta.normalized;
            if(Physics.SphereCast(transform.position+Vector3.up*.55f,.16f,direction,out _,.55f,1,QueryTriggerInteraction.Ignore))
            {index=(index+1)%route.Length;wait=Time.time+1;Play(idle);return;}
            Vector3 next=transform.position+direction*Mathf.Min(delta.magnitude,.8f*Time.deltaTime);
            if(Physics.Raycast(next+Vector3.up*2,Vector3.down,out var floor,4,1,QueryTriggerInteraction.Ignore)&&floor.normal.y>.68f)
            {next.y=floor.point.y;transform.position=next;transform.rotation=Quaternion.Slerp(transform.rotation,Quaternion.LookRotation(direction),Time.deltaTime*4);Play(walk);}
            else{index=(index+1)%route.Length;wait=Time.time+1;Play(idle);}
        }
    }
}
