from dphon.tokenizer import Token
from dphon.matcher import LevenshteinPhoneticMatcher
from dphon.loader import Document

direct = LevenshteinPhoneticMatcher("data/dummy_dict.json", threshold=0.75)

text_a = '與大子入，舍於孔氏之外圃。昏，二人蒙衣而乘，寺人羅御，如孔氏。孔氏之老欒寧問之，稱姻妾以告，#src:Z'
doc_a = Document('a', text_a)
doc_a.title = 'a'
seed_a = Token('a:1', doc_a, 0, 3, '與大子入')

text_b = '與太子入，舍孔氏之外圃。昏，二人蒙衣而乘，宦者羅御，如孔氏。孔氏之老欒甯問之，稱姻妾以告。遂入，適伯姬氏。'
doc_b = Document('b', text_b)
doc_b.title = 'b'
seed_b = Token('b:1', doc_b, 0, 3, '與大子入')

match = direct.extend(seed_a, seed_b)
print("%.02f" % match.meta["score"])
print(match)