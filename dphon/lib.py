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
    start: int
    end: int

    def __init__(self, start: int, end: int):
        self.start = start
        self.end = end

class Match(object):
    source: Sequence
    dest: Sequence

    def __init__(self, source: Sequence, dest: Sequence):
        self.source = source
        self.dest = dest
        
    def resolve(self, textA, textB):
        return '%s (%d) :: %s (%d)' % (
            textA[self.source.start:self.source.end],
            self.source.start,
            textB[self.dest.start:self.dest.end],
            self.dest.start
        )