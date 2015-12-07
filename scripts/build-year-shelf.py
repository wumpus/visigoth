#!/usr/bin/env python3

# rm $VISIGOTH_DATA/years_pickle # or not, this script is incremental 
# ./build-year-shelf.py *.thing-date.csv

import sys
files = sys.argv[1:]

import csv
import shelve

import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from visigoth.redirs import redirs # XXX what did I screw up here?

def process_one_file(file):

    if not os.path.isfile(file):
        print("Skipping", file, "because it does not exist.")
        return

    with open(file, 'r', newline='') as csvfile:
        r = csv.reader(csvfile, delimiter='\t')
        for row in r:
            year, thing, score = row

            # skip the first row
            if score == 'score':
                continue

            year = int(year)
            if year >= 2015: # probably wrong, if it's this big
                continue

            canon = redir.forward(thing)

            #if canon != thing:
            #    print("DEBUG:", thing, "forwarded to", canon)

            # because of shelf mutability issues, do a read-modify-write
            y = years.get(thing, {})
            y[year] = y.get(year,0) + int(score)
            years[thing] = y

redir = redirs()

# create if does not exist
years = shelve.open(os.environ.get('VISIGOTH_DATA','')+'/year_shelf', flag='c', writeback=True)

for file in files:
    process_one_file(file)

print("Beginning writeback")
years.close()
