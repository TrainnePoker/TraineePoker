import os
import sys, inspect
from os.path import join

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from tournament.poker_game import Game
import importlib

list_models_name = os.listdir(join(join(os.path.dirname(os.path.abspath(__file__)),".."),"models" ))

if len(list_models_name) % 6 == 1:
    list_models_name += [list_models_name[0]]

for i in range(0,len(list_models_name),6):

    models = [importlib.import_module('models.'+model_name+'.'+model_name).make_decision
              for model_name in list_models_name[i:i+6]]

    game = Game( join(current_dir,"test.yaml"), models)
    game.play_game(30)
print(game.game_logger)
