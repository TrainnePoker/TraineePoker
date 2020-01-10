from tournament.poker_game import Game
import importlib
import os

list_models_name = os.listdir(os.path.dirname(os.path.abspath(__file__)) +'\\..\\models' )

if len(list_models_name) % 6 == 1:
    list_models_name += [list_models_name[0]]

for i in range(0,len(list_models_name),6):

    models = [importlib.import_module('models.'+model_name+'.'+model_name).make_decision
              for model_name in list_models_name[i:i+6]]

    game = Game('',models)
    game.play_game(100)
