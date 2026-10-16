using System;
using Blackstone.Foundation;

public static class GraphicsSettingsTests
{
    static int checks;
    static void Check(bool condition,string message){checks++;if(!condition)throw new Exception(message);}
    public static void Main()
    {
        Check(GraphicsRules.DefaultPreset==3,"The requested high-end default is Ultra.");
        Check(GraphicsRules.Names.Length==4,"Story and exploration have four shared profiles.");
        Check(GraphicsRules.Get(int.MinValue).Index==0&&GraphicsRules.Get(int.MaxValue).Index==3,"Invalid saved preset indices are bounded.");
        for(int level=0;level<4;level++)
        {
            var p=GraphicsRules.Get(level);
            Check(p.Index==level&&p.RenderScale>0&&p.RenderScale<=1,"Profiles cannot silently supersample a 4K output.");
            Check(p.Cascades==1||p.Cascades==2||p.Cascades==4,"Shadow cascades are supported by URP.");
            Check(p.AdditionalLights>=0&&p.AdditionalLights<=8,"Forward lighting stays within the per-object limit.");
            Check(p.MipmapLimit>=0&&p.MipmapLimit<=2&&p.LodBias>0&&p.StreamingBudget>0,"Texture and geometry settings are usable.");
            if(level>0)
            {
                var before=GraphicsRules.Get(level-1);
                Check(p.ShadowDistance>=before.ShadowDistance&&p.ShadowMap>=before.ShadowMap,"Higher profiles do not reduce shadow detail.");
                Check(p.MipmapLimit<=before.MipmapLimit&&p.LodBias>=before.LodBias,"Higher profiles preserve at least the previous source detail.");
            }
        }
        foreach(int level in new[]{2,3})
        {
            var p=GraphicsRules.Get(level);
            Check(p.MipmapLimit==0&&p.RenderScale==1,"High and Ultra retain original textures and native resolution.");
            Check(p.Smaa&&p.ShadowMap==4096&&p.Cascades==4,"High-end profiles use SMAA and detailed cascaded shadows.");
        }
        Check(GraphicsRules.Get(3).ForceAnisotropy,"Ultra forces anisotropic texture sampling.");
        var widths=GraphicsRules.Widths;var heights=GraphicsRules.Heights;
        Check(widths.Length==4&&heights.Length==4&&GraphicsRules.ResolutionNames.Length==4,"All display controls share four output sizes.");
        for(int i=0;i<widths.Length;i++)Check(GraphicsRules.ResolutionIndex(widths[i],heights[i])==i,"Exact supported display size is preserved.");
        Check(widths[3]==3840&&heights[3]==2160,"Native 4K is available.");
        Check(GraphicsRules.ResolutionIndex(3440,1440)==2,"Ultrawide windows prefer their current vertical detail.");
        Check(GraphicsRules.ResolutionIndex(1024,768)==0,"Small custom windows choose a valid nearby display option.");
        foreach(int value in new[]{int.MinValue,-1,0,1,int.MaxValue})
        {
            int index=GraphicsRules.ResolutionIndex(value,value);
            Check(index>=0&&index<4,"Malformed and extreme display dimensions cannot index outside the options.");
        }
        widths[3]=1;heights[3]=1;var names=GraphicsRules.Names;names[3]="changed";
        Check(GraphicsRules.Widths[3]==3840&&GraphicsRules.Heights[3]==2160&&GraphicsRules.Names[3]=="ULTRA","UI callers cannot corrupt shared preset/display definitions.");
        Console.WriteLine("PASS: "+checks+" shared graphics and resolution assertions");
    }
}
