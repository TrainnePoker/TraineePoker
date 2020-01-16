
from copy import deepcopy
from pktools.deuces import Evaluator, Deck, Card
from numpy import mean
from random import shuffle

def set_deck(hand, board):
    deck = Deck()
    deck.cards = list( set(deck.cards)-set(hand)-set(board) )
    return deck

def estimate_proba(hand, board, n_player, n_simul=1000):
    evaluator = Evaluator()
    to_draw = 5-len(board)
    deck = set_deck(hand, board)

    winnings = []

    for _ in range(n_simul):
        deck2 = deepcopy(deck)
        shuffle(deck2.cards)
        if to_draw == 1:
            board2 = board + [deck2.draw(to_draw)]
        else:
            board2 = board + deck2.draw(to_draw)
        if n_player > 2:
            other_hands = list(zip(deck2.draw(n_player-1), deck2.draw(n_player-1)))
            score_others = min([evaluator.evaluate(list(hand2), board2) for hand2 in other_hands])
        elif n_player == 2:
            other_hand = deck2.draw(2)
            score_others = evaluator.evaluate(other_hand,board2)

        score_player = evaluator.evaluate(hand, board2)

        winnings += [score_player < score_others]

    return mean(winnings)

