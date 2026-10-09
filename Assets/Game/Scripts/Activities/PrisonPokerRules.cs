using System;
using System.Linq;

namespace Blackstone.Activities
{
    public struct PokerValue { public long score; public string name; }
    public static class PrisonPokerRules
    {
        public static int[] Deck(Random random)
        {
            int[] cards = Enumerable.Range(0,52).ToArray();
            for (int i = cards.Length-1; i > 0; i--)
            { int j = random.Next(i+1); int c = cards[i]; cards[i] = cards[j]; cards[j] = c; }
            return cards;
        }
        public static PokerValue Evaluate(int[] cards)
        {
            if (cards == null || cards.Length != 5 || cards.Distinct().Count() != 5 || cards.Any(c=>c<0||c>=52))
                throw new ArgumentException("A hand needs five distinct cards from one deck.");
            var ranks = cards.Select(c=>c%13+2).OrderByDescending(x=>x).ToArray();
            var groups = ranks.GroupBy(x=>x).OrderByDescending(g=>g.Count()).ThenByDescending(g=>g.Key).ToArray();
            bool flush = cards.All(c=>c/13==cards[0]/13);
            bool straight = ranks.Distinct().Count()==5 && (ranks[0]-ranks[4]==4 || ranks.SequenceEqual(new[]{14,5,4,3,2}));
            int top = ranks.SequenceEqual(new[]{14,5,4,3,2}) ? 5 : ranks[0];
            int category; string name; int[] kickers;
            if (straight && flush) { category=8; name=top==14?"Royal flush":"Straight flush"; kickers=new[]{top}; }
            else if (groups[0].Count()==4) { category=7; name="Four of a kind"; kickers=groups.Select(g=>g.Key).ToArray(); }
            else if (groups[0].Count()==3 && groups[1].Count()==2) { category=6; name="Full house"; kickers=groups.Select(g=>g.Key).ToArray(); }
            else if (flush) { category=5; name="Flush"; kickers=ranks; }
            else if (straight) { category=4; name="Straight"; kickers=new[]{top}; }
            else if (groups[0].Count()==3) { category=3; name="Three of a kind"; kickers=groups.Select(g=>g.Key).ToArray(); }
            else if (groups[0].Count()==2 && groups[1].Count()==2) { category=2; name="Two pairs"; kickers=groups.Select(g=>g.Key).ToArray(); }
            else if (groups[0].Count()==2) { category=1; name="One pair"; kickers=groups.Select(g=>g.Key).ToArray(); }
            else { category=0; name="High card"; kickers=ranks; }
            long score=category;
            for (int i=0;i<5;i++) score=score*15+(i<kickers.Length?kickers[i]:0);
            return new PokerValue {score=score,name=name};
        }
        public static string CardName(int card)
        {
            int rank=card%13+2;
            string label=rank==14?"A":rank==13?"K":rank==12?"Q":rank==11?"J":rank.ToString();
            return label+new[]{"♣","♦","♥","♠"}[card/13];
        }
    }
}
