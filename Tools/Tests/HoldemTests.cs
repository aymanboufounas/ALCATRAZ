using System;
using System.Linq;
using Blackstone.Activities;
using Blackstone.Foundation;
public static class HoldemTests
{
    static int checks;
    static void Assert(bool condition,string message){checks++;if(!condition)throw new Exception(message);}
    public static void Main()
    {
        Assert(PrisonPokerRules.Evaluate(new[]{8,9,10,11,12}).name=="Royal flush","Royal flush");
        Assert(HoldemGame.Best(new[]{12,0,1,2,3,20,35}).name=="Straight flush","Wheel best of seven");
        for(int seed=0;seed<400;seed++)
        {
            var g=new HoldemGame(seed,new HoldemGame.Seat("A",31+seed%71),new HoldemGame.Seat("B",55+seed%301),new HoldemGame.Seat("C",700),new HoldemGame.Seat("D",9+seed%83));
            int bank=g.Seats.Sum(s=>s.Stack);
            for(int hand=0;hand<12&&g.Deal();hand++)
            {
                Assert(g.Seats.SelectMany(s=>s.Folded?new int[0]:s.Hole).Distinct().Count()==g.Seats.Count(s=>!s.Folded)*2,"Unique deal");
                Assert(!g.Act(PokerAction.Raise,g.CurrentBet),"Invalid raise rejected");
                int turns=0;
                while(g.Street!=PokerStreet.Complete&&turns++<200)
                {
                    int total;PokerAction action=g.ChooseAI(out total);
                    if(seed%4==0&&turns%3==0)action=PokerAction.AllIn;
                    Assert(g.Act(action,total),"Legal AI action");
                    Assert(g.Seats.All(s=>s.Stack>=0&&s.TotalBet>=0),"Nonnegative chips");
                    Assert(g.Seats.Sum(s=>s.Stack)+g.Pot==bank,"Chip conservation during betting");
                }
                Assert(g.Street==PokerStreet.Complete,"Hand terminates");
                Assert(g.Seats.Sum(s=>s.Stack)==bank,"Payout conserves chips");
                Assert(g.Board.Concat(g.Seats.Where(s=>s.TotalBet>0).SelectMany(s=>s.Hole)).Distinct().Count()==g.Board.Count,"Unique board");
            }
        }
        var shortRaise=new HoldemGame(7,new HoldemGame.Seat("Dealer",100),new HoldemGame.Seat("Small",100),new HoldemGame.Seat("Big",15));
        shortRaise.Deal();Assert(shortRaise.Actor==0,"Preflop order");shortRaise.Act(PokerAction.CheckCall);shortRaise.Act(PokerAction.CheckCall);shortRaise.Act(PokerAction.AllIn);
        Assert(shortRaise.Actor==0&&!shortRaise.Seats[0].RaiseOpen,"Short all-in does not reopen betting");
        Assert(!shortRaise.Act(PokerAction.Raise,30),"Closed raise rejected");shortRaise.Act(PokerAction.CheckCall);shortRaise.Act(PokerAction.CheckCall);
        Assert(shortRaise.Street==PokerStreet.Flop&&shortRaise.Actor==1,"Flop starts left of dealer");
        var cumulative=new HoldemGame(23,new HoldemGame.Seat("D",20),new HoldemGame.Seat("SB",100),new HoldemGame.Seat("BB",100),new HoldemGame.Seat("Caller",100),new HoldemGame.Seat("Short",15));
        cumulative.Deal();cumulative.Act(PokerAction.CheckCall);cumulative.Act(PokerAction.AllIn);cumulative.Act(PokerAction.AllIn);cumulative.Act(PokerAction.CheckCall);cumulative.Act(PokerAction.CheckCall);
        Assert(cumulative.Actor==3&&cumulative.Seats[3].RaiseOpen,"Cumulative short raises reopen a full raise");Assert(cumulative.Act(PokerAction.Raise,40),"Reopened raise is legal");
        var shortBlind=new HoldemGame(29,new HoldemGame.Seat("SB",100),new HoldemGame.Seat("BB",3));shortBlind.Deal();Assert(shortBlind.Street==PokerStreet.Complete,"No unnecessary call against a short all-in blind");Assert(shortBlind.Seats.Sum(s=>s.Stack)==103,"Short blind conserves chips");
        var weapon=new WeaponState();weapon.Equip(Equipment.Pistol);weapon.Tick(1);int before=weapon.Magazine;Assert(weapon.TryUse()&&weapon.Magazine==before-1,"Gun consumes one round");Assert(!weapon.TryUse(),"Cooldown");weapon.Tick(1);Assert(weapon.TryReload(),"Reload starts");weapon.Tick(3);Assert(weapon.Magazine==weapon.Capacity,"Reload completes");
        Console.WriteLine("PASS: "+checks+" executable poker / weapon checks");
    }
}
