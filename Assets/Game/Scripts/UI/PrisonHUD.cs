using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using Blackstone.Story;

namespace Blackstone.UI
{
    public sealed class PrisonHUD : MonoBehaviour
    {
        public PrisonStoryDirector director;
        GUIStyle small, body, title, hero, button, subtitle;
        readonly Color amber = new Color(.88f, .71f, .37f);
        readonly Color green = new Color(.24f, .85f, .39f);
        readonly Color red = new Color(.96f, .24f, .26f);
        bool settings, debug;
        Blackstone.Foundation.PrisonPauseMenu pauseMenu;
        int quality = 2, resolution = 1;
        bool fullscreen, vsync = true;
        float sensitivity = .105f;
        bool invert;
        float frameTime = .016f;
        UniversalRenderPipelineAsset runtimePipeline;
        RenderPipelineAsset originalPipeline;
        Blackstone.Alcatraz.AlcatrazMap island;
        void Start()
        {
            island=FindFirstObjectByType<Blackstone.Alcatraz.AlcatrazMap>();
            pauseMenu=gameObject.GetComponent<Blackstone.Foundation.PrisonPauseMenu>();if(pauseMenu==null)pauseMenu=gameObject.AddComponent<Blackstone.Foundation.PrisonPauseMenu>();
            pauseMenu.Configure(null,director,island);
            quality = PlayerPrefs.GetInt("Blackstone.Quality", 2);
            sensitivity = PlayerPrefs.GetFloat("Blackstone.Sensitivity", .105f);
            invert = PlayerPrefs.GetInt("Blackstone.Invert", 0) == 1;
            vsync = PlayerPrefs.GetInt("Blackstone.VSync", 1) == 1;
            director.audioBus.master = PlayerPrefs.GetFloat("Blackstone.Master", .8f);
            director.audioBus.effects = PlayerPrefs.GetFloat("Blackstone.Effects", .8f);
            director.audioBus.dialogue = PlayerPrefs.GetFloat("Blackstone.Dialogue", .9f);
            director.audioBus.music = PlayerPrefs.GetFloat("Blackstone.Music", .35f);
            originalPipeline = GraphicsSettings.defaultRenderPipeline;
            if (originalPipeline is UniversalRenderPipelineAsset)
            {
                runtimePipeline = Instantiate((UniversalRenderPipelineAsset)originalPipeline);
                GraphicsSettings.defaultRenderPipeline = runtimePipeline;
                QualitySettings.renderPipeline = runtimePipeline;
            }
            ApplySettings(false);
        }
        void Update()
        {
            if (director.input.DebugPressed) debug = !debug;
            frameTime = Mathf.Lerp(frameTime, Time.unscaledDeltaTime, .08f);
            if (director.MainMenu && director.input.ConfirmPressed)
            { settings = false; director.StartSession(director.CanContinue); }
            if (director.MainMenu && director.input.RetryPressed)
            { settings = false; director.StartSession(false); }
        }
        void Styles()
        {
            if (body != null) return;
            body = new GUIStyle(GUI.skin.label) { fontSize = 23, wordWrap = true, alignment = TextAnchor.MiddleLeft };
            body.normal.textColor = Color.white;
            small = new GUIStyle(body) { fontSize = 17 };
            title = new GUIStyle(body) { fontSize = 27, fontStyle = FontStyle.Bold };
            hero = new GUIStyle(body) { fontSize = 64, alignment = TextAnchor.MiddleCenter, fontStyle = FontStyle.Bold };
            subtitle = new GUIStyle(body) { fontSize = 29, alignment = TextAnchor.MiddleCenter };
            button = new GUIStyle(GUI.skin.button) { fontSize = 21, alignment = TextAnchor.MiddleLeft, padding = new RectOffset(22, 20, 8, 8) };
        }
        void OnGUI()
        {
            if (director == null || director.input == null) return;
            Styles(); Matrix4x4 original = GUI.matrix;
            GUI.matrix = Matrix4x4.TRS(Vector3.zero, Quaternion.identity, new Vector3(Screen.width / 1920f, Screen.height / 1080f, 1));
            if (director.MainMenu)
            {
                GUI.matrix=Blackstone.Foundation.PrisonMenuTheme.MenuMatrix;Menu();
                GUI.matrix=Matrix4x4.TRS(Vector3.zero,Quaternion.identity,new Vector3(Screen.width/1920f,Screen.height/1080f,1));
            }
            else
            {
                if (!director.Letterbox && Blackstone.Activities.PrisonPokerTable.Active == null) Gameplay();
                if (director.Letterbox)
                {
                    Panel(new Rect(0,0,1920,100), Color.black); Panel(new Rect(0,920,1920,160), Color.black);
                    if (PlayerPrefs.GetInt("Blackstone.Subtitles",1)==1&&!string.IsNullOrEmpty(director.Subtitle))
                    {
                        Label(new Rect(300,926,1320,30), director.Speaker, small, amber, TextAnchor.MiddleCenter);
                        Label(new Rect(230,962,1460,64), director.Subtitle, subtitle);
                        Label(new Rect(1520,1040,330,24), "[SPACE / A] NEXT LINE", small, amber, TextAnchor.MiddleRight);
                    }
                }
                if (director.State.stage == StoryStage.SolitarySleeping) SleepClock();
                if (director.PhoneOpen) Phone();
                if (!string.IsNullOrEmpty(director.Banner)) Banner();
                if (!director.input.IsCaptured)
                {
                    GUI.matrix=Blackstone.Foundation.PrisonMenuTheme.MenuMatrix;Pause();
                    GUI.matrix=Matrix4x4.TRS(Vector3.zero,Quaternion.identity,new Vector3(Screen.width/1920f,Screen.height/1080f,1));
                }
            }
            if (director.Fade > 0) Panel(new Rect(0,0,1920,1080), new Color(0,0,0,director.Fade));
            if (debug)
            {
                Panel(new Rect(1360,30,530,145), new Color(0,0,0,.8f));
                Label(new Rect(1380,40,490,125), $"F3  |  Blackstone Chapter 01\n{1f / Mathf.Max(frameTime,.001f):0} FPS  |  {director.State.stage}\n" +
                    $"Position {director.player.transform.position:F1}\n{director.player.Speed:F1} m/s  |  saved locally", small);
            }
            GUI.matrix = original;
        }
        void Gameplay()
        {
            Panel(new Rect(42,38,570,210), new Color(.025f,.035f,.045f,.86f));
            Panel(new Rect(42,38,4,210), amber);
            Label(new Rect(62,48,520,24), (island!=null?"ALCATRAZ PENITENTIARY":"BLACKSTONE PENITENTIARY")+"  /  INMATE B-04", small, amber);
            Label(new Rect(62,79,510,40), "GOAL: ESCAPE THE PRISON", title);
            Label(new Rect(62,122,510,35), $"0{director.MissionNumber}  {director.MissionTitle}", body, amber);
            Label(new Rect(62,161,510,74), director.Objective, body);
            Label(new Rect(1260,45,620,28), $"DAY {director.State.gameDay}   |   INMATE ELIAS VALE  /  B-04", small, Color.white, TextAnchor.MiddleRight);
            Panel(new Rect(1610,86,270,5), new Color(1,1,1,.15f));
            Panel(new Rect(1610,86,270 * director.State.respect / 100f,5), amber);
            Label(new Rect(1450,102,430,30), $"GANG RESPECT  {director.State.respect}/100", small, amber, TextAnchor.MiddleRight);
            string knife = director.State.knife == KnifeLocation.None ? "NONE" : director.State.knife == KnifeLocation.Concealed ? "CONCEALED" : "STORED IN B-04";
            Label(new Rect(1420,141,460,50), "KNIFE: " + knife + (director.State.phone ? "    PHONE: ACQUIRED" : ""), small, Color.white, TextAnchor.MiddleRight);
            if (director.State.stage == StoryStage.Socialize)
            {
                int n = ((director.State.acquaintances & 1) != 0 ? 1 : 0) + ((director.State.acquaintances & 2) != 0 ? 1 : 0) + ((director.State.acquaintances & 4) != 0 ? 1 : 0);
                float left = Mathf.Max(0, director.fightAtSeconds - director.State.routineSeconds);
                Label(new Rect(62,254,680,40), $"CONTACTS {n}/3   |   YARD PERIOD {FormatTime(left)}   |   Training bag available", small, amber);
            }
            if (director.State.stage == StoryStage.KnifeOpportunity)
            {
                Panel(new Rect(780,150,360,75), new Color(0,0,0,.85f));
                Label(new Rect(790,155,340,65), $"HIDE IT  {director.State.knifeSeconds:0.0}s", title, red, TextAnchor.MiddleCenter);
            }
            if (director.State.stage == StoryStage.RivalFight)
                Label(new Rect(760,165,420,45), $"PUNCHES LANDED  {director.State.brawlHits}/3", title, red, TextAnchor.MiddleCenter);
            if (director.State.fatherKidnapped)
                Label(new Rect(1290,204,590,38), $"ESCAPE DEADLINE  {director.State.escapeDaysRemaining} DAYS", body, red, TextAnchor.MiddleRight);
            MiniMap(); Waypoint();
            if (director.input.CanControl)
            {
                Label(new Rect(944,524,32,32), "·", body, new Color(1,1,1,.65f), TextAnchor.MiddleCenter);
                if (!string.IsNullOrEmpty(director.interactor.CurrentPrompt))
                {
                    Panel(new Rect(610,866,700,52), new Color(0,0,0,.82f));
                    Label(new Rect(630,870,660,45), director.interactor.CurrentPrompt, body, Color.white, TextAnchor.MiddleCenter);
                }
            }
            if (!string.IsNullOrEmpty(director.Toast))
                Label(new Rect(510,934,900,60), director.Toast, body, amber, TextAnchor.MiddleCenter);
            Label(new Rect(500,1030,1360,30), "WASD / LEFT STICK  MOVE    SHIFT / L3  SPRINT    CTRL / B  CROUCH    E / X  INTERACT    P  PHONE    ESC / START  PAUSE", small,
                new Color(1,1,1,.65f), TextAnchor.MiddleRight);
        }
        void Waypoint()
        {
            Transform target = director.ObjectiveTarget; if (target == null || director.Busy || director.State.missed) return;
            Vector3 point = director.mainCamera.WorldToScreenPoint(target.position + Vector3.up * 1.9f);
            if (point.z <= 0) return;
            float x = Mathf.Clamp(point.x / Screen.width * 1920, 60, 1860);
            float y = Mathf.Clamp((1 - point.y / Screen.height) * 1080, 270, 780);
            Label(new Rect(x-55,y-30,110,70), "◆\n" + Vector3.Distance(director.player.transform.position, target.position).ToString("0") + " m", body, amber, TextAnchor.MiddleCenter);
        }
        void MiniMap()
        {
            if(island!=null)
            {
                Rect worldMap=new Rect(42,727,195,292);
                island.DrawMap(worldMap,director.player.transform.position,director.ObjectiveTarget,false);
                string tier=director.player.transform.position.y>island.baseElevation+4.5f?"TIER 3":
                    director.player.transform.position.y>island.baseElevation+2f?"TIER 2":"GROUND";
                Label(new Rect(42,694,320,28),"ALCATRAZ  /  "+tier+"  /  HOLD M",small,amber);
                return;
            }
            Rect map = new Rect(42,727,270,292); Panel(map, new Color(.015f,.02f,.026f,.94f));
            Label(new Rect(46,694,320,28), director.player.transform.position.y > 2.7f ? "PRISON  /  UPPER GALLERY" : "PRISON  /  GROUND FLOOR", small, amber);
            Rect inside = new Rect(54,743,246,263);
            MapArea(inside,20,44,10,40,new Color(.17f,.21f,.23f),"");
            MapArea(inside,18,27,-30,12.5f,new Color(.18f,.23f,.27f),"");
            MapArea(inside,-11.5f,11.5f,-30,4,new Color(.24f,.29f,.34f),"B / C");
            MapArea(inside,-18.2f,18.2f,6,40,new Color(.24f,.31f,.27f),"YARD");
            MapArea(inside,28,36,-26.5f,-10.5f,new Color(.35f,.24f,.22f),"ISO");
            MapArea(inside,23,37,-5.5f,3.5f,new Color(.29f,.26f,.37f),"VISITS");
            MapArea(inside,25,37,28,36,new Color(.43f,.33f,.22f),"MESS");
            MapArea(inside,31.5f,40.5f,13.5f,20.5f,new Color(.24f,.37f,.39f),"WASH");
            MapArea(inside,10,16.4f,29.8f,35.4f,new Color(.41f,.35f,.26f),"");
            DrawDot(inside, director.player.transform.position, Color.white, 7);
            if (director.ObjectiveTarget != null) DrawDot(inside, director.ObjectiveTarget.position, amber, 8);
        }
        void MapArea(Rect map,float x0,float x1,float z0,float z1,Color color,string text)
        {
            Rect area = new Rect(map.x+Mathf.InverseLerp(-27,46,x0)*map.width,
                map.y+(1-Mathf.InverseLerp(-34,44,z1))*map.height,
                (x1-x0)/73f*map.width,(z1-z0)/78f*map.height);
            Panel(area,color);
            if (!string.IsNullOrEmpty(text)) Label(area,text,new GUIStyle(small) { fontSize = 14 },Color.white,TextAnchor.MiddleCenter);
        }
        static void DrawDot(Rect map, Vector3 position, Color color, float size)
        {
            float x = map.x + Mathf.InverseLerp(-27,46,position.x) * map.width;
            float y = map.y + (1-Mathf.InverseLerp(-34,44,position.z)) * map.height;
            Panel(new Rect(x-size/2,y-size/2,size,size),color);
        }
        void Banner()
        {
            Color c = director.BannerFailed ? red : green;
            Panel(new Rect(0,354,1920,164), new Color(0,0,0,.81f));
            Panel(new Rect(0,515,1920,3), c);
            Label(new Rect(140,365,1640,85), director.Banner, hero, c);
            Label(new Rect(220,462,1480,38), director.BannerDetail, body, Color.white, TextAnchor.MiddleCenter);
        }
        void SleepClock()
        {
            float progress = Mathf.Clamp01(director.State.sleepSeconds / 60f);
            int hours = Mathf.Min(24, Mathf.FloorToInt(progress * 24));
            Panel(new Rect(665,275,590,290), new Color(.02f,.026f,.03f,.9f));
            Label(new Rect(700,300,520,40), "SOLITARY CONFINEMENT", title, amber, TextAnchor.MiddleCenter);
            Label(new Rect(700,362,520,80), $"{hours:00}:00 / 24:00", hero, Color.white);
            Panel(new Rect(720,477,480,6), new Color(1,1,1,.2f)); Panel(new Rect(720,477,480*progress,6), amber);
            Label(new Rect(700,510,520,32), $"ASLEEP  |  {Mathf.CeilToInt(60-director.State.sleepSeconds)} SECONDS LEFT", small, Color.white, TextAnchor.MiddleCenter);
        }
        void Phone()
        {
            Panel(new Rect(1360,400,445,590), new Color(.02f,.03f,.045f,.98f));
            Panel(new Rect(1390,430,385,90), new Color(.11f,.24f,.3f));
            Label(new Rect(1410,446,340,60), "BLUE MERIDIAN\nSECURE CONTACTS", body);
            Label(new Rect(1400,555,370,280), "MALIK REED — Gang leader\nNIKO SERRIN — Yard contact\n\n" +
                (director.State.escapeAgreement ? "MALIK: Find enough cooperation and we leave together. Six days."
                : "MALIK: Keep the phone hidden. We will be in touch."), body);
            Label(new Rect(1400,902,370,50), "[P / D-pad right] CLOSE", small, amber);
        }
        void Menu()
        {
            Blackstone.Foundation.PrisonMenuTheme.Frame(1920,1080,"ALCATRAZ\nISLAND","THE PRISONER  /  CHAPTER 01",false);
            if(settings){SettingsPanel();return;}
            if(Blackstone.Foundation.PrisonMenuTheme.Navigation(0,"01   Continue checkpoint",director.CanContinue))director.StartSession(true);
            if(Blackstone.Foundation.PrisonMenuTheme.Navigation(1,"02   New game"))director.StartSession(false);
            if(Blackstone.Foundation.PrisonMenuTheme.Navigation(2,"03   Settings"))
            {sensitivity=director.cameraRig.sensitivity;invert=director.cameraRig.invertY;fullscreen=Screen.fullScreen;settings=true;}
            if(Blackstone.Foundation.PrisonMenuTheme.Navigation(3,"04   Quit"))Application.Quit();
            Blackstone.Foundation.PrisonMenuTheme.Text(new Rect(750,235,950,32),"ELIAS VALE  /  INMATE B-04",true);
            Blackstone.Foundation.PrisonMenuTheme.Hero(new Rect(750,310,1050,100),"The prison has a rhythm.",68);
            Blackstone.Foundation.PrisonMenuTheme.Text(new Rect(750,440,850,180),"Learn it. Build alliances. Find the gaps. Your first days inside Alcatraz are the beginning of your escape.");
            Blackstone.Foundation.PrisonMenuTheme.Text(new Rect(750,745,930,80),"CONTROLLER   X: Continue  ·  Y: New game",true);
        }
        void Pause()
        {
            if(pauseMenu!=null&&pauseMenu.Draw()){settings=false;director.ReturnToMenu();}
        }
        void SettingsPanel()
        {
            Panel(new Rect(850,225,975,765), new Color(.026f,.037f,.048f,.98f));
            Label(new Rect(886,241,900,55), "SETTINGS", title, amber);
            Label(new Rect(886,314,220,45), "Quality", body);
            quality = GUI.SelectionGrid(new Rect(1130,314,644,45), quality, new[] {"LOW","MEDIUM","HIGH","ULTRA"}, 4);
            Label(new Rect(886,374,220,45), "Resolution", body);
            resolution = GUI.SelectionGrid(new Rect(1130,374,644,45), resolution, new[] {"1280 × 720","1920 × 1080","2560 × 1440"}, 3);
            fullscreen = GUI.Toggle(new Rect(1130,435,290,36), fullscreen, " Fullscreen");
            vsync = GUI.Toggle(new Rect(1470,435,260,36), vsync, " VSync");
            sensitivity = Slider("Camera sensitivity", sensitivity, .025f,.25f, 486);
            invert = GUI.Toggle(new Rect(1130,545,420,36), invert, " Invert camera Y");
            director.audioBus.master = Slider("Master volume", director.audioBus.master,0,1,596);
            director.audioBus.effects = Slider("Sound effects", director.audioBus.effects,0,1,646);
            director.audioBus.dialogue = Slider("Dialogue", director.audioBus.dialogue,0,1,696);
            director.audioBus.music = Slider("Music", director.audioBus.music,0,1,746);
            if (GUI.Button(new Rect(1130,849,644,60), "Apply & back", button)) { ApplySettings(true); settings = false; }
            Label(new Rect(886,930,875,38), "Quality also controls shadows, anti-aliasing and texture resolution.", small);
        }
        float Slider(string label, float value, float min, float max, float y)
        {
            Label(new Rect(886,y,250,35), label, body);
            return GUI.HorizontalSlider(new Rect(1150,y+15,610,24),value,min,max);
        }
        public int GraphicsPreset=>quality;
        public void SetGraphicsPreset(int preset)
        {
            quality=preset;sensitivity=director.cameraRig.sensitivity;invert=director.cameraRig.invertY;
            ApplySettings(false);
        }
        void ApplySettings(bool applyDisplay)
        {
            quality = Mathf.Clamp(quality,0,3);
            director.cameraRig.sensitivity = sensitivity; director.cameraRig.invertY = invert;
            QualitySettings.vSyncCount = vsync ? 1 : 0;
            QualitySettings.globalTextureMipmapLimit = quality == 0 ? 2 : quality == 1 ? 1 : 0;
            if (runtimePipeline != null)
            {
                runtimePipeline.shadowDistance = new[] {25f,45f,70f,95f}[quality];
                runtimePipeline.msaaSampleCount = new[] {1,2,2,4}[quality];
                runtimePipeline.renderScale = new[] {.8f,1f,1f,1f}[quality];
                runtimePipeline.shadowCascadeCount = quality == 0 ? 1 : quality == 1 ? 2 : 4;
            }
            if (applyDisplay)
            {
                int[] widths = {1280,1920,2560}; int[] heights = {720,1080,1440};
                Screen.SetResolution(widths[resolution],heights[resolution],fullscreen ? FullScreenMode.FullScreenWindow : FullScreenMode.Windowed);
            }
            PlayerPrefs.SetInt("Blackstone.Quality",quality); PlayerPrefs.SetFloat("Blackstone.Sensitivity",sensitivity);
            PlayerPrefs.SetInt("Blackstone.Invert",invert ? 1 : 0); PlayerPrefs.SetInt("Blackstone.VSync",vsync ? 1 : 0);
            PlayerPrefs.SetFloat("Blackstone.Master",director.audioBus.master); PlayerPrefs.SetFloat("Blackstone.Effects",director.audioBus.effects);
            PlayerPrefs.SetFloat("Blackstone.Dialogue",director.audioBus.dialogue); PlayerPrefs.SetFloat("Blackstone.Music",director.audioBus.music);
            PlayerPrefs.Save();
        }
        static void Panel(Rect rect, Color color)
        { Color old = GUI.color; GUI.color = color; GUI.DrawTexture(rect,Texture2D.whiteTexture); GUI.color = old; }
        static void Label(Rect rect, string text, GUIStyle style, Color? color = null, TextAnchor? alignment = null)
        {
            Color old = style.normal.textColor; TextAnchor a = style.alignment;
            if (color.HasValue) style.normal.textColor = color.Value;
            if (alignment.HasValue) style.alignment = alignment.Value;
            GUI.Label(rect,text,style); style.normal.textColor = old; style.alignment = a;
        }
        static string FormatTime(float seconds) => $"{(int)seconds/60:00}:{(int)seconds%60:00}";
        void OnDestroy()
        {
            if (runtimePipeline != null)
            { GraphicsSettings.defaultRenderPipeline = originalPipeline; QualitySettings.renderPipeline = originalPipeline; Destroy(runtimePipeline); }
        }
    }
}
