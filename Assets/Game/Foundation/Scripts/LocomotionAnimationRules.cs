using System;

namespace Blackstone.Foundation
{
    public enum LocomotionSignal { None, Start, Stop, RunStart, RunStop, TurnLeft, TurnRight }

    // Animation events use state and elapsed time, never a single-frame speed
    // crossing. The same acceleration trace must behave at 30 or 240 Hz.
    public sealed class LocomotionAnimationRules
    {
        public const float MovingThreshold=.2f;
        public const float StoppedThreshold=.08f;
        public const float RunningThreshold=2.8f;
        public const float RunningHistorySeconds=.35f;
        public const float TurnThreshold=40;
        public const float TurnCooldown=.65f;
        public bool Moving { get; private set; }
        float accumulatedYaw,turnWait,recentRun;
        bool stopping;

        public void Reset()
        {Moving=stopping=false;accumulatedYaw=turnWait=recentRun=0;}

        public LocomotionSignal Step(float sourceSpeed,float deltaYaw,float deltaTime,bool active,bool reverse,bool wantsSprint,bool moveRequested)
        {
            if(!active||!Finite(sourceSpeed)||!Finite(deltaYaw)||!Finite(deltaTime)||deltaTime<=0)
            {Reset();return LocomotionSignal.None;}
            sourceSpeed=Math.Max(0,sourceSpeed);
            turnWait=Math.Max(0,turnWait-deltaTime);
            bool wasMoving=Moving;
            if(!Moving&&sourceSpeed>=MovingThreshold)Moving=true;
            else if(Moving&&sourceSpeed<=StoppedThreshold)Moving=false;
            if(Moving)
            {
                // Remember a brief speed dip, but not a sprint from minutes ago.
                // Freeze this choice once braking begins so the selected stop
                // variant cannot change while the controller slows to zero.
                if(sourceSpeed>=RunningThreshold)recentRun=RunningHistorySeconds;
                else if(moveRequested)recentRun=Math.Max(0,recentRun-deltaTime);
                accumulatedYaw=0;
                if(moveRequested&&(!wasMoving||stopping))
                {
                    if(stopping)recentRun=sourceSpeed>=RunningThreshold?RunningHistorySeconds:0;
                    stopping=false;
                    if(!reverse)return wantsSprint?LocomotionSignal.RunStart:LocomotionSignal.Start;
                }
                if(!moveRequested&&!stopping)
                {
                    stopping=true;
                    return reverse?LocomotionSignal.None:recentRun>0?LocomotionSignal.RunStop:LocomotionSignal.Stop;
                }
                return LocomotionSignal.None;
            }
            if(wasMoving)
            {
                bool running=recentRun>0;recentRun=0;accumulatedYaw=0;
                bool alreadyStopping=stopping;stopping=false;
                return moveRequested||alreadyStopping||reverse?LocomotionSignal.None:running?LocomotionSignal.RunStop:LocomotionSignal.Stop;
            }
            stopping=false;
            // Ignore tiny movement inside the stop/start dead band. Deliberate
            // stationary turns accumulate even when each frame turns <1 degree.
            if(sourceSpeed>StoppedThreshold||turnWait>0){accumulatedYaw=0;return LocomotionSignal.None;}
            accumulatedYaw=Math.Max(-180,Math.Min(180,accumulatedYaw+deltaYaw));
            if(Math.Abs(accumulatedYaw)<TurnThreshold)return LocomotionSignal.None;
            var signal=accumulatedYaw<0?LocomotionSignal.TurnLeft:LocomotionSignal.TurnRight;
            accumulatedYaw=0;turnWait=TurnCooldown;return signal;
        }

        public static float PlaybackDirection(float lateral,float forward,float previous)
        {
            if(!Finite(lateral)||!Finite(forward))return 1;
            float magnitude=(float)Math.Sqrt(lateral*lateral+forward*forward);
            if(magnitude<.12f)return previous<0?-1:1;
            // Hysteresis prevents noisy near-sideways input from reversing the
            // gait on every frame. No dedicated strafe clips are shipped.
            float direction=forward/magnitude;
            return direction<-.18f?-1:direction>.18f?1:previous<0?-1:1;
        }
        public static float AimYaw(float lateral,float forward,float playbackDirection)
        {
            if(!Finite(lateral)||!Finite(forward)||lateral*lateral+forward*forward<.0144f)return 0;
            float direction=playbackDirection<0?-1:1;
            float yaw=(float)(Math.Atan2(lateral*direction,forward*direction)*180/Math.PI);
            return Math.Max(-90,Math.Min(90,yaw));
        }
        public static bool AllowsPending(LocomotionSignal signal,float sourceSpeed,bool moveRequested,bool reverse,bool active)
        {
            if(!active||!Finite(sourceSpeed)||sourceSpeed<0)return false;
            switch(signal)
            {
                case LocomotionSignal.Start:
                case LocomotionSignal.RunStart:
                    return moveRequested&&!reverse&&sourceSpeed>StoppedThreshold;
                case LocomotionSignal.Stop:
                case LocomotionSignal.RunStop:
                    return !moveRequested&&!reverse;
                case LocomotionSignal.TurnLeft:
                case LocomotionSignal.TurnRight:
                    return !moveRequested&&sourceSpeed<=StoppedThreshold;
                default:return false;
            }
        }
        public static LocomotionSignal PendingSignal(LocomotionSignal signal,float sourceSpeed,bool moveRequested,bool reverse,bool active)
            =>AllowsPending(signal,sourceSpeed,moveRequested,reverse,active)?signal:LocomotionSignal.None;
        // Source foot lift measurements put WalkSlow half a cycle away from
        // Walk/WalkFast/Run. Align the feet before blending their poses.
        public static float CycleOffset(string clip)=>clip=="WalkSlow"?.5f:0;
        static bool Finite(float value)=>!float.IsNaN(value)&&!float.IsInfinity(value);
    }
}
