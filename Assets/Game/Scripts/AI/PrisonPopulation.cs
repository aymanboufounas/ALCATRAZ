using UnityEngine;
using Blackstone.Story;
using Blackstone.Audio;

namespace Blackstone.Actors
{
    [DefaultExecutionOrder(50)]
    public sealed class PrisonPopulation:MonoBehaviour
    {
        public PrisonStoryDirector director;
        public PrisonActor[] contacts;
        public string[] lineIds;
        float nextLine, until;
        PrisonActor speaking;
        void Start(){nextLine=Time.time+17;}
        void Update()
        {
            if(director==null||Time.deltaTime<=0)return;
            if(speaking!=null&&(Time.time>=until||director.Busy))
            {speaking.SpeakTo(null,false);speaking=null;}
            if(director.MainMenu||director.Busy||!director.CanUseYardActivity||Time.time<nextLine)return;
            nextLine=Time.time+Random.Range(18f,31f);
            if(contacts==null||lineIds==null)return;
            int nearest=-1;float distance=6;
            for(int i=0;i<contacts.Length&&i<lineIds.Length;i++)
            {
                if(contacts[i]==null)continue;
                float d=Vector3.Distance(contacts[i].transform.position,director.player.transform.position);
                if(d<distance){distance=d;nearest=i;}
            }
            if(nearest<0)return;
            var actor=contacts[nearest];
            if(Physics.Linecast(actor.transform.position+Vector3.up*1.4f,director.player.transform.position+Vector3.up*1.3f,out _,1,QueryTriggerInteraction.Ignore))return;
            float duration=director.audioBus.AmbientLine(lineIds[nearest],actor.transform.position+Vector3.up*1.45f);
            if(duration>0){speaking=actor;actor.SpeakTo(director.player.transform,true);until=Time.time+duration;}
        }
    }
}
