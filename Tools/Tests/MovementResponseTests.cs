using System;
using Blackstone.Foundation;

public static class MovementResponseTests
{
    static int checks;
    static void Check(bool value,string message){checks++;if(!value)throw new Exception(message);}
    static bool Near(float a,float b,float tolerance=.0002f)=>Math.Abs(a-b)<=tolerance;
    static MovementResponseRules.PlanarVelocity Step(MovementResponseRules.PlanarVelocity value,float x,float z,float dt)
        =>MovementResponseRules.Approach(value.X,value.Z,x,z,8.5f,12,dt);
    public static void Main()
    {
        float minimumStopDistance=float.PositiveInfinity,maximumStopDistance=0;
        foreach(int fps in new[]{30,60,120,240})
        {
            float dt=1f/fps;
            var value=new MovementResponseRules.PlanarVelocity(0,0);
            for(int i=0;i<fps;i++)
            {
                value=Step(value,0,5.5f,dt);
                Check(value.Z>=0&&value.Z<=5.50001f,"Acceleration overshot the sprint target at "+fps+" Hz");
                if(i+1==fps/2)Check(Near(value.Z,4.25f),"Sprint acceleration changed with frame rate");
            }
            Check(Near(value.Z,5.5f),"Sprint reaches its requested speed");
            float distance=0,firstStopped=0;
            for(int i=0;i<fps;i++)
            {
                float previous=value.Z;value=Step(value,0,0,dt);distance+=value.Z*dt;
                Check(value.Z>=0&&value.Z<=previous+.00001f,"Braking overshot zero");
                if(value.Z==0&&firstStopped==0)firstStopped=(i+1)*dt;
            }
            Check(firstStopped>=5.5f/12-.0001f&&firstStopped<=5.5f/12+dt+.0001f,
                "Stopping time is bounded by one simulation frame");
            minimumStopDistance=Math.Min(minimumStopDistance,distance);maximumStopDistance=Math.Max(maximumStopDistance,distance);

            value=new MovementResponseRules.PlanarVelocity(0,5.5f);
            for(int i=0;i<fps*2;i++)
            {
                value=Step(value,0,-5.5f,dt);
                Check(value.Z>=-5.50001f&&value.Z<=5.50001f,"Reversal overshot its target");
                if(i+1==fps/5)Check(Near(value.Z,3.1f),"Reverse input uses braking rather than the weaker acceleration");
                if(i+1==fps)Check(Near(value.Z,-8.5f*(1-5.5f/12),.001f),
                    "Reversal spends residual frame time accelerating after the pivot");
            }
            Check(Near(value.Z,-5.5f),"Reversal reaches the opposite sprint speed");

            value=new MovementResponseRules.PlanarVelocity(0,5.5f);
            for(int i=0;i<fps;i++)
            {
                value=Step(value,0,2.15f,dt);
                Check(value.Z>=2.14999f&&value.Z<=5.50001f,"Sprint-to-jog undershot the requested gait");
                if(i+1==fps/5)Check(Near(value.Z,3.1f),"Sprint-to-jog uses the braking rate");
            }
            Check(Near(value.Z,2.15f),"Sprint-to-jog settles at the requested speed");

            float diagonal=5.5f/(float)Math.Sqrt(2);
            value=new MovementResponseRules.PlanarVelocity(0,0);
            for(int i=0;i<fps;i++)value=Step(value,diagonal,diagonal,dt);
            Check(Near(value.Magnitude,5.5f),"Diagonal input cannot exceed the sprint limit");
        }
        Check(maximumStopDistance-minimumStopDistance<.09f,"Stopping distances remain comparable across 30–240 Hz");
        Check(minimumStopDistance>1.15f&&maximumStopDistance<1.27f,"Braking distance stays near the continuous 1.26 m solution");

        var wall=MovementResponseRules.RejectIntoWall(2,5,0,-1);
        Check(Near(wall.X,2)&&Near(wall.Z,0),"A wall removes inward momentum and preserves tangent motion");
        wall=MovementResponseRules.RejectIntoWall(2,-5,0,-1);
        Check(Near(wall.X,2)&&Near(wall.Z,-5),"A wall cannot remove movement away from it");
        wall=MovementResponseRules.RejectIntoWall(2,5,0,-4);
        Check(Near(wall.X,2)&&Near(wall.Z,0),"Wall rejection accepts a non-unit normal");
        wall=MovementResponseRules.RejectIntoWall(5,0,-1,-1);
        Check(Near(wall.X,2.5f)&&Near(wall.Z,-2.5f),"Angled walls preserve their sliding tangent");
        wall=MovementResponseRules.RejectIntoWall(2,5,0,0);
        Check(Near(wall.X,2)&&Near(wall.Z,5),"Degenerate contact normals do not erase movement");
        var paused=MovementResponseRules.Approach(1,2,5,5,8.5f,12,0);
        Check(Near(paused.X,1)&&Near(paused.Z,2),"A zero-time update cannot advance movement");
        var air=MovementResponseRules.Approach(0,0,0,5.5f,8.5f*.25f,12*.25f,.2f);
        Check(Near(air.Z,.425f),"Air control keeps the configured reduced acceleration");
        foreach(float invalid in new[]{float.NaN,float.PositiveInfinity,float.NegativeInfinity})
        {
            var reset=MovementResponseRules.Approach(invalid,0,0,5,8.5f,12,.1f);
            Check(reset.Magnitude==0,"Invalid movement state is reset instead of propagating NaN");
            reset=MovementResponseRules.Approach(0,0,0,5,8.5f,12,invalid);
            Check(reset.Magnitude==0,"Invalid elapsed time cannot corrupt the controller");
            reset=MovementResponseRules.RejectIntoWall(1,2,invalid,0);
            Check(reset.Magnitude==0,"Invalid collision normals cannot corrupt movement");
        }
        Console.WriteLine("PASS: "+checks+" movement response assertions across 30/60/120/240 Hz");
    }
}
