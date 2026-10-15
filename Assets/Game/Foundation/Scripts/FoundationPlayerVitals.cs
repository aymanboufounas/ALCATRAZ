using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.InputSystem;
using DesertShift.Player;
using Blackstone.Story;

namespace Blackstone.Foundation
{
    [DefaultExecutionOrder(30), DisallowMultipleComponent]
    public sealed class FoundationPlayerVitals : MonoBehaviour
    {
        readonly PlayerFailureRules failure = new PlayerFailureRules();
        static string pendingRestart;
        FoundationBootstrap foundation;
        PrisonStoryDirector story;
        PlayerMovement movement;
        PlayerInputHandler input;
        FoundationDamageable damageable;
        FoundationSwimming swimming;
        bool restarting;
        string restartError;
        GUIStyle label, title, centered;
        public bool Failed => failure.Failed;
        public bool ActiveSession => story != null && story.enabled ? !story.MainMenu
            : foundation != null && foundation.GetComponent<FoundationHUD>() != null && !foundation.GetComponent<FoundationHUD>().TitleVisible;
        public bool CanTakeDamage => !Failed && ActiveSession && input != null && input.CanControl
            && movement != null && !movement.ExternalControl;
        public void Configure(FoundationBootstrap owner, PrisonStoryDirector director)
        {
            foundation = owner; story = director;
            movement = GetComponent<PlayerMovement>(); input = GetComponent<PlayerInputHandler>();
            damageable = GetComponent<FoundationDamageable>(); swimming = GetComponent<FoundationSwimming>();
        }
        public static bool ConsumeRestart(string scene)
        {
            if (pendingRestart != scene) return false;
            pendingRestart = null; return true;
        }
        public void Die(Vector3 impulse)
        {
            if (!BeginFailure(PlayerFailureReason.Dead)) return;
            var fall = GetComponent<FoundationFall>();
            if (fall != null) { fall.StayDown = true; fall.KnockDown(impulse); }
        }
        public bool BeginFailure(PlayerFailureReason reason)
        {
            if (!ActiveSession || !failure.Fail(reason)) return false;
            if (Blackstone.Activities.PrisonPokerTable.Active != null) Blackstone.Activities.PrisonPokerTable.Active.Close();
            var boxer = GetComponent<FoundationBoxing>(); if (boxer != null) boxer.StopCombat();
            if (input != null) { input.SetGameplayBlocked(true); input.Capture(true); }
            return true;
        }
        void Update()
        {
            if (!ActiveSession || input == null) return;
            if (!Failed && swimming != null && swimming.RestrictedWater)
                BeginFailure(PlayerFailureReason.RestrictedWater);
            if (!Failed && CanTakeDamage && movement.LandedThisFrame && !movement.IsSwimming)
                damageable.Damage(PlayerFailureRules.FallDamage(movement.LandingSpeed), transform.position, -Vector3.up * 3);
            if (!Failed) return;
            // Story scripts cannot reopen control during the failure screen.
            input.SetGameplayBlocked(true);
            failure.Tick(Time.deltaTime);
            if (!failure.ReadyToRestart || restarting) return;
            restarting = true;
            string scene = SceneManager.GetActiveScene().name;
            pendingRestart = scene;
            try { SceneManager.LoadScene(scene); }
            catch (System.Exception error)
            {
                pendingRestart = null;
                restartError = "Reload failed. Retry to restart the mission.";
                input.Capture(false);
                Debug.LogError(restartError + " " + error.Message);
            }
        }
        void OnGUI()
        {
            if (!ActiveSession || damageable == null) return;
            if (label == null)
            {
                label = new GUIStyle(GUI.skin.label) { fontSize = 19, alignment = TextAnchor.MiddleLeft, wordWrap = true };
                label.normal.textColor = Color.white;
                centered = new GUIStyle(label) { alignment = TextAnchor.MiddleCenter };
                title = new GUIStyle(centered) { fontSize = 78, fontStyle = FontStyle.Bold };
            }
            var old = GUI.matrix; int depth = GUI.depth; var color = GUI.color;
            GUI.depth = -100; GUI.color = Color.white;
            var viewport = new FoundationViewport(Screen.width, Screen.height); GUI.matrix = viewport.Matrix;
            try
            {
                if (Failed) { FailureScreen(viewport); return; }
                if (input == null || !input.IsCaptured || story != null && (story.Letterbox || story.PhoneOpen)
                    || Blackstone.Activities.PrisonPokerTable.Active != null) return;
                bool inventory=foundation!=null&&foundation.PlayerEquipment!=null
                    &&(Keyboard.current!=null&&Keyboard.current.tabKey.isPressed||Gamepad.current!=null&&Gamepad.current.leftShoulder.isPressed);
                if(inventory)return;
                float x = viewport.Width - 341, y = story != null ? 230 : 108;
                Panel(new Rect(x,y,316,62),new Color(.015f,.03f,.035f,.9f));
                GUI.Label(new Rect(x+15,y+5,286,30),"HEALTH  " + Mathf.CeilToInt(damageable.Health) + "%",label);
                Panel(new Rect(x+15,y+41,286,7),new Color(1,1,1,.16f));
                Panel(new Rect(x+15,y+41,286*damageable.Health/100,7),damageable.Health>40?new Color(.35f,.85f,.48f):new Color(1,.32f,.24f));
                if (swimming != null && movement.IsSwimming)
                {
                    GUI.Label(new Rect(viewport.Width/2-330,viewport.Height-66,660,32),"SWIMMING  ·  WASD / Left stick  ·  Shift / L3 faster  ·  Space / A climb ashore",centered);
                }
                if (swimming != null && swimming.NearRestrictedWater)
                {
                    Panel(new Rect(viewport.Width/2-370,165,740,52),new Color(.18f,.055f,.025f,.95f));
                    GUI.Label(new Rect(viewport.Width/2-355,173,710,38),"RESTRICTED WATERS AHEAD — turn back toward the island",centered);
                }
            }
            finally { GUI.matrix = old; GUI.depth = depth; GUI.color = color; }
        }
        void FailureScreen(FoundationViewport viewport)
        {
            float cx = viewport.Width/2, cy = viewport.Height/2;
            Panel(new Rect(0,0,viewport.Width,viewport.Height),new Color(.015f,.02f,.025f,.94f));
            GUI.Label(new Rect(cx-500,cy-140,1000,110),failure.Reason==PlayerFailureReason.Dead?"DEAD":"WANTED",title);
            GUI.Label(new Rect(cx-470,cy-25,940,72),failure.Reason==PlayerFailureReason.Dead
                ? "HEALTH 0%\nRestarting the mission from the latest checkpoint."
                : "You crossed the restricted water boundary.\nRestarting the mission from the latest checkpoint.",centered);
            if (restartError != null)
            {
                GUI.Label(new Rect(cx-400,cy+68,800,40),restartError,centered);
                if (GUI.Button(new Rect(cx-160,cy+115,320,50),"Retry mission restart")) { restarting=false; restartError=null; }
            }
            else if (!input.IsCaptured)
            {
                if (GUI.Button(new Rect(cx-160,cy+100,320,50),"Resume restart countdown")) input.Capture(true);
            }
            else GUI.Label(new Rect(cx-250,cy+80,500,42),"RESTARTING IN " + Mathf.CeilToInt(failure.Remaining) + "…",centered);
        }
        static void Panel(Rect rect,Color color)
        {var old=GUI.color;GUI.color=color;GUI.DrawTexture(rect,Texture2D.whiteTexture);GUI.color=old;}
    }
}
