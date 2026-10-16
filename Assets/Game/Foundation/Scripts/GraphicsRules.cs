using System;

namespace Blackstone.Foundation
{
    public struct GraphicsProfile
    {
        public readonly int Index,MipmapLimit,Cascades,ShadowMap,AdditionalLights,StreamingBudget;
        public readonly float RenderScale,ShadowDistance,LodBias;
        public readonly bool Smaa,ForceAnisotropy;
        public GraphicsProfile(int index,int mipmapLimit,float renderScale,float shadowDistance,int cascades,
            int shadowMap,int additionalLights,float lodBias,int streamingBudget,bool smaa,bool forceAnisotropy)
        {
            Index=index;MipmapLimit=mipmapLimit;RenderScale=renderScale;ShadowDistance=shadowDistance;
            Cascades=cascades;ShadowMap=shadowMap;AdditionalLights=additionalLights;LodBias=lodBias;
            StreamingBudget=streamingBudget;Smaa=smaa;ForceAnisotropy=forceAnisotropy;
        }
    }
    // Source settings only. A preset is not a measured frame-rate guarantee.
    public static class GraphicsRules
    {
        public const int DefaultPreset=3;
        static readonly string[] names={"LOW","MEDIUM","HIGH","ULTRA"};
        static readonly int[] widths={1280,1920,2560,3840},heights={720,1080,1440,2160};
        static readonly string[] resolutions={"1280 × 720","1920 × 1080","2560 × 1440","3840 × 2160"};
        public static string[] Names=>(string[])names.Clone();
        public static int[] Widths=>(int[])widths.Clone();
        public static int[] Heights=>(int[])heights.Clone();
        public static string[] ResolutionNames=>(string[])resolutions.Clone();
        public static int ClampPreset(int index)=>Math.Max(0,Math.Min(3,index));
        public static GraphicsProfile Get(int index)
        {
            switch(ClampPreset(index))
            {
                case 0:return new GraphicsProfile(0,2,.8f,30,1,1024,2,.75f,512,false,false);
                case 1:return new GraphicsProfile(1,1,1,60,2,2048,4,1,1024,true,false);
                case 2:return new GraphicsProfile(2,0,1,120,4,4096,8,1.6f,2048,true,false);
                default:return new GraphicsProfile(3,0,1,180,4,4096,8,2,4096,true,true);
            }
        }
        public static int ResolutionIndex(int width,int height)
        {
            if(width<=0||height<=0)return 2;
            int selected=0;long closest=long.MaxValue;
            for(int i=0;i<widths.Length;i++)
            {
                // Prefer the current vertical detail on ultrawide/custom windows.
                // Selecting a label never calls Screen.SetResolution.
                long distance=Math.Abs((long)heights[i]-height)*4+Math.Abs((long)widths[i]-width);
                if(distance<closest){closest=distance;selected=i;}
            }
            return selected;
        }
    }
}
