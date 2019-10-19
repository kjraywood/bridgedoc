#!/bin/env python3
"""RBN to JSON"""

# deque = double-ended queue
#       = provides methods appendleft, popleft, rotate ...
from collections import deque 

DOT = '.'
COLON = ':'
SPACE = ' '
NEWLINE = '\n'
NULL_DATA = '_'

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
VUL_NAME = dict( zip( VUL_KEYS
                    , ( 'None', 'NS', 'EW', 'Both', '?' )
                    )
               )

# suits, strains and levels
SUIT_KEYS = tuple( 'SHDC' )

STRAINS = ( 'N', ) + SUIT_KEYS
LEVELS = tuple( map( str, range(1,8) ) )

# Seats
SEAT_KEYS = tuple( 'WNES' )
SEAT_NAME = dict( zip( SEAT_KEYS
                     , ( 'West', 'North', 'East', 'South' )
                     )
                 )

def rotate( vec, num):
    """return a vector rotated by num steps"""
    return vec[num:] + vec[:num]

# extended string function that handles nulls
def xstr(s,default=''):
    return default if s is None else str(s)

def data( obj ):
    return obj._data()

def named_data( obj ):
    return ( type( obj ).__name__, data( obj ) )

class RBN_list( list ):
    """The elements of an RBN list have a _data method"""
    def _data( self ):
        return list( map( data, self ) )

class HeldSuit( object ):
    """A HeldSuit is a suit denomination and cards"""
    def __init__( self, suit, cards ):
        self.suit = suit
        self.cards = cards
    def __str__( self ):
        return '%s:%s' % ( self.suit, self.cards )
    def _data( self ):
        return ( self.suit, self.cards )

class Hand( object ):
    """A hand has a seat, a list of held-suits, and a visibility flag"""
    def __init__( self, seat, rbn_hand):
        """Input = string of a single hand with leading : or ;"""
        if not rbn_hand:
            raise SyntaxError('Null input to Hand')

        rbn_suits = rbn_hand[1:].split( DOT )
        n = len(rbn_suits)
        if n > 4 :
            raise ValueError( 'too many suits' )

        self.seat = seat
        self.held_suits = list( HeldSuit( suit, cards )
                                for suit, cards
                                in zip( SUIT_KEYS[:n], rbn_suits )
                              )
        self.visible = rbn_hand.startswith( COLON )

    def __str__( self ):
        return '[%-5s] %s' % ( SEAT_NAME[ self.seat ]
                           , SPACE.join( map( str, self.held_suits ) )
                           )

    def _data( self ):
        return ( SEAT_NAME[ self.seat ], dict( map( data, self.held_suits ) ) )

class Deal( RBN_list ):
    """A Deal is a list of hands"""
    def __init__( self, rbn_line):
        """Input = a deal specified by RBN tag H"""

        # split the hands retaining the delimiter (: or ;)
        # at the start of each suit
        rbn_list = deque( rbn_line.replace( ':', '~:'
                                          ).replace( ';', '~;'
                                                   ).split( '~' )
                        )

        start_seat = rbn_list.popleft()
        if start_seat not in SEAT_KEYS:
            raise ValueError( 'Bad starting seat' )

        n = len( rbn_list )
        if n > 4:
            raise ValueError( 'too many hands' )

        seats = rotate( SEAT_KEYS, SEAT_KEYS.index( start_seat ) )[:n]

        super().__init__( Hand( seat, rbn_hand )
                           for seat, rbn_hand
                           in zip( seats, rbn_list )
                        )

    def __str__( self ):
        return NEWLINE.join( map( str, self.hands ) )

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
            raise RuntimeError( 'Call already has strain' )
        if strain not in STRAINS:
            raise ValueError( 'Invalid strain' )
        self.strain = strain

    def add_notation( self, rbn_char ):
        if not self.is_open:
            raise RunTimeError( 'Call is closed. Cannot add notation' )
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
               + xstr( self.note_number if self.notation == NOTE_FLAG
                       else None )
               )
    def _data( self ):
        return ( xstr( self.level, default=NULL_DATA )
               + xstr( self.strain, default=NULL_DATA )
               + xstr( ( self.note_number
                         if self.notation == NOTE_FLAG
                         else self.notation
                       )
                     , default=NULL_DATA
                     )
               )

class Round( RBN_list ):
    """A round is a list of calls"""
    def __str__( self ):
        return '  '.join( [ '%-4s' % str(c) for c in self ] )

