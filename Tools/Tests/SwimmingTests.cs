using System;
using Blackstone.Foundation;

public static class SwimmingTests
{
    static int checks;
    static void Check(bool value,string label){checks++;if(!value)throw new Exception(label);}
    public static void Main()
    {
        Check(!SwimmingRules.ShouldSwim(true,false,false,1,0,false,0),"Dry player never swims");
        Check(SwimmingRules.ShouldSwim(true,false,false,-1,0,false,0),"Open sea starts swimming");
        Check(!SwimmingRules.ShouldSwim(true,true,false,-1,0,false,0),"Vehicle or ragdoll retains external control");
        Check(!SwimmingRules.ShouldSwim(false,false,false,-1,0,false,0),"Interior and unrelated scene cannot swim");
        Check(!SwimmingRules.ShouldSwim(true,false,false,-1,0,true,-.5f),"Shallow bank uses walking");
        Check(SwimmingRules.ShouldSwim(true,false,true,-.5f,0,false,0),"Swimming persists through a surface stroke");
        Check(!SwimmingRules.ShouldSwim(true,false,true,-.5f,0,true,-.5f),"Shallow shore releases swimming");
        Check(!SwimmingRules.ShouldSwim(true,false,true,.3f,0,false,0),"Jump out of water releases swimming");
        Check(SwimmingRules.ShouldSwim(true,false,false,-1.15f,-.15f,true,-4),"Supplied ocean level supported");
        foreach(float invalid in new[]{float.NaN,float.PositiveInfinity,float.NegativeInfinity})
        {
            Check(!SwimmingRules.ShouldSwim(true,false,false,invalid,0,false,0),"Invalid player height rejected");
            Check(!SwimmingRules.ShouldSwim(true,false,false,-1,invalid,false,0),"Invalid surface rejected");
            Check(!SwimmingRules.ShouldSwim(true,false,false,-1,0,true,invalid),"Invalid floor rejected");
            Check(SwimmingRules.BuoyancyVelocity(0,-1,0,invalid)==0,"Invalid frame cannot propel swimmer");
        }
        Check(!SwimmingRules.Warn(24)&&SwimmingRules.Warn(24.01f),"Coast warning boundary");
        Check(!SwimmingRules.Restricted(40)&&SwimmingRules.Restricted(40.01f),"Restricted coast boundary");
        Check(SwimmingRules.Restricted(float.PositiveInfinity),"Unbounded open sea is restricted");
        Check(!SwimmingRules.Restricted(float.NaN),"Unknown distance is not an invented boundary crossing");
        Check(SwimmingRules.CanClamberSurface(.3f,0,1,1.1f),"Nearby low dry bank permits clamber");
        Check(!SwimmingRules.CanClamberSurface(.3f,0,1,1.11f),"Distant bank cannot be reached");
        Check(!SwimmingRules.CanClamberSurface(.61f,0,1,1),"Tall dock cannot be climbed");
        Check(!SwimmingRules.CanClamberSurface(-.2f,0,1,1),"Submerged floor uses ordinary swimming");
        Check(!SwimmingRules.CanClamberSurface(.3f,0,.64f,1),"Steep edge cannot be a landing");
        Check(!SwimmingRules.CanClamberSurface(.3f,0,1,0),"Zero reach is not a clamber");
        Check(SwimmingRules.CanClamberSurface(.1f,-.15f,1,1),"Supplied sea level offsets valid bank height");
        foreach(float invalid in new[]{float.NaN,float.PositiveInfinity,float.NegativeInfinity})
        {
            Check(!SwimmingRules.CanClamberSurface(invalid,0,1,1),"Invalid clamber height rejected");
            Check(!SwimmingRules.CanClamberSurface(.3f,invalid,1,1),"Invalid clamber water level rejected");
            Check(!SwimmingRules.CanClamberSurface(.3f,0,invalid,1),"Invalid clamber slope rejected");
            Check(!SwimmingRules.CanClamberSurface(.3f,0,1,invalid),"Invalid clamber reach rejected");
        }
        Check(SwimmingRules.BuoyancyVelocity(0,-2,0,.02f)>0,"Deep swimmer rises");
        Check(SwimmingRules.BuoyancyVelocity(0,-.5f,0,.02f)<0,"High swimmer settles into surface");
        Check(SwimmingRules.BuoyancyVelocity(0,-1.2f,0,.02f)==0,"Surface body depth is equilibrium");
        Check(SwimmingRules.BuoyancyVelocity(0,-100,0,1)<=3,"Slow frame rise speed bounded");
        Check(SwimmingRules.BuoyancyVelocity(0,100,0,1)>=-3,"Slow frame descent speed bounded");
        Check(SwimmingRules.BuoyancyVelocity(2,-1.2f,0,0)==0,"Pause cannot advance buoyancy");
        foreach(float dt in new[]{1f/120,1f/60,1f/30,.1f})
        {
            float feet=-2,velocity=0;
            for(float t=0;t<8;t+=dt){velocity=SwimmingRules.BuoyancyVelocity(velocity,feet,0,dt);feet+=velocity*dt;}
            Check(Math.Abs(feet+1.2f)<.02f,"Buoyancy settles at each frame rate");
        }
        Console.WriteLine("PASS: "+checks+" swimming assertions");
    }
}
