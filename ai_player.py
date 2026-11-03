import random
from card import Card, card_ranks
from player import Player

suits = ["♠", "♥", "♣", "♦"]


class AIPlayer(Player):
   def __init__(self, name):
      super().__init__(name)  # kör Player sin __init__ så vi får name och hand
      self.seen_cards = []    # kort han vet redan är spelade
      self.claimed_cards = [] # kort människan har sagt utan att han sa bluffstopp
      self.passed_on = []     # kort som låg på bordet när människan sa pass
      self.wrong_calls = 0    # hur många gånger i rad han har synat ett ärligt kort

   # ---------- minnet ----------

   def remember_call(self, was_bluff):
      # efter hans bluffstopp: hade han fel blir han försiktigare, hade han rätt vågar han igen
      if was_bluff:
         self.wrong_calls = 0
      else:
         self.wrong_calls = self.wrong_calls + 1

   def remember_pass(self, card):
      # människan passade på card och har nog inga högre kort i den färgen
      self.passed_on.append(card)

   def forget_passes(self):
      # människan har fått nya kort, så han vet inte längre vad som saknas på den handen
      self.passed_on = []

   def probably_missing(self, card):
      # har motståndaren passat på ett lägre kort i samma färg finns card nog inte på den handen
      for passed in self.passed_on:
         if passed.suit == card.suit and card.rank() > passed.rank():
            return True
      return False

   def remember(self, card):
      self.seen_cards.append(card)
      self.forget_some()

   def remember_claim(self, card):
      self.claimed_cards.append(card)
      self.forget_some()

   def forget_some(self):
      # med fler än 10 kort i minnet glömmer han 1-3 av de äldsta, annars blir han för svår att lura.
      # det glöms slumpat från båda minnena, men det sista kortet i ett minne glöms aldrig
      if len(self.seen_cards) + len(self.claimed_cards) <= 10:
         return

      for i in range(random.randint(1, 3)):
         can_seen = len(self.seen_cards) > 1
         can_claimed = len(self.claimed_cards) > 1

         if can_seen and can_claimed:
            # båda går att glömma från. ett större minne glömmer oftare
            total = len(self.seen_cards) + len(self.claimed_cards)
            if random.randint(1, total) <= len(self.seen_cards):
               self.seen_cards.pop(0)  # det äldsta kortet ligger först
            else:
               self.claimed_cards.pop(0)
         elif can_seen:
            self.seen_cards.pop(0)
         elif can_claimed:
            self.claimed_cards.pop(0)

   def forget_all(self):
      self.seen_cards = []  # ny omgång, ny lek
      self.claimed_cards = []
      self.passed_on = []
      self.wrong_calls = 0

   def has_seen(self, suit, value):
      for card in self.seen_cards:
         if card.suit == suit and card.value == value:
            return True
      return False

   def has_claimed(self, suit, value):
      for card in self.claimed_cards:
         if card.suit == suit and card.value == value:
            return True
      return False

   def is_known(self, suit, value):
      # kort han har själv eller vet är spelade. de kan inte finnas hos motståndaren
      return self.has_card(suit, value) or self.has_seen(suit, value)

   def valid_cards(self, top):
      # positionerna för alla kort i handen som får läggas på top
      valid = []
      for i in range(len(self.hand)):
         if self.hand[i].can_follow(top):
            valid.append(i)
      return valid

   # ---------- välja drag ----------

   def choose_move(self, top, seconds, opponent_cards, deck_left):
      # ger tillbaka (position, kortet han säger) eller None om han säger pass
      # han går igenom alla drag han kan göra, ger varje drag poäng och väljer det bästa.
      # seconds är hur länge han har tänkt, opponent_cards hur många kort motståndaren har,
      # deck_left hur många kort som är kvar i leken
      nerves = self.nerves(seconds)
      best_move = None
      best_score = None

      if top is not None:  # på tomt bord får man inte passa
         best_score = self.score_pass(opponent_cards, deck_left) + self.noise()

      for i in range(len(self.hand)):
         # slumpen läggs per kort och inte per påstående. annars får ett kort med många
         # möjliga bluffar fler "lotter", och bluffar vinner oftare än poängen säger
         card_noise = self.noise()
         for claim in self.possible_claims(self.hand[i], top):
            score = self.score_move(i, claim, top, nerves, opponent_cards, deck_left)
            score = score + card_noise + random.uniform(-0.1, 0.1)  # lite slump i vad han säger
            if best_score is None or score > best_score:
               best_score = score
               best_move = (i, claim)

      return best_move

   def possible_claims(self, card, top):
      # allt han kan säga när han lägger card: kortet självt om det passar, och bluffar.
      # bluffen får vara ett kort han själv har eller ett som redan spelats,
      # det är upp till motståndaren att komma ihåg det
      claims = []
      if card.can_follow(top):
         claims.append(card)  # ärligt

      for suit in suits:
         for value in card_ranks:
            other = Card(suit, value)
            if other.same_as(card) or not other.can_follow(top):
               continue

            if top is None:
               # tomt bord: bluffa med ett högre kort eller samma valör i en annan färg
               if other.rank() >= card.rank():
                  claims.append(other)
            elif other.suit == top.suit:
               # samma färg: högst 5 steg upp, annars blir det för misstänkt
               if other.rank() - top.rank() <= 5:
                  claims.append(other)
            else:
               claims.append(other)  # samma valör i en annan färg

      return claims

   def score_pass(self, opponent_cards, deck_left):
      # pass: han drar ett kort (om leken inte är slut) och motståndaren får börja om
      if deck_left > 0:
         draw = 1
      else:
         draw = 0
      return -draw - self.free_start_value(opponent_cards)

   def penalty_cost(self, deck_left):
      # hur många kort det kostar att ha fel vid bluffstopp
      if deck_left == 0:
         return 2  # man tar ett kort från motståndaren: själv ett kort mer och motståndaren ett mindre
      return min(3, deck_left)

   def score_move(self, index, claim, top, nerves, opponent_cards, deck_left):
      # poäng för att lägga kortet på index och säga claim, när top ligger på bordet
      card = self.hand[index]
      rest = self.hand[:index] + self.hand[index + 1:]  # handen efter draget

      if len(rest) == 0:
         score = 10  # han går ut
      else:
         score = 1  # ett kort mindre
         stop = self.stop_value(claim, opponent_cards)
         score = score + stop * 0.5 * (1 + self.free_start_value(len(rest)))
         # blockera: ju färre kort motståndaren har, desto viktigare att han inte kan lägga på
         score = score + stop * 2.5 / max(opponent_cards, 1)
         score = score + self.dump_value(card, rest)
         score = score + self.follow_value(claim, rest)
         # bluffa med ett kort som kunde ha sparats kostar. på tomt bord kostar det inget,
         # där hade kortet ändå kunnat läggas ärligt, så frågan är bara vad han säger
         if not card.same_as(claim) and top is not None:
            score = score - self.waste_value(card, top, rest)

      if card.same_as(claim):
         # ärligt, ingen risk. säger motståndaren ändå bluffstopp får motståndaren straffet
         # och han börjar om. det händer ibland, så det är värt lite
         if len(rest) > 0:
            score = score + 0.15 * (self.penalty_cost(deck_left) + self.free_start_value(len(rest)))
         return score

      # bluff: blir han synad får han straffet och motståndaren får börja om
      risk = self.call_risk(len(rest), nerves, top is None, claim, opponent_cards)
      caught = 1 - self.penalty_cost(deck_left) - self.free_start_value(opponent_cards)
      return (1 - risk) * score + risk * caught

   def free_start_value(self, cards_left):
      # hur mycket det är värt att få börja om med vilket kort som helst.
      # har man bara 1 kort kvar går man ut direkt
      if cards_left <= 1:
         return 10
      return 3 / cards_left

   def stop_value(self, claim, opponent_cards):
      # chansen att motståndaren inte kan lägga något på claim. 0 = kan säkert, 1 = kan inte
      # räknar kort han inte vet var de är, och hur många av dem som skulle passa
      fits = 0
      unknown = 0
      for suit in suits:
         for value in card_ranks:
            if self.is_known(suit, value):
               continue
            unknown = unknown + 1
            if Card(suit, value).can_follow(claim):
               if self.probably_missing(Card(suit, value)):
                  fits = fits + 0.5  # motståndaren passade på den färgen, så kortet är mindre troligt
               else:
                  fits = fits + 1

      # ju fler kort motståndaren har, desto troligare att något av dem passar
      return (1 - fits / max(unknown, 1)) ** opponent_cards

   def dump_value(self, card, rest):
      # hur skönt det är att bli av med card. låga kort kan nästan bara läggas på tomt bord,
      # höga kort kan läggas på många kort och är bra att spara.
      # ett kort som inte hör ihop med något annat i handen är också svårt att bli av med
      value = (14 - card.rank()) / 12 * 3
      if not self.in_series(card, rest):
         value = value + 0.5
      return value

   def waste_value(self, card, top, rest):
      # hur dumt det är att slänga card som bluff i stället för att spara det
      # högt kort: kan läggas ärligt på många kort senare, ett ess på alla lägre i samma färg
      value = (card.rank() - 2) / 12 * 4
      if top is not None and card.can_follow(top):
         value = value + 2  # kortet passar ju nu, då ska han inte ljuga med det
      if self.in_series(card, rest):
         value = value + 0.5  # det hör ihop med andra kort i handen
      return value

   def in_series(self, card, rest):
      # har han något annat kort i samma färg eller med samma valör?
      for other in rest:
         if other.suit == card.suit or other.value == card.value:
            return True
      return False

   def follow_value(self, claim, rest):
      # kan han lägga på det motståndaren svarar med? går igenom alla kort motståndaren
      # kan svara med på claim, och räknar hur många av dem han kan följa med något kort i rest
      answers = 0
      covered = 0
      for suit in suits:
         for value in card_ranks:
            if self.is_known(suit, value):
               continue  # kort han har eller vet är spelade kan motståndaren inte svara med
            answer = Card(suit, value)
            if not answer.can_follow(claim):
               continue
            answers = answers + 1
            for other in rest:
               if other.can_follow(answer):
                  covered = covered + 1
                  break

      if answers == 0:
         return 0  # motståndaren kan inte svara alls, det räknas redan i stop_value
      return covered / answers * 0.6

   def call_risk(self, cards_after, nerves, empty_table, claim, opponent_cards):
      # hur troligt han tror det är att motståndaren säger bluffstopp på claim
      if cards_after == 0:
         return 0.97  # på sista kortet synar man nästan alltid
      risk = 0.2 + nerves
      if cards_after == 1:
         risk = risk + 0.2
      if empty_table:
         risk = risk - 0.5  # på tomt bord är alla kort tillåtna, så motståndaren har ingen ledtråd
      risk = max(0.05, min(risk, 0.95))

      # vet motståndaren att det är bluff säger han bluffstopp, annars gäller risken ovan
      knows = self.opponent_knows(claim, opponent_cards)
      return knows + (1 - knows) * risk

   def opponent_knows(self, claim, opponent_cards):
      # hur troligt det är att motståndaren vet att claim är en bluff
      if self.has_card(claim.suit, claim.value):
         return 0  # han har kortet själv, så motståndaren kan inte ha det
      if self.has_claimed(claim.suit, claim.value):
         return 0.8  # motståndaren har själv sagt det kortet, och oftast var det sant
      if self.has_seen(claim.suit, claim.value):
         return 0.2  # kortet är redan spelat, motståndaren kanske minns det

      # annars: chansen att kortet ligger på motståndarens hand
      unknown = 0
      for suit in suits:
         for value in card_ranks:
            if not self.is_known(suit, value):
               unknown = unknown + 1
      return min(1, opponent_cards / unknown)

   def nerves(self, seconds):
      # hur nervös han är just nu. har han tvekat länge tror han att det syns på honom,
      # men med 1-2 kort kvar struntar han i det och försöker gå ut
      nerves = random.uniform(0.05, 0.65)
      if seconds > 2.0 and len(self.hand) > 2:
         nerves = nerves + 0.55
      return nerves

   def noise(self):
      # lite slump så han inte alltid gör exakt samma sak
      return random.uniform(-0.5, 0.5)

   # ---------- bluffstopp ----------

   def wants_to_call_bluff(self, claim, top_before, human_cards_left):
      # claim är det människan sa, top_before kortet som låg innan (None = bordet var tomt)

      # har han själv kortet vet han att det är bluff
      if self.has_card(claim.suit, claim.value):
         return True

      # har kortet redan spelats kan det inte ligga där igen
      if self.has_seen(claim.suit, claim.value):
         return True

      # om människan la sitt sista kort måste han säga bluffstopp, annars förlorar han
      if human_cards_left == 0:
         return True

      chance = self.bluff_chance(top_before, human_cards_left)

      # har människan redan sagt det kortet är en av gångerna bluff, men det kan lika gärna ha
      # varit förra gången. han jämför chansen nu med en vanlig gång (ungefär 0.3).
      # på tomt bord fanns det ingen anledning att ljuga nu, så då var det nog förra gången
      if self.has_claimed(claim.suit, claim.value):
         chance = chance / (chance + 0.3)

      # människan har passat på ett lägre kort i samma färg och har nog inga högre där
      if self.probably_missing(claim):
         chance = chance + 0.4

      # människan är nära att vinna. men ett lågt kort (2-7) är oftast ärligt, så då litar han på det
      if human_cards_left <= 2 and claim.rank() > 7:
         chance = chance + 0.2

      # kan han inte lägga något själv är pass eller bluff dyrt, så då vågar han lite mer.
      # gånger och inte plus: utan något skäl att misstänka blir det fortfarande lite
      if len(self.valid_cards(claim)) == 0:
         chance = chance * 1.5

      # har han haft fel när han synat blir han försiktigare, hälften så ofta för varje gång
      chance = chance * 0.5 ** self.wrong_calls

      if random.random() < chance:
         return True
      return False

   def bluff_chance(self, top_before, human_cards_left):
      # hur troligt det är att människan behövde ljuga
      if top_before is None:
         return 0.03  # på tomt bord passar alla kort, så det finns sällan någon anledning att ljuga

      # hur många av korten han inte vet var de är hade passat på top_before?
      fits = 0
      unknown = 0
      for suit in suits:
         for value in card_ranks:
            if not self.is_known(suit, value):
               unknown = unknown + 1
               if Card(suit, value).can_follow(top_before):
                  fits = fits + 1

      # chansen att inget kort passade på handen människan hade innan (ett kort mer än nu)
      no_fit = (1 - fits / max(unknown, 1)) ** (human_cards_left + 1)

      # passade inget kort bluffar man ungefär varannan gång, annars säger man pass.
      # av alla gånger ett kort läggs: hur stor del är bluffar?
      bluffing = no_fit * 0.5
      return bluffing / ((1 - no_fit) + bluffing)

   # ---------- väntetid ----------

   def think_time(self):
      # hur länge han "tänker" innan han lägger kort. slumpas innan han bestämmer sig
      return random.uniform(1.0, 2.5)

   def bluff_think_time(self):
      # hur länge han funderar på om han ska säga bluffstopp
      return random.uniform(0.5, 1.5)
