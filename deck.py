import random
from card import Card


class Deck:
   def __init__(self, cards=None):
      self.cards = cards #instans

   def cards_left(self):
      return len(self.cards)

   def deal(self, num_cards):
      if num_cards > len(self.cards):
         raise ValueError("Not enough cards left to deal")

      before = len(self.cards)
      dealt_cards = self.cards[:num_cards]
      self.cards = self.cards[num_cards:]  # Remove dealt cards from the deck

      # felsökning: all dragning går genom den här raden, så siffrorna är de riktiga
      print(f"[Kortlek] {before} - {len(dealt_cards)} = {len(self.cards)} kort kvar")

      return dealt_cards

   def draw(self, num_cards):
      # som deal, men kraschar inte om leken håller på att ta slut
      if num_cards > len(self.cards):
         num_cards = len(self.cards)

      return self.deal(num_cards)

   @staticmethod
   def shuffle_deck(cards):
      for c in range(len(cards)):
         # c är ett nummer eller position i kortleken

         r = random.randint(c, len(cards) - 1)  # randint tar med slutvärdet, så -1 för att inte hamna utanför listan

         temp_card = cards[r]

         cards[r] = cards[c]
         cards[c] = temp_card

      return cards

   @staticmethod           # en metod som metod likt vanlig metod men en @staticmethod tar inte emot instansen (self)
   def make_deck():
      cards = []
      suits = ["♠", "♥", "♣", "♦"]
      values = ["A", 2, 3, 4, 5, 6, 7, 8, 9, 10, "J", "Q", "K"]

      for suit in suits:   # 4 suits
         for value in values: # 13 values per suit
            cards.append(Card(suit, value))

      return cards
