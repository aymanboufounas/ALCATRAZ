using UnityEngine;
using Blackstone.Actors;
using Blackstone.Audio;

namespace Blackstone.Foundation
{
    public sealed class FoundationConversations : MonoBehaviour
    {
        public string Speaker { get; private set; }
        public string Subtitle { get; private set; }
        Transform player;
        PrisonAudio audioBus;
        PrisonActor current;
        PrisonActor[] actors;
        float until,next;
        void Start()
        {
            var movement=FindFirstObjectByType<DesertShift.Player.PlayerMovement>();if(movement!=null)player=movement.transform;
            audioBus=FindFirstObjectByType<PrisonAudio>();actors=FindObjectsByType<PrisonActor>(FindObjectsSortMode.None);next=Time.time+4;
        }
        void Update()
        {
            if(Time.deltaTime<=0||player==null||audioBus==null)return;
            if(current!=null&&(Time.time>until||current.GetComponent<FoundationDamageable>()!=null&&current.GetComponent<FoundationDamageable>().Dead))
            {current.SpeakTo(null,false);current=null;Speaker=Subtitle=null;next=Time.time+16;}
            if(current!=null||Time.time<next)return;
            foreach(var actor in actors)
            {
                if(actor==null||actor.GetComponent<FoundationDamageable>()!=null&&actor.GetComponent<FoundationDamageable>().Dead)continue;
                string name=actor.displayName??"";string id=null,text=null;
                if(name.StartsWith("Niko")){id="ambient_niko_01";text="Keep your voice down. Harrow hears more than you think.";}
                else if(name.StartsWith("Malik")){id="ambient_malik_01";text="Every favor gets remembered. Good and bad.";}
                else if(name=="Samir"){id="ambient_samir_01";text="My cooking is better than my cards. That is not saying much.";}
                else if(name=="Tomas"){id="ambient_tomas_01";text="Counts in ten minutes. Plenty of time for another hand.";}
                else if(name=="Workshop contact"){id="ambient_jonah_01";text="Work detail at the next whistle. Do not be late.";}
                if(id==null||Vector3.Distance(player.position,actor.transform.position)>3.4f)continue;
                Vector3 origin=actor.transform.position+Vector3.up*1.35f,receiver=player.position+Vector3.up*1.3f;
                if(Physics.Linecast(origin,receiver,1,QueryTriggerInteraction.Ignore))continue;
                float seconds=audioBus.AmbientLine(id,origin);if(seconds<=0)continue;
                current=actor;actor.SpeakTo(player,true);Speaker=name;Subtitle=text;until=Time.time+seconds+.5f;break;
            }
        }
        void OnDisable(){if(current!=null)current.SpeakTo(null,false);}
    }
}
