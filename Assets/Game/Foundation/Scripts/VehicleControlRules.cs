namespace Blackstone.Foundation
{
    public static class VehicleControlRules
    {
        public static float Lift(bool canControl, bool keyboardRise, bool keyboardDescend,
            bool gamepadRise, bool gamepadDescend)
        {
            if (!canControl) return 0;
            int rise = (keyboardRise || gamepadRise) ? 1 : 0;
            int descend = (keyboardDescend || gamepadDescend) ? 1 : 0;
            return rise - descend;
        }
    }
}
