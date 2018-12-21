#!/usr/bin/python
# -*- coding: UTF-8-*-
import sys
import re
import file_handling

# markup.py
#
# This program marks up a Chinese text with phonological information in HTML.

__author__="John O'Leary <jo.10@princeton.edu>"
__date__ ="Last Updated: Dec 7, 2018"

eol_punctuation = tuple(('．'.decode('utf-8'), '。'.decode('utf-8'), '？'.decode('utf-8'),'；'.decode('utf-8')))
ignore = tuple(('、'.decode('utf-8'), '，'.decode('utf-8')))

def usage():
    print """
        python markup.py [text_to_markup.txt] [dummy_dict] [dummy_initgroup_dict] [phonology_dict]
        """

def write_header(markup_file, text_type, markup_type):
    css_file = file_handling.get_cssfilepath(markup_type)

    #add opening HTML tags
    markup_file.write('<!DOCTYPE html>\n')
    markup_file.write('<html>\n')
    markup_file.write('\n')

    #add HTML Head
    markup_file.write('<head>\n')
    markup_file.write('<meta charset="utf-8">\n')
    css_depth = file_handling.handle_cssdepth(text_type, css_file)
    markup_file.write(css_depth)
    markup_file.write('</head>\n')
    markup_file.write('\n')

def write_footer(markup_file):
    markup_file.write('</ruby>\n')
    markup_file.write('</body>\n')
    markup_file.write('</html>')

def handle_furigana(char, ruby_count, schuessler_dict):
    left_write = ''
    while ruby_count > 0:
        left_write += '<ruby>'
        ruby_count -= 1
    left_write += '<rb>%s</rb>' % char.encode('utf-8')
    for entry in schuessler_dict[char]:
        if isinstance(entry, list):
            for subentry in entry:
                left_write += '<rt>%s</rt></ruby>' % subentry.encode('utf-8')
        else:
            left_write += '<rt>%s</rt></ruby>' % entry.encode('utf-8')
    return left_write

def markup_text(poem_file, dummy_dict, dummy_initgroups, schuessler_dict, text_type):
    try:
        #read in arguments
        #read in input file
        #all HTML code adapted from examples from w3 school's tutorials
        input_file_path = file_handling.get_inputfilepath(text_type, poem_file)
        markup_file_path = file_handling.get_markupfilepath(text_type, poem_file)
        #phonology_file = '../output/%s_reconstructions.txt' % (poem_file[:-4])
    
        markup_file = open(markup_file_path, 'w')
        write_header(markup_file, text_type, 1)
        #write_body(input_file_path, markup_file, poem_file, dummy_dict, text_type)
        
        #begin HTML body
        markup_file.write('<body>\n')
        markup_file.write('<ruby>\n')
        #begin check of input file
        with open(input_file_path) as fp:
            
            left_text = []
            right_text = []
            towrite = ''
            
            reading_count = 0
            input_raw = open(input_file_path, "r")
            input_text = input_raw.read().decode('utf-8')
            for reading in input_text:
                parts = re.split('\t+', reading)
                char = parts[0]
                #first check to see if character in question is a special one that can be ignored, such punctuation, newline, carriage return, etc.
                if char in eol_punctuation:
                    towrite = '%s<br/>' % char
                    left_text.append(towrite.encode('utf-8'))
                    right_text.append(towrite.encode('utf-8'))
                elif char == '\n'.decode('utf-8'):
                    towrite = '<br/>'
                    left_text.append(towrite.encode('utf-8'))
                    right_text.append(towrite.encode('utf-8'))
                elif char in ignore:
                    towrite = '%s' % char
                    left_text.append(towrite.encode('utf-8'))
                    right_text.append(towrite.encode('utf-8'))
                elif char == '\r'.decode('utf-8'):
                    pass
                #if not an ignore character, check to see if we can mark it up in various ways
                else:
                    #check to see if it's in our dummy dictionary
                    if char in dummy_dict:
                        dummy_info = dummy_dict[char]
                        dummy_init = dummy_info[0][0]
                        dummy_rhyme = dummy_info[0][1]
                        dummy = dummy_info[0][2]
                        right_text.append('<a><div class="tooltip">%s<span class="tooltiptext">%s, %s</span></div></a>' % (dummy.encode('utf-8'), dummy_initgroups[str(dummy_init)].encode('utf-8'), dummy_rhyme.encode('utf-8')))
                    else:
                        right_text.append('%s' % char.encode('utf-8'))
                    ruby_count = 0
                    #check to see if schuessler reconstructed it
                    if char in schuessler_dict:
                        for item in schuessler_dict[char]:
                            ruby_count += 1
                        left_write = handle_furigana(char, ruby_count, schuessler_dict)
                    else:
                        left_write = char.encode('utf-8')
                    left_text.append(left_write)
                    reading_count += 1

        #write left side
        markup_file.write('<div class="split left">')
        for item in left_text:
            markup_file.write('%s' % item)
        markup_file.write('</div>')

        #write right side
        markup_file.write('<div class="split right">')
        for item in right_text:
            markup_file.write('%s' % item)
        markup_file.write('</div>')
        
        #add closing HTML tags
        write_footer(markup_file)
        print '%s marked up' % poem_file

    except IOError:
        sys.stderr.write("ERROR: Cannot read inputfile.\n")
        sys.exit(1)

