import json
import os

# filen hamnar i samma mapp som spelet, oavsett var man startar det ifrån
SCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scores.json")


class Scoreboard:
   def __init__(self, filename=SCORE_FILE):
      self.filename = filename
      # namn -> {"wins": vunna, "losses": förlorade, "streak": vinster i rad just nu, "best_streak": rekordet}
      self.scores = {}
      self.load()

   def load(self):
      # finns ingen fil än börjar alla på 0
      if not os.path.exists(self.filename):
         return
      try:
         with open(self.filename, "r", encoding="utf-8") as file:
            self.scores = json.load(file)
      except ValueError:
         self.scores = {}  # filen är trasig, då börjar vi om från 0

   def save(self):
      with open(self.filename, "w", encoding="utf-8") as file:
         json.dump(self.scores, file, indent=3, ensure_ascii=False)  # ensure_ascii=False så å, ä, ö syns i filen

   def add_player(self, name):
      if name not in self.scores:
         self.scores[name] = {}
      # en äldre fil kan sakna några av siffrorna, då börjar de på 0
      for key in ["wins", "losses", "streak", "best_streak"]:
         if key not in self.scores[name]:
            self.scores[name][key] = 0

   def add_win(self, name):
      # ger tillbaka True om det blev nytt rekord i vinster i rad
      self.add_player(name)
      score = self.scores[name]
      score["wins"] = score["wins"] + 1
      score["streak"] = score["streak"] + 1
      if score["streak"] > score["best_streak"]:
         score["best_streak"] = score["streak"]
         return True
      return False

   def add_loss(self, name):
      self.add_player(name)
      self.scores[name]["losses"] = self.scores[name]["losses"] + 1
      self.scores[name]["streak"] = 0  # förlust = vinstsviten är bruten

   def wins(self, name):
      self.add_player(name)
      return self.scores[name]["wins"]

   def losses(self, name):
      self.add_player(name)
      return self.scores[name]["losses"]

   def streak(self, name):
      self.add_player(name)
      return self.scores[name]["streak"]

   def best_streak(self, name):
      self.add_player(name)
      return self.scores[name]["best_streak"]
