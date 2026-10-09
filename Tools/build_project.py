"""Reproduce the original project assets. Requires Python, NumPy, SciPy and Pillow.
Run manually; Unity never regenerates or deletes the scene on launch.
"""
import json,math,wave,time
import numpy as np
from scipy.ndimage import gaussian_filter1d
from unity_writer import *
from geometry import *
from textures import build_materials
from world import *
from character import create_character,build_animations

def audio():
    rate=22050;rng=np.random.default_rng(8402)
    specs={'Wind':12,'Birds':12,'Generator':5,'WashHum':6,'Drips':8,'Sand':.26,'Concrete':.20,'Metal':.25,'Wood':.22,'WetConcrete':.3,'Asphalt':.2}
    for name,duration in specs.items():
        n=int(rate*duration);t=np.arange(n)/rate;noise=rng.normal(0,1,n)
        if name=='Wind':
            a=gaussian_filter1d(noise,12)*(.45+.2*np.sin(t*.65))+.04*gaussian_filter1d(noise,3)
        elif name in ['Generator','WashHum']:
            freq=62 if name=='Generator' else 47
            a=.11*np.sin(math.tau*freq*t)+.055*np.sin(math.tau*freq*2*t)+.025*gaussian_filter1d(noise,4)
        elif name=='Birds':
            a=np.zeros(n)
            for at in [1.2,1.6,5.2,8.4,8.8]:
                u=t-at;gate=(u>=0)*(u<.23);env=np.sin(np.clip(u/.23,0,1)*math.pi)**2
                a+=gate*env*.11*np.sin(math.tau*(2400*u+1800*u*u))
        elif name=='Drips':
            a=np.zeros(n)
            for at in [1.1,2.45,4.6,5.2,7.2]:
                u=np.maximum(0,t-at);gate=(t>=at)*(u<.18);a+=gate*np.exp(-u*30)*.35*np.sin(math.tau*(1300*u-1800*u*u))
        else:
            decay=np.exp(-t*(23 if name!='Sand' else 13));attack=np.minimum(t/.007,1)
            a=gaussian_filter1d(noise,1.8 if name=='Sand' else 4)*decay*attack
            if name in ['Metal','Wood']:a+=.14*np.sin(math.tau*(660 if name=='Metal' else 170)*t)*np.exp(-t*22)
            if name=='WetConcrete':a+=noise*.1*np.exp(-t*10)
        if duration>1:
            fade=int(.10*rate);a[:fade]*=np.linspace(0,1,fade);a[-fade:]*=np.linspace(1,0,fade)
        path=f'Assets/_DesertShift/Audio/{name}.wav';p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True)
        with wave.open(str(p),'wb') as f:f.setparams((1,2,rate,0,'NONE','not compressed'));f.writeframes((np.clip(a,-.95,.95)*32767).astype('<i2').tobytes())
        meta(path,'AudioImporter','  serializedVersion: 7\n  defaultSettings:\n    serializedVersion: 2\n    loadType: 0\n    sampleRateSetting: 0\n    sampleRateOverride: 22050\n    compressionFormat: 1\n    quality: 0.65\n    conversionMode: 0\n  forceToMono: 1\n  normalize: 0\n  preloadAudioData: 1\n  loadInBackground: 0\n  ambisonic: 0\n  3D: 1\n')

