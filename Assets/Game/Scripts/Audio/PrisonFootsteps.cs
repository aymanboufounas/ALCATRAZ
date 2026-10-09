using UnityEngine;
using Blackstone.Actors;
using DesertShift.Player;
using DesertShift.Environment;

namespace Blackstone.Audio
{
    public sealed class PrisonFootsteps : MonoBehaviour
    {
        public PrisonLocomotion locomotion;
        public AudioClip[] concrete, metal;
        AudioSource source;
        PrisonAudio mix;
        PlayerMovement player;
        float nextStep;
        int variant;
        void Awake()
        {
            source = gameObject.AddComponent<AudioSource>(); source.playOnAwake = false;
            source.spatialBlend = 1; source.minDistance = 1.5f; source.maxDistance = 13;
            source.dopplerLevel = 0; player = GetComponent<PlayerMovement>();
            mix = FindFirstObjectByType<PrisonAudio>();
            if (locomotion != null) locomotion.FootContact += Step;
        }
        void Update(){if(Time.timeScale==0)source.Pause();else source.UnPause();}
        void Step(bool left)
        {
            if (Time.time < nextStep || Time.deltaTime <= 0 || (player != null && !player.Grounded)) return;
            nextStep = Time.time + .18f;
            var clips = concrete;
            if (Physics.Raycast(transform.position + Vector3.up*.25f, Vector3.down, out var hit, .7f, 1, QueryTriggerInteraction.Ignore))
            {
                var surface = hit.collider.GetComponentInParent<SurfaceTag>();
                if (surface != null && surface.surface == SurfaceKind.Metal) clips = metal;
            }
            if (clips == null || clips.Length == 0) return;
            var clip = clips[(variant++ + (left ? 1 : 0)) % clips.Length];
            source.pitch = Random.Range(.96f,1.035f);
            float volume = (mix != null ? mix.master*mix.effects : .6f) * (player != null ? .55f : .23f);
            if (player != null && player.IsCrouching) volume *= .4f;
            if (clip != null) source.PlayOneShot(clip,volume);
        }
        void OnDestroy() { if (locomotion != null) locomotion.FootContact -= Step; }
    }
}
