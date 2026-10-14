using System;
using System.IO;
using UnityEngine;
using UnityEngine.SceneManagement;
using Blackstone.Supplied;

namespace Blackstone.Foundation
{
    [Serializable]
    public sealed class ExplorationCheckpoint
    {
        public int version=1;
        public string scene,savedUtc;
        public Vector3 position;
        public float yaw;
        public bool interior,annex;
        public Equipment equipped;
        public int[] magazines,ammunition;
        public bool Valid()
        {
            if(version!=1||scene!=SceneManager.GetActiveScene().name||!Finite(yaw)
                ||!Finite(position.x)||!Finite(position.y)||!Finite(position.z))return false;
            if(!new WeaponState().Restore(magazines,ammunition,equipped))return false;
            if(annex)return interior&&SuppliedExtrasWorld.ContainsPosition(position)&&position.y<90;
            if(interior)
            {
                Vector3 local=SuppliedPrisonInterior.Local(position);
                return Mathf.Abs(local.x)<29&&local.z> -45&&local.z<69&&local.y>29&&local.y<40;
            }
            return Mathf.Abs(position.x)<350&&Mathf.Abs(position.z)<240&&position.y> -5&&position.y<160;
        }
        static bool Finite(float x)=>!float.IsNaN(x)&&!float.IsInfinity(x);
    }
    public static class ExplorationSave
    {
        public static string PathName(int slot)
        {
            string name=SceneManager.GetActiveScene().name;
            foreach(char c in Path.GetInvalidFileNameChars())name=name.Replace(c,'_');
            return Blackstone.Save.CheckpointStorage.SlotPath(Application.persistentDataPath,name+".exploration.json",slot);
        }
        public static bool TryLoad(int slot,out ExplorationCheckpoint checkpoint)
        {
            ExplorationCheckpoint loaded=null;
            bool found=Blackstone.Save.CheckpointStorage.TryRead(PathName(slot),json=>
            {
                var candidate=JsonUtility.FromJson<ExplorationCheckpoint>(json);
                if(candidate==null||!candidate.Valid())return false;
                loaded=candidate;return true;
            },out var contents);
            checkpoint=found?loaded:null;return found;
        }
        public static bool Write(int slot,ExplorationCheckpoint checkpoint)
        {
            if(checkpoint==null||!checkpoint.Valid())return false;
            checkpoint.savedUtc=DateTime.UtcNow.ToString("o");
            return Blackstone.Save.CheckpointStorage.Write(PathName(slot),JsonUtility.ToJson(checkpoint,true));
        }
    }
}
