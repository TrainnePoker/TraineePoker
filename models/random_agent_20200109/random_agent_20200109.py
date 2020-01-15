import numpy as np

def make_decision(input):

    rand_nb = np.random.rand()
    if rand_nb < 0.65:
        return 'call'
    elif rand_nb > 0.85:
        return input['current raise'] - input['player info'][3] + input['minimum raise']
    else:
        return 'fold'

