class Card():
    """
    Static class that handles cards. We represent cards as 32-bit integers, so 
    there is no object instantiation - they are just ints. Most of the bits are 
    used, and have a specific meaning. See below: 

                                    Card:

                          bitrank     suit rank   prime
                    +--------+--------+--------+--------+
                    |xxxbbbbb|bbbbbbbb|cdhsrrrr|xxpppppp|
                    +--------+--------+--------+--------+

        1) p = prime number of rank (deuce=2,trey=3,four=5,...,ace=41)
        2) r = rank of card (deuce=0,trey=1,four=2,five=3,...,ace=12)
        3) cdhs = suit of card (bit turned on based on suit of card)
        4) b = bit turned on depending on rank of card
        5) x = unused

    This representation will allow us to do very important things like:
    - Make a unique prime prodcut for each hand
    - Detect flushes
    - Detect straights

    and is also quite performant.
    """

    # the basics
    STR_RANKS = '23456789TJQKA'
    INT_RANKS = range(13)
    PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41]

    # converstion from string => int
    CHAR_RANK_TO_INT_RANK = dict(zip(list(STR_RANKS), INT_RANKS))
    CHAR_SUIT_TO_INT_SUIT = {
        '♠': 1,  # spades
        '❤': 2,  # hearts
        '♦': 4,  # diamonds
        '♣': 8,  # clubs
    }
    INT_SUIT_TO_CHAR_SUIT = 'xshxdxxxc'

    # for pretty printing
    PRETTY_SUITS = {
        1: "♠",  # spades
        2: "❤", # hearts
        4: "♦",  # diamonds
        8: "♣"  # clubs
    }



    # hearts and diamonds
    PRETTY_REDS = [2, 4]

    @staticmethod
    def str_to_int(strings):
        """
        Converts Card string to binary integer representation of card, inspired by:

        http://www.suffecool.net/poker/evaluator.html
        """

        if type(strings) == str:
            strings = [strings]

        cards = []

        for string in strings:
            rank_char = string[0]
            suit_char = string[1]
            rank_int = Card.CHAR_RANK_TO_INT_RANK[rank_char]
            suit_int = Card.CHAR_SUIT_TO_INT_SUIT[suit_char]
            rank_prime = Card.PRIMES[rank_int]

            bitrank = 1 << rank_int << 16
            suit = suit_int << 12
            rank = rank_int << 8
            cards += [bitrank | suit | rank | rank_prime]

        if len(cards) == 1:
            cards = cards[0]

        return cards

    @staticmethod
    def int_to_str(card_ints):

        if type(card_ints) == int:
            card_ints = [card_ints]

        card_strings = []
        for card_int in card_ints:
            rank_int = Card.get_rank_int(card_int)
            suit_int = Card.get_suit_int(card_int)
            full_string = Card.STR_RANKS[rank_int] + Card.PRETTY_SUITS[suit_int]
            card_strings += [full_string]

        if len(card_strings) == 1:
            card_strings = card_strings[0]
        return card_strings

    @staticmethod
    def get_rank_int(card_int):
        return (card_int >> 8) & 0xF

    @staticmethod
    def get_suit_int(card_int):
        return (card_int >> 12) & 0xF

    @staticmethod
    def get_bitrank_int(card_int):
        return (card_int >> 16) & 0x1FFF

    @staticmethod
    def get_prime(card_int):
        return card_int & 0x3F

    @staticmethod
    def hand_to_binary(card_strs):
        """
        Expects a list of cards as strings and returns a list
        of integers of same length corresponding to those strings.
        """
        bhand = []
        for c in card_strs:
            bhand.append(Card.str_to_int(c))
        return bhand

    @staticmethod
    def prime_product_from_hand(card_ints):
        """
        Expects a list of cards in integer form.
        """

        product = 1
        for c in card_ints:
            product *= (c & 0xFF)

        return product

    @staticmethod
    def prime_product_from_rankbits(rankbits):
        """
        Returns the prime product using the bitrank (b)
        bits of the hand. Each 1 in the sequence is converted
        to the correct prime and multiplied in.

        Params:
            rankbits = a single 32-bit (only 13-bits set) integer representing
                    the ranks of 5 _different_ ranked cards
                    (5 of 13 bits are set)

        Primarily used for evaulating flushes and straights,
        two occasions where we know the ranks are *ALL* different.

        Assumes that the input is in form (set bits):

                              rankbits
                        +--------+--------+
                        |xxxbbbbb|bbbbbbbb|
                        +--------+--------+

        """
        product = 1
        for i in Card.INT_RANKS:
            # if the ith bit is set
            if rankbits & (1 << i):
                product *= Card.PRIMES[i]

        return product

    @staticmethod
    def int_to_binary(card_int):
        """
        For debugging purposes. Displays the binary number as a
        human readable string in groups of four digits.
        """
        bstr = bin(card_int)[2:][::-1]  # chop off the 0b and THEN reverse string
        output = list("".join(["0000" + "\t"] * 7) + "0000")

        for i in range(len(bstr)):
            output[i + int(i / 4)] = bstr[i]

        # output the string to console
        output.reverse()
        return "".join(output)

    @staticmethod
    def int_to_pretty_str(card_int):
        """
        Prints a single card
        """

        color = False
        try:
            from termcolor import colored
            ### for mac, linux: http://pypi.python.org/pypi/termcolor
            ### can use for windows: http://pypi.python.org/pypi/colorama
            color = True
        except ImportError:
            pass

        # suit and rank
        suit_int = Card.get_suit_int(card_int)
        rank_int = Card.get_rank_int(card_int)

        # if we need to color red
        s = Card.PRETTY_SUITS[suit_int]
        if color and suit_int in Card.PRETTY_REDS:
            s = colored(s, "red")

        r = Card.STR_RANKS[rank_int]

        return " [ " + r + " " + s + " ] "

    @staticmethod
    def print_pretty_card(card_int):
        """
        Expects a single integer as input
        """
        print(Card.int_to_pretty_str(card_int))

    @staticmethod
    def print_pretty_cards(card_ints):
        """
        Expects a list of cards in integer form.
        """
        output = " "
        for i in range(len(card_ints)):
            c = card_ints[i]
            if i != len(card_ints) - 1:
                output += Card.int_to_pretty_str(c) + ","
            else:
                output += Card.int_to_pretty_str(c) + " "

        print(output)
