using System;

namespace Blackstone.Story
{
    // Kept independent of Unity so gates, clocks and save invariants can be tested directly.
    public enum StoryStage
    {
        CellIntro, Socialize, KnifeOpportunity, Recognition, GangOath, Tattoo,
        StashKnife, ReceivePhone, PhoneCall, RivalChallenge, RivalFight, Arrest,
        Solitary, SolitarySleeping, DoorKnock, VisitBrother, ReturnToCell,
        EscapeMeeting, ChapterComplete
    }
    public enum StoryAction
    {
        LeaveCell, MeetReader, MeetCook, MeetFixer, ConcealKnife, ThankNiko,
        JoinGang, ReceiveTattoo, StoreKnife, AcceptPhone, AnswerPhone,
        ChallengeRival, StrikeRival, Sleep, FollowGuard, SpeakToBrother,
        ReflectInCell, ProposeEscape
    }
    public enum KnifeLocation { None, Concealed, CellStash }
    public enum StorySignal { None, IncidentReady, Missed, Released }

    [Serializable]
    public sealed class PrisonStoryState
    {
        public const int CurrentVersion = 1;
        public int version = CurrentVersion;
        public StoryStage stage = StoryStage.CellIntro;
        public int acquaintances;
        public float routineSeconds;
        public float knifeSeconds = 22f;
        public bool missed;
        public int respect;
        public bool gangMember, tattoo, phone;
        public KnifeLocation knife;
        public int brawlHits;
        public float sleepSeconds;
        public int gameDay = 1;
        public int escapeDaysRemaining = 6;
        public bool fatherKidnapped, escapeAgreement;

