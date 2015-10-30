#!/usr/bin/env python3

# ./query-year-pickle.py 1872 'Pope Gregory XIII'

import sys
year = sys.argv[1]
thing = sys.argv[2]
year = int(year)
thing = thing.lower()

import pickle

f = open('sentences_pickle', 'rb')

years = pickle.load(f)
f.close()

sentences = years.get(thing, {}).get(year, {})

if len(sentences) == 0:
    foo = list(years.get(thing,{}).keys()) # XXX slow
    print("example years for this thing", foo[0:10])

for s in sentences:
    ia_id, leaf, sentence = s
    print(ia_id, leaf, sentence)



