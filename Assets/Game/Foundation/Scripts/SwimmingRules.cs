using System;

namespace Blackstone.Foundation
{
    // World-independent thresholds shared by entry detection, the HUD and tests.
    public static class SwimmingRules
    {
        public const float SurfaceBodyDepth=1.2f;
        public const float WarningDistance=24;
        public const float RestrictedDistance=40;
        public const float ClamberReach=1.1f;
        public const float ClamberHeight=.6f;
        public static bool ShouldSwim(bool available,bool externalControl,bool swimming,
            float feet,float surface,bool hasFloor,float floor)
        {
            if(!available||externalControl||!Finite(feet)||!Finite(surface)||hasFloor&&!Finite(floor))return false;
            // Hysteresis prevents the shore transition toggling every wave/frame.
            float shallowLimit=surface-(swimming?.75f:.9f);
            if(hasFloor&&floor>=shallowLimit)return false;
            return feet<surface+(swimming?.2f:-.65f);
        }
        public static bool Warn(float shoreDistance)=>!float.IsNaN(shoreDistance)&&shoreDistance>WarningDistance;
        public static bool Restricted(float shoreDistance)=>!float.IsNaN(shoreDistance)&&shoreDistance>RestrictedDistance;
        public static bool CanClamberSurface(float height,float surface,float normalY,float reach)
        {
            return Finite(height)&&Finite(surface)&&Finite(normalY)&&Finite(reach)&&reach>0&&reach<=ClamberReach
                &&height>=surface+.05f&&height<=surface+ClamberHeight&&normalY>=.65f;
        }
        public static float BuoyancyVelocity(float velocity,float feet,float surface,float deltaTime)
        {
            if(!Finite(velocity)||!Finite(feet)||!Finite(surface)||!Finite(deltaTime)||deltaTime<=0)return 0;
            // Bounded substeps remain stable after a slow frame.
            float remaining=Math.Min(deltaTime,.2f);
            while(remaining>0)
            {
                float step=Math.Min(remaining,.02f);
                velocity=Math.Max(-3,Math.Min(3,velocity+((surface-SurfaceBodyDepth-feet)*12-velocity*5)*step));
                remaining-=step;
            }
            return velocity;
        }
        static bool Finite(float value)=>!float.IsNaN(value)&&!float.IsInfinity(value);
    }
}
