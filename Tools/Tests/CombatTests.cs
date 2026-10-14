using System;
using Blackstone.Foundation;

public static class CombatTests
{
    static int checks;
    static void Check(bool ok,string name){checks++;if(!ok)throw new Exception(name);}
    public static void Main()
    {
        var health=new CombatHealth();
        foreach(float amount in new[]{0,-1,float.NaN,float.PositiveInfinity,float.NegativeInfinity})
            Check(!health.Damage(amount)&&health.Health==100,"Invalid damage cannot change health");
        Check(health.Damage(34)&&health.Health==66,"Pistol damage");
        Check(health.Damage(35)&&health.Health==31,"Knife damage shares the same health");
        Check(health.Damage(9)&&health.Health==22,"Punch shares health");
        Check(health.Damage(45)&&health.Health==0&&health.Dead,"Overkill clamps to zero");
        Check(!health.Damage(1)&&health.Health==0,"Death cannot be applied twice");
        float[] expected={0,35,34,30,50,45,34,34,20,45,30};
        for(int i=0;i<expected.Length;i++)Check(CombatHealth.WeaponDamage((Equipment)i)==expected[i],"Weapon damage mapping "+i);
        Check(CombatHealth.WeaponDamage((Equipment)999)==0,"Unknown equipment cannot damage");
        Check(CombatHealth.PunchStaminaCost(0)==12,"Jab stamina cost");
        Check(CombatHealth.PunchStaminaCost(1)==20,"Cross stamina cost");
        Check(CombatHealth.PunchStaminaCost(2)==20,"Hook stamina cost");
        var target=new CombatHealth();var weapon=new WeaponState();weapon.Equip(Equipment.Pistol);weapon.Tick(1);
        for(int i=0;i<3;i++)
        {
            Check(weapon.TryUse(),"Loaded pistol can fire");
            Check(target.Damage(CombatHealth.WeaponDamage(weapon.Equipped)),"Shot damages live target");weapon.Tick(1);
        }
        Check(target.Dead&&weapon.Magazine==12,"Three pistol hits kill and consume exactly three rounds");
        Check(weapon.TryReload()&&!weapon.TryUse(),"Reloading cannot fire an extra shot");
        Console.WriteLine("PASS: "+checks+" combat health/weapon/stamina assertions");
    }
}
