import math
import random
import time
import pygame
from card import Card
from game import Game
from scoreboard import Scoreboard
from card_sprite import CardSprite, CARD_W, CARD_H

SHOW_AI_HAND = False  # felsökning: visa datorns kort. F1 slår av och på under spelet

WIDTH = 1280
HEIGHT = 800

# färger
BACKGROUND = (241, 243, 244)
WHITE = (255, 255, 255)
TEXT = (30, 30, 34)
GRAY = (125, 125, 132)
LIGHT_GRAY = (205, 205, 210)
BORDER = (226, 226, 230)
RED = (222, 52, 52)
GREEN = (36, 150, 80)
DARK = (28, 30, 34)

# platser på skärmen
TABLE_X = 430     # mitten av bordet till vänster
AI_HAND_Y = 90
PILE_X = 430
PILE_Y = 296
DECK_X = 170      # leken ligger till vänster om mittkortet
DECK_Y = 296
HAND_Y = 668
BUTTON_Y = 498   # Pass och Bluffstopp ovanför handen
RIGHT_X = 796     # spalten till höger med poängen och händelserna. 24 px luft till kanten, som nedtill
RIGHT_W = 460
MINI_W = 52       # små kort i panelen där man väljer vad man säger
MINI_H = 76
LOG_BOTTOM = 776
LOG_OPEN_TOP = 140

# listan med spelare på startskärmen
RECENT_COUNT = 5     # så många av de senaste spelarna syns
LIST_TOP = 250
LIST_W = 420
LIST_ROW_H = 58

# datorns hand: större och tydligare när det är hans tur. din hand ändras aldrig
TABLE_SCALE = 0.9
AI_SCALE = {"active": 0.82, "waiting": 0.66, "none": 0.72}
ALPHA = {"active": 255, "waiting": 140, "none": 255}

# typsnitt. ♠ ♥ ♣ ♦ finns inte i Century Gothic, så de ritas med ett annat
TEXT_FONTS = "centurygothic,segoeui,arial"
BOLD_FONTS = "centurygothicfet,segoeuisemibold,arial"
ITALIC_FONTS = "centurygothickursiv,segoeui,arial"
SYMBOL_FONTS = "segoeuisymbol,dejavusans,arial"

suit_order = ["♠", "♥", "♣", "♦"]
value_order = [2, 3, 4, 5, 6, 7, 8, 9, 10, "J", "Q", "K", "A"]


class Button:
   def __init__(self, text, x, y, width, height, style):
      self.text = text
      self.rect = pygame.Rect(0, 0, width, height)
      self.rect.center = (x, y)
      self.style = style  # "primary" (röd), "secondary" (vit) eller "small" (liten grå)

   def contains(self, pos):
      return self.rect.collidepoint(pos)

   def draw(self, screen, font, enabled):
      hover = enabled and self.contains(pygame.mouse.get_pos())
      rect = self.rect.copy()
      radius = rect.height // 2
      if hover:
         rect.y = rect.y - 2  # knappen lyfts lite under musen

      if self.style == "small":
         if hover:
            pygame.draw.rect(screen, (226, 228, 232), rect, border_radius=radius)
         else:
            pygame.draw.rect(screen, BACKGROUND, rect, border_radius=radius)
         color = TEXT
      elif not enabled:
         pygame.draw.rect(screen, (232, 233, 236), rect, border_radius=radius)
         color = (172, 172, 178)
      else:
         # skuggan stannar kvar när knappen lyfts, så det ser ut som att den kommer upp mot musen
         shadow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
         if hover:
            shadow_alpha = 50
         else:
            shadow_alpha = 30
         pygame.draw.rect(shadow, (0, 0, 0, shadow_alpha), shadow.get_rect(), border_radius=radius)
         screen.blit(shadow, (self.rect.x, self.rect.y + 3))

         if self.style == "primary":
            if hover:
               pygame.draw.rect(screen, (238, 74, 74), rect, border_radius=radius)
            else:
               pygame.draw.rect(screen, RED, rect, border_radius=radius)
            color = WHITE
         else:
            pygame.draw.rect(screen, WHITE, rect, border_radius=radius)
            if hover:
               pygame.draw.rect(screen, DARK, rect, 2, border_radius=radius)
            else:
               pygame.draw.rect(screen, LIGHT_GRAY, rect, 2, border_radius=radius)
            color = DARK

      label = font.render(self.text, True, color)
      screen.blit(label, label.get_rect(center=rect.center))


