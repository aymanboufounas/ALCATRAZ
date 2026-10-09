using UnityEngine;

namespace DesertShift.Interaction
{
    public sealed class DoorController : MonoBehaviour, IInteractable
    {
        public Transform hinge;
        public BoxCollider leaf;
        public string doorName = "door";
        public bool locked;
        public float openAngle = 105f;
        public float degreesPerSecond = 120f;
        public bool OpensPositiveByDefault = true;
        public string Prompt => locked ? "Check locked " + doorName : (isOpen ? "Close " : "Open ") + doorName;
        public bool IsOpen => isOpen;
        Quaternion closed;
        float angle, target;
        bool isOpen;
        readonly Collider[] occupants = new Collider[12];
        void Awake()
        {
            if (hinge == null) hinge = transform;
            closed = hinge.localRotation;
        }
        public void Interact(PlayerInteractor player)
        {
            if (locked) { player.ShowNotice("Locked from the service side."); return; }
            isOpen = !isOpen;
            if (isOpen)
            {
                // A leaf extends along local +X; positive Y rotates it toward local -Z.
                Quaternion closedWorld = hinge.parent != null ? hinge.parent.rotation * closed : closed;
                float side = Vector3.Dot(player.transform.position - hinge.position, closedWorld * Vector3.forward);
                float sign = Mathf.Abs(side) < .05f ? (OpensPositiveByDefault ? 1 : -1) : Mathf.Sign(side);
                target = openAngle * sign;
            }
            else target = 0;
        }
        public void SetLocked(bool value) { locked = value; }
        void Update()
        {
            if (Mathf.Abs(angle - target) < .02f || Time.deltaTime <= 0) return;
            // Small swept increments prevent a fast frame from rotating through a person.
            float remaining = degreesPerSecond * Time.deltaTime;
            while (remaining > 0)
            {
                float step = Mathf.Min(remaining, 2f);
                float next = Mathf.MoveTowards(angle, target, step);
                Quaternion rotation = closed * Quaternion.Euler(0, next, 0);
                if (leaf != null)
                {
                    Quaternion world = hinge.parent != null ? hinge.parent.rotation * rotation : rotation;
                    Vector3 offset = hinge.InverseTransformPoint(leaf.transform.TransformPoint(leaf.center));
                    Vector3 worldCenter = hinge.position + world * Vector3.Scale(offset, hinge.lossyScale);
                    Vector3 extents = Vector3.Scale(leaf.size, leaf.transform.lossyScale) * .5f + Vector3.one * .025f;
                    if (Physics.OverlapBoxNonAlloc(worldCenter, extents, occupants, world,
                        1 << 8, QueryTriggerInteraction.Ignore) > 0) return;
                }
                angle = next; hinge.localRotation = rotation; remaining -= step;
                if (Mathf.Abs(angle - target) < .02f) break;
            }
        }
    }
}
