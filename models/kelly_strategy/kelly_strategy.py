
import numpy as np
from pktools.feature_engineering.winning_prob import estimate_proba

"""

This model is implementing a strategy based on the kelly criterion, 
which tries to maximize the log-expectancy of return on a bet.

the 'kelly-fraction' being the fraction of your money you should bet
to maximize this log-expectancy.

"""


def make_decision(input_dict):

    round_nb = len(input_dict['round history'])

    n_players = len(input_dict['others info'])

    winning_proba = estimate_proba(input_dict['hand'],input_dict['community'], input_dict['n_players'])

    scale_factor, normalized_input = normalize_input(input_dict)



    log_expectation_fold = log_expectation(win_proba=0.0, pay_off=1, bet_fraction=normalized_input['player info']['bet'])
    log_expectation_call = log_expectation(win_proba=winning_proba,
                                           pay_off=estimate_payoff(normalized_input, normalized_input['current raise']),
                                           bet_fraction=normalized_input['current raise'])

    # the AI never raises before the last betting round, for simplicity.
    # but it will call if the call value is in line with its current estimation
    # of what is an appropriate value to bet
    if round_nb < 4:
        if log_expectation_call > log_expectation_fold:
            return 'call'
        else:
            return 'fold'


    # in this portion of code, the game is always in the last betting round
    estimated_payoff = n_players - 1

    for _ in range(10):

        optimal_bet = kelly_fraction(winning_proba, estimated_payoff)

        estimated_payoff = estimate_payoff(normalized_input, optimal_bet)

    if optimal_bet > normalized_input['current raise'] + normalized_input['minimum raise']:
        return int((optimal_bet - input_dict['player info']['bet']) * scale_factor) + 1
    elif log_expectation_call > log_expectation_fold:
        return 'call'
    else:
        return 'fold'


def kelly_fraction(win_proba, pay_off):

    result = (pay_off*win_proba + win_proba - 1)/pay_off

    if result > 1:
        raise ValueError(f"impossible kelly_fraction value: {result}")
    elif result < 0:
        result = 0

    return result

def log_expectation(win_proba, pay_off, bet_fraction):
    return win_proba * np.log(1 + pay_off * bet_fraction) \
           + (1-win_proba) * np.log(1 - bet_fraction)

def normalize_input(input_dict):

    scale_factor = input_dict['player info']['bet'] + input_dict['player info']['stack']

    input_dict['player info']['bet'] /= scale_factor
    input_dict['player info']['stack'] /= scale_factor
    input_dict['current raise'] /= scale_factor
    input_dict['minimum raise'] /= scale_factor

    for player in input_dict['others info']:
        player['bet'] /= scale_factor
        player['stack'] /= scale_factor

    return scale_factor, input_dict


def estimate_payoff(normalized_input, bet):

    if bet <= 0:
        return 1

    pot = 0

    for rival in normalized_input['others info']:

        if rival['ID'] == normalized_input['player info']['ID']:
            continue
        elif rival['status'] == 'in':
            pot += min([bet, rival['bet'] + rival['stack'] ])
        else:
            pot += min([bet, rival['bet']])

    payoff = pot / bet

    return payoff
