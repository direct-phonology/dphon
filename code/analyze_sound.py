#!/usr/bin/python
# -*- coding: UTF-8-*-
import sys
import re
import json
import file_handling

# analyze_sound.py
#
# This program contains the methods needed for phonological analysis of Chinese characters.

__author__="John O'Leary <jo.10@princeton.edu>"
__date__ ="Last Updated: Dec 28, 2018"

def get_info(file_type):
    #file_type: 1 = sound_table.txt
    #           2 = baxter.txt -> not written yet
    #           3 = hunter_schuessler.txt
    file_path = file_handling.get_datatable(file_type)
    print file_path
    data = file_handling.open_file(file_path, '\n')
    if file_type == 1:
        get_dummies(data)
    elif file_type == 2:
        get_bsinfo(data)
    else:
        get_schuessler(data)

def get_dummies(data):
    info = []
    initgroup_count = 0
    initgroup_dict = {}
    dummy_dict = {}
    dummy_list = []
    for line in data:
        chunks = re.split(r'\t', line)
        if len(chunks[0]) > 1:
            initial = initgroup_count
            initgroup_dict[initgroup_count] = chunks[0]
            initgroup_count += 1
        rhyme = chunks[1]
        dummy = chunks[2][0]
        for char in chunks[2]:
            match = 0
            if char != '\r' and char != '-'.decode('utf-8'):
                for unit in dummy_list:
                    if char == unit[0]:
                        match = 1
                        dummy_match = 0
                        for group in unit[1:]:
                            if group[-1] == dummy:
                                dummy_match = 1
                        if dummy_match == 0:
                            unit.append([initial, rhyme, dummy])
                if match == 0:
                    dummy_list.append([char, [initial, rhyme, dummy]])
        for unit in dummy_list:
            dummy_dict[unit[0]] = unit[1:]
    json_dump('dummy_dict', dummy_dict)
    json_dump('dummy_initgroup_dict', initgroup_dict)

def get_schuessler(data):
    line_count = 0
    group_number = 0
    reconstructions = []
    dict = {}
    while line_count < len(data):
        reading_list = []
        char = data[line_count][0]
        match = 0
        
        #mark which character is being analyzed in first position of list
        reading_list.append(char)
        readings = data[line_count][5:-3].split('$')
    
        #connect all readings to character
        for reading in readings:
            reading_list.append(reading)
            
        #check to see if character appears elsewhere in database with other set of readings, if so, append these readings to that list, otherwise append new list as standalone
        for entry in reconstructions:
            if entry[0] == reading_list[0]:
                entry.append(reading_list[1:])
                match = 1
        if match == 0:
            reconstructions.append(reading_list)
            
        #sys.stdout.write('\rReading Hunter file: %s/%s done.' % (line_count, len(lines)-1))
        #sys.stdout.flush()
        line_count += 1
        dict_printstatus(1, line_count, len(data))

    #populate dictionary with reconstructions for easy retrieval
    for reconstruction in reconstructions:
        dict[reconstruction[0]] = reconstruction[1:]

    json_dump('schuessler_dict', dict)

def load_dict(file_path):
    with open(file_path, "r") as f:
        data = f.read()
    dict = json.loads(data)
    return dict

def load_dummydict():
    dummy_dict = load_dict('../data/json/dummy_dict.json')
    return dummy_dict

def load_bsdict():
    bsdict = load_dict('../data/json/bs_dict.json')
    return bs_dict

def load_schuesslerdict():
    schuessler_dict = load_dict('../data/json/schuessler_dict.json')
    return schuessler_dict

def load_dummyinit():
    dummyinit_dict = load_dict('../data/json/dummy_initgroup_dict.json')
    return dummyinit_dict

def json_dump(file_name, file):
    with open('../data/json/%s.json' % file_name, 'w') as write_file:
        json.dump(file, write_file)

def dict_printstatus(dict_type, line_count, lines_len):
    if dict_type == 1:
        sys.stdout.write('\rReading Schuessler file: %s/%s done.' % (line_count, lines_len-1))
    elif dict_type == 2:
        sys.stdout.write('\rReading Baxter file: %s/%s done.' % (line_count, lines_len-1))
    sys.stdout.flush()

'''
def clean_bspinyin(line):
    if line[0] == '【'.decode('utf-8'):
        pron_array = []
        prons = re.split(r'◎'.decode('utf-8'), line[1:])
        for pron in prons:
            pron_array.append(pron[1:-1])
        pinyin = pron_array
    else:
        pinyin = line
    return pinyin

def get_bsinfo(data):
    medieval_pron = {}
    reconstructions = []
    file = open('test.txt', "w")
    
    lines = data
    line_count = 1
    
    while line_count < len(lines):
        reading_list = []
        match = 0
        items = lines[line_count].split()
        char = items[1]
        pron = items[3]
        #pinyin = clean_bspinyin(lines[line_count][15])
        
        reading_list.append(char)
        reading_list.append(pron)
        
        for entry in reconstructions:
            if entry[0] == reading_list[0]:
                entry.append(reading_list[1:][0])
                match = 1
        if match == 0:
            reconstructions.append(reading_list)
        line_count += 1
        dict_printstatus(2, line_count-1, len(data))

for reconstruction in reconstructions:
    medieval_pron[reconstruction[0]] = reconstruction[1:]
    
    json_dump('bs_dict', medieval_pron)

'''
