import timeit
from uniseg.graphemecluster import grapheme_clusters
from grapheme import graphemes, length

# setup text & number of iterations to test
text = '''
九五曰：「飛龍在天，利見大人」。
何謂也？子曰：「同聲相應，同氣相求。
水流濕，火就燥，雲從龍，風從虎，聖人作而萬物覩。
本乎天者親上，本乎地者親下，則各從其類也。」
'''
kwargs = {'globals': globals(), 'number': 100}

enum_time = timeit.timeit('for c in enumerate(text): pass', **kwargs)
grapheme_time = timeit.timeit('for c in graphemes(text): pass', **kwargs)
uniseg_time = timeit.timeit('for c in grapheme_clusters(text): pass', **kwargs)

print('------------------------------------')
print('avg of %d trials:' % kwargs['number'])
print('enumerate() iteration time: %fs' % enum_time)
print('graphemes() iteration time: %fs' % grapheme_time)
print('grapheme_clusters() iteration time: %fs' % uniseg_time)
