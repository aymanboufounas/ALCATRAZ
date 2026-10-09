using UnityEngine;

namespace DesertShift.Interaction
{
    public sealed class LightSwitch : MonoBehaviour, IInteractable
    {
        public Light[] controlledLights;
        public string switchName = "bay lights";
        bool on = true;
        public string Prompt => (on ? "Switch off " : "Switch on ") + switchName;
        public void Interact(PlayerInteractor player)
        {
            on = !on;
            foreach (var lightSource in controlledLights)
                if (lightSource != null) lightSource.enabled = on;
        }
    }
}
