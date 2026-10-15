using System;

namespace Blackstone.Foundation
{
    // Planar response shared by the real controller and executable source tests.
    // Collision queries and slope ownership remain in PlayerMovement.
    public static class MovementResponseRules
    {
        public struct PlanarVelocity
        {
            public readonly float X, Z;
            public PlanarVelocity(float x,float z){X=x;Z=z;}
            public float Magnitude=>(float)Math.Sqrt(X*X+Z*Z);
        }
        static bool Finite(float value)=>!float.IsNaN(value)&&!float.IsInfinity(value);
        static PlanarVelocity Toward(PlanarVelocity current,PlanarVelocity target,float distance)
        {
            float x=target.X-current.X,z=target.Z-current.Z;
            float length=(float)Math.Sqrt(x*x+z*z);
            if(length<=distance||length<.000001f)return target;
            return new PlanarVelocity(current.X+x/length*distance,current.Z+z/length*distance);
        }
        public static PlanarVelocity Approach(float currentX,float currentZ,float targetX,float targetZ,
            float acceleration,float braking,float deltaTime)
        {
            if(!Finite(currentX)||!Finite(currentZ)||!Finite(targetX)||!Finite(targetZ)
                ||!Finite(acceleration)||!Finite(braking)||!Finite(deltaTime))return new PlanarVelocity(0,0);
            var current=new PlanarVelocity(currentX,currentZ);
            var target=new PlanarVelocity(targetX,targetZ);
            if(deltaTime<=0)return current;
            acceleration=Math.Max(0,acceleration);braking=Math.Max(0,braking);
            float currentSpeed=current.Magnitude,targetSpeed=target.Magnitude;
            if(currentX*targetX+currentZ*targetZ<-.000001f&&currentSpeed>.000001f)
            {
                // Stop old momentum before accelerating in the opposite direction.
                // Spend any time left after reaching zero on the new acceleration,
                // rather than adding a frame-rate-dependent pause at the pivot.
                if(braking<=0)return current;
                float stopTime=currentSpeed/braking;
                if(stopTime>=deltaTime)return Toward(current,new PlanarVelocity(0,0),braking*deltaTime);
                return Toward(new PlanarVelocity(0,0),target,acceleration*(deltaTime-stopTime));
            }
            float rate=targetSpeed<currentSpeed?braking:acceleration;
            return Toward(current,target,rate*deltaTime);
        }
        public static PlanarVelocity RejectIntoWall(float velocityX,float velocityZ,float normalX,float normalZ)
        {
            if(!Finite(velocityX)||!Finite(velocityZ)||!Finite(normalX)||!Finite(normalZ))return new PlanarVelocity(0,0);
            float square=normalX*normalX+normalZ*normalZ;
            if(square<.000001f)return new PlanarVelocity(velocityX,velocityZ);
            float inward=(velocityX*normalX+velocityZ*normalZ)/square;
            if(inward>=0)return new PlanarVelocity(velocityX,velocityZ);
            return new PlanarVelocity(velocityX-normalX*inward,velocityZ-normalZ*inward);
        }
    }
}
