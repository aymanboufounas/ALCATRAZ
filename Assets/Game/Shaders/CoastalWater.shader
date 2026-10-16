Shader "Blackstone/Coastal Water"
{
    Properties { _BaseColor("Deep water", Color) = (0.06,0.18,0.20,1) }
    SubShader
    {
        Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Transparent" "Queue"="Transparent-20" }
        Pass
        {
            Name "Coastal Water"
            Tags { "LightMode"="UniversalForward" }
            Cull Back ZWrite Off
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE
            #pragma multi_compile_fragment _ _SHADOWS_SOFT
            #pragma multi_compile_fragment _ _REFLECTION_PROBE_BLENDING
            #pragma multi_compile_fragment _ _REFLECTION_PROBE_BOX_PROJECTION
            #pragma multi_compile_fog
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareDepthTexture.hlsl"
            CBUFFER_START(UnityPerMaterial)
            half4 _BaseColor;
            CBUFFER_END
            struct Attributes { float4 positionOS : POSITION; };
            struct Varyings { float4 positionCS : SV_POSITION; float3 positionWS : TEXCOORD0; half fog : TEXCOORD1; };
            Varyings vert(Attributes input)
            {
                Varyings output;
                VertexPositionInputs position=GetVertexPositionInputs(input.positionOS.xyz);
                output.positionCS=position.positionCS; output.positionWS=position.positionWS;
                output.fog=ComputeFogFactor(position.positionCS.z);
                return output;
            }
            half4 frag(Varyings input) : SV_Target
            {
                float2 p=input.positionWS.xz;
                float time=_Time.y;
                float2 wave=float2(cos(p.x*.23+p.y*.11+time*.58)*.085+cos(p.y*1.3-time*1.1)*.035,
                                   sin(p.y*.26-p.x*.08-time*.43)*.090+sin(p.x*1.7+time*.8)*.025);
                half3 normal=normalize(float3(-wave.x,1,-wave.y));
                half3 view=GetWorldSpaceNormalizeViewDir(input.positionWS);
                Light sun=GetMainLight(TransformWorldToShadowCoord(input.positionWS));
                half fresnel=pow(1-saturate(dot(normal,view)),5);
                half3 reflectedDirection=reflect(-view,normal);
                float2 screenUV=GetNormalizedScreenSpaceUV(input.positionCS);
                // Use the active sky/reflection probes, including their HDR
                // decoding and roughness mip selection, rather than a fixed tint.
                half3 reflection=GlossyEnvironmentReflection(reflectedDirection,input.positionWS,.16h,1.0h,screenUV);
                half specular=pow(saturate(dot(normal,normalize(view+sun.direction))),
                                  130)*sun.shadowAttenuation;
                float rawDepth=SampleSceneDepth(screenUV);
                float sceneEye=LinearEyeDepth(rawDepth,_ZBufferParams);
                float waterEye=-TransformWorldToView(input.positionWS).z;
                float waterDepth=max(0,sceneEye-waterEye);
                half shallow=exp(-waterDepth*.13);
                half foam=saturate(1-waterDepth*.55)
                    *smoothstep(.15,.8,sin(p.x*1.9+p.y*1.4-time*1.1)*.5+.5);
                half3 color=lerp(_BaseColor.rgb,half3(.10,.24,.22),shallow*.45);
                color=lerp(color,reflection,fresnel*.82);
                color+=sun.color*specular*.62+half3(.63,.73,.70)*foam*.38;
                return half4(MixFog(color,input.fog),1);
            }
            ENDHLSL
        }
    }
}
