using System;
using Blackstone.Foundation;

public static class PlayerFailureTests
{
    static int checks;
    static void Check(bool ok, string name) { checks++; if (!ok) throw new Exception(name); }
    public static void Main()
    {
        var health = new CombatHealth();
        Check(health.Health == 100 && !health.Dead, "Player starts at full health");
        Check(health.Damage(12) && health.Health == 88, "A rival strike reduces health percentage");
        Check(health.Restore(45) && health.Health == 45, "Checkpoint restores damaged health");
        foreach (float value in new[] { -1, 101, float.NaN, float.PositiveInfinity, float.NegativeInfinity })
            Check(!health.Restore(value) && health.Health == 45, "Invalid checkpoint health is rejected without mutation");
        Check(health.Damage(500) && health.Health == 0 && health.Dead, "Overkill is exactly zero health");
        var dead = new PlayerFailureRules();
        dead.Tick(100);
        Check(!dead.Failed && !dead.ReadyToRestart, "No restart without failure");
        Check(!dead.Fail(PlayerFailureReason.None) && !dead.Fail((PlayerFailureReason)99), "Invalid failure reason is rejected");
        Check(dead.Fail(PlayerFailureReason.Dead) && dead.Remaining == 3, "Death shows a three second alert");
        Check(!dead.Fail(PlayerFailureReason.RestrictedWater) && dead.Reason == PlayerFailureReason.Dead, "Failure cannot overwrite a death or reset countdown");
        foreach (float time in new[] { 0, -1, float.NaN, float.PositiveInfinity, float.NegativeInfinity })
            dead.Tick(time);
        Check(dead.Remaining == 3 && !dead.ReadyToRestart, "Paused and invalid deltas cannot advance failure");
        dead.Tick(1.25f);
        Check(Math.Abs(dead.Remaining - 1.75f) < .001f && !dead.ReadyToRestart, "Countdown advances with active gameplay");
        dead.Tick(5);
        Check(dead.Remaining == 0 && dead.ReadyToRestart, "Restart becomes ready once, without a negative timer");
        Check(health.Restore(100) && !health.Dead, "Mission restart recovers full health");
        var wanted = new PlayerFailureRules();
        Check(wanted.Fail(PlayerFailureReason.RestrictedWater), "Boundary crossing can fail without damage");
        wanted.Tick(3);
        Check(wanted.ReadyToRestart && health.Health == 100, "Wanted restart does not need to kill player");
        foreach (float speed in new[] { -1, 0, 9, 10.5f, float.NaN, float.PositiveInfinity })
            Check(PlayerFailureRules.FallDamage(speed) == 0, "Ordinary jump or invalid speed does not damage player");
        Check(PlayerFailureRules.FallDamage(15.5f) == 40, "Hard fall deals proportional damage");
        Check(PlayerFailureRules.FallDamage(50) == 100, "Extreme fall can be fatal");
        Console.WriteLine("PASS: " + checks + " player health/failure/restart assertions");
    }
}
