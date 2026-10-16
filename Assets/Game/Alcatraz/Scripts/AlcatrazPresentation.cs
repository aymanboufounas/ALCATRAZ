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
        Material runtimeSky, originalSky;
        void Start()
        {
            // A consistent late-afternoon key light gives every outdoor area the
            // same direction and keeps cloud highlights aligned with real shadows.
            Vector3 sunDirection = new Vector3(.398f, .530f, -.748f).normalized;
            foreach (var light in FindObjectsByType<Light>(FindObjectsSortMode.None))
            {
                if (light.type != LightType.Directional) continue;
                light.transform.rotation = Quaternion.Euler(32f, -28f, 0f);
                light.color = new Color(1f, .91f, .77f);
                light.intensity = 1.7f;
                light.shadows = LightShadows.Soft;
                light.shadowStrength = .78f;
                RenderSettings.sun = light;
                sunDirection = -light.transform.forward;
                break;
            }
            var sky = Resources.Load<Material>("Alcatraz/MarineSky");
            if (sky != null)
            {
                // Runtime shader parameters must not dirty the imported material.
                originalSky = RenderSettings.skybox;
                runtimeSky = new Material(sky) { name = "Alcatraz marine sky (runtime)", hideFlags = HideFlags.DontSave };
                runtimeSky.SetVector("_SunDirection", sunDirection);
                RenderSettings.skybox = runtimeSky;
            }
            RenderSettings.defaultReflectionMode = DefaultReflectionMode.Skybox;
            RenderSettings.ambientMode = AmbientMode.Custom;
            // Schedule one environment refresh for the newly assigned sky.
            // Explicit ambient SH below keeps unbaked interiors readable.
            DynamicGI.UpdateEnvironment();
            // These scenes have no baked lightmaps or light probes. Set their SH
            // environment explicitly rather than depending on a stale lighting cache.
            RenderSettings.ambientSkyColor = new Color(.53f, .65f, .76f);
            RenderSettings.ambientEquatorColor = new Color(.46f, .51f, .53f);
            RenderSettings.ambientGroundColor = new Color(.30f, .30f, .26f);
            RenderSettings.ambientIntensity = 1;
            var ambient = new SphericalHarmonicsL2();
            ambient.AddAmbientLight(LightingColor(new Color(.47f, .54f, .60f)));
            ambient.AddDirectionalLight(Vector3.up, LightingColor(new Color(.68f, .81f, .96f)), .34f);
            ambient.AddDirectionalLight(Vector3.down, LightingColor(new Color(.43f, .39f, .30f)), .18f);
            RenderSettings.ambientProbe = ambient;
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.ExponentialSquared;
            RenderSettings.fogColor = new Color(.72f, .77f, .78f);
            RenderSettings.fogDensity = .00125f;
            profile = ScriptableObject.CreateInstance<VolumeProfile>();
            var tone = profile.Add<Tonemapping>(true);
            tone.mode.value = TonemappingMode.ACES;
            var color = profile.Add<ColorAdjustments>(true);
            color.postExposure.value = .05f;
            color.contrast.value = 6f;
            color.saturation.value = -3f;
            var bloom = profile.Add<Bloom>(true);
            bloom.threshold.value = 1.35f;
            bloom.intensity.value = .07f;
            bloom.scatter.value = .55f;
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
            AlcatrazEnvironmentDetails.Ensure(gameObject);
        }
        static Color LightingColor(Color color)
        { return QualitySettings.activeColorSpace == ColorSpace.Linear ? color.linear : color; }
        void OnDestroy()
        {
            if (runtimeSky != null)
            {
                if (RenderSettings.skybox == runtimeSky) RenderSettings.skybox = originalSky;
                Destroy(runtimeSky);
            }
            if (profile == null) return;
            foreach (var component in profile.components)
                if (component != null) Destroy(component);
            Destroy(profile);
        }
    }
}
