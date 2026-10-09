using System;
using UnityEngine;
using DesertShift.Interaction;
using Blackstone.Story;
using Blackstone.Actors;

namespace Blackstone.Activities
{
    public sealed class PrisonPokerTable : MonoBehaviour, IInteractable
    {
        public PrisonStoryDirector director;
        public PrisonActor[] players;
        public Transform playerSeat;
        Vector3 previousPosition;
        Quaternion previousRotation;
        public Vector3 ReturnPosition=>previousPosition;
        public Quaternion ReturnRotation=>previousRotation;
        float openedAt;
        public static PrisonPokerTable Active { get; private set; }
        public string Prompt => director != null && director.CanUseYardActivity ? "Sit down — five-card draw" : "";
        int[] deck, hand=new int[5], opponent=new int[5];
        bool[] keep=new bool[5];
        int dealt, selected, wins, hands;
        bool revealed;
        string result;
        readonly System.Random random=new System.Random();
        Texture2D[] cards=new Texture2D[52];
        Texture2D back;
        GUIStyle label, heading, button;
        public void Interact(PlayerInteractor player)
        {
            if (string.IsNullOrEmpty(Prompt)) return;
            Active=this;openedAt=Time.time; director.input.SetGameplayBlocked(true);
            previousPosition=director.player.transform.position;previousRotation=director.player.transform.rotation;
            if(playerSeat!=null){director.player.Teleport(playerSeat.position);director.player.transform.rotation=playerSeat.rotation;}
            director.playerActor.SetPose(ActorPose.Cards);
            Cursor.lockState=CursorLockMode.None;Cursor.visible=true;
            if (players != null) foreach(var p in players) if(p!=null) p.SpeakTo(director.player.transform,false);
            for(int i=0;i<52;i++) cards[i]=Resources.Load<Texture2D>("Blackstone/Cards/card_"+i.ToString("00"));
            back=Resources.Load<Texture2D>("Blackstone/Cards/back");
            Deal(); director.audioBus.Play(director.audioBus.cardShuffle);
            director.audioBus.Speak("poker_welcome_01");
        }
        void Deal()
        {
            deck=PrisonPokerRules.Deck(random);dealt=0;revealed=false;selected=0;
            for(int i=0;i<5;i++) { hand[i]=deck[dealt++];opponent[i]=deck[dealt++];keep[i]=false; }
            result="Choose the cards to KEEP, then draw once.";
        }
        void Draw()
        {
            if(revealed)return;
            for(int i=0;i<5;i++)if(!keep[i])hand[i]=deck[dealt++];
            // Opponent keeps pairs or better; a single draw from the same deck.
            var value=PrisonPokerRules.Evaluate(opponent);
            if(value.score<4*759375L)
            {
                int[] counts=new int[15];foreach(int c in opponent)counts[c%13+2]++;
                for(int i=0;i<5;i++)if(counts[opponent[i]%13+2]<2)opponent[i]=deck[dealt++];
            }
            var player=PrisonPokerRules.Evaluate(hand);var other=PrisonPokerRules.Evaluate(opponent);
            if(player.score>other.score)wins++;
            hands++;revealed=true;
            result=(player.score>other.score?"You win the hand.":player.score<other.score?"Samir wins the hand.":"Split hand.")+"  "+player.name+" / "+other.name;
            director.audioBus.Play(director.audioBus.cardDeal);
        }
        public void Close()
        {
            if(Active!=this)return;
            Active=null;director.audioBus.StopDialogue();
            director.playerActor.SetPose(ActorPose.Idle);
            director.player.Teleport(previousPosition);director.player.transform.rotation=previousRotation;
            Cursor.lockState=director.input.IsCaptured?CursorLockMode.Locked:CursorLockMode.None;
            Cursor.visible=!director.input.IsCaptured;
            director.input.SetGameplayBlocked(director.Busy||director.PhoneOpen);
            if(players!=null)foreach(var p in players)if(p!=null)p.SpeakTo(null,false);
        }
        void Update()
        {
            if(Active!=this)return;
            if(director.Busy||!director.CanUseYardActivity){Close();return;}
            if(!director.input.IsCaptured||Time.time<openedAt+.2f)return;
            Cursor.lockState=CursorLockMode.None;Cursor.visible=true;
            if(UnityEngine.InputSystem.Keyboard.current!=null&&UnityEngine.InputSystem.Keyboard.current.pKey.wasPressedThisFrame){Close();return;}
            // Controller: D-pad selects, X keeps, Y draws/deals, B leaves.
            var pad=UnityEngine.InputSystem.Gamepad.current;
            if(pad!=null)
            {
                if(pad.buttonEast.wasPressedThisFrame){Close();return;}
                if(pad.dpad.left.wasPressedThisFrame)selected=(selected+4)%5;
                if(pad.dpad.right.wasPressedThisFrame)selected=(selected+1)%5;
            }
            if(director.input.ConfirmPressed&&!revealed)keep[selected]=!keep[selected];
            if(director.input.RetryPressed){if(revealed)Deal();else Draw();}
        }
        void OnGUI()
        {
            if(Active!=this||!director.input.IsCaptured)return;
            if(label==null)
            {
                label=new GUIStyle(GUI.skin.label){fontSize=22,alignment=TextAnchor.MiddleCenter,wordWrap=true};
                heading=new GUIStyle(label){fontSize=36,fontStyle=FontStyle.Bold};
                button=new GUIStyle(GUI.skin.button){fontSize=21};
            }
            var matrix=GUI.matrix;GUI.matrix=Matrix4x4.TRS(Vector3.zero,Quaternion.identity,new Vector3(Screen.width/1920f,Screen.height/1080f,1));
            Panel(new Rect(0,0,1920,1080),new Color(.012f,.022f,.027f,.91f));
            Panel(new Rect(370,100,1180,865),new Color(.04f,.16f,.13f,1));
            GUI.Label(new Rect(420,117,1080,70),"YARD TABLE  /  FIVE-CARD DRAW",heading);
            GUI.Label(new Rect(450,199,1020,45),"Friendly game · wins "+wins+" / "+hands+" · mission progress stays intact",label);
            for(int i=0;i<5;i++)Card(new Rect(567+i*166,270,140,194),revealed?cards[opponent[i]]:back,opponent[i]);
            GUI.Label(new Rect(430,471,1060,60),result,label);
            for(int i=0;i<5;i++)
            {
                Rect rect=new Rect(567+i*166,550,140,194);
                if(keep[i]||selected==i)Panel(new Rect(rect.x-5,rect.y-5,rect.width+10,rect.height+10),keep[i]?new Color(.89f,.69f,.3f):new Color(.65f,.75f,.73f));
                Card(rect,cards[hand[i]],hand[i]);
                if(!revealed&&GUI.Button(rect,"",GUIStyle.none)){keep[i]=!keep[i];selected=i;director.audioBus.Play(director.audioBus.cardDeal,.3f);}
                GUI.Label(new Rect(rect.x,rect.y+194,rect.width,38),keep[i]?"KEEP":"DRAW",label);
            }
            if(GUI.Button(new Rect(615,807,360,60),revealed?"Deal again  [R / Y]":"Draw & reveal  [R / Y]",button)){if(revealed)Deal();else Draw();}
            if(GUI.Button(new Rect(1000,807,315,60),"Leave table  [P / B]",button))Close();
            GUI.Label(new Rect(410,894,1100,36),"Click cards to keep · Controller: D-pad selects, X keeps, Y draws · Esc pauses",label);
            GUI.matrix=matrix;
        }
        void Card(Rect rect,Texture2D texture,int card)
        {
            if(texture!=null)GUI.DrawTexture(rect,texture,ScaleMode.StretchToFill);
            else {Panel(rect,new Color(.88f,.87f,.82f));GUI.Label(rect,PrisonPokerRules.CardName(card),heading);}
        }
        static void Panel(Rect rect,Color color)
        {var old=GUI.color;GUI.color=color;GUI.DrawTexture(rect,Texture2D.whiteTexture);GUI.color=old;}
        void OnDisable(){if(Active==this)Close();}
    }
}
