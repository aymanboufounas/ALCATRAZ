Shader "Alcatraz/Marine Sky"
{
    Properties
    {
        _BaseColor("Horizon", Color) = (.76,.79,.77,1)
        _ZenithColor("Zenith", Color) = (.28,.48,.67,1)
        _CloudColor("Cloud highlights", Color) = (.96,.93,.84,1)
        _CloudShadowColor("Cloud shade", Color) = (.50,.58,.65,1)
        _SunColor("Sunlight", Color) = (1,.86,.65,1)
        _SunDirection("Direction to sun", Vector) = (.398,.530,-.748,0)
        _CloudCoverage("Cloud coverage", Range(0,1)) = .52
    }
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
            half4 _BaseColor, _ZenithColor, _CloudColor, _CloudShadowColor, _SunColor;
            float4 _SunDirection;
            half _CloudCoverage;
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
            // Arithmetic value noise avoids a texture download and the old,
            // visibly repeating sine bands. Four octaves are fixed-cost: this
            // is an analytic sky layer, not a volumetric ray march.
            float SkyHash(float2 point)
            {
                float3 p = frac(float3(point.x, point.y, point.x) * .1031);
                p += dot(p, p.yzx + 33.33);
                return frac((p.x + p.y) * p.z);
            }
            float SkyNoise(float2 point)
            {
                float2 cell = floor(point);
                float2 weight = frac(point);
                weight = weight * weight * (3 - 2 * weight);
                return lerp(lerp(SkyHash(cell), SkyHash(cell + float2(1, 0)), weight.x),
                            lerp(SkyHash(cell + float2(0, 1)), SkyHash(cell + 1), weight.x), weight.y);
            }
            float CloudField(float2 point)
            {
                float value = SkyNoise(point) * .54;
                point = mul(float2x2(.80, -.60, .60, .80), point) * 2.03 + 17.1;
                value += SkyNoise(point) * .27;
                point = mul(float2x2(.80, -.60, .60, .80), point) * 2.01 + 9.2;
                value += SkyNoise(point) * .13;
                value += SkyNoise(point * 2.04 + 4.6) * .06;
                return value;
            }
            half4 frag(Varyings input) : SV_Target
            {
                float3 direction = normalize(input.direction);
                float3 sunDirection = normalize(_SunDirection.xyz);
                half skyHeight = pow(saturate(direction.y), .48);
                half3 color = lerp(_BaseColor.rgb, _ZenithColor.rgb, skyHeight);
                float sunAlignment = saturate(dot(direction, sunDirection));
                // A broad warm aureole and compact HDR disk share the real
                // directional light vector, including in the water reflection.
                half aureole = pow(sunAlignment, 24) * .18;
                half disk = smoothstep(.99994, .99998, sunAlignment);
                color += _SunColor.rgb * (aureole + disk * 2.5);

                float2 cloudPoint = direction.xz / max(.12, direction.y + .08) * 1.6;
                float field = CloudField(cloudPoint);
                float threshold = lerp(.78, .35, _CloudCoverage);
                half density = smoothstep(threshold - .07, threshold + .18, field);
                half horizonFade = smoothstep(.025, .16, direction.y);
                // Dense undersides stay cool, while thinner sun-facing edges
                // take the warm key. Static clouds keep the one-shot reflection
                // capture coherent without per-frame environment updates.
                half sunFacing = saturate(.5 + dot(normalize(float3(direction.x, .35, direction.z)), sunDirection) * .5);
                half cloudLight = saturate(.62 - density * .35 + sunFacing * .35);
                half3 cloudColor = lerp(_CloudShadowColor.rgb, _CloudColor.rgb, cloudLight);
                color = lerp(color, cloudColor, density * horizonFade * .90);
                return half4(color, 1);
            }
            ENDHLSL
        }
    }
    Fallback Off
}
