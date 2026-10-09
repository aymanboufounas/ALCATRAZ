using UnityEngine;
using DesertShift.Interaction;
namespace DesertShift.Environment
{
    public sealed class RVController : MonoBehaviour
    {
        public DoorController sideDoor;
        public string vehicleName = "Sundowner 84";
        public bool IsAccessible => sideDoor != null && !sideDoor.locked;
    }
}
