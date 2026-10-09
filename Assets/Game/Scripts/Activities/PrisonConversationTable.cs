using UnityEngine;
using DesertShift.Interaction;
using Blackstone.Story;
namespace Blackstone.Activities
{
    public sealed class PrisonConversationTable:MonoBehaviour,IInteractable
    {
        public PrisonStoryDirector director;
        public Transform playerSeat;
        public string Prompt=>director!=null&&director.CanUseYardActivity?"Sit and talk — yard stories":"";
        public void Interact(PlayerInteractor player)
        {if(!string.IsNullOrEmpty(Prompt))director.YardConversation(playerSeat);}
    }
}
