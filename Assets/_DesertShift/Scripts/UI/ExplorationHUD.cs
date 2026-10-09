using UnityEngine;
using UnityEngine.SceneManagement;
using DesertShift.Player;
using DesertShift.Interaction;
namespace DesertShift.UI
{
    public sealed class ExplorationHUD : MonoBehaviour
    {
        public PlayerMovement player;
        public PlayerInputHandler input;
        public PlayerInteractor interactor;
        bool debug;
        float smoothedFrameTime = .016f;
        GUIStyle prompt, tiny, status;
        void Update()
        {
            if (input != null && input.DebugPressed) debug = !debug;
            smoothedFrameTime = Mathf.Lerp(smoothedFrameTime, Time.unscaledDeltaTime, .08f);
        }
        void OnGUI()
        {
            if (player == null || input == null) return;
            if (prompt == null)
            {
                prompt = new GUIStyle(GUI.skin.label) { fontSize = 18, alignment = TextAnchor.MiddleCenter };
                prompt.normal.textColor = new Color(.97f, .91f, .77f);
                tiny = new GUIStyle(prompt) { fontSize = 14 };
                status = new GUIStyle(GUI.skin.box) { fontSize = 14, alignment = TextAnchor.UpperLeft };
                status.normal.textColor = Color.white;
            }
            float w = Screen.width, h = Screen.height;
            if (input.IsCaptured)
            {
                GUI.Label(new Rect(w / 2 - 5, h / 2 - 7, 10, 16), "·", tiny);
                if (interactor != null && !string.IsNullOrEmpty(interactor.CurrentPrompt))
                    GUI.Label(new Rect(w / 2 - 240, h * .80f, 480, 38), interactor.CurrentPrompt, prompt);
                if (interactor != null && !string.IsNullOrEmpty(interactor.Notice))
                    GUI.Label(new Rect(w / 2 - 300, h * .86f, 600, 35), interactor.Notice, tiny);
            }
            else GUI.Label(new Rect(w / 2 - 260, h / 2 - 25, 520, 50), "PAUSED  ·  Esc or click to resume", prompt);
            if (debug)
                GUI.Box(new Rect(14, 14, 310, 136),
                    $"DESERT SHIFT  /  F3\nFPS: {1f / Mathf.Max(smoothedFrameTime, .001f):0}\n" +
                    $"Position: {player.transform.position:F1}\nSpeed: {player.Speed:F2} m/s\n" +
                    $"Grounded: {player.Grounded}\nScene: {SceneManager.GetActiveScene().name}", status);
        }
    }
}
