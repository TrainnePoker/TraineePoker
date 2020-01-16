# TraineePoker


## Principle of the project:

 every now and then, a simulation of a poker game is run. It is done by triggering
  the run_tournament.py

 This simulation will collect all the models found in the models directory and make them play against each-other

 It will append the result to a yaml file, collecting the history of all the tournaments



## Structure of a model:

To be picked up by the tournament simulation, a model needs to have the following element:

- it has a directory with the name: *model_name*
- this directory must contain a file: *model_name.py*
- this file must contain a function: make_decision(input)
- this function must take 1 input argument
- this function must return either:
    - "fold"
    - "call"
    - "all in"
    - "*int*"
    - *int*

the simulation will call the 'make_decision' function, give it the input object and
process the return of the function. It will makes sure the return is a legal decision (c.f poker rules paragraph).

**WARNING**: for robustness, the model has only 5 seconds to make a decision, after that, the simulation stops the function and gives a default "fold" decision to the player.


## Rules of the poker simulation
(TODO)

## Structure of the input:

 If you want to explore the structure of the input object type in your console the string written at the end of this document.
 This will instantiate an input object.


 The simulation will provide an input dictionary to the model with the following structure as an example:

    'blind': 10,                                    # (rule) value of big blind
    'timeout': 5,                                   # (rule) how much time the model has to make decision
    'community': ['2♣', 'K❤', '5♦', '8♠', '8❤'],  # list of community cards
    'current raise': 90,                            # value of the current highest bet
    'hand': ['K♠', 'J❤'],                          # cards of the player
    'initial stack': 1000,                          # (rule) how much money everybody had at the beginning
    'minimum raise': 10,                            # (rule) value of the minimum raise
    'n_players': 3,                                 # number of players
    'pot': 230,                                    # total money bet at this round

                                                # dictionnary containing some of the player's data
    'player info': {'ID': 0,                       # ID number
                 'bet': 80,                     # how much he has bet at this round so far
                 'last_action': 20,             # the latest action he took
                 'stack': 900,                  # how much money left in the stack
                 'status': 'in'},               # his current game status

                                                # 'others info' contains a list of dictionnary similar to 'player info' but for all the other players
    'others info': [{'ID': 0,
                  'bet': 80,
                  'last_action': 20,
                  'stack': 900,
                  'status': 'in'},
                 {'ID': 1,
                  'bet': 60,
                  'last_action': 'fold',
                  'stack': 920,
                  'status': 'out'},
                 {'ID': 2,
                  'bet': 90,
                  'last_action': 20,
                  'stack': 950,
                  'status': 'in'}],

    'round history': [
                   [{'ID': 2,                   # 'round history' is a list of list of 'action' dictionnary: [betting_round_nb][action_nb][action_key]
                     'bet': 10,                 # where each action dict contains a decision made by a player and data about the player of made the decision
                     'last_action': 'call',
                     'stack': 1030,
                     'status': 'in'},
                    {'ID': 0,
                     'bet': 10,
                     'last_action': 'call',
                     'stack': 970,
                     'status': 'in'},
                    {'ID': 1,
                     'bet': 20,
                     'last_action': 10,
                     'stack': 960,
                     'status': 'in'}],

                   [{'ID': 2,
                     'bet': 40,
                     'last_action': 'call',
                     'stack': 1000,
                     'status': 'in'},
                    {'ID': 0,
                     'bet': 50,
                     'last_action': 10,
                     'stack': 930,
                     'status': 'in'},
                    {'ID': 1,
                     'bet': 50,
                     'last_action': 'call',
                     'stack': 930,
                     'status': 'in'}],

                   [{'ID': 2,
                     'bet': 70,
                     'last_action': 10,
                     'stack': 970,
                     'status': 'in'},
                    {'ID': 0,
                     'bet': 80,
                     'last_action': 20,
                     'stack': 900,
                     'status': 'in'},
                    {'ID': 1,
                     'bet': 60,
                     'last_action': 'fold',
                     'stack': 920,
                     'status': 'out'}]],

    'game history': [{                                                       # 'game history' is a list of dict providing the data about previous rounds [round_nb][round_key]
                   'round_number': 0,                                    # each dict has some meta data about the given round (players infos and cards, winner(s) of the round, etc.)
                   'winner': [0]                                         # and the dicts contain the round history for all the rounds (same format as previous entry)
                   'community': ['Q♠', 'T♣', '3♦', '9♦', 'A❤'],         # NOTE: the players_info is taken at the end of the round, after the pot has been distributed
                   'players_in': [0, 1, 2],
                   'players_info': [{'ID': 0,
                                     'bet': 0,
                                     'hand': ['K♠', 'A♦'],
                                     'last_action': 10,
                                     'stack': 1030,
                                     'status': 'in'},
                                    {'ID': 1,
                                     'bet': 0,
                                     'hand': ['6❤', '8♣'],
                                     'last_action': 'fold',
                                     'stack': 990,
                                     'status': 'out'},
                                    {'ID': 2,
                                     'bet': 0,
                                     'hand': ['2♠', 'A♠'],
                                     'last_action': 'call',
                                     'stack': 980,
                                     'status': 'in'}],

                   'round_history': [[{'ID': 1,
                                       'bet': 10,
                                       'last_action': 'call',
                                       'stack': 990,
                                       'status': 'in'},
                                      {'ID': 2,
                                       'bet': 10,
                                       'last_action': 'call',
                                       'stack': 990,
                                       'status': 'in'},
                                      {'ID': 0,
                                       'bet': 10,
                                       'last_action': 'call',
                                       'stack': 990,
                                       'status': 'in'}],

                                     [{'ID': 1,
                                       'bet': 10,
                                       'last_action': 'call',
                                       'stack': 990,
                                       'status': 'in'},
                                      {'ID': 2,
                                       'bet': 10,
                                       'last_action': 'call',
                                       'stack': 990,
                                       'status': 'in'},
                                      {'ID': 0,
                                       'bet': 10,
                                       'last_action': 'call',
                                       'stack': 990,
                                       'status': 'in'}],

                                     [{'ID': 1,
                                       'bet': 10,
                                       'last_action': 'fold',
                                       'stack': 990,
                                       'status': 'out'},
                                      {'ID': 2,
                                       'bet': 10,
                                       'last_action': 'call',
                                       'stack': 990,
                                       'status': 'in'},
                                      {'ID': 0,
                                       'bet': 10,
                                       'last_action': 'call',
                                       'stack': 990,
                                       'status': 'in'}],

                                     [{'ID': 2,
                                       'bet': 10,
                                       'last_action': 'call',
                                       'stack': 990,
                                       'status': 'in'},
                                      {'ID': 0,
                                       'bet': 20,
                                       'last_action': 10,
                                       'stack': 980,
                                       'status': 'in'},
                                      {'ID': 2,
                                       'bet': 20,
                                       'last_action': 'call',
                                       'stack': 980,
                                       'status': 'in'}]],

                    *other entries for other rounds*]


Type this in your console to get en example of the layout of the input object:

input = {'n_players': 3, 'blind': 10, 'minimum raise': 10, 'timeout': 5, 'initial stack': 1000, 'current raise': 20, 'pot': 50, 'community': [], 'hand': ['4♦', 'T♠'], 'player info': {'ID': 0, 'last_action': 10, 'stack': 1020, 'bet': 10, 'status': 'in'}, 'others info': [{'ID': 0, 'last_action': 10, 'stack': 1030, 'bet': 0, 'status': 'in'}, {'ID': 1, 'last_action': 10, 'stack': 1000, 'bet': 20, 'status': 'in'}, {'ID': 2, 'last_action': 'call', 'stack': 930, 'bet': 20, 'status': 'in'}], 'round history': [[{'ID': 1, 'last_action': 10, 'stack': 1000, 'bet': 20, 'status': 'in'}, {'ID': 2, 'last_action': 'call', 'stack': 930, 'bet': 20, 'status': 'in'}]], 'game history': [{'round_number': 0, 'players_in': [0, 1, 2], 'community': ['Q♠', 'T♣', '3♦', '9♦', 'A❤'], 'players_info': [{'ID': 0, 'last_action': 10, 'stack': 1030, 'bet': 0, 'status': 'in', 'hand': ['K♠', 'A♦']}, {'ID': 1, 'last_action': 'fold', 'stack': 990, 'bet': 0, 'status': 'out', 'hand': ['6❤', '8♣']}, {'ID': 2, 'last_action': 'call', 'stack': 980, 'bet': 0, 'status': 'in', 'hand': ['2♠', 'A♠']}], 'round_history': [[{'ID': 1, 'last_action': 'call', 'stack': 990, 'bet': 10, 'status': 'in'}, {'ID': 2, 'last_action': 'call', 'stack': 990, 'bet': 10, 'status': 'in'}, {'ID': 0, 'last_action': 'call', 'stack': 990, 'bet': 10, 'status': 'in'}], [{'ID': 1, 'last_action': 'call', 'stack': 990, 'bet': 10, 'status': 'in'}, {'ID': 2, 'last_action': 'call', 'stack': 990, 'bet': 10, 'status': 'in'}, {'ID': 0, 'last_action': 'call', 'stack': 990, 'bet': 10, 'status': 'in'}], [{'ID': 1, 'last_action': 'fold', 'stack': 990, 'bet': 10, 'status': 'out'}, {'ID': 2, 'last_action': 'call', 'stack': 990, 'bet': 10, 'status': 'in'}, {'ID': 0, 'last_action': 'call', 'stack': 990, 'bet': 10, 'status': 'in'}], [{'ID': 2, 'last_action': 'call', 'stack': 990, 'bet': 10, 'status': 'in'}, {'ID': 0, 'last_action': 10, 'stack': 980, 'bet': 20, 'status': 'in'}, {'ID': 2, 'last_action': 'call', 'stack': 980, 'bet': 20, 'status': 'in'}]], 'winner': [0]}, {'round_number': 1, 'players_in': [0, 1, 2], 'community': ['6♣', 'J♦', '6♦', 'T♣', '4♣'], 'players_info': [{'ID': 0, 'last_action': 'fold', 'stack': 1010, 'bet': 0, 'status': 'out', 'hand': ['7♦', '8♣']}, {'ID': 1, 'last_action': 10, 'stack': 1030, 'bet': 0, 'status': 'in', 'hand': ['5♠', '8♦']}, {'ID': 2, 'last_action': 'fold', 'stack': 960, 'bet': 0, 'status': 'out', 'hand': ['3❤', 'A♣']}], 'round_history': [[{'ID': 2, 'last_action': 'call', 'stack': 970, 'bet': 10, 'status': 'in'}, {'ID': 0, 'last_action': 'call', 'stack': 1020, 'bet': 10, 'status': 'in'}, {'ID': 1, 'last_action': 10, 'stack': 970, 'bet': 20, 'status': 'in'}, {'ID': 2, 'last_action': 'call', 'stack': 960, 'bet': 20, 'status': 'in'}, {'ID': 0, 'last_action': 'call', 'stack': 1010, 'bet': 20, 'status': 'in'}], [{'ID': 2, 'last_action': 'fold', 'stack': 960, 'bet': 20, 'status': 'out'}, {'ID': 0, 'last_action': 'fold', 'stack': 1010, 'bet': 20, 'status': 'out'}], [], []], 'winner': [1]}]}

## structure of the output file