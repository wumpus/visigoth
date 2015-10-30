#!/usr/bin/env python3

# ./query-year-pickle.py 'Pope Gregory XIII'

import sys
thing = sys.argv[1]

import pickle

f = open('years_pickle', 'rb')

years = pickle.load(f)
f.close()

thing = thing.lower()
my_year = years.get(thing, {})

for y in sorted(my_year):
    print(thing, y, my_year[y])


