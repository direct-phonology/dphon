#!/usr/bin/python
# -*- coding: UTF-8-*-
import sys
import re
import json

# filehandling.py

__author__="John O'Leary <jo.10@princeton.edu>"
__date__ ="Last Updated: Dec 7, 2018"

def open_file(file_path, parse_criteria):
    file = open(file_path, "r")
    text= file.read().decode('utf-8')
    lines = re.split(r'%s+' % parse_criteria, text)
    return lines

def get_markupfilepath(text_type, poem_file):
    if text_type == '1':
        file_path = '../output/markup/Chuci/CTXT/%s_markup.html' % poem_file[:-4]
    elif text_type == '2':
        file_path = '../output/markup/Chuci/scripta_sinica/%s_markup.html' % poem_file[:-4]
    elif text_type == '3':
        file_path = '../output/markup/Chuci/CHANT/%s_markup.html' % poem_file[:-4]
    elif text_type == '4':
        file_path = '../output/markup/Chuci/chuci_parts/%s_markup.html' % poem_file[:-4]
    elif text_type == '5':
        file_path = '../output/markup/Shijing/CTXT/%s_markup.html' % poem_file[:-4]
    elif text_type == '6':
        file_path = '../output/markup/Shijing/CHANT/%s_markup.html' % poem_file[:-4]
    elif text_type == '7':
        file_path = '../output/markup/kern_markup/%s_markup.html' % poem_file[:-4]
    else:
        file_path = '../output/markup/misc_markup/%s_markup.html' % poem_file[:-4]
    return file_path

def get_inputfilepath(text_type, poem_file):
    if text_type == '1':
        file_path = '../data/raw_text/Chuci/CTXT/%s' % poem_file
    elif text_type == '2':
        file_path = '../data/raw_text/Chuci/scripta_sinica/%s' % poem_file
    elif text_type == '3':
        file_path = '../data/raw_text/Chuci/CHANT/%s' % poem_file
    elif text_type == '4':
        file_path = '../data/raw_text/Chuci/CHANT/chuci_parts/%s' % poem_file
    elif text_type == '5':
        file_path = '../data/raw_text/Shijing/CTXT/%s' % poem_file
    elif text_type == '6':
        file_path = '../data/raw_text/Shijing/CHANT/%s' % poem_file
    elif text_type == '7':
        file_path = '../data/raw_text/kernfiles/%s' % poem_file
    else:
        file_path = '../data/test/%s' % poem_file
    return file_path

def get_cssfilepath(text_type):
    if text_type == 1:
        file_path = 'markup_style.css'
    else:
        file_path = 'nonsplit_markup_style.css'
    return file_path

def get_datatable(table_type):
    if table_type == 1:
        file_path = '../data/tables/sound_table.txt'
    elif table_type == 2:
        file_path = '../data/tables/baxter.txt'
    else:
        file_path = file_path = '../data/tables/hunter_schuessler.txt'
    return file_path

def handle_cssdepth(text_type, css_file):
    depth_two = ['7']
    depth_three = ['1', '2', '3', '5', '6']
    depth_four = ['4']

    if text_type in depth_two:
        css_depth = '<link rel="stylesheet" type="text/css" href="../../../data/css/%s">' % css_file
    elif text_type in depth_three:
        css_depth = '<link rel="stylesheet" type="text/css" href="../../../../data/css/%s">' % css_file
    elif text_type in depth_four:
        css_depth = '<link rel="stylesheet" type="text/css" href="../../../../../data/css/%s">' % css_file
    else:
        css_depth = '<link rel="stylesheet" type="text/css" href="../../../data/css/%s">' % css_file
    return css_depth
