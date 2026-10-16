using System;
using Blackstone.Foundation;

public static class LocomotionAnimationTests
{
    static int checks;
    static void Check(bool ok,string label){checks++;if(!ok)throw new Exception(label);}
    static float Towards(float value,float target,float distance)
        =>value<target?Math.Min(target,value+distance):Math.Max(target,value-distance);

    static void WalkTrace(int fps,bool sprint)
    {
        var rules=new LocomotionAnimationRules();float speed=0,dt=1f/fps;
        int starts=0,stops=0;bool releasedWhileMoving=false;
        for(int frame=0;frame<fps*3;frame++)
        {
            float time=frame*dt;bool requested=time<1.1f;
            speed=Towards(speed,requested?sprint?5.5f:1.45f:0,(requested?8.5f:5)*dt);
            var signal=rules.Step(speed,0,dt,true,false,sprint,requested);
            if(signal==LocomotionSignal.Start||signal==LocomotionSignal.RunStart)
            {
                starts++;
                Check(signal==(sprint?LocomotionSignal.RunStart:LocomotionSignal.Start),"Correct start variant at "+fps+" Hz");
            }
            if(signal==LocomotionSignal.Stop||signal==LocomotionSignal.RunStop)
            {
                stops++;releasedWhileMoving=speed>.2f;
                Check(signal==(sprint?LocomotionSignal.RunStop:LocomotionSignal.Stop),"Correct stop variant at "+fps+" Hz");
            }
        }
        Check(starts==1&&stops==1,"Exactly one start and one stop at "+fps+" Hz");
        Check(releasedWhileMoving,"Stop begins during braking, before the controller stops, at "+fps+" Hz");
        Check(!rules.Moving,"Moving latch settles after deceleration at "+fps+" Hz");
    }

    static void RecentGaitTrace(int fps)
    {
        float dt=1f/fps;
        foreach(float settledSpeed in new[]{1.45f,2.15f})
        {
            var rules=new LocomotionAnimationRules();
            Check(rules.Step(5.5f,0,dt,true,false,true,true)==LocomotionSignal.RunStart,"Sprint starts the recent-gait trace");
            for(int frame=0;frame<fps*30;frame++)
                Check(rules.Step(settledSpeed,0,dt,true,false,false,true)==LocomotionSignal.None,
                    "Changing to a sustained lower gait does not emit a stop with movement still held");
            Check(rules.Step(settledSpeed,0,dt,true,false,false,false)==LocomotionSignal.Stop,
                "Sprint then 30 seconds of walking/jogging selects a normal stop at "+fps+" Hz");
            Check(rules.Step(0,0,dt,true,false,false,false)==LocomotionSignal.None,
                "A lower-gait braking stop is not repeated when speed reaches zero");
        }

        var immediate=new LocomotionAnimationRules();
        immediate.Step(5.5f,0,dt,true,false,true,true);
        Check(immediate.Step(5.5f-12*dt,0,dt,true,false,false,false)==LocomotionSignal.RunStop,
            "Immediate sprint release retains the run-stop clip during braking at "+fps+" Hz");
        for(int frame=0;frame<fps;frame++)
            Check(immediate.Step(Math.Max(0,5.5f-12*(frame+2)*dt),0,dt,true,false,false,false)==LocomotionSignal.None,
                "A run-stop event stays latched through all of its braking frames");

        var dipped=new LocomotionAnimationRules();
        dipped.Step(3,0,dt,true,false,true,true);
        for(int frame=0;frame<Math.Max(1,fps/10);frame++)
            Check(dipped.Step(2.7f,0,dt,true,false,true,true)==LocomotionSignal.None,
                "A brief threshold dip emits no extra start/stop event");
        Check(dipped.Step(2.6f,0,dt,true,false,false,false)==LocomotionSignal.RunStop,
            "A brief running-speed dip does not flicker to a walking stop at "+fps+" Hz");

        var noise=new LocomotionAnimationRules();
        noise.Step(3,0,dt,true,false,true,true);
        for(int frame=0;frame<fps;frame++)
            Check(noise.Step(frame%2==0?2.79f:2.81f,0,dt,true,false,true,true)==LocomotionSignal.None,
                "Running-threshold noise does not emit transitions");
        Check(noise.Step(2.7f,0,dt,true,false,false,false)==LocomotionSignal.RunStop,
            "Recent running samples survive ordinary threshold noise");
    }

