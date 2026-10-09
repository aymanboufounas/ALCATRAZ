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
    }
    public static class PrisonSave
    {
        static bool Alcatraz => SceneManager.GetActiveScene().name.StartsWith("SC_Alcatraz", StringComparison.Ordinal);
        public static string PathName => Path.Combine(Application.persistentDataPath,
            Alcatraz ? Blackstone.Alcatraz.AlcatrazMap.CheckpointFile : "blackstone-chapter01.json");
        public static bool Exists => File.Exists(PathName) || File.Exists(PathName + ".bak");
        public static bool TryLoad(out PrisonCheckpoint checkpoint)
        {
            foreach (string path in new[] { PathName, PathName + ".bak" })
            {
                try
                {
                    if (!File.Exists(path)) continue;
                    var candidate = JsonUtility.FromJson<PrisonCheckpoint>(File.ReadAllText(path));
                    if (candidate == null || candidate.story == null || !candidate.story.IsValid()) continue;
                    Vector3 p = candidate.position;
                    bool outside = Alcatraz ? p.x < -130 || p.x > 135 || p.z < -190 || p.z > 190 || p.y < 1.2f || p.y > 68
                        : p.x < -50 || p.x > 50 || p.z < -45 || p.z > 55 || p.y < -.2f || p.y > 6;
                    if (!Finite(p.x) || !Finite(p.y) || !Finite(p.z) || !Finite(candidate.yaw) || outside) continue;
                    checkpoint = candidate; return true;
                }
                catch (Exception e) when (e is IOException || e is ArgumentException || e is UnauthorizedAccessException)
                { Debug.LogWarning("Blackstone could not read a checkpoint; trying the backup."); }
            }
            checkpoint = null; return false;
        }
        public static bool Write(PrisonCheckpoint checkpoint)
        {
            if (checkpoint == null || checkpoint.story == null || !checkpoint.story.IsValid()) return false;
            try
            {
                Directory.CreateDirectory(Application.persistentDataPath);
                string temp = PathName + ".tmp";
                File.WriteAllText(temp, JsonUtility.ToJson(checkpoint, true));
                if (File.Exists(PathName)) File.Replace(temp, PathName, PathName + ".bak");
                else File.Move(temp, PathName);
                return true;
            }
            catch (Exception e) when (e is IOException || e is UnauthorizedAccessException)
            { Debug.LogWarning("Checkpoint could not be saved: " + e.Message); return false; }
        }
        static bool Finite(float x) => !float.IsNaN(x) && !float.IsInfinity(x);
    }
}
