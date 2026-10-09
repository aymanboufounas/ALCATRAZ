Shader "DesertShift/DesertSky"
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