    public static void Main()
    {
        foreach(int fps in new[]{24,30,50,60,72,90,100,120,144,240})
        {
            WalkTrace(fps,false);WalkTrace(fps,true);RecentGaitTrace(fps);
            foreach(int sign in new[]{-1,1})
            {
                var turn=new LocomotionAnimationRules();int turns=0;
                for(int frame=0;frame<fps;frame++)
                {
                    var signal=turn.Step(0,sign*90f/fps,1f/fps,true,false,false,false);
                    if(signal!=LocomotionSignal.None)
                    {turns++;Check(signal==(sign<0?LocomotionSignal.TurnLeft:LocomotionSignal.TurnRight),"Correct accumulated turn direction");}
                }
                Check(turns==1,"Slow per-frame rotation produces one turn with cooldown at "+fps+" Hz");
            }
        }

        var rules=new LocomotionAnimationRules();
        Check(rules.Step(.25f,0,.01f,true,false,false,true)==LocomotionSignal.Start,"Large speed crossing starts once");
        foreach(float speed in new[]{.19f,.09f,.13f,.18f,.081f})
            Check(rules.Step(speed,0,.01f,true,false,false,true)==LocomotionSignal.None&&rules.Moving,"Speed noise inside hysteresis does not retrigger");
        Check(rules.Step(.08f,0,.01f,true,false,false,true)==LocomotionSignal.None&&!rules.Moving,"A blocked held move settles without playing stopping steps");
        Check(rules.Step(.3f,0,.01f,true,false,false,true)==LocomotionSignal.Start,"Movement starts again when the obstruction clears");
        Check(rules.Step(.28f,0,.01f,true,false,false,false)==LocomotionSignal.Stop,"Intent release starts stopping above zero speed");
        Check(rules.Step(.26f,0,.01f,true,false,false,false)==LocomotionSignal.None,"Braking does not repeat the stop event");
        Check(rules.Step(.29f,0,.01f,true,false,false,true)==LocomotionSignal.Start,"Input restart interrupts braking before a full stop");
        Check(rules.Step(.2f,0,.01f,true,false,false,false)==LocomotionSignal.Stop,"A later release gets its own stop event");
        Check(rules.Step(0,0,.01f,true,false,false,false)==LocomotionSignal.None,"Reaching zero does not duplicate a braking stop");

        rules.Reset();
        Check(rules.Step(.5f,0,.02f,true,true,false,true)==LocomotionSignal.None&&rules.Moving,"Backward movement latches without a forward start gesture");
        Check(rules.Step(.4f,0,.02f,true,true,false,false)==LocomotionSignal.None,"Backward release does not use a forward stopping clip");
        Check(rules.Step(0,0,.02f,true,true,false,false)==LocomotionSignal.None,"Backward completion leaves no queued stop");
        rules.Step(4,0,.02f,true,false,true,true);
        Check(rules.Step(4,90,.02f,false,false,true,true)==LocomotionSignal.None&&!rules.Moving,"Activity ownership clears movement and yaw state");
        Check(rules.Step(0,0,.02f,true,false,false,false)==LocomotionSignal.None,"Activity return cannot leak a previous stop or turn");
        rules.Step(0,30,.02f,true,false,false,false);rules.Reset();
        Check(rules.Step(0,20,.02f,true,false,false,false)==LocomotionSignal.None,"Teleport reset clears accumulated yaw");
        Check(rules.Step(0,-20,.02f,true,false,false,false)==LocomotionSignal.None,"Opposing small turns cancel");

        foreach(float invalid in new[]{float.NaN,float.PositiveInfinity,float.NegativeInfinity})
        {
            Check(rules.Step(invalid,0,.02f,true,false,false,true)==LocomotionSignal.None,"Invalid speed is rejected");
            Check(rules.Step(1,invalid,.02f,true,false,false,true)==LocomotionSignal.None,"Invalid yaw is rejected");
            Check(rules.Step(1,0,invalid,true,false,false,true)==LocomotionSignal.None,"Invalid elapsed time is rejected");
            Check(LocomotionAnimationRules.AimYaw(invalid,1,1)==0,"Invalid aim input cannot turn the rig");
        }
        Check(rules.Step(1,0,0,true,false,false,true)==LocomotionSignal.None,"Paused time resets queued events");

        foreach(float lateral in new[]{-1f,0f,1f})foreach(float forward in new[]{-1f,0f,1f})
        {
            if(lateral==0&&forward==0)continue;
            float direction=LocomotionAnimationRules.PlaybackDirection(lateral,forward,1);
            float yaw=LocomotionAnimationRules.AimYaw(lateral,forward,direction)*(float)Math.PI/180;
            double magnitude=Math.Sqrt(lateral*lateral+forward*forward);
            double x=direction*Math.Sin(yaw),z=direction*Math.Cos(yaw);
            Check(x*lateral/magnitude+z*forward/magnitude>.99999,"Leg gait aligns with travel for every aiming cardinal/diagonal");
        }
        Check(LocomotionAnimationRules.AimYaw(1,-1,-1)<0,"Backward-right travel uses left-facing reversed gait");
        Check(LocomotionAnimationRules.AimYaw(-1,-1,-1)>0,"Backward-left travel uses right-facing reversed gait");
        Check(LocomotionAnimationRules.PlaybackDirection(1,-.01f,1)==1,"Near-sideways noise keeps forward playback");
        Check(LocomotionAnimationRules.PlaybackDirection(1,.01f,-1)==-1,"Near-sideways noise keeps backward playback");
        Check(LocomotionAnimationRules.AimYaw(0,0,-1)==0,"Stopped aim returns to a neutral leg orientation");
        Check(LocomotionAnimationRules.CycleOffset("WalkSlow")==.5f,"Opposite source slow-walk phase is corrected");
        foreach(string clip in new[]{"Idle","Walk","WalkFast","Run","RunFast"})
            Check(LocomotionAnimationRules.CycleOffset(clip)==0,"Already aligned source gait keeps its phase");
        foreach(var start in new[]{LocomotionSignal.Start,LocomotionSignal.RunStart})
        {
            Check(LocomotionAnimationRules.PendingSignal(start,.4f,true,false,true)==start,"A useful queued start survives a transient state");
            Check(LocomotionAnimationRules.PendingSignal(start,0,true,false,true)==LocomotionSignal.None,"Wall contact invalidates queued starts even with held input");
            Check(LocomotionAnimationRules.PendingSignal(start,.4f,false,false,true)==LocomotionSignal.None,"Intent release invalidates queued starts before the controller stops");
            Check(LocomotionAnimationRules.PendingSignal(start,.4f,true,true,true)==LocomotionSignal.None,"Reversed gait invalidates a queued forward start");
        }
        foreach(var stop in new[]{LocomotionSignal.Stop,LocomotionSignal.RunStop})
        {
            Check(LocomotionAnimationRules.PendingSignal(stop,.4f,false,false,true)==stop,"A useful queued stop survives ongoing braking");
            Check(LocomotionAnimationRules.PendingSignal(stop,.4f,true,false,true)==LocomotionSignal.None,"Restarted input invalidates a queued stop");
            Check(LocomotionAnimationRules.PendingSignal(stop,.4f,false,true,true)==LocomotionSignal.None,"Reversed gait invalidates a queued forward stop without needing a new event");
        }
        foreach(var turn in new[]{LocomotionSignal.TurnLeft,LocomotionSignal.TurnRight})
        {
            Check(LocomotionAnimationRules.PendingSignal(turn,0,false,false,true)==turn,"A stationary queued turn remains usable");
            Check(LocomotionAnimationRules.PendingSignal(turn,0,true,false,true)==LocomotionSignal.None,"Fresh movement intent clears a turn before acceleration starts");
            Check(LocomotionAnimationRules.PendingSignal(turn,.3f,false,false,true)==LocomotionSignal.None,"Residual travel clears a queued stationary turn");
        }
        foreach(LocomotionSignal signal in Enum.GetValues(typeof(LocomotionSignal)))
        {
            Check(LocomotionAnimationRules.PendingSignal(signal,1,true,false,false)==LocomotionSignal.None,"Activity ownership invalidates every pending signal");
            Check(LocomotionAnimationRules.PendingSignal(signal,float.NaN,true,false,true)==LocomotionSignal.None,"Invalid speed cannot preserve a pending signal");
        }
        Console.WriteLine("PASS: "+checks+" locomotion animation assertions");
    }
}
