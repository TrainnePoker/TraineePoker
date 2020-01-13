import os
import sys, inspect

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from tournament.poker_game import Game
import importlib

# TODO: remove the *3 used here to duplicate models
list_models_name = os.listdir(os.path.dirname(os.path.abspath(__file__)) +'\\..\\models' ) * 3

if len(list_models_name) % 6 == 1:
    list_models_name += [list_models_name[0]]

for i in range(0,len(list_models_name),6):

    models = [importlib.import_module('models.'+model_name+'.'+model_name).make_decision
              for model_name in list_models_name[i:i+6]]

    game = Game('',models)
    game.play_game(100)
