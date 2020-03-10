from datetime import datetime

from tabulate import tabulate

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
    def __init__(self, model, ID, stack=1000):
        self.model = model
        self.ID = ID
        self.stack = stack
        self.hand = []
        self.bet = 0
        self.game_status = 'in'
        self.round_status = 'in'
        self.last_action = ''

    def get_player_data(self, hide_hand=True):
        """returns a quick snapshot of player status, for logging and model's input"""
        info = {"ID": self.ID, "last_action": self.last_action, "stack": self.stack,
                "bet": int(self.bet), "status": self.round_status}
        if not hide_hand:
            info["hand"] = self.hand
        return info

    def _bet(self, amount):
        """
        applies the betting of a given amount (handles when amount > stack)
        :param amount: amount to be bet by the player
        :return:
        """
        if self.round_status != 'in':
            raise (PermissionError('Out or all in player cannot bet'))

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

        if amount > self.bet:
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
            self._bet(self.stack)
        elif decision == 'call':
            self._bet(calling_bet)
            print('player %d calls' % self.ID)
        else:
            try:
                # checking if the decision is a value to bet
                to_bet = int(decision)
                # check if the value correspond to calling
                if to_bet == (calling_bet):
                    self._bet(to_bet)
                    print('player %d calls' % self.ID)
                # check if the value correspond to all in
                elif to_bet >= self.stack:
                    self._bet(to_bet)
                    print('player %d goes all in' % self.ID)
                # check if the value corresponds to a legal raise
                elif (to_bet + self.bet) >= (current_raise + rules['minimum raise']):
                    self._bet(to_bet)
                    print(f"player {self.ID} raises to {self.bet}" )
                else:
                    # here the value corresponds to no legal bet
                    raise ValueError("""amount being bet is not permitted.
                                        Must be the call value(%d), all in(>%d), or 
                                        a raise greater than %d.
                                        Instead got %s"""
                                     % ((calling_bet), self.stack,
                                        (calling_bet + rules['minimum raise']), str(to_bet)))
            except ValueError:
                # here the output is neither 'fold', 'call', or a betting int
                raise ValueError(
                    'output of decision algorithm must be fold, call or an int raise value'
                    'instead got ' + str(decision))

        return

    def reset_status(self):
        if self.stack <= 0:
            self.game_status = 'out'
        self.hand = []
        self.round_status = self.game_status
        self.bet = 0


