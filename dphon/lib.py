import json
from collections import defaultdict
from typing import List, Dict, Tuple
from os.path import basename, splitext


with open('data/dummy_dict.json', encoding='utf-8') as file:
    DUMMY_DICT = json.loads(file.read())


def phonetic_tokens(string: str) -> str:
    return (DUMMY_DICT[char][2] for char in string if char in DUMMY_DICT)


class Match(object):
    a_start: int
    a_end: int
    b_start: int
    b_end: int

    def __init__(self, a_start: int, a_end: int, b_start: int, b_end: int):
        self.a_start = a_start
        self.a_end = a_end
        self.b_start = b_start
        self.b_end = b_end

    def __str__(self) -> str:
        """Basic string reprentation of a match, showing its locations."""
        return 'A (%d - %d) :: B (%d - %d)' % (self.a_start, self.a_end,
                                               self.b_start, self.b_end)

    def has_graphic_variation(self, a:str, b:str) -> bool:
        """Whether a match contains an actual graphic variant of a character,
        ignoring punctuation and other differences."""
        # strip punctuation initially
        a_seq = ''.join([c for c in a[self.a_start:self.a_end + 1] if c.isalpha()])
        b_seq = ''.join([c for c in b[self.b_start:self.b_end + 1] if c.isalpha()])

        # if we find a character in b that we have an entry for but it's in a
        # different form, that's graphic variation
        for (i, char) in enumerate(a_seq):
            if char in DUMMY_DICT and char != b_seq[i]:
                return True

        return False

    def resolve(self, a: str, b: str):
        """Get the actual text of a match by mapping its locations to texts."""
        return '%s :: %s\t%s' % (
            a[self.a_start:self.a_end + 1],
            b[self.b_start:self.b_end + 1],
            str(self)
        )


class Comparator(object):
    a: str
    b: str
    a_name: str
    b_name: str
    a_linemap: List[int]
    b_linemap: List[int]
    matches: List[Match]

    def __init__(self, a: str, b: str, a_name: str, b_name: str):
        self.a = a
        self.b = b
        self.a_name = splitext(basename(a_name))[0]
        self.b_name = splitext(basename(b_name))[0]
        self.a_linemap = self.get_linemap(self.a)
        self.b_linemap = self.get_linemap(self.b)
        self.matches = []

    @staticmethod
    def get_linemap(text: str):
        m = []
        l = 1
        for char in text:
            m.append(l)
            if char == '\n':
                l += 1
        return m

    @staticmethod
    def create_numbered_text(text: str):
        output = ''
        # iterate through each line, with index
        for i, line in enumerate(text.splitlines(True)):
            # add the index + 1  and a tab as the first char of each line
            output += '%s\t%s' % (i + 1, line)

        return output
        # save the lines into a new string
        # write the string to a file

    @staticmethod
    def get_text_ngrams(text: str, n: int = 3) -> List[Dict]:
        """Returns all overlapping token ngrams for a text, with start and end
        pointers to locations in the original text."""
        if n < 1:
            raise ValueError('Value for `n` must be 1 or greater.')
        ngrams = []
        for pos, char in enumerate(text):
            if char.isalpha():
                # create a new ngram
                ngram = {'text': '', 'start': None, 'end': None}
                # add either the original character or a token if we have one
                if char in DUMMY_DICT:
                    char_to_append = DUMMY_DICT[char][2]
                else:
                    char_to_append = char
                ngram['text'] += char_to_append
                # set the start position
                if not ngram['start']:
                    ngram['start'] = pos
                # set the end position
                ngram['end'] = pos
                # add the character to n-1 previous ngrams and update their ends
                for x in range(-1, -n, -1):
                    try:
                        ngrams[x]['text'] += char_to_append
                        ngrams[x]['end'] = pos
                    except IndexError:
                        continue
                ngrams.append(ngram)
        # return all but the last n - 1 ngrams, as they are redundant
        return ngrams[:len(ngrams) - n + 1]

    def get_initial_matches(self, n: int = 3) -> List[Match]:
        """Gets a set of initial, overlapping matches between two texts that can
        be further refined using `reduce_matches`."""
        initial_matches = []
        # get ngrams for both texts
        a_ngrams = self.get_text_ngrams(self.a, n)
        b_ngrams = self.get_text_ngrams(self.b, n)
        # match every ngram in A against every ngram in B
        for a_ngram in a_ngrams:
            for b_ngram in b_ngrams:
                if a_ngram['text'] == b_ngram['text']:
                    initial_matches.append(Match(
                        a_start=a_ngram['start'],
                        a_end=a_ngram['end'],
                        b_start=b_ngram['start'],
                        b_end=b_ngram['end'],
                    ))
        return initial_matches

    @staticmethod
    def reduce_matches(matches: List[Match]) -> List[Match]:
        """Combines a list of overlapping matches to find the longest possible
        contiguous matches."""
        for i, match in enumerate(matches):
            # lookahead
            for candidate in matches[i+1:]:
                # ignore matches that are fully congruent
                if candidate.a_start == match.a_start and candidate.a_end == match.a_end:
                    continue
                # next we should find matches that are overlapping in A, if any
                if candidate.a_start < match.a_end and candidate.a_start > match.a_start:
                    # ignore matches pointing to somewhere else in B
                    if candidate.b_start >= match.b_end or candidate.b_start <= match.b_start:
                        continue
                    # ignore matches in B that are completely inside ours
                    if candidate.b_start > match.b_start and candidate.b_end < match.b_end:
                        continue
                    # if we overlap in both A and B, merge into our match
                    if candidate.b_start < match.b_end and candidate.b_start > match.b_start:
                        match.a_end = candidate.a_end
                        match.b_end = candidate.b_end
                        matches.remove(candidate)
                        continue
                # if we didn't find any overlapping, we're done
                break
        # some matches may still be completely subsumed by others
        for i, match in enumerate(matches):
            # lookahead to see if any matches fit inside this one
            for candidate in matches[i+1:]:
                # if so, remove
                if candidate.a_start >= match.a_start and candidate.a_end <= match.a_end and candidate.b_start >= match.b_start and candidate.b_end <= match.b_end:
                    matches.remove(candidate)
        # return final list
        return matches

    @staticmethod
    def group_matches(matches: List[Match]) -> Dict[range, List[range]]:
        """Groups a list of matches by position in a text, so that a single
        location in a can reference a list of locations in b."""
        grouped_matches = {}
        for match in matches:
            if range(match.a_start, match.a_end) not in grouped_matches:
                grouped_matches[range(match.a_start, match.a_end)] = []
            grouped_matches[range(match.a_start, match.a_end)].append(
                range(match.b_start, match.b_end))
        return grouped_matches

    def resolve_groups(self, matches: Dict[range, List[range]]) -> str:
        """Print grouped matches by mapping their locations to texts."""
        output = ''
        for a, bs in matches.items():
            output += '%s (%s: %d)\n' % (
                self.a[a.start:a.stop+1], self.a_name, self.a_linemap[a.start])
            for b in bs:
                output += '%s (%s: %d)\n' % (
                    self.b[b.start:b.stop+1], self.b_name, self.b_linemap[b.start])
            output += '\n'
        return output

    def get_matches(self, min_length: int = 3) -> List[Match]:
        """Matches the two texts stored in the comparator."""
        return self.reduce_matches(self.get_initial_matches(min_length))
