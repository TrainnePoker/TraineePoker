import numpy as np

def make_decision(input):

    rand_nb = np.random.rand()
    if rand_nb < 0.1:
        return 'call'
    elif rand_nb > 0.9:
        return input['current raise'] - input['player info'][3] + input['minimum raise']
    else:
        return 'fold'