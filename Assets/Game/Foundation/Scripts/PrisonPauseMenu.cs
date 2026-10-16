using System;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.SceneManagement;
using Blackstone.Alcatraz;
using Blackstone.Story;
using Blackstone.Save;
using Blackstone.Supplied;
using DesertShift.Player;

namespace Blackstone.Foundation
{
    // Shared, live-data pause sections used by both exploration and Chapter 01.
    public sealed class PrisonPauseMenu : MonoBehaviour
    {
        public static readonly string[] Sections={"Map","Mission","Inventory","Character","Weapons","Journal","Settings","Save Game","Load Game","Exit to Main Menu"};
        FoundationBootstrap exploration;
        PrisonStoryDirector story;
        FoundationHUD explorationHUD;
        AlcatrazMap map;
        int section,slot,weaponIndex;
        Vector2 scroll;
        string message;
        public string Status=>message;
        int pendingSave=-1,pendingLoad=-1;
        bool returnToTitle;
        float nextAutosave;
        GUIStyle small,control,track,thumb;
        bool displayInitialized,fullscreen,wasOpen;
        int resolution;
        readonly int[] widths=GraphicsRules.Widths,heights=GraphicsRules.Heights;
        readonly string[] resolutions=GraphicsRules.ResolutionNames;
        PlayerMovement Player=>story!=null?story.player:exploration!=null?exploration.Player:null;
        PlayerInputHandler Input=>story!=null?story.input:exploration!=null?exploration.Input:null;
        FoundationWeapons Weapons=>Player!=null?Player.GetComponent<FoundationWeapons>():null;
        PrisonStoryState State=>story!=null?story.State:null;
        SuppliedIslandWorld World=>exploration!=null?exploration.GetComponent<SuppliedIslandWorld>():null;
        SuppliedExtrasWorld Annex=>exploration!=null?exploration.GetComponent<SuppliedExtrasWorld>():null;
        FoundationPlayerVitals Vitals=>Player!=null?Player.GetComponent<FoundationPlayerVitals>():null;
        FoundationDamageable PlayerHealth=>Player!=null?Player.GetComponent<FoundationDamageable>():null;
        bool ExplorationReady=>exploration!=null&&exploration.Status=="Ready"&&(World==null||World.Ready);
        bool Open=>Input!=null&&!Input.IsCaptured&&(story!=null?!story.MainMenu:explorationHUD!=null&&!explorationHUD.TitleVisible);
        bool CheckpointPlayerAvailable=>Player!=null&&!Player.ExternalControl&&!Player.IsSwimming&&(Vitals==null||!Vitals.Failed)&&(PlayerHealth==null||!PlayerHealth.Dead);
        bool SafeCheckpoint=>CheckpointPlayerAvailable&&(story!=null?!story.Busy&&!story.PhoneOpen:ExplorationReady&&Player.Grounded);
        // Loading validates the destination below. It must also work from a title screen
        // before the paused controller has completed its first grounded update.
        bool CanLoadCheckpoint=>CheckpointPlayerAvailable&&(story!=null?!story.Busy&&!story.PhoneOpen:ExplorationReady);
        public void Configure(FoundationBootstrap foundation,PrisonStoryDirector director,AlcatrazMap island)
        {exploration=foundation;story=director;map=island;explorationHUD=foundation!=null?foundation.GetComponent<FoundationHUD>():null;nextAutosave=Time.unscaledTime+30;fullscreen=Screen.fullScreen;resolution=GraphicsRules.ResolutionIndex(Screen.width,Screen.height);displayInitialized=true;}
        void Update()
        {
            bool open=Open;
            if(open&&!wasOpen)displayInitialized=false;
            wasOpen=open;
            if(!open)
            {
                pendingSave=pendingLoad=-1;returnToTitle=false;
                if(exploration!=null&&Input!=null&&Input.CanControl&&Time.unscaledTime>=nextAutosave)
                {if(SafeCheckpoint)Save(0,false);nextAutosave=Time.unscaledTime+30;}
                return;
            }
            var key=Keyboard.current;var pad=Gamepad.current;
            bool confirm=key!=null&&key.enterKey.wasPressedThisFrame||pad!=null&&pad.buttonSouth.wasPressedThisFrame;
            if(pendingSave>=0||pendingLoad>=0)
            {
                // Keep focus on the confirmation; section navigation must not silently
                // dismiss an overwrite/load decision or operate the page underneath.
                bool cancel=key!=null&&key.backspaceKey.wasPressedThisFrame||pad!=null&&pad.buttonEast.wasPressedThisFrame;
                if(cancel)pendingSave=pendingLoad=-1;
                else if(confirm)
                {if(pendingSave>=0)Save(pendingSave,true);else Load(pendingLoad);pendingSave=pendingLoad=-1;}
                return;
            }
            if(key!=null&&key.downArrowKey.wasPressedThisFrame||pad!=null&&pad.dpad.down.wasPressedThisFrame)Select((section+1)%Sections.Length);
            if(key!=null&&key.upArrowKey.wasPressedThisFrame||pad!=null&&pad.dpad.up.wasPressedThisFrame)Select((section+Sections.Length-1)%Sections.Length);
            if(key!=null&&key.rightArrowKey.wasPressedThisFrame||pad!=null&&pad.dpad.right.wasPressedThisFrame)Choice(1);
            if(key!=null&&key.leftArrowKey.wasPressedThisFrame||pad!=null&&pad.dpad.left.wasPressedThisFrame)Choice(-1);
            if(confirm)
            {
                if(section==7)RequestSave(slot);
                else if(section==8)RequestLoad(slot);
                else if(section==9)returnToTitle=true;
                else if(section==4)EquipSelected();
                else if(section==6){Screen.SetResolution(widths[resolution],heights[resolution],fullscreen?FullScreenMode.FullScreenWindow:FullScreenMode.Windowed);PersistSettings();}
            }
        }
        void Choice(int direction)
        {
            if(section==7||section==8)slot=(slot+direction+4)%4;
            else if(section==4)
            {
                weaponIndex=(weaponIndex+direction+11)%11;
                float top=weaponIndex/2*135,bottom=top+120;
                if(top<scroll.y)scroll.y=top;
                else if(bottom>scroll.y+460)scroll.y=bottom-460;
            }
        }
        void Select(int index)
        {
            bool enteringSettings=index==6&&section!=6;
            section=index;scroll=Vector2.zero;pendingSave=pendingLoad=-1;message=null;
            if(enteringSettings)displayInitialized=false;
            if(section==4)Choice(0);
        }
        void Styles()
        {
            if(small!=null)return;
            small=new GUIStyle(GUI.skin.label){fontSize=18,wordWrap=true};small.normal.textColor=PrisonMenuTheme.Paper;
            control=new GUIStyle(GUI.skin.button){fontSize=20,padding=new RectOffset(10,10,7,7)};
            control.normal.textColor=control.hover.textColor=control.active.textColor=PrisonMenuTheme.Paper;
            track=new GUIStyle(GUI.skin.horizontalSlider);thumb=new GUIStyle(GUI.skin.horizontalSliderThumb);
        }
        public bool Draw()
        {
            Styles();
            PrisonMenuTheme.Frame(1920,1080,"PAUSED",story!=null?"CHAPTER 01":World!=null&&World.InsidePrison?"CELLHOUSE":"EXPLORATION",true);
            PrisonMenuTheme.Panel(new Rect(615,160,1265,810),new Color(.015f,.023f,.028f,.88f));
            bool enabled=GUI.enabled;
            GUI.enabled=enabled&&pendingSave<0&&pendingLoad<0;
            for(int i=0;i<Sections.Length;i++)if(PrisonMenuTheme.SectionNavigation(i,Sections[i],section==i))Select(i);
            PrisonMenuTheme.Text(new Rect(665,165,1160,28),"THE PRISON ESCAPE  /  SESSION PAUSED",true);
            PrisonMenuTheme.Hero(new Rect(665,205,1160,95),section==0?"ISLAND MAP":Sections[section],62);
            PrisonMenuTheme.Panel(new Rect(665,315,1160,1),new Color(.83f,.68f,.39f,.5f));
            if(section==0)Map();else if(section==1)Mission();else if(section==2)Inventory();else if(section==3)Character();
            else if(section==4)Equipment();else if(section==5)Journal();else if(section==6)Settings();
            else if(section==7||section==8)Slots(section==7);else Exit();
            GUI.enabled=enabled;
            if(message!=null)GUI.Label(new Rect(665,943,1150,38),message,small);
            PrisonMenuTheme.Text(new Rect(665,1008,1020,28),"ESC / START: RESUME    ↑ ↓: SECTION    ← →: SLOT / WEAPON    ENTER / A: SELECT",true);
            PrisonMenuTheme.Text(new Rect(1770,1008,90,28),(section+1).ToString("00")+" / 10",true);
            if(pendingSave>=0||pendingLoad>=0)Confirmation();
            bool result=returnToTitle;returnToTitle=false;return result;
        }
        void Card(Rect r,string title,string detail)
        {
            PrisonMenuTheme.Panel(r,new Color(.055f,.067f,.071f,.95f));
            PrisonMenuTheme.Panel(new Rect(r.x,r.y,3,r.height),new Color(.83f,.68f,.39f,.6f));
            PrisonMenuTheme.Text(new Rect(r.x+24,r.y+20,r.width-48,28),title.ToUpperInvariant(),true);
            PrisonMenuTheme.Text(new Rect(r.x+24,r.y+61,r.width-48,r.height-70),detail);
        }
        void Map()
        {
            PrisonMenuTheme.Text(new Rect(665,338,1160,40),"Explore the prison, docks, helipad and connected annex.");
            if(Annex!=null&&Annex.Visiting)
            {
                Rect r=new Rect(665,400,770,490);PrisonMenuTheme.Panel(r,new Color(.05f,.1f,.12f));
                Vector3 local=Player.transform.position-SuppliedExtrasWorld.Origin;
                Func<float,float,float,Rect> dot=(x,z,size)=>new Rect(r.x+(x+50)/146*r.width-size/2,r.y+(144-z)/199*r.height-size/2,size,size);
                foreach(var place in new[]{new Vector3(-20,0,103),new Vector3(27,0,120),new Vector3(72,0,0),new Vector3(0,0,-47),new Vector3(12,0,138)})
                    PrisonMenuTheme.Panel(dot(place.x,place.z,12),PrisonMenuTheme.Gold);
                PrisonMenuTheme.Panel(dot(local.x,local.z,12),Color.white);
                Card(new Rect(1470,400,330,320),"Annex","White: Elias\nGold: factory, carport, warehouse, solitary cell and return door\n\nNorth is up.");return;
            }
            if(map==null||Player==null){Card(new Rect(665,400,1160,220),"Map unavailable","This scene has no island map component.");return;}
            float aspect=map.SuppliedExterior?1.5f:World!=null&&World.InsidePrison ? .5f : 2f/3;
            float height=530,width=height*aspect;
            map.DrawMap(new Rect(665,390,width,height),Player.transform.position,story!=null?story.ObjectiveTarget:World!=null?World.Objective:null,true);
            Card(new Rect(665+width+35,390,Mathf.Max(280,1125-width),260),"Current zone",story!=null?"Chapter 01 / "+story.State.stage.ToString():World!=null&&World.InsidePrison?"Cellhouse\nWhite: Elias\nGold: return door":"Alcatraz Island\nWhite: Elias\nGold: cellhouse\nH: helipad\nD: coastal house");
        }
        void Mission()
        {
            Card(new Rect(665,365,750,260),"Active mission",story!=null?story.Objective:World!=null&&World.InsidePrison?"Explore the cells and galleries. Meet the inmates and find your route through the prison.":"Find the cellhouse entrance. Explore the island and its connected activities.");
            Card(new Rect(1450,365,375,260),"Mission status",State!=null?(State.stage==StoryStage.ChapterComplete?"CHAPTER COMPLETE":"IN PROGRESS")+"\n\nDay "+State.gameDay+"\nGang respect: "+State.respect:"EXPLORATION\n\nChapter progress begins in Chapter 01.");
            Card(new Rect(665,665,1160,230),"Chapter progression","Meet the inmates   /   Earn the gang’s trust\nObtain a phone   /   Face the rival gang\nSurvive isolation   /   Plan the escape");
        }
        void Inventory()
        {
            string knife=State!=null?(State.knife==KnifeLocation.Concealed?"Concealed quest item":State.knife==KnifeLocation.CellStash?"Stored in Cell B-04":"Not acquired"):"Available in equipment";
            string[,] items={{"Prison ID","B-04 / Elias Vale"},{"Cell key","Not acquired"},{"Phone",State!=null&&State.phone?"Acquired":"Not acquired"},{"Hidden knife",knife},{"Gang tattoo",State!=null&&State.tattoo?"Blue Meridian / acquired":"Not acquired"},{"Uniform","Prison work uniform"}};
            string[] icons={"id","key","phone","knife","tattoo","uniform"};
            for(int i=0;i<6;i++)
            {
                Rect r=new Rect(665+i%3*395,365+i/3*255,370,230);
                Card(r,items[i,0],"");PrisonMenuTheme.Icon(new Rect(r.x+24,r.y+78,68,68),icons[i]);
                PrisonMenuTheme.Text(new Rect(r.x+115,r.y+78,230,130),items[i,1]);
            }
        }
        void Character()
        {
            Card(new Rect(665,365,385,515),"Prisoner record","ELIAS VALE\nINMATE B-04");
            PrisonMenuTheme.Icon(new Rect(760,525,195,195),"inmate");
            PrisonMenuTheme.Text(new Rect(689,760,335,95),"Status: incarcerated\n"+(State!=null?"Chapter day "+State.gameDay:"Island exploration"));
            var boxer=Player!=null?Player.GetComponent<FoundationBoxing>():null;
            var health=Player!=null?Player.GetComponent<FoundationDamageable>():null;
            Stat("Health",health!=null?health.Health:boxer!=null?boxer.Health:100,100,1085,365,true);
            Stat("Stamina",boxer!=null?boxer.Stamina:100,100,1085,470);
            Stat("Gang respect",State!=null?State.respect:0,100,1085,575);
            string contacts=State!=null?(((State.acquaintances&1)!=0?1:0)+((State.acquaintances&2)!=0?1:0)+((State.acquaintances&4)!=0?1:0))+" / 3":"Chapter not started";
            Card(new Rect(1085,685,740,195),"Contacts / combat",contacts+"\nSuccessful combat hits: "+(Weapons!=null?Weapons.Hits:0));
        }
        void Stat(string title,float value,float max,float x,float y,bool percentage=false)
        {
            PrisonMenuTheme.Text(new Rect(x,y,520,35),title.ToUpperInvariant(),true);
            PrisonMenuTheme.Text(new Rect(x+535,y,180,35),percentage?Mathf.RoundToInt(Mathf.Clamp01(value/max)*100)+"%":Mathf.RoundToInt(value)+" / "+max);
            PrisonMenuTheme.Panel(new Rect(x,y+54,740,9),new Color(.22f,.25f,.25f));
            PrisonMenuTheme.Panel(new Rect(x,y+54,740*Mathf.Clamp01(value/max),9),PrisonMenuTheme.Gold);
        }
        void Equipment()
        {
            int rows=6;scroll=GUI.BeginScrollView(new Rect(665,365,1160,460),scroll,new Rect(0,0,1120,rows*135));
            for(int i=0;i<11;i++)
            {
                var value=(Blackstone.Foundation.Equipment)i;Rect r=new Rect(i%2*560,i/2*135,540,120);
                string detail=Weapons!=null?(Weapons.State.Equipped==value?"EQUIPPED":"AVAILABLE")+(i>=2&&i!=5?"  /  "+Weapons.State.LoadedFor(value)+" + "+Weapons.State.ReserveFor(value)+" rounds":""):(i==0?"FISTS / STORY COMBAT":i==1&&State!=null&&State.knife!=KnifeLocation.None?"QUEST ITEM / NON-EQUIPPABLE":"NOT AVAILABLE IN STORY");
                if(PrisonMenuTheme.Button(r,value.ToString().ToUpperInvariant()+"\n"+detail,true,i==weaponIndex)){weaponIndex=i;EquipSelected();}
            }
            GUI.EndScrollView();
            PrisonMenuTheme.Text(new Rect(665,850,1160,65),"Selected: "+((Blackstone.Foundation.Equipment)weaponIndex)+". Use ← → and Enter, or click a card.");
        }
        void EquipSelected()
        {
            if(Weapons==null){message="Story equipment is controlled by the mission.";return;}
            Weapons.Equip((Blackstone.Foundation.Equipment)weaponIndex);message="Equipped: "+Weapons.State.Equipped;
        }
        void Journal()
        {
            if(State==null)
            {
                Card(new Rect(665,365,1160,155),"Island routes","The cellhouse, helipad and coastal dock can be reached from Island locations on the title screen.");
                Card(new Rect(665,545,1160,155),"Connected annex","The workshop connects to a factory yard, warehouse and wooden carport.");
                Card(new Rect(665,725,1160,155),"Chapter file","Story discoveries appear here after you begin Chapter 01.");return;
            }
            int rows=1+(State.acquaintances!=0?1:0)+(State.knife!=KnifeLocation.None?1:0)+(State.gangMember?1:0)+(State.phone?1:0)
                +(State.gameDay>=2?1:0)+(State.fatherKidnapped?1:0)+(State.escapeAgreement?1:0);
            scroll=GUI.BeginScrollView(new Rect(665,365,1160,525),scroll,new Rect(0,0,1120,Mathf.Max(525,rows*130)));
            int row=0;JournalRow(ref row,"DAY 01 / Arrival","First days inside Alcatraz. Cell assignment: B-04.");
            if(State.acquaintances!=0)JournalRow(ref row,"CONTACTS / The inmates","Contacts met: "+((State.acquaintances&1)!=0?"Tomas  ":"")+((State.acquaintances&2)!=0?"Samir  ":"")+((State.acquaintances&4)!=0?"Workshop contact":""));
            if(State.knife!=KnifeLocation.None)JournalRow(ref row,"QUEST / The confiscated knife",State.knife==KnifeLocation.CellStash?"The knife is hidden in your cell stash.":"You concealed the confiscated knife.");
            if(State.gangMember)JournalRow(ref row,"CONTACT / Blue Meridian","You joined the gang. Current respect: "+State.respect+".");
            if(State.phone)JournalRow(ref row,"QUEST / The phone","The gang supplied a phone. Keep it concealed.");
            if(State.gameDay>=2)JournalRow(ref row,"DAY 02 / Isolation","You survived isolation and were released for visitation.");
            if(State.fatherKidnapped)JournalRow(ref row,"ESCAPE FILE / Family","Your father has been kidnapped. Escape must happen before next week.");
            if(State.escapeAgreement)JournalRow(ref row,"ESCAPE FILE / Agreement","The gang agreed to plan the escape.");
            GUI.EndScrollView();
        }
        void JournalRow(ref int row,string title,string detail){Card(new Rect(0,row++*130,1100,115),title,detail);}
        float Slider(string title,float value,float min,float max,float y)
        {
            PrisonMenuTheme.Text(new Rect(665,y,340,35),title);
            float next=GUI.HorizontalSlider(new Rect(1035,y+15,665,24),value,min,max,track,thumb);
            GUI.Label(new Rect(1720,y,100,35),Mathf.RoundToInt((next-min)/(max-min)*100)+"%",small);return next;
        }
        void Settings()
        {
            if(!displayInitialized)
            {
                fullscreen=Screen.fullScreen;resolution=GraphicsRules.ResolutionIndex(Screen.width,Screen.height);displayInitialized=true;
            }
            PrisonMenuTheme.Text(new Rect(665,350,300,35),"Display mode");
            if(PrisonMenuTheme.Button(new Rect(1035,345,350,46),fullscreen?"FULLSCREEN":"WINDOWED"))fullscreen=!fullscreen;
            PrisonMenuTheme.Text(new Rect(665,410,300,35),"Resolution");
            resolution=GUI.SelectionGrid(new Rect(1035,405,790,48),resolution,resolutions,resolutions.Length,control);
            PrisonMenuTheme.Text(new Rect(665,470,300,35),"Graphics quality");
            string[] qualities=FoundationGraphics.Names;
            int quality=FoundationGraphics.SelectedPreset;
            int selected=GUI.SelectionGrid(new Rect(1035,465,790,46),quality,qualities,Mathf.Min(4,qualities.Length),control);
            if(selected!=quality)FoundationGraphics.SetPreset(selected);
            var audio=story!=null?null:FoundationAudio.Instance;var bus=story!=null?story.audioBus:FindFirstObjectByType<Blackstone.Audio.PrisonAudio>();
            if(audio!=null)audio.master=Slider("Master volume",audio.master,0,1,530);else if(bus!=null)bus.master=Slider("Master volume",bus.master,0,1,530);
            if(audio!=null)audio.effects=Slider("Sound effects",audio.effects,0,1,580);else if(bus!=null)bus.effects=Slider("Sound effects",bus.effects,0,1,580);
            if(bus!=null){bus.music=Slider("Music",bus.music,0,1,630);bus.dialogue=Slider("Dialogue",bus.dialogue,0,1,680);}
            else GUI.Label(new Rect(665,630,1160,65),"This scene has no music or dialogue mixer.",small);
            if(story!=null&&story.cameraRig!=null)story.cameraRig.sensitivity=Slider("Camera sensitivity",story.cameraRig.sensitivity,.025f,.25f,730);
            else if(exploration!=null&&exploration.CameraRig!=null)exploration.CameraRig.sensitivity=Slider("Camera sensitivity",exploration.CameraRig.sensitivity,.025f,.25f,730);
            bool subtitles=PlayerPrefs.GetInt("Blackstone.Subtitles",1)==1;
            if(PrisonMenuTheme.Button(new Rect(665,785,350,40),"Subtitles: "+(subtitles?"ON":"OFF")))PlayerPrefs.SetInt("Blackstone.Subtitles",subtitles?0:1);
            bool invert=story!=null&&story.cameraRig!=null?story.cameraRig.invertY:exploration!=null&&exploration.CameraRig!=null&&exploration.CameraRig.invertY;
            if(PrisonMenuTheme.Button(new Rect(1040,785,380,40),"Invert camera Y: "+(invert?"ON":"OFF")))
            {if(story!=null&&story.cameraRig!=null)story.cameraRig.invertY=!invert;else if(exploration!=null&&exploration.CameraRig!=null)exploration.CameraRig.invertY=!invert;}
            if(PrisonMenuTheme.Button(new Rect(1460,785,365,40),"VSync: "+(FoundationGraphics.VSync?"ON":"OFF")))
                FoundationGraphics.SetVSync(!FoundationGraphics.VSync);
            if(PrisonMenuTheme.Button(new Rect(665,835,1160,65),"Apply display & save settings"))
            {Screen.SetResolution(widths[resolution],heights[resolution],fullscreen?FullScreenMode.FullScreenWindow:FullScreenMode.Windowed);PersistSettings();}
        }
        void PersistSettings()
        {
            var audio=story!=null?null:FoundationAudio.Instance;var bus=story!=null?story.audioBus:FindFirstObjectByType<Blackstone.Audio.PrisonAudio>();
            if(audio!=null){PlayerPrefs.SetFloat("Blackstone.Master",audio.master);PlayerPrefs.SetFloat("Blackstone.Effects",audio.effects);}
            else if(bus!=null){PlayerPrefs.SetFloat("Blackstone.Master",bus.master);PlayerPrefs.SetFloat("Blackstone.Effects",bus.effects);}
            if(bus!=null){PlayerPrefs.SetFloat("Blackstone.Music",bus.music);PlayerPrefs.SetFloat("Blackstone.Dialogue",bus.dialogue);}
            if(story!=null&&story.cameraRig!=null){PlayerPrefs.SetFloat("Blackstone.Sensitivity",story.cameraRig.sensitivity);PlayerPrefs.SetInt("Blackstone.Invert",story.cameraRig.invertY?1:0);}
            else if(exploration!=null&&exploration.CameraRig!=null){PlayerPrefs.SetFloat("Blackstone.Sensitivity",exploration.CameraRig.sensitivity);PlayerPrefs.SetInt("Blackstone.Invert",exploration.CameraRig.invertY?1:0);}
            PlayerPrefs.SetInt("Blackstone.Quality",FoundationGraphics.SelectedPreset);PlayerPrefs.SetInt("Blackstone.VSync",FoundationGraphics.VSync?1:0);PlayerPrefs.Save();message="Settings saved.";
        }
        bool Saved(int index,out string detail)
        {
            if(story!=null)
            {
                bool found=PrisonSave.TryLoad(out var checkpoint,index);detail=found?checkpoint.story.stage+" / "+Timestamp(checkpoint.savedUtc):"NO VALID SAVE DATA";return found;
            }
            bool valid=ExplorationSave.TryLoad(index,out var saved);detail=valid?(saved.annex?"Factory annex":saved.interior?"Cellhouse":"Island")+" / "+Timestamp(saved.savedUtc):"NO VALID SAVE DATA";return valid;
        }
        static string Timestamp(string utc)=>DateTime.TryParse(utc,out var date)?date.ToLocalTime().ToString("dd MMM / HH:mm"):"Legacy checkpoint";
        void Slots(bool saving)
        {
            PrisonMenuTheme.Text(new Rect(665,338,1160,40),saving?"Select a slot to save the current checkpoint.":"Resume a valid saved checkpoint.");
            for(int i=0;i<4;i++)
            {
                bool exists=Saved(i,out var detail);
                Rect r=new Rect(665,405+i*120,1160,100);
                Card(r,i==0?"Autosave / latest checkpoint":"Manual slot "+i.ToString("00"),detail);
                if(i==slot)PrisonMenuTheme.Panel(new Rect(r.x,r.y,r.width,2),PrisonMenuTheme.Gold);
                if(PrisonMenuTheme.Button(new Rect(1530,r.y+22,270,56),saving?"SAVE  ›":"LOAD  ›",saving?SafeCheckpoint:exists))
                {slot=i;if(saving)RequestSave(i);else RequestLoad(i);}
            }
            GUI.Label(new Rect(665,902,1160,36),story!=null?"Chapter checkpoints restore story progression and player location.":"Exploration checkpoints restore location and equipment; NPC/world state is not reset.",small);
        }
        void RequestSave(int index)
        {if(!SafeCheckpoint){message="Leave the vehicle or activity and stand on safe ground before saving.";return;}if(Saved(index,out var detail))pendingSave=index;else Save(index,true);}
        void RequestLoad(int index)
        {if(!CanLoadCheckpoint){message="Leave the current vehicle, activity or cinematic before loading.";return;}if(Saved(index,out var detail))pendingLoad=index;else message="This slot has no valid checkpoint.";}
        bool Save(int index,bool notify)
        {
            bool saved;
            if(story!=null)saved=story.SaveNow(index);
            else
            {
                var state=Weapons!=null?Weapons.State:new WeaponState();
                saved=ExplorationSave.Write(index,new ExplorationCheckpoint{scene=SceneManager.GetActiveScene().name,position=Player.transform.position,yaw=Player.transform.eulerAngles.y,health=PlayerHealth!=null?PlayerHealth.Health:100,interior=World!=null&&World.InsidePrison,annex=Annex!=null&&Annex.Visiting,equipped=state.Equipped,magazines=state.LoadedSnapshot(),ammunition=state.ReserveSnapshot()});
            }
            if(notify)message=saved?"Checkpoint saved to "+(index==0?"Autosave":"Slot "+index)+".":"Saving failed. Current progress remains in this session.";return saved;
        }
        public bool ResumeLatest()=>Load(0);
        bool Load(int index)
        {
            if(!CanLoadCheckpoint){message="Loading unavailable during the current activity.";return false;}
            if(story!=null)
            {
                if(!PrisonSave.TryLoad(out var checkpoint,index)){message="Checkpoint unavailable.";return false;}
                story.StartSession(true,index);return true;
            }
            if(!ExplorationSave.TryLoad(index,out var saved)){message="Checkpoint unavailable.";return false;}
            if((saved.interior||saved.annex)&&World==null||saved.annex&&Annex==null)
            {message="This checkpoint requires a prison interior or annex unavailable in this scene.";return false;}
            Physics.SyncTransforms();
            if(!Physics.Raycast(saved.position+Vector3.up*.4f,Vector3.down,out var floor,1.2f,1,QueryTriggerInteraction.Ignore)||floor.normal.y<.55f)
            {message="This checkpoint currently has no safe floor.";return false;}
            foreach(var collider in Physics.OverlapCapsule(saved.position+Vector3.up*.32f,saved.position+Vector3.up*1.53f,.25f,1,QueryTriggerInteraction.Ignore))
                if(!collider.transform.IsChildOf(Player.transform))
                {message="The checkpoint position is currently blocked. Move the obstacle or choose another slot.";return false;}
            if(World!=null){if(saved.interior)World.EnterCellhouse();else World.VisitCellhouse();}
            if(saved.annex&&Annex!=null)Annex.Visit();
            Player.Teleport(saved.position);Player.transform.rotation=Quaternion.Euler(0,saved.yaw,0);
            if(map!=null)map.SetSafePosition(saved.position);
            if(Weapons!=null)
            {
                Weapons.Equip(saved.equipped);
                // Equip validates the native held model before ammunition is restored.
                Weapons.State.Restore(saved.magazines,saved.ammunition,Weapons.State.Equipped);
            }
            if(PlayerHealth!=null)PlayerHealth.Restore(saved.health);
            if(exploration.CameraRig!=null)exploration.CameraRig.SnapToPlayer();
            Input.Capture(true);message=null;nextAutosave=Time.unscaledTime+30;return true;
        }
        void Confirmation()
        {
            PrisonMenuTheme.Panel(new Rect(615,160,1265,810),new Color(0,0,0,.95f));
            bool saving=pendingSave>=0;
            PrisonMenuTheme.Hero(new Rect(710,350,1050,100),saving?"Overwrite this checkpoint?":"Load this checkpoint?",56);
            PrisonMenuTheme.Text(new Rect(710,490,1050,110),saving?"The selected slot’s previous checkpoint will be replaced. A backup is retained.":"Current unsaved progress will be replaced by the selected checkpoint.");
            if(PrisonMenuTheme.Button(new Rect(710,655,480,70),saving?"Overwrite & save":"Load checkpoint"))
            {if(saving)Save(pendingSave,true);else Load(pendingLoad);pendingSave=pendingLoad=-1;}
            if(PrisonMenuTheme.Button(new Rect(1230,655,480,70),"Cancel / stay  [Backspace / B]"))pendingSave=pendingLoad=-1;
        }
        void Exit()
        {
            PrisonMenuTheme.Hero(new Rect(740,420,1050,100),"Leave your current session?",56);
            PrisonMenuTheme.Text(new Rect(740,560,1010,100),"Your latest checkpoint remains available. Progress after that checkpoint may be lost.");
            if(PrisonMenuTheme.Button(new Rect(740,735,495,75),"Yes, return to title"))returnToTitle=true;
            if(PrisonMenuTheme.Button(new Rect(1270,735,495,75),"Cancel / stay"))Select(0);
        }
    }
}
