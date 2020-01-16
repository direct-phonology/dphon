from dphon.lib import Comparator, phonetic_tokens

"""This is a small script for visualizing problems when debugging functions that
operate on matches. You can paste in text that is known to reproduce a bug for
text1 and text2, run the script, remove some text from each, and repeat until
you have a minimal reproduction test case. Then use the output to console to
visualize what step of the process is causing the problem."""

text1 = '''
中士聞道，若存若亡；下士聞道。
'''
text2 = '''
中士聞道，若存若亡。下士聞道。
'''
c = Comparator(a=text1, b=text2, a_name='a', b_name='b')
initial = c.get_initial_matches()
matches = c.get_matches()
groups = c.group_matches(matches)

print('\n-----------------------------\n')
print('INPUT\n')

print(''.join((str(i + 1) + ' ') if i < 9 else (str(i + 1)) for (i, _) in enumerate(text2)))
print(text1.strip())
print(text2.strip())

print('\n-----------------------------\n')
print('PHONETIC TOKENS\n')

print(''.join((str(i + 1) + ' ') if i < 9 else (str(i + 1)) for (i, _) in enumerate(phonetic_tokens(text2))))
print(''.join([t for t in phonetic_tokens(text1)]))
print(''.join([t for t in phonetic_tokens(text2)]))

print('\n-----------------------------\n')
print('INITIAL MATCHES\n')

for match in initial:
    print('%s\t\t%s' % (match, match.resolve(text1, text2)))

print('\n-----------------------------\n')
print('REDUCED MATCHES\n')

for match in matches:
    print('%s\t\t%s' % (match, match.resolve(text1, text2)))

print('\n-----------------------------\n')
print('OUTPUT\n')

print(c.resolve_groups(groups))