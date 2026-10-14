using System;

namespace Blackstone.Foundation
{
    public enum Equipment { Unarmed, Knife, Pistol, Rifle, Revolver, Machete, M9A3, PX4, PMX, BRX1, ColtM5 }

    // Independent of Unity: finite ammunition, cooldowns and interruptible reloads.
    public sealed class WeaponState
    {
        readonly int[] loaded = { 0, 0, 15, 30, 6, 0, 17, 17, 30, 10, 30 };
        readonly int[] reserve = { 0, 0, 75, 120, 36, 0, 68, 68, 120, 40, 120 };
        float cooldown, reloadRemaining;
        public Equipment Equipped { get; private set; }
        public bool Reloading { get; private set; }
        public int Magazine => loaded[(int)Equipped];
        public int Reserve => reserve[(int)Equipped];
        static readonly int[] capacities={0,0,15,30,6,0,17,17,30,10,30};
        public int Capacity=>capacities[(int)Equipped];
        public float ReloadSeconds=>Equipped==Equipment.Revolver?2.7f:IsAutomatic?2.2f:1.7f;
        public float ReloadProgress => Reloading ? 1f - reloadRemaining / ReloadSeconds : 0;
        public bool IsFirearm => (int)Equipped>=2&&Equipped!=Equipment.Machete;
        public bool IsAutomatic=>Equipped==Equipment.Rifle||Equipped==Equipment.PMX||Equipped==Equipment.ColtM5;
        public int LoadedFor(Equipment value) => Enum.IsDefined(typeof(Equipment),value)?loaded[(int)value]:0;
        public int ReserveFor(Equipment value) => Enum.IsDefined(typeof(Equipment),value)?reserve[(int)value]:0;

        public int[] LoadedSnapshot() => (int[])loaded.Clone();
        public int[] ReserveSnapshot() => (int[])reserve.Clone();
        public bool Restore(int[] magazines,int[] ammunition,Equipment equipped)
        {
            if(!Enum.IsDefined(typeof(Equipment),equipped)||magazines==null||ammunition==null
                ||magazines.Length!=loaded.Length||ammunition.Length!=reserve.Length)return false;
            for(int i=0;i<loaded.Length;i++)
                if(magazines[i]<0||magazines[i]>capacities[i]||ammunition[i]<0||ammunition[i]>10000
                    ||capacities[i]==0&&ammunition[i]!=0)return false;
            Array.Copy(magazines,loaded,loaded.Length);Array.Copy(ammunition,reserve,reserve.Length);
            Equipped=equipped;Reloading=false;reloadRemaining=cooldown=0;return true;
        }

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
                cooldown = IsAutomatic ? .13f : Equipped == Equipment.Revolver ? .40f : .26f;
            }
            else cooldown = Equipped == Equipment.Knife || Equipped==Equipment.Machete ? .58f : .65f;
            return true;
        }
    }
}
