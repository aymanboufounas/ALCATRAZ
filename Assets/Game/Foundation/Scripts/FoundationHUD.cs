using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.SceneManagement;
using DesertShift.Interaction;

namespace Blackstone.Foundation
{
    public sealed class FoundationHUD : MonoBehaviour
    {
        public string worldTitle="BLACKSTONE\nISLAND";
        public string storyScene="SC_BlackstoneStory_Upgraded";
        FoundationBootstrap foundation;
        FoundationConversations conversations;
        PlayerInteractor interactor;
        bool title=true;
        Blackstone.Supplied.SuppliedIslandWorld suppliedWorld;
        readonly Blackstone.Supplied.SuppliedWeaponCards weaponCards=new Blackstone.Supplied.SuppliedWeaponCards();
        GUIStyle large,heading,text,small,button;
        void Start()
        {
            foundation=GetComponent<FoundationBootstrap>();conversations=GetComponent<FoundationConversations>();
            suppliedWorld=GetComponent<Blackstone.Supplied.SuppliedIslandWorld>();
            if(foundation.Player!=null)interactor=foundation.Player.GetComponent<PlayerInteractor>();
            if(foundation.Input!=null)
            {foundation.Input.ResumeOnClick=false;foundation.Input.PauseEnabled=true;foundation.Input.SetGameplayBlocked(true);foundation.Input.Capture(false);}
        }
        void Enter()
        {
            if(foundation.Status!="Ready")return;
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
        void OnGUI()
        {
            if(foundation==null)return;
            if(text==null)
            {
                text=new GUIStyle(GUI.skin.label){fontSize=22,wordWrap=true};
                small=new GUIStyle(text){fontSize=17};heading=new GUIStyle(text){fontSize=28,fontStyle=FontStyle.Bold};
                large=new GUIStyle(heading){fontSize=64};button=new GUIStyle(GUI.skin.button){fontSize=22};
            }
            var old=GUI.matrix;GUI.matrix=Matrix4x4.TRS(Vector3.zero,Quaternion.identity,new Vector3(Screen.width/1600f,Screen.height/900f,1));
            bool paused=foundation.Input==null||!foundation.Input.IsCaptured;
            if(title||paused)
            {
                Panel(new Rect(0,0,1600,900),new Color(.015f,.023f,.027f,.77f));
                Panel(new Rect(90,100,640,710),new Color(.025f,.045f,.055f,.94f));
                GUI.Label(new Rect(130,128,550,40),"THE SILENT BLUEPRINT",heading);
                GUI.Label(new Rect(125,188,570,155),title?worldTitle:"PAUSED",large);
                GUI.Label(new Rect(130,365,540,80),"Elias Vale · Inmate B-04\nA prisoner with a reason to escape.",text);
                if(foundation.Status!="Ready")GUI.Label(new Rect(130,455,530,90),foundation.Status??"Preparing characters...",text);
                else
                {
                    if(GUI.Button(new Rect(130,470,530,58),title?(suppliedWorld!=null?"Explore Alcatraz  [Enter / A]":"Enter the prison  [Enter / A]"):"Resume  [Esc / A]",button))
                    {if(title)Enter();else foundation.Input.Capture(true);}
                    if(Application.CanStreamedLevelBeLoaded(storyScene)&&GUI.Button(new Rect(130,541,530,48),"Play Chapter 01",button))
                    {Time.timeScale=1;SceneManager.LoadScene(storyScene);}
                    var audio=FoundationAudio.Instance;
                    if(audio!=null)
                    {
                        GUI.Label(new Rect(130,607,220,35),"Master volume",small);audio.master=GUI.HorizontalSlider(new Rect(350,620,300,25),audio.master,0,1);
                        GUI.Label(new Rect(130,650,220,35),"Effects / footsteps",small);audio.effects=GUI.HorizontalSlider(new Rect(350,663,300,25),audio.effects,0,1);
                    }
                    if(foundation.CameraRig!=null)
                    {GUI.Label(new Rect(130,693,220,35),"Camera sensitivity",small);foundation.CameraRig.sensitivity=GUI.HorizontalSlider(new Rect(350,706,300,25),foundation.CameraRig.sensitivity,.035f,.18f);}
                }
                Panel(new Rect(810,245,660,435),new Color(.025f,.045f,.055f,.85f));
                GUI.Label(new Rect(850,275,550,45),"PRISON ROUTINE",heading);
                GUI.Label(new Rect(850,342,550,300),"WASD / Left stick   Move\nShift / L3   Run     ·     Alt   Slow walk\nCtrl / B   Crouch     ·     Space / A   Jump\nMouse / Right stick   Camera\nE / X   Doors     ·     Q / RB   Shoulder\n1–5 / D-pad left   Equipment\nRMB / LT   Aim     ·     LMB / RT   Use\nR / Y   Reload     ·     Esc / Start   Pause",text);
            }
            else
            {
                Panel(new Rect(25,22,455,120),new Color(.015f,.03f,.035f,.88f));
                GUI.Label(new Rect(43,32,420,28),"GOAL: ESCAPE THE PRISON",heading);
                GUI.Label(new Rect(43,70,420,28),suppliedWorld!=null?"Find the cellhouse entrance":"Explore the prison",text);
                GUI.Label(new Rect(43,107,420,23),"Prepare your route · Play Chapter 01",small);
                Panel(new Rect(1195,22,380,105),new Color(.015f,.03f,.035f,.88f));
                GUI.Label(new Rect(1212,33,350,30),"INMATE ELIAS VALE  /  B-04",small);
                GUI.Label(new Rect(1212,67,350,30),"ALCATRAZ ISLAND",heading);
                var equipment=foundation.PlayerEquipment;
                if(equipment!=null)
                {
                    var state=equipment.State;string status=state.Equipped.ToString().ToUpperInvariant();
                    if(state.IsFirearm)status+="   "+state.Magazine+" / "+state.Reserve;
                    weaponCards.Draw(equipment);
                    Panel(new Rect(1200,790,375,80),new Color(.015f,.03f,.035f,.8f));
                    GUI.Label(new Rect(1220,804,350,33),status,heading);
                    GUI.Label(new Rect(1220,842,345,25),state.Reloading?"Reloading...":"Practice hits  "+equipment.Hits,small);
                    GUI.color=Time.time<equipment.HitMarkerUntil?new Color(.45f,1,.5f):Color.white;
                    GUI.DrawTexture(new Rect(792,449,16,2),Texture2D.whiteTexture);GUI.DrawTexture(new Rect(799,442,2,16),Texture2D.whiteTexture);GUI.color=Color.white;
                }
                GUI.Label(new Rect(390,861,805,28),"WASD Move   Shift Run   RMB Aim   LMB Use   R Reload   1–5 Equipment",small);
                if(suppliedWorld!=null&&suppliedWorld.ChapterGate!=null&&foundation.Player!=null&&Vector3.Distance(foundation.Player.transform.position,suppliedWorld.ChapterGate.position)<3.4f)
                    GUI.Label(new Rect(455,739,715,43),"E / X   ENTER CELLHOUSE · CHAPTER 01",heading);
                if(interactor!=null&&!string.IsNullOrEmpty(interactor.CurrentPrompt))
                    GUI.Label(new Rect(480,740,660,45),interactor.CurrentPrompt,heading);
                if(conversations!=null&&!string.IsNullOrEmpty(conversations.Subtitle))
                {
                    Panel(new Rect(370,788,770,92),new Color(.015f,.03f,.035f,.88f));
                    GUI.Label(new Rect(390,800,725,25),conversations.Speaker,small);
                    GUI.Label(new Rect(390,828,725,50),conversations.Subtitle,text);
                }
            }
            GUI.matrix=old;
        }
        static void Panel(Rect rect,Color color)
        {var old=GUI.color;GUI.color=color;GUI.DrawTexture(rect,Texture2D.whiteTexture);GUI.color=old;}
    }
}