def setup_files():
    dirs=['Art/Characters/EliasCalder','Art/Environment/Desert','Art/Environment/RV','Art/Environment/CarWash','Art/Environment/Road','Art/Props','Art/Materials','Art/Textures','Art/Decals','Audio','Animations/Character','Animations/Environment','Prefabs/Characters','Prefabs/Environment','Prefabs/Props','Prefabs/Interactables','Scenes','Scripts/Player','Scripts/Camera','Scripts/Interaction','Scripts/Environment','Scripts/UI','Scripts/Utilities','Settings','Editor']
    for d in dirs:(ROOT/'Assets/_DesertShift'/d).mkdir(parents=True,exist_ok=True)
    for p in (ROOT/'Assets').rglob('*.cs'):meta(str(p.relative_to(ROOT)),'MonoImporter','  serializedVersion: 2\n  defaultReferences: []\n  executionOrder: 0\n  icon: {instanceID: 0}\n')
    manifest={'dependencies':{'com.unity.render-pipelines.universal':'17.0.4','com.unity.inputsystem':'1.11.2','com.unity.cinemachine':'3.1.7',**{'com.unity.modules.'+n:'1.0.0' for n in ['ai','animation','audio','director','imageconversion','imgui','jsonserialize','particlesystem','physics','ui','uielements']}}}
    write('Packages/manifest.json',json.dumps(manifest,indent=2)+'\n')
    write('ProjectSettings/ProjectVersion.txt','m_EditorVersion: 6000.0.62f1\n')
    write('ProjectSettings/ProjectSettings.asset',HEAD+'''--- !u!129 &1
PlayerSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 28
  companyName: Desert Shift Studio
  productName: Desert Shift
  bundleVersion: 0.1.0
  defaultScreenWidth: 1920
  defaultScreenHeight: 1080
  defaultIsNativeResolution: 1
  runInBackground: 0
  resizableWindow: 1
  fullscreenMode: 3
  usePlayerLog: 1
  colorSpace: 1
  activeInputHandler: 1
  applicationIdentifier:
    Standalone: com.desertshift.game
  scriptingBackend:
    Standalone: 0
  apiCompatibilityLevelPerPlatform:
    Standalone: 6
  managedStrippingLevel:
    Standalone: 1
  allowUnsafeCode: 0
  stripEngineCode: 1
  useDeterministicCompilation: 1
''')
    layers=['Default','TransparentFX','Ignore Raycast','','Water','UI','','','Player']+['']*23
    write('ProjectSettings/TagManager.asset',HEAD+'--- !u!78 &1\nTagManager:\n  serializedVersion: 2\n  tags: []\n  layers:\n'+''.join('  - '+x+'\n' for x in layers)+'  m_SortingLayers:\n  - name: Default\n    uniqueID: 0\n    locked: 0\n  m_RenderingLayers:\n  - Default\n')
    scene='Assets/_DesertShift/Scenes/SC_DesertTown.unity'
    write('ProjectSettings/EditorBuildSettings.asset',HEAD+f'''--- !u!1045 &1
EditorBuildSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 2
  m_Scenes:
  - enabled: 1
    path: {scene}
    guid: {guid(scene)}
  m_configObjects: {{}}
''')
    write('ProjectSettings/TimeManager.asset',HEAD+'''--- !u!5 &1
TimeManager:
  m_ObjectHideFlags: 0
  Fixed Timestep: 0.02
  Maximum Allowed Timestep: 0.1
  m_TimeScale: 1
  Maximum Particle Timestep: 0.03
''')
    write('.gitignore','[Ll]ibrary/\n[Tt]emp/\n[Oo]bj/\n[Bb]uilds/\n[Ll]ogs/\nUserSettings/\n.vs/\n*.csproj\n*.sln\n__pycache__/\n')
    # Camera and geometry collision layers include everything but the player's own layer.
    write('Assets/_DesertShift/Settings/link.xml','<linker>\n  <assembly fullname="Unity.RenderPipelines.Universal.Runtime" preserve="all" />\n  <assembly fullname="Unity.Cinemachine" preserve="all" />\n</linker>\n')
    meta('Assets/_DesertShift/Settings/link.xml')

