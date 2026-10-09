using System;
using Blackstone.Foundation;

public static class WeaponStateTests
{
    static int checks;
    static void Check(bool value,string message){checks++;if(!value)throw new Exception(message);}
    static void Ready(WeaponState s){s.Tick(3);}
    public static void Main()
    {
        var s=new WeaponState();Check(s.Equipped==Equipment.Unarmed,"Initial unarmed state");
        Check(!s.Equip((Equipment)99),"Reject invalid equipment");
        Check(s.TryUse(),"First punch");Check(!s.TryUse(),"Punch cooldown");
        s.Tick(20,false);Check(!s.TryUse(),"Blocked clock cannot bypass cooldown");Ready(s);
        Check(s.Equip(Equipment.Pistol),"Equip pistol");Check(!s.TryUse(),"Equip has a brief cooldown");Ready(s);
        int shots=0;
        for(int i=0;i<12;i++)
        {Check(s.TryUse(),"Pistol shot "+i);shots++;Check(!s.TryUse(),"No same-frame duplicate shot");s.Tick(.3f);}
        Check(s.Magazine==0&&s.Reserve==60,"Empty magazine retains reserve");Check(!s.TryUse(),"No empty shot");
        Check(!s.TryReload(false),"Blocked input cannot start reload");Check(s.TryReload(),"Start reload");
        Check(!s.TryReload(),"No duplicate reload");Check(!s.TryUse(),"No fire during reload");
        s.Tick(.7f);Check(s.Reloading&&s.Magazine==0,"No early ammo transfer");
        float progress=s.ReloadProgress;
        foreach(float bad in new[]{-1f,float.NaN,float.PositiveInfinity,float.NegativeInfinity})s.Tick(bad);
        Check(s.ReloadProgress==progress,"Invalid deltas leave clock intact");
        s.Tick(60,false);Check(s.Reloading&&s.ReloadProgress==progress,"Pause freezes reload");
        Check(s.Equip(Equipment.Rifle),"Switch cancels pistol reload");Check(!s.Reloading,"Reload interrupted");
        Check(s.Equip(Equipment.Pistol),"Return to pistol");Ready(s);Check(s.Magazine==0&&s.Reserve==60,"Canceled reload cannot generate ammo");
        Check(s.TryReload(),"Reload after interruption");s.Tick(1.7f);Check(!s.Reloading&&s.Magazine==12&&s.Reserve==48,"Exact reload time completes");
        Check(!s.TryReload(),"Cannot reload full magazine");
        Check(s.TryUse(),"Fire after reload");shots++;Ready(s);Check(s.TryReload(),"Top up partial magazine");s.Tick(2);
        Check(s.Magazine==12&&s.Reserve==47,"Only missing rounds transferred");
        Check(s.Magazine+s.Reserve+shots==72,"Pistol ammo conservation");
        // Exhaust every reserve: the final partial magazine must not create extra rounds.
        while(s.Magazine>0||s.Reserve>0)
        {
            Ready(s);
            if(s.Magazine>0){Check(s.TryUse(),"Consume remaining ammo");shots++;}
            else {Check(s.TryReload(),"Reload remaining reserve");s.Tick(3);}
            Check(s.Magazine>=0&&s.Magazine<=s.Capacity&&s.Reserve>=0,"Ammo bounds");
            Check(s.Magazine+s.Reserve+shots==72,"Ammo conservation across depletion");
        }
        Check(shots==72,"All available pistol rounds accounted for");Check(!s.TryReload(),"No reload without reserve");
        Check(s.Equip(Equipment.Rifle),"Equip independent rifle");Ready(s);Check(s.Magazine==24&&s.Reserve==96,"Rifle ammo is independent");
        Check(s.TryUse(),"Rifle fires");s.Tick(.12f);Check(!s.TryUse(),"Rifle rate limit");s.Tick(.02f);Check(s.TryUse(),"Rifle fires after cooldown");
        Check(s.TryReload(),"Rifle reload");s.Tick(2.19f);Check(s.Reloading,"Rifle duration gate");s.Tick(.01f);Check(!s.Reloading&&s.Magazine==24&&s.Reserve==94,"Rifle reload completion");
        Check(s.Equip(Equipment.Knife),"Equip knife");Ready(s);Check(!s.TryReload(),"Melee cannot reload");Check(s.TryUse(),"Knife strike");Check(!s.TryUse(),"Knife cooldown");
        Console.WriteLine("PASS: "+checks+" ammunition, cooldown, reload, interruption and pause assertions.");
    }
}