        public bool AllContacts => (acquaintances & 7) == 7;
        public StorySignal Tick(float delta, float incidentAt = 240f, float isolationDuration = 60f)
        {
            if (delta <= 0 || float.IsNaN(delta) || float.IsInfinity(delta)) return StorySignal.None;
            if (stage == StoryStage.Socialize)
            {
                routineSeconds += delta;
                if (AllContacts && routineSeconds >= incidentAt) return StorySignal.IncidentReady;
            }
            if (stage == StoryStage.KnifeOpportunity && !missed)
            {
                knifeSeconds = Math.Max(0, knifeSeconds - delta);
                if (knifeSeconds <= 0) { missed = true; return StorySignal.Missed; }
            }
            if (stage == StoryStage.SolitarySleeping)
            {
                sleepSeconds = Math.Min(isolationDuration, sleepSeconds + delta);
                if (sleepSeconds >= isolationDuration)
                { stage = StoryStage.DoorKnock; gameDay = 2; return StorySignal.Released; }
            }
            return StorySignal.None;
        }
        public bool BeginIncident(float incidentAt = 240f)
        {
            if (stage != StoryStage.Socialize || !AllContacts || routineSeconds < incidentAt) return false;
            stage = StoryStage.KnifeOpportunity; knifeSeconds = 22f; missed = false; return true;
        }
        public bool RetryIncident()
        {
            if (stage != StoryStage.KnifeOpportunity || !missed) return false;
            missed = false; knifeSeconds = 22f; return true;
        }
        public bool FinishArrest()
        {
            if (stage != StoryStage.Arrest) return false;
            stage = StoryStage.Solitary; return true;
        }
        public bool TryAct(StoryAction action)
        {
            if (missed) return false;
            switch (stage)
            {
                case StoryStage.CellIntro:
                    if (action != StoryAction.LeaveCell) return false;
                    stage = StoryStage.Socialize; break;
                case StoryStage.Socialize:
                    if (action == StoryAction.MeetReader) acquaintances |= 1;
                    else if (action == StoryAction.MeetCook) acquaintances |= 2;
                    else if (action == StoryAction.MeetFixer) acquaintances |= 4;
                    else return false;
                    break;
                case StoryStage.KnifeOpportunity:
                    if (action != StoryAction.ConcealKnife || knifeSeconds <= 0) return false;
                    knife = KnifeLocation.Concealed; respect = 15; stage = StoryStage.Recognition; break;
                case StoryStage.Recognition:
                    if (action != StoryAction.ThankNiko || knife != KnifeLocation.Concealed) return false;
                    stage = StoryStage.GangOath; break;
                case StoryStage.GangOath:
                    if (action != StoryAction.JoinGang) return false;
                    gangMember = true; respect = 30; stage = StoryStage.Tattoo; break;
                case StoryStage.Tattoo:
                    if (action != StoryAction.ReceiveTattoo || !gangMember) return false;
                    tattoo = true; respect = 50; stage = StoryStage.StashKnife; break;
                case StoryStage.StashKnife:
                    if (action != StoryAction.StoreKnife || knife != KnifeLocation.Concealed) return false;
                    knife = KnifeLocation.CellStash; stage = StoryStage.ReceivePhone; break;
                case StoryStage.ReceivePhone:
                    if (action != StoryAction.AcceptPhone || !tattoo || knife != KnifeLocation.CellStash) return false;
                    phone = true; stage = StoryStage.PhoneCall; break;
                case StoryStage.PhoneCall:
                    if (action != StoryAction.AnswerPhone || !phone) return false;
                    respect = 65; stage = StoryStage.RivalChallenge; break;
                case StoryStage.RivalChallenge:
                    if (action != StoryAction.ChallengeRival) return false;
                    brawlHits = 0; stage = StoryStage.RivalFight; break;
                case StoryStage.RivalFight:
                    if (action != StoryAction.StrikeRival) return false;
                    if (++brawlHits >= 3) stage = StoryStage.Arrest;
                    break;
                case StoryStage.Solitary:
                    if (action != StoryAction.Sleep) return false;
                    sleepSeconds = 0; stage = StoryStage.SolitarySleeping; break;
                case StoryStage.DoorKnock:
                    if (action != StoryAction.FollowGuard) return false;
                    stage = StoryStage.VisitBrother; break;
                case StoryStage.VisitBrother:
                    if (action != StoryAction.SpeakToBrother) return false;
                    fatherKidnapped = true; stage = StoryStage.ReturnToCell; break;
                case StoryStage.ReturnToCell:
                    if (action != StoryAction.ReflectInCell) return false;
                    stage = StoryStage.EscapeMeeting; break;
                case StoryStage.EscapeMeeting:
                    if (action != StoryAction.ProposeEscape || !fatherKidnapped || !gangMember) return false;
                    escapeAgreement = true; respect = 80; stage = StoryStage.ChapterComplete; break;
                default: return false;
            }
            return true;
        }
        public bool IsValid()
        {
            if (version != CurrentVersion || !Enum.IsDefined(typeof(StoryStage), stage)
                || !Enum.IsDefined(typeof(KnifeLocation), knife)) return false;
            if (acquaintances < 0 || acquaintances > 7 || respect < 0 || respect > 100
                || brawlHits < 0 || brawlHits > 3 || gameDay < 1 || gameDay > 2
                || escapeDaysRemaining != 6 || !Finite(routineSeconds) || routineSeconds < 0
                || !Finite(knifeSeconds) || knifeSeconds < 0 || knifeSeconds > 22
                || !Finite(sleepSeconds) || sleepSeconds < 0 || sleepSeconds > 60) return false;
            if (stage >= StoryStage.Recognition && knife == KnifeLocation.None) return false;
            if (stage >= StoryStage.Tattoo && !gangMember) return false;
            if (stage >= StoryStage.StashKnife && !tattoo) return false;
            if (stage >= StoryStage.ReceivePhone && knife != KnifeLocation.CellStash) return false;
            if (stage >= StoryStage.PhoneCall && !phone) return false;
            if (stage >= StoryStage.ReturnToCell && !fatherKidnapped) return false;
            if (stage == StoryStage.ChapterComplete && !escapeAgreement) return false;
            return !missed || stage == StoryStage.KnifeOpportunity;
        }
        static bool Finite(float x) => !float.IsNaN(x) && !float.IsInfinity(x);
    }
}
