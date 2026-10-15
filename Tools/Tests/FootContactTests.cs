using System;
using System.Collections.Generic;
using Blackstone.Foundation;

public static class FootContactTests
{
    static int checks;
    static void Check(bool condition,string label)
    {checks++;if(!condition)throw new Exception(label);}
    static void Cadence(float duration,float clearance,float swing,int fps)
    {
        var rules=new FootContactRules();var times=new List<float>();
        int frames=(int)Math.Round(duration*8*fps);
        for(int frame=0;frame<frames;frame++)
        {
            float time=(float)frame/fps;
            for(int foot=0;foot<2;foot++)
            {
                double phase=time/duration+foot*.5;
                float height=clearance+swing*(float)(.5-.5*Math.Cos(phase*Math.PI*2));
                if(rules.Step(foot,height,clearance,true,time))times.Add(time);
            }
        }
        Check(times.Count==16,"Both feet retain eight walk/run cycles at "+fps+" FPS");
        for(int i=1;i<times.Count;i++)
            Check(Math.Abs(times[i]-times[i-1]-duration*.5f)<=2f/fps+.0001f,
                "Contact cadence follows the sampled feet, independent of frame rate");
    }
    public static void Main()
    {
        var rules=new FootContactRules();
        Check(!rules.Step(0,.105f,.105f,true,0),"Startup planted foot is primed silently");
        Check(!rules.Step(0,.105f,.105f,true,.5f),"Stationary foot cannot emit repeated steps");
        Check(!rules.Step(0,.3f,.105f,true,.6f),"Rising foot rearms without a sound");
        Check(rules.Step(0,.105f,.105f,true,.9f),"Descending foot produces one ground contact");
        Check(!rules.Step(0,.11f,.105f,true,1.3f),"Planted jitter cannot retrigger a contact");
        foreach(string transition in new[]{"idle","sit","swim","air","external control","ragdoll","teleport"})
        {
            rules.Reset();
            Check(!rules.Step(0,.105f,.105f,true,2),transition+" resets stale contact history");
            Check(!rules.Step(0,.12f,.105f,true,2.1f),transition+" cannot invent a landing on resume");
            Check(!rules.Step(0,.3f,.105f,true,2.2f),transition+" resumes with a genuine swing");
            Check(rules.Step(0,.105f,.105f,true,2.5f),transition+" allows the next genuine footfall");
        }
        rules.Reset();
        Check(!rules.Step(0,.32f,.1f,false,3),"Unsupported foot cannot arm a contact");
        Check(!rules.Step(0,.1f,.1f,true,3.1f),"Regaining support primes the foot silently");
        foreach(float invalid in new[]{float.NaN,float.PositiveInfinity,float.NegativeInfinity})
        {
            Check(!rules.Step(0,invalid,.1f,true,4),"Nonfinite ankle data cannot create audio");
            Check(!rules.Step(0,.1f,invalid,true,4),"Nonfinite clearance cannot create audio");
            Check(!rules.Step(0,.1f,.1f,true,invalid),"Nonfinite time cannot create audio");
            Check(FootContactRules.StepVolume(invalid,true,false)==0,"Invalid motion has no step volume");
            Check(FootContactRules.LandingVolume(invalid)==0,"Invalid landing has no impact volume");
        }
        Check(!rules.Step(0,-1,.1f,true,4),"Buried ankle cannot emit a floor contact");
        foreach(int fps in new[]{30,60,120})
        {
            Cadence(1.2f,.105f,.17f,fps);
            Cadence(.6f,.105f,.36f,fps);
            Cadence(1.2f,.06f,.17f,fps);
            Cadence(.6f,.18f,.36f,fps);
        }
        rules.Reset();
        rules.Step(0,.1f,.1f,true,5);rules.Step(1,.1f,.1f,true,5);
        rules.Step(0,.3f,.1f,true,5.1f);rules.Step(1,.3f,.1f,true,5.1f);
        Check(rules.Step(0,.1f,.1f,true,5.3f),"First simultaneous contact plays");
        Check(!rules.Step(1,.1f,.1f,true,5.3f),"Near-simultaneous feet do not double the sound");
        Check(!rules.Step(1,.1f,.1f,true,5.7f),"Suppressed planted contact cannot play late");
        float impact=rules.Land(100,7,6);
        Check(impact>0,"An actual landing has impact volume");
        Check(rules.Land(100,7,6)==0,"A landing is accepted once per frame");
        rules.Reset();
        Check(rules.Land(100,7,6)==0,"History reset cannot duplicate the same landing frame");
        Check(!rules.Step(0,.1f,.1f,true,6),"Landing foot is primed without an extra step");
        Check(rules.Land(101,9,6.5f)>impact,"Harder new landing is louder");
        Check(FootContactRules.LandingVolume(2)==0,"Tiny support corrections have no landing impact");
        Check(FootContactRules.LandingVolume(100)<=.7f,"Landing gain has an upper bound");
        float walk=FootContactRules.StepVolume(1.45f,true,false),run=FootContactRules.StepVolume(5.5f,true,false);
        Check(run>walk&&run<=.58f,"Sprint has a modest bounded increase in step gain");
        Check(FootContactRules.StepVolume(1.45f,false,false)<walk,"NPC footsteps remain quieter than player steps");
        Check(Math.Abs(FootContactRules.StepVolume(1.45f,true,true)-walk*.42f)<.0001f,"Crouch preserves its quiet gain");
        Check(FootContactRules.StepVolume(0,true,false)==0,"Idle has no step volume");
        Console.WriteLine("PASS: "+checks+" foot-contact, cadence and landing assertions");
    }
}
