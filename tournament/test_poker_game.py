from pktools.deuces import Deck, Evaluator, Card
import numpy as np
import pandas as pd
import importlib
import os
from tournament.timeout import timeout
from poker_game import Player

list_models_name = os.listdir(os.path.dirname(os.path.abspath(__file__)) +'\\..\\models' )
model_name = list_models_name[0]
model = importlib.import_module('models.'+model_name+'.'+model_name).make_decision

# =============================================================================
# Class Player
# =============================================================================
pl = Player(model, ID = 1, stack = 1000)

class TestPlayer():
    
    def test_get_player_data(self):
        assert isinstance(pl.ID, int), "ID is not an integer"
        assert callable(model), "model is not a function object"
        assert isinstance(pl.stack, int), "stack is not an integer"
        assert pl.stack > 0, "stack is negative"   

    def test_bet2pot(self, amount):
        pass

#    def test_make_decision(self, input, current_raise, minimum_raise, time_delay):
#        pass
#
#    def test_new_round(self, hand, blind=10):
#        pass