class GraphicUI:
   def __init__(self):
      pygame.init()
      self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
      pygame.display.set_caption("Bluffstopp")
      self.clock = pygame.time.Clock()
      CardSprite.load_images()
      self.layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)  # för att tona ned en hel hand på en gång
      self.deck_images = {}

      self.font = pygame.font.SysFont(TEXT_FONTS, 16)
      self.symbol_font = pygame.font.SysFont(SYMBOL_FONTS, 16)
      self.small_font = pygame.font.SysFont(TEXT_FONTS, 14)
      self.small_symbol_font = pygame.font.SysFont(SYMBOL_FONTS, 14)
      self.bold_font = pygame.font.SysFont(BOLD_FONTS, 17)
      self.claim_font = pygame.font.SysFont(ITALIC_FONTS, 19)
      self.claim_symbol_font = pygame.font.SysFont(SYMBOL_FONTS, 19)
      self.title_font = pygame.font.SysFont(BOLD_FONTS, 22)
      self.heading_font = pygame.font.SysFont(BOLD_FONTS, 28)
      self.big_font = pygame.font.SysFont(BOLD_FONTS, 46)
      self.button_font = pygame.font.SysFont(BOLD_FONTS, 17)

      self.game = None
      self.state = "name"  # "name", "human", "ai_bluff_wait", "ai_wait", "reveal" eller "round_over"
      self.running = True
      self.name_text = ""
      # de senaste spelarna från scores.json. choice är raden som är vald,
      # och raden efter sista namnet är "Ny spelare". finns inga namn är den rad 0
      self.scoreboard = Scoreboard()
      self.players = self.scoreboard.recent_players(RECENT_COUNT)
      self.choice = 0
      self.messages = []   # [text, ord i svart, ord i grått]

      # korten på skärmen
      self.hand_sprites = []     # dina kort, i den ordning de syns
      self.ai_sprites = []
      self.pile_sprites = []     # korten på bordet i den här sekvensen
      self.leaving_sprites = []  # kort som tonas bort
      self.pile_cards = []
      self.next_delay = 0

      # hur hela händerna och leken syns just nu. glider mjukt som korten
      self.ai_alpha = 255
      self.deck_scale = TABLE_SCALE
      self.deck_alpha = 150

      self.selected = None   # kortet du har valt i handen
      self.hovered = None    # kortet musen är över
      self.deck_hover = False
      self.pile_hover = False
      self.code_text = ""    # kod som skrivs med tangenterna, t.ex. "hk"
      self.error_text = ""
      self.show_grid = False    # rutnätet med alla kort
      self.show_scores = False  # topplistan
      self.show_ai_hand = SHOW_AI_HAND
      self.log_open = True
      self.log_top = LOG_OPEN_TOP
      self.log_scroll = 0       # hur långt upp man har scrollat i händelserna

      self.wait_until = 0    # när datorn är klar med att tänka
      self.busy_until = 0    # datorn väntar tills korten har delats ut
      self.ai_seconds = 0
      self.reveal_title = ""
      self.reveal_line = ""
      self.reveal_was_bluff = False
      self.reveal_time = 0
      self.round_winner = None
      self.record_text = None

      self.pass_button = Button("Pass", TABLE_X - 85, BUTTON_Y, 150, 44, "secondary")
      self.bluff_button = Button("Bluffstopp!", TABLE_X + 85, BUTTON_Y, 150, 44, "primary")
      # i poängrutan, med samma luft till höger som till vänster
      restart_x = RIGHT_X + RIGHT_W - 26 - 46
      self.restart_button = Button("Starta om", restart_x, 94, 92, 34, "small")
      self.scores_button = Button("Visa", restart_x - 46 - 6 - 28, 94, 56, 34, "small")
      self.start_button = Button("Spela", WIDTH // 2, 470, 160, 46, "primary")
      if len(self.players) > 0:
         box, rows = self.name_list_rects()
         self.start_button.rect.centery = box.bottom + 52  # under listan
      self.again_button = Button("Ny omgång", WIDTH // 2 - 90, 500, 160, 44, "primary")
      self.end_button = Button("Avsluta", WIDTH // 2 + 90, 500, 160, 44, "secondary")

   def run(self):
      while self.running:
         dt = self.clock.tick(60) / 1000
         for event in pygame.event.get():
            self.handle_event(event)
         self.update(dt)
         self.draw()
         pygame.display.flip()
      pygame.quit()

   # ---------- spelets gång ----------

   def start_game(self):
      if self.choice < len(self.players):
         name = self.players[self.choice]
      else:
         name = self.name_text.strip()
         if name == "":
            name = "Spelare 1"
      self.game = Game(name)
      self.add_message(f"Spelomgången börjar. {self.game.current.name} börjar.")
      self.add_message(self.game.start_message)
      self.new_deal()

   def new_deal(self):
      # alla gamla kort tonas bort och nya delas ut från leken
      for sprite in self.hand_sprites + self.ai_sprites + self.pile_sprites:
         self.fade_away(sprite)
      self.hand_sprites = []
      self.ai_sprites = []
      self.pile_sprites = []
      self.pile_cards = []
      self.select(None)
      self.sync_sprites()
      self.busy_until = time.time() + 1.5
      self.next_step()

   def next_step(self):
      # vad händer nu? samma ordning som TerminalUI.run()
      game = self.game
      if game.current == game.human:
         # om du inte kan säga bluffstopp och någon redan har 0 kort är omgången slut
         if not game.can_call_bluff() and game.winner() is not None:
            self.end_round()
         else:
            self.state = "human"
         return

      # 1. datorn kan säga bluffstopp på ditt kort. han funderar alltid en stund
      if game.can_call_bluff():
         self.state = "ai_bluff_wait"
         self.wait_until = time.time() + game.ai.bluff_think_time()
         return
      self.ai_turn()

   def ai_turn(self):
      # 2. har någon blivit av med alla kort?
      if self.game.winner() is not None:
         self.end_round()
         return
      # 3. datorn lägger ett kort eller säger pass. väntetiden slumpas först
      self.ai_seconds = self.game.ai.think_time()
      self.wait_until = time.time() + self.ai_seconds
      self.state = "ai_wait"

   def ai_bluff_decision(self):
      game = self.game
      card = game.last_card   # sparas innan bordet töms
      claim = game.claim
      laid_by = game.last_player
      text = game.ai_try_call_bluff()
      if text is None:
         self.ai_turn()
      else:
         was_bluff = not card.same_as(claim)
         self.start_reveal(card, claim, game.ai, laid_by, was_bluff, text)

   def ai_play(self):
      text = self.game.ai_move(self.ai_seconds)
      self.add_message(text)
      self.sync_sprites()
      self.next_step()

   def must_answer_last_card(self):
      # datorn har lagt sitt sista kort: du kan bara säga bluffstopp eller godta
      return self.game.winner() is not None

   def play_selected(self, claimed_card):
      game = self.game
      if not game.is_valid_claim(claimed_card):
         self.error_text = f"Du kan inte säga {claimed_card} här. Välj ett annat kort att säga."
         return

      card = self.selected.card
      index = self.hand_index(card)
      if game.play_card(index, claimed_card):
         if card.same_as(claimed_card):
            self.add_message(f"Du la {card}")
         else:
            self.add_message(f"Du la {card} och sa {claimed_card} (bluff)")
         self.select(None)
         self.sync_sprites()
         self.next_step()

   def play_code(self):
      # Enter: utan kod läggs kortet ärligt, med kod bluffar man
      if self.code_text == "":
         self.play_selected(self.selected.card)
         return
      claimed_card = Card.from_code(self.code_text)
      if claimed_card is None:
         self.error_text = "Förstår inte. Färg först (s, h, k, r) och sen valör (2-10, J, Q, K, A)."
      else:
         self.play_selected(claimed_card)

   def human_pass(self):
      self.select(None)
      self.add_message(self.game.pass_turn())
      self.sync_sprites()
      self.next_step()

   def human_bluff(self):
      game = self.game
      self.select(None)
      card = game.last_card   # sparas innan bordet töms
      claim = game.claim
      caller = game.current
      laid_by = game.last_player
      was_bluff, text = game.call_bluff()
      self.start_reveal(card, claim, caller, laid_by, was_bluff, text)

   def start_reveal(self, card, claim, caller, laid_by, was_bluff, text):
      # kortet på bordet vänds upp. straffkorten kommer först när man har klickat vidare
      self.add_message(text)
      self.state = "reveal"
      self.reveal_was_bluff = was_bluff
      if was_bluff:
         self.reveal_title = "BLUFF!"
      else:
         self.reveal_title = "Det stämde!"
      self.reveal_line = f"{caller.name} synade. {laid_by.name} sa {claim} och kortet var {card}."
      self.reveal_time = time.time()
      if len(self.pile_sprites) > 0:
         self.pile_sprites[-1].open_on_table = True

   def end_reveal(self):
      if time.time() - self.reveal_time < 0.6:
         return  # så att man hinner se kortet innan ett dubbelklick hoppar förbi
      self.sync_sprites()
      self.next_step()

   def end_round(self):
      self.round_winner = self.game.winner()
      self.record_text = self.game.record_result()  # anropas en gång per omgång
      self.state = "round_over"
      self.select(None)
      self.sync_sprites()

   def next_round(self):
      winner = self.round_winner
      self.game.new_round(winner)  # vinnaren börjar nästa omgång
      self.messages = []
      self.add_message(f"Ny omgång! {winner.name} vann förra och börjar.")
      self.add_message(self.game.start_message)
      self.new_deal()

   def restart(self):
      # ny omgång direkt. den räknas inte i ställningen
      self.game.new_round(None)
      self.messages = []
      self.add_message(f"Omstart! {self.game.current.name} börjar.")
      self.add_message(self.game.start_message)
      self.new_deal()

   # ---------- korten på skärmen ----------

   def sync_sprites(self):
      # jämför korten på skärmen med spelet. kort som har bytt plats flyger dit,
      # nya kort kommer från leken och kort som inte finns kvar tonas bort
      game = self.game
      if game.claim is None:
         self.pile_cards = []
      elif game.last_card is not None and not self.has_card(self.pile_cards, game.last_card):
         self.pile_cards.append(game.last_card)

      free = []
      self.hand_sprites = self.keep_sprites(self.hand_sprites, game.human.hand, free)
      self.ai_sprites = self.keep_sprites(self.ai_sprites, game.ai.hand, free)
      self.pile_sprites = self.keep_sprites(self.pile_sprites, self.pile_cards, free)

      self.next_delay = 0
      self.add_sprites(self.hand_sprites, game.human.hand, free)
      self.add_sprites(self.ai_sprites, game.ai.hand, free)
      added = self.add_sprites(self.pile_sprites, self.pile_cards, free)
      for sprite in added:
         # kortet från leken ser alla, så det ligger med framsidan upp. lagda kort med baksidan upp
         sprite.open_on_table = game.last_player is None
         # lite huller om buller, men alltid rakt så det är lätt att se
         sprite.table_dx = random.randint(-8, 8)
         sprite.table_dy = random.randint(-6, 6)

      for sprite in free:
         self.fade_away(sprite)

      self.hand_sprites.sort(key=self.hand_order)
      if self.selected not in self.hand_sprites:
         self.select(None)

   def keep_sprites(self, sprites, cards, free):
      # behåller korten som finns kvar. de andra läggs i free så de kan flyga till sin nya plats
      kept = []
      for sprite in sprites:
         if self.has_card(cards, sprite.card):
            kept.append(sprite)
         else:
            free.append(sprite)
      return kept

   def add_sprites(self, sprites, cards, free):
      # lägger till kort som saknas på skärmen. ger tillbaka de nya
      added = []
      for card in cards:
         found = False
         for sprite in sprites:
            if sprite.card.same_as(card):
               found = True
         if found:
            continue

         sprite = None
         for old in free:
            if old.card.same_as(card):
               sprite = old
         if sprite is not None:
            free.remove(sprite)  # kortet flyger från där det var
         else:
            sprite = CardSprite(card, DECK_X, DECK_Y)  # kortet kommer från leken
            sprite.scale = TABLE_SCALE
            sprite.delay = self.next_delay
            self.next_delay = self.next_delay + 0.09  # korten kommer ett i taget
         sprites.append(sprite)
         added.append(sprite)
      return added

   def fade_away(self, sprite):
      # kortet lyfts lite och tonas bort där det är
      sprite.target_y = sprite.y - 30
      sprite.target_alpha = 0
      sprite.want_face_up = False
      self.leaving_sprites.append(sprite)

   def has_card(self, cards, card):
      for other in cards:
         if other.same_as(card):
            return True
      return False

   def hand_index(self, card):
      # var kortet ligger i spelarens hand i Game (ordningen på skärmen är sorterad)
      hand = self.game.human.hand
      for i in range(len(hand)):
         if hand[i].same_as(card):
            return i
      return -1

   def hand_order(self, sprite):
      # sortera handen efter färg och sen valör
      return suit_order.index(sprite.card.suit) * 100 + sprite.card.rank()

   def hand_sprite_at(self, pos):
      # det valda kortet sticker upp, så det kollas först. sen uppifrån och ned i högen
      if self.selected is not None and self.selected.contains(pos):
         return self.selected
      for i in range(len(self.hand_sprites) - 1, -1, -1):
         if self.hand_sprites[i].contains_home(pos):
            return self.hand_sprites[i]
      return None

   def select(self, sprite):
      self.selected = sprite
      self.code_text = ""
      self.error_text = ""
      self.show_grid = False

   def turn_mode(self):
      # hur datorns hand ska synas: "active" på hans tur, "waiting" på din, "none" däremellan
      if self.state == "human":
         return "waiting"
      if self.state == "ai_wait" or self.state == "ai_bluff_wait":
         return "active"
      return "none"

   def no_popup(self):
      return not self.show_grid and not self.show_scores

   def can_click_deck(self):
      # klicka på leken = pass
      if self.state != "human" or not self.no_popup() or self.must_answer_last_card():
         return False
      return self.game.can_pass() and self.game.deck.cards_left() > 0

   def can_click_pile(self):
      # klicka på mittkortet = syna, bara på motståndarens kort
      if self.state != "human" or not self.no_popup():
         return False
      return self.game.can_call_bluff() and len(self.pile_sprites) > 0

   def deck_rect(self):
      rect = pygame.Rect(0, 0, int(CARD_W * self.deck_scale), int(CARD_H * self.deck_scale))
      rect.center = (DECK_X, DECK_Y)
      return rect

   def layout(self):
      # bestämmer vart alla kort ska. själva rörelsen sköter CardSprite.update
      mouse = pygame.mouse.get_pos()
      self.hovered = None
      if self.can_choose_card():
         self.hovered = self.hand_sprite_at(mouse)
      self.deck_hover = self.can_click_deck() and self.deck_rect().collidepoint(mouse)
      self.pile_hover = self.can_click_pile() and self.pile_sprites[-1].contains(mouse)

      ai_mode = self.turn_mode()
      self.fan(self.hand_sprites, HAND_Y, 1, 640, 1)
      self.fan(self.ai_sprites, AI_HAND_Y, AI_SCALE[ai_mode], 440, -1)

      for sprite in self.hand_sprites:
         sprite.want_face_up = True
      for sprite in self.ai_sprites:
         sprite.want_face_up = self.show_ai_hand

      for i in range(len(self.pile_sprites)):
         sprite = self.pile_sprites[i]
         sprite.target_x = PILE_X + sprite.table_dx
         sprite.target_y = PILE_Y + sprite.table_dy
         sprite.target_angle = 0
         sprite.want_face_up = sprite.open_on_table
         sprite.target_scale = TABLE_SCALE
         if i == len(self.pile_sprites) - 1:
            # det översta kortet blir större när man synar det eller har musen över det
            if self.state == "reveal":
               sprite.target_scale = 1.3
            elif self.pile_hover:
               sprite.target_scale = 1.0

   def fan(self, sprites, y, scale, max_width, direction):
      # lägger korten som en solfjäder. fler kort = mindre mellanrum, så hela handen får plats.
      # direction 1 = din hand (böjd nedåt i kanterna), -1 = datorns hand (spegelvänd)
      n = len(sprites)
      if n == 0:
         return
      width = CARD_W * scale
      max_width = max_width * scale
      spacing = width * 0.62
      if n > 1 and (max_width - width) / (n - 1) < spacing:
         spacing = (max_width - width) / (n - 1)
      step = 30 / n  # vinkel mellan korten
      if step > 4:
         step = 4

      for i in range(n):
         sprite = sprites[i]
         offset = i - (n - 1) / 2  # negativt till vänster om mitten
         dx = offset * spacing
         sprite.home_x = TABLE_X + dx
         sprite.home_y = y + direction * dx * dx / 3000
         sprite.home_angle = -offset * step * direction

         lift = 0
         if sprite == self.selected:
            lift = 40
         elif sprite == self.hovered:
            lift = 16
         # lyft kortet i den riktning det lutar
         a = math.radians(sprite.home_angle)
         sprite.target_x = sprite.home_x - lift * math.sin(a)
         sprite.target_y = sprite.home_y - lift * math.cos(a)
         sprite.target_angle = sprite.home_angle
         sprite.target_scale = scale

   def suggested_claims(self, card):
      # ger tillbaka [dina kort, andra kort] som man får säga just nu.
      # dina egna kort först: dem kan datorn inte veta att du ljuger om
      game = self.game
      own = []
      for sprite in self.hand_sprites:
         other = sprite.card
         if not other.same_as(card) and game.is_valid_claim(other) and len(own) < 6:
            own.append(other)

      # sen de vanligaste bluffarna: samma valör i en annan färg och de närmaste högre i samma färg
      base = game.claim
      if base is None:
         base = card  # tomt bord: utgå från kortet man lägger
      near = []
      for other in game.allowed_claims():
         if other.value == base.value and not other.same_as(base):
            near.append(other)
      for step in range(1, 4):
         for other in game.allowed_claims():
            if other.suit == base.suit and other.rank() == base.rank() + step:
               near.append(other)

      rest = []
      for other in near:
         if other.same_as(card) or self.has_card(own, other) or self.has_card(rest, other):
            continue
         if len(own) + len(rest) < 8:
            rest.append(other)
      return [own, rest]

   def can_choose_card(self):
      if self.game is None or self.state != "human" or not self.no_popup():
         return False
      return not self.must_answer_last_card()

   # ---------- tangenter och mus ----------

   def handle_event(self, event):
      if event.type == pygame.QUIT:
         self.running = False
      elif event.type == pygame.KEYDOWN:
         self.handle_key(event)
      elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
         self.handle_click(event.pos)
      elif event.type == pygame.MOUSEWHEEL:
         # scrolla bland händelserna, bara när listan är öppen
         if self.game is not None and self.log_open and self.log_rect().collidepoint(pygame.mouse.get_pos()):
            self.log_scroll = self.log_scroll + event.y * 40

   def handle_key(self, event):
      enter = event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER

      if self.state == "name":
         if enter:
            self.start_game()
         elif event.key == pygame.K_UP:
            if self.choice > 0:
               self.choice = self.choice - 1
         elif event.key == pygame.K_DOWN:
            if self.choice < len(self.players):
               self.choice = self.choice + 1
         elif event.key == pygame.K_BACKSPACE:
            if self.choice == len(self.players):
               self.name_text = self.name_text[:-1]
         elif event.unicode != "" and event.unicode.isprintable() and len(self.name_text) < 16:
            # börjar man skriva hoppar man till "Ny spelare"
            self.choice = len(self.players)
            self.name_text = self.name_text + event.unicode
         return

      if self.show_scores:
         if event.key == pygame.K_ESCAPE or enter:
            self.show_scores = False
         return
      if event.key == pygame.K_F1:
         self.show_ai_hand = not self.show_ai_hand
         return
      if self.state == "reveal":
         if enter or event.key == pygame.K_SPACE:
            self.end_reveal()
         return
      if self.state == "round_over":
         if enter:
            self.next_round()
         return
      if self.state != "human":
         return

      if self.must_answer_last_card():
         if event.key == pygame.K_b:
            self.human_bluff()
         elif enter:
            self.end_round()  # godta
         return

      if self.selected is None:
         if event.key == pygame.K_p and self.game.can_pass():
            self.human_pass()
         elif event.key == pygame.K_b and self.game.can_call_bluff():
            self.human_bluff()
         elif event.unicode.isdigit() and event.unicode != "0":
            index = int(event.unicode) - 1
            if index < len(self.hand_sprites):
               self.select(self.hand_sprites[index])
         return

      # ett kort är valt: det man skriver blir en kod, t.ex. hk
      if event.key == pygame.K_ESCAPE:
         if self.show_grid:
            self.show_grid = False
         else:
            self.select(None)
      elif enter:
         self.play_code()
      elif event.key == pygame.K_BACKSPACE:
         self.code_text = self.code_text[:-1]
      elif event.unicode.isalnum() and len(self.code_text) < 3:
         self.code_text = self.code_text + event.unicode.lower()
         self.error_text = ""

   def handle_click(self, pos):
      if self.state == "name":
         if self.start_button.contains(pos):
            self.start_game()
            return
         if len(self.players) > 0:
            box, rows = self.name_list_rects()
            for i in range(len(rows)):
               if rows[i].collidepoint(pos):
                  if i == self.choice and i < len(self.players):
                     self.start_game()  # klick på samma namn igen = spela, som med korten
                  else:
                     self.choice = i
         return

      if self.show_scores:
         self.show_scores = False  # klick var som helst stänger topplistan
         return
      if self.scores_button.contains(pos):
         self.show_scores = True
         return
      if self.restart_button.contains(pos):
         self.restart()
         return
      if self.log_header_rect().collidepoint(pos):
         self.log_open = not self.log_open
         self.log_scroll = 0
         return
      if self.state == "reveal":
         self.end_reveal()
         return
      if self.state == "round_over":
         if self.again_button.contains(pos):
            self.next_round()
         elif self.end_button.contains(pos):
            self.running = False
         return
      if self.state != "human":
         return

      if self.show_grid:
         card = self.grid_card_at(pos)
         if card is not None and self.game.is_valid_claim(card):
            self.play_selected(card)
         elif not self.grid_rect().collidepoint(pos):
            self.show_grid = False
         return

      # syna genom att klicka på knappen eller på mittkortet
      if self.game.can_call_bluff():
         if (self.buttons_visible() and self.bluff_button.contains(pos)) or (self.pile_hover and self.pile_sprites[-1].contains(pos)):
            self.human_bluff()
            return
      if self.must_answer_last_card():
         if self.buttons_visible() and self.pass_button.contains(pos):
            self.end_round()  # knappen heter Godta just då
         return
      # pass genom att klicka på knappen eller på leken
      if self.game.can_pass():
         if (self.buttons_visible() and self.pass_button.contains(pos)) or (self.can_click_deck() and self.deck_rect().collidepoint(pos)):
            self.human_pass()
            return

      if self.selected is not None:
         for item in self.panel_items():
            if item[0].collidepoint(pos):
               self.play_selected(item[1])
               return
         if self.all_cards_rect().collidepoint(pos):
            self.show_grid = True
            return

      sprite = self.hand_sprite_at(pos)
      if sprite is None:
         self.select(None)
      elif sprite == self.selected:
         self.play_selected(sprite.card)  # klick på samma kort igen = lägg det ärligt
      else:
         self.select(sprite)

   # ---------- uppdatering ----------

   def update(self, dt):
      if self.game is not None:
         self.layout()

      for sprite in self.pile_sprites + self.ai_sprites + self.hand_sprites + self.leaving_sprites:
         sprite.update(dt)

      # kort som har tonats bort behövs inte längre
      still_here = []
      for sprite in self.leaving_sprites:
         if sprite.alpha > 8:
            still_here.append(sprite)
      self.leaving_sprites = still_here

      if self.game is None:
         return

      # händerna, leken och händelselistan glider mot sina mål
      step = dt * 10
      if step > 1:
         step = 1
      ai_mode = self.turn_mode()
      self.ai_alpha = self.ai_alpha + (ALPHA[ai_mode] - self.ai_alpha) * step
      if self.deck_hover:
         self.deck_scale = self.deck_scale + (1.0 - self.deck_scale) * step
         self.deck_alpha = self.deck_alpha + (255 - self.deck_alpha) * step
      else:
         self.deck_scale = self.deck_scale + (TABLE_SCALE - self.deck_scale) * step
         self.deck_alpha = self.deck_alpha + (150 - self.deck_alpha) * step
      self.log_top = self.log_top + (self.log_target_top() - self.log_top) * step

      if self.show_scores:
         # spelet står still medan topplistan visas
         self.wait_until = self.wait_until + dt
         self.busy_until = self.busy_until + dt
         return

      now = time.time()
      if now < self.wait_until or now < self.busy_until:
         return
      if self.state == "ai_bluff_wait":
         self.ai_bluff_decision()
      elif self.state == "ai_wait":
         self.ai_play()

   def add_message(self, text):
      # orden ritas en gång här, inte varje bild
      new = self.render_words(text, self.font, self.symbol_font, TEXT)
      old = self.render_words(text, self.font, self.symbol_font, GRAY)
      self.messages.append([text, new, old])
      if len(self.messages) > 200:
         self.messages.pop(0)
      self.log_scroll = 0  # visa det nyaste

   # ---------- ritning ----------

   def draw(self):
      self.screen.fill(BACKGROUND)
      if self.game is None:
         self.draw_name_screen()
         return

      self.draw_score_panel()
      self.draw_log_panel()
      self.draw_table_texts()
      self.draw_deck()
      moving = self.draw_sprites()

      if self.buttons_visible():
         self.draw_hint()
         self.draw_buttons()
      elif self.state == "human" and self.selected is not None and not self.show_grid:
         self.draw_claim_panel()

      # kort som flyger ritas efter knapparna, annars åker de under dem
      for sprite in moving:
         sprite.draw(self.screen)
      for sprite in self.leaving_sprites:
         sprite.draw(self.screen)
      if self.state == "ai_wait" or self.state == "ai_bluff_wait":
         self.draw_thinking()
      if self.state == "reveal":
         self.draw_reveal()
      if self.show_grid:
         self.draw_grid()
      if self.state == "round_over":
         self.draw_round_over()
      if self.show_scores:
         self.draw_scores()

   def draw_name_screen(self):
      if len(self.players) > 0:
         self.draw_player_list()
         return

      # ingen har spelat än: bara en ruta för namnet
      title = self.big_font.render("Bluffstopp", True, RED)
      self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 260)))
      question = self.bold_font.render("Vad heter du?", True, TEXT)
      self.screen.blit(question, question.get_rect(center=(WIDTH // 2, 340)))

      box = pygame.Rect(0, 0, 320, 48)
      box.center = (WIDTH // 2, 395)
      pygame.draw.rect(self.screen, WHITE, box, border_radius=10)
      pygame.draw.rect(self.screen, LIGHT_GRAY, box, 2, border_radius=10)
      text = self.name_text
      if int(time.time() * 2) % 2 == 0:
         text = text + "|"  # blinkande markör
      label = self.claim_font.render(text, True, TEXT)
      self.screen.blit(label, (box.x + 14, box.centery - label.get_height() // 2))

      self.start_button.draw(self.screen, self.button_font, True)

   def name_list_rects(self):
      # panelen med listan, och en ruta per rad. "Ny spelare" är sista raden
      count = len(self.players) + 1
      box = pygame.Rect(0, 0, LIST_W, count * LIST_ROW_H + 32)
      box.midtop = (WIDTH // 2, LIST_TOP)
      rows = []
      for i in range(count):
         y = box.y + 16 + i * LIST_ROW_H
         rows.append(pygame.Rect(box.x + 16, y, box.width - 32, LIST_ROW_H - 6))
      return box, rows

   def draw_player_list(self):
      # som rutan för namnet, fast man väljer bland de som spelat senast
      title = self.big_font.render("Bluffstopp", True, RED)
      self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 150)))
      question = self.bold_font.render("Vem spelar?", True, TEXT)
      self.screen.blit(question, question.get_rect(center=(WIDTH // 2, 218)))

      box, rows = self.name_list_rects()
      self.draw_panel(box)
      mouse = pygame.mouse.get_pos()
      for i in range(len(rows)):
         row = rows[i]
         radius = row.height // 2
         # vald rad får mörk ram som en knapp under musen, raden under musen blir grå
         if row.collidepoint(mouse) and i != self.choice:
            pygame.draw.rect(self.screen, BACKGROUND, row, border_radius=radius)
         if i == self.choice:
            pygame.draw.rect(self.screen, DARK, row, 2, border_radius=radius)

         # en rund bricka med första bokstaven, eller + för en ny spelare
         center = (row.x + 30, row.centery)
         pygame.draw.circle(self.screen, BACKGROUND, center, 19)
         pygame.draw.circle(self.screen, BORDER, center, 19, 1)
         if i < len(self.players):
            letter = self.title_font.render(self.players[i][0].upper(), True, TEXT)
         else:
            letter = self.title_font.render("+", True, GRAY)
         self.screen.blit(letter, letter.get_rect(center=center))

         x = row.x + 62
         if i < len(self.players):
            self.draw_player_row(row, x, self.players[i])
         else:
            self.draw_new_player_row(row, x, i == self.choice)

      self.start_button.draw(self.screen, self.button_font, True)

   def draw_player_row(self, row, x, name):
      label = self.bold_font.render(name, True, TEXT)
      self.screen.blit(label, (x, row.y + 7))
      wins = self.scoreboard.wins(name)
      losses = self.scoreboard.losses(name)
      info = self.small_font.render(f"{wins} vunna, {losses} förlorade", True, GRAY)
      self.screen.blit(info, (x, row.y + 29))

   def draw_new_player_row(self, row, x, chosen):
      if not chosen:
         label = self.bold_font.render("Ny spelare", True, TEXT)
         self.screen.blit(label, (x, row.centery - label.get_height() // 2))
         return

      # vald: raden blir samma ruta för namnet som när ingen har spelat än
      box = pygame.Rect(x - 6, row.y + 7, row.right - 14 - x, row.height - 14)
      pygame.draw.rect(self.screen, WHITE, box, border_radius=10)
      pygame.draw.rect(self.screen, LIGHT_GRAY, box, 2, border_radius=10)
      blink = int(time.time() * 2) % 2 == 0
      if self.name_text == "" and not blink:
         hint = self.font.render("Skriv ditt namn", True, LIGHT_GRAY)
         self.screen.blit(hint, (box.x + 12, box.centery - hint.get_height() // 2))
         return
      text = self.name_text
      if blink:
         text = text + "|"  # blinkande markör
      label = self.claim_font.render(text, True, TEXT)
      self.screen.blit(label, (box.x + 12, box.centery - label.get_height() // 2))

   def draw_panel(self, rect):
      pygame.draw.rect(self.screen, WHITE, rect, border_radius=22)
      pygame.draw.rect(self.screen, BORDER, rect, 1, border_radius=22)

   def draw_score_panel(self):
      game = self.game
      panel = pygame.Rect(RIGHT_X, 24, RIGHT_W, 100)
      self.draw_panel(panel)

      name = game.human.name
      title = self.title_font.render(f"{name} vs {game.ai.name}", True, TEXT)
      # rubriken har en egen rad. för långt namn: korta det med …
      room = panel.width - 52
      short = name
      while title.get_width() > room and len(short) > 1:
         short = short[:-1]
         title = self.title_font.render(f"{short}… vs {game.ai.name}", True, TEXT)
      self.screen.blit(title, title.get_rect(midleft=(panel.x + 26, panel.y + 36)))

      wins = game.scoreboard.wins(name)
      losses = game.scoreboard.losses(name)
      score = self.font.render(f"Aktuell poängställning: {wins} – {losses}", True, TEXT)
      self.screen.blit(score, score.get_rect(midleft=(panel.x + 26, self.scores_button.rect.centery)))

      self.scores_button.draw(self.screen, self.button_font, True)
      self.restart_button.draw(self.screen, self.button_font, True)

   def log_target_top(self):
      if self.log_open:
         return LOG_OPEN_TOP
      # stängd: bara plats för det senaste meddelandet
      lines = 1
      if len(self.messages) > 0:
         lines = len(self.wrap(self.messages[-1][1], RIGHT_W - 52))
      return LOG_BOTTOM - 62 - lines * 22

   def log_rect(self):
      top = int(self.log_top)
      return pygame.Rect(RIGHT_X, top, RIGHT_W, LOG_BOTTOM - top)

   def log_header_rect(self):
      rect = self.log_rect()
      return pygame.Rect(rect.x, rect.y, rect.width, 46)

   def draw_log_panel(self):
      panel = self.log_rect()
      self.draw_panel(panel)

      header = self.log_header_rect()
      heading = self.small_font.render("HÄNDELSER", True, GRAY)
      self.screen.blit(heading, (panel.x + 26, panel.y + 18))
      if header.collidepoint(pygame.mouse.get_pos()):
         color = RED
      else:
         color = TEXT
      # chevron: pekar ned när listan är öppen (stäng), upp när den är stängd (öppna)
      cx = panel.right - 32
      cy = panel.y + 26
      if self.log_open:
         points = [(cx - 7, cy - 3), (cx, cy + 4), (cx + 7, cy - 3)]
      else:
         points = [(cx - 7, cy + 3), (cx, cy - 4), (cx + 7, cy + 3)]
      pygame.draw.lines(self.screen, color, False, points, 3)

      if len(self.messages) == 0:
         return
      area = pygame.Rect(panel.x + 26, panel.y + 46, panel.width - 52, panel.height - 60)

      if not self.log_open:
         # "hard mode": bara det senaste som hänt
         lines = self.wrap(self.messages[-1][1], area.width)
         for j in range(len(lines)):
            self.draw_line(lines[j], area.x, area.y + j * 22, False)
         return

      # alla rader, nyast längst ned. äldre meddelanden är gråa
      rows = []
      for i in range(len(self.messages)):
         if i == len(self.messages) - 1:
            words = self.messages[i][1]
         else:
            words = self.messages[i][2]
         for line in self.wrap(words, area.width):
            rows.append(line)
         rows.append(None)  # lite luft mellan meddelandena
      total = 0
      for row in rows:
         if row is None:
            total = total + 8
         else:
            total = total + 22

      # man kan inte scrolla längre än listan räcker
      most = total - area.height
      if most < 0:
         most = 0
      if self.log_scroll > most:
         self.log_scroll = most
      if self.log_scroll < 0:
         self.log_scroll = 0

      y = area.bottom - total + self.log_scroll
      self.screen.set_clip(area)
      for row in rows:
         if row is None:
            y = y + 8
         else:
            self.draw_line(row, area.x, y, False)
            y = y + 22
      self.screen.set_clip(None)

   def draw_table_texts(self):
      game = self.game

      # datorn: namn och antal kort. antalet räknas på skärmen så det stämmer med animationerna
      label = self.bold_font.render(game.ai.name, True, TEXT)
      self.screen.blit(label, label.get_rect(center=(TABLE_X, 162)))
      count = self.small_font.render(f"({len(self.ai_sprites)} kort kvar)", True, TEXT)
      self.screen.blit(count, count.get_rect(center=(TABLE_X, 181)))

      # du: "Johan (6)" under handen
      name = self.bold_font.render(game.human.name, True, TEXT)
      count = self.font.render(f" ({len(self.hand_sprites)})", True, TEXT)
      x = TABLE_X - (name.get_width() + count.get_width()) // 2
      self.screen.blit(name, (x, 780 - name.get_height() // 2))
      self.screen.blit(count, (x + name.get_width(), 780 - count.get_height() // 2))

      # leken
      label = self.font.render("Kortlek", True, TEXT)
      self.screen.blit(label, label.get_rect(center=(DECK_X, 384)))
      count = self.font.render(f"({self.game.deck.cards_left()} kort kvar)", True, GRAY)
      self.screen.blit(count, count.get_rect(center=(DECK_X, 406)))

      # bordet. när ett kort vänds är bordet redan tomt i Game, men kortet ligger kvar på skärmen
      if self.state == "reveal":
         return
      if game.claim is None:
         empty = pygame.Rect(0, 0, int(CARD_W * TABLE_SCALE), int(CARD_H * TABLE_SCALE))
         empty.center = (PILE_X, PILE_Y)
         pygame.draw.rect(self.screen, LIGHT_GRAY, empty, 2, border_radius=8)
         if game.current == game.human:
            text = "Bordet är tomt – du lägger valfritt kort"
         else:
            text = f"Bordet är tomt – {game.current.name} lägger valfritt kort"
         words = self.render_words(text, self.claim_font, self.claim_symbol_font, GRAY)
      else:
         if game.last_player is None:
            text = f"Från leken: {game.claim}"
         elif game.last_player == game.human:
            text = f"Du sa: {game.claim} ?"
         else:
            text = f"{game.ai.name} sa: {game.claim} ?"
         words = self.render_words(text, self.claim_font, self.claim_symbol_font, TEXT)
      self.draw_line(words, PILE_X, 384, True)

   def deck_image(self, layers):
      # leken ritas som några baksidor på varandra. sparas så det inte görs varje bild
      if layers not in self.deck_images:
         back = CardSprite.back
         surface = pygame.Surface((back.get_width() + 6, back.get_height() + 6), pygame.SRCALPHA)
         for i in range(layers):
            offset = (layers - 1 - i) * 3
            surface.blit(back, (6 - offset, 6 - offset))
         self.deck_images[layers] = surface
      return self.deck_images[layers]

   def draw_deck(self):
      left = self.game.deck.cards_left()
      if left == 0:
         empty = pygame.Rect(0, 0, int(CARD_W * TABLE_SCALE), int(CARD_H * TABLE_SCALE))
         empty.center = (DECK_X, DECK_Y)
         pygame.draw.rect(self.screen, LIGHT_GRAY, empty, 2, border_radius=8)
         return

      layers = 1
      if left > 10:
         layers = 3
      elif left > 1:
         layers = 2
      image = pygame.transform.rotozoom(self.deck_image(layers), 0, self.deck_scale)
      image.set_alpha(int(self.deck_alpha))
      self.screen.blit(image, image.get_rect(center=(DECK_X, DECK_Y)))

      if self.deck_hover:
         self.draw_card_hover(self.deck_rect(), "Pass – dra kort")

   def draw_card_hover(self, rect, text):
      # kortet tonas ned lite och texten visar vad som händer om man klickar
      cover = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
      pygame.draw.rect(cover, (20, 22, 28, 80), cover.get_rect(), border_radius=8)
      self.screen.blit(cover, rect)

      label = self.button_font.render(text, True, WHITE)
      pill = pygame.Rect(0, 0, label.get_width() + 24, 28)
      pill.midbottom = (rect.centerx, rect.y - 6)
      pygame.draw.rect(self.screen, DARK, pill, border_radius=14)
      self.screen.blit(label, label.get_rect(center=pill.center))

   def draw_zone(self, sprites, alpha):
      # hela handen tonas ned på en gång, annars syns korten igenom varandra
      if alpha >= 250:
         for sprite in sprites:
            sprite.draw(self.screen)
         return
      self.layer.fill((0, 0, 0, 0))
      for sprite in sprites:
         sprite.draw(self.layer)
      self.layer.set_alpha(int(alpha))
      self.screen.blit(self.layer, (0, 0))

   def draw_sprites(self):
      # ritar korten som ligger still. ger tillbaka korten som flyger, de ritas sist av draw()
      pile = []
      ai = []
      hand = []
      moving = []
      for sprite in self.pile_sprites:
         if sprite.is_moving():
            moving.append(sprite)
         else:
            pile.append(sprite)
      for sprite in self.ai_sprites:
         if sprite.is_moving():
            moving.append(sprite)
         else:
            ai.append(sprite)
      for sprite in self.hand_sprites:
         if sprite == self.selected:
            continue
         if sprite.is_moving():
            moving.append(sprite)
         else:
            hand.append(sprite)
      if self.selected is not None:
         hand.append(self.selected)

      for sprite in pile:
         sprite.draw(self.screen)
      self.draw_pile_extras()
      self.draw_zone(ai, self.ai_alpha)
      for sprite in hand:
         sprite.draw(self.screen)
      return moving

   def draw_pile_extras(self):
      # frågetecknet på mittkortet, och "Syna kort" när musen är över det
      if len(self.pile_sprites) == 0:
         return
      top = self.pile_sprites[-1]
      if top.is_moving():
         return
      width = int(CARD_W * top.scale)
      height = int(CARD_H * top.scale)
      rect = pygame.Rect(0, 0, width, height)
      rect.center = (int(top.x), int(top.y))

      if self.pile_hover:
         self.draw_card_hover(rect, "Syna kort")

      if self.game.claim is not None and self.game.last_player is not None and not top.face_up:
         center = (rect.right - 4, rect.y + 4)
         pygame.draw.circle(self.screen, WHITE, center, 18)
         pygame.draw.circle(self.screen, DARK, center, 16)
         mark = self.heading_font.render("?", True, WHITE)
         self.screen.blit(mark, mark.get_rect(center=(center[0], center[1] + 1)))

   def buttons_visible(self):
      # knapparna ligger ovanför handen. när ett kort är valt syns panelen där i stället
      if self.state == "human":
         return self.selected is None and self.no_popup()
      return self.state == "ai_wait" or self.state == "ai_bluff_wait"

   def draw_buttons(self):
      game = self.game
      my_turn = self.state == "human"
      if my_turn and self.must_answer_last_card():
         self.pass_button.text = "Godta"
         self.pass_button.draw(self.screen, self.button_font, True)
      else:
         self.pass_button.text = "Pass"
         self.pass_button.draw(self.screen, self.button_font, my_turn and game.can_pass())
      self.bluff_button.draw(self.screen, self.button_font, my_turn and game.can_call_bluff())

   def draw_hint(self):
      game = self.game
      color = TEXT
      if self.state != "human":
         text = f"{game.ai.name}s tur"
         color = GRAY
      elif self.must_answer_last_card():
         text = f"{game.ai.name} la sitt sista kort! Syna eller godta."
      elif game.claim is None:
         text = "Din tur – lägg valfritt kort"
      else:
         text = "Din tur – välj ett kort"
      label = self.bold_font.render(text, True, color)
      self.screen.blit(label, label.get_rect(center=(TABLE_X, 450)))

   def draw_thinking(self):
      # en pratbubbla till vänster om datorns hand
      if self.state == "ai_bluff_wait":
         text = "Funderar på ditt kort"
      else:
         text = "Tänker"
      dots = int(time.time() * 3) % 4
      label = self.small_font.render(text + "." * dots, True, TEXT)
      full = self.small_font.render(text + "...", True, TEXT)  # bubblan ändrar inte storlek med prickarna
      bubble = pygame.Rect(0, 0, full.get_width() + 36, 36)
      bubble.midright = (TABLE_X - 215, AI_HAND_Y)
      pygame.draw.rect(self.screen, WHITE, bubble, border_radius=18)
      pygame.draw.rect(self.screen, LIGHT_GRAY, bubble, 1, border_radius=18)
      tip = [(bubble.right - 2, bubble.centery - 7), (bubble.right - 2, bubble.centery + 7), (bubble.right + 12, bubble.centery)]
      pygame.draw.polygon(self.screen, WHITE, tip)
      self.screen.blit(label, (bubble.x + 18, bubble.centery - label.get_height() // 2))

   def panel_items(self):
      # [ruta, kort] för korten i panelen: det riktiga kortet, dina kort, andra kort.
      # lite luft mellan grupperna
      groups = [[self.selected.card]]
      suggestions = self.suggested_claims(self.selected.card)
      for group in suggestions:
         if len(group) > 0:
            groups.append(group)

      total = 100
      for group in groups:
         total = total + len(group) * (MINI_W + 8) + 16
      x = TABLE_X - total // 2
      items = []
      for group in groups:
         for card in group:
            rect = pygame.Rect(x, 438, MINI_W, MINI_H)
            items.append([rect, card])
            x = x + MINI_W + 8
         x = x + 16
      return items

   def all_cards_rect(self):
      items = self.panel_items()
      last = items[len(items) - 1][0]
      return pygame.Rect(last.right + 12, last.centery - 20, 92, 40)

   def draw_claim_panel(self):
      items = self.panel_items()
      button = self.all_cards_rect()
      panel = pygame.Rect(items[0][0].x - 16, items[0][0].y - 14, button.right - items[0][0].x + 32, MINI_H + 28)
      pygame.draw.rect(self.screen, WHITE, panel, border_radius=16)
      pygame.draw.rect(self.screen, LIGHT_GRAY, panel, 1, border_radius=16)

      honest_ok = self.game.is_valid_claim(self.selected.card)

      # ingen förklaring behövs. text bara när man skriver en kod eller något inte går
      note = None
      if self.error_text != "":
         note = self.small_font.render(self.error_text, True, WHITE)
         note_color = RED
      elif self.code_text != "":
         note = self.small_font.render(f"Du skriver: {self.code_text}", True, WHITE)
         note_color = DARK
      if note is not None:
         pill = pygame.Rect(0, 0, note.get_width() + 24, 26)
         pill.midbottom = (panel.centerx, panel.y - 6)
         pygame.draw.rect(self.screen, note_color, pill, border_radius=13)
         self.screen.blit(note, note.get_rect(center=pill.center))

      mouse = pygame.mouse.get_pos()
      for i in range(len(items)):
         rect = items[i][0]
         card = items[i][1]
         y = rect.y
         if rect.collidepoint(mouse):
            y = y - 5  # kortet under musen lyfts lite
         self.screen.blit(self.mini_image(card), (rect.x, y))
         if i == 0:
            if honest_ok:
               pygame.draw.rect(self.screen, GREEN, (rect.x - 3, y - 3, MINI_W + 6, MINI_H + 6), 3, border_radius=8)
            else:
               self.dim(rect.x, y)

      # knappen för alla kort
      if button.collidepoint(mouse):
         pygame.draw.rect(self.screen, (232, 232, 236), button, border_radius=20)
      pygame.draw.rect(self.screen, DARK, button, 2, border_radius=20)
      label = self.button_font.render("Alla…", True, DARK)
      self.screen.blit(label, label.get_rect(center=button.center))

   def grid_rect(self):
      rect = pygame.Rect(0, 0, 820, 440)
      rect.center = (WIDTH // 2, HEIGHT // 2)
      return rect

   def grid_items(self):
      # alla 52 kort: en rad per färg, 2 till ess
      box = self.grid_rect()
      items = []
      for row in range(len(suit_order)):
         for col in range(len(value_order)):
            rect = pygame.Rect(box.x + 37 + col * (MINI_W + 6), box.y + 70 + row * (MINI_H + 12), MINI_W, MINI_H)
            items.append([rect, Card(suit_order[row], value_order[col])])
      return items

   def grid_card_at(self, pos):
      for item in self.grid_items():
         if item[0].collidepoint(pos):
            return item[1]
      return None

   def draw_grid(self):
      self.shade_screen()
      box = self.grid_rect()
      pygame.draw.rect(self.screen, WHITE, box, border_radius=20)
      title = self.bold_font.render("Välj vad du säger att kortet är", True, TEXT)
      self.screen.blit(title, title.get_rect(center=(box.centerx, box.y + 32)))
      hint = self.small_font.render("Gråa kort får man inte säga här · Esc = stäng", True, GRAY)
      self.screen.blit(hint, hint.get_rect(center=(box.centerx, box.bottom - 22)))

      mouse = pygame.mouse.get_pos()
      for item in self.grid_items():
         rect = item[0]
         card = item[1]
         allowed = self.game.is_valid_claim(card)
         y = rect.y
         if allowed and rect.collidepoint(mouse):
            y = y - 6
         self.screen.blit(self.mini_image(card), (rect.x, y))
         if not allowed:
            self.dim(rect.x, y)
         if card.same_as(self.selected.card):
            pygame.draw.rect(self.screen, GREEN, (rect.x - 3, y - 3, MINI_W + 6, MINI_H + 6), 3, border_radius=8)

   def draw_reveal(self):
      if self.reveal_was_bluff:
         color = RED
      else:
         color = GREEN
      box = pygame.Rect(0, 0, 620, 110)
      box.midtop = (TABLE_X, 412)
      pygame.draw.rect(self.screen, WHITE, box, border_radius=18)
      pygame.draw.rect(self.screen, color, box, 3, border_radius=18)
      title = self.big_font.render(self.reveal_title, True, color)
      self.screen.blit(title, title.get_rect(center=(box.centerx, box.y + 32)))
      words = self.render_words(self.reveal_line, self.font, self.symbol_font, TEXT)
      self.draw_line(words, box.centerx, box.y + 68, True)
      more = self.small_font.render("Klicka eller tryck Enter för att fortsätta", True, GRAY)
      self.screen.blit(more, more.get_rect(center=(box.centerx, box.y + 92)))

   def draw_round_over(self):
      self.shade_screen()
      game = self.game
      box = pygame.Rect(0, 0, 520, 300)
      box.center = (WIDTH // 2, 420)
      pygame.draw.rect(self.screen, WHITE, box, border_radius=22)

      if self.round_winner == game.human:
         title = self.big_font.render("Du vann!", True, GREEN)
      else:
         title = self.big_font.render(f"{game.ai.name} vann!", True, RED)
      self.screen.blit(title, title.get_rect(center=(box.centerx, box.y + 60)))

      lines = [game.score_text(), game.streak_text()]
      if self.record_text is not None:
         lines.append(self.record_text)
      y = box.y + 115
      for line in lines:
         label = self.font.render(line, True, TEXT)
         self.screen.blit(label, label.get_rect(center=(box.centerx, y)))
         y = y + 28

      self.again_button.draw(self.screen, self.button_font, True)
      self.end_button.draw(self.screen, self.button_font, True)

   def draw_scores(self):
      # topplistan med alla spelare i scores.json
      self.shade_screen()
      rows = self.game.scoreboard.top_list()
      shown = rows[:12]
      box = pygame.Rect(0, 0, 560, 150 + len(shown) * 30)
      box.center = (WIDTH // 2, HEIGHT // 2)
      pygame.draw.rect(self.screen, WHITE, box, border_radius=22)

      title = self.heading_font.render("Topplista", True, TEXT)
      self.screen.blit(title, title.get_rect(center=(box.centerx, box.y + 38)))

      columns = [box.x + 40, box.x + 290, box.x + 380, box.x + 480]
      headings = ["Namn", "Vunna", "Förlorade", "Bäst i rad"]
      for i in range(len(headings)):
         label = self.small_font.render(headings[i], True, GRAY)
         if i == 0:
            self.screen.blit(label, (columns[i], box.y + 76))
         else:
            self.screen.blit(label, label.get_rect(midtop=(columns[i], box.y + 76)))

      y = box.y + 104
      if len(shown) == 0:
         label = self.font.render("Inga spelade omgångar än.", True, GRAY)
         self.screen.blit(label, (columns[0], y))
      for row in shown:
         # du själv står i fetstil
         if row[0] == self.game.human.name:
            font = self.bold_font
         else:
            font = self.font
         label = font.render(str(row[0]), True, TEXT)
         self.screen.blit(label, (columns[0], y))
         for i in range(1, 4):
            label = font.render(str(row[i]), True, TEXT)
            self.screen.blit(label, label.get_rect(midtop=(columns[i], y)))
         y = y + 30

      hint = self.small_font.render("Klicka var som helst för att stänga", True, GRAY)
      self.screen.blit(hint, hint.get_rect(center=(box.centerx, box.bottom - 22)))

   # ---------- hjälpmetoder för ritning ----------

   def mini_image(self, card):
      key = "mini " + str(card)
      if key not in CardSprite.plain:
         CardSprite.plain[key] = pygame.transform.smoothscale(CardSprite.plain[str(card)], (MINI_W, MINI_H))
      return CardSprite.plain[key]

   def dim(self, x, y):
      # lägger en ljus hinna över ett litet kort som inte går att välja
      cover = pygame.Surface((MINI_W, MINI_H), pygame.SRCALPHA)
      pygame.draw.rect(cover, (241, 243, 244, 185), cover.get_rect(), border_radius=6)
      self.screen.blit(cover, (x, y))

   def shade_screen(self):
      shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
      shade.fill((20, 22, 28, 120))
      self.screen.blit(shade, (0, 0))

   def render_words(self, text, font, symbol_font, color):
      # delar upp texten i ord. färgsymbolerna ritas med symbol_font,
      # och ♥ och ♦ och valören efter dem blir röda
      words = []
      red_next = False
      for word in text.split(" "):
         if "♥" in word or "♦" in word:
            words.append(symbol_font.render(word, True, RED))
            red_next = len(word) == 1  # bara symbolen, då kommer valören i nästa ord
         elif "♠" in word or "♣" in word:
            words.append(symbol_font.render(word, True, color))
            red_next = False
         elif red_next:
            words.append(font.render(word, True, RED))
            red_next = False
         else:
            words.append(font.render(word, True, color))
      return words

   def wrap(self, words, max_width):
      # delar upp orden i rader som får plats
      lines = []
      line = []
      width = 0
      space = self.font.size(" ")[0]
      for word in words:
         if len(line) > 0 and width + space + word.get_width() > max_width:
            lines.append(line)
            line = []
            width = 0
         if len(line) > 0:
            width = width + space
         line.append(word)
         width = width + word.get_width()
      if len(line) > 0:
         lines.append(line)
      return lines

   def draw_line(self, words, x, y, center):
      if len(words) == 0:
         return
      space = self.font.size(" ")[0]
      if center:
         total = 0
         for word in words:
            total = total + word.get_width() + space
         x = x - (total - space) // 2
         y = y - words[0].get_height() // 2
      for word in words:
         self.screen.blit(word, (x, y))
         x = x + word.get_width() + space
