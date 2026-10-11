using UnityEngine;
namespace Blackstone.Foundation
{
    [RequireComponent(typeof(Rigidbody))]
    public sealed class FoundationPunchingBag : MonoBehaviour
    {
        public void Hit(Vector3 impulse,Vector3 point){GetComponent<Rigidbody>().AddForceAtPosition(impulse,point,ForceMode.Impulse);}
    }
}
