import random
from deck import Deck
from player import Player
from ai_player import AIPlayer


class Game:
   def __init__(self, player_name):
      self.human = Player(player_name)
      self.ai = AIPlayer("Datorn")

      self.new_round(None)  # första omgången: slumpa vem som börjar

   def new_round(self, starter):
      # 1. Ny blandad kortlek
      temp = Deck.make_deck()
      cards = Deck.shuffle_deck(temp)
      self.deck = Deck(cards)  # resten blir leken

      # 2. Dela ut 6 kort var
      self.human.hand = []
      self.ai.hand = []
      self.human.take_cards(self.deck.deal(6))
      self.ai.take_cards(self.deck.deal(6))
      self.ai.forget_all()  # datorn glömmer korten från förra omgången

      self.claim = None       # kortet man SÄGER att man la
      self.last_card = None    # kortet som faktiskt ligger där
      self.last_player = None  # den som la senaste kortet
      self.bluff_called = False    # man får bara säga bluffstopp en gång per tur

      # den som vann förra omgången börjar, annars slumpas det
      if starter is not None:
         self.current = starter
      elif random.randint(0, 1) == 0:
         self.current = self.human
      else:
         self.current = self.ai

      # 3. första kortet från leken annonseras och läggs på bordet
      self.start_message = self.flip_start_card()

   def opponent(self, player):
      if player == self.human:
         return self.ai
      else:
         return self.human

   def can_call_bluff(self):
      # man får bara säga bluffstopp på motståndarens kort
      if self.claim is None or self.bluff_called:
         return False
      if self.last_player is None:
         return False  # kortet kom från leken, det går inte att säga bluffstopp på
      if self.last_player == self.current:
         return False
      return True

   def can_pass(self):
      # är bordet tomt (ny sekvens) måste man lägga ett kort
      if self.claim is None:
         return False
      return True

   def is_valid_claim(self, claimed_card):
      return claimed_card.can_follow(self.claim)

   def next_turn(self):
      self.current = self.opponent(self.current)
      self.bluff_called = False

   def flip_start_card(self):
      # bara när omgången börjar: översta kortet i leken annonseras och läggs på bordet
      cards = self.deck.draw(1)
      self.last_card = cards[0]
      self.claim = cards[0]  # alla vet vilket kort det är, så det är ingen bluff
      self.last_player = None
      self.ai.remember(cards[0])
      return f"Från leken läggs {cards[0]} på bordet."

   def new_sequence(self, starter):
      # efter pass eller bluffstopp: bordet töms och starter får lägga vilket kort som helst
      self.claim = None
      self.last_card = None
      self.last_player = None
      self.current = starter
      self.bluff_called = False
      return f"{starter.name} börjar om och får lägga vilket kort som helst."

   def play_card(self, index, claimed_card):
      # kortet på index läggs med baksidan upp och man säger claimed_card
      if not self.is_valid_claim(claimed_card):
         return False

      self.last_card = self.current.remove_card(index)
      if self.current == self.ai:
         self.ai.remember(self.last_card)  # datorn vet vilka kort han själv har lagt
      self.claim = claimed_card
      self.last_player = self.current
      self.next_turn()
      return True

   def pass_turn(self):
      player = self.current
      drawn = self.deck.draw(1)
      player.take_cards(drawn)

      if drawn:
         text = f"{player.name} sa pass och drog ett kort. "
      else:
         text = f"{player.name} sa pass. "

      text = text + self.new_sequence(self.opponent(player))  # motståndaren börjar en ny sekvens
      return text

   def penalty(self, loser, winner):
      # den som hade fel drar 3 kort, eller tar 1 kort från motståndaren om leken är slut
      if self.deck.cards_left() > 0:
         loser.take_cards(self.deck.draw(3))
         return f"{loser.name} drar 3 kort."

      card = winner.random_card()
      if card is None:
         return f"Leken är slut och {winner.name} har inga kort att spela."

      loser.take_cards([card])
      return f"Leken är slut, {loser.name} tar ett kort från {winner.name}."

   def call_bluff(self):
      # vänder senaste kortet. ger tillbaka (var det bluff?, text om vad som hände)
      caller = self.current        # den som säger bluffstopp
      laid_by = self.last_player   # den som la kortet
      self.bluff_called = True
      self.ai.remember(self.last_card)  # kortet vänds upp, så nu har datorn sett det

      text = f"{caller.name} säger bluffstopp! {laid_by.name} sa {self.claim} och kortet var {self.last_card}. "

      if self.last_card.same_as(self.claim):
         text = text + "Det stämde! " + self.penalty(caller, laid_by) + " "
         text = text + self.new_sequence(laid_by)  # den som la ärligt får turen igen
         return False, text
      else:
         text = text + "Det var bluff! " + self.penalty(laid_by, caller) + " "
         text = text + self.new_sequence(caller)  # bluffaren räknas som att den sa pass
         return True, text

   def ai_try_call_bluff(self):
      # datorn bestämmer om den vill säga bluffstopp. ger tillbaka text, eller None om den inte gör det
      if self.ai.wants_to_call_bluff(self.claim, self.human.cards_left()):
         was_bluff, text = self.call_bluff()
         return text
      self.ai.remember_claim(self.claim)  # han litade på det, men kommer ihåg att du sa det
      return None

   def ai_move(self, seconds):
      # datorn lägger ett kort eller säger pass efter att ha tänkt i seconds sekunder. ger tillbaka text
      move = self.ai.choose_move(self.claim, seconds, self.human.cards_left())

      if move is None:
         return self.pass_turn()

      index = move[0]
      claimed_card = move[1]
      self.play_card(index, claimed_card)

      return f"{self.ai.name} lägger ett kort och säger: {claimed_card}"

   def winner(self):
      # kollas efter att motståndaren har fått chansen att säga bluffstopp
      if self.human.cards_left() == 0:
         return self.human
      if self.ai.cards_left() == 0:
         return self.ai
      return None
