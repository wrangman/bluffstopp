import os
import subprocess
import time
from card import Card, card_ranks


class TerminalUI:
    def __init__(self, game):
        self.game = game
        self.messages = []  # det senaste som hänt, visas under bordet
        self.suit_codes = {"s": "♠", "h": "♥", "k": "♣", "r": "♦"}

        self.add_message(game.start_message)  # visa kortet som lades från talongen

    def clear(self):
        subprocess.run('cls' if os.name == 'nt' else 'clear', shell=True)

    def colored(self, card):
        if card.is_red(): #om det är röda kort ändra färgen på texten med denna ansi-kod
            return f"\033[31m{card}\033[0m"
        else:
            return f"{card}"

    def add_message(self, text):
        self.messages.append(text)
        if len(self.messages) > 6:
            self.messages.pop(0)  # visa bara de 6 senaste

    def show_table(self):
        game = self.game
        self.clear()

        print("========== BLUFFSTOPP ==========")
        print(f"Talongen: {game.deck.cards_left()} kort    {game.ai.name}: {game.ai.cards_left()} kort")
        print()

        for message in self.messages:
            print(message)
        print()

        if game.claim is None:
            print("Bordet: tomt, talongen är slut så vilket kort som helst får läggas")
        else:
            if game.last_player is None:
                who = "från talongen"
            elif game.last_player == game.human:
                who = "ditt drag"
            else:
                who = f"{game.ai.name}s drag"
            print(f"Bordet:  [ {self.colored(game.claim)} ]   ({who})")
        print()

        print("Din hand:")
        self.show_hand(game.human)
        print()

    def show_hand(self, player):
        # en lista med siffror framför, t.ex. "1. ♥ K"
        for i in range(len(player.hand)):
            print(f"{i + 1}. {self.colored(player.hand[i])}")

    def parse_code(self, code):
        # "hk" -> Card("♥", "K"), "s10" -> Card("♠", 10)
        code = code.strip().lower()
        if len(code) < 2:
            return None

        letter = code[0]
        rest = code[1:].upper()

        if letter not in self.suit_codes:
            return None

        if rest.isdigit():
            value = int(rest)
        else:
            value = rest

        if value not in card_ranks:
            return None

        return Card(self.suit_codes[letter], value)

    def human_syn(self):
        game = self.game
        answer = input(f"Vill du syna {game.ai.name}s kort? (j/n): ")

        if answer.strip().lower() == "j":
            was_bluff, text = game.syn()
            self.add_message(text)
            self.pause(text)
            return True
        return False

    def ai_syn(self):
        text = self.game.ai_try_syn()
        if text is not None:
            self.add_message(text)
            self.pause(text)
            return True
        return False

    def pause(self, text):
        # visar vad som hände och väntar på enter innan skärmen rensas
        print()
        print(">>> " + text)
        input("Tryck enter för att fortsätta...")

    def human_move(self):
        game = self.game

        while True:
            if game.can_stopp():
                choice = input("Välj kortnummer eller skriv 'stopp': ")
            else:
                choice = input("Välj kortnummer: ")
            choice = choice.strip().lower()

            if choice == "stopp" and game.can_stopp():
                self.add_message(game.stopp())
                return

            if not choice.isdigit():
                print("Skriv ett nummer.")
                continue

            index = int(choice) - 1
            if index < 0 or index >= game.human.cards_left():
                print("Du har inget kort med det numret.")
                continue

            card = game.human.hand[index]  # sparas innan det tas bort från handen

            code = input(f"Enter = lägg {self.colored(card)}, eller skriv vad du säger att det är för att bluffa (t.ex. hk, s4): ")
            if code.strip() == "":
                claimed_card = card  # inget skrivet = man säger det kort man faktiskt lägger
            else:
                claimed_card = self.parse_code(code)
                if claimed_card is None:
                    print("Förstår inte. Färg först (s, h, k, r) och sen valör (2-10, J, Q, K, A).")
                    continue

            if game.play_card(index, claimed_card):
                if card.same_as(claimed_card):
                    self.add_message(f"Du la {self.colored(card)}")
                else:
                    self.add_message(f"Du la {self.colored(card)} och sa {self.colored(claimed_card)} (bluff)")
                return

            print(f"Du kan inte säga {claimed_card} här. Samma färg och högre, eller samma valör i en annan färg.")

    def ai_move(self):
        game = self.game
        print(f"{game.ai.name} tänker...")

        is_bluff, text = game.ai_move()
        time.sleep(game.ai.think_time(is_bluff))  # väntan ligger här och inte i AIPlayer

        self.add_message(text)
        self.pause(text)

    def run(self):
        game = self.game

        while True:
            self.show_table()

            # 1. får man syna motståndarens kort?
            if game.can_syn():
                if game.current == game.human:
                    synade = self.human_syn()
                else:
                    synade = self.ai_syn()

                if synade:
                    self.show_table()

            # 2. har någon blivit av med alla kort?
            winner = game.winner()
            if winner is not None:
                self.show_table()
                if winner == game.human:
                    print("Du blev av med alla kort. Du vann!")
                else:
                    print(f"{game.ai.name} blev av med alla kort. {game.ai.name} vann!")
                break

            # 3. lägg ett kort eller säg stopp
            if game.current == game.human:
                self.human_move()
            else:
                self.ai_move()