def render_settings():
    pipeline='Assets/_DesertShift/Settings/DesertShift_URP.asset';renderer='Assets/_DesertShift/Settings/DesertShift_Renderer.asset'
    write(renderer,HEAD+'''--- !u!114 &11400000
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: 0}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {fileID: 11500000, guid: de640fe3d0db1804a85f9fc8f5cadab6, type: 3}
  m_Name: DesertShift_Renderer
  m_EditorClassIdentifier: 
  debugShaders: {}
  m_RendererFeatures: []
  m_RendererFeatureMap: 
  m_UseNativeRenderPass: 0
  postProcessData: {fileID: 0}
  m_AssetVersion: 2
  m_OpaqueLayerMask:
    serializedVersion: 2
    m_Bits: 4294967295
  m_TransparentLayerMask:
    serializedVersion: 2
    m_Bits: 4294967295
  m_DefaultStencilState:
    overrideStencilState: 0
    stencilReference: 0
    stencilCompareFunction: 8
    passOperation: 0
    failOperation: 0
    zFailOperation: 0
  m_ShadowTransparentReceive: 1
  m_RenderingMode: 0
  m_DepthPrimingMode: 0
  m_CopyDepthMode: 0
  m_DepthAttachmentFormat: 0
  m_DepthTextureFormat: 0
  m_AccurateGbufferNormals: 0
  m_IntermediateTextureMode: 1
''');meta(renderer,'NativeFormatImporter','  mainObjectFileID: 11400000\n')
    write(pipeline,HEAD+f'''--- !u!114 &11400000
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 0}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: bf2edee5c58d82540a51f03df9d42094, type: 3}}
  m_Name: DesertShift_URP
  m_EditorClassIdentifier: 
  k_AssetVersion: 12
  k_AssetPreviousVersion: 12
  m_RendererType: 1
  m_RendererData: {{fileID: 0}}
  m_RendererDataList:
  - {ref(renderer,11400000)}
  m_DefaultRendererIndex: 0
  m_RequireDepthTexture: 1
  m_RequireOpaqueTexture: 0
  m_OpaqueDownsampling: 1
  m_SupportsTerrainHoles: 1
  m_SupportsHDR: 1
  m_HDRColorBufferPrecision: 0
  m_MSAA: 2
  m_RenderScale: 1
  m_UpscalingFilter: 0
  m_MainLightRenderingMode: 1
  m_MainLightShadowsSupported: 1
  m_MainLightShadowmapResolution: 2048
  m_AdditionalLightsRenderingMode: 1
  m_AdditionalLightsPerObjectLimit: 4
  m_AdditionalLightShadowsSupported: 0
  m_AdditionalLightsShadowmapResolution: 1024
  m_AdditionalLightsShadowResolutionTierLow: 256
  m_AdditionalLightsShadowResolutionTierMedium: 512
  m_AdditionalLightsShadowResolutionTierHigh: 1024
  m_ReflectionProbeBlending: 1
  m_ReflectionProbeBoxProjection: 1
  m_ShadowDistance: 90
  m_ShadowCascadeCount: 4
  m_Cascade2Split: 0.25
  m_Cascade3Split: {{x: 0.1, y: 0.3}}
  m_Cascade4Split: {{x: 0.067, y: 0.2, z: 0.467}}
  m_CascadeBorder: 0.1
  m_ShadowDepthBias: 1
  m_ShadowNormalBias: 0.7
  m_SoftShadowsSupported: 1
  m_SoftShadowQuality: 2
  m_UseSRPBatcher: 1
  m_SupportsDynamicBatching: 0
  m_MixedLightingSupported: 1
  m_SupportsLightCookies: 0
  m_UseAdaptivePerformance: 0
  m_ColorGradingMode: 0
  m_ColorGradingLutSize: 32
  m_UseFastSRGBLinearConversion: 0
  m_SupportDataDrivenLensFlare: 0
''');meta(pipeline,'NativeFormatImporter','  mainObjectFileID: 11400000\n')
    write('ProjectSettings/GraphicsSettings.asset',HEAD+f'''--- !u!30 &1
GraphicsSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 16
  m_CustomRenderPipeline: {ref(pipeline,11400000)}
  m_TransparencySortMode: 0
  m_TransparencySortAxis: {{x: 0, y: 0, z: 1}}
  m_DefaultRenderingPath: 1
  m_DefaultMobileRenderingPath: 1
  m_TierSettings: []
  m_LightmapStripping: 0
  m_FogStripping: 0
  m_InstancingStripping: 0
  m_BrgStripping: 0
  m_LightsUseLinearIntensity: 1
  m_LightsUseColorTemperature: 1
  m_LogWhenShaderIsCompiled: 0
  m_AlwaysIncludedShaders: []
''')
    write('ProjectSettings/QualitySettings.asset',HEAD+f'''--- !u!47 &1
QualitySettings:
  m_ObjectHideFlags: 0
  serializedVersion: 5
  m_CurrentQuality: 0
  m_QualitySettings:
  - serializedVersion: 4
    name: Desert High
    pixelLightCount: 4
    shadows: 2
    shadowResolution: 2
    shadowProjection: 1
    shadowCascades: 4
    shadowDistance: 90
    shadowNearPlaneOffset: 2
    shadowCascade2Split: 0.25
    shadowCascade4Split: {{x: 0.067, y: 0.2, z: 0.467}}
    shadowmaskMode: 0
    skinWeights: 4
    globalTextureMipmapLimit: 0
    anisotropicTextures: 1
    antiAliasing: 2
    softParticles: 1
    softVegetation: 1
    realtimeReflectionProbes: 1
    billboardsFaceCameraPosition: 1
    vSyncCount: 1
    lodBias: 1.3
    maximumLODLevel: 0
    streamingMipmapsActive: 1
    streamingMipmapsMemoryBudget: 512
    streamingMipmapsMaxLevelReduction: 2
    particleRaycastBudget: 256
    asyncUploadTimeSlice: 2
    asyncUploadBufferSize: 16
    asyncUploadPersistentBuffer: 1
    customRenderPipeline: {ref(pipeline,11400000)}
    excludedTargetPlatforms: []
  m_TextureMipmapLimitGroupNames: []
  m_PerPlatformDefaultQuality:
    Standalone: 0
''')
    return pipeline,renderer

