namespace DesertShift.Interaction
{
    public interface IInteractable
    {
        string Prompt { get; }
        void Interact(PlayerInteractor player);
    }
}
