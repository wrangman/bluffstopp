import math
import os
import pygame
from deck import Deck

CARD_W = 96    # kortets storlek på skärmen i pixlar
CARD_H = 140
FLIP_TIME = 0.3  # sekunder för att vända ett kort
SPEED = 10       # hur snabbt korten glider mot sin plats, högre = snabbare

FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "cards")

# filerna heter t.ex. king_of_hearts.png och 10_of_spades.png
suit_names = {"♠": "spades", "♥": "hearts", "♣": "clubs", "♦": "diamonds"}
value_names = {"J": "jack", "Q": "queen", "K": "king", "A": "ace"}


class CardSprite:
   # bilderna laddas en gång och delas av alla kort
   fronts = {}      # "♥ K" -> framsida med skugga
   plain = {}       # "♥ K" -> framsida utan skugga (för de små korten i panelen)
   back = None      # baksida med skugga
   plain_back = None

   def __init__(self, card, x, y):
      self.card = card
      self.x = x          # var kortet är just nu (mitten)
      self.y = y
      self.angle = 0
      self.scale = 1
      self.target_x = x   # vart kortet är på väg
      self.target_y = y
      self.target_angle = 0
      self.target_scale = 1
      self.home_x = x     # platsen i solfjädern utan lyft, används när man klickar
      self.home_y = y
      self.home_angle = 0
      self.alpha = 255    # 0 = osynligt, 255 = helt synligt
      self.target_alpha = 255

      self.face_up = False       # vilken sida som syns just nu
      self.want_face_up = False  # vilken sida som ska synas
      self.flip = 0              # 0 = vänds inte, annars hur långt vändningen har kommit (0-1)
      self.delay = 0             # sekunder innan kortet börjar röra sig

      # bara för kort på bordet
      self.open_on_table = False  # vänds upp när någon synar kortet
      self.table_dx = 0           # lite huller om buller i högen, men aldrig snett
      self.table_dy = 0

   def distance_to_target(self):
      dx = self.target_x - self.x
      dy = self.target_y - self.y
      return math.sqrt(dx * dx + dy * dy)

   def is_moving(self):
      return self.delay <= 0 and self.distance_to_target() > 60

   def update(self, dt):
      if self.delay > 0:
         self.delay = self.delay - dt
         return

      # glid en bit mot målet varje bild. långt kvar = snabbt, nästan framme = långsamt
      step = dt * SPEED
      if step > 1:
         step = 1
      self.x = self.x + (self.target_x - self.x) * step
      self.y = self.y + (self.target_y - self.y) * step
      self.angle = self.angle + (self.target_angle - self.angle) * step
      self.scale = self.scale + (self.target_scale - self.scale) * step
      self.alpha = self.alpha + (self.target_alpha - self.alpha) * step

      if self.flip > 0:
         self.flip = self.flip + dt / FLIP_TIME
         if self.flip >= 0.5:
            self.face_up = self.want_face_up  # halvvägs är kortet tunt som en linje, då byts sidan
         if self.flip >= 1:
            self.flip = 0
      elif self.face_up != self.want_face_up:
         # baksidan vänds upp direkt, framsidan först när kortet är framme
         if not self.want_face_up or self.distance_to_target() < 40:
            self.flip = 0.01

   def draw(self, screen):
      if self.face_up:
         image = CardSprite.fronts[str(self.card)]
      else:
         image = CardSprite.back

      if self.flip > 0:
         # kortet trycks ihop på bredden och växer tillbaka med andra sidan upp
         width = int(image.get_width() * abs(1 - 2 * self.flip))
         if width < 1:
            width = 1
         image = pygame.transform.smoothscale(image, (width, image.get_height()))

      image = pygame.transform.rotozoom(image, self.angle, self.scale)
      if self.alpha < 250:
         image.set_alpha(int(self.alpha))
      rect = image.get_rect(center=(int(self.x), int(self.y)))
      screen.blit(image, rect)

   def contains(self, pos):
      # där kortet syns just nu
      return CardSprite.point_in_card(pos, self.x, self.y, self.angle, self.scale)

   def contains_home(self, pos):
      # på kortets plats i solfjädern. annars flyttar sig kortet undan musen när det lyfts
      return CardSprite.point_in_card(pos, self.home_x, self.home_y, self.home_angle, self.scale)

   @staticmethod
   def point_in_card(pos, x, y, angle, scale):
      # vrid tillbaka punkten så att kortet står rakt, sen räcker det att jämföra med bredd och höjd
      dx = pos[0] - x
      dy = pos[1] - y
      a = math.radians(angle)
      local_x = dx * math.cos(a) - dy * math.sin(a)
      local_y = dx * math.sin(a) + dy * math.cos(a)
      if abs(local_x) <= CARD_W * scale / 2 and abs(local_y) <= CARD_H * scale / 2:
         return True
      return False

   @staticmethod
   def file_name(card):
      if card.value in value_names:
         value = value_names[card.value]
      else:
         value = str(card.value)
      return f"{value}_of_{suit_names[card.suit]}.png"

   @staticmethod
   def load_images():
      # måste köras efter pygame.display.set_mode
      for card in Deck.make_deck():
         picture = pygame.image.load(os.path.join(FOLDER, CardSprite.file_name(card))).convert_alpha()
         front = CardSprite.make_front(picture)
         CardSprite.plain[str(card)] = front
         CardSprite.fronts[str(card)] = CardSprite.add_shadow(front)

      CardSprite.plain_back = CardSprite.make_back()
      CardSprite.back = CardSprite.add_shadow(CardSprite.plain_back)

   @staticmethod
   def make_front(picture):
      # bilderna saknar ram, så de läggs på ett vitt kort med rundade hörn
      card = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
      rect = card.get_rect()
      pygame.draw.rect(card, (255, 255, 255), rect, border_radius=8)
      picture = pygame.transform.smoothscale(picture, (CARD_W - 8, CARD_H - 8))
      card.blit(picture, (4, 4))
      pygame.draw.rect(card, (175, 175, 180), rect, 1, border_radius=8)
      return card

   @staticmethod
   def make_back():
      card = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
      rect = card.get_rect()
      pygame.draw.rect(card, (255, 255, 255), rect, border_radius=8)
      inner = rect.inflate(-8, -8)
      pygame.draw.rect(card, (22, 38, 82), inner, border_radius=6)
      gold = (201, 162, 72)
      pygame.draw.rect(card, gold, inner.inflate(-8, -8), 2, border_radius=5)

      # "BS" i mitten, B vit och S röd, en spader ovanför och ett streck under
      letter_font = pygame.font.SysFont("georgia,timesnewroman,serif", 34, True)
      b = letter_font.render("B", True, (255, 255, 255))
      s = letter_font.render("S", True, (220, 50, 50))
      x = (CARD_W - b.get_width() - s.get_width()) // 2
      y = CARD_H // 2 - b.get_height() // 2 + 4
      card.blit(b, (x, y))
      card.blit(s, (x + b.get_width(), y))

      symbol_font = pygame.font.SysFont("segoeuisymbol,dejavusans,arial", 18)
      spade = symbol_font.render("♠", True, gold)
      card.blit(spade, ((CARD_W - spade.get_width()) // 2, y - spade.get_height() + 2))
      line_y = y + b.get_height() + 4
      pygame.draw.line(card, gold, (24, line_y), (CARD_W - 24, line_y), 2)

      pygame.draw.rect(card, (175, 175, 180), rect, 1, border_radius=8)
      return card

   @staticmethod
   def add_shadow(card):
      # en mjuk skugga under kortet gör att det ser ut att ligga på bordet
      surface = pygame.Surface((CARD_W + 8, CARD_H + 8), pygame.SRCALPHA)
      pygame.draw.rect(surface, (0, 0, 0, 18), (2, 5, CARD_W + 4, CARD_H + 2), border_radius=10)
      pygame.draw.rect(surface, (0, 0, 0, 35), (4, 6, CARD_W, CARD_H), border_radius=8)
      surface.blit(card, (4, 2))
      return surface
