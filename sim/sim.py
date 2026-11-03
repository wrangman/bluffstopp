import sys, random
import os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)))
from deck import Deck
from ai_player import AIPlayer
from old_ai_player import AIPlayer as OldAI

stats = {"no_valid": 0, 
         "no_valid_pass": 0,              
         "no_valid_long": 0, 
         "no_valid_long_pass": 0,
         "last_nofit": 0, 
         "last_nofit_pass": 0, 
         "bluff_with_valid": 0, 
         "moves": 0,
         "bluff_same_value": 0, 
         "free": 0, 
         "free_few": 0, 
         "bluff_free_few": 0, 
         "bluff_own": 0, 
         "bluff_seen": 0, 
         "bluff_total": 0, 
         "low_high": 0, 
         "bluff_high_real": 0, 
         "bluff_ace_real": 0, 
         "bluff_valid_real": 0, 
         "bluff_up": {}, 
         "bluff_free": 0, 
         "bluff_opp_has": 0, 
         "near": 0, 
         "near_pass": 0, 
         "near_high": 0, 
         "near_high_honest": 0}

OPP = [None]

def move(p, top, opp_cards, deck_left):
    if isinstance(p, OldAI):
        return p.choose_move(top)
    seconds = p.think_time()
    valid = len(p.valid_cards(top)) > 0 if top is not None else True
    m = p.choose_move(top, seconds, opp_cards, deck_left)
    stats["moves"] += 1
    if top is not None and not valid:
        stats["no_valid"] += 1
        if seconds > 2.0 and len(p.hand) > 2:
            stats["no_valid_long"] += 1
            if m is None: stats["no_valid_long_pass"] += 1
        if m is None: stats["no_valid_pass"] += 1
        if len(p.hand) == 1:
            stats["last_nofit"] += 1
            if m is None: stats["last_nofit_pass"] += 1
    if opp_cards <= 2:
        stats["near"] += 1
        if m is None: stats["near_pass"] += 1
    if m is not None and opp_cards <= 2:
        real, claim = p.hand[m[0]], m[1]
        if claim.rank() >= 12:
            stats["near_high"] += 1
            if real.same_as(claim): stats["near_high_honest"] += 1
    if m is not None:
        real, claim = p.hand[m[0]], m[1]
        if top is None:
            stats["free"] += 1
            if len(p.hand) <= 3: stats["free_few"] += 1
        if not real.same_as(claim):
            stats["bluff_total"] += 1
            if p.has_card(claim.suit, claim.value): stats["bluff_own"] += 1
            if p.has_seen(claim.suit, claim.value): stats["bluff_seen"] += 1
            if OPP[0] is not None and OPP[0].has_card(claim.suit, claim.value): stats["bluff_opp_has"] += 1
            if real.rank() <= 7 and claim.rank() >= 11: stats["low_high"] += 1
            if len(p.hand) > 1 and real.rank() >= 12: stats["bluff_high_real"] += 1
            if len(p.hand) > 1 and real.rank() == 14: stats["bluff_ace_real"] += 1
            if top is not None and real.can_follow(top): stats["bluff_valid_real"] += 1
            if top is None and len(p.hand) <= 3: stats["bluff_free_few"] += 1
            if valid and top is not None: stats["bluff_with_valid"] += 1
            if top is None: stats["bluff_free"] += 1
            elif claim.value == top.value: stats["bluff_same_value"] += 1
            else:
                d = claim.rank() - top.rank()
                stats["bluff_up"][d] = stats["bluff_up"].get(d, 0) + 1
    return m

def penalty(loser, winner, deck):
    if deck:
        n = min(3, len(deck)); loser.take_cards(deck[:n]); del deck[:n]
    else:
        c = winner.random_card()
        if c is not None: loser.take_cards([c])

def play(a, b, starter):
    deck = Deck.shuffle_deck(Deck.make_deck())
    a.hand, b.hand = [], []
    a.take_cards(deck[:6]); b.take_cards(deck[6:12]); del deck[:12]
    a.forget_all(); b.forget_all()
    top_real = deck.pop(0); claim = top_real
    for p in (a, b): p.remember(top_real)
    last = None; called = False; cur = starter; before = None
    for step in range(2000):
        opp = b if cur is a else a
        if claim is not None and last is opp and not called:
            if isinstance(cur, OldAI):
                call = cur.wants_to_call_bluff(claim, opp.cards_left())
            else:
                call = cur.wants_to_call_bluff(claim, before, opp.cards_left())
            if call:
                for p in (a, b): p.remember(top_real)
                if top_real.same_as(claim):
                    penalty(cur, opp, deck); cur = opp
                else:
                    penalty(opp, cur, deck)
                claim = None; last = None; called = False
                continue
            if hasattr(cur, "remember_claim"): cur.remember_claim(claim)
        if opp.cards_left() == 0: return opp
        if cur.cards_left() == 0: return cur
        OPP[0] = opp
        m = move(cur, claim, opp.cards_left(), len(deck))
        if m is None:
            if deck: cur.take_cards([deck.pop(0)])
            claim = None; last = None; called = False; cur = opp
            continue
        top_real = cur.hand.pop(m[0]); before = claim; claim = m[1]
        cur.remember(top_real)
        last = cur; called = False; cur = opp
    return None

N = int(sys.argv[1]) if len(sys.argv) > 1 else 400
new, old = AIPlayer("ny"), OldAI("gammal")
wins = {"ny": 0, "gammal": 0, "oavgjort": 0}
for g in range(N):
    w = play(new, old, new if g % 2 == 0 else old)
    wins[w.name if w else "oavgjort"] += 1
print("ny mot gammal:", wins)
s = stats
print("inget kort passar -> pass:", round(s["no_valid_pass"] / max(1, s["no_valid"]), 2), "av", s["no_valid"])
print("  efter lång tvekan (>2 kort) -> pass:", round(s["no_valid_long_pass"] / max(1, s["no_valid_long"]), 2), "av", s["no_valid_long"])
print("sista kortet passar inte -> pass:", round(s["last_nofit_pass"] / max(1, s["last_nofit"]), 2), "av", s["last_nofit"])
print("bluff fast han hade passande kort:", s["bluff_with_valid"], "av", s["moves"], "drag")
print("tomt bord -> bluff:", round(s["bluff_free"] / max(1, s["free"]), 2), "av", s["free"])
print("  tomt bord, <=3 kort -> bluff:", round(s["bluff_free_few"] / max(1, s["free_few"]), 2), "av", s["free_few"])
print("bluffar totalt:", s["bluff_total"], " säger eget kort:", s["bluff_own"], " säger spelat kort:", s["bluff_seen"], " lägger 2-7 säger J-A:", s["low_high"])
print("bluffar med D/K/A (ej sista kortet):", s["bluff_high_real"], " varav ess:", s["bluff_ace_real"], " med ett kort som passade:", s["bluff_valid_real"])
print("motståndaren har 1-2 kort: drag", s["near"], " pass:", round(s["near_pass"] / max(1, s["near"]), 2),
      " säger D/K/A:", round(s["near_high"] / max(1, s["near"]), 2), " varav ärligt:", round(s["near_high_honest"] / max(1, s["near_high"]), 2))
print("bluffkortet låg hos motståndaren:", s["bluff_opp_has"], "av", s["bluff_total"])
print("bluff samma valör annan färg:", s["bluff_same_value"])
print("bluff samma färg, steg upp:", dict(sorted(s["bluff_up"].items())))
