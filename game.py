import random
from deck import Deck
from player import Player
from ai_player import AIPlayer


class Game:
    def __init__(self, player_name):
        # 1. Skapa kortlek och spelare
        temp = Deck.make_deck()
        cards = Deck.shuffle_deck(temp)
        self.deck = Deck(cards)  # resten blir talongen

        self.human = Player(player_name)
        self.ai = AIPlayer("Datorn")

        # 2. Dela ut 6 kort var
        self.human.take_cards(self.deck.deal(6))
        self.ai.take_cards(self.deck.deal(6))

        self.claim = None        # kortet man SÄGER att man la
        self.last_card = None    # kortet som faktiskt ligger där
        self.last_player = None  # den som la senaste kortet
        self.syn_used = False    # man får bara syna en gång per tur

        # slumpa vem som börjar
        if random.randint(0, 1) == 0:
            self.current = self.human
        else:
            self.current = self.ai

        # 3. första kortet från talongen annonseras och läggs på bordet
        self.start_message = self.flip_start_card()

    def opponent(self, player):
        if player == self.human:
            return self.ai
        else:
            return self.human

    def can_syn(self):
        # man får bara syna motståndarens kort
        if self.claim is None or self.syn_used:
            return False
        if self.last_player is None:
            return False  # kortet kom från talongen, det går inte att syna
        if self.last_player == self.current:
            return False
        return True

    def can_stopp(self):
        # är bordet tomt (talongen slut) måste man lägga ett kort
        if self.claim is None:
            return False
        return True

    def is_valid_claim(self, claimed_card):
        return claimed_card.can_follow(self.claim)

    def next_turn(self):
        self.current = self.opponent(self.current)
        self.syn_used = False

    def flip_start_card(self):
        # översta kortet i talongen annonseras och läggs upp och ned på bordet
        cards = self.deck.draw(1)
        if cards:
            self.last_card = cards[0]
            self.claim = cards[0]  # alla vet vilket kort det är, så det är ingen bluff
            self.last_player = None
            return f"Från talongen läggs {cards[0]} på bordet."
        else:
            return "Talongen är slut, vilket kort som helst får läggas."

    def new_sequence(self, starter):
        # bordet töms och ett nytt kort från talongen läggs ut
        self.claim = None
        self.last_card = None
        self.last_player = None
        self.current = starter
        self.syn_used = False
        return self.flip_start_card()

    def play_card(self, index, claimed_card):
        # kortet på index läggs med baksidan upp och man säger claimed_card
        if not self.is_valid_claim(claimed_card):
            return False

        self.last_card = self.current.remove_card(index)
        self.claim = claimed_card
        self.last_player = self.current
        self.next_turn()
        return True

    def stopp(self):
        player = self.current
        drawn = self.deck.draw(1)
        player.take_cards(drawn)

        if drawn:
            text = f"{player.name} sa stopp och drog ett kort. "
        else:
            text = f"{player.name} sa stopp. "

        text = text + self.new_sequence(self.opponent(player))  # motståndaren börjar en ny sekvens
        return text

    def penalty(self, loser, winner):
        # den som hade fel drar 3 kort, eller tar 1 kort från motståndaren om talongen är slut
        if self.deck.cards_left() > 0:
            loser.take_cards(self.deck.draw(3))
            return f"{loser.name} drar 3 kort."

        card = winner.random_card()
        if card is None:
            return f"Talongen är slut och {winner.name} har inga kort att ge."

        loser.take_cards([card])
        return f"Talongen är slut, {loser.name} tar ett kort från {winner.name}."

    def syn(self):
        # vänder senaste kortet. ger tillbaka (var det bluff?, text om vad som hände)
        caller = self.current
        bluffer = self.last_player
        self.syn_used = True

        text = f"{caller.name} synar! {bluffer.name} sa {self.claim} och kortet var {self.last_card}. "

        if self.last_card.same_as(self.claim):
            text = text + "Det stämde! " + self.penalty(caller, bluffer)
            return False, text  # caller har kvar turen och måste lägga eller säga stopp
        else:
            text = text + "Det var bluff! " + self.penalty(bluffer, caller) + " "
            text = text + self.new_sequence(caller)  # bluffaren räknas som att den sa stopp
            return True, text

    def ai_try_syn(self):
        # datorn bestämmer om den vill syna. ger tillbaka text, eller None om den inte synar
        if self.ai.wants_to_syn(self.claim, self.human.cards_left()):
            was_bluff, text = self.syn()
            return text
        return None

    def ai_move(self):
        # datorn lägger ett kort eller säger stopp. ger tillbaka (bluffade han?, text)
        move = self.ai.choose_move(self.claim)

        if move is None:
            return False, self.stopp()

        index = move[0]
        claimed_card = move[1]
        real_card = self.ai.hand[index]

        is_bluff = not real_card.same_as(claimed_card)
        self.play_card(index, claimed_card)

        return is_bluff, f"{self.ai.name} lägger ett kort och säger: {claimed_card}"

    def winner(self):
        # kollas efter att motståndaren har fått chansen att syna
        if self.human.cards_left() == 0:
            return self.human
        if self.ai.cards_left() == 0:
            return self.ai
        return None
