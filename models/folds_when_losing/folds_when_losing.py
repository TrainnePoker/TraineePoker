import numpy as np
from pktools.feature_engineering.winning_prob import estimate_proba

def make_decision(input):
    
    proba = estimate_proba(input['hand'],input['community'], input['n_players'])

    if proba > 0.9:
        return 100000000

    if proba > 0.7:
        return input['current raise'] - input['player info']['bet'] + input['minimum raise']

    if (proba * 1.3) > ( (1/input['n_players'])):
        return 'call'
    else:
        return 'fold'
