using System;
using System.Linq;
using Blackstone.Activities;

// Exercises the shipping, Unity-independent rules; not a duplicate evaluator.
public static class PokerRulesTests
{
    static int checks;
    static int C(int rank, int suit = 0) { return suit * 13 + rank - 2; }
    static long S(params int[] hand) { return PrisonPokerRules.Evaluate(hand).score; }
    static void Check(bool value, string message)
    {
        checks++;
        if (!value) throw new Exception(message);
    }
    static void Invalid(int[] hand)
    {
        bool rejected = false;
        try { PrisonPokerRules.Evaluate(hand); }
        catch (ArgumentException) { rejected = true; }
        Check(rejected, "Invalid hand was accepted");
    }
    public static void Main()
    {
        int[][] categories = {
            new[] {C(14),C(11,1),C(9,2),C(6,3),C(3)},
            new[] {C(2),C(2,1),C(14,2),C(12,3),C(10)},
            new[] {C(2),C(2,1),C(3,2),C(3,3),C(14)},
            new[] {C(2),C(2,1),C(2,2),C(14,3),C(13)},
            new[] {C(2),C(3,1),C(4,2),C(5,3),C(6)},
            new[] {C(2),C(5),C(8),C(10),C(13)},
            new[] {C(2),C(2,1),C(2,2),C(3,3),C(3)},
            new[] {C(2),C(2,1),C(2,2),C(2,3),C(14)},
            new[] {C(2),C(3),C(4),C(5),C(6)},
            new[] {C(10),C(11),C(12),C(13),C(14)}
        };
        string[] names = {"High card","One pair","Two pairs","Three of a kind","Straight","Flush","Full house","Four of a kind","Straight flush","Royal flush"};
        for(int i=0;i<categories.Length;i++)
        {
            Check(PrisonPokerRules.Evaluate(categories[i]).name==names[i], "Wrong category " + names[i]);
            if(i>0) Check(S(categories[i])>S(categories[i-1]), "Category ordering");
            Check(S(categories[i])==S(categories[i].Reverse().ToArray()), "Hand order affects score");
        }
        Check(S(C(14),C(2,1),C(3,2),C(4,3),C(5)) < S(categories[4]), "Ace-low straight beats six-high");
        Check(PrisonPokerRules.Evaluate(new[]{C(14),C(2),C(3),C(4),C(5)}).name=="Straight flush", "Ace-low flush");
        Check(PrisonPokerRules.Evaluate(new[]{C(12),C(13,1),C(14,2),C(2,3),C(3)}).name=="High card", "Illegal wrapped straight");
        Check(S(C(10),C(10,1),C(14,2),C(12,3),C(9)) > S(C(10),C(10,1),C(14,2),C(11,3),C(9)), "Pair second kicker ignored");
        Check(S(C(8),C(8,1),C(6,2),C(6,3),C(14)) > S(C(8),C(8,1),C(6,2),C(6,3),C(13)), "Two-pair kicker ignored");
        Check(S(C(3),C(3,1),C(3,2),C(2,3),C(2)) > S(C(2),C(2,1),C(2,2),C(14,3),C(14)), "Full-house triplet priority");
        Check(S(C(9),C(9,1),C(9,2),C(9,3),C(14)) > S(C(9),C(9,1),C(9,2),C(9,3),C(13)), "Quads kicker ignored");
        Check(S(C(14),C(11),C(9),C(6),C(3)) > S(C(14,1),C(11,1),C(8,1),C(7,1),C(4,1)), "Flush third kicker ignored");
        Check(S(C(14),C(11,1),C(9,2),C(6,3),C(3)) == S(C(14,1),C(11,2),C(9,3),C(6),C(3,1)), "Suits break a tie");
        Invalid(null); Invalid(new int[4]); Invalid(new[]{0,1,2,3,3});
        Invalid(new[]{-1,0,1,2,3}); Invalid(new[]{0,1,2,3,52});
        for(int seed=0;seed<100;seed++)
        {
            int[] deck=PrisonPokerRules.Deck(new Random(seed));
            Check(deck.Length==52 && deck.Distinct().Count()==52 && deck.Min()==0 && deck.Max()==51, "Deck loses or repeats a card");
        }
        Check(PrisonPokerRules.Deck(new Random(37)).SequenceEqual(PrisonPokerRules.Deck(new Random(37))), "Seed reproducibility");
        Check(!PrisonPokerRules.Deck(new Random(37)).SequenceEqual(Enumerable.Range(0,52)), "Deck was not shuffled");
        int wheelFlushes=0;
        for(int pattern=0;pattern<1024;pattern++)
        {
            int p=pattern;int[] ranks={14,2,3,4,5};int[] hand=new int[5];
            for(int i=0;i<5;i++){hand[i]=C(ranks[i],p%4);p/=4;}
            var value=PrisonPokerRules.Evaluate(hand);
            Check(value.name=="Straight"||value.name=="Straight flush", "Wheel suit permutation rejected");
            if(value.name=="Straight flush")wheelFlushes++;
        }
        Check(wheelFlushes==4, "Wheel flush count");
        Check(PrisonPokerRules.CardName(C(14,3))=="A♠", "Ace card label");
        Console.WriteLine("PASS: " + checks + " assertions against shipping PrisonPokerRules.cs.");
    }
}
