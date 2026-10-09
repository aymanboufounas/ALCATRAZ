using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using DesertShift.Player;

namespace DesertShift.Core
{
    [DefaultExecutionOrder(-300)]
    public sealed class GameBootstrap : MonoBehaviour
    {
        public RenderPipelineAsset renderPipeline;
        public UniversalRendererData rendererData;
        public Material skyMaterial;
        public Light sun;
        public PlayerInputHandler playerInput;
        public bool prisonNight;
        Light flashlight;
        ScriptableRendererFeature ambientOcclusion;
        void Awake()
        {
            Application.targetFrameRate = prisonNight ? 60 : 90; QualitySettings.vSyncCount = 1;
            // URP's SSAO feature is an internal type in some 17.x package revisions.
            // Resolve the official implementation without linking against a private API.
            if (rendererData != null)
            {
                bool present = rendererData.rendererFeatures.Exists(f => f != null &&
                    f.GetType().Name == "ScreenSpaceAmbientOcclusion");
                var featureType = typeof(UniversalRenderPipelineAsset).Assembly.GetType(
                    "UnityEngine.Rendering.Universal.ScreenSpaceAmbientOcclusion");
                if (!present && featureType != null)
                {
                    ambientOcclusion = ScriptableObject.CreateInstance(featureType) as ScriptableRendererFeature;
                    if (ambientOcclusion != null)
                    {
                        ambientOcclusion.name = "Desert Contact Occlusion";
                        rendererData.rendererFeatures.Add(ambientOcclusion);
                        rendererData.SetDirty();
                    }
                }
            }
            if (renderPipeline != null)
            {
                GraphicsSettings.defaultRenderPipeline = renderPipeline;
                QualitySettings.renderPipeline = renderPipeline;
            }
            if (skyMaterial != null) RenderSettings.skybox = skyMaterial;
            RenderSettings.sun = sun;
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = prisonNight ? new Color(.58f, .64f, .70f) : new Color(.43f, .57f, .66f);
            RenderSettings.ambientEquatorColor = prisonNight ? new Color(.44f, .43f, .38f) : new Color(.61f, .48f, .32f);
            RenderSettings.ambientGroundColor = prisonNight ? new Color(.27f, .27f, .24f) : new Color(.33f, .25f, .16f);
            RenderSettings.ambientIntensity = 1f;
            RenderSettings.fog = true; RenderSettings.fogMode = FogMode.ExponentialSquared;
            RenderSettings.fogDensity = prisonNight ? .0023f : .00165f;
            RenderSettings.fogColor = prisonNight ? new Color(.65f, .69f, .68f) : new Color(.67f, .69f, .61f);
        }
        void Start()
        {
            var camera = UnityEngine.Camera.main;
            if (camera == null) { Debug.LogError("Desert Shift needs the scene's Main Camera."); return; }
            var data = camera.GetUniversalAdditionalCameraData();
            data.renderPostProcessing = true;
            data.antialiasing = AntialiasingMode.SubpixelMorphologicalAntiAliasing;
            data.antialiasingQuality = AntialiasingQuality.High;
            data.renderShadows = true;
            var torch = new GameObject("Calder Flashlight"); torch.transform.SetParent(camera.transform, false);
            torch.transform.localPosition = new Vector3(.2f, -.2f, .15f);
            flashlight = torch.AddComponent<Light>(); flashlight.type = LightType.Spot;
            flashlight.color = new Color(1f, .91f, .71f); flashlight.intensity = 3;
            flashlight.range = 20; flashlight.spotAngle = 48; flashlight.innerSpotAngle = 28;
            flashlight.shadows = LightShadows.Soft; flashlight.enabled = false;
            foreach (var probe in FindObjectsByType<ReflectionProbe>(FindObjectsSortMode.None))
            {
                probe.mode = ReflectionProbeMode.Realtime;
                probe.refreshMode = ReflectionProbeRefreshMode.ViaScripting;
                probe.timeSlicingMode = ReflectionProbeTimeSlicingMode.IndividualFaces;
                probe.RenderProbe();
            }
        }
        void Update()
        {
            if (playerInput != null && playerInput.FlashlightPressed && flashlight != null)
                flashlight.enabled = !flashlight.enabled;
        }
        void OnDestroy()
        {
            if (ambientOcclusion != null)
            {
                if (rendererData != null) { rendererData.rendererFeatures.Remove(ambientOcclusion); rendererData.SetDirty(); }
                Destroy(ambientOcclusion);
            }
            Time.timeScale = 1; Cursor.lockState = CursorLockMode.None; Cursor.visible = true;
        }
    }
}