class Auction( RBN_list ):
    """An auction is a list of rounds
       constructed from a sequence of calls
    """
    def __init__( self, rbn_line, dlr ):
        super().__init__([])

        # rbn_line is a colon-separated list of auction rounds
        if not rbn_line:
            return

        rbn_rounds = deque( rbn_line.split( COLON ) )
        
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
                raise ValueError( 'blank round' )

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
        if not calls:
            return

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

class RBN_str( str ):
    def _data( self ):
        return super().__str__()

class Dealer( RBN_str ):
    def __new__( cls, value ):
        if value in SEAT_KEYS:
            return super().__new__( cls, value )
        else:
            raise ValueError( 'Bad dealer' )

    def __str__( self ):
        return 'Dlr: ' + self

class Vul( str ):
    def __new__( cls, value ):
        if value in VUL_KEYS:
            return super().__new__( cls, value )
        else:
            raise ValueError( 'Bad vulnerability' )

    def __str__( self ):
        return 'Vul: %s' % ( VUL_NAME[ self ] )
    def _data( self ):
        return VUL_NAME[ self ]

def ParseAuctionTag( rbn_line ):
    """Input = an auction specified by RBN tag A
       Return = iter( dealer, vulnerability, Auction )
    """
    # split the input into the Dealer+Vul string
    # and the remainder
    head, tail = rbn_line.split( COLON, 1 )

    # extract dealer+vul
    d, v = list( head )

    yield Dealer(d)
    yield Vul(v)
    yield Auction( tail, d)

class RBN_int( int ):
    def __str__( self ):
        return '%s %d' % ( type( self ).__name__, self )
    def _data( self ):
        return super().__str__()

class Session( RBN_int ):
    pass

class Board( RBN_int ):
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
    def _data( self ):
        return ( str( self.number), self.note )

class Paragraph( RBN_str ):
    def __new__( cls, value ):
        return super().__new__( cls, value.strip() )

    def __add__( self, value ):
         return self.__class__( super().__add__( SPACE + value.lstrip() ) )

CMNT_CHAR = '%'
LEFT_BRACE = '{'
RIGHT_BRACE = '}'

def brace_contents( string, level=0 ):
    stack = list( range( level ) )
    for i, c in enumerate( string, 1 ):
        if c == LEFT_BRACE:
            stack.append(i)
        elif c == RIGHT_BRACE:
            if not stack:
                raise SyntaxError( 'End brace without begin brace' )
            start = stack.pop()
            if not stack:
                if string[i:].strip():
                    raise SyntaxError( 'Content after end brace' )
                return ( 0, string[ start : i-1 ] )
        elif not stack and c.strip():
                raise SyntaxError( 'Content before begin brace' )
    if not stack:
        raise ValueError( 'Blank input' )
    return ( len(stack), string[ stack[0] : ] )

RBN_CLASS_BY_TAG = { 'H': Deal
                   , 'B': Board
                   , 'S': Session
                   }

AUCTION_TAG = 'A'

class BridgeRecord( list ):
    """The elements of a BridgeRecord are various classes of
       RBN object, each with a name _data method.  So the data
       of the BridgeRecord must be named to identify them.
    """
    def _data( self ):
        return list( map( named_data, self ) )

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
    bridge_rec = BridgeRecord()
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
            bridge_rec = BridgeRecord()

        if x.startswith( LEFT_BRACE ):
            level, x = brace_contents( x )
            bridge_obj = Paragraph( x )
            while level:
                x = f.readline().rstrip()
                if not x:
                    raise SyntaxError( 'Unmatched brace' )
                level, x = brace_contents( x, level )
                bridge_obj += x
            bridge_rec.append( bridge_obj )
        else:
            tag, data = x.split( maxsplit=1 )
            if tag == AUCTION_TAG:
                bridge_rec.extend( ParseAuctionTag( data ) )
            elif tag in RBN_CLASS_BY_TAG.keys():
                bridge_rec.append( RBN_CLASS_BY_TAG[ tag ](data) )
            elif tag in ('0',) + NOTE_NUMBERS:
                bridge_rec.append( NumberedNote( tag, data ) )
            else:
                raise ValueError( 'Unknown tag' )
    if bridge_rec is not None:
        yield bridge_rec

import sys, fileinput, json

if __name__ == "__main__":

    with fileinput.input() as f:
        BridgeRecords = list( ParseRBN( f ) )

    print( json.dumps( list( rec._data() for rec in BridgeRecords )
                     , indent=None
                     )
         )
