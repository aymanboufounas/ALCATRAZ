using System;
using System.IO;

namespace Blackstone.Save
{
    // Disk operations independent of Unity; callers validate the decoded checkpoint.
    public static class CheckpointStorage
    {
        public static string SlotPath(string directory,string legacyName,int slot)
        {
            if(slot<0||slot>3)throw new ArgumentOutOfRangeException(nameof(slot));
            string name=slot==0?legacyName:Path.GetFileNameWithoutExtension(legacyName)+".slot"+slot+".json";
            return Path.Combine(directory,name);
        }
        public static bool TryRead(string path,Func<string,bool> accept,out string contents)
        {
            if(string.IsNullOrEmpty(path)||accept==null){contents=null;return false;}
            foreach(string candidate in new[]{path,path+".bak"})
            {
                try
                {
                    if(!File.Exists(candidate))continue;
                    string data=File.ReadAllText(candidate);
                    if(!accept(data))continue;
                    contents=data;return true;
                }
                catch(Exception e) when(e is IOException||e is UnauthorizedAccessException||e is ArgumentException)
                { }
            }
            contents=null;return false;
        }
        public static bool Write(string path,string contents)
        {
            if(string.IsNullOrEmpty(path)||contents==null)return false;
            string temp=path+".tmp";
            try
            {
                string directory=Path.GetDirectoryName(path);if(!string.IsNullOrEmpty(directory))Directory.CreateDirectory(directory);
                File.WriteAllText(temp,contents);
                if(File.Exists(path))File.Replace(temp,path,path+".bak");else File.Move(temp,path);
                return true;
            }
            catch(Exception e) when(e is IOException||e is UnauthorizedAccessException||e is ArgumentException||e is NotSupportedException)
            {
                try{if(File.Exists(temp))File.Delete(temp);}catch(IOException){ }catch(UnauthorizedAccessException){ }
                return false;
            }
        }
    }
}
