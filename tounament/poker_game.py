from  pktools.deuces import Deck, Evaluator, Card
import numpy as np
import pandas as pd

#TO DELETE
def algo_0(minimum_raise):
    rand_nb = np.random.rand()
    if rand_nb < 0.7:
        return 'call'
    elif rand_nb > 0.8:
        return minimum_raise
    else:
        return 'fold'

class Player:
    def __init__(self, model, ID, stack = 1000 ):
        self.model = model
        self.ID = ID
        self.stack = stack
        self.hand = []
        self.bet = 0
        self.game_status = 'in'
        self.round_status = 'in'

    def __bet(self, amount):

        if self.round_status != 'in':
            raise(PermissionError('Out or all in player cannot bet'))

        if amount >= self.stack:
            amount = self.stack
            self.round_status = 'all in'

        self.bet += amount
        self.stack -= amount

    def bet2pot(self, amount):
        if amount > self.bet :
            amount = self.bet
        self.bet -= amount
        return amount

    def make_decision(self, input, call_value, minimum_raise):
        """
        Here we call the decision algorithm, implement its decision or make
        sure it provides a legal decision
        :param input: input to provide to the decision algorithm (std to be defined)
        :param call_value: what is the current highest bet
        :param minimum_raise: what is the minimum amount for a raise
        :return:
        """
        decision = self.model(minimum_raise + call_value - self.bet)

        # The output of the algorithm must be 'fold', 'call' or an int (or string of an int)
        # corresponding to a valib sum to bet (call value, all in, or raise above the minimum raise)

        if decision == 'fold':
            self.round_status = 'out'
            print('player %d folds' % self.ID)
        elif decision == 'call':
            self.__bet(call_value - self.bet)
            print('player %d calls' % self.ID)
        else:
            try:
                # checking if the decision is a value to bet
                to_bet = int(decision)
                # check if the value correspond to calling
                if to_bet == (call_value - self.bet):
                    self.__bet(to_bet)
                    print('player %d calls' % self.ID)
                # check if the value correspond to all in
                elif to_bet >= self.stack:
                    self.__bet(to_bet)
                    print('player %d goes all in' % self.ID)
                # check if the value corresponds to a legal raise
                elif (to_bet + self.bet) >= (call_value + minimum_raise):
                    self.__bet(to_bet)
                    print('player %d raises' % self.ID)
                else:
                    # here the value corresponds to no legal bet
                    raise ValueError("""amount being bet is not permitted.
                                        Must be the call value(%d), all in(>%d), or 
                                        a raise greater than %d.
                                        Instead got %s"""
                                     % ((call_value - self.bet), self.stack,
                                        (call_value + minimum_raise - self.bet),str(to_bet)))
            except ValueError:
                # here the output is neither 'fold', 'call', or a betting int
                raise ValueError('output of decision algorithm must be fold, call or an int raise value'
                                 'instead got ' + str(decision))

        return

    def new_round(self, hand, blind=10):

        self.round_status = 'in'
        self.bet = 0
        # blind
        self.__bet(blind)
        self.hand = hand


