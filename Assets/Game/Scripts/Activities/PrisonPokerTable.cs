using System;
using UnityEngine;
using UnityEngine.InputSystem;
using DesertShift.Interaction;
using DesertShift.Player;
using Blackstone.Story;
using Blackstone.Actors;
using Blackstone.Foundation;

namespace Blackstone.Activities
{
    public sealed class PrisonPokerTable : MonoBehaviour, IInteractable
    {
        public PrisonStoryDirector director;
        public PrisonActor[] players;
        public Transform playerSeat;
        public Vector3 ReturnPosition=>previousPosition;
        public Quaternion ReturnRotation=>previousRotation;
        public static PrisonPokerTable Active { get; private set; }
        public string Prompt => Active==null&&(director==null||director.CanUseYardActivity)?"Sit down — Texas Hold’em":"";
        PlayerMovement movement;PlayerInputHandler input;FoundationAvatar avatar;FoundationCamera cameraRig;
        Vector3 previousPosition;Quaternion previousRotation;ActorPose previousPose;bool previousBlocked,previousSeated,previousResumeOnClick;
        Vector3 cameraPosition;Quaternion cameraRotation;float cameraFov,openedAt,actAt;int raiseTo;
        HoldemGame game;readonly Texture2D[] cards=new Texture2D[52];Texture2D back;
        Vector3[] opponentPositions;Quaternion[] opponentRotations;ActorPose[] opponentPoses;bool[] opponentSeated,opponentSuspended;
        readonly System.Random random=new System.Random();GUIStyle text,heading,button;
        void Start()
        {
            movement=FindFirstObjectByType<PlayerMovement>();if(movement==null)return;
            input=movement.GetComponent<PlayerInputHandler>();avatar=movement.GetComponent<FoundationAvatar>();cameraRig=FindFirstObjectByType<FoundationCamera>();
            for(int i=0;i<52;i++)cards[i]=Resources.Load<Texture2D>("Blackstone/Cards/card_"+i.ToString("00"));back=Resources.Load<Texture2D>("Blackstone/Cards/back");
        }
        public void Interact(PlayerInteractor player)
        {
            if(string.IsNullOrEmpty(Prompt)||movement==null||movement.ExternalControl||input==null||!input.CanControl)return;
            previousPosition=movement.transform.position;previousRotation=movement.transform.rotation;previousBlocked=input.GameplayBlocked;previousResumeOnClick=input.ResumeOnClick;previousSeated=avatar!=null&&avatar.seated;
            Active=this;openedAt=Time.time;input.SetGameplayBlocked(true);input.ResumeOnClick=false;
            if(playerSeat!=null){movement.Teleport(playerSeat.position);movement.transform.rotation=playerSeat.rotation;}
            movement.SetExternalControl(true);
            if(avatar!=null)avatar.seated=true;
            if(director!=null){previousPose=director.playerActor.pose;director.playerActor.SetPose(ActorPose.Cards);}
            if(players!=null)
            {
                opponentPositions=new Vector3[players.Length];opponentRotations=new Quaternion[players.Length];opponentPoses=new ActorPose[players.Length];opponentSeated=new bool[players.Length];opponentSuspended=new bool[players.Length];
                for(int i=0;i<players.Length;i++)
                {
                    var p=players[i];if(p==null)continue;opponentPositions[i]=p.transform.position;opponentRotations[i]=p.transform.rotation;opponentPoses[i]=p.pose;opponentSuspended[i]=p.Suspended;
                    var a=p.GetComponent<FoundationAvatar>();opponentSeated[i]=a!=null&&a.seated;
                    float angle=(i+1)*Mathf.PI*.5f;Vector3 seat=transform.position+new Vector3(Mathf.Sin(angle)*1.55f,0,-Mathf.Cos(angle)*1.55f);
                    seat.y=movement.transform.position.y;p.transform.position=seat;p.transform.rotation=Quaternion.LookRotation(Vector3.ProjectOnPlane(transform.position-seat,Vector3.up));
                    p.Suspended=true;p.SetPose(ActorPose.Cards);p.SpeakTo(movement.transform,false);if(a!=null)a.seated=true;
                }
            }
            var view=Camera.main;if(view!=null)
            {
                cameraPosition=view.transform.position;cameraRotation=view.transform.rotation;cameraFov=view.fieldOfView;
                if(cameraRig!=null)cameraRig.ActivityCamera=true;
                Vector3 center=transform.position+Vector3.up*.8f;
                view.transform.position=center-movement.transform.forward*2.6f+Vector3.up*1.9f;
                view.transform.LookAt(center);view.fieldOfView=48;
            }
            game=new HoldemGame(random.Next(),new HoldemGame.Seat("Elias",500),new HoldemGame.Seat("Samir",500),new HoldemGame.Seat("Tomas",500),new HoldemGame.Seat("Luis",500));
            Deal();Cursor.lockState=CursorLockMode.None;Cursor.visible=true;
            if(director!=null){director.audioBus.Play(director.audioBus.cardShuffle);director.audioBus.Speak("poker_welcome_01");}
        }
        void Deal(){game.Deal();raiseTo=game.MinRaiseTo;actAt=Time.time+1;}
        void Action(PokerAction action)
        {if(game.Actor!=0)return;if(game.Act(action,raiseTo)){raiseTo=game.MinRaiseTo;actAt=Time.time+1;if(director!=null)director.audioBus.Play(director.audioBus.cardDeal);}}
        public void Close()
        {
            if(Active!=this)return;
            // Settle the hand with the departing player folded (or their committed all-in).
            for(int i=0;i<200&&game.Street!=PokerStreet.Complete;i++)
            {if(game.Actor==0)game.Act(PokerAction.Fold);else{int amount;var action=game.ChooseAI(out amount);game.Act(action,amount);}}
            Active=null;if(director!=null){director.audioBus.StopDialogue();director.playerActor.SetPose(previousPose);}
            if(avatar!=null)avatar.seated=previousSeated;
            movement.Teleport(previousPosition);movement.transform.rotation=previousRotation;movement.SetExternalControl(false);input.SetGameplayBlocked(previousBlocked||director!=null&&(director.Busy||director.PhoneOpen));input.ResumeOnClick=previousResumeOnClick;
            if(players!=null&&opponentPositions!=null)for(int i=0;i<players.Length;i++)
            {var p=players[i];if(p==null)continue;p.transform.SetPositionAndRotation(opponentPositions[i],opponentRotations[i]);p.SetPose(opponentPoses[i]);p.Suspended=opponentSuspended[i];p.SpeakTo(null,false);var a=p.GetComponent<FoundationAvatar>();if(a!=null)a.seated=opponentSeated[i];}
            var view=Camera.main;if(view!=null){view.transform.SetPositionAndRotation(cameraPosition,cameraRotation);view.fieldOfView=cameraFov;}
            if(cameraRig!=null){cameraRig.ActivityCamera=false;cameraRig.SnapToPlayer();}
            Cursor.lockState=input.IsCaptured?CursorLockMode.Locked:CursorLockMode.None;Cursor.visible=!input.IsCaptured;
        }
        void Update()
        {
            if(movement==null||input==null)return;
            if(Active!=this)
            {if(Active==null&&!movement.ExternalControl&&input.InteractPressed&&Vector3.Distance(movement.transform.position,transform.position)<2.6f)Interact(null);return;}
            if(director!=null&&(director.Busy||!director.CanUseYardActivity)){Close();return;}
            if(!input.IsCaptured||Time.deltaTime<=0||Time.time<openedAt+.3f)return;
            Cursor.lockState=CursorLockMode.None;Cursor.visible=true;
            if(Keyboard.current!=null&&Keyboard.current.pKey.wasPressedThisFrame||Gamepad.current!=null&&Gamepad.current.buttonEast.wasPressedThisFrame){Close();return;}
            if(game.Actor>0&&Time.time>actAt){int total;var action=game.ChooseAI(out total);game.Act(action,total);raiseTo=game.MinRaiseTo;actAt=Time.time+.9f;}
            if(game.Actor==0&&Gamepad.current!=null){var pad=Gamepad.current;if(pad.buttonWest.wasPressedThisFrame)Action(PokerAction.CheckCall);if(pad.buttonNorth.wasPressedThisFrame)Action(PokerAction.Fold);}
        }
        void OnDisable(){Close();}
        void OnGUI()
        {
            if(Active!=this||input==null||!input.IsCaptured)return;
            if(text==null){text=new GUIStyle(GUI.skin.label){fontSize=23,alignment=TextAnchor.MiddleCenter,wordWrap=true};text.normal.textColor=PrisonMenuTheme.Paper;heading=new GUIStyle(text){fontSize=33,fontStyle=FontStyle.Bold};button=new GUIStyle(GUI.skin.button){fontSize=23};}
            var matrix=GUI.matrix;GUI.matrix=Matrix4x4.TRS(Vector3.zero,Quaternion.identity,new Vector3(Screen.width/1920f,Screen.height/1080f,1));
            try
            {
                PrisonMenuTheme.Panel(new Rect(0,0,1920,145),new Color(.025f,.033f,.04f,.95f));
                GUI.Label(new Rect(60,25,700,55),"ALCATRAZ  /  TEXAS HOLD’EM",heading);
                GUI.Label(new Rect(60,90,700,40),"Small blind 5  ·  Big blind 10  ·  Friendly table",text);
                GUI.Label(new Rect(1300,25,560,55),game.Street.ToString().ToUpperInvariant()+"   /   POT "+(game.Street==PokerStreet.Complete?game.LastPot:game.Pot),heading);
                for(int i=1;i<4;i++)
                {
                    float x=410+(i-1)*390;var s=game.Seats[i];
                    PrisonMenuTheme.Panel(new Rect(x,168,350,110),new Color(.025f,.04f,.04f,.88f));
                    GUI.Label(new Rect(x,175,350,43),s.Name+(game.Dealer==i?"  [D]":"")+"  ·  "+s.Stack,text);
                    GUI.Label(new Rect(x,221,350,42),s.Folded?"Folded":s.AllIn?"All-in":game.Actor==i?"Thinking…":"Bet "+s.StreetBet,text);
                    if(game.Street==PokerStreet.Complete&&!s.Folded){Card(new Rect(x+87,285,80,112),s.Hole[0],true);Card(new Rect(x+179,285,80,112),s.Hole[1],true);}
                }
                for(int i=0;i<5;i++)Card(new Rect(610+i*145,422,126,175),i<game.Board.Count?game.Board[i]:0,i<game.Board.Count);
                PrisonMenuTheme.Panel(new Rect(0,650,1920,430),new Color(.025f,.033f,.04f,.96f));
                Card(new Rect(85,698,122,169),game.Seats[0].Hole[0],true);Card(new Rect(219,698,122,169),game.Seats[0].Hole[1],true);
                GUI.Label(new Rect(70,910,300,45),"ELIAS  ·  "+game.Seats[0].Stack+(game.Dealer==0?"  [D]":""),text);
                if(game.Street==PokerStreet.Complete)
                {
                    GUI.Label(new Rect(440,682,1330,155),game.Result,heading);
                    if(game.Seats[0].Stack>0&&GUI.Button(new Rect(490,890,440,65),"Deal next hand",button))Deal();
                    if(game.Seats[0].Stack==0&&GUI.Button(new Rect(960,890,440,65),"Start a new table",button)){Close();}
                }
                else
                {
                    GUI.Label(new Rect(430,681,1330,55),game.Actor==0?"YOUR TURN   /   "+(game.ToCall(0)==0?"Check or bet":"Call "+game.ToCall(0)):"Waiting for "+game.Seats[game.Actor].Name,heading);
                    int from=Math.Max(0,game.History.Count-3);GUI.Label(new Rect(490,747,1180,115),string.Join("   ·   ",game.History.GetRange(from,game.History.Count-from).ToArray()),text);
                    bool old=GUI.enabled;GUI.enabled=game.Actor==0;
                    if(GUI.Button(new Rect(455,912,220,65),"Fold",button))Action(PokerAction.Fold);
                    if(GUI.Button(new Rect(690,912,270,65),game.ToCall(0)==0?"Check":"Call "+Math.Min(game.ToCall(0),game.Seats[0].Stack),button))Action(PokerAction.CheckCall);
                    int max=game.Seats[0].Stack+game.Seats[0].StreetBet;
                    raiseTo=Mathf.Clamp(raiseTo,Math.Min(game.MinRaiseTo,max),max);
                    if(max>game.CurrentBet)raiseTo=Mathf.RoundToInt(GUI.HorizontalSlider(new Rect(1000,868,530,24),raiseTo,Math.Min(game.MinRaiseTo,max),max));
                    GUI.enabled=game.Actor==0&&game.Seats[0].RaiseOpen&&max>game.CurrentBet;
                    if(GUI.Button(new Rect(980,912,290,65),"Raise to "+raiseTo,button))Action(PokerAction.Raise);
                    GUI.enabled=game.Actor==0&&(game.Seats[0].RaiseOpen||max<=game.CurrentBet);
                    if(GUI.Button(new Rect(1290,912,240,65),"All-in",button))Action(PokerAction.AllIn);
                    GUI.enabled=old;
                }
                if(GUI.Button(new Rect(1610,986,250,55),"Leave table [P / B]",button))Close();
            }
            finally{GUI.matrix=matrix;}
        }
        void Card(Rect r,int card,bool face)
        {var image=face?cards[card]:back;if(image!=null)GUI.DrawTexture(r,image,ScaleMode.ScaleToFit);else{PrisonMenuTheme.Panel(r,PrisonMenuTheme.Paper);Color c=GUI.color;GUI.color=Color.black;GUI.Label(r,face?PrisonPokerRules.CardName(card):"♠",heading);GUI.color=c;}}
    }
}
