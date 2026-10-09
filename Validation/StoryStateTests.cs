using System;
using Blackstone.Story;

// Standalone executable tests of the actual shipping state class, not a rewritten model.
public static class StoryStateTests
{
    static int checks;
    static void Check(bool value, string description)
    { checks++; if (!value) throw new Exception("FAILED: " + description); }
    static void Act(PrisonStoryState s, StoryAction a)
    { Check(s.TryAct(a), a.ToString()); Check(s.IsValid(), "Valid after " + a); }
    static PrisonStoryState ReachIncident()
    {
        var s = new PrisonStoryState(); Check(s.IsValid(),"Valid new game");
        Check(!s.TryAct(StoryAction.AcceptPhone),"Cannot get phone early");
        Act(s,StoryAction.LeaveCell); Act(s,StoryAction.MeetReader); Act(s,StoryAction.MeetCook);
        Check(!s.BeginIncident(),"Missing contact gates incident"); Act(s,StoryAction.MeetFixer);
        Check(!s.BeginIncident(),"Timing gates incident");
        Check(s.Tick(239)==StorySignal.None,"Fight does not occur early");
        Check(s.Tick(0)==StorySignal.None,"Pause does not tick");
        Check(s.Tick(1)==StorySignal.IncidentReady,"Fight ready at four minute routine");
        Check(s.BeginIncident(),"Incident starts");return s;
    }
    public static void Main()
    {
        var missed = ReachIncident();
        Check(missed.Tick(22)==StorySignal.Missed,"Timed missed outcome");
        Check(missed.respect==0 && missed.knife==KnifeLocation.None,"Failure cannot award respect or knife");
        Check(!missed.TryAct(StoryAction.ConcealKnife),"Cannot conceal after expiry");
        Check(!missed.TryAct(StoryAction.JoinGang),"Failure blocks rewards");
        Check(missed.IsValid(),"Failed checkpoint valid");
        Check(missed.RetryIncident(),"Retry checkpoint");
        Check(missed.knifeSeconds==22 && !missed.missed,"Retry resets opportunity");
        var s=ReachIncident(); s.Tick(21.5f); Act(s,StoryAction.ConcealKnife);
        Check(s.respect==15 && s.knife==KnifeLocation.Concealed,"Success awards respect and inventory");
        Check(!s.TryAct(StoryAction.ConcealKnife),"Cannot award same knife twice");
        Act(s,StoryAction.ThankNiko); Act(s,StoryAction.JoinGang); Act(s,StoryAction.ReceiveTattoo);
        Check(!s.TryAct(StoryAction.AcceptPhone),"Phone requires the cell stash");
        Act(s,StoryAction.StoreKnife); Act(s,StoryAction.AcceptPhone); Act(s,StoryAction.AnswerPhone);
        Act(s,StoryAction.ChallengeRival);
        for(int i=0;i<3;i++)Act(s,StoryAction.StrikeRival);
        Check(s.stage==StoryStage.Arrest,"Three hits trigger arrests");
        Check(s.FinishArrest(),"Arrest sends player to solitary");Act(s,StoryAction.Sleep);
        Check(s.Tick(59)==StorySignal.None,"No early release");
        float t=s.sleepSeconds;s.Tick(0);Check(s.sleepSeconds==t,"Pause freezes isolation");
        Check(s.Tick(1)==StorySignal.Released,"Sixty seconds equals 24 hours");
        Check(s.gameDay==2,"A full game day passed");
        Act(s,StoryAction.FollowGuard); Act(s,StoryAction.SpeakToBrother); Act(s,StoryAction.ReflectInCell);
        Act(s,StoryAction.ProposeEscape);
        Check(s.stage==StoryStage.ChapterComplete && s.escapeAgreement && s.escapeDaysRemaining==6,"Requested ending reached");
        Check(s.phone && s.tattoo && s.gangMember && s.knife==KnifeLocation.CellStash,"Rewards persist through all missions");
        Check(!s.TryAct(StoryAction.AcceptPhone),"Cannot duplicate reward after completion");
        s.sleepSeconds=float.NaN;Check(!s.IsValid(),"Corrupt clock rejected");
        Console.WriteLine("PASS: " + checks + " story gate, failure, timing and reward assertions.");
    }
}
