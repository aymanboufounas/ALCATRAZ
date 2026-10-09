using UnityEngine;
namespace DesertShift.Environment
{
    public sealed class EnvironmentAudio : MonoBehaviour
    {
        public AudioClip clip;
        [Range(0, 1)] public float volume = .2f;
        public bool spatial = true;
        public float range = 22;
        void Start()
        {
            if (clip == null) return;
            var source = gameObject.AddComponent<AudioSource>();
            source.clip = clip; source.loop = true; source.volume = volume;
            source.spatialBlend = spatial ? 1 : 0; source.minDistance = 2; source.maxDistance = range;
            source.rolloffMode = AudioRolloffMode.Linear; source.Play();
        }
    }
}
