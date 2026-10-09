using UnityEngine;
using DesertShift.Interaction;
using Blackstone.Story;

namespace Blackstone.Interaction
{
    public enum StoryTarget
    {
        CellDoor, Reader, Cook, Fixer, DroppedKnife, Niko, Leader, Tattooist,
        CellStash, Phone, Rival, SolitaryBed, SolitaryDoor, Brother, Reflection, Training
    }
    public sealed class StoryInteractable : MonoBehaviour, IInteractable
    {
        public PrisonStoryDirector director;
        public StoryTarget target;
        public Vector3 promptOffset = Vector3.up;
        public string Prompt => director != null ? director.PromptFor(target) : null;
        public void Interact(PlayerInteractor user)
        { if (director != null) director.Interact(target); }
    }
}
