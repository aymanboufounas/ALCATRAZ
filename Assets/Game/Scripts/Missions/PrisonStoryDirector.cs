using System;
using System.Collections;
using UnityEngine;
using DesertShift.Player;
using DesertShift.Camera;
using DesertShift.Interaction;
using Blackstone.Actors;
using Blackstone.Audio;
using Blackstone.Interaction;
using Blackstone.Save;
using Blackstone.Activities;

namespace Blackstone.Story
{
    [Serializable] public sealed class DialogueLine
    { public string id, speaker, text; public float seconds = 3; }
    [Serializable] public sealed class DialogueScene
    { public string id; public DialogueLine[] lines; }
    [Serializable] public sealed class DialogueBook { public DialogueScene[] scenes; }
    [Serializable] public sealed class StoryShot
    { public string id; public Transform camera, focus; }

    [DefaultExecutionOrder(25)]
    public sealed class PrisonStoryDirector : MonoBehaviour
    {
        [Header("Existing player systems")]
        public PlayerMovement player;
        public PlayerInputHandler input;
        public PlayerInteractor interactor;
        public ThirdPersonCameraController cameraRig;
        public UnityEngine.Camera mainCamera;
        public PrisonAudio audioBus;
        public PrisonActor playerActor, niko, leader, rival, guard, brother, tattooist;
        [Header("Chapter locations")]
        public Transform cellSpawn, yardSpawn, solitarySpawn, visitSpawn, sleepPosition;
        public Transform cellDoor, solitaryDoor, playerVisual;
        // Optional map placements preserve the classic chapter's fallback coordinates.
        public Transform guardIncidentPoint, guardIsolationPoint, rivalIsolationPoint;
        public StoryInteractable[] targets;
        public StoryShot[] shots;
        public GameObject droppedKnife, stashedKnife, tattooMark, phoneProp;
        public GameObject nikoHeldKnife, concealKnifeProp;
        public Transform nikoHand;
        [Header("Pacing")]
        [Min(1)] public float fightAtSeconds = 240;
        // One game day is exactly one real minute while sleeping; pausing stops both clocks.
        public const float IsolationSeconds = 60;
        public PrisonStoryState State { get; private set; } = new PrisonStoryState();
        public bool MainMenu { get; private set; } = true;
        public bool Busy { get; private set; }
        public bool Letterbox { get; private set; }
        public bool PhoneOpen { get; private set; }
        public string Speaker { get; private set; }
        public string Subtitle { get; private set; }
        public string Banner { get; private set; }
        public string BannerDetail { get; private set; }
        public bool BannerFailed { get; private set; }
        public float Fade { get; private set; }
        public string Toast { get; private set; }
        public bool CanUseYardActivity => !MainMenu && !Busy && !PhoneOpen && !State.missed
            && ((State.stage >= StoryStage.Socialize && State.stage < StoryStage.KnifeOpportunity)
            || (State.stage >= StoryStage.Recognition && State.stage < StoryStage.RivalChallenge)
            || State.stage >= StoryStage.EscapeMeeting);
        public bool CanContinue => PrisonSave.TryLoad(out var checkpoint);
        public string StartupProblem
        {
            get
            {
                var foundation=FindFirstObjectByType<Blackstone.Foundation.FoundationBootstrap>();
                if(foundation==null)return null;
                return foundation.Status=="Ready"?null:foundation.Status??"Preparing the prisoner and third-person camera…";
            }
        }
        DialogueBook dialogueBook;
        float bannerUntil, toastUntil, nextSave, nextRivalStrike, nextPlayerStrike, nextPhoneRing;
        Vector3 visualPosition;
        Quaternion visualRotation;
        Vector3 knifeHome;
        Quaternion knifeRotation;
        bool sessionStarted, wakePending;

