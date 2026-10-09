using UnityEngine;

namespace Blackstone.Foundation
{
    public sealed class FoundationAgent : MonoBehaviour
    {
        public Vector3[] route;
        public FoundationAvatar avatar;
        public Transform player;
        public float speed = 1.05f;
        int index;
        float wait;
        Blackstone.Actors.PrisonActor[] neighbours;
        Blackstone.Actors.PrisonActor actor;
        void Start()
        {
            actor=GetComponent<Blackstone.Actors.PrisonActor>();
            neighbours=FindObjectsByType<Blackstone.Actors.PrisonActor>(FindObjectsSortMode.None);
            wait = Time.time + Mathf.Repeat(transform.position.x * .4f, 3);
        }
        void Update()
        {
            if(avatar==null)return;
            avatar.agentSpeed = 0;
            if (Time.deltaTime <= 0 || avatar.seated || (actor!=null&&(actor.Talking||actor.Suspended)) || route == null || route.Length == 0 || Time.time < wait) return;
            Vector3 delta = route[index] - transform.position; delta.y = 0;
            if (delta.magnitude < .2f)
            { index = (index + 1) % route.Length; wait = Time.time + 1.5f; return; }
            Vector3 dir = delta.normalized;
            bool blocked = Physics.CapsuleCast(transform.position + Vector3.up*.35f, transform.position + Vector3.up*1.4f,
                .23f, dir, out _, .45f, 1, QueryTriggerInteraction.Ignore);
            if (player != null && Vector3.Distance(transform.position, player.position) < .9f
                && Vector3.Dot(dir, (player.position-transform.position).normalized) > 0) blocked = true;
            // Keep local routines from walking through stationary inmates.
            if(neighbours!=null)foreach(var other in neighbours)
            {
                if(other==null||other==actor||!other.gameObject.activeInHierarchy)continue;
                Vector3 separation=other.transform.position-transform.position;
                if(Mathf.Abs(separation.y)>.65f)continue;
                separation.y=0;
                if(separation.sqrMagnitude<.65f*.65f&&Vector3.Dot(dir,separation)>.05f)
                {blocked=true;break;}
            }
            if (blocked) { wait = Time.time + .5f; return; }
            Vector3 wanted = transform.position + dir * Mathf.Min(delta.magnitude, speed * Time.deltaTime);
            // No route step is committed without a supporting, walkable floor.
            if(!Physics.Raycast(wanted + Vector3.up*.55f, Vector3.down, out var floor, 1.3f, 1, QueryTriggerInteraction.Ignore)
                ||floor.normal.y<.65f||Mathf.Abs(floor.point.y-transform.position.y)>.35f)
            {wait=Time.time+.5f;return;}
            wanted.y = floor.point.y + .025f;
            transform.position = wanted;
            transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(dir), 1-Mathf.Exp(-6*Time.deltaTime));
            avatar.agentSpeed = speed;
        }
    }
}
