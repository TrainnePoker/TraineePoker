
import numpy as np

def make_decision(input):

    rand_nb = np.random.rand()
    if rand_nb < 0.7:
        return 'call'
    elif rand_nb > 0.8:
        return input['current raise'] - input['player info']['bet'] + input['minimum raise']
    else:
        return 'fold'