        void Start()
        {
            var text = Resources.Load<TextAsset>("Blackstone/story-dialogue");
            if (text != null) dialogueBook = JsonUtility.FromJson<DialogueBook>(text.text);
            if (player == null || input == null || cameraRig == null || mainCamera == null || audioBus == null)
            { Debug.LogError("Blackstone chapter references are incomplete. Use Blackstone > Validate Chapter."); enabled = false; return; }
            visualPosition = playerVisual.localPosition; visualRotation = playerVisual.localRotation;
            knifeHome = droppedKnife.transform.position; knifeRotation = droppedKnife.transform.rotation;
            input.ResumeOnClick = false;
            input.PauseEnabled = false; input.SetGameplayBlocked(true); input.Capture(false);
            UpdateWorld();
            if (Blackstone.Foundation.FoundationPlayerVitals.ConsumeRestart(UnityEngine.SceneManagement.SceneManager.GetActiveScene().name))
            {
                StartSession(CanContinue);
                player.GetComponent<Blackstone.Foundation.FoundationDamageable>()?.Restore(100);
            }
        }
        public void StartSession(bool resume, int slot=0)
        {
            string startupProblem=StartupProblem;
            if(startupProblem!=null){Notice(startupProblem);Debug.LogError("The chapter cannot start: "+startupProblem);return;}
            PrisonCheckpoint saved=null;
            bool loaded=resume&&PrisonSave.TryLoad(out saved,slot);
            if(resume&&!loaded){Notice("No valid checkpoint is available in this slot.");return;}
            StopAllCoroutines(); cameraRig.SetCinematic(false); audioBus.StopDialogue();
            ResetVisual(); Busy = Letterbox = PhoneOpen = wakePending = false;
            Speaker = Subtitle = Banner = Toast = null; Fade = 0;
            foreach (var actor in new[] { niko, leader, rival, guard, brother, tattooist })
                if (actor != null) actor.ResetActor();
            foreach(var actor in FindObjectsByType<PrisonActor>(FindObjectsSortMode.None)){actor.Suspended=false;actor.SpeakTo(null,false);}
            playerActor.SetPose(ActorPose.Idle);
            droppedKnife.transform.SetPositionAndRotation(knifeHome, knifeRotation);
            if (nikoHeldKnife != null) nikoHeldKnife.SetActive(false);
            if (concealKnifeProp != null) concealKnifeProp.SetActive(false);
            State = new PrisonStoryState();
            if (loaded) State = saved.story;
            MainMenu = false; sessionStarted = true;
            player.GetComponent<Blackstone.Foundation.FoundationDamageable>()?.Restore(loaded ? saved.health : 100);
            input.PauseEnabled = true; input.SetGameplayBlocked(false); input.Capture(true);
            Transform spawn = SpawnForStage();
            player.Teleport(loaded && !SpecialLocation(State.stage) ? saved.position : spawn.position);
            player.transform.rotation = Quaternion.Euler(0, loaded ? saved.yaw : spawn.eulerAngles.y, 0);
            cameraRig.SnapBehind(player.transform.eulerAngles.y);
            UpdateWorld();
            if (State.missed) ShowMissed();
            else if (State.stage == StoryStage.CellIntro) StartCoroutine(Intro());
            else if (State.stage == StoryStage.Arrest) StartCoroutine(ArrestRoutine());
            else if (State.stage == StoryStage.SolitarySleeping) StartSleeping();
            else if (State.stage == StoryStage.DoorKnock) StartCoroutine(WakeRoutine());
            if (!loaded) SaveNow();
            nextSave = Time.time + 10;
        }
        public void ReturnToMenu()
        {
            if (PrisonPokerTable.Active != null) PrisonPokerTable.Active.Close();
            SaveNow(); StopAllCoroutines(); ResetVisual();
            audioBus.StopDialogue(); audioBus.Tension(false); cameraRig.SetCinematic(false);
            Busy = Letterbox = PhoneOpen = false; Subtitle = Speaker = null; Fade = 0;
            MainMenu = true; input.PauseEnabled = false; input.SetGameplayBlocked(true); input.Capture(false);
        }
        void Update()
        {
            if (MainMenu || player.GetComponent<Blackstone.Foundation.FoundationPlayerVitals>()?.Failed == true) return;
            if (Time.time > bannerUntil && !State.missed) Banner = null;
            if (Time.time > toastUntil) Toast = null;
            if (State.missed)
            {
                if (input.IsCaptured && input.RetryPressed) StartCoroutine(RetryRoutine());
                return;
            }
            if (input.PhonePressed && !Busy && State.phone && PrisonPokerTable.Active == null)
            {
                if (State.stage == StoryStage.PhoneCall) Interact(StoryTarget.Phone);
                else { PhoneOpen = !PhoneOpen; input.SetGameplayBlocked(PhoneOpen); audioBus.Play(audioBus.phoneClick); }
            }
            if (PhoneOpen) return;
            // Social routine and sleep clocks continue during their own scenes, never while paused.
            float delta = State.stage == StoryStage.KnifeOpportunity && Busy ? 0 : Time.deltaTime;
            StorySignal signal = State.Tick(delta, fightAtSeconds, IsolationSeconds);
            if (signal == StorySignal.IncidentReady && !Busy
                && Vector3.Distance(player.transform.position, yardSpawn.position) < 19)
                StartCoroutine(IncidentRoutine(false));
            if (signal == StorySignal.Missed) { SaveNow(); ShowMissed(); }
            if (signal == StorySignal.Released && !wakePending)
            { wakePending = true; SaveNow(); StartCoroutine(WakeRoutine()); }
            if (State.stage == StoryStage.Arrest && !Busy) StartCoroutine(ArrestRoutine());
            if (State.stage == StoryStage.RivalFight && !Busy && input.CanControl) UpdateBrawl();
            if (State.stage == StoryStage.PhoneCall && !Busy && Time.time >= nextPhoneRing)
            { audioBus.Play(audioBus.phoneRing, .7f); nextPhoneRing = Time.time + 6; }
            if (!Busy && Time.time >= nextSave) { SaveNow(); nextSave = Time.time + 10; }
        }
        void UpdateBrawl()
        {
            if (Vector3.Distance(player.transform.position, yardSpawn.position) > 13)
            { Teleport(yardSpawn); Notice("The guards keep the fighters inside the yard."); }
            Vector3 d = player.transform.position - rival.transform.position; d.y = 0;
            if (d.sqrMagnitude > .01f) rival.transform.rotation = Quaternion.LookRotation(d);
            if (d.magnitude > 1.6f && d.magnitude < 12)
                rival.transform.position += d.normalized * Mathf.Min(d.magnitude - 1.6f, 1.4f * Time.deltaTime);
            if (d.magnitude < 2 && Time.time > nextRivalStrike)
            {
                rival.SetPose(ActorPose.Punch, .6f); nextRivalStrike = Time.time + 1.7f;
                bool blocked = Physics.Linecast(rival.transform.position + Vector3.up * 1.3f,
                    player.transform.position + Vector3.up * 1.3f, 1, QueryTriggerInteraction.Ignore);
                if (!blocked)
                {
                    player.GetComponent<Blackstone.Foundation.FoundationDamageable>()?.Damage(12,
                        player.transform.position + Vector3.up, d.normalized * 3);
                    audioBus.Play(audioBus.punch, .25f);
                }
                if(player.GetComponent<Blackstone.Foundation.FoundationPlayerVitals>()?.Failed == true)return;
            }
            if (input.AttackPressed && Time.time > nextPlayerStrike)
            {
                nextPlayerStrike = Time.time + .55f; playerActor.SetPose(ActorPose.Punch, .45f);
                bool clear = false;
                if (d.magnitude <= 2.4f)
                {
                    clear = !Physics.Linecast(player.transform.position + Vector3.up * 1.4f,
                        rival.transform.position + Vector3.up * 1.4f, out var hit, ~(1 << 8), QueryTriggerInteraction.Ignore)
                        || hit.collider.transform.IsChildOf(rival.transform);
                }
                if (clear)
                {
                    rival.SetPose(ActorPose.Flinch, .45f); audioBus.Play(audioBus.punch);
                    State.TryAct(StoryAction.StrikeRival); SaveNow();
                }
                else Notice("Get closer to the rival. The knife stays hidden in your cell.");
            }
        }
        public string PromptFor(StoryTarget target)
        {
            if (MainMenu || Busy || State.missed || PhoneOpen) return null;
            switch (State.stage)
            {
                case StoryStage.CellIntro: return target == StoryTarget.CellDoor ? "Join the scheduled yard period" : null;
                case StoryStage.Socialize:
                    if (target == StoryTarget.Reader && (State.acquaintances & 1) == 0) return "Introduce yourself to Tomas";
                    if (target == StoryTarget.Cook && (State.acquaintances & 2) == 0) return "Help Samir at the meal cart";
                    if (target == StoryTarget.Fixer && (State.acquaintances & 4) == 0) return "Speak to the workshop contact";
                    if (target == StoryTarget.Training) return "Practice on the training bag";
                    break;
                case StoryStage.KnifeOpportunity: return target == StoryTarget.DroppedKnife ? "Conceal the dropped knife" : null;
                case StoryStage.Recognition: return target == StoryTarget.Niko ? "Talk to Niko" : null;
                case StoryStage.GangOath: return target == StoryTarget.Leader ? "Meet Malik, the gang leader" : null;
                case StoryStage.Tattoo: return target == StoryTarget.Tattooist ? "Receive the Blue Meridian tattoo" : null;
                case StoryStage.StashKnife: return target == StoryTarget.CellStash ? "Hide the knife inside Cell B-04" : null;
                case StoryStage.ReceivePhone: return target == StoryTarget.Phone ? "Accept the gang's phone" : null;
                case StoryStage.PhoneCall: return target == StoryTarget.Phone ? "Answer the phone [P / D-pad right]" : null;
                case StoryStage.RivalChallenge: return target == StoryTarget.Rival ? "Confront the Iron Rooks rival" : null;
                case StoryStage.Solitary: return target == StoryTarget.SolitaryBed ? "Sleep through 24 hours of isolation" : null;
                case StoryStage.DoorKnock: return target == StoryTarget.SolitaryDoor ? "Answer the guard and leave for visitation" : null;
                case StoryStage.VisitBrother: return target == StoryTarget.Brother ? "Pick up the visitation receiver" : null;
                case StoryStage.ReturnToCell: return target == StoryTarget.Reflection ? "Sit down and think about your father" : null;
                case StoryStage.EscapeMeeting: return target == StoryTarget.Leader ? "Discuss escaping before next week" : null;
            }
            return null;
        }
        public void Interact(StoryTarget target)
        {
            if (string.IsNullOrEmpty(PromptFor(target))) return;
            if (target == StoryTarget.Training)
            { playerActor.SetPose(ActorPose.Punch, .5f); audioBus.Play(audioBus.punch, .5f); Notice("Stay sharp. Yard time ends soon."); return; }
            if (target == StoryTarget.DroppedKnife)
            {
                if (State.TryAct(StoryAction.ConcealKnife))
                {
                    audioBus.Play(audioBus.clothHide); UpdateWorld(); SaveNow();
                    ShowBanner("Mission completed", "FIRST RESPECT  |  Niko's knife is safe. Respect +15", false);
                    StartCoroutine(ConcealRoutine());
                }
                return;
            }
            if (target == StoryTarget.SolitaryBed) { if (State.TryAct(StoryAction.Sleep)) { SaveNow(); StartSleeping(); } return; }
            StartCoroutine(InteractionRoutine(target));
        }
        IEnumerator InteractionRoutine(StoryTarget target)
        {
            BeginCinematic(); StoryAction action = StoryAction.LeaveCell;
            switch (target)
            {
                case StoryTarget.CellDoor:
                    audioBus.Play(audioBus.metalDoor); yield return Wait(.8f); action = StoryAction.LeaveCell; break;
                case StoryTarget.Reader: yield return Say("reader", "reader"); action = StoryAction.MeetReader; break;
                case StoryTarget.Cook: yield return Say("cook", "cook"); action = StoryAction.MeetCook; break;
                case StoryTarget.Fixer: yield return Say("fixer", "fixer"); action = StoryAction.MeetFixer; break;
                case StoryTarget.Niko: yield return Say("thanks", "niko"); action = StoryAction.ThankNiko; break;
                case StoryTarget.Leader:
                    if (State.stage == StoryStage.EscapeMeeting)
                    { yield return Say("escape_plan", "leader"); action = StoryAction.ProposeEscape; }
                    else { yield return Say("gang_oath", "leader"); action = StoryAction.JoinGang; }
                    break;
                case StoryTarget.Tattooist:
                    tattooist.SetPose(ActorPose.Tattoo); audioBus.Play(audioBus.tattooBuzz);
                    yield return Say("tattoo", "tattoo"); tattooist.SetPose(ActorPose.Idle);
                    action = StoryAction.ReceiveTattoo; break;
                case StoryTarget.CellStash:
                    audioBus.Play(audioBus.clothHide); yield return Say("stash", "cell"); action = StoryAction.StoreKnife; break;
                case StoryTarget.Phone:
                    if (State.stage == StoryStage.PhoneCall)
                    { audioBus.Play(audioBus.phoneClick); yield return Say("phone_call", "niko"); action = StoryAction.AnswerPhone; }
                    else { yield return Say("phone_gift", "niko"); action = StoryAction.AcceptPhone; }
                    break;
                case StoryTarget.Rival:
                    yield return Say("rival", "yard"); action = StoryAction.ChallengeRival; break;
                case StoryTarget.SolitaryDoor:
                    yield return Say("guard_visit", "door"); action = StoryAction.FollowGuard; break;
                case StoryTarget.Brother:
                    brother.SetPose(ActorPose.Cry); audioBus.Play(audioBus.sob, .45f);
                    yield return Say("brother_visit", "visit"); action = StoryAction.SpeakToBrother; break;
                case StoryTarget.Reflection:
                    yield return Say("reflection", "cell"); action = StoryAction.ReflectInCell; break;
            }
            bool changed = State.TryAct(action);
            if (changed && (target == StoryTarget.SolitaryDoor || target == StoryTarget.Brother))
            {
                audioBus.Play(audioBus.metalDoor); yield return FadeTo(1, .55f);
                Teleport(SpawnForStage()); UpdateWorld(); yield return FadeTo(0, .7f);
            }
            UpdateWorld(); EndCinematic(); SaveNow();
            if (changed && State.stage == StoryStage.RivalChallenge)
                ShowBanner("Mission completed", "TRUST LINE  |  Phone acquired. Gang contact unlocked.", false);
            if (changed && State.stage == StoryStage.ReceivePhone) Notice("Knife secured beneath your mattress. Go back to Niko.");
            if (changed && State.stage == StoryStage.ChapterComplete)
                ShowBanner("Mission completed", "ESCAPE AGREEMENT  |  Six days left. Chapter 01 complete.", false);
        }
        IEnumerator Intro()
        { BeginCinematic(); yield return Say("intro", "cell"); EndCinematic(); }
        IEnumerator ConcealRoutine()
        {
            BeginCinematic(); audioBus.Tension(false);
            playerActor.SetPose(ActorPose.Conceal, 1.3f);
            if (concealKnifeProp != null) concealKnifeProp.SetActive(true);
            yield return Wait(1.2f);
            if (concealKnifeProp != null) concealKnifeProp.SetActive(false);
            yield return Say("conceal", "niko"); EndCinematic();
        }
        IEnumerator IncidentRoutine(bool retry)
        {
            BeginCinematic(); audioBus.Tension(true);
            Teleport(yardSpawn); niko.ResetActor(); rival.ResetActor(); guard.patrolEnabled = false;
            niko.transform.rotation = Quaternion.LookRotation(rival.transform.position - niko.transform.position);
            rival.transform.rotation = Quaternion.LookRotation(niko.transform.position - rival.transform.position);
            niko.SetPose(ActorPose.Punch); rival.SetPose(ActorPose.Punch);
            if (nikoHeldKnife != null) nikoHeldKnife.SetActive(true);
            yield return Shot("yard");
            Speaker = "NIKO"; Subtitle = "Back off. You don't own this yard.";
            audioBus.Speak("incident_niko"); audioBus.Play(audioBus.punch);
            yield return Wait(3.1f); niko.SetPose(ActorPose.Flinch, 1); rival.SetPose(ActorPose.Idle);
            if (nikoHeldKnife != null) nikoHeldKnife.SetActive(false);
            yield return DropKnife();
            Speaker = "GUARD"; Subtitle = "Break it up! Hands where I can see them!";
            audioBus.Speak("incident_guard"); audioBus.Play(audioBus.whistle);
            yield return Wait(3.2f); niko.SetPose(ActorPose.Idle); rival.SetPose(ActorPose.Idle);
            if (!retry) State.BeginIncident(fightAtSeconds);
            UpdateWorld();
            guard.transform.position = MapPoint(guardIncidentPoint, new Vector3(6, .02f, 32));
            Notice("Niko dropped a knife. Hide it before the guard reaches him!");
            EndCinematic(); SaveNow();
        }
        IEnumerator DropKnife()
        {
            droppedKnife.SetActive(true);
            Vector3 from = nikoHand != null ? nikoHand.position : niko.transform.position + Vector3.up;
            float elapsed = 0;
            while (elapsed < .65f)
            {
                elapsed += Time.deltaTime; float t = Mathf.Clamp01(elapsed / .65f);
                droppedKnife.transform.position = Vector3.Lerp(from, knifeHome, t) + Vector3.up * (Mathf.Sin(t*Mathf.PI)*.16f);
                droppedKnife.transform.rotation = Quaternion.Slerp(Quaternion.Euler(70,0,0), knifeRotation, t);
                yield return null;
            }
            droppedKnife.transform.SetPositionAndRotation(knifeHome, knifeRotation);
            audioBus.Play(audioBus.knifeDrop);
        }
        IEnumerator RetryRoutine()
        {
            if (Busy || !State.RetryIncident()) yield break;
            Banner = null; input.SetGameplayBlocked(false);
            yield return IncidentRoutine(true);
        }
        void ShowMissed()
        {
            audioBus.Tension(false); guard.SetPose(ActorPose.Idle); guard.patrolEnabled = false;
            niko.SetPose(ActorPose.HandsUp);
            input.SetGameplayBlocked(true);
            ShowBanner("Missed", "The guard saw the knife. Niko was searched. [R / Y] Retry", true);
        }
        IEnumerator ArrestRoutine()
        {
            BeginCinematic(); playerActor.SetPose(ActorPose.HandsUp); rival.SetPose(ActorPose.HandsUp);
            guard.patrolEnabled = false; audioBus.Play(audioBus.whistle);
            yield return Say("arrest", "yard"); yield return FadeTo(1, .8f);
            State.FinishArrest(); UpdateWorld(); Teleport(solitarySpawn);
            rival.transform.position = MapPoint(rivalIsolationPoint, new Vector3(32, .02f, -14.5f));
            playerActor.SetPose(ActorPose.Idle); rival.SetPose(ActorPose.Idle);
            audioBus.Play(audioBus.metalDoor); yield return Shot("solitary"); yield return FadeTo(0, 1);
            yield return Say("isolation", "solitary"); EndCinematic(); SaveNow();
        }
        void StartSleeping()
        {
            BeginCinematic(); Teleport(sleepPosition);
            playerVisual.localPosition = visualPosition + new Vector3(0, .45f, 0);
            playerVisual.localRotation = Quaternion.Euler(0, 0, 90);
            audioBus.Tension(false); Speaker = "24 HOURS IN ISOLATION";
            Subtitle = "Elias sleeps. One minute of play represents a full day.";
            StartCoroutine(SleepShot());
        }
        IEnumerator SleepShot() { yield return Shot("solitary"); yield return FadeTo(.72f, 2); }
        IEnumerator WakeRoutine()
        {
            StopSleepOnly(); BeginCinematic(); ResetVisual(); Teleport(solitarySpawn); UpdateWorld();
            audioBus.Play(audioBus.doorKnock); yield return FadeTo(0, .8f);
            yield return Say("wake", "door"); EndCinematic(); SaveNow();
            ShowBanner("Mission completed", "YARD TROUBLE  |  24 hours served. Your brother is waiting.", false);
        }
        void StopSleepOnly() { Speaker = Subtitle = null; }
        public void YardConversation(Transform seat)
        { if (CanUseYardActivity) StartCoroutine(YardTableRoutine(seat)); }
        IEnumerator YardTableRoutine(Transform seat)
        {
            Vector3 before=player.transform.position;Quaternion rotation=player.transform.rotation;
            var avatar=player.GetComponent<Blackstone.Foundation.FoundationAvatar>();
            bool wasSeated=avatar!=null&&avatar.seated,wasExternal=player.ExternalControl;
            ActorPose beforePose=playerActor.pose;
            BeginCinematic();if(seat!=null)Teleport(seat);
            player.SetExternalControl(true);playerActor.SetPose(ActorPose.SeatedTalk);
            if(avatar!=null)avatar.seated=true;
            try { yield return Say("yard_table","reader"); }
            finally
            {
                playerActor.SetPose(beforePose);if(avatar!=null)avatar.seated=wasSeated;
                player.Teleport(before);player.transform.rotation=rotation;player.SetExternalControl(wasExternal);
                EndCinematic();
            }
        }
        PrisonActor SpeakerActor(string name)
        {
            switch(name)
            {
                case "ELIAS":return playerActor;
                case "NIKO":return niko;
                case "MALIK":return leader;
                case "THEO":return brother;
                case "GUARD":return guard;
                case "RAFI":return tattooist;
                case "IRON ROOKS":return rival;
            }
            var roles = name=="TOMAS"?StoryTarget.Reader:name=="SAMIR"?StoryTarget.Cook:StoryTarget.Fixer;
            if(targets!=null)foreach(var item in targets)if(item!=null&&item.target==roles)return item.GetComponent<PrisonActor>();
            return null;
        }
        IEnumerator Say(string sceneId, string shotId)
        {
            yield return Shot(shotId);
            DialogueScene scene = null;
            if (dialogueBook != null && dialogueBook.scenes != null)
                foreach (var item in dialogueBook.scenes) if (item.id == sceneId) { scene = item; break; }
            if (scene == null || scene.lines == null)
            { Debug.LogError("Missing dialogue scene: " + sceneId); yield break; }
            foreach (var line in scene.lines)
            {
                Speaker = line.speaker; Subtitle = line.text;
                var actor = SpeakerActor(line.speaker);
                Transform partner = actor==playerActor ? (SpeakerActor(scene.lines[0].speaker)?.transform) : player.transform;
                if(actor!=null)actor.SpeakTo(partner,true);
                // Alternate close framing only when the two speakers are nearby and the view is clear.
                if(actor!=null&&actor!=guard&&Vector3.Distance(actor.transform.position,player.transform.position)<4.5f)
                    yield return ConversationShot(actor,partner,shotId);
                float duration = audioBus.Speak(line.id);
                float elapsed=0,hold=duration>0?duration+.28f:line.seconds;
                while(elapsed<hold)
                {
                    elapsed+=Time.deltaTime;
                    if(elapsed>.9f&&input.DialogueAdvancePressed)break;
                    yield return null;
                }
                if(actor!=null)actor.SpeakTo(null,false);
                audioBus.StopDialogue();
            }
            Speaker = Subtitle = null;
        }
        IEnumerator ConversationShot(PrisonActor actor,Transform partner,string fallback)
        {
            if(partner==null||partner==actor.transform){yield return Shot(fallback);yield break;}
            Vector3 facing=partner.position-actor.transform.position;facing.y=0;
            if(facing.sqrMagnitude<.01f)yield break;
            facing=facing.normalized;
            if(actor.pose==ActorPose.Idle)actor.transform.rotation=Quaternion.LookRotation(facing);
            Vector3 side=Vector3.Cross(Vector3.up,facing);
            Vector3 eye=actor.transform.position+facing*1.65f+side*.57f+Vector3.up*1.68f;
            Vector3 focus=actor.transform.position+Vector3.up*1.48f;
            if(Physics.Linecast(focus,eye,out _,1,QueryTriggerInteraction.Ignore)){yield return Shot(fallback);yield break;}
            Vector3 from=mainCamera.transform.position;Quaternion rot=mainCamera.transform.rotation;
            Quaternion target=Quaternion.LookRotation(focus-eye);float elapsed=0;
            while(elapsed<.35f)
            {
                elapsed+=Time.deltaTime;float t=Mathf.SmoothStep(0,1,elapsed/.35f);
                mainCamera.transform.SetPositionAndRotation(Vector3.Lerp(from,eye,t),Quaternion.Slerp(rot,target,t));yield return null;
            }
        }
        IEnumerator Shot(string id)
        {
            StoryShot selected = null;
            if (shots != null) foreach (var shot in shots) if (shot.id == id) { selected = shot; break; }
            if (selected == null || selected.camera == null || selected.focus == null) yield break;
            Vector3 from = mainCamera.transform.position;
            Quaternion rot = mainCamera.transform.rotation;
            Quaternion target = Quaternion.LookRotation(selected.focus.position - selected.camera.position);
            float elapsed = 0;
            while (elapsed < .65f)
            {
                elapsed += Time.deltaTime; float t = Mathf.SmoothStep(0, 1, elapsed / .65f);
                mainCamera.transform.SetPositionAndRotation(Vector3.Lerp(from, selected.camera.position, t), Quaternion.Slerp(rot, target, t));
                yield return null;
            }
        }
        IEnumerator FadeTo(float opacity, float seconds)
        {
            float initial = Fade, elapsed = 0;
            while (elapsed < seconds)
            { elapsed += Time.deltaTime; Fade = Mathf.Lerp(initial, opacity, Mathf.Clamp01(elapsed / seconds)); yield return null; }
            Fade = opacity;
        }
        static IEnumerator Wait(float seconds)
        { float elapsed = 0; while (elapsed < seconds) { elapsed += Time.deltaTime; yield return null; } }
        void BeginCinematic()
        {
            if(PrisonPokerTable.Active!=null)PrisonPokerTable.Active.Close();
            foreach(var actor in FindObjectsByType<PrisonActor>(FindObjectsSortMode.None))actor.Suspended=true;
            Busy = Letterbox = true; PhoneOpen = false; input.SetGameplayBlocked(true); cameraRig.SetCinematic(true);
        }
        void EndCinematic()
        {
            foreach(var actor in FindObjectsByType<PrisonActor>(FindObjectsSortMode.None)){actor.Suspended=false;actor.SpeakTo(null,false);}
            Busy = Letterbox = false; Speaker = Subtitle = null;
            input.SetGameplayBlocked(State.missed); cameraRig.SetCinematic(false); audioBus.StopDialogue();
            cameraRig.SnapBehind(player.transform.eulerAngles.y);
        }
        void Teleport(Transform point)
        {
            player.Teleport(point.position); player.transform.rotation = point.rotation;
            cameraRig.SnapBehind(point.eulerAngles.y);
        }
        static Vector3 MapPoint(Transform point,Vector3 fallback) => point != null ? point.position : fallback;
        void ResetVisual()
        { if (playerVisual != null) { playerVisual.localPosition = visualPosition; playerVisual.localRotation = visualRotation; } }
        Transform SpawnForStage()
        {
            if (State.stage >= StoryStage.Solitary && State.stage <= StoryStage.DoorKnock) return solitarySpawn;
            if (State.stage == StoryStage.VisitBrother) return visitSpawn;
            if (State.stage == StoryStage.KnifeOpportunity || State.stage == StoryStage.Recognition
                || State.stage == StoryStage.Arrest || State.stage == StoryStage.RivalFight) return yardSpawn;
            return cellSpawn;
        }
        static bool SpecialLocation(StoryStage stage) => stage == StoryStage.CellIntro || stage == StoryStage.Arrest
            || stage == StoryStage.SolitarySleeping || stage == StoryStage.DoorKnock || stage == StoryStage.Solitary;
        void UpdateWorld()
        {
            if (droppedKnife != null) droppedKnife.SetActive(State.stage == StoryStage.KnifeOpportunity);
            if (stashedKnife != null) stashedKnife.SetActive(State.knife == KnifeLocation.CellStash);
            if (tattooMark != null) tattooMark.SetActive(State.tattoo);
            if (phoneProp != null) phoneProp.SetActive(State.stage == StoryStage.ReceivePhone);
            if (cellDoor != null) cellDoor.localRotation = Quaternion.Euler(0, State.stage == StoryStage.CellIntro ? 0 : -95, 0);
            if (solitaryDoor != null) solitaryDoor.localRotation = Quaternion.Euler(0, State.stage <= StoryStage.DoorKnock ? 0 : -95, 0);
            if (guard != null)
            {
                guard.patrolEnabled = State.stage == StoryStage.Socialize || State.stage >= StoryStage.ReturnToCell;
                if (State.stage >= StoryStage.Solitary && State.stage <= StoryStage.DoorKnock)
                    guard.transform.position = MapPoint(guardIsolationPoint, new Vector3(26.5f, .02f, -22.5f));
            }
            if (brother != null) brother.SetPose(State.stage == StoryStage.VisitBrother ? ActorPose.Cry : ActorPose.Idle);
            if (State.stage >= StoryStage.Solitary && State.stage <= StoryStage.VisitBrother && rival != null)
                rival.transform.position = MapPoint(rivalIsolationPoint, new Vector3(32, .02f, -14.5f));
            else if (State.stage >= StoryStage.ReturnToCell && rival != null) rival.ResetActor();
        }
        void LateUpdate()
        {
            if (!MainMenu && !Busy && !State.missed && State.stage == StoryStage.KnifeOpportunity && Time.deltaTime > 0)
            {
                Vector3 target = droppedKnife.transform.position;
                Vector3 d = target - guard.transform.position; d.y = 0;
                if (d.magnitude > .8f)
                { guard.transform.position += d.normalized * .55f * Time.deltaTime; guard.transform.rotation = Quaternion.LookRotation(d); }
            }
        }
        public Transform ObjectiveTarget
        {
            get
            {
                if (State.stage == StoryStage.Socialize && State.AllContacts) return yardSpawn;
                if (State.stage == StoryStage.RivalFight) return rival.transform;
                if (targets != null)
                    foreach (var t in targets) if (t != null && t.target != StoryTarget.Training && !string.IsNullOrEmpty(PromptFor(t.target))) return t.transform;
                return null;
            }
        }
        public string Objective
        {
            get
            {
                if (State.missed) return "Retry the knife incident. No respect was awarded.";
                switch (State.stage)
                {
                    case StoryStage.CellIntro: return "Leave Cell B-04 for the scheduled yard period.";
                    case StoryStage.Socialize: return State.AllContacts ? "Explore the yard. Stay nearby until the fight begins." : "Meet Tomas, help Samir and speak to the workshop contact.";
                    case StoryStage.KnifeOpportunity: return "Conceal Niko's knife before the guard notices it!";
                    case StoryStage.Recognition: return "Niko owes you. Speak to him.";
                    case StoryStage.GangOath: return "Meet Malik and join the Blue Meridian gang.";
                    case StoryStage.Tattoo: return "Receive the gang tattoo from Rafi.";
                    case StoryStage.StashKnife: return "Return to Cell B-04 and hide the knife beneath the mattress.";
                    case StoryStage.ReceivePhone: return "You earned their trust. Niko has a phone for you.";
                    case StoryStage.PhoneCall: return "[P / D-pad right] Answer Malik's first call.";
                    case StoryStage.RivalChallenge: return "Confront the Iron Rooks rival in the yard.";
                    case StoryStage.RivalFight: return "[LMB / RT] Land three punches. Keep the knife hidden.";
                    case StoryStage.Arrest: return "The guards are separating both gangs.";
                    case StoryStage.Solitary: return "Use the bed. Each fighter received 24 hours of isolation.";
                    case StoryStage.SolitarySleeping: return "Sleep until the guard knocks. 24 hours = 60 seconds.";
                    case StoryStage.DoorKnock: return "Answer the knocking guard. You have a visitor.";
                    case StoryStage.VisitBrother: return "Speak to your brother through the visitation receiver.";
                    case StoryStage.ReturnToCell: return "Back in B-04, sit down and think about your father.";
                    case StoryStage.EscapeMeeting: return "Tell Malik you must escape before next week.";
                    default: return "Escape agreement reached. Continue the story in the next chapter.";
                }
            }
        }
        public int MissionNumber => State.stage <= StoryStage.StashKnife ? 1 : State.stage <= StoryStage.PhoneCall ? 2 : 3;
        public string MissionTitle => MissionNumber == 1 ? "FIRST RESPECT" : MissionNumber == 2 ? "TRUST LINE" : "YARD TROUBLE";
        public void Notice(string text) { Toast = text; toastUntil = Time.time + 4; }
        void ShowBanner(string title, string detail, bool failed)
        {
            Banner = title; BannerDetail = detail; BannerFailed = failed; bannerUntil = Time.time + 6;
            audioBus.Play(failed ? audioBus.missed : audioBus.success);
        }
        public bool SaveNow(int slot=0)
        {
            if (!sessionStarted || player.GetComponent<Blackstone.Foundation.FoundationPlayerVitals>()?.Failed == true || player.IsSwimming
                || player.GetComponent<Blackstone.Foundation.FoundationSwimming>()?.RestrictedWater == true
                || Blackstone.Foundation.FoundationVehicle.Active != null
                || player.ExternalControl && !Busy && PrisonPokerTable.Active == null) return false;
            var health=player.GetComponent<Blackstone.Foundation.FoundationDamageable>();
            Vector3 position = PrisonPokerTable.Active!=null?PrisonPokerTable.Active.ReturnPosition:
                Busy ? SpawnForStage().position : player.transform.position;
            bool saved=PrisonSave.Write(new PrisonCheckpoint { story = State, position = position,
                health = health!=null?Mathf.CeilToInt(health.Health):100,
                yaw = PrisonPokerTable.Active!=null?PrisonPokerTable.Active.ReturnRotation.eulerAngles.y:player.transform.eulerAngles.y },slot);
            if(!saved)Notice("Saving was unavailable. Progress remains in this session.");
            return saved;
        }
        void OnApplicationQuit() { if (sessionStarted) SaveNow(); }
        void OnDisable()
        { if (input != null) input.SetGameplayBlocked(false); if (cameraRig != null) cameraRig.SetCinematic(false); }
    }
}
