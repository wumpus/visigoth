#!/usr/bin/env python3

# ./build-year-pickle.py *.thing-date.csv

import sys
files = sys.argv[1:]

import csv
import pickle

years = {} # thing, year, count

# XXX use all the redirs and not just this one!
thingmap = { 'Gregory XIII': 'Pope Gregory XIII' }

def process_one_file(file):
    with open(file, 'r', newline='') as csvfile:
        r = csv.reader(csvfile, delimiter='\t')
        for row in r:
            year, thing, score = row
            if score == 'score':
                continue

            year = int(year)
            if year < 1000:
                continue
            if year >= 2000:
                continue
            if thingmap.get(thing) is not None:
                thing = thingmap[thing]

            thing = thing.lower()

            if years.get(thing) is None:
                years[thing] = {}

            years[thing][year] = years[thing].get(year,0) + int(score)

for file in files:
    process_one_file(file)

# I tried to compress the pickle by changing years[thing] into a list
# from a dict, but it remained the same size. Never mind.

f = open("years_pickle", 'wb') # utf-8?

pickle.dump(years, f)

