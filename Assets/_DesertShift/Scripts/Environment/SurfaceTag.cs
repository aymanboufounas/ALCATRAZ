using UnityEngine;
namespace DesertShift.Environment
{
    public enum SurfaceKind { Sand, Concrete, Metal, Wood, WetConcrete, Asphalt }
    public sealed class SurfaceTag : MonoBehaviour { public SurfaceKind surface; }
}
