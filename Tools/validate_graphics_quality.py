"""Validate native graphics bindings and shared-setting integration, not rendering."""
from pathlib import Path
import json
import re
import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ROOT / 'Assets/_DesertShift/Settings'
POST_DATA = '41439944d30ece34e96484bdb6645b55'


def native(path):
    text = path.read_text()
    text = re.sub(r'^%.*\n', '', text, flags=re.M)
    text = re.sub(r'^--- !u!\d+ &-?\d+', '---', text, flags=re.M)
    documents = list(yaml.load_all(text, Loader=yaml.CSafeLoader))
    # Saving the editor-created SSAO feature adds a native subasset document.
    # Select the main asset rather than rejecting valid multi-document YAML.
    bodies = [body for document in documents if isinstance(document, dict)
              for body in document.values() if isinstance(body, dict)]
    return next((body for body in bodies if body.get('m_Name') == path.stem), bodies[0])


def guid(path):
    return re.search(r'^guid: ([0-9a-f]{32})$', Path(str(path) + '.meta').read_text(), re.M)[1]


def validate():
    checks = 0
    errors = []

    def check(condition, label):
        nonlocal checks
        checks += 1
        if not condition:
            errors.append(label)

    pipe_path = SETTINGS / 'DesertShift_URP.asset'
    renderer_path = SETTINGS / 'DesertShift_Renderer.asset'
    pipe, renderer = native(pipe_path), native(renderer_path)
    graphics = native(ROOT / 'ProjectSettings/GraphicsSettings.asset')
    quality = native(ROOT / 'ProjectSettings/QualitySettings.asset')
    check(graphics['m_CustomRenderPipeline']['guid'] == guid(pipe_path), 'Project default selects the committed URP pipeline.')
    check(all(level['customRenderPipeline']['guid'] == guid(pipe_path) for level in quality['m_QualitySettings']), 'Native quality levels retain the compatible URP baseline.')
    selected = pipe['m_RendererDataList'][pipe['m_DefaultRendererIndex']]
    check(selected['guid'] == guid(renderer_path), 'Pipeline selects the committed renderer.')
    check(renderer['postProcessData'] == {'fileID': 11400000, 'guid': POST_DATA, 'type': 2}, 'Renderer references the official URP post-processing resource.')
    check(pipe['m_SupportsHDR'] == 1 and pipe['m_ColorGradingMode'] == 1, 'HDR lighting and HDR color grading are available.')
    check(pipe['m_RequireDepthTexture'] == 1, 'Depth remains available for coastal water and post-processing.')
    check(pipe['m_MainLightShadowsSupported'] == 1 and pipe['m_AdditionalLightShadowsSupported'] == 1, 'Main and local-light shadow capabilities are retained.')
    check(pipe['m_MainLightShadowmapResolution'] >= 4096 and pipe['m_ShadowCascadeCount'] == 4, 'Baseline supports detailed cascaded shadows.')
    check(pipe['m_ReflectionProbeBlending'] == 1 and pipe['m_ReflectionProbeBoxProjection'] == 1, 'Environment reflection capabilities remain available.')
    check(pipe['m_UseSRPBatcher'] == 1, 'SRP batching stays enabled.')
    for kind in ['m_OpaqueLayerMask', 'm_TransparentLayerMask']:
        mask = renderer[kind]['m_Bits']
        check((mask & (1 << 8)) != 0 and (mask & 1) != 0, f'{kind} includes the player and world layers.')

    sources = {name: (ROOT / path).read_text() for name, path in {
        'service': 'Assets/Game/Foundation/Scripts/FoundationGraphics.cs',
        'bootstrap': 'Assets/Game/Foundation/Scripts/FoundationBootstrap.cs',
        'preparation': 'Assets/Game/Foundation/Editor/FoundationPreparation.cs',
        'editor': 'Assets/_DesertShift/Editor/ProjectTools.cs',
        'legacy': 'Assets/_DesertShift/Scripts/Utilities/GameBootstrap.cs',
        'story': 'Assets/Game/Scripts/UI/PrisonHUD.cs',
        'title': 'Assets/Game/Foundation/Scripts/FoundationHUD.cs',
        'pause': 'Assets/Game/Foundation/Scripts/PrisonPauseMenu.cs',
        'water': 'Assets/Game/Shaders/CoastalWater.shader',
        'presentation': 'Assets/Game/Alcatraz/Scripts/AlcatrazPresentation.cs',
    }.items()}
    check('FoundationGraphics.Ensure(gameObject)' in sources['bootstrap'], 'Foundation scenes create the shared graphics owner.')
    for name in ['story', 'title', 'pause']:
        check('FoundationGraphics.SetPreset(' in sources[name] and 'QualitySettings.SetQualityLevel(' not in sources[name], f'{name} UI uses the shared preset model.')
    for name in ['story', 'pause']:
        check('GraphicsRules.ResolutionNames' in sources[name] and 'GraphicsRules.ResolutionIndex(' in sources[name], f'{name} display settings use the shared 4K-capable choices.')
    check('runtimePipeline' not in sources['story'], 'Story UI no longer competes with the graphics owner for a pipeline clone.')
    check('if(open&&!wasOpen)displayInitialized=false' in sources['pause'] and 'if(enteringSettings)displayInitialized=false' in sources['pause'], 'Display staging refreshes on menu entry without overwriting edits every frame.')
    check('ProjectTools.EnsureRendering();' in sources['preparation'], 'Rendering preparation is checked even when character imports are cached.')
    check('Packages/com.unity.render-pipelines.universal/Runtime/Data/PostProcessData.asset' in sources['editor'], 'Editor repair resolves the official package resource.')
    check('public static void ValidateRendering()' in sources['editor'] and 'feature.isActive&&AssetDatabase.Contains(feature)' in sources['editor'], 'Editor preflight requires saved, active ambient occlusion.')
    check('rendererFeatures.Add' not in sources['legacy'] and 'rendererFeatures.Remove' not in sources['legacy'], 'Runtime bootstrap does not mutate shared renderer features.')
    check('GlossyEnvironmentReflection(reflectedDirection,input.positionWS,' in sources['water'], 'Water samples actual environment reflection.')
    check('_REFLECTION_PROBE_BLENDING' in sources['water'] and '_REFLECTION_PROBE_BOX_PROJECTION' in sources['water'], 'Water retains supported reflection variants.')
    check('SampleSceneDepth(screenUV)' in sources['water'], 'Water retains shoreline depth sampling.')
    check('DynamicGI.UpdateEnvironment();' in sources['presentation'] and 'RenderSettings.ambientProbe = ambient;' in sources['presentation'], 'Sky reflection refresh retains the explicit readable ambient probe.')

    # This supplied asset has genuine 4K source maps. A quality preset should
    # preserve them, rather than generating bigger images from smaller sources.
    texture_rows = []
    folder = ROOT / 'Assets/Game/Supplied/Resources/AlcatrazExtras/PrisonToilet/Textures'
    for path in sorted(folder.glob('*.png')):
        with Image.open(path) as image:
            width, height = image.size
        meta = yaml.safe_load(Path(str(path) + '.meta').read_text())['TextureImporter']
        check(meta['maxTextureSize'] >= max(width, height), f'Original supplied texture resolution is preserved: {path.name}')
        texture_rows.append({'path': str(path.relative_to(ROOT)), 'width': width, 'height': height, 'import_max': meta['maxTextureSize']})
    check(len(texture_rows) == 5, 'All five original 4K prison-toilet maps are present.')
    return {'status': 'FAIL' if errors else 'PASS', 'checks': checks, 'errors': errors,
            'preserved_source_textures': texture_rows,
            'official_postprocess_data_guid': POST_DATA,
            'scope': 'Native pipeline/resource/layer bindings, source integration guards and original texture dimensions. Preset values are tested separately by executable C# rules. Unity resource preparation, shader/API compilation, live settings, rendered quality and 1440p/4K performance remain unverified.',
            'serialized_renderer_features': len(renderer.get('m_RendererFeatures', [])),
            'unity_preparation_required': 'The editor must validate or create a saved, active SSAO feature before Play/build. Source checks do not establish successful shader resource preparation.'}


if __name__ == '__main__':
    result = validate()
    print(json.dumps(result, indent=2))
    raise SystemExit(result['status'] != 'PASS')
