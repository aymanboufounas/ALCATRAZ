using System.Collections.Generic;
using UnityEngine;
using Blackstone.Audio;

namespace Blackstone.Foundation
{
    public sealed class FoundationAudio : MonoBehaviour
    {
        public static FoundationAudio Instance { get; private set; }
        public float master = .8f, effects = .8f;
        public bool followStoryMixer;
        AudioSource[] pool;
        AudioLowPassFilter[] filters;
        AudioReverbFilter[] rooms;
        float[] gains;
        Transform listener;
        PrisonAudio ambience;
        int cursor;
        readonly Dictionary<string, AudioClip[]> clips = new Dictionary<string, AudioClip[]>();
        readonly Dictionary<string, int> last = new Dictionary<string, int>();
        void Awake()
        {
            master=PlayerPrefs.GetFloat("Blackstone.Master",1);effects=PlayerPrefs.GetFloat("Blackstone.Effects",1);
            Instance = this; pool = new AudioSource[24]; filters = new AudioLowPassFilter[24]; rooms = new AudioReverbFilter[24];gains=new float[24];
            for (int i=0;i<pool.Length;i++)
            {
                var go=new GameObject("Spatial voice "+i);go.transform.SetParent(transform,false);
                var s=go.AddComponent<AudioSource>();s.playOnAwake=false;s.spatialBlend=1;s.dopplerLevel=0;
                s.minDistance=1.4f;s.maxDistance=32;s.rolloffMode=AudioRolloffMode.Logarithmic;pool[i]=s;
                filters[i]=go.AddComponent<AudioLowPassFilter>();rooms[i]=go.AddComponent<AudioReverbFilter>();
            }
            var p=FindFirstObjectByType<DesertShift.Player.PlayerMovement>();if(p!=null)listener=p.transform;
            ambience=FindFirstObjectByType<PrisonAudio>();
            foreach(string name in new[]{"Concrete","Metal","Wood","Grass","Pistol","Rifle","Impact","Punch","Handling"})
                clips[name]=Resources.LoadAll<AudioClip>("BlackstoneFoundation/Audio/"+name);
        }
        void Update()
        {
            if(ambience!=null)
            {
                if(followStoryMixer){master=ambience.master;effects=ambience.effects;}
                else {ambience.master=master;ambience.effects=effects;}
            }
            bool paused=Time.timeScale<=0;
            for(int i=0;i<pool.Length;i++)
            {
                pool[i].volume=gains[i]*master*effects;
                if(paused)pool[i].Pause();else pool[i].UnPause();
                if(!pool[i].isPlaying||listener==null)continue;
                Vector3 source=pool[i].transform.position, end=listener.position+Vector3.up*1.3f;
                filters[i].cutoffFrequency=Physics.Linecast(source,end,1,QueryTriggerInteraction.Ignore)?2400:22000;
                bool indoors=source.z<6||source.x>18.4f;
                rooms[i].reverbPreset=indoors?AudioReverbPreset.Room:AudioReverbPreset.Off;
            }
            FoundationFmodBridge.SetPaused(paused);
            FoundationFmodBridge.SetVolume(master*effects);
        }
        public void Variation(string group, Vector3 position, float volume=.7f, float pitch=1)
        {
            if(!clips.TryGetValue(group,out var available)||available.Length==0)return;
            int choice=Random.Range(0,available.Length);
            if(available.Length>1&&last.TryGetValue(group,out var previous)&&choice==previous)choice=(choice+1)%available.Length;
            last[group]=choice; Play(available[choice],position,volume,pitch);
        }
        public void Named(string group,string name,Vector3 position,float volume=.7f)
        {
            if(!clips.TryGetValue(group,out var available))return;
            foreach(var clip in available)if(clip.name==name){Play(clip,position,volume);return;}
        }
        public void Play(AudioClip clip,Vector3 position,float volume=.7f,float pitch=1)
        {
            if(clip==null||Time.timeScale<=0)return;
            if(FoundationFmodBridge.TryPlay(clip.name,position,volume,pitch))return;
            var source=pool[cursor];gains[cursor]=volume;cursor=(cursor+1)%pool.Length;source.Stop();source.transform.position=position;
            source.clip=clip;source.pitch=pitch;source.volume=volume*master*effects;source.Play();
        }
        void OnDestroy(){if(Instance==this)Instance=null;}
    }
}
