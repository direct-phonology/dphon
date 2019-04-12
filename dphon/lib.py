import json

with open('data/dummy_dict.json') as file:
    DUMMY_DICT = json.loads(file.read())

class Character(object):
    original: str
    dummy: str
    position: int

    def __init__(self, original: str, position: int):
        self.original = original
        self.position = position
        if original.isalpha():
            if original in DUMMY_DICT:
                self.dummy = DUMMY_DICT[original][2]
            else:
                self.dummy = original

    def __str__(self):
        return 'char: %s (%s), %d' % (self.original, self.dummy, self.position)

    
class Sequence(object):
    text: int # which text is this in
    start: int # what position does it start
    length: int # how long is the string

    def __init__(self, text: int, start: int, length: int):
        self.text = text
        self.start = start
        self.length = length

class Match(object):
    source: Sequence
    dest: Sequence

    def __init__(self, source: Sequence, dest: Sequence):
        self.source = source
        self.dest = dest
        
    def resolve(self, textA, textB):
        return '%s (%d) :: %s (%d)' % (
            textA[self.source.start:self.source.start + self.source.length],
            self.source.start,
            textB[self.dest.start:self.dest.start + self.dest.length],
            self.dest.start
        )