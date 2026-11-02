# Mappning för att kunna jämföra strängar ("J", "Q", "K", "A") med siffror
card_ranks = {
    2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7,
    8: 8, 9: 9, 10: 10, "J": 11, "Q": 12, "K": 13, "A": 14
}


class Card:
    def __init__(self, suit, value):
        self.suit = suit  #instans
        self.value = value

    def __str__(self):
        return f"{self.suit} {self.value}"

    def __repr__(self):                                #mer för utvecklare visa vad klassen innebär
        return f"Card('{self.suit}', {self.value})"

    def rank(self):
        return card_ranks[self.value]  # kortets värde som siffra, t.ex. K = 13

    def is_red(self):
        if self.suit == "♥" or self.suit == "♦":
            return True
        else:
            return False

    def same_as(self, other):
        # samma färg och samma valör = samma kort
        if self.suit == other.suit and self.value == other.value:
            return True
        else:
            return False

    def can_follow(self, top):
        # får det här kortet läggas på top?
        if top is None:
            return True  # ny sekvens, alla kort är okej

        if self.suit == top.suit and self.rank() > top.rank():
            return True  # samma färg och högre valör

        if self.value == top.value and self.suit != top.suit:
            return True  # samma valör, då byter man färg

        return False
