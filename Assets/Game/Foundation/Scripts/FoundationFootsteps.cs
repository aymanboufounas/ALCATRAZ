using UnityEngine;
using DesertShift.Environment;

namespace Blackstone.Foundation
{
    [DefaultExecutionOrder(120)]
    public sealed class FoundationFootsteps : MonoBehaviour
    {
        public FoundationAvatar avatar;
        readonly bool[] contact = new bool[2];
        readonly float[] previousHeight = { 1, 1 };
        float next;
        void LateUpdate()
        {
            if(Time.deltaTime<=0||avatar==null||avatar.seated||avatar.MotionSpeed<.15f)return;
            if(avatar.movement!=null&&!avatar.movement.Grounded)return;
            Foot(0,avatar.leftFoot);Foot(1,avatar.rightFoot);
        }
        void Foot(int index,Transform foot)
        {
            if(foot==null)return;
            if(!Physics.Raycast(foot.position+Vector3.up*.4f,Vector3.down,out var hit,.9f,1,QueryTriggerInteraction.Ignore))
            {contact[index]=false;return;}
            float height=foot.position.y-hit.point.y;
            bool low=height<.15f;
            if(height>.19f)contact[index]=false;
            bool landing=low&&!contact[index]&&height<=previousHeight[index]+.003f;
            previousHeight[index]=height;
            if(!landing)return;
            contact[index]=true;
            if(Time.time<next||FoundationAudio.Instance==null)return;
            next=Time.time+.22f;
            var tag=hit.collider.GetComponentInParent<SurfaceTag>();
            string surface=tag==null?"Concrete":tag.surface==SurfaceKind.Metal?"Metal":tag.surface==SurfaceKind.Wood?"Wood":tag.surface==SurfaceKind.Sand?"Grass":"Concrete";
            float volume=avatar.movement!=null ? .5f : .24f;
            if(avatar.movement!=null&&avatar.movement.IsCrouching)volume*=.42f;
            FoundationAudio.Instance.Variation(surface,hit.point+Vector3.up*.08f,volume,Random.Range(.97f,1.035f));
        }
    }
}