def sky():
    path='Assets/_DesertShift/Art/Materials/DesertSky.shader'
    write(path,'''Shader "DesertShift/DesertSky"
{
    Properties { _Zenith("Zenith", Color) = (0.18,0.40,0.59,1)
                 _Horizon("Horizon", Color) = (0.70,0.76,0.69,1) }
    SubShader {
        Tags { "Queue"="Background" "RenderType"="Background" "PreviewType"="Skybox" "RenderPipeline"="UniversalPipeline" }
        Cull Off ZWrite Off
        Pass {
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            struct Attributes { float4 positionOS : POSITION; };
            struct Varyings { float4 positionCS : SV_POSITION; float3 dir : TEXCOORD0; };
            CBUFFER_START(UnityPerMaterial)
            float4 _Zenith; float4 _Horizon;
            CBUFFER_END
            Varyings vert(Attributes v) {
                Varyings o; o.positionCS = TransformObjectToHClip(v.positionOS.xyz);
                o.dir = v.positionOS.xyz; return o;
            }
            half4 frag(Varyings i) : SV_Target {
                float3 d=normalize(i.dir);
                float h=pow(saturate(d.y),0.48);
                float3 c=lerp(_Horizon.rgb,_Zenith.rgb,h);
                float glow=pow(saturate(dot(d,normalize(float3(0.53,0.57,-0.63)))),30);
                c+=float3(0.18,0.13,0.06)*glow;
                return half4(c,1);
            }
            ENDHLSL
        }
    }
}
''');meta(path,'ShaderImporter')
    p=f'{ART}/Materials/M_DesertSky.mat'
    write(p,HEAD+f'''--- !u!21 &2100000
Material:
  serializedVersion: 8
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name: M_DesertSky
  m_Shader: {ref(path,4800000,3)}
  m_Parent: {{fileID: 0}}
  m_ValidKeywords: []
  m_InvalidKeywords: []
  m_LightmapFlags: 4
  m_EnableInstancingVariants: 0
  m_DoubleSidedGI: 0
  m_CustomRenderQueue: -1
  stringTagMap: {{}}
  disabledShaderPasses: []
  m_SavedProperties:
    serializedVersion: 3
    m_TexEnvs: []
    m_Ints: []
    m_Floats: []
    m_Colors:
    - _Zenith: {{r: 0.18, g: 0.40, b: 0.59, a: 1}}
    - _Horizon: {{r: 0.70, g: 0.76, b: 0.69, a: 1}}
  m_BuildTextureStacks: []
''');meta(p,'NativeFormatImporter','  mainObjectFileID: 2100000\n');return p

