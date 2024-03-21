from classes.fractal.Fractal import FractalExplorer
from classes.player.player import Player
from classes.interpreter.interpreter import Interpreter
from classes.fractal_player.fractal_player import Fractal_Player

def player_main(shared_memory):
    player=Player(shared_memory)
    player.main()
def interpreter_main(shared_memory):
    interpreter = Interpreter(shared_memory)
    interpreter.main()
def fractal_player_main(shared_memory):
    fractal_player = Fractal_Player(shared_memory)
    fractal_player.main()

def fractal_main(shared_memory):
    explorer = FractalExplorer(rotation_speed=0.000000000001, width=shared_memory['width'], height=shared_memory['height'], zoom_factor=0.1,shared_memory=shared_memory)
    explorer.run()
