using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.SceneManagement;
using DesertShift.Interaction;
using Blackstone.Alcatraz;

namespace Blackstone.Foundation
{
    public sealed class FoundationHUD : MonoBehaviour
    {
        public string worldTitle="BLACKSTONE\nISLAND";
        public string storyScene="SC_BlackstoneStory_Upgraded";
        FoundationBootstrap foundation;
        FoundationConversations conversations;
        PlayerInteractor interactor;
        AlcatrazMap island;
        bool title=true;
        Blackstone.Supplied.SuppliedIslandWorld suppliedWorld;
        readonly Blackstone.Supplied.SuppliedWeaponCards weaponCards=new Blackstone.Supplied.SuppliedWeaponCards();
        GUIStyle large,heading,text,small,button,centered;
        void Start()
        {
            foundation=GetComponent<FoundationBootstrap>();conversations=GetComponent<FoundationConversations>();
            if(foundation==null){enabled=false;return;}
            suppliedWorld=GetComponent<Blackstone.Supplied.SuppliedIslandWorld>();
            island=FindFirstObjectByType<AlcatrazMap>();if(island!=null)island.ExplorationHudOwnsMap=true;
            if(foundation.Player!=null)interactor=foundation.Player.GetComponent<PlayerInteractor>();
            if(foundation.Input!=null)
            {foundation.Input.ResumeOnClick=false;foundation.Input.PauseEnabled=true;foundation.Input.SetGameplayBlocked(true);foundation.Input.Capture(false);}
        }
        void OnEnable(){if(island!=null)island.ExplorationHudOwnsMap=true;}
        void OnDisable(){if(island!=null)island.ExplorationHudOwnsMap=false;}
        void Enter()
        {
            if(foundation.Status!="Ready"||foundation.Input==null)return;
            title=false;foundation.Input.SetGameplayBlocked(false);foundation.Input.Capture(true);
        }
        void Update()
        {
            if(foundation==null||foundation.Input==null)return;
            if(title&&((Keyboard.current!=null&&Keyboard.current.enterKey.wasPressedThisFrame)
                ||(Gamepad.current!=null&&Gamepad.current.buttonSouth.wasPressedThisFrame)))Enter();
            if(!title&&!foundation.Input.IsCaptured&&Gamepad.current!=null&&Gamepad.current.buttonSouth.wasPressedThisFrame)
                foundation.Input.Capture(true);
        }
        void Styles()
        {
            if(text!=null)return;
            text=new GUIStyle(GUI.skin.label){fontSize=21,wordWrap=true};text.normal.textColor=Color.white;
            small=new GUIStyle(text){fontSize=15,wordWrap=false};
            heading=new GUIStyle(text){fontSize=24,fontStyle=FontStyle.Bold,wordWrap=false};
            large=new GUIStyle(heading){fontSize=58,wordWrap=true};
            button=new GUIStyle(GUI.skin.button){fontSize=20};
            centered=new GUIStyle(text){alignment=TextAnchor.MiddleCenter};
        }
        void OnGUI()
        {
            if(foundation==null)return;Styles();
            var viewport=new FoundationViewport(Screen.width,Screen.height);
            Matrix4x4 old=GUI.matrix;Color oldColor=GUI.color;
            GUI.matrix=viewport.Matrix;GUI.color=Color.white;
            try
            {
                bool paused=foundation.Input==null||!foundation.Input.IsCaptured;
                if(title||paused){Menu(viewport);return;}
                bool mapHeld=Keyboard.current!=null&&Keyboard.current.mKey.isPressed
                    ||Gamepad.current!=null&&Gamepad.current.selectButton.isPressed;
                if(mapHeld&&island!=null){FullMap(viewport);return;}
                Gameplay(viewport);
            }
            finally{GUI.matrix=old;GUI.color=oldColor;}
        }
        void Menu(FoundationViewport viewport)
        {
            float x=(viewport.Width-1380)/2,y=(viewport.Height-720)/2;
            Panel(new Rect(0,0,viewport.Width,viewport.Height),new Color(.015f,.023f,.027f,.77f));
            Panel(new Rect(x,y,640,720),new Color(.025f,.045f,.055f,.94f));
            GUI.Label(new Rect(x+40,y+28,550,40),"THE SILENT BLUEPRINT",heading);
            GUI.Label(new Rect(x+35,y+85,570,155),title?worldTitle:"PAUSED",large);
            GUI.Label(new Rect(x+40,y+249,550,30),suppliedWorld!=null?"Alcatraz exterior":"Playable prison island",small);
            GUI.Label(new Rect(x+40,y+294,550,62),"Elias Vale · Inmate B-04\nA prisoner with a reason to escape.",text);
            if(foundation.Status!="Ready")
                GUI.Label(new Rect(x+40,y+379,550,175),foundation.Status??"Preparing characters...",text);
            else
            {
                if(GUI.Button(new Rect(x+40,y+380,550,58),title?"Explore  [Enter / A]":"Resume  [Esc / A]",button))
                {if(title)Enter();else foundation.Input.Capture(true);}
                if(Application.CanStreamedLevelBeLoaded(storyScene)&&GUI.Button(new Rect(x+40,y+450,550,48),"Play Chapter 01",button))
                {Time.timeScale=1;SceneManager.LoadScene(storyScene);}
                if(suppliedWorld==null&&Application.CanStreamedLevelBeLoaded("SC_AlcatrazSuppliedIsland")
                    &&Resources.Load<GameObject>("AlcatrazSupplied/Prepared/Island")!=null
                    &&GUI.Button(new Rect(x+40,y+507,550,42),"Explore supplied Alcatraz",button))
                {Time.timeScale=1;SceneManager.LoadScene("SC_AlcatrazSuppliedIsland");}
                var audio=FoundationAudio.Instance;
                if(audio!=null)
                {
                    GUI.Label(new Rect(x+40,y+571,220,30),"Master volume",small);
                    audio.master=GUI.HorizontalSlider(new Rect(x+270,y+582,320,25),audio.master,0,1);
                    GUI.Label(new Rect(x+40,y+613,220,30),"Effects / footsteps",small);
                    audio.effects=GUI.HorizontalSlider(new Rect(x+270,y+624,320,25),audio.effects,0,1);
                }
                if(foundation.CameraRig!=null)
                {
                    GUI.Label(new Rect(x+40,y+655,220,30),"Camera sensitivity",small);
                    foundation.CameraRig.sensitivity=GUI.HorizontalSlider(new Rect(x+270,y+666,320,25),foundation.CameraRig.sensitivity,.035f,.18f);
                }
            }
            Panel(new Rect(x+720,y+150,660,470),new Color(.025f,.045f,.055f,.85f));
            GUI.Label(new Rect(x+760,y+178,550,45),"PRISON ROUTINE",heading);
            GUI.Label(new Rect(x+760,y+242,550,355),"WASD / Left stick   Move\nShift / L3   Run     ·     Alt   Slow walk\nCtrl / B   Crouch     ·     Space / A   Jump\nMouse / Right stick   Camera\nE / X   Doors     ·     Q / RB   Shoulder\n1–5 / D-pad left   Equipment\nHold Tab / LB   Inventory     ·     M / View   Map\nRMB / LT   Aim     ·     LMB / RT   Use\nR / Y   Reload     ·     Esc / Start   Pause",text);
        }
        void Gameplay(FoundationViewport viewport)
        {
            Panel(new Rect(25,22,555,114),new Color(.015f,.03f,.035f,.88f));
            GUI.Label(new Rect(43,33,522,34),"GOAL: ESCAPE THE PRISON",heading);
            GUI.Label(new Rect(43,75,522,30),suppliedWorld!=null?"Find the cellhouse entrance":"Explore the prison",text);
            GUI.Label(new Rect(43,109,522,23),"Prepare your route · Chapter 01 in the pause menu",small);
            float right=viewport.Width-341;
            Panel(new Rect(right,22,316,74),new Color(.015f,.03f,.035f,.88f));
            GUI.Label(new Rect(right+15,31,286,26),"INMATE ELIAS VALE  /  B-04",small);
            GUI.Label(new Rect(right+15,60,286,30),suppliedWorld!=null?"ALCATRAZ EXTERIOR":"ALCATRAZ PRISON",heading);
            if(island!=null&&foundation.Player!=null)
            {
                Rect map=viewport.Map(island.suppliedLayout);
                island.DrawMap(map,foundation.Player.transform.position,suppliedWorld!=null?suppliedWorld.ChapterGate:null,false);
                GUI.Label(new Rect(map.x,map.yMax+5,280,25),"M / View  ·  Island map",small);
            }
            var equipment=foundation.PlayerEquipment;
            bool inventory=Keyboard.current!=null&&Keyboard.current.tabKey.isPressed
                ||Gamepad.current!=null&&Gamepad.current.leftShoulder.isPressed;
            if(equipment!=null)
            {
                if(inventory)weaponCards.DrawInventory(equipment,viewport);
                weaponCards.DrawEquipped(equipment,viewport.Equipment);
                // Only armed/aimed gameplay needs an aiming reticle.
                if(equipment.State.Equipped!=Equipment.Unarmed||foundation.Player.IsAiming)
                {
                    GUI.color=Time.time<equipment.HitMarkerUntil?new Color(.45f,1,.5f):Color.white;
                    float cx=viewport.Width/2,cy=viewport.Height/2;
                    GUI.DrawTexture(new Rect(cx-8,cy-1,16,2),Texture2D.whiteTexture);
                    GUI.DrawTexture(new Rect(cx-1,cy-8,2,16),Texture2D.whiteTexture);GUI.color=Color.white;
                }
            }
            float center=viewport.Width/2;
            string prompt=null;
            if(island!=null&&Time.unscaledTime<island.RecoveryMessageUntil)prompt="Returned to safe ground";
            else if(suppliedWorld!=null&&suppliedWorld.ChapterGate!=null&&foundation.Player!=null
                &&Vector3.Distance(foundation.Player.transform.position,suppliedWorld.ChapterGate.position)<3.4f)
                prompt="E / X   ENTER CELLHOUSE · CHAPTER 01";
            else if(interactor!=null)prompt=interactor.CurrentPrompt;
            if(!string.IsNullOrEmpty(prompt))
            {
                Rect rect=new Rect(center-350,viewport.Height-207,700,48);
                Panel(rect,new Color(.015f,.03f,.035f,.88f));GUI.Label(rect,prompt,centered);
            }
            if(conversations!=null&&!string.IsNullOrEmpty(conversations.Subtitle))
            {
                Panel(new Rect(center-375,viewport.Height-137,750,92),new Color(.015f,.03f,.035f,.88f));
                GUI.Label(new Rect(center-355,viewport.Height-129,710,25),conversations.Speaker,small);
                GUI.Label(new Rect(center-355,viewport.Height-100,710,50),conversations.Subtitle,text);
            }
            GUI.Label(new Rect(center-430,viewport.Height-28,860,25),"WASD Move   Shift Run   E Interact   RMB Aim   R Reload   Tab Inventory   M Map",small);
        }
        void FullMap(FoundationViewport viewport)
        {
            Panel(new Rect(0,0,viewport.Width,viewport.Height),new Color(.015f,.024f,.03f,.97f));
            GUI.Label(new Rect(viewport.Width/2-170,28,340,40),"ALCATRAZ ISLAND",heading);
            float aspect=island.suppliedLayout?1.5f:2f/3;
            float height=Mathf.Min(viewport.Height-180,760);
            height=Mathf.Min(height,(viewport.Width-100)/aspect);
            Rect bounds=new Rect((viewport.Width-height*aspect)/2,(viewport.Height-height)/2,height*aspect,height);
            island.DrawMap(bounds,foundation.Player.transform.position,suppliedWorld!=null?suppliedWorld.ChapterGate:null,true);
            GUI.Label(new Rect(viewport.Width/2-235,viewport.Height-46,470,30),"Release M / View to return · White: Elias · Gold: entrance",small);
        }
        static void Panel(Rect rect,Color color)
        {Color old=GUI.color;GUI.color=color;GUI.DrawTexture(rect,Texture2D.whiteTexture);GUI.color=old;}
    }
}