def process_char(char, dummy_dict):
    return_this = []
    if char in eol_punctuation:
        towrite = '%s' % char
        return_this.append(towrite.encode('utf-8'))
        return_this.append(towrite.encode('utf-8'))
    elif char == '\n'.decode('utf-8'):
        towrite = '<br/><br/>'
        return_this.append('newline')
        return_this.append(towrite.encode('utf-8'))
    elif char in ignore:
        towrite = '%s' % char
        return_this.append(towrite.encode('utf-8'))
        return_this.append(towrite.encode('utf-8'))
    elif char == '\r'.decode('utf-8'):
        return_this.append('pass')
    else:
        if char in dummy_dict:
            dummy_info = dummy_dict[char]
            right_char = dummy_info[0][2]
        else:
            right_char = char
        return_this.append(char.encode('utf-8'))
        return_this.append(right_char.encode('utf-8'))
    return return_this

    '''
    def bsmarkup(poem_file, dummy_dict, dummy_initgroups, bs_dict, text_type):
    try:
    #read in arguments
    #read in input file
    #all HTML code adapted from examples from w3 school's tutorials
    input_file_path = '../data/raw_text/tang/%s.txt' % poem_file
    markup_file_path = '../output/markup/tang/%s_markup.html' % poem_file
    #phonology_file = '../output/%s_reconstructions.txt' % (poem_file[:-4])
    
    markup_file = open(markup_file_path, 'w')
    write_header(markup_file, text_type, 2)
    print "done"
    
    write_body(input_file_path, markup_file, poem_file, dummy_dict, text_type)
    #add closing HTML tags
    markup_file.write('</p>\n')
    markup_file.write('</twrap>\n')
    markup_file.write('</body>\n')
    markup_file.write('</html>')
    
    print '%s marked up' % poem_file
    
    print '%s marked up' % poem_file
    
    except IOError:
    sys.stderr.write("ERROR: Cannot read inputfile.\n")
    sys.exit(1)
    
    
    def make_marker(markup_file, title, subtitle, poem, title_no, subtitle_no, poem_no, line_no, marker_type):
    marker = ''
    if marker_type == 1:
    marker = '<tspace1><a><div class="tooltip">‧<span class="tooltiptext">%s</span></div></a></tspace1>' % (title.encode('utf-8'))
    elif marker_type == 2:
    marker = '<tspace1><a><div class="tooltip">‧<span class="tooltiptext">%s‧%s</span></div></a></tspace1>' % (title.encode('utf-8'), subtitle.encode('utf-8'))
    elif marker_type == 3:
    if subtitle != '':
    marker = '<tspace1><a><div class="tooltip">‧<span class="tooltiptext">%s‧%s</span></div></a></tspace1>' % (title.encode('utf-8'), subtitle.encode('utf-8'))
    else:
    marker = '<tspace1><a><div class="tooltip">‧<span class="tooltiptext">%s</span></div></a></tspace1>' % (title.encode('utf-8'))
    elif marker_type == 4:
    marker = '<tspace1><a><div class="tooltip">‧<span class="tooltiptext">%s</span></div></a></tspace1>' % (title.encode('utf-8'))
    elif marker_type == 5:
    marker = '<tspace1><a><div class="tooltip">‧<span class="tooltiptext">%s‧%s</span></div></a></tspace1>' % (title.encode('utf-8'), subtitle.encode('utf-8'))
    elif marker_type == 6:
    marker = '<tspace1><a><div class="tooltip">‧<span class="tooltiptext">%s‧%s‧%s</span></div></a></tspace1>' % (title.encode('utf-8'), subtitle.encode('utf-8'), poem.encode('utf-8'))
    else:
    if poem != '':
    marker = '<tspace1><a><div class="tooltip">‧<span class="tooltiptext">%s‧%s‧%s</span></div></a></tspace1>' % (title.encode('utf-8'), subtitle.encode('utf-8'), poem.encode('utf-8'))
    elif subtitle != '':
    marker = '<tspace1><a><div class="tooltip">‧<span class="tooltiptext">%s‧%s</span></div></a></tspace1>' % (title.encode('utf-8'), subtitle.encode('utf-8'))
    else:
    marker = '<tspace1><a><div class="tooltip">‧<span class="tooltiptext">%s</span></div></a></tspace1>' % (title.encode('utf-8'))
    return marker
    
def write_body(input_file_path, markup_file, poem_file, dummy_dict, text_type):
    title = ''
    subtitle = ''
    poem = ''
    title_no = 0
    subtitle_no = 0
    poem_no = 0
    line_no = 0

    #begin HTML body
    markup_file.write('<body>\n')
    markup_file.write('<twrap>\n')
    print(input_file_path)
    with open(input_file_path) as fp:
        left_text = []
        right_text = []
        towrite = ''

        input_raw = open(input_file_path, "r")
        input_text = input_raw.readlines()
        left_line = ''
        right_line = ''

        if text_type == '3':
            for line in input_text:
                tocheck = line.decode('utf-8')
                if tocheck[0:7] == '[TITLE]':
                    subtitle = ''
                    title = tocheck[7:]
                    title_no += 1
                    marker = make_marker(markup_file, title, subtitle, poem, title_no, subtitle_no, poem_no, line_no, 1)
                    left_line += marker
                    left_line += '<tspace2>'
                    for char in title:
                        toappend = process_char(char, dummy_dict)
                        if toappend[0] == 'pass':
                            pass
                        elif toappend[0] == 'newline':
                            left_line += '</tspace2>'
                            right_line += '</tspace2>%s' % toappend[1]
                            left_text.append(left_line)
                            right_text.append(right_line)
                            left_line = ''
                            right_line = ''
                        else:
                            left_line += toappend[0]
                            right_line += toappend[1]
                elif tocheck[0:10] == '[SUBTITLE]':
                    subtitle = tocheck[10:]
                    subtitle_no += 1
                    marker = make_marker(markup_file, title, subtitle, poem, title_no, subtitle_no, poem_no, line_no, 2)
                    left_line += marker
                    left_line += '<tspace2>'
                    for char in subtitle:
                        toappend = process_char(char, dummy_dict)
                        if toappend[0] == 'pass':
                            pass
                        elif toappend[0] == 'newline':
                            left_line += '</tspace2>'
                            right_line += '</tspace2>%s' % toappend[1]
                            left_text.append(left_line)
                            right_text.append(right_line)
                            left_line = ''
                            right_line = ''
                        else:
                            left_line += toappend[0]
                            right_line += toappend[1]
                else:
                    marker = make_marker(markup_file, title, subtitle, poem, title_no, subtitle_no, poem_no, line_no, 3)
                    left_line += marker
                    left_line += '<tspace2>'
                    for char in tocheck:
                        toappend = process_char(char, dummy_dict)
                        if toappend[0] == 'pass':
                            pass
                        elif toappend[0] == 'newline':
                            left_line += '</tspace2>'
                            right_line += '</tspace2>%s' % toappend[1]
                            left_text.append(left_line)
                            right_text.append(right_line)
                            left_line = ''
                            right_line = ''
                        else:
                            left_line += toappend[0]
                            right_line += toappend[1]
        else:
            for line in input_text:
                tocheck = line.decode('utf-8')
                if tocheck[0:9] == '[SECTION]':
                    subtitle = ''
                    title = tocheck[9:]
                    title_no += 1
                    marker = make_marker(markup_file, title, subtitle, poem, title_no, subtitle_no, poem_no, line_no, 4)
                    left_line += marker
                    left_line += '<tspace2>'
                    for char in title:
                        toappend = process_char(char, dummy_dict)
                        if toappend[0] == 'pass':
                            pass
                        elif toappend[0] == 'newline':
                            left_line += '</tspace2>'
                            right_line += '</tspace2>%s' % toappend[1]
                            left_text.append(left_line)
                            right_text.append(right_line)
                            left_line = ''
                            right_line = ''
                        else:
                            left_line += toappend[0]
                            right_line += toappend[1]
                elif tocheck[0:12] == '[SUBSECTION]':
                    subtitle = tocheck[12:]
                    poem = ''
                    subtitle_no += 1
                    marker = make_marker(markup_file, title, subtitle, poem, title_no, subtitle_no, poem_no, line_no, 5)
                    left_line += marker
                    left_line += '<tspace2>'
                    for char in subtitle:
                        toappend = process_char(char, dummy_dict)
                        if toappend[0] == 'pass':
                            pass
                        elif toappend[0] == 'newline':
                            left_line += '</tspace2>'
                            right_line += '</tspace2>%s' % toappend[1]
                            left_text.append(left_line)
                            right_text.append(right_line)
                            left_line = ''
                            right_line = ''
                        else:
                            left_line += toappend[0]
                            right_line += toappend[1]
                elif tocheck[0:6] == '[POEM]':
                    poem = tocheck[6:]
                    poem_no += 1
                    line_no = 0
                    marker = make_marker(markup_file, title, subtitle, poem, title_no, subtitle_no, poem_no, line_no, 6)
                    left_line += marker
                    left_line += '<tspace2>'
                    for char in poem:
                        toappend = process_char(char, dummy_dict)
                        if toappend[0] == 'pass':
                            pass
                        elif toappend[0] == 'newline':
                            left_line += '</tspace2>'
                            right_line += '</tspace2>%s' % toappend[1]
                            left_text.append(left_line)
                            right_text.append(right_line)
                            left_line = ''
                            right_line = ''
                        else:
                            left_line += toappend[0]
                            right_line += toappend[1]
                else:
                    line_no += 1
                    marker = make_marker(markup_file, title, subtitle, poem, title_no, subtitle_no, poem_no, line_no, 7)
                    left_line += marker
                    left_line += '<tspace2>'
                    for char in tocheck:
                        toappend = process_char(char, dummy_dict)
                        if toappend[0] == 'pass':
                            pass
                        elif toappend[0] == 'newline':
                            left_line += '</tspace2>'
                            right_line += '</tspace2>%s' % toappend[1]
                            left_text.append(left_line)
                            right_text.append(right_line)
                            left_line = ''
                            right_line = ''
                        else:
                            left_line += toappend[0]
                            right_line += toappend[1]

        item_count = 0
        while item_count < len(left_text):
            markup_file.write('%s' % left_text[item_count])
            markup_file.write('%s' % right_text[item_count])
            item_count += 1
        markup_file.write('</p>')

def kernmarkup(poem_file, dummy_dict, dummy_initgroups, schuessler_dict, text_type):
    try:
        #read in arguments
        #read in input file
        #all HTML code adapted from examples from w3 school's tutorials
        input_file_path = get_inputfilepath(text_type, poem_file)
        markup_file_path = get_markupfilepath(text_type, poem_file)
        markup_file = open(markup_file_path, 'w')
        
        write_header(markup_file, text_type, 2)
        write_body(input_file_path, markup_file, poem_file, dummy_dict, text_type)
        
        #add closing HTML tags
        markup_file.write('</p>\n')
        markup_file.write('</twrap>\n')
        markup_file.write('</body>\n')
        markup_file.write('</html>')

        print '%s marked up' % poem_file
        

    except IOError:
        sys.stderr.write("ERROR: Cannot read inputfile.\n")
        sys.exit(1)
        
def handle_rightfurigana(right_char, char, ruby_count, schuessler_dict):
    left_write = ''
    while ruby_count > 0:
        left_write += '<ruby>'
        ruby_count -= 1
    left_write += '<rb>%s</rb>' % right_char.encode('utf-8')
    for entry in schuessler_dict[char]:
        if isinstance(entry, list):
            for subentry in entry:
                left_write += '<rt>%s</rt></ruby>' % subentry.encode('utf-8')
        else:
            left_write += '<rt>%s</rt></ruby>' % entry.encode('utf-8')
    return left_write
    '''
