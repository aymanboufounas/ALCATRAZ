using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
namespace DesertShift.Environment
{
    public sealed class DesertAtmosphere : MonoBehaviour
    {
        public bool prisonNight;
        VolumeProfile runtimeProfile;
        void Awake()
        {
            var volume = GetComponent<Volume>();
            if (volume == null) volume = gameObject.AddComponent<Volume>();
            volume.isGlobal = true; volume.priority = 1; volume.weight = 1;
            runtimeProfile = ScriptableObject.CreateInstance<VolumeProfile>();
            var tone = runtimeProfile.Add<Tonemapping>(true); tone.mode.Override(TonemappingMode.ACES);
            var bloom = runtimeProfile.Add<Bloom>(true); bloom.intensity.Override(prisonNight ? .045f : .12f); bloom.threshold.Override(1.25f);
            var color = runtimeProfile.Add<ColorAdjustments>(true);
            color.postExposure.Override(prisonNight ? .12f : .12f); color.contrast.Override(prisonNight ? 11 : 8); color.saturation.Override(prisonNight ? -6 : -7);
            var balance = runtimeProfile.Add<WhiteBalance>(true); balance.temperature.Override(prisonNight ? 4 : 7);
            var vignette = runtimeProfile.Add<Vignette>(true); vignette.intensity.Override(prisonNight ? .055f : .095f); vignette.smoothness.Override(.55f);
            volume.sharedProfile = runtimeProfile;
        }
        void OnDestroy() { if (runtimeProfile != null) Destroy(runtimeProfile); }
    }
}
