using System;

namespace Blackstone.Foundation
{
    public enum PlayerFailureReason { None, Dead, RestrictedWater }

    // Scaled gameplay time keeps a focus loss or paused game from consuming the alert.
    public sealed class PlayerFailureRules
    {
        public const float RestartDelay = 3;
        public PlayerFailureReason Reason { get; private set; }
        public float Remaining { get; private set; }
        public bool Failed => Reason != PlayerFailureReason.None;
        public bool ReadyToRestart => Failed && Remaining <= 0;
        public bool Fail(PlayerFailureReason reason)
        {
            if (Failed || (reason != PlayerFailureReason.Dead && reason != PlayerFailureReason.RestrictedWater)) return false;
            Reason = reason; Remaining = RestartDelay;
            return true;
        }
        public void Tick(float seconds)
        {
            if (!Failed || seconds <= 0 || float.IsNaN(seconds) || float.IsInfinity(seconds)) return;
            Remaining = Math.Max(0, Remaining - seconds);
        }
        public static float FallDamage(float landingSpeed)
        {
            if (float.IsNaN(landingSpeed) || float.IsInfinity(landingSpeed) || landingSpeed <= 10.5f) return 0;
            return Math.Min(100, (landingSpeed - 10.5f) * 8);
        }
    }
}