def make_camera(game):
    cam=Node('Main Camera',game,(-74,2.3,-35),(12,10,0),static=False)
    cid=cam.component(20,'''  m_Enabled: 1
  serializedVersion: 2
  m_ClearFlags: 1
  m_BackGroundColor: {r: 0.6, g: 0.7, b: 0.7, a: 0}
  m_projectionMatrixMode: 1
  m_GateFitMode: 2
  m_FOVAxisMode: 0
  m_Iso: 200
  m_ShutterSpeed: 0.005
  m_Aperture: 16
  m_FocusDistance: 10
  m_FocalLength: 50
  m_BladeCount: 5
  m_Curvature: {x: 2, y: 11}
  m_BarrelClipping: 0.25
  m_Anamorphism: 0
  m_SensorSize: {x: 36, y: 24}
  m_LensShift: {x: 0, y: 0}
  m_NormalizedViewPortRect:
    serializedVersion: 2
    x: 0
    y: 0
    width: 1
    height: 1
  near clip plane: 0.055
  far clip plane: 1500
  field of view: 58
  orthographic: 0
  orthographic size: 5
  m_Depth: -1
  m_CullingMask:
    serializedVersion: 2
    m_Bits: 4294967295
  m_RenderingPath: -1
  m_TargetTexture: {fileID: 0}
  m_TargetDisplay: 0
  m_TargetEye: 3
  m_HDR: 1
  m_AllowMSAA: 1
  m_AllowDynamicResolution: 0
  m_ForceIntoRT: 0
  m_OcclusionCulling: 1
  m_StereoConvergence: 10
  m_StereoSeparation: 0.022
''')
    cam.component(81,'  m_Enabled: 1\n');return cam,cid

def reflection(parent,name,pos,size):
    n=Node(name,parent,pos,static=False)
    n.component(215,f'''  m_Enabled: 1
  serializedVersion: 2
  m_Type: 0
  m_Mode: 1
  m_RefreshMode: 2
  m_TimeSlicingMode: 1
  m_Resolution: 128
  m_UpdateFrequency: 0
  m_BoxSize: {vec(size)}
  m_BoxOffset: {{x: 0, y: 0, z: 0}}
  m_NearClip: 0.1
  m_FarClip: 500
  m_ShadowDistance: 35
  m_ClearFlags: 1
  m_BackGroundColor: {{r: 0.4, g: 0.5, b: 0.6, a: 1}}
  m_CullingMask:
    serializedVersion: 2
    m_Bits: 4294967039
  m_IntensityMultiplier: 1
  m_BlendDistance: 2
  m_HDR: 1
  m_BoxProjection: 1
  m_RenderDynamicObjects: 0
  m_UseOcclusionCulling: 1
  m_Importance: 1
  m_CustomBakedTexture: {{fileID: 0}}
  m_BakedTexture: {{fileID: 0}}
''')

