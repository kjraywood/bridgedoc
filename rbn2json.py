#!/bin/env python3
"""RBN to JSON"""

# deque = double-ended queue
#       = provides methods appendleft, popleft, rotate ...
from collections import deque 
from collections import OrderedDict

DOT = '.'
COLON = ':'
SPACE = ' '
NEWLINE = '\n'

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
VUL_KEYS = tuple( 'ZNEB?' )
VUL_STR = OrderedDict( zip( VUL_KEYS
                          , ( 'None', 'NS', 'EW', 'Both', '?' )
                          )
                     )

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

class RBN_SequenceError( Exception ):
    pass

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
        self.suit = OrderedDict( zip( SUIT_KEYS[:n]
                                    , map( Suit, rbn_suits )
                                    )
                               )
        self.visible = rbn_hand.startswith( COLON )

    def __str__( self ):
        return SPACE.join( [ k + COLON + str( self.suit[k] )
                             for k in self.suit.keys()
                           ]
                         )

class Deal( object ):
    """Input = a deal specified by RBN tag H"""
    def __init__( self, rbn_line):

        # split the hands retaining the delimiter (: or ;)
        # at the start of each suit
        rbn_list = deque( rbn_line.replace( ':', '~:'
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
        self.hand = OrderedDict( zip( rotate( SEAT_KEYS, seat_offset )[:n]
                                    , map( Hand, rbn_list )
                                    )
                               )
    def __str__( self ):
        return NEWLINE.join( [ '[%s] %s' % ( k, str( self.hand[k] ) )
                               for k in self.hand.keys()
                             ]
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

class Round( list ):
    """one round of an auction"""
    def __str__( self ):
        return '  '.join( [ '%-4s' % str(c) for c in self ] )

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
        # that start with west by prepending null calls, then
        # append null calls to reach a multiple of 4
        calls.extendleft( [ Call( None )
                            for _ in range( SEAT_KEYS.index(dlr) )
                          ]
                        )
        calls.extend( [ Call( None )
                        for _ in range( (4 - ( len(calls) % 4)) % 4 )
                      ]
                    )

        # Split auctions into list of rounds of four calls
        while calls:
            self.append( Round( calls.popleft() for _ in range(4) ) )

    def __str__( self ):
        return NEWLINE.join( [ str( rnd ) for rnd in self ] )

class Dealer( str ):
    def __str__( self ):
        return 'Dlr: %s' % ( self )

class Vul( str ):
    def __str__( self ):
        return 'Vul: %s' % ( VUL_STR[ self ] )

def ParseAuctionTag( rbn_line ):
    """Input = an auction specified by RBN tag A
       Return = ( dealer, vulnerability, Auction )
    """
    # split the input
    rbn_list = deque( rbn_line.split( COLON ) )

    # extract dealer+vul and check validity
    dlr, vul = list( rbn_list.popleft() )

    if dlr not in SEAT_KEYS:
        raise ValueError( 'Bad dealer' )
    if vul not in VUL_KEYS:
            raise ValueError( 'Bad vulnerability' )

    return ( dlr, vul, Auction( rbn_list, dlr))

class _RBN_int( int ):
    def __str__( self ):
        return '%s %d' % ( type( self ).__name__, self )

class Session( _RBN_int ):
    pass

class Board( _RBN_int ):
    pass

class NumberedNote( object ):
    def __init__( self, numb, note ):
        """The tag is the number so must be passed as the first arg"""
        self.number = int( numb )
        self.note = note

    def __str__( self ):
        return ( str( self.note ) if self.number is 0
                 else '%d. %s' % ( self.number, self.note )
               )

class Paragraph( str ):
    def __add__( self, value ):
         return self.__class__( super().__add__( SPACE + value ) )

CMNT_CHAR = '%'
LEFT_BRACE = '{'
RIGHT_BRACE = '}'

RBN_CLASS_BY_TAG = { 'H': Hand
                   , 'B': Board
                   , 'S': Session
                   }

ALL_RBN_TAGS = tuple( RBN_CLASS_BY_TAG.keys() ) + NOTE_NUMBERS

def brace_contents( string, level=0 ):
    # If continuing, create a stack with first element = -1
    # -1 to ensure that we return this string from the beginning
    stack = list( range( -1, level - 1 ) )
    for i, c in enumerate( string ):
        if c == LEFT_BRACE:
            stack.append(i)
        elif c == RIGHT_BRACE:
            if not stack:
                raise ValueError( 'End brace without begin brace')
            start = stack.pop()
            if not stack:
                return ( 0, string[ start + 1: i ] )
    return ( len(stack), string[ stack[0] + 1:] )

def ParseRBN( f ):
    """A generator that parses an RBN file and returns each record
       as a list of objects in the record
    """
    # Check the first line
    x = f.readline().rstrip()
    if not ( x.startswith( CMNT_CHAR )
             and x[1:].lstrip().startswith( 'RBN' )
           ):
        raise SyntaxError( 'Not an RBN file' )
    # Start a record
    bridge_rec = []
    for line in f:
        x = line.rstrip()
        # A blank line indicates end-of-record
        # but we delay starting a new record
        # until we have more data
        if not x:
            if bridge_rec is not None:
                yield bridge_rec
                bridge_rec = None
            continue
        if x.startswith( CMNT_CHAR ):
            continue
        # We have something so if we have not yet
        # started a record, then do so now
        if bridge_rec is None:
            bridge_rec = []

        if x.startswith( LEFT_BRACE ):
            level, x = brace_contents( x )
            bridge_obj = Paragraph( x.strip() )
            while level:
                x = f.readline().rstrip()
                if not x:
                    raise SyntaxError( 'Unmatched brace' )
                level, x = brace_contents( x, level )
                bridge_obj += x.strip()
                
            
import sys, fileinput

if __name__ == "__main__":

    with fileinput.input() as f:
        BridgeRecords = list( ParseRBN( f ) )
