using System;
using Blackstone.Foundation;

public static class CameraFramingTests
{
    static int checks;
    static void Check(bool ok,string label){checks++;if(!ok)throw new Exception(label);}
    public static void Main()
    {
        Check(float.IsNegativeInfinity(CameraFramingRules.Score(0,.3f,true,false)),"Contracted boom cannot qualify as full-body framing");
        Check(float.IsNegativeInfinity(CameraFramingRules.Score(35,3,false,false)),"Blocked alternate cannot qualify");
        foreach(float invalid in new[]{float.NaN,float.PositiveInfinity,float.NegativeInfinity})
        {
            Check(float.IsNegativeInfinity(CameraFramingRules.Score(35,invalid,true,false)),"Invalid distance rejected");
            Check(float.IsNegativeInfinity(CameraFramingRules.Score(invalid,3,true,false)),"Invalid angle rejected");
        }
        Check(CameraFramingRules.Score(0,3.15f,true,false)>CameraFramingRules.Score(90,3.15f,true,false),"Unobstructed rear orbit preferred");
        Check(CameraFramingRules.Score(70,3,true,false)>CameraFramingRules.Score(35,1.65f,true,false),"Safe framing room beats near-head view");
        Check(CameraFramingRules.Score(35,3,true,false)==CameraFramingRules.Score(-35,3,true,false),"Left/right candidates treated symmetrically");
        Check(CameraFramingRules.FieldOfView(false,1.65f)>CameraFramingRules.FieldOfView(false,3.15f),"Close spaces widen field of view");
        Check(CameraFramingRules.FieldOfView(true,1.9f)==48,"Clear aimed view preserved");
        Check(CameraFramingRules.FieldOfView(true,.4f)==72,"Severely blocked aim widens framing");
        float best=float.NegativeInfinity;int chosen=-1;
        for(int i=0;i<CameraFramingRules.CandidateCount;i++)
        {
            bool clear=i==4;float score=CameraFramingRules.Score(CameraFramingRules.Offset(i),clear?2.8f:.2f,clear,false);
            if(score>best){best=score;chosen=i;}
        }
        Check(chosen==4,"A side escape is selected when rear and nearer candidates are blocked");
        chosen=-1;best=float.NegativeInfinity;
        for(int i=0;i<CameraFramingRules.CandidateCount;i++)
        {
            float score=CameraFramingRules.Score(CameraFramingRules.Offset(i),.3f,false,false);
            if(score>best){best=score;chosen=i;}
        }
        Check(chosen==-1,"No unsafe camera position is invented in a fully enclosed space");
        Check(CameraFramingRules.ElevatedMinimumDistance(false)>=.9f,"Raised fallback keeps the lens away from the head");
        Check(CameraFramingRules.ElevatedMinimumDistance(true)>=CameraFramingRules.MinimumDistance(true),"Raised aim preserves its minimum lens distance");
        Check(float.IsNegativeInfinity(CameraFramingRules.ElevatedScore(0,58,.3f,true,false)),"Raised view cannot accept a head-level contracted boom");
        Check(!float.IsNegativeInfinity(CameraFramingRules.ElevatedScore(0,58,1.3f,true,false)),"Raised view accepts usable room above a narrow cell");
        Check(float.IsNegativeInfinity(CameraFramingRules.ElevatedScore(0,58,1.3f,false,false)),"Raised view still rejects obstructed positions");
        Check(CameraFramingRules.ElevatedScore(0,23,1.4f,true,false)>CameraFramingRules.ElevatedScore(0,58,1.4f,true,false),
            "Equal clearance prefers the smaller pitch change");
        Check(CameraFramingRules.ElevatedScore(0,58,1.4f,true,false)>CameraFramingRules.ElevatedScore(0,23,.95f,true,false),
            "Useful body clearance can justify the steeper raised view");
        foreach(float invalid in new[]{float.NaN,float.PositiveInfinity,float.NegativeInfinity})
        {
            Check(float.IsNegativeInfinity(CameraFramingRules.ElevatedScore(0,58,invalid,true,false)),"Raised view rejects invalid distance");
            Check(float.IsNegativeInfinity(CameraFramingRules.ElevatedScore(invalid,58,1.3f,true,false)),"Raised view rejects invalid yaw");
            Check(float.IsNegativeInfinity(CameraFramingRules.ElevatedScore(0,invalid,1.3f,true,false)),"Raised view rejects invalid pitch");
        }
        Check(float.IsNegativeInfinity(CameraFramingRules.ElevatedScore(0,0,1.3f,true,false)),"Raised pool requires an actual pitch increase");
        Check(float.IsNegativeInfinity(CameraFramingRules.ElevatedScore(0,101,1.3f,true,false)),"Raised pool rejects an out-of-range pitch change");
        Console.WriteLine("PASS: "+checks+" third-person framing assertions");
    }
}
