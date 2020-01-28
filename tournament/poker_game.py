from datetime import datetime
from pktools.deuces.evaluator import Evaluator
from pktools.deuces.card import Card
from pktools.deuces.deck import Deck
import numpy as np
import pandas as pd
from tournament.timeout import timeout
import yaml
from tournament.get_poker_rules import read_config_file, default_rules
from copy import deepcopy
"""
Game pseudo_code:

loop -> Game starts round
    loop -> Game starts turn
        loop -> Game creates input
             -> Game calls player action(input)
             -> player calls model decision(input)
             -> player updates status
    -> Game distributes round gains
"""


# debug:
# could be about betting the blind, check out what happens in term of pot eligibility when every body folds directly
# in this attempt, we see that the last player to play hasn't bet (no blind neither). Which shouldn't be possible

class Player:
    def __init__(self, model, ID, stack = 1000 ):
        self.model = model
        self.ID = ID
        self.stack = stack
        self.hand = []
        self.bet = 0
        self.game_status = 'in'
        self.round_status = 'in'
        self.last_action = ''

    def get_player_data(self, hide_hand = True):
        """returns a quick snapshot of player status, for logging and model's input"""
        info = {"ID":self.ID, "last_action":self.last_action, "stack":self.stack, "bet":int(self.bet), "status":self.round_status}
        if not hide_hand:
            info["hand"] = self.hand
        return info

    def __bet(self, amount):
        """
        applies the betting of a given amount (handles when amount > stack)
        :param amount: amount to be bet by the player
        :return:
        """
        if self.round_status != 'in':
            raise(PermissionError('Out or all in player cannot bet'))

        if amount >= self.stack:
            amount = self.stack
            self.round_status = 'all in'

        self.bet += amount
        self.stack -= amount

    def bet2pot(self, amount):
        """
        Transfers the money from the bet into the pot
        :param amount: value of the pot
        :return:
        """
        if amount > self.bet :
            amount = self.bet
        self.bet -= amount
        return amount

    def make_decision(self, input_dict, current_raise, rules):
        """
        Here we call the decision algorithm, implement its decision or make
        sure it provides a legal decision
        :param input: input to provide to the decision algorithm (std to be defined)
        :param current_raise: what is the current highest bet
        :param minimum_raise: what is the minimum amount for a raise
        :return:
        """

        try:
            decision = timeout(time_delay=rules['timeout'])(self.model)(deepcopy(input_dict))
        except Exception:
            decision = 'timeout'

        self.last_action = decision

        calling_bet = current_raise - self.bet

        # The output of the algorithm must be 'fold', 'call' or an int (or string of an int)
        # corresponding to a valib sum to bet (call value, all in, or raise above the minimum raise)

        if decision == 'fold':
            self.round_status = 'out'
            print('player %d folds' % self.ID)
        elif decision == 'timeout':
            self.round_status = 'out'
            print('player %d timed out' % self.ID)
        elif decision == 'all in':
            self.__bet(self.stack)
        elif decision == 'call':
            self.__bet(calling_bet)
            print('player %d calls' % self.ID)
        else:
            try:
                # checking if the decision is a value to bet
                to_bet = int(decision)
                # check if the value correspond to calling
                if to_bet == (calling_bet):
                    self.__bet(to_bet)
                    print('player %d calls' % self.ID)
                # check if the value correspond to all in
                elif to_bet >= self.stack:
                    self.__bet(to_bet)
                    print('player %d goes all in' % self.ID)
                # check if the value corresponds to a legal raise
                elif (to_bet + self.bet) >= (current_raise + rules['minimum raise']):
                    self.__bet(to_bet)
                    print('player %d raises' % self.ID)
                else:
                    # here the value corresponds to no legal bet
                    raise ValueError("""amount being bet is not permitted.
                                        Must be the call value(%d), all in(>%d), or 
                                        a raise greater than %d.
                                        Instead got %s"""
                                     % ((calling_bet), self.stack,
                                        (calling_bet + rules['minimum raise']),str(to_bet)))
            except ValueError:
                # here the output is neither 'fold', 'call', or a betting int
                raise ValueError('output of decision algorithm must be fold, call or an int raise value'
                                 'instead got ' + str(decision))

        return

    def new_round(self, hand, blind):

        self.hand = hand

        self.round_status = self.game_status
        self.bet = 0
        # blind
        self.__bet(blind)


