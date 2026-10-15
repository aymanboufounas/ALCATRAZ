using System;

namespace Blackstone.Foundation
{
    public sealed class CombatHealth
    {
        public float Health { get; private set; } = 100;
        public bool Dead => Health <= 0;
        public static int PunchStaminaCost(int combo) => combo == 0 ? 12 : 20;
        public bool Restore(float health)
        {
            if (float.IsNaN(health) || float.IsInfinity(health) || health < 0 || health > 100) return false;
            Health = health;
            return true;
        }
        public bool Damage(float amount)
        {
            if (Dead || amount <= 0 || float.IsNaN(amount) || float.IsInfinity(amount)) return false;
            Health = Math.Max(0, Health - amount);
            return true;
        }
        public static float WeaponDamage(Equipment weapon)
        {
            switch (weapon)
            {
                case Equipment.Knife: return 35;
                case Equipment.Machete: return 45;
                case Equipment.Pistol: case Equipment.M9A3: case Equipment.PX4: return 34;
                case Equipment.Revolver: return 50;
                case Equipment.Rifle: case Equipment.ColtM5: return 30;
                case Equipment.PMX: return 20;
                case Equipment.BRX1: return 45;
                default: return 0;
            }
        }
    }
}
