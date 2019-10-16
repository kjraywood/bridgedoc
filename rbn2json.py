#!/bin/env python3
"""RBN to JSON"""

# a list-like sequence that includes methods popleft and rotate
from collections import deque

DOT = '.'
COLON = ':'

class RBNlist( list ):
    def has_item( self, item ):
        try:
            _ = self.index( item )
            return True
        except ValueError:
            return False

NOTE_CONV = '*'
NOTE_FLAG = '^'

DIRECTIONS = RBNlist( 'WNES' )
VULNERABILITIES = RBNlist( 'ZNEB?' )
NONBID_CALLS = RBNlist( 'PXRAY' )
STRAINS = RBNlist( 'NSHDC' )
LEVELS = RBNlist( map( str, range(1,8) ) )
NOTATIONS = RBNlist( (NOTE_CONV, NOTE_FLAG) )
NOTE_NUMBERS = RBNlist( map( str, range(1,10) ) )

class RBNobject( object ):
    def __init__( self ):
        self.valid = False

    def __bool__( self ):
        return self.__dict__.get( 'valid', False )
    
class Suit( RBNlist ):
    """Input = string containing cards in a single suit"""
    def __str__( self ):
        return self.string()

    def string( self, sep = '' ):
        return sep.join( self )

class OneHand( RBNobject ):
    """Input = string of a single hand with leading : or ;"""
    def __init__( self, rbn_hand):
        suits = rbn_hand[1:].split( DOT )
        if len(suits) != 4 :
            raise ValueError( 'wrong number of suits' )
        self.clubs    = Suit( suits.pop() )
        self.diamonds = Suit( suits.pop() )
        self.hearts   = Suit( suits.pop() )
        self.spades   = Suit( suits.pop() )
        self.visible = rbn_hand.startswith( COLON )
        self.valid = True

class Hands( RBNobject ):
    """Input = a deal specified by RBN tag H"""
    def __init__( self, rbn_line):

        # split the hands retaining the delimiter (: or ;)
        # at the start of each suit
        rbn_list = deque( rbn_line.replace( ':', '~:'
                                          ).replace( ';', '~;'
                                                   ).split( '~' )
                        )

        # get the starting direction
        start_dir = rbn_list.popleft()

        n = len( rbn_list )
        if n > 4:
            raise ValueError( 'too many hands' )

        # Add nulls for missing hands and populate list of hands
        rbn_list.extend( [ None for _ in range( 4 - n ) ] )
        four_hands = deque( [ OneHand( x ) for x in rbn_list ] )

        # rotate the list according to the starting direction
        four_hands.rotate( DIRECTIONS.index( start_dir ) )
        self.west = four_hands.popleft()
        self.north = four_hands.popleft()
        self.east = four_hands.popleft()
        self.south = four_hands.popleft()
        self.valid = True

class Call( RBNobject ):
    def __init__( self, rbn_char ):
        if LEVELS.has_item( rbn_char ):
            self.level = rbn_char
            self.strain = None
        elif NONBID_CALLS.has_item( rbn_char ):
            self.level = None
            self.strain = rbn_char
            self.valid = True
        else:
            raise ValueError( 'Invalid call' )
        self.is_open = True
        self.notation = None

    def add_strain( self, strain ):
        if self.strain:
            raise Exception( 'Call already has strain' )

        if not STRAINS.has_item( strain ):
            raise ValueError( 'Invalid strain' )

        self.strain = strain
        self.valid = True

    def add_notation( self, rbn_char ):
        if not self.is_open:
            raise Exception( 'Call is closed. Cannot add notation' )

        if self.notation:
            # notation must be NOTE_FLAG since is_open is true
            # but check anyway to be ready for other types
            if self.notation == NOTE_FLAG:
                if NOTE_NUMBERS.has_item( rbn_char):
                    self.note_number = rbn_char
                else:
                    raise ValueError( 'Notification requires number' )
            else:
                raise Exception( 'Impossible path' )

        elif NOTATIONS.has_item( rbn_char ):
            self.notation = rbn_char
            self.is_open = ( rbn_char == NOTE_FLAG )
        else:
            self.is_open = False
            return False

        return True

class Auction( list ):
    def __init__( self, rbn_rounds, dlr ):
        super().__init__([])
        # rbn_rounds is a list of auction strings for each round
        if not rbn_rounds:
            return

        # go through each round building a list of all calls
        calls = deque()
        num_calls_remaining = 0

        while rbn_rounds:
            # Check for missing calls from previous round
            if num_calls_remaining:
                raise ValueError( 'incomplete round' )

            # Pop the next round and do not allow blank rounds
            rnd = deque( rbn_rounds.popleft() )
            if not rnd:
                raise ValueError( 'incomplete round' )

            num_calls_remaining = 4

            while rnd:
                c = Call( rnd.popleft() )
                if c.level:
                    c.add_strain( rnd.popleft() )

                # Check for call notation
                while c.is_open and rnd:
                    if c.add_notation( rnd[0] ):
                        rnd.popleft()

                if not c:
                    raise ValueError( 'Bad call' )

                calls.append( c )
                num_calls_remaining -= 1

        # No more input.  Convert sequence of calls to rounds
        # that start with west by prepending nulls, then
        # append nulls to reach a multiple of 4
        calls.extendleft( [ None for _ in range( DIRECTIONS.index(dlr) ) ] )
        calls.extend( [ None for _ in range( 4 - ( len(calls) % 4) ) ] )

        # Split auctions into simple lists of rounds of four calls
        while calls:
            self.append( [ calls.popleft() for _ in range(4) ] )

def ParseAuctionTag(  rbn_line ):
    """Input = an auction specified by RBN tag A
       Return = tuple( dealer, vulnerability, Auction )
    """
    # split the input
    rbn_list = deque( rbn_line.split( ':' ) )

    # extract dealer+vul and check validity
    dlr, vul = list( rbn_list.popleft() )

    if not  DIRECTIONS.has_item( dlr ):
        raise ValueError( 'Bad dealer' )
    if not VULNERABILITIES.has_item( vul ):
            raise ValueError( 'Bad vulnerability' )

    return tuple( dlr, vul, Auction( rbn_list, dlr))

