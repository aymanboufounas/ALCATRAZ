Shader "Blackstone/Coastal Sky"
{
    Properties
    {
        _Zenith("Zenith",Color)=(.24,.43,.62,1)
        _Horizon("Horizon",Color)=(.77,.80,.78,1)
    }
    SubShader
    {
        Tags { "Queue"="Background" "RenderType"="Background" "PreviewType"="Skybox" "RenderPipeline"="UniversalPipeline" }
        Cull Off ZWrite Off
        Pass
        {
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            CBUFFER_START(UnityPerMaterial)
            half4 _Zenith;half4 _Horizon;
            CBUFFER_END
            struct Attributes {float4 positionOS:POSITION;};
            struct Varyings {float4 positionCS:SV_POSITION;float3 direction:TEXCOORD0;};
            float hash(float2 p){return frac(sin(dot(p,float2(127.1,311.7)))*43758.5453);}
            float noise(float2 p)
            {
                float2 i=floor(p),f=frac(p);f=f*f*(3-2*f);
                return lerp(lerp(hash(i),hash(i+float2(1,0)),f.x),lerp(hash(i+float2(0,1)),hash(i+1),f.x),f.y);
            }
            Varyings vert(Attributes input)
            {
                Varyings output;output.positionCS=TransformObjectToHClip(input.positionOS.xyz);output.direction=input.positionOS.xyz;return output;
            }
            half4 frag(Varyings input):SV_Target
            {
                float3 d=normalize(input.direction);float h=pow(saturate(d.y),.48);
                half3 color=lerp(_Horizon.rgb,_Zenith.rgb,h);
                float sun=pow(saturate(dot(d,normalize(float3(.53,.57,-.63)))),45);
                color+=half3(.24,.17,.075)*sun;
                float2 p=d.xz/max(.12,d.y)*2.1+float2(_Time.y*.0015,0);
                float cloud=noise(p)*.55+noise(p*2.1)*.27+noise(p*4.3)*.13+noise(p*8.7)*.05;
                cloud=smoothstep(.51,.72,cloud)*smoothstep(.07,.30,d.y)*.58;
                color=lerp(color,half3(.85,.83,.76),cloud);
                return half4(color,1);
            }
            ENDHLSL
        }
    }
}
