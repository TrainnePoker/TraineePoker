import os
import sys, inspect
from os.path import join
from tournament.poker_game import Game
import importlib


# getting the paths of the project's directories
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

config_file_path = join(current_dir,'config.yaml')
log_file_path = join(current_dir,'history.yaml')

# collect a list of all available models in the *models* directory
list_models_name = os.listdir(join(join(os.path.dirname(os.path.abspath(__file__)),".."),"models" ))

# ensuring there won't be a game with only one player
if len(list_models_name) % 6 == 1:
    list_models_name += [list_models_name[0]]

# split the models into groups of maximum 6, and making them play against each-others
for i in range(0,len(list_models_name),6):

    models = [importlib.import_module('models.'+model_name+'.'+model_name).make_decision
              for model_name in list_models_name[i:i+6]]

    game = Game(log_file=log_file_path,config_file=config_file_path,models=models)
    game.play_game(100)
