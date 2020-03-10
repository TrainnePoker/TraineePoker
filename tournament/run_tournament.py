import os
import sys, inspect
from os.path import join
from tournament.poker_game import Game
import importlib
from numpy import ceil
import numpy as np
from random import seed

SEED = np.random.randint(1e5)
print(f"seed: {SEED}")
np.random.seed(SEED)
seed(SEED)


def split_list(liste, n=6):
    n_groups = int(ceil(len(liste) / n))
    container = [[] for _ in range(n_groups)]

    for i in range(len(liste)):
        container[i%n_groups] += [liste[i]]
    return container


# getting the paths of the project's directories
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

config_file_path = join(current_dir, 'config.yaml')
log_file_path = join(current_dir, 'history.yaml')

# collect a list of all available models in the *models* directory
list_models_name = os.listdir(join(join(os.path.dirname(os.path.abspath(__file__)),".."),"models" ))

list_models_name = split_list(list_models_name)

for group in list_models_name:

    models = [importlib.import_module('models.'+model_name+'.'+model_name).make_decision
              for model_name in group]

    game = Game(log_file=log_file_path,config_file=config_file_path,models=models)
    game.play_game(100)


