using UnityEngine;
namespace DesertShift.Player
{
    [DefaultExecutionOrder(0)]
    public sealed class PlayerAnimator : MonoBehaviour
    {
        public PlayerMovement movement;
        public Animator animator;
        static readonly int Speed = Animator.StringToHash("Speed");
        static readonly int MoveX = Animator.StringToHash("MoveX");
        static readonly int MoveY = Animator.StringToHash("MoveY");
        static readonly int Crouch = Animator.StringToHash("Crouch");
        static readonly int Grounded = Animator.StringToHash("Grounded");
        static readonly int Vertical = Animator.StringToHash("VerticalSpeed");
        static readonly int Turn = Animator.StringToHash("Turn");
        void Update()
        {
            if (movement == null || animator == null || Time.deltaTime <= 0) return;
            animator.SetFloat(Speed, movement.Speed, .12f, Time.deltaTime);
            animator.SetFloat(MoveX, movement.LocalMotion.x, .10f, Time.deltaTime);
            animator.SetFloat(MoveY, movement.LocalMotion.y, .10f, Time.deltaTime);
            animator.SetBool(Crouch, movement.IsCrouching);
            animator.SetBool(Grounded, movement.Grounded);
            animator.SetFloat(Vertical, movement.VerticalSpeed);
            animator.SetFloat(Turn, movement.TurnRate, .1f, Time.deltaTime);
            if (movement.JumpedThisFrame) animator.SetTrigger("Jump");
            if (movement.LandedThisFrame) animator.SetTrigger("Land");
        }
    }
}
