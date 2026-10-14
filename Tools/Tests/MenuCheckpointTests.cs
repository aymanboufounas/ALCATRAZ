using System;
using System.IO;
using Blackstone.Save;
using Blackstone.Foundation;

public static class MenuCheckpointTests
{
    static int checks;
    static void Check(bool valid,string label){checks++;if(!valid)throw new Exception(label);}
    public static void Main()
    {
        string root=Path.Combine(Path.GetTempPath(),"alcatraz-menu-tests-"+Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        try
        {
            string autosave=CheckpointStorage.SlotPath(root,"chapter.json",0),manual=CheckpointStorage.SlotPath(root,"chapter.json",1);
            Check(autosave==Path.Combine(root,"chapter.json"),"Autosave keeps legacy filename");
            for(int i=1;i<4;i++)Check(CheckpointStorage.SlotPath(root,"chapter.json",i)==Path.Combine(root,"chapter.slot"+i+".json"),"Manual slot filename "+i);
            foreach(int bad in new[]{-1,4})
            {
                bool rejected=false;try{CheckpointStorage.SlotPath(root,"chapter.json",bad);}catch(ArgumentOutOfRangeException){rejected=true;}
                Check(rejected,"Invalid slot cannot reach a path");
            }
            Check(!CheckpointStorage.TryRead(autosave,x=>x=="valid",out var data),"Empty slot cannot load");
            Check(!CheckpointStorage.TryRead(null,x=>true,out data),"Missing path cannot read a backup");
            Check(!CheckpointStorage.TryRead(autosave,null,out data),"Missing validator cannot accept a checkpoint");
            Check(CheckpointStorage.Write(autosave,"valid"),"First save writes");
            Check(CheckpointStorage.TryRead(autosave,x=>x=="valid",out data)&&data=="valid","Save loads");
            Check(CheckpointStorage.Write(manual,"manual"),"Manual slot writes");
            Check(File.ReadAllText(autosave)=="valid","Manual save does not replace autosave");
            Check(CheckpointStorage.Write(autosave,"new"),"Existing slot replaces atomically");
            Check(File.ReadAllText(autosave+".bak")=="valid","Previous save retained as backup");
            File.WriteAllText(autosave,"corrupt");
            Check(CheckpointStorage.TryRead(autosave,x=>x=="valid",out data)&&data=="valid","Invalid primary falls back to valid backup");
            Check(CheckpointStorage.TryRead(autosave,x=>{if(x=="corrupt")throw new ArgumentException();return x=="valid";},out data),"Parser rejection falls back to backup");
            File.WriteAllText(autosave+".bak","bad backup");
            Check(!CheckpointStorage.TryRead(autosave,x=>x=="valid",out data)&&data==null,"Two invalid saves never load");
            Check(!CheckpointStorage.Write(root,"blocked"),"Filesystem failure returns false");
            Check(!File.Exists(root+".tmp"),"Failed writes clean temporary file");
            Check(!CheckpointStorage.Write(null,"data")&&!CheckpointStorage.Write(manual,null),"Invalid writes rejected");
            Check(File.ReadAllText(manual)=="manual","Rejected write keeps manual save");
            var weapon=new WeaponState();weapon.Equip(Equipment.Pistol);weapon.Tick(1);weapon.TryUse();
            int[] loaded=weapon.LoadedSnapshot(),reserve=weapon.ReserveSnapshot();
            var restored=new WeaponState();
            Check(restored.Restore(loaded,reserve,Equipment.Pistol)&&restored.Magazine==14&&restored.Reserve==75,"Ammo checkpoint restored");
            loaded[2]=0;reserve[2]=0;
            Check(restored.Magazine==14&&restored.Reserve==75,"Restore copies arrays");
            loaded=restored.LoadedSnapshot();reserve=restored.ReserveSnapshot();
            Check(!restored.Restore(null,reserve,Equipment.Pistol),"Null ammo rejects");
            Check(!restored.Restore(new int[1],reserve,Equipment.Pistol),"Truncated ammo rejects");
            loaded[2]=999;Check(!restored.Restore(loaded,reserve,Equipment.Pistol)&&restored.Magazine==14,"Over-capacity ammo rejected atomically");
            loaded[2]=14;reserve[2]=-1;Check(!restored.Restore(loaded,reserve,Equipment.Pistol)&&restored.Reserve==75,"Negative reserve rejected atomically");
            reserve[2]=10001;Check(!restored.Restore(loaded,reserve,Equipment.Pistol),"Unbounded reserve rejected");
            reserve[2]=75;Check(!restored.Restore(loaded,reserve,(Equipment)999),"Unknown equipment rejected");
            reserve[0]=1;Check(!restored.Restore(loaded,reserve,Equipment.Pistol),"Melee ammunition rejected");
            reserve[0]=0;Check(restored.Restore(loaded,reserve,Equipment.Pistol),"Valid restore after rejected mutations");
            restored.TryReload();Check(restored.Reloading,"Damaged magazine can start reload");
            Check(restored.Restore(loaded,reserve,Equipment.Pistol)&&!restored.Reloading&&restored.TryUse(),"Restoring checkpoint cancels pending reload and cooldown");
            Console.WriteLine("PASS: "+checks+" menu checkpoint assertions");
        }
        finally{Directory.Delete(root,true);}
    }
}
