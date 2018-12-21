#!/usr/bin/python
# -*- coding: UTF-8-*-
import sys
import json
import analyze_sound
import markup

# main.py
#
# The main module for DIRECT.

__date__ ="Last Updated: Dec 21, 2018"

def usage():
    print """
        python main.py [text_to_be_analyzed.txt] [text_type]
        """

#read user input
text = sys.argv[1]
text_type = sys.argv[2]

#initialize dictionaries (only needed when data files get updated/json files get corrupted)
'''
analyze_sound.get_info(1)
analyze_sound.get_info(2)
analyze_sound.get_info(3)
'''

#load dictionaries
dummy_dict = analyze_sound.load_dummydict()
dummy_initgroups = analyze_sound.load_dummyinit()
schuessler_dict = analyze_sound.load_schuesslerdict()

#still need to write code to scrape this from baxter
#bs_dict = {}

#TBD if we're doing any additional work with tags
#tags = {}

try:
    #OC markup
    markup.markup_text(text, dummy_dict, dummy_initgroups, schuessler_dict, text_type)

except UnicodeEncodeError:
    print('unicode encoding error')

except IOError:
    sys.stderr.write("ERROR: Cannot read inputfile.\n")
    sys.exit(1)
