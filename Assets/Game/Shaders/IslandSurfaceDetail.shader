Shader "Blackstone/Island Surface Detail"
{
    Properties
    {
        [MainTexture] _BaseMap("Original island atlas", 2D) = "white" {}
        [MainColor] _BaseColor("Atlas tint", Color) = (1,1,1,1)
        _GroundMap("Ground detail albedo", 2D) = "gray" {}
        _WallMap("Masonry detail albedo", 2D) = "gray" {}
        [Normal] _GroundNormal("Ground detail normal", 2D) = "bump" {}
        [Normal] _WallNormal("Masonry detail normal", 2D) = "bump" {}
        _GroundSurface("Ground AO (G), smoothness (A)", 2D) = "white" {}
        _WallSurface("Masonry AO (G), smoothness (A)", 2D) = "white" {}
        _GroundWorldScale("Ground repeats per metre", Range(.05,4)) = .85
        _WallWorldScale("Masonry repeats per metre", Range(.05,4)) = .65
        _DetailColorStrength("Conservative detail color", Range(0,1)) = .12
        _GroundAlbedoReplacement("Pale ground resurfacing", Range(0,1)) = .6
        _DetailNormalStrength("Detail normal strength", Range(0,2)) = .5
        _DetailOcclusionStrength("Detail occlusion", Range(0,1)) = .3
        _SurfaceVariation("Smoothness variation", Range(0,1)) = .35
        _GroundSmoothness("Ground smoothness", Range(0,1)) = .18
        _WallSmoothness("Masonry smoothness", Range(0,1)) = .12
        _TriplanarSharpness("Projection blend sharpness", Range(1,8)) = 4
        _GroundSlopeStart("Ground blend starts at normal Y", Range(0,1)) = .5
        _GroundSlopeEnd("Ground blend ends at normal Y", Range(0,1)) = .85
        _DetailFadeStart("Detail fade starts in metres", Float) = 45
        _DetailFadeEnd("Detail fade ends in metres", Float) = 120
        [Enum(UnityEngine.Rendering.CullMode)] _Cull("Cull", Float) = 2
    }
    SubShader
    {
        Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" "Queue"="Geometry" }
        LOD 300
        Cull [_Cull]

        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
        #include "Packages/com.unity.render-pipelines.core/ShaderLibrary/Packing.hlsl"

        TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);
        TEXTURE2D(_GroundMap); SAMPLER(sampler_GroundMap);
        TEXTURE2D(_WallMap); SAMPLER(sampler_WallMap);
        TEXTURE2D(_GroundNormal); SAMPLER(sampler_GroundNormal);
        TEXTURE2D(_WallNormal); SAMPLER(sampler_WallNormal);
        TEXTURE2D(_GroundSurface); SAMPLER(sampler_GroundSurface);
        TEXTURE2D(_WallSurface); SAMPLER(sampler_WallSurface);

        // One identical layout across forward, depth, normals and shadow passes.
        CBUFFER_START(UnityPerMaterial)
            float4 _BaseMap_ST;
            half4 _BaseColor;
            float _GroundWorldScale, _WallWorldScale;
            half _DetailColorStrength, _GroundAlbedoReplacement, _DetailNormalStrength;
            half _DetailOcclusionStrength, _SurfaceVariation;
            half _GroundSmoothness, _WallSmoothness;
            float _TriplanarSharpness, _GroundSlopeStart, _GroundSlopeEnd;
            float _DetailFadeStart, _DetailFadeEnd;
            float _Cull;
        CBUFFER_END

        struct Attributes
        {
            float4 positionOS : POSITION;
            float3 normalOS : NORMAL;
            float2 uv : TEXCOORD0;
            float2 lightmapUV : TEXCOORD1;
            UNITY_VERTEX_INPUT_INSTANCE_ID
        };

        struct DetailSample
        {
            half3 albedo;
            half3 normalTS;
            half2 surface;
        };

        DetailSample GroundDetail(float2 uv, half strength)
        {
            DetailSample detail;
            detail.albedo = SAMPLE_TEXTURE2D(_GroundMap, sampler_GroundMap, uv).rgb;
            detail.normalTS = UnpackNormalScale(SAMPLE_TEXTURE2D(_GroundNormal, sampler_GroundNormal, uv), strength);
            half4 surface = SAMPLE_TEXTURE2D(_GroundSurface, sampler_GroundSurface, uv);
            detail.surface = surface.ga;
            return detail;
        }

        DetailSample WallDetail(float2 uv, half strength)
        {
            DetailSample detail;
            detail.albedo = SAMPLE_TEXTURE2D(_WallMap, sampler_WallMap, uv).rgb;
            detail.normalTS = UnpackNormalScale(SAMPLE_TEXTURE2D(_WallNormal, sampler_WallNormal, uv), strength);
            half4 surface = SAMPLE_TEXTURE2D(_WallSurface, sampler_WallSurface, uv);
            detail.surface = surface.ga;
            return detail;
        }

        void SampleIslandDetail(float3 positionWS, half3 geometricNormalWS,
            out half3 detailColor, out half3 normalWS, out half occlusion, out half smoothness,
            out half3 groundAlbedo, out half detailFade)
        {
            half3 n = NormalizeNormalPerPixel(geometricNormalWS);
            float groundBlend = saturate((n.y - _GroundSlopeStart) / max(.001, _GroundSlopeEnd - _GroundSlopeStart));
            groundBlend = groundBlend * groundBlend * (3 - 2 * groundBlend);
            smoothness = lerp(_WallSmoothness, _GroundSmoothness, groundBlend);
            detailColor = 1;
            groundAlbedo = 1;
            occlusion = 1;
            normalWS = n;

            // Fade small details before they shimmer and skip their reads in the distance.
            float distanceToCamera = distance(positionWS, GetCameraPositionWS());
            half fade = 1 - saturate((distanceToCamera - _DetailFadeStart)
                / max(.001, _DetailFadeEnd - _DetailFadeStart));
            detailFade = fade;
            UNITY_BRANCH
            if (fade <= 0) return;

            float3 weights = pow(abs((float3)n), max(1, _TriplanarSharpness));
            weights /= max(dot(weights, float3(1,1,1)), .0001);
            float3 axisSign = float3(n.x < 0 ? -1 : 1, n.y < 0 ? -1 : 1, n.z < 0 ? -1 : 1);
            // Tangent/bitangent cross products point along each signed projection normal.
            float2 uvX = float2(-axisSign.x * positionWS.z, positionWS.y);
            float2 uvY = float2(positionWS.x, -axisSign.y * positionWS.z);
            float2 uvZ = float2(axisSign.z * positionWS.x, positionWS.y);
            half normalStrength = _DetailNormalStrength * fade;
            DetailSample x = WallDetail(uvX * _WallWorldScale, normalStrength);
            DetailSample z = WallDetail(uvZ * _WallWorldScale, normalStrength);
            DetailSample y;
            // Horizontal ground uses its own surface; undersides remain masonry.
            // The common flat-ground/vertical-wall cases need only nine texture reads.
            UNITY_BRANCH
            if (groundBlend >= .999)
                y = GroundDetail(uvY * _GroundWorldScale, normalStrength);
            else if (groundBlend <= .001)
                y = WallDetail(uvY * _WallWorldScale, normalStrength);
            else
            {
                DetailSample ground = GroundDetail(uvY * _GroundWorldScale, normalStrength);
                DetailSample wall = WallDetail(uvY * _WallWorldScale, normalStrength);
                y.albedo = lerp(wall.albedo, ground.albedo, groundBlend);
                y.normalTS = SafeNormalize(lerp(wall.normalTS, ground.normalTS, groundBlend));
                y.surface = lerp(wall.surface, ground.surface, groundBlend);
            }
            groundAlbedo = y.albedo;

            // Whiteout reorientation preserves the original geometric normal for a
            // neutral tangent map. A naive axis swizzle would flatten sloped surfaces.
            half3 nx = SafeNormalize(half3(n.x * x.normalTS.z, n.y + x.normalTS.y,
                n.z - axisSign.x * x.normalTS.x));
            half3 ny = SafeNormalize(half3(n.x + y.normalTS.x, n.y * y.normalTS.z,
                n.z - axisSign.y * y.normalTS.y));
            half3 nz = SafeNormalize(half3(n.x + axisSign.z * z.normalTS.x,
                n.y + z.normalTS.y, n.z * z.normalTS.z));
            normalWS = NormalizeNormalPerPixel(nx * weights.x + ny * weights.y + nz * weights.z);

            half3 detailAlbedo = x.albedo * weights.x + y.albedo * weights.y + z.albedo * weights.z;
            // Keep the scanned windows, doors, paint and large color features intact.
            // Detail can vary atlas color by only 6% at the default .12 strength.
            detailColor = lerp(half3(1,1,1), clamp(detailAlbedo * 2, .5h, 1.5h), _DetailColorStrength * fade);
            half2 surface = x.surface * weights.x + y.surface * weights.y + z.surface * weights.z;
            occlusion = lerp(1, surface.x, _DetailOcclusionStrength * fade);
            smoothness = saturate(smoothness * lerp(1, .5h + surface.y, _SurfaceVariation * fade));
        }
        ENDHLSL

        Pass
        {
            Name "IslandForward"
            Tags { "LightMode"="UniversalForwardOnly" }
            ZWrite On
            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex IslandVertex
            #pragma fragment IslandFragment
            #pragma multi_compile_instancing
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
            #pragma multi_compile _ _FORWARD_PLUS
            #pragma multi_compile_fragment _ _ADDITIONAL_LIGHT_SHADOWS
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile_fragment _ _SCREEN_SPACE_OCCLUSION
            #pragma multi_compile_fragment _ _REFLECTION_PROBE_BLENDING
            #pragma multi_compile_fragment _ _REFLECTION_PROBE_BOX_PROJECTION
            #pragma multi_compile _ LIGHTMAP_ON
            #pragma multi_compile _ DIRLIGHTMAP_COMBINED
            #pragma multi_compile _ LIGHTMAP_SHADOW_MIXING
            #pragma multi_compile _ SHADOWS_SHADOWMASK
            #pragma multi_compile_fog

            struct ForwardVaryings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                half3 normalWS : TEXCOORD1;
                float2 uv : TEXCOORD2;
                half4 fogAndVertexLight : TEXCOORD3;
                DECLARE_LIGHTMAP_OR_SH(lightmapUV, vertexSH, 4);
                UNITY_VERTEX_INPUT_INSTANCE_ID
                UNITY_VERTEX_OUTPUT_STEREO
            };

            ForwardVaryings IslandVertex(Attributes input)
            {
                ForwardVaryings output = (ForwardVaryings)0;
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_TRANSFER_INSTANCE_ID(input, output);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(output);
                VertexPositionInputs position = GetVertexPositionInputs(input.positionOS.xyz);
                output.positionCS = position.positionCS;
                output.positionWS = position.positionWS;
                output.normalWS = TransformObjectToWorldNormal(input.normalOS);
                output.uv = TRANSFORM_TEX(input.uv, _BaseMap);
                output.fogAndVertexLight = half4(ComputeFogFactor(position.positionCS.z),
                    VertexLighting(position.positionWS, output.normalWS));
                OUTPUT_LIGHTMAP_UV(input.lightmapUV, unity_LightmapST, output.lightmapUV);
                OUTPUT_SH(output.normalWS, output.vertexSH);
                return output;
            }

            half4 IslandFragment(ForwardVaryings input) : SV_Target
            {
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);
                half3 detailColor, normalWS;
                half3 groundAlbedo;
                half occlusion, smoothness, detailFade;
                SampleIslandDetail(input.positionWS, input.normalWS, detailColor, normalWS,
                    occlusion, smoothness, groundAlbedo, detailFade);

                SurfaceData surface = (SurfaceData)0;
                half3 atlas = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, input.uv).rgb * _BaseColor.rgb;
                // Resurface pale neutral, nearly horizontal areas with the real
                // ground texture. Dark asphalt, colored vegetation and all wall
                // features retain their original atlas color and UV placement.
                half luminance = dot(atlas, half3(.2126h, .7152h, .0722h));
                // Perceptual chroma keeps visually neutral pale concrete in the
                // mask; linear RGB would overstate its slight warm scan tint.
                half3 perceptualAtlas = sqrt(max(atlas, 0));
                half maximum = max(perceptualAtlas.r, max(perceptualAtlas.g, perceptualAtlas.b));
                half minimum = min(perceptualAtlas.r, min(perceptualAtlas.g, perceptualAtlas.b));
                half chroma = (maximum - minimum) / max(maximum, .001h);
                half groundMask = smoothstep(.85h, .95h, NormalizeNormalPerPixel(input.normalWS).y)
                    * smoothstep(.28h, .60h, luminance) * (1 - smoothstep(.20h, .45h, chroma));
                half replacement = groundMask * _GroundAlbedoReplacement * detailFade;
                half3 macroTint = clamp(atlas / max(luminance, .1h), .75h, 1.25h);
                surface.albedo = lerp(atlas * detailColor, groundAlbedo * macroTint, replacement);
                surface.metallic = 0;
                surface.specular = half3(.04h,.04h,.04h);
                surface.smoothness = smoothness;
                surface.normalTS = half3(0,0,1);
                surface.occlusion = occlusion;
                surface.alpha = 1;

                InputData lighting = (InputData)0;
                lighting.positionWS = input.positionWS;
                lighting.normalWS = normalWS;
                lighting.viewDirectionWS = GetWorldSpaceNormalizeViewDir(input.positionWS);
                #if defined(_MAIN_LIGHT_SHADOWS_SCREEN)
                    lighting.shadowCoord = ComputeScreenPos(TransformWorldToHClip(input.positionWS));
                #else
                    lighting.shadowCoord = TransformWorldToShadowCoord(input.positionWS);
                #endif
                lighting.fogCoord = InitializeInputDataFog(float4(input.positionWS, 1), input.fogAndVertexLight.x);
                lighting.vertexLighting = input.fogAndVertexLight.yzw;
                lighting.bakedGI = SAMPLE_GI(input.lightmapUV, input.vertexSH, normalWS);
                lighting.shadowMask = SAMPLE_SHADOWMASK(input.lightmapUV);
                lighting.normalizedScreenSpaceUV = GetNormalizedScreenSpaceUV(input.positionCS);
                half4 color = UniversalFragmentPBR(lighting, surface);
                color.rgb = MixFog(color.rgb, lighting.fogCoord);
                color.a = 1;
                return color;
            }
            ENDHLSL
        }

        Pass
        {
            Name "ShadowCaster"
            Tags { "LightMode"="ShadowCaster" }
            ZWrite On ZTest LEqual ColorMask 0
            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex IslandShadowVertex
            #pragma fragment IslandDepthFragment
            #pragma multi_compile_instancing
            #pragma multi_compile_vertex _ _CASTING_PUNCTUAL_LIGHT_SHADOW
            float3 _LightDirection;
            float3 _LightPosition;
            struct ShadowVaryings { float4 positionCS : SV_POSITION; };
            ShadowVaryings IslandShadowVertex(Attributes input)
            {
                UNITY_SETUP_INSTANCE_ID(input);
                float3 positionWS = TransformObjectToWorld(input.positionOS.xyz);
                float3 normalWS = TransformObjectToWorldNormal(input.normalOS);
                #if defined(_CASTING_PUNCTUAL_LIGHT_SHADOW)
                    float3 lightDirectionWS = normalize(_LightPosition - positionWS);
                #else
                    float3 lightDirectionWS = _LightDirection;
                #endif
                ShadowVaryings output;
                output.positionCS = TransformWorldToHClip(ApplyShadowBias(positionWS, normalWS, lightDirectionWS));
                // Inline directional near-plane clamping also supports early URP
                // 17.0.x packages which predate the ApplyShadowClamping helper.
                #if !defined(_CASTING_PUNCTUAL_LIGHT_SHADOW)
                    #if UNITY_REVERSED_Z
                        output.positionCS.z = min(output.positionCS.z, output.positionCS.w * UNITY_NEAR_CLIP_VALUE);
                    #else
                        output.positionCS.z = max(output.positionCS.z, output.positionCS.w * UNITY_NEAR_CLIP_VALUE);
                    #endif
                #endif
                return output;
            }
            half4 IslandDepthFragment(ShadowVaryings input) : SV_Target { return 0; }
            ENDHLSL
        }

        Pass
        {
            Name "DepthOnly"
            Tags { "LightMode"="DepthOnly" }
            ZWrite On ColorMask R
            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex IslandDepthVertex
            #pragma fragment IslandDepthFragment
            #pragma multi_compile_instancing
            struct DepthVaryings
            {
                float4 positionCS : SV_POSITION;
                UNITY_VERTEX_OUTPUT_STEREO
            };
            DepthVaryings IslandDepthVertex(Attributes input)
            {
                DepthVaryings output = (DepthVaryings)0;
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(output);
                output.positionCS = TransformObjectToHClip(input.positionOS.xyz);
                return output;
            }
            half IslandDepthFragment(DepthVaryings input) : SV_Target { return input.positionCS.z; }
            ENDHLSL
        }

        Pass
        {
            Name "DepthNormals"
            Tags { "LightMode"="DepthNormalsOnly" }
            ZWrite On
            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex IslandNormalVertex
            #pragma fragment IslandNormalFragment
            #pragma multi_compile_instancing
            #pragma multi_compile_fragment _ _GBUFFER_NORMALS_OCT
            struct NormalVaryings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                half3 normalWS : TEXCOORD1;
                UNITY_VERTEX_INPUT_INSTANCE_ID
                UNITY_VERTEX_OUTPUT_STEREO
            };
            NormalVaryings IslandNormalVertex(Attributes input)
            {
                NormalVaryings output = (NormalVaryings)0;
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_TRANSFER_INSTANCE_ID(input, output);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(output);
                VertexPositionInputs position = GetVertexPositionInputs(input.positionOS.xyz);
                output.positionCS = position.positionCS;
                output.positionWS = position.positionWS;
                output.normalWS = TransformObjectToWorldNormal(input.normalOS);
                return output;
            }
            half4 IslandNormalFragment(NormalVaryings input) : SV_Target
            {
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);
                half3 detailColor, normalWS;
                half3 groundAlbedo;
                half occlusion, smoothness, detailFade;
                SampleIslandDetail(input.positionWS, input.normalWS, detailColor, normalWS,
                    occlusion, smoothness, groundAlbedo, detailFade);
                #if defined(_GBUFFER_NORMALS_OCT)
                    float2 octNormal = PackNormalOctQuadEncode(normalWS);
                    half3 packedNormal = PackFloat2To888(saturate(octNormal * .5 + .5));
                    return half4(packedNormal, 0);
                #else
                    return half4(normalWS, 0);
                #endif
            }
            ENDHLSL
        }
    }
    FallBack "Hidden/Universal Render Pipeline/FallbackError"
}
