#!/bin/env python3
"""RBN to JSON"""

# a list-like sequence that includes methods popleft and rotate
from collections import deque as CollectionsList

DOT = '.'
COLON = ':'

class RBN_SequenceError( Exception ):
    pass

# Notations
NOTE_CONV = '*'
NOTE_FLAG = '^'

NOTATIONS = ( NOTE_CONV, NOTE_FLAG )
NOTE_NUMBERS = tuple( map( str, range(1,10) ) )

# Non-bid calls
PASS = 'P'
DOUBLE = 'X'
REDOUBLE = 'R'
ALL_PASS = 'A'
YOUR_CALL = 'Y'

NONBID_CALLS = ( PASS, DOUBLE, REDOUBLE, ALL_PASS, YOUR_CALL )

# Vulnerabilities
NONE_VUL = 'Z'
NS_VUL = 'N'
EW_VUL = 'E'
BOTH_VUL = 'B'
UNKNOWN_VUL = '?'

VULNERABILITIES = ( NONE_VUL, NS_VUL, EW_VUL, BOTH_VUL, UNKNOWN_VUL )

# suits, strains and levels
NOTRUMP = 'N'
SPADES = 'S'
HEARTS = 'H'
DIAMONDS = 'D'
CLUBS = 'C'

SUIT_KEYS = ( SPADES, HEARTS, DIAMONDS, CLUBS )
STRAINS = ( NOTRUMP, ) + SUIT_KEYS
LEVELS = tuple( map( str, range(1,8) ) )

# Seats
WEST  = 'W'
NORTH = 'N'
EAST  = 'E'
SOUTH = 'S'

SEAT_KEYS = ( WEST, NORTH, EAST, SOUTH )

def rotate( vec, num):
    """return a vector rotated by num steps"""
    return vec[num:] + vec[:num]

# extended string function that handles nulls
def xstr(s):
    return '' if s is None else str(s)

class Suit( list ):
    """Input = string containing cards in a single suit"""
    def __str__( self ):
        return self.string()

    def string( self, sep = '' ):
        return sep.join( self )

class Hand( object ):
    """Input = string of a single hand with leading : or ;"""
    def __init__( self, rbn_hand):
        if not rbn_hand:
            raise SyntaxError('Null input to Hand')

        rbn_suits = rbn_hand[1:].split( DOT )
        n = len(rbn_suits)
        if n > 4 :
            raise ValueError( 'too many suits' )

        # Create a dictionary with keys from SUIT_KEYS and
        # values of class Suit mapped to each item of rbn_suits
        self.suit = dict( zip( SUIT_KEYS[:n]
                             , map( Suit, rbn_suits )
                             )
                        )
        self.visible = rbn_hand.startswith( COLON )

class Deal( object ):
    """Input = a deal specified by RBN tag H"""
    def __init__( self, rbn_line):

        # split the hands retaining the delimiter (: or ;)
        # at the start of each suit
        rbn_list = CollectionsList( rbn_line.replace( ':', '~:'
                                             ).replace( ';', '~;'
                                               ).split( '~' )
                                  )

        # determine the rotation relative to west
        try:
            seat_offset = SEAT_KEYS.index( rbn_list.popleft() )
        except:
            raise ValueError( 'Bad starting seat' )

        n = len( rbn_list )
        if n > 4:
            raise ValueError( 'too many hands' )

        # save hands in a dictionary
        self.hand = dict( zip( rotate( SEAT_KEYS, seat_offset )[:n]
                             , map( Hand, rbn_list )
                             )
                        )

class Call( object ):
    def __init__( self, rbn_char ):
        self.level  = rbn_char if rbn_char in LEVELS       else None
        self.strain = rbn_char if rbn_char in NONBID_CALLS else None
        if self.level or self.strain or (rbn_char is None):
            self.is_open = bool( rbn_char )
            self.notation = None
        else:
            raise ValueError( 'Invalid call' )

    def add_strain( self, strain ):
        if self.strain:
            raise RBN_SequenceError( 'Call already has strain' )

        if strain not in STRAINS:
            raise ValueError( 'Invalid strain' )

        self.strain = strain

    def add_notation( self, rbn_char ):
        if not self.is_open:
            raise RBN_SequenceError( 'Call is closed. Cannot add notation' )

        if self.notation:
            # notation must be NOTE_FLAG since is_open is true
            # but check anyway to be ready for other types
            if self.notation == NOTE_FLAG:
                if rbn_char in NOTE_NUMBERS:
                    self.note_number = rbn_char
                    self.is_open = False
                else:
                    raise ValueError( 'Notification requires number' )
            else:
                raise Exception( 'Impossible path' )

        elif rbn_char in NOTATIONS:
            self.notation = rbn_char
            self.is_open = ( rbn_char == NOTE_FLAG )
        else:
            self.is_open = False
            return False

        return True

    def __bool__( self ):
        return bool( self.strain
                     and not ( self.notation and self.is_open )
                   )
    def __str__( self ):
        return ( xstr( self.level )
               + xstr( self.strain )
               + xstr( self.notation )
               + xstr( self.note_number if self.notation == NOTE_FLAG else None )
               )

class Auction( list ):
    def __init__( self, rbn_rounds, dlr ):
        super().__init__([])
        # rbn_rounds is a list of auction strings for each round
        if not rbn_rounds:
            return

        # go through each round building a list of all calls
        calls = CollectionsList()
        num_calls_remaining = 0

        while rbn_rounds:
            # Check for missing calls from previous round
            if num_calls_remaining:
                raise ValueError( 'incomplete round' )

            # Pop the next round and do not allow blank rounds
            rnd = CollectionsList( rbn_rounds.popleft() )
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
        # that start with west by prepending null calls, then
        # append null calls to reach a multiple of 4
        calls.extendleft( [ Call( None ) for _ in range( SEAT_KEYS.index(dlr) ) ] )
        calls.extend( [ Call( None ) for _ in range( (4 - ( len(calls) % 4)) % 4 ) ] )

        # Split auctions into simple lists of rounds of four calls
        while calls:
            self.append( [ calls.popleft() for _ in range(4) ] )

def ParseAuctionTag( rbn_line ):
    """Input = an auction specified by RBN tag A
       Return = ( dealer, vulnerability, Auction )
    """
    # split the input
    rbn_list = CollectionsList( rbn_line.split( COLON ) )

    # extract dealer+vul and check validity
    dlr, vul = list( rbn_list.popleft() )

    if dlr not in SEAT_KEYS:
        raise ValueError( 'Bad dealer' )
    if vul not in VULNERABILITIES:
            raise ValueError( 'Bad vulnerability' )

    return ( dlr, vul, Auction( rbn_list, dlr))
