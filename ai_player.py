import random
from card import Card, card_ranks
from player import Player


class AIPlayer(Player):
    def __init__(self, name):
        super().__init__(name)  # kör Player sin __init__ så vi får name och hand

    def valid_cards(self, top):
        # positionerna för alla kort i handen som får läggas på top
        valid = []
        for i in range(len(self.hand)):
            if self.hand[i].can_follow(top):
                valid.append(i)
        return valid

    def choose_move(self, top):
        # ger tillbaka (position, kortet han säger) eller None om han säger stopp

        # ny sekvens: lägg lägsta kortet, ärligt
        if top is None:
            index = self.lowest_card_index()
            return (index, self.hand[index])

        # har han ett kort som passar lägger han det lägsta av dem, ärligt
        valid = self.valid_cards(top)
        if len(valid) > 0:
            lowest = valid[0]
            for i in valid:
                if self.hand[i].rank() < self.hand[lowest].rank():
                    lowest = i
            return (lowest, self.hand[lowest])

        # inget kort passar. han vill inte dra kort så han bluffar oftast
        if random.random() < 0.8:
            index = self.lowest_card_index()
            return (index, self.make_bluff(top))

        return None

    def make_bluff(self, top):
        # hittar på ett kort som låter rimligt att lägga på top
        suits = ["♠", "♥", "♣", "♦"]
        options = []

        # alternativ 1: samma färg, ett steg högre (går inte på ess)
        for value in card_ranks:
            if card_ranks[value] == top.rank() + 1:
                options.append(Card(top.suit, value))

        # alternativ 2: samma valör, annan färg
        other_suits = []
        for suit in suits:
            if suit != top.suit:
                other_suits.append(suit)
        options.append(Card(random.choice(other_suits), top.value))

        return random.choice(options)

    def wants_to_syn(self, claim, human_cards_left):
        # har han själv kortet vet han att det är bluff
        if self.has_card(claim.suit, claim.value):
            return True

        # om människan la sitt sista kort måste han syna, annars förlorar han
        if human_cards_left == 0:
            return True

        chance = 0.2
        if human_cards_left <= 2:
            chance = chance + 0.3  # människan är nära att vinna

        if len(self.valid_cards(claim)) == 0:
            chance = chance + 0.15  # han kan ändå inte lägga något

        if random.random() < chance:
            return True
        return False

    def think_time(self, is_bluff):
        # hur länge han "tänker" så det inte känns så dator
        seconds = random.uniform(1.0, 2.5)

        # när han bluffar tar det ibland längre, ibland lika lång eller kortare tid
        if is_bluff:
            seconds = seconds * random.choice([0.7, 1.0, 1.5])

        return seconds
