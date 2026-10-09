Shader "Alcatraz/Marine Sky"
{
    Properties { _BaseColor("Horizon", Color) = (.68,.79,.86,1) }
    SubShader
    {
        Tags { "RenderPipeline"="UniversalPipeline" "Queue"="Background" "RenderType"="Background" "PreviewType"="Skybox" }
        Cull Off ZWrite Off
        Pass
        {
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            CBUFFER_START(UnityPerMaterial)
            half4 _BaseColor;
            CBUFFER_END
            struct Attributes { float4 positionOS : POSITION; };
            struct Varyings { float4 positionCS : SV_POSITION; float3 direction : TEXCOORD0; };
            Varyings vert(Attributes input)
            {
                Varyings output;
                output.positionCS = TransformObjectToHClip(input.positionOS.xyz);
                output.direction = TransformObjectToWorldDir(input.positionOS.xyz);
                return output;
            }
            half4 frag(Varyings input) : SV_Target
            {
                float3 direction = normalize(input.direction);
                half horizon = pow(saturate(1 - abs(direction.y)), 5);
                half3 color = lerp(half3(.28,.51,.70), _BaseColor.rgb, horizon);
                float wisps = sin(direction.x * 17 + direction.z * 23)
                            * sin(direction.x * 7 - direction.z * 13 + direction.y * 26);
                half cloud = smoothstep(.12,.48,wisps) * smoothstep(.01,.22,direction.y)
                           * (1 - smoothstep(.38,.75,direction.y));
                color = lerp(color, half3(.83,.87,.88), cloud * .45);
                return half4(color, 1);
            }
            ENDHLSL
        }
    }
    Fallback Off
}
