import os
import subprocess
import time
from card import Card, card_ranks

SHOW_AI_MEMORY = True  # felsökning: visa vad datorn kommer ihåg.
SHOW_AI_HAND = True  # felsökning: visa datorns hand.


class TerminalUI:
   def __init__(self, game):
      self.game = game
      self.messages = []  # det senaste som hänt, visas under bordet
      self.suit_codes = {"s": "♠", "h": "♥", "k": "♣", "r": "♦"}
      self.ai_hand_before = game.ai.hand[:]  # felsökning: datorns hand före hans senaste drag
      self.ai_played = None                   # felsökning: kortet han faktiskt la, None om han passade

      self.add_message(game.start_message)  # visa kortet som lades från leken

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
      if game.ai.cards_left() == 0:
         ai_text = "inga kort kvar"
      else:
         ai_text = f"{game.ai.cards_left()} kort"
      print(f"Leken: {game.deck.cards_left()} kort    {game.ai.name}: {ai_text}")
      print()

      if SHOW_AI_MEMORY:
         self.show_ai_memory()
      if SHOW_AI_HAND:
         self.show_ai_hand()

      for message in self.messages:
         print(message)
      print()

      if game.claim is None:
         print(f"Bordet: tomt, {game.current.name} får lägga vilket kort som helst")
      else:
         # kortet från leken vet alla vad det är. andra kort ligger upp och ned och får ett frågetecken
         if game.last_player is None:
            who = "från leken"
            mark = ""
         elif game.last_player == game.human:
            who = "ditt drag"
            mark = " ?"
         else:
            who = f"{game.ai.name}s drag"
            mark = " ?"
         print(f"Bordet:  [ {self.colored(game.claim)}{mark} ]   ({who})")
      print()

      if game.human.cards_left() == 0:
         print("Din hand: inga kort kvar")
      else:
         print("Din hand:")
         self.show_hand(game.human)
      print()

   def show_ai_memory(self):
      # bara för felsökning: visar vad datorn kommer ihåg just nu
      ai = self.game.ai
      print(f"--- {ai.name}s minne (felsökning) ---")
      print("Vet är spelade: " + self.card_list(ai.seen_cards))
      print("Du har sagt:    " + self.card_list(ai.claimed_cards))
      print("Du passade på:  " + self.card_list(ai.passed_on))
      print()

   def show_ai_hand(self):
      # bara för felsökning: visar datorns kort
      ai = self.game.ai
      # "före draget" står kvar så man kan se om kortet han sa fanns på handen
      print(f"--- {ai.name}s hand (felsökning) ---")
      print("Före draget: " + self.card_list(self.ai_hand_before, self.ai_played))
      print()

   def card_list(self, cards, marked=None):
      # korten efter varandra, röda kort i rött. "inga" om listan är tom.
      # kortet som är samma som marked får hakparenteser runt sig
      if len(cards) == 0:
         return "inga"
      text = ""
      for card in cards:
         if marked is not None and card.same_as(marked):
            text = text + "[" + self.colored(card) + "]  "
         else:
            text = text + self.colored(card) + "  "
      return text

   def show_hand(self, player):
      # upp till 6 kort: en lista. fler än 6: max 3 spalter så det inte blir så högt
      # numreringen går nedåt i spalt 1 först, sen spalt 2 osv.
      if len(player.hand) <= 6:
         columns = 1
      else:
         columns = 3

      # hur många rader behövs? avrunda uppåt
      rows = len(player.hand) // columns
      if len(player.hand) % columns != 0:
         rows = rows + 1

      for row in range(rows):
         line = ""
         for col in range(columns):
            i = col * rows + row  # positionen i handen för den här rutan
            if i < len(player.hand):
               card = player.hand[i]
               text = f"{i + 1}. {card}"
               spaces = " " * (12 - len(text))  # fyller ut så korten hamnar i raka spalter
               line = line + f"{i + 1}. {self.colored(card)}" + spaces
         print(line)

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

   def ai_call_bluff(self):
      # han funderar alltid en stund, så att väntan inte avslöjar om han säger bluffstopp
      print(f"{self.game.ai.name} funderar på ditt kort...")
      time.sleep(self.game.ai.bluff_think_time())

      card = self.game.last_card  # sparas innan bordet töms
      text = self.game.ai_try_call_bluff()
      if text is not None:
         self.show_bluff_call(card, text)
         return True
      return False

   def show_bluff_call(self, card, text):
      # kortet man sa bluffstopp på vänds upp, så det visas utan frågetecken
      self.add_message(text)
      print()
      print(f"Kortet vänds:  [ {self.colored(card)} ]")
      self.pause(text)

   def pause(self, text):
      # visar vad som hände och väntar på enter innan skärmen rensas
      print()
      print(">>> " + text)
      input("Tryck enter för att fortsätta...")

   def show_options(self):
      game = self.game
      line = f"1-{game.human.cards_left()} = Lägg kort"
      if game.can_call_bluff():
         line = line + "   (B)luffstopp!"
      if game.can_pass():
         line = line + "   (P)ass"
      line = line + "   (A)vsluta"
      print(line)

   def human_move(self):
      # ger tillbaka "spelat", "bluffstopp", "slut" eller "avsluta"
      game = self.game
      self.show_options()

      while True:
         choice = input("> ").strip().lower()

         if choice == "q" or choice == "a":
            return "avsluta"

         if (choice == "b" or choice == "s") and game.can_call_bluff():
            card = game.last_card  # sparas innan bordet töms
            was_bluff, text = game.call_bluff()
            self.show_bluff_call(card, text)
            return "bluffstopp"

         # har datorn lagt sitt sista kort och du inte säger bluffstopp har den vunnit
         if game.winner() is not None:
            return "slut"

         if choice == "p" and game.can_pass():
            self.add_message(game.pass_turn())
            return "spelat"

         if not choice.isdigit():
            print("Det valet finns inte.")
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
            return "spelat"

         print(f"Du kan inte säga {claimed_card} här. Samma färg och högre, eller samma valör i en annan färg.")

   def ai_move(self):
      game = self.game
      print(f"{game.ai.name} tänker...")

      # väntetiden slumpas först, sen bestämmer han sig. väntan ligger här och inte i AIPlayer
      seconds = game.ai.think_time()
      time.sleep(seconds)
      self.ai_hand_before = game.ai.hand[:]  # felsökning: spara handen innan kortet försvinner
      text = game.ai_move(seconds)
      if game.last_player == game.ai:
         self.ai_played = game.last_card  # det riktiga kortet han la
      else:
         self.ai_played = None  # han sa pass

      self.add_message(text)  # syns på bordet och i listan, så ingen enter behövs

   def end_round(self):
      # visar vem som vann. ger tillbaka True om man vill spela en omgång till
      game = self.game
      winner = game.winner()
      self.show_table()

      if winner == game.human:
         print("Du vann omgången!")
      else:
         print(f"{game.ai.name} vann omgången!")
      print()

      choice = input("Enter = ny omgång   q/a = avsluta\n> ").strip().lower()
      if choice == "q" or choice == "a":
         print("Spelet avslutades.")
         return False

      game.new_round(winner)  # vinnaren börjar nästa omgång
      self.ai_hand_before = game.ai.hand[:]
      self.ai_played = None
      self.messages = []
      self.add_message(f"Ny omgång! {winner.name} vann förra och börjar.")
      self.add_message(game.start_message)
      return True

   def run(self):
      game = self.game

      while True:
         self.show_table()

         if game.current == game.human:
            # om du inte kan säga bluffstopp och någon redan har 0 kort är omgången slut
            if not game.can_call_bluff() and game.winner() is not None:
               if self.end_round():
                  continue
               break

            action = self.human_move()

            if action == "avsluta":
               print("Spelet avslutades.")
               break
            if action == "slut":
               if self.end_round():
                  continue
               break

         else:
            # 1. datorn kan säga bluffstopp på ditt kort
            if game.can_call_bluff():
               if self.ai_call_bluff():
                  continue  # visa bordet igen innan datorn spelar

            # 2. har någon blivit av med alla kort?
            if game.winner() is not None:
               if self.end_round():
                  continue
               break

            # 3. datorn lägger ett kort eller säger pass
            self.ai_move()
