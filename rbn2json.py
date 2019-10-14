#!/bin/env python3
"""RBN to JSON"""

DOT = "."
COLON = ":"
SEMICOLON = ";"

ROTATE_BY_DIR = { "W": 0, "N": 1, "E": 2, "S": 3 }

class Suit( list ):
    def __init__( self, rbnsuit ):
        """Input = string containing cards in a single suit"""
        super().__init__( rbnsuit.upper() )

    def __str__( self ):
        return self.string()

    def string( self, sep = '' ):
        return sep.join( self )

    def has_card( self, card ):
        try:
            i = self.index( card )
            return True
        except ValueError:
            return False

class Hand( object ):
    def __init__( self, rbnhand):
        """Input = single hand with leading colon or semicolon of RBN tag H"""
        try:
            suits = rbnhand[1:].split( DOT )
            if len(suits) != 4 :
                raise ValueError( 'wrong number of suits' )
            self.clubs    = Suit( suits.pop() )
            self.diamonds = Suit( suits.pop() )
            self.hearts   = Suit( suits.pop() )
            self.spades   = Suit( suits.pop() )
            self.valid = True
            self.visible = rbnhand.startswith( COLON )
        except:
            self.valid = False
            self.visible = False

    def __bool__( self ):
        return self.valid

# a list-like sequence that includes methods popleft and rotate
from collections import deque

class Deal( object ):
    def __init__( self, rbndeal):
        """Input = a deal specified by RBN tag H"""

        try:
            # split the deal retaining the delimiter (: or ;)
            # at the start of each suit
            sdeal = deque( rbndeal.replace( ':', '~:'
                                          ).replace( ';', '~;'
                                                   ).split( '~' )
                         )

            # get the starting direction
            start_dir = sdeal.popleft()

            n = len( sdeal )
            if n > 4:
                raise ValueError( 'too many hands' )

            # Add nulls for missing hands
            sdeal.extend( [ None for _ in range( 4 - n ) ] )

            # populate list of hands
            hands = deque( [ Hand( x ) for x in sdeal ] )
        
            # rotate the list according to the starting direction
            hands.rotate( ROTATE_BY_DIR[ start_dir ] )
            self.west = hands.popleft()
            self.north = hands.popleft()
            self.east = hands.popleft()
            self.south = hands.popleft()
            self.valid = True
        except:
            self.valid = False
