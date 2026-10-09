using UnityEngine;
using UnityEngine.InputSystem;

namespace DesertShift.Player
{
    [DefaultExecutionOrder(-200), DisallowMultipleComponent]
    public sealed class PlayerInputHandler : MonoBehaviour
    {
        public Vector2 Move => CanControl ? move.ReadValue<Vector2>() : Vector2.zero;
        public Vector2 Look => CanControl ? mouseLook.ReadValue<Vector2>() +
            padLook.ReadValue<Vector2>() * (220f * Time.deltaTime / .105f) : Vector2.zero;
        public bool Sprint => CanControl && sprint.IsPressed();
        public bool Crouch => CanControl && crouch.IsPressed();
        public bool Aim => CanControl && aim.IsPressed();
        public bool Walk => CanControl && walk.IsPressed();
        public bool JumpPressed => CanControl && jump.WasPressedThisFrame();
        public bool DialogueAdvancePressed => IsCaptured && jump.WasPressedThisFrame();
        public bool InteractPressed => CanControl && interact.WasPressedThisFrame();
        public bool AttackPressed => CanControl && attack.WasPressedThisFrame();
        public bool FlashlightPressed => CanControl && flashlight.WasPressedThisFrame();
        public bool PhonePressed => IsCaptured && phone.WasPressedThisFrame();
        public bool RetryPressed => retry.WasPressedThisFrame();
        public bool ConfirmPressed => interact.WasPressedThisFrame();
        public bool ShoulderPressed => CanControl && shoulder.WasPressedThisFrame();
        public bool DebugPressed => debug.WasPressedThisFrame();
        public bool IsCaptured { get; private set; }
        public bool GameplayBlocked { get; private set; }
        public bool CanControl => IsCaptured && !GameplayBlocked;
        public bool PauseEnabled { get; set; } = true;
        public bool ResumeOnClick { get; set; } = true;
        InputActionMap actions;
        InputAction move, mouseLook, padLook, sprint, crouch, jump, interact, flashlight, pause,
            debug, attack, phone, retry, aim, walk, shoulder;

        void Awake()
        {
            actions = new InputActionMap("DesertShift");
            move = actions.AddAction("Move", InputActionType.Value);
            move.AddCompositeBinding("2DVector").With("Up", "<Keyboard>/w")
                .With("Down", "<Keyboard>/s").With("Left", "<Keyboard>/a").With("Right", "<Keyboard>/d");
            move.AddBinding("<Gamepad>/leftStick").WithProcessor("stickDeadzone(min=0.18,max=0.95)");
            mouseLook = actions.AddAction("MouseLook", InputActionType.Value, "<Mouse>/delta");
            padLook = actions.AddAction("PadLook", InputActionType.Value);
            padLook.AddBinding("<Gamepad>/rightStick").WithProcessor("stickDeadzone(min=0.16,max=0.95)");
            sprint = actions.AddAction("Sprint", InputActionType.Button, "<Keyboard>/leftShift");
            crouch = actions.AddAction("Crouch", InputActionType.Button, "<Keyboard>/leftCtrl");
            jump = actions.AddAction("Jump", InputActionType.Button, "<Keyboard>/space");
            interact = actions.AddAction("Interact", InputActionType.Button, "<Keyboard>/e");
            flashlight = actions.AddAction("Flashlight", InputActionType.Button, "<Keyboard>/f");
            pause = actions.AddAction("Pause", InputActionType.Button, "<Keyboard>/escape");
            debug = actions.AddAction("Debug", InputActionType.Button, "<Keyboard>/f3");
            attack = actions.AddAction("Attack", InputActionType.Button, "<Mouse>/leftButton");
            phone = actions.AddAction("Phone", InputActionType.Button, "<Keyboard>/p");
            retry = actions.AddAction("Retry", InputActionType.Button, "<Keyboard>/r");
            aim = actions.AddAction("Aim", InputActionType.Button, "<Mouse>/rightButton");
            walk = actions.AddAction("Walk", InputActionType.Button, "<Keyboard>/leftAlt");
            shoulder = actions.AddAction("Shoulder", InputActionType.Button, "<Keyboard>/q");
            sprint.AddBinding("<Gamepad>/leftStickPress"); crouch.AddBinding("<Gamepad>/buttonEast");
            jump.AddBinding("<Gamepad>/buttonSouth"); interact.AddBinding("<Gamepad>/buttonWest");
            flashlight.AddBinding("<Gamepad>/dpad/up"); pause.AddBinding("<Gamepad>/start");
            attack.AddBinding("<Gamepad>/rightTrigger"); phone.AddBinding("<Gamepad>/dpad/right");
            retry.AddBinding("<Gamepad>/buttonNorth"); aim.AddBinding("<Gamepad>/leftTrigger");
            shoulder.AddBinding("<Gamepad>/rightShoulder");
        }
        void OnEnable() { actions.Enable(); Capture(true); }
        void OnDisable() { actions.Disable(); Capture(false); }
        void OnDestroy() { actions.Dispose(); Time.timeScale = 1f; }
        void Update()
        {
            if (PauseEnabled && pause.WasPressedThisFrame()) Capture(!IsCaptured);
            if (ResumeOnClick && !IsCaptured && Mouse.current != null && Mouse.current.leftButton.wasPressedThisFrame
                && Application.isFocused) Capture(true);
        }
        void OnApplicationFocus(bool focus) { if (!focus) Capture(false); }
        public void Capture(bool captured)
        {
            IsCaptured = captured;
            Cursor.lockState = captured ? CursorLockMode.Locked : CursorLockMode.None;
            Cursor.visible = !captured;
            Time.timeScale = captured ? 1f : 0f;
        }
        public void SetGameplayBlocked(bool blocked) { GameplayBlocked = blocked; }
    }
}
