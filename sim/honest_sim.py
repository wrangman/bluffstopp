import sys, random
import os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from deck import Deck
from card import Card
from player import Player
from ai_player import AIPlayer


class HonestBot(Player):
    # spelar som en försiktig människa: lägsta passande kort ärligt,
    # inget passar -> bluffa med lägsta kortet (säger ett steg upp) eller passa, hälften var.
    # säger bluffstopp bara när det är säkert (har kortet) eller på datorns sista kort
    def choose(self, top):
        if top is None:
            i = self.lowest_card_index()
            return (i, self.hand[i])
        best = None
        for i in range(len(self.hand)):
            if self.hand[i].can_follow(top):
                if best is None or self.hand[i].rank() < self.hand[best].rank():
                    best = i
        if best is not None:
            return (best, self.hand[best])
        if random.random() < 0.5:
            return None
        i = self.lowest_card_index()
        for v, r in [("2",2)]:
            pass
        # säger samma valör i annan färg
        for s in ["♠", "♥", "♣", "♦"]:
            if s != top.suit and not self.has_card(s, top.value):
                return (i, Card(s, top.value))
        return None

    def calls(self, claim, opp_left):
        return self.has_card(claim.suit, claim.value) or opp_left == 0


def penalty(loser, winner, deck):
    if deck:
        n = min(3, len(deck)); loser.take_cards(deck[:n]); del deck[:n]
    else:
        c = winner.random_card()
        if c is not None: loser.take_cards([c])


stats = {"ai_calls": 0, "ai_calls_right": 0, "ai_calls_far": 0, "ai_calls_far_right": 0,
         "ai_pass": 0, "ai_pass_with_valid": 0, "ai_moves": 0, "max_hand": [], "end_hand": [],
         "human_bluffs": 0, "human_moves": 0}


def play(ai, bot, starter):
    deck = Deck.shuffle_deck(Deck.make_deck())
    ai.hand, bot.hand = [], []
    ai.take_cards(deck[:6]); bot.take_cards(deck[6:12]); del deck[:12]
    ai.forget_all()
    top_real = deck.pop(0); claim = top_real
    ai.remember(top_real)
    last = None; cur = starter; max_hand = 6; before = None
    for step in range(3000):
        opp = bot if cur is ai else ai
        max_hand = max(max_hand, ai.cards_left())
        if claim is not None and last is opp:
            if cur is ai:
                call = ai.wants_to_call_bluff(claim, before, bot.cards_left())
            else:
                call = bot.calls(claim, ai.cards_left())
            if call:
                ai.remember(top_real)
                honest = top_real.same_as(claim)
                if cur is ai:
                    stats["ai_calls"] += 1
                    if not honest: stats["ai_calls_right"] += 1
                    if bot.cards_left() >= 4:
                        stats["ai_calls_far"] += 1
                        if not honest: stats["ai_calls_far_right"] += 1
                if honest:
                    penalty(cur, opp, deck)
                    if cur is bot: ai.forget_passes() if False else None
                    if cur is bot: ai.forget_passes()
                    cur = opp
                else:
                    penalty(opp, cur, deck)
                    if opp is bot: ai.forget_passes()
                claim = None; last = None
                continue
            if cur is ai:
                ai.remember_claim(claim)
        if opp.cards_left() == 0:
            stats["max_hand"].append(max_hand); return opp
        if cur.cards_left() == 0:
            stats["max_hand"].append(max_hand); return cur
        if cur is ai:
            valid = claim is None or len(ai.valid_cards(claim)) > 0
            m = ai.choose_move(claim, ai.think_time(), bot.cards_left(), len(deck))
            stats["ai_moves"] += 1
            if m is None:
                stats["ai_pass"] += 1
                if valid: stats["ai_pass_with_valid"] += 1
        else:
            m = bot.choose(claim)
            stats["human_moves"] += 1
            if m is None:
                ai.remember_pass(claim)
            elif not bot.hand[m[0]].same_as(m[1]):
                stats["human_bluffs"] += 1
        if m is None:
            if deck: cur.take_cards([deck.pop(0)])
            claim = None; last = None; cur = opp
            continue
        top_real = cur.hand.pop(m[0]); before = claim; claim = m[1]
        if cur is ai: ai.remember(top_real)
        last = cur; cur = opp
    stats["max_hand"].append(max_hand)
    return None


N = int(sys.argv[1]) if len(sys.argv) > 1 else 400
ai, bot = AIPlayer("ny"), HonestBot("ärlig")
wins = {"ny": 0, "ärlig": 0, "oavgjort": 0}
for g in range(N):
    w = play(ai, bot, ai if g % 2 == 0 else bot)
    wins[w.name if w else "oavgjort"] += 1
s = stats
print("vinster:", wins)
print("motståndarens bluffar:", s["human_bluffs"], "av", s["human_moves"], "drag",
      f"({s['human_bluffs'] / s['human_moves']:.0%})")
print("datorn säger bluffstopp:", s["ai_calls"], "gånger, rätt:", f"{s['ai_calls_right'] / max(1, s['ai_calls']):.0%}",
      f"({s['ai_calls'] / N:.1f} per spel)")
print("  när motståndaren har 4+ kort:", s["ai_calls_far"], "gånger, rätt:", f"{s['ai_calls_far_right'] / max(1, s['ai_calls_far']):.0%}")
print("datorn passar:", s["ai_pass"], "av", s["ai_moves"], "drag, varav med passande kort:", s["ai_pass_with_valid"])
mh = sorted(s["max_hand"])
print("datorns största hand per spel: median", mh[len(mh) // 2], " 90%:", mh[int(len(mh) * 0.9)], " max", mh[-1])
