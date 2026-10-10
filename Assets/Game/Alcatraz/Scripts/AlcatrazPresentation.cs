using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Blackstone.Alcatraz
{
    // Apply lighting after the legacy bootstrap and the supplied world's Start.
    [DefaultExecutionOrder(100)]
    public sealed class AlcatrazPresentation : MonoBehaviour
    {
        VolumeProfile profile;
        void Start()
        {
            var sky = Resources.Load<Material>("Alcatraz/MarineSky");
            if (sky != null) RenderSettings.skybox = sky;
            // These scenes have no baked lightmaps or light probes. Set their SH
            // environment explicitly rather than depending on a stale lighting cache.
            RenderSettings.ambientMode = AmbientMode.Custom;
            RenderSettings.ambientSkyColor = new Color(.57f, .68f, .76f);
            RenderSettings.ambientEquatorColor = new Color(.45f, .49f, .46f);
            RenderSettings.ambientGroundColor = new Color(.26f, .28f, .25f);
            RenderSettings.ambientIntensity = 1;
            var ambient = new SphericalHarmonicsL2();
            ambient.AddAmbientLight(LightingColor(new Color(.55f, .60f, .63f)));
            ambient.AddDirectionalLight(Vector3.up, LightingColor(new Color(.75f, .84f, .96f)), .30f);
            ambient.AddDirectionalLight(Vector3.down, LightingColor(new Color(.34f, .32f, .28f)), .15f);
            RenderSettings.ambientProbe = ambient;
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.ExponentialSquared;
            RenderSettings.fogColor = new Color(.69f, .77f, .80f);
            RenderSettings.fogDensity = .0011f;
            foreach (var light in FindObjectsByType<Light>(FindObjectsSortMode.None))
            {
                if (light.type != LightType.Directional) continue;
                light.color = new Color(1f, .95f, .85f);
                light.intensity = 1.5f;
                light.shadows = LightShadows.Soft;
                light.shadowStrength = .65f;
                RenderSettings.sun = light;
                break;
            }
            profile = ScriptableObject.CreateInstance<VolumeProfile>();
            var tone = profile.Add<Tonemapping>(true);
            tone.mode.value = TonemappingMode.ACES;
            var color = profile.Add<ColorAdjustments>(true);
            color.postExposure.value = .15f;
            color.contrast.value = 4f;
            color.saturation.value = -7f;
            var bloom = profile.Add<Bloom>(true);
            bloom.threshold.value = 1.25f;
            bloom.intensity.value = .06f;
            bloom.scatter.value = .58f;
            var vignette = profile.Add<Vignette>(true);
            vignette.intensity.value = .07f;
            vignette.smoothness.value = .65f;
            var volume = gameObject.AddComponent<Volume>();
            volume.isGlobal = true;
            volume.priority = 20;
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
            foreach (var probe in FindObjectsByType<ReflectionProbe>(FindObjectsSortMode.None))
            {
                probe.mode = ReflectionProbeMode.Realtime;
                probe.refreshMode = ReflectionProbeRefreshMode.ViaScripting;
                probe.timeSlicingMode = ReflectionProbeTimeSlicingMode.IndividualFaces;
                probe.RenderProbe();
            }
        }
        static Color LightingColor(Color color)
        { return QualitySettings.activeColorSpace == ColorSpace.Linear ? color.linear : color; }
        void OnDestroy()
        {
            if (profile == null) return;
            foreach (var component in profile.components)
                if (component != null) Destroy(component);
            Destroy(profile);
        }
    }
}
