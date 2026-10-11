using System;
using System.Collections.Generic;
using System.Linq;

namespace Blackstone.Activities
{
    public enum PokerAction { Fold, CheckCall, Raise, AllIn }
    public enum PokerStreet { Preflop, Flop, Turn, River, Complete }
    // Deterministic cash-table rules. Chip totals are conserved, including split side pots.
    public sealed class HoldemGame
    {
        public sealed class Seat
        {
            public string Name; public int Stack,StreetBet,TotalBet; public int[] Hole=new int[2];
            public bool Folded,AllIn,Pending,RaiseOpen;
            public int LastActedBet;
            public Seat(string name,int stack){Name=name;Stack=stack;}
        }
        public Seat[] Seats { get; private set; }
        public readonly List<int> Board=new List<int>();
        public readonly List<string> History=new List<string>();
        public PokerStreet Street { get; private set; }=PokerStreet.Complete;
        public int Dealer { get; private set; }=-1;
        public int Actor { get; private set; }=-1;
        public int CurrentBet { get; private set; }
        public int MinimumRaise { get; private set; }=10;
        public int Pot=>Seats.Sum(s=>s.TotalBet);
        public int LastPot { get; private set; }
        public string Result { get; private set; }="";
        public int ToCall(int index)=>Math.Max(0,CurrentBet-Seats[index].StreetBet);
        public int MinRaiseTo=>CurrentBet+MinimumRaise;
        readonly Random random; int[] deck;int dealt;
        public HoldemGame(int seed,params Seat[] seats)
        {if(seats.Length<2||seats.Length>6||seats.Any(s=>s.Stack<0))throw new ArgumentException("Two to six valid seats are required.");Seats=seats;random=new Random(seed);}
        int Next(int index,Func<Seat,bool> test)
        {for(int j=1;j<=Seats.Length;j++){int k=(index+j)%Seats.Length;if(test(Seats[k]))return k;}return -1;}
        public bool Deal()
        {
            if(Street!=PokerStreet.Complete||Seats.Count(s=>s.Stack>0)<2)return false;
            Board.Clear();History.Clear();Result="";LastPot=0;CurrentBet=0;MinimumRaise=10;dealt=0;deck=PrisonPokerRules.Deck(random);
            foreach(var s in Seats){s.Folded=s.Stack<=0;s.AllIn=false;s.TotalBet=s.StreetBet=s.LastActedBet=0;s.Pending=!s.Folded;s.RaiseOpen=true;}
            Dealer=Next(Dealer,s=>!s.Folded);bool heads=Seats.Count(s=>!s.Folded)==2;
            int small=heads?Dealer:Next(Dealer,s=>!s.Folded),big=Next(small,s=>!s.Folded);
            for(int round=0;round<2;round++)for(int j=1;j<=Seats.Length;j++){int i=(Dealer+j)%Seats.Length;if(!Seats[i].Folded)Seats[i].Hole[round]=deck[dealt++];}
            Pay(small,5);Pay(big,10);CurrentBet=10;Street=PokerStreet.Preflop;
            Actor=Next(big,s=>!s.Folded&&!s.AllIn&&s.Pending);Progress(big);return true;
        }
        void Pay(int i,int amount)
        {var s=Seats[i];amount=Math.Min(amount,s.Stack);s.Stack-=amount;s.StreetBet+=amount;s.TotalBet+=amount;if(s.Stack==0){s.AllIn=true;s.Pending=false;}}
        public bool Act(PokerAction action,int raiseTo=0)
        {
            if(Actor<0||Street==PokerStreet.Complete)return false;
            int index=Actor;var s=Seats[index];int call=ToCall(index);
            if(action==PokerAction.AllIn){raiseTo=s.StreetBet+s.Stack;action=raiseTo>CurrentBet?PokerAction.Raise:PokerAction.CheckCall;}
            if(action==PokerAction.Raise)
            {
                int total=s.StreetBet+s.Stack;
                if(!s.RaiseOpen||raiseTo<=CurrentBet||raiseTo>total||(raiseTo<MinRaiseTo&&raiseTo!=total))return false;
                int increase=raiseTo-CurrentBet;bool full=increase>=MinimumRaise;
                Pay(index,raiseTo-s.StreetBet);CurrentBet=raiseTo;
                if(full)MinimumRaise=increase;
                foreach(var other in Seats)
                {if(other==s||other.Folded||other.AllIn)continue;if(other.StreetBet<CurrentBet)other.Pending=true;if(full||CurrentBet-other.LastActedBet>=MinimumRaise)other.RaiseOpen=true;}
                History.Add(s.Name+" raises to "+raiseTo+(s.AllIn?" · all-in":""));
            }
            else if(action==PokerAction.Fold){s.Folded=true;History.Add(s.Name+" folds");}
            else if(action==PokerAction.CheckCall){Pay(index,call);History.Add(s.Name+(call==0?" checks":" calls "+Math.Min(call,s.StreetBet))+(s.AllIn?" · all-in":""));}
            else return false;
            s.Pending=false;s.RaiseOpen=false;s.LastActedBet=CurrentBet;Progress(index);return true;
        }
        void Progress(int previous)
        {
            if(Seats.Count(s=>!s.Folded)==1){int winner=Array.FindIndex(Seats,s=>!s.Folded);LastPot=Pot;Seats[winner].Stack+=Pot;Result=Seats[winner].Name+" wins "+LastPot+" · everyone else folded";Complete();return;}
            if(Seats.Count(s=>!s.Folded&&!s.AllIn)<=1)
            {foreach(var s in Seats)if(!s.Folded&&!s.AllIn&&s.StreetBet>=Seats.Where(other=>other!=s&&!other.Folded).Max(other=>other.StreetBet))s.Pending=false;}
            Actor=Next(previous,s=>!s.Folded&&!s.AllIn&&s.Pending);
            if(Actor>=0)return;
            RefundUncalled();
            if(Street==PokerStreet.River){Showdown();return;}
            AdvanceStreet();
        }
        void RefundUncalled()
        {
            var ordered=Seats.OrderByDescending(s=>s.TotalBet).ToArray();
            int extra=ordered[0].TotalBet-ordered[1].TotalBet;
            if(extra>0){ordered[0].TotalBet-=extra;ordered[0].StreetBet=Math.Max(0,ordered[0].StreetBet-extra);ordered[0].Stack+=extra;}
        }
        void AdvanceStreet()
        {
            Street=(PokerStreet)((int)Street+1);dealt++; // Burn one card before each street.
            int count=Street==PokerStreet.Flop?3:1;for(int i=0;i<count;i++)Board.Add(deck[dealt++]);
            CurrentBet=0;MinimumRaise=10;
            bool contest=Seats.Count(s=>!s.Folded&&!s.AllIn)>1;
            foreach(var s in Seats){s.StreetBet=0;s.Pending=contest&&!s.Folded&&!s.AllIn;s.RaiseOpen=true;}
            Actor=Next(Dealer,s=>s.Pending);
            if(Actor<0){if(Street==PokerStreet.River)Showdown();else AdvanceStreet();}
        }
        public static PokerValue Best(IEnumerable<int> source)
        {
            int[] c=source.ToArray();if(c.Length<5||c.Length>7||c.Distinct().Count()!=c.Length)throw new ArgumentException("Five to seven distinct cards required.");
            PokerValue best=new PokerValue{score=-1};
            for(int a=0;a<c.Length-4;a++)for(int b=a+1;b<c.Length-3;b++)for(int d=b+1;d<c.Length-2;d++)for(int e=d+1;e<c.Length-1;e++)for(int f=e+1;f<c.Length;f++)
            {var value=PrisonPokerRules.Evaluate(new[]{c[a],c[b],c[d],c[e],c[f]});if(value.score>best.score)best=value;}
            return best;
        }
        void Showdown()
        {
            LastPot=Pot;int previous=0;var lines=new List<string>();
            var values=Seats.Select(s=>s.Folded?new PokerValue{score=-1}:Best(s.Hole.Concat(Board))).ToArray();
            foreach(int level in Seats.Select(s=>s.TotalBet).Where(n=>n>0).Distinct().OrderBy(n=>n))
            {
                int amount=(level-previous)*Seats.Count(s=>s.TotalBet>=level);previous=level;
                long best=Seats.Select((s,i)=>s.TotalBet>=level&&!s.Folded?values[i].score:-1).Max();
                int[] winners=Enumerable.Range(0,Seats.Length).Where(i=>Seats[i].TotalBet>=level&&!Seats[i].Folded&&values[i].score==best).ToArray();
                if(winners.Length==0)throw new InvalidOperationException("Side pot has no eligible player.");
                int share=amount/winners.Length,odd=amount%winners.Length;
                foreach(int i in winners)Seats[i].Stack+=share;
                for(int step=1;step<=Seats.Length&&odd>0;step++){int i=(Dealer+step)%Seats.Length;if(winners.Contains(i)){Seats[i].Stack++;odd--;}}
                lines.Add(string.Join(" & ",winners.Select(i=>Seats[i].Name).ToArray())+" win "+amount+" · "+values[winners[0]].name);
            }
            Result=string.Join("\n",lines.ToArray());Complete();
        }
        void Complete(){Street=PokerStreet.Complete;Actor=-1;foreach(var s in Seats){s.TotalBet=s.StreetBet=0;s.Pending=false;}}
        public PokerAction ChooseAI(out int total)
        {
            total=0;if(Actor<0)return PokerAction.CheckCall;var s=Seats[Actor];
            // Decisions use only this player's cards and public community cards.
            float strength;
            if(Board.Count<3){int a=s.Hole[0]%13+2,b=s.Hole[1]%13+2;strength=(a+b)/30f;if(a==b)strength+=.24f;if(s.Hole[0]/13==s.Hole[1]/13)strength+=.08f;}
            else strength=Math.Min(.95f,.25f+Best(s.Hole.Concat(Board)).score/759375f*.13f);
            float odds=(float)ToCall(Actor)/Math.Max(1,Pot+ToCall(Actor));float noise=(float)random.NextDouble()*.25f;
            if(ToCall(Actor)>0&&strength+noise<odds+.2f)return PokerAction.Fold;
            total=Math.Min(s.StreetBet+s.Stack,Math.Max(MinRaiseTo,CurrentBet+Math.Max(10,Pot/2)));
            if(s.RaiseOpen&&strength>.7f&&random.NextDouble()<.22&&total>=MinRaiseTo)return PokerAction.Raise;
            return PokerAction.CheckCall;
        }
    }
}
