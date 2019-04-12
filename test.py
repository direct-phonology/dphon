from dphon.util import build_character_array, clean, match

with open('ddj.txt') as file:
    ddj = file.read()

with open('gd_laoziA.txt') as file2:
    gd = file2.read()

ddj_chars = build_character_array(ddj)
gd_chars = build_character_array(gd)
ddj_cleaned = clean(ddj_chars)
gd_cleaned = clean(gd_chars)

matches = match(ddj_cleaned, gd_cleaned)

for match in matches:
    print('%s\n' % match.resolve(ddj, gd))