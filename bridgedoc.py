#!/bin/env python
"""BridgeDoc preprocessor"""

import argparse, re

# Suit bids
BIDS_REGEX = re.compile( r'([1-7])([CDHS])' )
BIDS_REPL  = r'\1{\2}'

def proc_bids( s ):
    """ Sub bids: 1C -> 1{C}, ..."""
    return BIDS_REGEX.sub( BIDS_REPL, s )

# Allow escaping of C,D,H or S
ESC_REGEX = re.compile( r'\\([CDHS])' )
ESC_REPL  = r'\1'

def proc_esc( s ):
    """ \C -> C, ..."""
    return ESC_REGEX.sub( ESC_REPL, s )

# Suit-lengths
SUITLEN_REGEX = re.compile( r'(\d)\*([{mMoO])' )
SUITLEN_REPL = r'\1{xtimes}\2'

# For identifying section-header lines
HEADER_REGEX = re.compile( r'^=+\s+' )

def proc_suitlen( s ):
    """ Sub suit-lengths: 4*m -> 4{xtimes}m """
    return SUITLEN_REGEX.sub( SUITLEN_REPL, s )

# Alerts
ALERT_REGEX = re.compile( r'!([\w{}]+)!' )
ALERT_REPL  = r'[alert]#\1#'

ALERT_REGEX2 = re.compile( r'!!([\w{}]+)!!' )
ALERT_REPL2  = r'[alert]##\1##'

def proc_alerts( s ):
    """ Sub alerts: !3{S}! -> [alert]##3{S}## """
    return ALERT_REGEX.sub( ALERT_REPL
                          ,  ALERT_REGEX2.sub( ALERT_REPL2, s )
                          )

# in-line level-4 header
L4HEAD_REGEX = re.compile( r'^&([^&]+)&(?=[^&]|$)' )
L4HEAD_REPL  = r'[bold-brickred]##\1##'

def proc_l4head( s ):
    """ Sub lev-4 header: &text& -> [boldbrickred]##text## """
    return L4HEAD_REGEX.sub( L4HEAD_REPL, s )


# Lines beginning with ALERT:
ALERT_LINE_REGEX = re.compile( r'^ALERT:\s+(.*)$' )
ALERT_LINE_REPL  = r'{important} [blue]##__\1__##'

def proc_alert_line( s ):
    """ Sub lines beiginging with 'ALERT: '"""
    return ALERT_LINE_REGEX.sub( ALERT_LINE_REPL, s )

# Parse input line
parser = argparse.ArgumentParser(description='Preprocess a BridgeDoc file')
parser.add_argument('bdocfile', type=argparse.FileType('r'))
parser.add_argument('adocfile', type=argparse.FileType('w'))
args = parser.parse_args()

# wrapping-list bullets and backspace
WL_BULLS = {  '@' : ( '&nbsp;{bull}'         , None )
           , '@@' : ( '&emsp;&nbsp;{tribull}', '{backspace}' )
           , '_'  : ( '&emsp;'               , '{backspacex}' )
           , '__' : ( '&emsp;&emsp;'         , '{backspace}{backspace}' )
           }

# wrapping-list format-string
WL_FMT = '[nobr]##%s %s##%s'

# asciidoc new-line
ADNL = ' +\n'

with args.bdocfile as f:
    bdoc = f.readlines()

adoc = []
prev = False

for line in bdoc:

    # Bids and suit-lengths on lines that do not begin with '['
    # and are not header lines following a blank line
    if not line.startswith( '[' ) and (
         prev or not HEADER_REGEX.match( line ) ):
        line = proc_bids( line )
        line = proc_suitlen( line )

    line = proc_esc( line )
    line = proc_alerts( line )
    line = proc_l4head( line )
    line = proc_alert_line( line )
    
    # Wrapping lists
    try:
        # unpacking the split line will raise a ValueError
        # if there are not exactly two values
        head, tail = line.split( None, 1)

        # If the first word is not a valid bullet-parameter
        # then NameError will be raised
        bull, backspace = WL_BULLS[ head ]
    except:
        pass
    else:
        # Is there something to be added to the previous line?
        if backspace:
            line = adoc.pop()
            n = -3 if line.endswith( ADNL ) else -1
            adoc.append( line[:n] + backspace + line[n:] )

        # Determine index for inserting before EOL
        n = -3 if tail.endswith( ADNL ) else -1
        line = WL_FMT % ( bull, tail[:n], tail[n:] )

    adoc.append( line )

    # If the line starts with '[', then do not change
    # the value of prev.
    if not line.startswith( '[' ):
        prev = bool( line.strip() )

with args.adocfile as f:
    f.writelines( adoc )