class Game:

    def __init__(self, log_file, models: list, config_file = None, tournament_id: str = 'none'):

        if config_file is None:
            self.rules = default_rules()
        else:
            self.rules = read_config_file(config_file)

        self.tournament_id = tournament_id
        self.initial_stack = 1000

        self.deck = Deck()
        self.log_file = log_file

        self.players = [Player(model=model, ID=ID, stack=self.rules['initial stack'])
                        for ID, model in enumerate(models)]

        self.community_cards = []

        self.n_players = len(self.players)
        self.round_nb = 0
        self.turn_nb = 0
        self.first_player = 0

        self.players_info = [] # list of tuples [player ID][player feature]; player feature = (ID, last_action, stack, bet, round_status)
        self.round_logger = [] # list of list of tuple [turn nb][action nb][player feature]
        self.game_logger = [] # list of dict [{init_round_status, round_logger, final_round_status}]
        self.input_dict = {'player': [], 'opponents': [], 'round':[], 'game':[]}


    def play_game(self, n_rounds=100):

        while self.round_nb < n_rounds:

            active_players = sum([player.game_status == 'in' for player in self.players])
            if active_players < 2:
                break

            self.__next_round()
            self.round_nb += 1

        self.__save_game_log()

        return

    def __get_game_metadata(self):
        return {'n_players': self.n_players,
                'big blind': self.rules['big blind'],
                'small blind': self.rules['small blind'],
                'minimum raise': self.rules['minimum raise'],
                'timeout': self.rules['timeout'],
                'initial stack': self.rules['initial stack']}

    def __get_round_info(self):
        players_in = [i for i,player in enumerate(self.players) if player.game_status == 'in']
        return {'round_number': self.round_nb,
                'players_in': players_in,
                'community': self.community_cards,
                'players_info': [self.players[p].get_player_data(hide_hand=False) for p in players_in]}

    def __update_community(self):
        # card increment based on which round we are in
        if self.turn_nb == 0:
            pass
        elif self.turn_nb == 1:
            self.community_cards += Card.int_to_str(self.deck.draw(3))
        elif self.turn_nb == 2:
            self.community_cards += [Card.int_to_str(self.deck.draw(1))]
        elif self.turn_nb == 3:
            self.community_cards += [Card.int_to_str(self.deck.draw(1))]
        elif self.turn_nb > 3:
            return

    def __rank_players(self):

        # we first compute the strength of each player's hand
        # warning: the evaluator gives value 0 to the best possible hand
        evaluator = Evaluator()
        hand_strength = np.array([evaluator.evaluate( Card.str_to_int(player.hand) , Card.str_to_int(self.community_cards))
                                  if player.round_status != 'out' else np.inf
                                  for player in self.players])

        # we then rank them, making sure equal players have equal ranks
        player_ranking = np.zeros(self.n_players)
        for rank, hand_value in enumerate(np.unique(np.sort(hand_strength))):
            player_ranking[hand_strength == hand_value] = rank

        return player_ranking

    def __create_pots(self):
        """
        We use the side-pots structure (cf. the internet), to compute more easily
        how to spread the money when the winner of the round was all in and
        couldn't mach the highest raise.

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
        """"""
        for _, pot in pots.iterrows():
            eligible_ranks = ranking[pot.eligible]
            best_rank = min(eligible_ranks)
            winners = pot.eligible[ eligible_ranks == best_rank ]
            for winner in winners:
                self.players[winner].stack += int(pot.content / len(winners))


    def __next_round(self):

        # reinitializing/updating round specific parameters

        self.round_logger = []
        self.first_player += 1
        self.first_player %= self.n_players
        self.turn_nb = 0
        self.deck = Deck()
        self.community_cards = []

        # distributing cards to players still in
        print('Starting round %d with players %s'
              % (self.round_nb, str([i for i,player in enumerate(self.players)
                                     if player.game_status == 'in'])))

        nth_player = 0
        for player_id in range(self.n_players):
            player = self.players[(player_id + self.first_player) % self.n_players]

            if player.game_status == 'in':
                if nth_player == 0:
                    blind = self.rules['small blind']
                elif nth_player == 1:
                    blind = self.rules['big blind']
                else:
                    blind = 0

                player.new_round(hand=Card.int_to_str(self.deck.draw(2)), blind=blind)

                nth_player += 1

        self.players_info = [player.get_player_data() for player in self.players]

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
                player.hand = []

        # logging
        self.game_logger += [self.__get_round_info()]
        self.game_logger[-1]['round_history'] = self.round_logger

        self.game_logger[-1]["winner"] = np.where(ranking == 0)[0].tolist()
        self.display()

    def __next_turn(self):

        self.round_logger += [[]]
        self.__update_community()

        print('\n turn %d' % self.turn_nb)
        print(self.community_cards)
        print('\n actions:')

        # Betting round

        current_raise = max([player.bet for player in self.players]) # current raise value
        who_plays = self.first_player # player starting to bet
        last_update = 0 # when was the last raise

        if self.turn_nb == 0: # pre-flop round
            who_plays = np.argmax([player.bet for player in self.players]) + 1

        # n_active_players is initialized by counting all the 'in' players
        # but update in the loop only for the out players.
        # This is because player all in before the turn can be seen as inactive,
        # be must be considered active if they go all in during the turn
        n_active_players = sum([player.round_status == 'in' for player in self.players])
        while last_update < self.n_players and n_active_players >= 2:
            # insure a circular iteration of all players
            who_plays %= self.n_players
            player = self.players[who_plays]

            # checks if player is still playing (excluding all in)
            if player.round_status == 'in':

                player.make_decision(input_dict=self.__make_input(player, current_raise),
                                     current_raise=current_raise,
                                     rules=self.rules)

                # updating the data for the input dict
                player_data = player.get_player_data()
                self.round_logger[-1] += [player_data]
                self.players_info[player.ID] = player_data

                if player.round_status == 'out':
                    n_active_players -= 1
                # check if a raise has happened
                if player.bet > current_raise:
                    current_raise = player.bet
                    last_update = 0

            last_update += 1
            who_plays += 1

        # End of betting round
        self.turn_nb += 1

    def __save_game_log(self):

        models_dict = {}
        for player in self.players:
            model_name = player.model.__module__.replace('.', ' ').split()[-1]
            models_dict["player_%d" % player.ID] = model_name

        log_dict = {**self.__get_game_metadata(),
                    "tournament_ID": str(self.tournament_id),
                    "game_date": str(datetime.now()),
                    "player_models": models_dict,
                    "game_history":self.game_logger
                    }

        with open(self.log_file, 'a+', encoding='utf8') as outfile:
            yaml.dump(log_dict, outfile, default_flow_style=False, allow_unicode=True)

        return

    def __make_input(self, player, current_raise):
        return {**self.__get_game_metadata(),
                'current raise': current_raise,
                'pot': sum([player.bet for player in self.players]),
                'community': self.community_cards,
                'hand': player.hand,
                'player info':player.get_player_data(),
                'others info': self.players_info,
                'round history': self.round_logger,
                'game history': self.game_logger[:-1]}

        # [:-1] -> very important to not give last round info (contains all the hands values)

    def display(self):
        for player in self.players:

            print("player %d: \t Stack: %d \t Bets: %d \t Status: %s "
                  %(player.ID, player.stack ,player.bet, player.round_status))
            print(player.hand)

        print("community:")
        print(self.community_cards)

