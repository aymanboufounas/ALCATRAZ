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
        public bool TitleVisible=>title;
        PrisonPauseMenu pauseMenu;
        int menuPage,menuSelection;
        string menuNotice;
        Blackstone.Supplied.SuppliedIslandWorld suppliedWorld;
        readonly Blackstone.Supplied.SuppliedWeaponCards weaponCards=new Blackstone.Supplied.SuppliedWeaponCards();
        GUIStyle large,heading,text,small,button,centered;
        void Start()
        {
            foundation=GetComponent<FoundationBootstrap>();conversations=GetComponent<FoundationConversations>();
            if(foundation==null){enabled=false;return;}
            suppliedWorld=GetComponent<Blackstone.Supplied.SuppliedIslandWorld>();
            island=FindFirstObjectByType<AlcatrazMap>();if(island!=null)island.ExplorationHudOwnsMap=true;
            pauseMenu=gameObject.GetComponent<PrisonPauseMenu>();if(pauseMenu==null)pauseMenu=gameObject.AddComponent<PrisonPauseMenu>();
            pauseMenu.Configure(foundation,null,island);
            if(foundation.CameraRig!=null){foundation.CameraRig.sensitivity=PlayerPrefs.GetFloat("Blackstone.Sensitivity",.09f);foundation.CameraRig.invertY=PlayerPrefs.GetInt("Blackstone.Invert",0)!=0;}
            if(foundation.Player!=null)interactor=foundation.Player.GetComponent<PlayerInteractor>();
            if(foundation.Input!=null)
            {foundation.Input.ResumeOnClick=false;foundation.Input.PauseEnabled=true;foundation.Input.SetGameplayBlocked(true);foundation.Input.Capture(false);}
            if(FoundationPlayerVitals.ConsumeRestart(SceneManager.GetActiveScene().name))
            {
                Enter(); if(title)Enter(false);
                foundation.Player?.GetComponent<FoundationDamageable>()?.Restore(100);
            }
        }
        void OnEnable(){if(island!=null)island.ExplorationHudOwnsMap=true;}
        void OnDisable(){if(island!=null)island.ExplorationHudOwnsMap=false;}
        void Enter(bool resumeCheckpoint=true)
        {
            if(foundation.Status!="Ready"||foundation.Input==null)return;
            if(resumeCheckpoint&&title&&pauseMenu!=null&&ExplorationSave.TryLoad(0,out var checkpoint)&&!pauseMenu.ResumeLatest())
            {menuNotice=pauseMenu.Status??"This checkpoint could not be restored.";return;}
            menuNotice=null;
            title=false;foundation.Input.SetGameplayBlocked(false);foundation.Input.Capture(true);
        }
        void ReturnToTitle()
        {
            // Recreate the session so a hidden vehicle passenger, poker camera,
            // ragdoll or external-control flag cannot survive into Continue.
            var scene=SceneManager.GetActiveScene();
            Time.timeScale=1;
#if UNITY_EDITOR
            if(!Application.CanStreamedLevelBeLoaded(scene.name)&&!string.IsNullOrEmpty(scene.path))
            {
                UnityEditor.SceneManagement.EditorSceneManager.LoadSceneInPlayMode(scene.path,new LoadSceneParameters(LoadSceneMode.Single));
                return;
            }
#endif
            SceneManager.LoadScene(scene.name);
        }
        void Update()
        {
            if(foundation==null||foundation.Input==null)return;
            if(!title||foundation.Player!=null&&foundation.Player.GetComponent<FoundationPlayerVitals>()?.Failed==true)return;
            var key=Keyboard.current;var pad=Gamepad.current;
            bool down=key!=null&&key.downArrowKey.wasPressedThisFrame||pad!=null&&pad.dpad.down.wasPressedThisFrame;
            bool up=key!=null&&key.upArrowKey.wasPressedThisFrame||pad!=null&&pad.dpad.up.wasPressedThisFrame;
            if(down||up)
            {
                int direction=down?1:-1;
                do{menuSelection=(menuSelection+direction+6)%6;}while(!MenuAvailable(menuSelection));
            }
            if(key!=null&&key.enterKey.wasPressedThisFrame||pad!=null&&pad.buttonSouth.wasPressedThisFrame)
                ActivateMenu(menuSelection);
        }
        bool MenuAvailable(int index)
        {
            if(index==0)return foundation.Status=="Ready";
            if(index==1)return Application.CanStreamedLevelBeLoaded(storyScene);
            if(index==2)return suppliedWorld!=null&&suppliedWorld.Ready;
            return true;
        }
        void ActivateMenu(int index)
        {
            if(!MenuAvailable(index))return;
            menuSelection=index;
            if(index==0){menuPage=0;if(title)Enter();else foundation.Input.Capture(true);}
            else if(index==1){Time.timeScale=1;SceneManager.LoadScene(storyScene);}
            else if(index==2)menuPage=1;
            else if(index==3)menuPage=2;
            else if(index==4)menuPage=3;
            else if(title)Application.Quit();
            else ReturnToTitle();
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
            if(foundation==null||foundation.Player!=null&&foundation.Player.GetComponent<FoundationPlayerVitals>()?.Failed==true
                ||Blackstone.Activities.PrisonPokerTable.Active!=null&&foundation.Input!=null&&foundation.Input.IsCaptured)return;Styles();
            var viewport=new FoundationViewport(Screen.width,Screen.height);
            Matrix4x4 old=GUI.matrix;Color oldColor=GUI.color;
            GUI.matrix=viewport.Matrix;GUI.color=Color.white;
            try
            {
                bool paused=foundation.Input==null||!foundation.Input.IsCaptured;
                if(title||paused)
                {
                    GUI.matrix=PrisonMenuTheme.MenuMatrix;
                    if(title)Menu();
                    else if(pauseMenu!=null&&pauseMenu.Draw())
                    ReturnToTitle();
                    return;
                }
                bool mapHeld=Keyboard.current!=null&&Keyboard.current.mKey.isPressed
                    ||Gamepad.current!=null&&Gamepad.current.selectButton.isPressed;
                if(mapHeld&&island!=null){FullMap(viewport);return;}
                Gameplay(viewport);
            }
            finally{GUI.matrix=old;GUI.color=oldColor;}
        }
        void Menu()
        {
            PrisonMenuTheme.Frame(1920,1080,title?"ALCATRAZ\nISLAND":"PAUSED",suppliedWorld!=null&&suppliedWorld.InsidePrison?"CELLHOUSE":"SAN FRANCISCO BAY",!title);
            bool ready=foundation.Status=="Ready";
            string[] entries={title?(ExplorationSave.TryLoad(0,out var checkpoint)?"01   Continue checkpoint":"01   Enter the island"):"01   Resume game",
                "02   Chapter 01","03   Island locations","04   Settings","05   Controls",title?"06   Quit":"06   Return to title"};
            for(int i=0;i<entries.Length;i++)
                if(PrisonMenuTheme.Navigation(i,entries[i],MenuAvailable(i),menuSelection==i))ActivateMenu(i);
            float x=665,w=1170;
            if(menuPage>0&&Event.current.type==EventType.MouseDown&&new Rect(x,160,w,810).Contains(Event.current.mousePosition))
                menuSelection=menuPage+1;
            if(!ready){PrisonMenuTheme.Text(new Rect(x,160,w,250),foundation.Status??"Preparing the island…");return;}
            if(menuPage==0)
            {
                PrisonMenuTheme.Text(new Rect(x,260,w,30),"CHAPTER 01  /  THE PRISONER",true);
                PrisonMenuTheme.Hero(new Rect(x,285,w,105),"A way out begins here.",76);
                PrisonMenuTheme.Panel(new Rect(x,421,80,3),PrisonMenuTheme.Gold);
                PrisonMenuTheme.Text(new Rect(x,464,Mathf.Min(w,650),145),"Discover the island, meet the inmates and learn the prison routine. Build alliances. Find your route to freedom.");
                PrisonMenuTheme.Panel(new Rect(x,655,w,1),new Color(.83f,.68f,.39f,.5f));
                PrisonMenuTheme.Text(new Rect(x,685,w,30),"AVAILABLE ON THE ISLAND",true);
                PrisonMenuTheme.Features(x,745,w);
            }
            else if(menuPage==1)
            {
                PrisonMenuTheme.Hero(new Rect(x,180,w,90),"ISLAND LOCATIONS",68);
                if(PrisonMenuTheme.Button(new Rect(x,335,w,80),"Cellhouse   /   Cells, dining hall & poker")){suppliedWorld.EnterCellhouse();Enter(false);}
                if(PrisonMenuTheme.Button(new Rect(x,440,w,80),"Helipad   /   Little Bird flight")){suppliedWorld.VisitHelipad();Enter(false);}
                if(PrisonMenuTheme.Button(new Rect(x,545,w,80),"Coastal dock   /   Patrol boat")){suppliedWorld.VisitCoastalHouse();Enter(false);}
                if(PrisonMenuTheme.Button(new Rect(x,650,w,80),"Workshop & recreation annex")){var extras=FindFirstObjectByType<Blackstone.Supplied.SuppliedExtrasWorld>();if(extras!=null){extras.Visit();Enter(false);}}
            }
            else if(menuPage==2)
            {
                PrisonMenuTheme.Hero(new Rect(x,180,w,90),"SETTINGS",68);
                var audio=FoundationAudio.Instance;
                if(audio!=null){PrisonMenuTheme.Text(new Rect(x,335,300,35),"Master volume");audio.master=GUI.HorizontalSlider(new Rect(x+330,352,w-350,22),audio.master,0,1);PrisonMenuTheme.Text(new Rect(x,414,300,35),"Effects & footsteps");audio.effects=GUI.HorizontalSlider(new Rect(x+330,430,w-350,22),audio.effects,0,1);}
                if(foundation.CameraRig!=null){PrisonMenuTheme.Text(new Rect(x,493,300,35),"Camera sensitivity");foundation.CameraRig.sensitivity=GUI.HorizontalSlider(new Rect(x+330,510,w-350,22),foundation.CameraRig.sensitivity,.025f,.25f);foundation.CameraRig.invertY=GUI.Toggle(new Rect(x,572,w,40),foundation.CameraRig.invertY," Invert camera Y");}
                PrisonMenuTheme.Text(new Rect(x,640,300,35),"Display quality");int quality=GUI.SelectionGrid(new Rect(x+330,642,w-350,48),Mathf.Clamp(QualitySettings.GetQualityLevel(),0,QualitySettings.names.Length-1),QualitySettings.names,QualitySettings.names.Length);if(quality!=QualitySettings.GetQualityLevel())QualitySettings.SetQualityLevel(quality,true);
                if(PrisonMenuTheme.Button(new Rect(x,765,w,66),"Save settings")){if(audio!=null){PlayerPrefs.SetFloat("Blackstone.Master",audio.master);PlayerPrefs.SetFloat("Blackstone.Effects",audio.effects);}if(foundation.CameraRig!=null){PlayerPrefs.SetFloat("Blackstone.Sensitivity",foundation.CameraRig.sensitivity);PlayerPrefs.SetInt("Blackstone.Invert",foundation.CameraRig.invertY?1:0);}PlayerPrefs.SetInt("Blackstone.Quality",quality);PlayerPrefs.Save();menuPage=menuSelection=0;}
            }
            else
            {
                PrisonMenuTheme.Hero(new Rect(x,180,w,90),"CONTROLS",68);
                PrisonMenuTheme.Text(new Rect(x,320,w,470),"WASD / Left stick     Move or swim\nShift / L3     Run or swim faster      ·      Alt     Walk\nCtrl / B     Crouch      ·      Space / A     Jump or climb a low shore\nE / X     Interact & board vehicles\n1–5     Equipment      ·      Mouse wheel     Extra weapons\nRMB / LT     Aim or boxing guard\nLMB / RT     Fire or punch      ·      R / Y     Reload\nSpace / Ctrl     Helicopter rise / descend\nTab / LB     Inventory      ·      M / View     Map\nEsc / Start     Pause      ·      P / B     Leave poker\nRestricted water: wanted alert, then mission checkpoint restart.\nHealth starts at 100%. At 0%, restart from the latest checkpoint.");
            }
            if(menuNotice!=null)GUI.Label(new Rect(x,930,w,55),menuNotice,text);
            PrisonMenuTheme.Text(new Rect(x,1000,w,28),"↑ ↓ / D-PAD: MENU   ·   ENTER / A: SELECT   ·   MOUSE: PAGE CONTROLS",true);
        }
        void Gameplay(FoundationViewport viewport)
        {
            Panel(new Rect(25,22,555,114),new Color(.015f,.03f,.035f,.88f));
            GUI.Label(new Rect(43,33,522,34),"GOAL: ESCAPE THE PRISON",heading);
            GUI.Label(new Rect(43,75,522,30),suppliedWorld!=null?(suppliedWorld.InsidePrison?"Explore the cells and galleries":"Find the cellhouse entrance"):"Explore the prison",text);
            GUI.Label(new Rect(43,109,522,23),suppliedWorld!=null?"Esc · Cellhouse / Helipad / Coastal house":"Prepare your route · Chapter 01 in the pause menu",small);
            float right=viewport.Width-341;
            Panel(new Rect(right,22,316,74),new Color(.015f,.03f,.035f,.88f));
            GUI.Label(new Rect(right+15,31,286,26),"INMATE ELIAS VALE  /  B-04",small);
            GUI.Label(new Rect(right+15,60,286,30),suppliedWorld!=null&&!suppliedWorld.InsidePrison?"ALCATRAZ EXTERIOR":"ALCATRAZ CELLHOUSE",heading);
            if(island!=null&&foundation.Player!=null)
            {
                Rect map=viewport.Map(island.SuppliedExterior);
                island.DrawMap(map,foundation.Player.transform.position,suppliedWorld!=null?suppliedWorld.Objective:null,false);
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
            else if(suppliedWorld!=null&&suppliedWorld.Objective!=null&&foundation.Player!=null
                &&Vector3.Distance(foundation.Player.transform.position,suppliedWorld.Objective.position)<3.4f)
                prompt=suppliedWorld.InsidePrison?"E / X   RETURN TO ALCATRAZ ISLAND":"E / X   ENTER CELLHOUSE";
            else if(interactor!=null)prompt=interactor.CurrentPrompt;
            if(!string.IsNullOrEmpty(prompt))
            {
                Rect rect=new Rect(center-350,viewport.Height-207,700,48);
                Panel(rect,new Color(.015f,.03f,.035f,.88f));GUI.Label(rect,prompt,centered);
            }
            if(PlayerPrefs.GetInt("Blackstone.Subtitles",1)==1&&conversations!=null&&!string.IsNullOrEmpty(conversations.Subtitle))
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
            GUI.Label(new Rect(viewport.Width/2-170,28,340,40),suppliedWorld!=null&&suppliedWorld.InsidePrison?"ALCATRAZ CELLHOUSE":"ALCATRAZ ISLAND",heading);
            float aspect=island.SuppliedExterior?1.5f:2f/3;
            float height=Mathf.Min(viewport.Height-180,760);
            height=Mathf.Min(height,(viewport.Width-100)/aspect);
            Rect bounds=new Rect((viewport.Width-height*aspect)/2,(viewport.Height-height)/2,height*aspect,height);
            island.DrawMap(bounds,foundation.Player.transform.position,suppliedWorld!=null?suppliedWorld.Objective:null,true);
            GUI.Label(new Rect(viewport.Width/2-235,viewport.Height-46,470,30),"Release M / View to return · White: Elias · Gold: door",small);
        }
        static void Panel(Rect rect,Color color)
        {Color old=GUI.color;GUI.color=color;GUI.DrawTexture(rect,Texture2D.whiteTexture);GUI.color=old;}
    }
}
