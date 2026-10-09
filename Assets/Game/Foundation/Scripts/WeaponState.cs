using System;

namespace Blackstone.Foundation
{
    public enum Equipment { Unarmed, Knife, Pistol, Rifle }

    // Independent of Unity: finite ammunition, cooldowns and interruptible reloads.
    public sealed class WeaponState
    {
        readonly int[] loaded = { 0, 0, 12, 24 };
        readonly int[] reserve = { 0, 0, 60, 96 };
        float cooldown, reloadRemaining;
        public Equipment Equipped { get; private set; }
        public bool Reloading { get; private set; }
        public int Magazine => loaded[(int)Equipped];
        public int Reserve => reserve[(int)Equipped];
        public int Capacity => Equipped == Equipment.Pistol ? 12 : Equipped == Equipment.Rifle ? 24 : 0;
        public float ReloadSeconds => Equipped == Equipment.Pistol ? 1.7f : 2.2f;
        public float ReloadProgress => Reloading ? 1f - reloadRemaining / ReloadSeconds : 0;
        public bool IsFirearm => Equipped == Equipment.Pistol || Equipped == Equipment.Rifle;

        public bool Equip(Equipment value)
        {
            if (!Enum.IsDefined(typeof(Equipment), value) || value == Equipped) return false;
            Equipped = value; Reloading = false; reloadRemaining = 0; cooldown = .2f;
            return true;
        }
        public void Tick(float seconds, bool canAct = true)
        {
            if (!canAct || seconds <= 0 || float.IsNaN(seconds) || float.IsInfinity(seconds)) return;
            cooldown = Math.Max(0, cooldown - seconds);
            if (!Reloading) return;
            reloadRemaining -= seconds;
            if (reloadRemaining > .00001f) return;
            int index = (int)Equipped;
            int transferred = Math.Min(Capacity - loaded[index], reserve[index]);
            loaded[index] += transferred; reserve[index] -= transferred;
            Reloading = false; reloadRemaining = 0;
        }
        public bool TryReload(bool canAct = true)
        {
            if (!canAct || !IsFirearm || Reloading || Magazine == Capacity || Reserve == 0) return false;
            Reloading = true; reloadRemaining = ReloadSeconds; return true;
        }
        public bool TryUse(bool canAct = true)
        {
            if (!canAct || Reloading || cooldown > .00001f) return false;
            if (IsFirearm)
            {
                if (Magazine == 0) return false;
                loaded[(int)Equipped]--;
                cooldown = Equipped == Equipment.Rifle ? .13f : .26f;
            }
            else cooldown = Equipped == Equipment.Knife ? .58f : .65f;
            return true;
        }
    }
}
