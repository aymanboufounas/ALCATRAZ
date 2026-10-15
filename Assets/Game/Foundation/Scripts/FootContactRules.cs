using System;

namespace Blackstone.Foundation
{
    // Audio follows measured foot contacts, not a second locomotion clock.
    public sealed class FootContactRules
    {
        readonly bool[] sampled=new bool[2], touching=new bool[2];
        readonly float[] previousHeight=new float[2];
        float nextStep=float.NegativeInfinity;
        int lastLandingFrame=int.MinValue;
        public void Reset()
        {
            for(int foot=0;foot<2;foot++)ResetFoot(foot);
            nextStep=float.NegativeInfinity;
        }
        void ResetFoot(int foot)
        {sampled[foot]=touching[foot]=false;previousHeight[foot]=0;}
        static bool Finite(float value)=>!float.IsNaN(value)&&!float.IsInfinity(value);
        static float Clamp01(float value)=>Math.Max(0,Math.Min(1,value));
        public bool Step(int foot,float ankleHeight,float clearance,bool supported,float time)
        {
            if(foot<0||foot>1)throw new ArgumentOutOfRangeException(nameof(foot));
            if(!supported||!Finite(ankleHeight)||!Finite(clearance)||!Finite(time)
                ||clearance<0||clearance>.5f||ankleHeight<-.2f)
            {ResetFoot(foot);return false;}
            float low=clearance+.045f, raised=clearance+.09f;
            if(!sampled[foot])
            {
                // A resumed or teleported planted foot is already in contact.
                // It must visibly lift before it can create a new footfall.
                sampled[foot]=true;touching[foot]=ankleHeight<raised;
                previousHeight[foot]=ankleHeight;return false;
            }
            if(ankleHeight>=raised)touching[foot]=false;
            bool plant=ankleHeight<=low&&!touching[foot]&&ankleHeight<=previousHeight[foot]+.003f;
            previousHeight[foot]=ankleHeight;
            if(!plant)return false;
            touching[foot]=true;
            if(time<nextStep)return false;
            nextStep=time+.22f;return true;
        }
        public float Land(int frame,float impactSpeed,float time)
        {
            float volume=LandingVolume(impactSpeed);
            if(frame==lastLandingFrame||!Finite(time)||volume<=0)return 0;
            lastLandingFrame=frame;Reset();nextStep=time+.22f;
            return volume;
        }
        public static float StepVolume(float speed,bool player,bool crouching)
        {
            if(!Finite(speed)||speed<.15f)return 0;
            float gait=Clamp01((speed-.5f)/5);
            float volume=player?.38f+.2f*gait:.19f+.07f*gait;
            return crouching?volume*.42f:volume;
        }
        public static float LandingVolume(float impactSpeed)
        {
            if(!Finite(impactSpeed)||impactSpeed<=2.5f)return 0;
            return .28f+.42f*Clamp01((impactSpeed-2.5f)/8);
        }
    }
}
