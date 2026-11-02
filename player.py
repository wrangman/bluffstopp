import random


class Player():
    def __init__(self, name):
        self.name = name
        self.hand = []

    def take_cards(self, cards):
        self.hand.extend(cards)

    def remove_card(self, index):
        return self.hand.pop(index)  # tar bort kortet på den positionen och skickar tillbaka det

    def cards_left(self):
        return len(self.hand)

    def has_card(self, suit, value):
        for card in self.hand:
            if card.suit == suit and card.value == value:
                return True
        return False

    def lowest_card_index(self):
        # letar upp positionen för det lägsta kortet i handen
        lowest = 0
        for i in range(len(self.hand)):
            if self.hand[i].rank() < self.hand[lowest].rank():
                lowest = i
        return lowest

    def random_card(self):
        # tar ett slumpat kort ur handen (används när leken är slut)
        if self.hand:
            r = random.randint(0, len(self.hand) - 1)
            return self.hand.pop(r)
        else:
            return None