class Game:

    def __init__(self, log_file):

        self.initial_stack = 1000
        self.blind = 10
        self.minimum_raise = 10

        self.deck = Deck()
        self.log_file = log_file

        self.players = [Player(model=model, ID=ID, stack=self.initial_stack)
                        for ID, model in enumerate(self.__get_models())]

        self.community_cards = []

        self.n_players = len(self.players)
        self.round_nb = 0
        self.turn_nb = 0
        self.dealer = 0


    def play_game(self, n_rounds=100):

        while self.round_nb < n_rounds:

            active_players = sum([player.game_status == 'in' for player in self.players])
            if active_players < 2:
                break

            self.__next_round()
            self.round_nb += 1

        return

    def __get_game_nb(self):
        return

    @staticmethod
    def __get_models():
        return [algo_0 for _ in range(6)]

    def __update_community(self):
        # card increment based on which round we are in
        if self.turn_nb == 0:
            pass
        elif self.turn_nb == 1:
            self.community_cards += self.deck.draw(3)
        elif self.turn_nb == 2:
            self.community_cards += [self.deck.draw(1)]
        elif self.turn_nb == 3:
            self.community_cards += [self.deck.draw(1)]
        elif self.turn_nb > 3:
            return

    def __rank_players(self):

        # we first compute the strength of each player's hand
        # warning: the evaluator gives value 0 to the best possible hand
        evaluator = Evaluator()
        hand_strength = np.array([evaluator.evaluate(player.hand, self.community_cards)
                                  if player.round_status != 'out' else np.inf
                                  for player in self.players])

        # we then rank them, making sure equal players have equal ranks
        player_ranking = np.zeros(self.n_players)
        for rank, hand_value in enumerate(np.unique(np.sort(hand_strength))):
            player_ranking[hand_strength == hand_value] = rank

        return player_ranking

    def __create_pots(self):
        """
        We spread the bets into pots, so that player all in who couldn't match the raise
        are eligible only to the smaller pots.

        :return:
        """
        # we make sure there is a 0 bet
        bets = np.unique(np.sort([player.bet for player in self.players] + [0]))
        pots = pd.DataFrame({'amount': [], 'eligible': [], 'content': []})

        for i in range(1, len(bets)):

            amount = bets[i]-bets[i-1]
            pot_content = 0
            eligible = []

            for ID, player in enumerate(self.players):

                if player.round_status != 'out' and player.bet >= amount:
                    eligible += [ID]
                pot_content += player.bet2pot(amount)
            pots = pots.append({'amount': amount, 'eligible':np.array(eligible), 'content':pot_content},
                               ignore_index=True)
        return pots

    def __distribute_pots(self, pots, ranking):

        for _, pot in pots.iterrows():
            eligible_ranks = ranking[pot.eligible]
            best_rank = min(eligible_ranks)
            winners = pot.eligible[ eligible_ranks == best_rank ]
            for winner in winners:
                self.players[winner].stack += int(pot.content / len(winners))

    def __next_round(self):

        self.dealer += 1
        self.turn_nb = 0
        self.dealer %= self.n_players

        # distributing cards to players still in
        self.deck = Deck()
        self.community_cards = []

        print('Starting round %d with players %s'
              % (self.round_nb, str([player.ID for player in self.players
                                     if player.game_status == 'in'])))

        for player in self.players:
            if player.game_status == 'in':
                player.new_round(hand=self.deck.draw(2), blind=self.blind)

        # running the 4 betting turns
        for _ in range(4):
            self.__next_turn()

        self.display()

        # attributing the gains
        pots = self.__create_pots()
        ranking = self.__rank_players()
        self.__distribute_pots(pots, ranking)

        for player in self.players:
            if player.stack <= 0 and player.game_status != 'out':
                player.game_status = 'out'
                player.round_status = 'out'


        self.display()

    def __next_turn(self):
        self.__update_community()

        print('\n turn %d' % self.turn_nb)
        Card.print_pretty_cards(self.community_cards)
        print('\n actions:')

        # Betting round

        highest_bet = max([player.bet for player in self.players]) # current raise value
        player = self.dealer # player starting to bet
        last_update = 0 # when was the last raise

        # n_active_players is initialized by counting all the 'in' players
        # but update in the loop only for the out players.
        # This is because player all in before the turn can be seen as inactive,
        # be must be considered active if they go all in during the turn
        n_active_players = sum([player.round_status == 'in' for player in self.players])
        while last_update < self.n_players and n_active_players >= 2:
            # insure a circular iteration of all players
            player %= self.n_players
            # checks if player is still playing (excluding all in)
            if self.players[player].round_status == 'in':

                self.players[player].make_decision(input=None,
                                                   call_value=highest_bet,
                                                   minimum_raise=self.minimum_raise)
                if self.players[player].round_status == 'out':
                    n_active_players -= 1
                # check if a raise has happened
                if self.players[player].bet > highest_bet:
                    highest_bet = self.players[player].bet
                    last_update = 0

            last_update += 1
            player += 1

        # End of betting round
        self.turn_nb += 1

    def display(self):
        for player in self.players:

            print("player %d: \t Stack: %d \t Bets: %d \t Status: %s "
                  %(player.ID, player.stack ,player.bet, player.round_status))
            Card.print_pretty_cards(player.hand)

        print("community:")
        Card.print_pretty_cards(self.community_cards)

game = Game('')
game.play_game(1)


# TODO: """
#  logging for the output,
#  creating a standard for the input (based on output)
#  creating a standard for the model search
#  creating testing
#  """
