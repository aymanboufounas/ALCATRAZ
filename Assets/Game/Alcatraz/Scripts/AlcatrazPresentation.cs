using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Blackstone.Alcatraz
{
    [DefaultExecutionOrder(-550)]
    public sealed class AlcatrazPresentation : MonoBehaviour
    {
        VolumeProfile profile;
        void Awake()
        {
            var sky = Resources.Load<Material>("Alcatraz/MarineSky");
            if (sky != null) RenderSettings.skybox = sky;
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(.57f, .68f, .76f);
            RenderSettings.ambientEquatorColor = new Color(.45f, .49f, .46f);
            RenderSettings.ambientGroundColor = new Color(.26f, .28f, .25f);
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.ExponentialSquared;
            RenderSettings.fogColor = new Color(.69f, .77f, .80f);
            RenderSettings.fogDensity = .0011f;
            foreach (var light in FindObjectsByType<Light>(FindObjectsSortMode.None))
            {
                if (light.type != LightType.Directional) continue;
                light.color = new Color(1f, .95f, .85f);
                light.intensity = 1.7f;
                light.shadows = LightShadows.Soft;
                light.shadowStrength = .82f;
                RenderSettings.sun = light;
                break;
            }
            profile = ScriptableObject.CreateInstance<VolumeProfile>();
            var tone = profile.Add<Tonemapping>(true);
            tone.mode.value = TonemappingMode.ACES;
            var color = profile.Add<ColorAdjustments>(true);
            color.postExposure.value = .30f;
            color.contrast.value = 8f;
            color.saturation.value = -7f;
            var bloom = profile.Add<Bloom>(true);
            bloom.threshold.value = 1.25f;
            bloom.intensity.value = .12f;
            bloom.scatter.value = .58f;
            var vignette = profile.Add<Vignette>(true);
            vignette.intensity.value = .10f;
            vignette.smoothness.value = .65f;
            var volume = gameObject.AddComponent<Volume>();
            volume.isGlobal = true;
            volume.priority = 10;
            volume.sharedProfile = profile;
            var camera = Camera.main;
            if (camera != null)
            {
                camera.clearFlags = CameraClearFlags.Skybox;
                camera.allowHDR = true;
                camera.farClipPlane = 2200;
                var data = camera.GetUniversalAdditionalCameraData();
                data.renderPostProcessing = true;
                data.requiresDepthTexture = true;
                data.antialiasing = AntialiasingMode.SubpixelMorphologicalAntiAliasing;
            }
        }
        void OnDestroy()
        {
            if (profile == null) return;
            foreach (var component in profile.components)
                if (component != null) Destroy(component);
            Destroy(profile);
        }
    }
}
