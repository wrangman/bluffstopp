from game import Game
from terminal_ui import TerminalUI


name = input("Vad heter du? ")
if name.strip() == "":
   name = "Spelare 1"

game = Game(name)
ui = TerminalUI(game)
ui.run()
