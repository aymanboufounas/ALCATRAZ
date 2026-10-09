using UnityEngine;

namespace Blackstone.Audio
{
    public sealed class PrisonAudio : MonoBehaviour
    {
        public AudioClip success,missed,knifeDrop,clothHide,tattooBuzz,phoneRing,
            phoneClick,punch,whistle,metalDoor,doorKnock,sob,cellAmbience,yardAmbience,tension,cardShuffle,cardDeal;
        public float master=.8f,effects=.8f,dialogue=.9f,music=.28f;
        AudioSource sfx,voices,inside,outside,score,nearby;
        AudioSource[] sources;
        AudioLowPassFilter phoneFilter;
        Transform player;
        float yardWeight;
        Blackstone.Alcatraz.AlcatrazMap island;
        void Awake()
        {
            island=FindFirstObjectByType<Blackstone.Alcatraz.AlcatrazMap>();
            sfx=Source("Effects",0);voices=Source("Story voices",0);inside=Source("Interior room tone",0);
            outside=Source("Yard atmosphere",0);score=Source("Score",0);nearby=Source("Nearby conversation",1);
            nearby.minDistance=1.5f;nearby.maxDistance=8;nearby.dopplerLevel=0;
            sources=new[]{sfx,voices,inside,outside,score,nearby};
            phoneFilter=voices.gameObject.AddComponent<AudioLowPassFilter>();phoneFilter.cutoffFrequency=22000;
            inside.clip=cellAmbience;inside.loop=true;outside.clip=yardAmbience;outside.loop=true;
            score.clip=tension;score.loop=true;voices.priority=40;
            if(inside.clip!=null)inside.Play();if(outside.clip!=null)outside.Play();
            var movement=FindFirstObjectByType<DesertShift.Player.PlayerMovement>();if(movement!=null)player=movement.transform;
        }
        AudioSource Source(string name,float spatial)
        {
            var go=new GameObject(name);go.transform.SetParent(transform,false);
            var source=go.AddComponent<AudioSource>();source.playOnAwake=false;source.spatialBlend=spatial;source.dopplerLevel=0;
            return source;
        }
        void Update()
        {
            bool yard=player!=null&&(island!=null?!island.IsInterior(player.position):player.position.z>6&&player.position.x<18.4f);
            yardWeight=Mathf.Lerp(yardWeight,yard?1:0,1-Mathf.Exp(-2*Time.deltaTime));
            sfx.volume=master*effects;voices.volume=master*dialogue;nearby.volume=master*dialogue*.40f;
            inside.volume=master*effects*.23f*(1-yardWeight);outside.volume=master*effects*.25f*yardWeight;
            score.volume=master*music;
            bool paused=Time.timeScale==0;foreach(var source in sources){if(paused)source.Pause();else source.UnPause();}
        }
        public void Play(AudioClip clip,float volume=1)
        {if(clip!=null)sfx.PlayOneShot(clip,volume);}
        public float Speak(string id)
        {
            voices.Stop();nearby.Stop();
            var clip=Resources.Load<AudioClip>("Blackstone/Dialogue/"+id);if(clip==null)return 0;
            phoneFilter.cutoffFrequency=id.StartsWith("phone_call")?4200:22000;
            voices.clip=clip;voices.Play();return clip.length;
        }
        public float AmbientLine(string id,Vector3 position)
        {
            if(voices.isPlaying)return 0;var clip=Resources.Load<AudioClip>("Blackstone/Dialogue/"+id);if(clip==null)return 0;
            nearby.transform.position=position;nearby.clip=clip;nearby.Play();return clip.length;
        }
        public void Tension(bool enabled)
        {if(enabled&&score.clip!=null&&!score.isPlaying)score.Play();else if(!enabled)score.Stop();}
        public void StopDialogue(){if(voices!=null)voices.Stop();if(nearby!=null)nearby.Stop();}
    }
}
