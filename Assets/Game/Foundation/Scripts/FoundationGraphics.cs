using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Blackstone.Foundation
{
    // One scene owner for story and exploration settings. Only its runtime URP
    // clone is edited; renderer data, features and source assets remain shared.
    [DefaultExecutionOrder(200),DisallowMultipleComponent]
    public sealed class FoundationGraphics : MonoBehaviour
    {
        static FoundationGraphics instance;
        static int? requestedPreset;
        static bool? requestedVSync;
        UniversalRenderPipelineAsset runtime;
        RenderPipelineAsset originalDefault,originalQuality;
        int originalMip,originalVSync,originalTarget,preset;
        float originalLod,originalStreaming;
        AnisotropicFiltering originalAnisotropy;
        bool initialized,vsync;
        string status;
        Camera lastCamera;
        readonly Dictionary<Camera,CameraState> cameras=new Dictionary<Camera,CameraState>();
        public static string[] Names=>GraphicsRules.Names;
        public static int SelectedPreset=>instance!=null&&instance.initialized?instance.preset:
            requestedPreset??GraphicsRules.ClampPreset(PlayerPrefs.GetInt("Blackstone.Quality",GraphicsRules.DefaultPreset));
        public static bool VSync=>instance!=null&&instance.initialized?instance.vsync:
            requestedVSync??PlayerPrefs.GetInt("Blackstone.VSync",1)!=0;
        public static string Status=>instance!=null?instance.status:"Graphics will initialize with the scene.";

        public static FoundationGraphics Ensure(GameObject owner)
        {
            if(instance!=null){instance.Initialize();return instance;}
            if(owner==null)return null;
            var service=owner.GetComponent<FoundationGraphics>();
            if(service==null)service=owner.AddComponent<FoundationGraphics>();
            service.Initialize();return service;
        }
        void Awake(){Initialize();}
        void Start(){ApplyCurrent();}
        void LateUpdate()
        {
            if(!initialized||instance!=this)return;
            var camera=Camera.main;
            if(camera!=lastCamera){lastCamera=camera;ApplyCamera(camera);}
        }
        void Initialize()
        {
            if(initialized)return;
            if(instance!=null&&instance!=this){enabled=false;return;}
            instance=this;
            var active=QualitySettings.renderPipeline!=null?QualitySettings.renderPipeline:GraphicsSettings.defaultRenderPipeline;
            var source=active as UniversalRenderPipelineAsset;
            if(source==null){status="The active scene needs a Universal Render Pipeline asset.";return;}
            originalDefault=GraphicsSettings.defaultRenderPipeline;originalQuality=QualitySettings.renderPipeline;
            originalMip=QualitySettings.globalTextureMipmapLimit;originalVSync=QualitySettings.vSyncCount;
            originalTarget=Application.targetFrameRate;originalAnisotropy=QualitySettings.anisotropicFiltering;
            originalLod=QualitySettings.lodBias;originalStreaming=QualitySettings.streamingMipmapsMemoryBudget;
            runtime=Instantiate(source);runtime.name=source.name+" (Alcatraz runtime graphics)";runtime.hideFlags=HideFlags.DontSave;
            GraphicsSettings.defaultRenderPipeline=runtime;QualitySettings.renderPipeline=runtime;
            preset=requestedPreset??GraphicsRules.ClampPreset(PlayerPrefs.GetInt("Blackstone.Quality",GraphicsRules.DefaultPreset));
            vsync=requestedVSync??PlayerPrefs.GetInt("Blackstone.VSync",1)!=0;
            initialized=true;ApplyCurrent();
        }
        public static void SetPreset(int selected,bool persist=true)
        {
            selected=GraphicsRules.ClampPreset(selected);requestedPreset=selected;
            if(persist){PlayerPrefs.SetInt("Blackstone.Quality",selected);PlayerPrefs.Save();}
            if(instance!=null){instance.Initialize();instance.preset=selected;instance.ApplyCurrent();}
        }
        public static void SetVSync(bool enabled,bool persist=true)
        {
            requestedVSync=enabled;
            if(persist){PlayerPrefs.SetInt("Blackstone.VSync",enabled?1:0);PlayerPrefs.Save();}
            if(instance!=null){instance.Initialize();instance.vsync=enabled;instance.ApplyCurrent();}
        }
        void ApplyCurrent()
        {
            if(!initialized||runtime==null||instance!=this)return;
            // A different system can replace the active pipeline. Do not edit
            // that system's assets or silently claim to control its rendering.
            if(GraphicsSettings.defaultRenderPipeline!=runtime||QualitySettings.renderPipeline!=runtime)
            {status="Another renderer replaced the Alcatraz runtime pipeline.";return;}
            var settings=GraphicsRules.Get(preset);
            runtime.renderScale=settings.RenderScale;runtime.msaaSampleCount=1;
            runtime.shadowDistance=settings.ShadowDistance;runtime.shadowCascadeCount=settings.Cascades;
            runtime.mainLightShadowmapResolution=settings.ShadowMap;runtime.maxAdditionalLightsCount=settings.AdditionalLights;
            QualitySettings.globalTextureMipmapLimit=settings.MipmapLimit;
            QualitySettings.vSyncCount=vsync?1:0;Application.targetFrameRate=-1;
            QualitySettings.anisotropicFiltering=settings.ForceAnisotropy?AnisotropicFiltering.ForceEnable:
                preset==0?AnisotropicFiltering.Disable:AnisotropicFiltering.Enable;
            QualitySettings.lodBias=settings.LodBias;QualitySettings.streamingMipmapsMemoryBudget=settings.StreamingBudget;
            status=Names[preset]+" / "+(settings.MipmapLimit==0?"full texture detail":"reduced texture detail")
                +" / "+(settings.RenderScale==1?"native rendering":"80% render scale");
            lastCamera=Camera.main;ApplyCamera(lastCamera);
        }
        public static void ApplyCamera(Camera camera)
        {
            if(instance==null||!instance.initialized||camera==null||camera.cameraType!=CameraType.Game||camera.orthographic)return;
            if(GraphicsSettings.defaultRenderPipeline!=instance.runtime||QualitySettings.renderPipeline!=instance.runtime)return;
            var data=camera.GetUniversalAdditionalCameraData();
            if(!instance.cameras.ContainsKey(camera))instance.cameras[camera]=new CameraState(camera,data);
            var settings=GraphicsRules.Get(instance.preset);
            camera.allowHDR=instance.runtime.supportsHDR;camera.allowMSAA=false;
            data.renderPostProcessing=true;data.requiresDepthOption=CameraOverrideOption.On;data.renderShadows=true;
            data.antialiasing=settings.Smaa?AntialiasingMode.SubpixelMorphologicalAntiAliasing:AntialiasingMode.FastApproximateAntialiasing;
            data.antialiasingQuality=instance.preset>=2?AntialiasingQuality.High:
                instance.preset==1?AntialiasingQuality.Medium:AntialiasingQuality.Low;
        }
        void OnDestroy()
        {
            if(initialized&&runtime!=null)
            {
                bool ownsDefault=GraphicsSettings.defaultRenderPipeline==runtime;
                bool ownsQuality=QualitySettings.renderPipeline==runtime;
                if(ownsDefault)GraphicsSettings.defaultRenderPipeline=originalDefault;
                if(ownsQuality)QualitySettings.renderPipeline=originalQuality;
                if(ownsDefault&&ownsQuality)
                {
                    QualitySettings.globalTextureMipmapLimit=originalMip;QualitySettings.vSyncCount=originalVSync;
                    Application.targetFrameRate=originalTarget;QualitySettings.anisotropicFiltering=originalAnisotropy;
                    QualitySettings.lodBias=originalLod;QualitySettings.streamingMipmapsMemoryBudget=originalStreaming;
                    foreach(var camera in cameras)camera.Value.Restore();
                }
                Destroy(runtime);
            }
            if(instance==this){instance=null;requestedPreset=null;requestedVSync=null;}
        }
        sealed class CameraState
        {
            readonly Camera camera;
            readonly UniversalAdditionalCameraData data;
            readonly bool hdr,msaa,post,shadows;
            readonly CameraOverrideOption depth;
            readonly AntialiasingMode aa;
            readonly AntialiasingQuality quality;
            public CameraState(Camera view,UniversalAdditionalCameraData extra)
            {
                camera=view;data=extra;hdr=view.allowHDR;msaa=view.allowMSAA;post=extra.renderPostProcessing;
                shadows=extra.renderShadows;depth=extra.requiresDepthOption;aa=extra.antialiasing;quality=extra.antialiasingQuality;
            }
            public void Restore()
            {
                if(camera==null||data==null)return;
                camera.allowHDR=hdr;camera.allowMSAA=msaa;data.renderPostProcessing=post;data.renderShadows=shadows;
                data.requiresDepthOption=depth;data.antialiasing=aa;data.antialiasingQuality=quality;
            }
        }
    }
}
