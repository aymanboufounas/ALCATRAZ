using UnityEngine;
using DesertShift.Player;

namespace DesertShift.Interaction
{
    [RequireComponent(typeof(PlayerInputHandler))]
    public sealed class PlayerInteractor : MonoBehaviour
    {
        public float reach = 2.2f;
        public LayerMask layers = ~(1 << 8);
        public string CurrentPrompt { get; private set; }
        public string Notice { get; private set; }
        float noticeUntil;
        PlayerInputHandler input;
        IInteractable current;
        void Awake() { input = GetComponent<PlayerInputHandler>(); }
        void Update()
        {
            current = null; CurrentPrompt = null;
            if (Time.unscaledTime > noticeUntil) Notice = null;
            if (!input.CanControl) return;
            var cam = UnityEngine.Camera.main; if (cam == null) return;
            var ray = new Ray(cam.transform.position, cam.transform.forward);
            if (Physics.SphereCast(ray, .075f, out var hit, 7f, layers, QueryTriggerInteraction.Ignore)
                && Vector3.Distance(transform.position + Vector3.up, hit.point) <= reach)
            {
                // The first physical hit gates interaction: closed walls cannot be reached through.
                current = hit.collider.GetComponentInParent<IInteractable>();
                if (current != null && !string.IsNullOrEmpty(current.Prompt))
                    CurrentPrompt = "[E / X] " + current.Prompt;
                else current = null;
            }
            // Nearby story targets are forgiving to aim at, but still require physical line of sight.
            if (current == null)
            {
                float nearest = reach;
                foreach (var hitCollider in Physics.OverlapSphere(transform.position + Vector3.up, reach, layers, QueryTriggerInteraction.Ignore))
                {
                    var target = hitCollider.GetComponentInParent<IInteractable>();
                    var story = target as Blackstone.Interaction.StoryInteractable;
                    var poker = target as Blackstone.Activities.PrisonPokerTable;
                    var table = target as Blackstone.Activities.PrisonConversationTable;
                    if (story == null && poker == null && table == null) continue;
                    if (target == null || string.IsNullOrEmpty(target.Prompt)) continue;
                    var component = target as Component;
                    Vector3 point = component.transform.position + (story != null ? story.promptOffset : Vector3.up*.8f);
                    Vector3 from = transform.position + Vector3.up * 1.2f;
                    float d = Vector3.Distance(from, point);
                    if (d >= nearest || Vector3.Dot(cam.transform.forward, (point-from).normalized) < -.1f) continue;
                    if (Physics.Linecast(from, point, out var blocker, layers, QueryTriggerInteraction.Ignore)
                        && blocker.collider.GetComponentInParent<IInteractable>() != target) continue;
                    nearest = d; current = target; CurrentPrompt = "[E / X] " + target.Prompt;
                }
            }
            if (current != null && input.InteractPressed) current.Interact(this);
        }
        public void ShowNotice(string text) { Notice = text; noticeUntil = Time.unscaledTime + 2.5f; }
    }
}
