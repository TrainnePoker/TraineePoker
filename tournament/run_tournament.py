import os
import sys, inspect
from os.path import join
from tournament.poker_game import Game
import importlib



current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

config_file_path = join(current_dir,'config.yaml')
log_file_path = join(current_dir,'history.yaml')

list_models_name = os.listdir(join(join(os.path.dirname(os.path.abspath(__file__)),".."),"models" ))

if len(list_models_name) % 6 == 1:
    list_models_name += [list_models_name[0]]

for i in range(0,len(list_models_name),6):

    models = [importlib.import_module('models.'+model_name+'.'+model_name).make_decision
              for model_name in list_models_name[i:i+6]]

    game = Game(log_file=log_file_path,config_file=config_file_path,models=models)
    game.play_game(100)
