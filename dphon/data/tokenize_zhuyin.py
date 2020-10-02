#!/usr/bin/env python3
"""Script to convert utf-8 plaintext into Zhuyin phonetic tokens."""

import json
import sys

if __name__ == '__main__':
    with open(sys.argv[1]) as dict_file:
        zhuyin_dict = json.loads(dict_file.read())

    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")

    for char in sys.stdin.read():
        sys.stdout.write(zhuyin_dict.get(char, char))
