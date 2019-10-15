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

DIRECTIONS = RBNlist( 'WNES' )
VULNERABILITIES = RBNlist( 'ZNEB?' )
NONBID_CALLS = RBNlist( 'PXRAY' )
STRAINS = RBNlist( 'NSHDC' )
LEVELS = RBNlist( map( str, range(1,8) ) )
OPINIONS = RBNlist( '!?' )
CONVENTIONAL = RBNlist( '*' )
ALERTS = RBNlist( '^' )
ALERT_NUMBERS = RBNlist( map( str, range(1,10) ) )

class RBNobject( object ):
    def __init__( self ):
        self.valid = False

    def __bool__( self ):
        return self.valid
    
class Suit( RBNlist ):
    """Input = string containing cards in a single suit"""
    def __str__( self ):
        return self.string()

    def string( self, sep = '' ):
        return sep.join( self )

class OneHand( RBNobject ):
    """Input = string of a single hand with leading : or ;"""
    def __init__( self, rbn_hand):
        try:
            suits = rbn_hand[1:].split( DOT )
            if len(suits) != 4 :
                raise ValueError( 'wrong number of suits' )
            self.clubs    = Suit( suits.pop() )
            self.diamonds = Suit( suits.pop() )
            self.hearts   = Suit( suits.pop() )
            self.spades   = Suit( suits.pop() )
            self.valid = True
            self.visible = rbn_hand.startswith( COLON )
        except:
            self.valid = False
            self.visible = False

class Hands( RBNobject ):
    """Input = a deal specified by RBN tag H"""
    def __init__( self, rbn_line):

        try:
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
            four_hands = deque( [ OneHand( x ) for x in hand_list ] )
        
            # rotate the list according to the starting direction
            four_hands.rotate( DIRECTIONS.index( start_dir ) )
            self.west = four_hands.popleft()
            self.north = four_hands.popleft()
            self.east = four_hands.popleft()
            self.south = four_hands.popleft()
            self.valid = True
        except:
            self.valid = False

class Call( RBNobject ):
    def __init__( self, rbn_char ):
        self.is_bid = LEVELS.has_item( rbn_char )
        if self.is_bid:
            self.level = rbn_char
            self.strain = None
            self.valid = False
        else:
            self.valid = NONBID_CALLS.has_item( rbn_char )
            self.rbn_char = rbn_char if self.valid else None
        self.note_open = self.valid

    def add_strain( self, strain ):
        self.valid = self.bid and STRAINS.has_item( strain )
        self.strain = strain if self.valid else None
        self.note_open = self.valid

    ### FIXME ###
    # def add_note( self, note ):
    #     self.valid = self.note_open

                            
    #                     if NOTATIONS.has_item( s ):
    #                         c.set_note( s )
    #                         if round_chars:
    #                             s = round_chars.popleft()
    #                             if NOTATIONS.has_item( s ):
    #                                 c.append_note( s)
    #                             else:
    #                     else if 
    #############



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
                if c.is_bid:
                    c.add_strain( rnd.popleft() )

                # Check for call notation
                while c.is_open and rnd:
                    if c.add_note( rnd[0] ):
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

