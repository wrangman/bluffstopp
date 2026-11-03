import os
import sys

USE_GRAPHICS = True  # True = spela i ett fönster med grafik, False = i terminalen

# "python main.py terminal" startar terminalen även om USE_GRAPHICS är True
use_graphics = USE_GRAPHICS
if len(sys.argv) > 1 and sys.argv[1] == "terminal":
   use_graphics = False

if use_graphics:
   os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"  # pygame skriver annars en hälsning i terminalen
   try:
      import pygame
   except ImportError:
      print("pygame-ce saknas (installera med: pip install pygame-ce), så spelet startar i terminalen.")
      use_graphics = False

if use_graphics:
   from graphic_ui import GraphicUI
   ui = GraphicUI()  # frågar efter namnet i fönstret
   ui.run()
else:
   from game import Game
   from terminal_ui import TerminalUI

   name = input("Vad heter du? ")
   if name.strip() == "":
      name = "Spelare 1"

   game = Game(name)
   ui = TerminalUI(game)
   ui.run()