def main():
    start=time.time();print('Creating settings and authored textures',flush=True)
    setup_files();pipeline,renderer=render_settings();sky_mat=sky();build_materials();audio();catalog();build_animations()
    game=Node('_Game',static=False);env=Node('_Environment');lighting=Node('_Lighting',static=False);audioroot=Node('_Audio',static=False);ui=Node('_UI',static=False)
    print('Building terrain, road and vegetation',flush=True);make_landscape(env)
    print('Building detailed RV and car wash',flush=True);camp,rv=make_rv(env);wash=make_carwash(env)
    x,z=-73,-33;player=Node('Player',game,(x,float(terrain_height(x,z))+.14,z),layer=8,static=False)
    cc=player.component(143,collider_base()+'''  serializedVersion: 3
  m_Height: 1.78
  m_Radius: 0.25
  m_SlopeLimit: 46
  m_StepOffset: 0.3
  m_SkinWidth: 0.035
  m_MinMoveDistance: 0
  m_Center: {x: 0, y: 0.89, z: 0}
''')
    inp=player.script('PlayerInputHandler');target=Node('CameraTarget',player,(0,1.45,0),layer=8,static=False)
    move=player.script('PlayerMovement',f'  cameraTarget: {{fileID: {target.tid}}}\n')
    interactor=player.script('PlayerInteractor')
    player.script('SurfaceFootsteps','  clips:\n'+''.join('  - '+ref(f'Assets/_DesertShift/Audio/{n}.wav',8300000,3)+'\n' for n in ['Sand','Concrete','Metal','Wood','WetConcrete','Asphalt']))
    print('Skinning Elias Calder and authoring character prefab',flush=True);visual,bones=create_character(player,move)
    save_prefab(player,'Characters','PF_DrCalder')
    cam,cameraid=make_camera(game)
    cameraRig=Node('Cinemachine Camera Rig',game,static=False)
    cameraRig.script('ThirdPersonCameraController',f'  followTarget: {{fileID: {target.tid}}}\n  input: {{fileID: {inp}}}\n  initialYaw: -12\n  initialPitch: 12\n')
    sun,sunid=light(lighting,'Sun',(-30,80,-20),2.15,1000,(1,.88,.68),1,(35,-40,0),2)
    Node('Global Volume',lighting,static=False).script('DesertAtmosphere')
    reflection(lighting,'RV interior reflection',(-77,1.8,-18),(5,4,12))
    reflection(lighting,'Wet wash reflections',(89,2.0,-12),(22,6,18))
    reflection(lighting,'Office reflection',(104,1.8,-15),(10,5,16))
    CLASSES[220]='LightProbeGroup'
    probes=Node('Light probe layout',lighting,static=False)
    positions=[]
    for cx,cz,rx,rz in [(-77,-18,7,8),(89,-12,11,8),(104,-15,5,7)]:
      for px in [-rx,0,rx]:
       for pz in [-rz,0,rz]:
        for py in [.8,2.6,4.5]:positions.append([cx+px,py,cz+pz])
    probes.component(220,'  m_Enabled: 1\n  m_SourcePositions:\n'+''.join('  - '+vec(p)+'\n' for p in positions)+'  m_Dering: 1\n')
    bootstrap=Node('GameBootstrap',game,static=False)
    bootstrap.script('GameBootstrap',f'  renderPipeline: {ref(pipeline,11400000)}\n  rendererData: {ref(renderer,11400000)}\n  skyMaterial: {ref(sky_mat,2100000)}\n  sun: {{fileID: {sunid}}}\n  playerInput: {{fileID: {inp}}}\n')
    ui.script('ExplorationHUD',f'  player: {{fileID: {move}}}\n  input: {{fileID: {inp}}}\n  interactor: {{fileID: {interactor}}}\n')
    for name,vol in [('Wind',.35),('Birds',.32)]:
        Node(name,audioroot,static=False).script('EnvironmentAudio',f'  clip: {ref("Assets/_DesertShift/Audio/"+name+".wav",8300000,3)}\n  volume: {vol}\n  spatial: 0\n  range: 500\n')
    shots=Node('_CinematicViews',static=False)
    camera_views=[('01_Calder_and_Sundowner',[-66,2.0,-7],[-78,1.4,-17],52),('02_Isolated_camp',[-48,8,-53],[-77,1.2,-18],52),('03_Sunset_Splash', [65,4.0,-56],[94,2.2,-12],53),('04_Wet_bay',[88,1.7,-22],[89,1.8,-8],58),('05_RV_interior',[-77,1.85,-18],[-77,1.9,-21],68),('06_Roof_to_desert',[106,5.3,-11],[-63,1,-23],58)]
    for name,pos,look,fov in camera_views:
        d=np.array(look)-pos;yaw=math.degrees(math.atan2(d[0],d[2]));pitch=-math.degrees(math.atan2(d[1],math.sqrt(d[0]**2+d[2]**2)))
        staging={'01_Calder_and_Sundowner':([-73,.08,-13],40),'04_Wet_bay':([89,.25,-16],0)}
        n=Node(name,shots,pos,(pitch,yaw,0),static=False)
        body=f'  fieldOfView: {fov}\n'
        if name in staging:body+=f'  stagePlayer: 1\n  playerPosition: {vec(staging[name][0])}\n  playerYaw: {staging[name][1]}\n'
        n.script('CinematicView',body)
    settings=f'''--- !u!29 &1
OcclusionCullingSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 2
  m_OcclusionBakeSettings:
    smallestOccluder: 5
    smallestHole: 0.25
    backfaceThreshold: 100
  m_SceneGUID: 00000000000000000000000000000000
  m_OcclusionCullingData: {{fileID: 0}}
--- !u!104 &2
RenderSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 10
  m_Fog: 1
  m_FogColor: {{r: 0.67, g: 0.69, b: 0.61, a: 1}}
  m_FogMode: 3
  m_FogDensity: 0.00165
  m_LinearFogStart: 180
  m_LinearFogEnd: 1100
  m_AmbientSkyColor: {{r: 0.43, g: 0.57, b: 0.66, a: 1}}
  m_AmbientEquatorColor: {{r: 0.61, g: 0.48, b: 0.32, a: 1}}
  m_AmbientGroundColor: {{r: 0.33, g: 0.25, b: 0.16, a: 1}}
  m_AmbientIntensity: 1
  m_AmbientMode: 1
  m_SubtractiveShadowColor: {{r: 0.22, g: 0.26, b: 0.28, a: 1}}
  m_SkyboxMaterial: {ref(sky_mat,2100000)}
  m_HaloStrength: 0.1
  m_FlareStrength: 0.1
  m_FlareFadeSpeed: 3
  m_HaloTexture: {{fileID: 0}}
  m_SpotCookie: {{fileID: 0}}
  m_DefaultReflectionMode: 0
  m_DefaultReflectionResolution: 128
  m_ReflectionBounces: 1
  m_ReflectionIntensity: 1
  m_CustomReflection: {{fileID: 0}}
  m_Sun: {{fileID: {sunid}}}
  m_UseRadianceAmbientProbe: 0
--- !u!157 &3
LightmapSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 13
  m_GIWorkflowMode: 1
  m_GISettings:
    serializedVersion: 2
    m_BounceScale: 1
    m_IndirectOutputScale: 1
    m_AlbedoBoost: 1
    m_EnvironmentLightingMode: 0
    m_EnableBakedLightmaps: 0
    m_EnableRealtimeLightmaps: 0
  m_LightingDataAsset: {{fileID: 0}}
  m_LightingSettings: {{fileID: 0}}
'''
    print('Serializing the fully populated scene',flush=True);save_scene(settings)
    for p in (ROOT/'Assets').rglob('*'):
        rel=str(p.relative_to(ROOT))
        if p.is_dir() and not (ROOT/(rel+'.meta')).exists():
            write(rel+'.meta',f'fileFormatVersion: 2\nguid: {guid(rel)}\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {{}}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n')
    # Scratch mirror for geometry QA, not a replacement game engine.
    qa=ROOT.parent/'.checks';qa.mkdir(exist_ok=True)
    import gzip,pickle,os
    for m in PREVIEW['meshes'].values():
        for key in ['v','n','uv','weights','bind']:
            if key in m:m[key]=np.asarray(m[key],dtype=np.float32)
        m['t']=np.asarray(m['t'],dtype=np.uint32)
    raw=pickle.dumps(PREVIEW,protocol=5)
    packed=gzip.compress(raw,compresslevel=3)
    temp=qa/'scene_preview.tmp';temp.write_bytes(packed);os.replace(temp,qa/'scene_preview.pkl.gz')
    stats={'scene_objects':len(Node.all),'unique_meshes':len(MESHES),'materials':len(MATERIALS),'mesh_triangles':sum(len(m.t)//3 for _,m in MESHES.values()),'render_instances':sum(n.mesh is not None for n in Node.all),'animation_clips':14,'skinned_character':True,'world_size_m':[600,600],'unity_editor_available':False}
    write('Documentation/AssetInventory.json',json.dumps(stats,indent=2)+'\n')
    write('Documentation/CinematicViews.json',json.dumps(camera_views,indent=2)+'\n')
    print(json.dumps(stats),flush=True);print('Generation seconds',round(time.time()-start,1),flush=True)

if __name__=='__main__':main()
