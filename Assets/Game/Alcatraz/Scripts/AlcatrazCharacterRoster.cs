using System;
using UnityEngine;

namespace Blackstone.Alcatraz
{
    [Serializable]
    public sealed class AlcatrazCharacterProfile
    {
        public string actorName, model, role;
        public float height = 1.78f, build = 1, walkSpeed = 1.05f, idlePhase;
        public bool ambient;
        public Vector3 position;
        public float yaw;
        public Vector3[] route;
    }

    [Serializable]
    public sealed class AlcatrazCharacterRoster
    {
        public AlcatrazCharacterProfile[] actors;

        public static AlcatrazCharacterRoster Load()
        {
            var asset = Resources.Load<TextAsset>("Alcatraz/CharacterRoster");
            if (asset == null) return null;
            try { return JsonUtility.FromJson<AlcatrazCharacterRoster>(asset.text); }
            catch (Exception error)
            { Debug.LogError("Alcatraz character roster could not load: " + error.Message); return null; }
        }

        public AlcatrazCharacterProfile Find(string actorName)
        {
            if (actors != null)
                foreach (var profile in actors)
                    if (profile.actorName == actorName) return profile;
            return null;
        }
    }
}
