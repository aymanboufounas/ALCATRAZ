#if UNITY_EDITOR
using System;
using System.Reflection;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Blackstone.Foundation.Editor
{
    // Synchronous lifecycle fixture. Existing gameplay graphics are suspended
    // while a temporary scene owner clones two distinct, temporary URP assets.
    // It does not render a frame or claim a graphics/performance certification.
    public static class GraphicsGameplayChecks
    {
        static int checks;
        static void Check(bool condition,string message)
        {checks++;if(!condition)throw new InvalidOperationException("Graphics regression: "+message);}
        static FieldInfo Field(string name)=>typeof(FoundationGraphics).GetField(name,BindingFlags.Static|BindingFlags.NonPublic);
        [MenuItem("Alcatraz/Validate Shared Graphics Lifecycle (Play Mode)",priority=32)]
        public static void Run()
        {
            if(!EditorApplication.isPlaying)throw new InvalidOperationException("Enter Play Mode before checking runtime graphics. No tests ran.");
            var active=(QualitySettings.renderPipeline!=null?QualitySettings.renderPipeline:GraphicsSettings.defaultRenderPipeline) as UniversalRenderPipelineAsset;
            if(active==null)throw new InvalidOperationException("The loaded scene must use URP before checking runtime graphics. No tests ran.");
            var originalDefault=GraphicsSettings.defaultRenderPipeline;var originalQuality=QualitySettings.renderPipeline;
            int mip=QualitySettings.globalTextureMipmapLimit,vsync=QualitySettings.vSyncCount,target=Application.targetFrameRate;
            float lod=QualitySettings.lodBias,budget=QualitySettings.streamingMipmapsMemoryBudget;
            var aniso=QualitySettings.anisotropicFiltering;
            var instanceField=Field("instance");var presetField=Field("requestedPreset");var vsyncField=Field("requestedVSync");
            var previous=instanceField.GetValue(null) as FoundationGraphics;
            bool previousEnabled=previous!=null&&previous.enabled;
            object oldRequestedPreset=presetField.GetValue(null),oldRequestedVSync=vsyncField.GetValue(null);
            bool qualityPref=PlayerPrefs.HasKey("Blackstone.Quality"),vsyncPref=PlayerPrefs.HasKey("Blackstone.VSync");
            int savedQuality=PlayerPrefs.GetInt("Blackstone.Quality",-987),savedVsync=PlayerPrefs.GetInt("Blackstone.VSync",-654);
            var root=new GameObject("Temporary shared graphics lifecycle");root.hideFlags=HideFlags.HideAndDontSave;
            var owner=new GameObject("Temporary graphics owner");owner.transform.SetParent(root.transform);
            var defaultAsset=UnityEngine.Object.Instantiate(active);var overrideAsset=UnityEngine.Object.Instantiate(active);
            defaultAsset.hideFlags=overrideAsset.hideFlags=HideFlags.HideAndDontSave;
            defaultAsset.renderScale=.77f;overrideAsset.renderScale=.91f;
            defaultAsset.supportsHDR=false;overrideAsset.supportsHDR=true;
            var cameraObject=new GameObject("Temporary graphics camera");cameraObject.transform.SetParent(root.transform);
            var camera=cameraObject.AddComponent<Camera>();camera.enabled=false;
            camera.allowHDR=false;camera.allowMSAA=true;
            var cameraData=camera.GetUniversalAdditionalCameraData();cameraData.renderPostProcessing=false;
            cameraData.antialiasing=AntialiasingMode.None;cameraData.antialiasingQuality=AntialiasingQuality.Low;
            cameraData.requiresDepthOption=CameraOverrideOption.UsePipelineSettings;cameraData.renderShadows=false;
            UniversalRenderPipelineAsset runtime=null;checks=0;
            try
            {
                if(previous!=null)previous.enabled=false;
                // Isolate the singleton for this synchronous editor-only fixture.
                // No production object or source rendering asset is destroyed.
                instanceField.SetValue(null,null);presetField.SetValue(null,null);vsyncField.SetValue(null,null);
                GraphicsSettings.defaultRenderPipeline=defaultAsset;QualitySettings.renderPipeline=overrideAsset;
                QualitySettings.globalTextureMipmapLimit=1;QualitySettings.vSyncCount=0;Application.targetFrameRate=47;
                QualitySettings.anisotropicFiltering=AnisotropicFiltering.Disable;QualitySettings.lodBias=.87f;
                QualitySettings.streamingMipmapsMemoryBudget=333;
                var service=FoundationGraphics.Ensure(owner);
                runtime=QualitySettings.renderPipeline as UniversalRenderPipelineAsset;
                Check(service!=null&&runtime!=null&&runtime!=defaultAsset&&runtime!=overrideAsset,
                    "runtime settings clone the effective URP asset");
                Check(GraphicsSettings.defaultRenderPipeline==runtime,"both rendering selections use the owned clone");
                Check(FoundationGraphics.Ensure(owner)==service,"repeated setup reuses the same scene owner");

                FoundationGraphics.SetVSync(false,false);
                foreach(int level in new[]{2,3})
                {
                    FoundationGraphics.SetPreset(level,false);FoundationGraphics.ApplyCamera(camera);
                    Check(FoundationGraphics.SelectedPreset==level&&QualitySettings.globalTextureMipmapLimit==0,
                        "High/Ultra preserve full source texture detail");
                    Check(runtime.renderScale==1&&runtime.msaaSampleCount==1,
                        "native output does not stack MSAA with post-process AA");
                    Check(runtime.mainLightShadowmapResolution==4096&&runtime.shadowCascadeCount==4,
                        "High/Ultra configure detailed cascaded main-light shadows");
                    Check(cameraData.antialiasing==AntialiasingMode.SubpixelMorphologicalAntiAliasing
                        &&cameraData.antialiasingQuality==AntialiasingQuality.High&&!camera.allowMSAA,
                        "the same profile reaches actual gameplay camera AA settings");
                    Check(!FoundationGraphics.VSync&&QualitySettings.vSyncCount==0&&Application.targetFrameRate==-1,
                        "profile switches retain explicit VSync choice and remove stale scene frame caps");
                }
                Check(Mathf.Abs(defaultAsset.renderScale-.77f)<.0001f&&Mathf.Abs(overrideAsset.renderScale-.91f)<.0001f,
                    "neither default nor quality source assets are modified");
                Check(runtime.supportsHDR&&!defaultAsset.supportsHDR,
                    "runtime setup clones the active quality override rather than the different default asset");
                FoundationGraphics.SetPreset(0,false);FoundationGraphics.ApplyCamera(camera);
                Check(QualitySettings.globalTextureMipmapLimit==2&&runtime.renderScale<1
                    &&cameraData.antialiasing==AntialiasingMode.FastApproximateAntialiasing,
                    "Low changes textures, render scale and actual camera AA together");
                FoundationGraphics.SetVSync(true,false);
                Check(FoundationGraphics.VSync&&QualitySettings.vSyncCount==1,"VSync changes reach global rendering");
                Check(PlayerPrefs.HasKey("Blackstone.Quality")==qualityPref&&PlayerPrefs.GetInt("Blackstone.Quality",-987)==savedQuality
                    &&PlayerPrefs.HasKey("Blackstone.VSync")==vsyncPref&&PlayerPrefs.GetInt("Blackstone.VSync",-654)==savedVsync,
                    "nonpersistent checks leave the user's saved settings untouched");

                UnityEngine.Object.DestroyImmediate(owner);owner=null;
                Check(GraphicsSettings.defaultRenderPipeline==defaultAsset&&QualitySettings.renderPipeline==overrideAsset,
                    "destroying the scene owner restores distinct default and quality selections");
                Check(QualitySettings.globalTextureMipmapLimit==1&&QualitySettings.vSyncCount==0&&Application.targetFrameRate==47,
                    "destroying the owner restores texture, VSync and frame-cap state");
                Check(QualitySettings.anisotropicFiltering==AnisotropicFiltering.Disable
                    &&Mathf.Abs(QualitySettings.lodBias-.87f)<.0001f&&Mathf.Abs(QualitySettings.streamingMipmapsMemoryBudget-333)<.001f,
                    "destroying the owner restores sampling, LOD and streaming budget");
                Check(!camera.allowHDR&&camera.allowMSAA&&!cameraData.renderPostProcessing&&!cameraData.renderShadows
                    &&cameraData.antialiasing==AntialiasingMode.None&&cameraData.antialiasingQuality==AntialiasingQuality.Low
                    &&cameraData.requiresDepthOption==CameraOverrideOption.UsePipelineSettings,
                    "destroying the owner restores original camera overrides");

                // Also exercise a null quality override: it must stay null rather
                // than being overwritten with the previous default asset.
                QualitySettings.renderPipeline=null;
                owner=new GameObject("Temporary default-only graphics owner");owner.transform.SetParent(root.transform);
                FoundationGraphics.Ensure(owner);
                Check(QualitySettings.renderPipeline!=null&&QualitySettings.renderPipeline!=defaultAsset,
                    "a scene without an override still receives a runtime clone");
                UnityEngine.Object.DestroyImmediate(owner);owner=null;
                Check(GraphicsSettings.defaultRenderPipeline==defaultAsset&&QualitySettings.renderPipeline==null,
                    "a null quality override is restored exactly");
                Debug.Log("Shared graphics lifecycle passed: "+checks+" assertions using real URP assets and camera components. Rendering and performance remain unverified.");
            }
            finally
            {
                try
                {
                    if(owner!=null)UnityEngine.Object.DestroyImmediate(owner);
                    UnityEngine.Object.DestroyImmediate(root);
                    GraphicsSettings.defaultRenderPipeline=originalDefault;QualitySettings.renderPipeline=originalQuality;
                    QualitySettings.globalTextureMipmapLimit=mip;QualitySettings.vSyncCount=vsync;Application.targetFrameRate=target;
                    QualitySettings.anisotropicFiltering=aniso;QualitySettings.lodBias=lod;QualitySettings.streamingMipmapsMemoryBudget=budget;
                    instanceField.SetValue(null,previous);presetField.SetValue(null,oldRequestedPreset);vsyncField.SetValue(null,oldRequestedVSync);
                    if(previous!=null)previous.enabled=previousEnabled;
                }
                finally
                {UnityEngine.Object.DestroyImmediate(defaultAsset);UnityEngine.Object.DestroyImmediate(overrideAsset);}
            }
        }
    }
}
#endif