class Game:

    def __init__(self, log_file, models: list, config_file=None, tournament_id: str = 'none'):

        if config_file is None:
            self.rules = default_rules()
        else:
            self.rules = read_config_file(config_file)

        self.tournament_id = tournament_id

        self.deck = Deck()
        self.log_file = log_file

        self.players = [Player(model=model, ID=ID, stack=self.rules['initial stack'])
                        for ID, model in enumerate(models)]

        self.n_players = len(self.players)
        self.community_cards = []

        self.round_nb = 0
        self.turn_nb = 0
        self.first_player = 0

        self.players_info = []  # list of tuples [player ID][player feature]; player feature = (ID, last_action, stack, bet, round_status)
        self.round_logger = []  # list of list of tuple [turn nb][action nb][player feature]
        self.game_logger = []  # list of dict [{init_round_status, round_logger, final_round_status}]

    def play_game(self, n_rounds=100):

        while self.round_nb < n_rounds and self.__n_active_players() > 1:

            self.__next_round()
            self.round_nb += 1

        self.__save_game_log()

        return

    def __next_round(self):

        players_in = [i for i, player in enumerate(self.players) if player.game_status == 'in']

        self.__reset_round_data()
        self.__distribute_cards()

        print(f'Starting round {self.round_nb} with players {players_in}')
        self.players_info = [player.get_player_data() for player in self.players]

        # running the 1st betting round with the blinds
        first_player = self.__make_blinds()
        self.__next_turn(first_player)
        # running the next 3 rounds
        for _ in range(3):
            self.__next_turn()

        self.display()

        # attributing the gains
        pots = self.__create_pots()
        ranking = self.__rank_players()
        self.__distribute_pots(pots, ranking)
        winners = np.where(ranking == 0)[0].tolist()
        print(f"players {winners} win !!!", "\n" + "#" * 50 + "\n")

        # log game data
        self.game_logger += [self.__get_round_info(players_in)]
        self.game_logger[-1]['round_history'] = self.round_logger
        self.game_logger[-1]["winner"] = winners

        for player in self.players:
            player.reset_status()

    def __next_turn(self, first_player: int = None):

        self.round_logger += [[]]
        self.__update_community()

        print('\n turn %d' % self.turn_nb)
        print(self.community_cards)
        print('\n actions:')


        # Betting round
        current_raise = max([player.bet for player in self.players])  # current raise value

        who_plays = self.first_player if first_player is None else first_player  # player starting to bet
        who_raised = None

        while who_plays != who_raised and not self.stop_condition(current_raise):

            if who_raised is None:
                who_raised = who_plays

            # insures a circular iteration of all players
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

                # check if a raise has happened
                if player.bet > current_raise:
                    who_raised = who_plays
                    current_raise = player.bet

            who_plays = (who_plays + 1) % self.n_players

        # End of betting round
        self.turn_nb += 1

    def __get_game_metadata(self):
        return {**self.rules,
                'n_players': self.n_players}

    def __get_round_info(self, players_in):
        return {'round_number': self.round_nb,
                'players_in': players_in,
                'community': self.community_cards,
                'players_info': [self.players[p].get_player_data(hide_hand=False) for p in
                                 players_in]}

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
        hand_strength = np.array(
            [evaluator.evaluate(Card.str_to_int(player.hand), Card.str_to_int(self.community_cards))
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

            amount = bets[i] - bets[i - 1]
            pot_content = 0
            eligible = []

            for ID, player in enumerate(self.players):
                if player.round_status != 'out' and player.bet >= amount:
                    eligible += [ID]
                pot_content += player.bet2pot(amount)

            pots = pots.append(
                {'amount': amount, 'eligible': np.array(eligible), 'content': pot_content},
                ignore_index=True
            )

        return pots

    def __distribute_pots(self, pots, ranking):

        for _, pot in pots.iterrows():
            eligible_ranks = ranking[pot.eligible]
            best_rank = min(eligible_ranks)
            winners = pot.eligible[eligible_ranks == best_rank]
            for winner in winners:
                self.players[winner].stack += int(pot.content / len(winners))

    def __reset_round_data(self):
        self.round_logger = []
        self.first_player = (self.first_player + 1) % self.n_players
        self.turn_nb = 0

        self.deck = Deck()
        self.community_cards = []

    def __n_active_players(self):
        return sum([player.game_status == 'in' for player in self.players])

    def __distribute_cards(self):
        for player in self.players:
            if player.game_status == 'in':
                player.hand = Card.int_to_str(self.deck.draw(2))

    def __make_blinds(self):

        small_blind_paid = False
        big_blind_paid = False

        for player in np.roll(self.players, -self.first_player):

            if player.game_status == 'in':
                if not small_blind_paid:
                    player._bet(self.rules['small blind'])
                    small_blind_paid = True
                elif not big_blind_paid:
                    player._bet(self.rules['big blind'])
                    first_player = (player.ID + 1) % self.n_players
                    break

        return first_player

    def stop_condition(self, current_raise):
        n_players_left = 0
        for player in self.players:
            if (player.round_status == 'in') or\
               (player.round_status == 'all in' and player.bet == current_raise):
                n_players_left += 1
        if n_players_left > 1:
            return False
        else:
            return True

    def __save_game_log(self):

        models_dict = {}
        for player in self.players:
            model_name = player.model.__module__.replace('.', ' ').split()[-1]
            models_dict["player_%d" % player.ID] = model_name

        log_dict = {**self.__get_game_metadata(),
                    "tournament_ID": str(self.tournament_id),
                    "game_date": str(datetime.now()),
                    "player_models": models_dict,
                    "game_history": self.game_logger
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
                'player info': player.get_player_data(),
                'others info': self.players_info,
                'round history': self.round_logger,
                'game history': self.game_logger[:-1]}

        # [:-1] -> very important to not give last round info (contains all the hands values)

    def display(self):

        id_, stack, bet, status, hand = [], [], [], [], []
        for player in self.players:
            if player.game_status == 'in':
                id_ += [player.ID]
                stack += [player.stack]
                bet += [player.bet]
                status += [player.round_status]
                hand += ["[" + str(player.hand[0]) + " " + str(player.hand[1]) + "]"]

        df = pd.DataFrame({'player_id': id_, 'stack': stack, 'bet': bet, 'status': status, 'hand': hand})
        community_string = "community cards: ["
        for c in self.community_cards: community_string += c + " "

        print("\nfinal status:")
        print(tabulate(df, headers='keys', tablefmt='psql', showindex="never"))
        print(community_string+"]")

        # TODO: delete!!!!
        max_raise = max([player.bet for player in self.players])
        for player in self.players:
            if player.round_status == 'in' and player.bet != max_raise:
                raise ValueError("not everybody raised correctly")


