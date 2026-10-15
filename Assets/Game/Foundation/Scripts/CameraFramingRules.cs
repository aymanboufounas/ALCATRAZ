using System;

namespace Blackstone.Foundation
{
    // Independent of Unity: rank obstruction-safe orbit alternatives without hiding the avatar.
    public static class CameraFramingRules
    {
        static readonly float[] offsets={35,-35,70,-70,105,-105,140,-140,180};
        public static int CandidateCount=>offsets.Length;
        public static float Offset(int index)=>offsets[index];
        public static float MinimumDistance(bool aiming)=>aiming?1.05f:1.65f;
        // A raised view can show the body in a narrow cell even when the normal
        // horizontal boom cannot fit. This is only a last-resort candidate pool.
        public static float ElevatedMinimumDistance(bool aiming)=>aiming?1.05f:.95f;
        public static float ElevatedScore(float offset,float pitchIncrease,float distance,bool clear,bool aiming)
        {
            if(!clear||float.IsNaN(offset)||float.IsInfinity(offset)||float.IsNaN(pitchIncrease)||float.IsInfinity(pitchIncrease)
                ||float.IsNaN(distance)||float.IsInfinity(distance)||pitchIncrease<=0||pitchIncrease>100
                ||distance<ElevatedMinimumDistance(aiming))return float.NegativeInfinity;
            return Math.Min(distance,3.15f)*1.5f-Math.Abs(offset)*.004f-pitchIncrease*.009f;
        }
        public static float Score(float offset,float distance,bool clear,bool aiming)
        {
            if(!clear||float.IsNaN(offset)||float.IsInfinity(offset)||float.IsNaN(distance)||float.IsInfinity(distance)
                ||distance<MinimumDistance(aiming))return float.NegativeInfinity;
            return Math.Min(distance,3.15f)*1.5f-Math.Abs(offset)*.004f;
        }
        public static float FieldOfView(bool aiming,float distance)
        {
            if(float.IsNaN(distance)||float.IsInfinity(distance)||distance<0)return 58;
            if(aiming&&distance>=MinimumDistance(true))return 48;
            return distance<2.4f?72:58;
        }
    }
}
