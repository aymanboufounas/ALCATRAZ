using System;
using System.IO;
using UnityEngine;
using UnityEngine.SceneManagement;
using Blackstone.Story;

namespace Blackstone.Save
{
    [Serializable]
    public sealed class PrisonCheckpoint
    {
        public PrisonStoryState story = new PrisonStoryState();
        public Vector3 position;
        public float yaw;
        public string playerName = "Elias Vale";
        public string outfit = "PrisonWorkUniform";
        public int health = 100;
        public string savedUtc;
    }
    public static class PrisonSave
    {
        static bool Alcatraz => SceneManager.GetActiveScene().name.StartsWith("SC_Alcatraz", StringComparison.Ordinal);
        public static string PathName => SlotPath(0);
        public static string SlotPath(int slot)
        {
            string name=Alcatraz?Blackstone.Alcatraz.AlcatrazMap.CheckpointFile:"blackstone-chapter01.json";
            return CheckpointStorage.SlotPath(Application.persistentDataPath,name,slot);
        }
        public static bool Exists => File.Exists(PathName) || File.Exists(PathName + ".bak");
        public static bool TryLoad(out PrisonCheckpoint checkpoint, int slot=0)
        {
            PrisonCheckpoint loaded=null;
            bool found=CheckpointStorage.TryRead(SlotPath(slot),json=>
            {
                var candidate=JsonUtility.FromJson<PrisonCheckpoint>(json);
                if(!Valid(candidate))return false;
                loaded=candidate;return true;
            },out var contents);
            checkpoint=found?loaded:null;return found;
        }
        public static bool Write(PrisonCheckpoint checkpoint, int slot=0)
        {
            if(!Valid(checkpoint))return false;
            checkpoint.savedUtc=DateTime.UtcNow.ToString("o");
            return CheckpointStorage.Write(SlotPath(slot),JsonUtility.ToJson(checkpoint,true));
        }
        static bool Valid(PrisonCheckpoint candidate)
        {
            if(candidate==null||candidate.story==null||!candidate.story.IsValid()||candidate.health<=0||candidate.health>100)return false;
            Vector3 p=candidate.position;
            bool outside=Alcatraz?p.x< -130||p.x > 135||p.z< -190||p.z>190||p.y<1.2f||p.y > 68
                :p.x< -50||p.x>50||p.z< -45||p.z>55||p.y< -.2f||p.y>6;
            return Finite(p.x)&&Finite(p.y)&&Finite(p.z)&&Finite(candidate.yaw)&&!outside;
        }
        static bool Finite(float x) => !float.IsNaN(x) && !float.IsInfinity(x);
    }
}
