#!/usr/bin/env python3

# ./build-sentence-pickle.py *.thing-date-sentence.csv

import sys
files = sys.argv[1:]

import csv
import pickle
from random import shuffle

years = {} # thing, year, [sentences] (random selection of up to 20)

thingmap = { 'Gregory XIII': 'Pope Gregory XIII' }

keepallthings = { 'Pope Gregory XIII': 1, 'Harriet Tubman': 1 }

def randn(n, l):
    """                                                                                                                                                        
    trim list down to up to n randomly-chosen items
    """
    shuffle(l)
    return l[0:min(len(l), n)]

def process_one_file(file):
    local_count = {}

    with open(file, 'r', newline='') as csvfile:
        r = csv.reader(csvfile, delimiter='\t')
        for row in r:
            year, thing, ia_id, leaf, sentence = row
            if year == 'date': # header line
                continue

            year = int(year)
            # trim year to something reasonable
            if year < 1000:
                continue
            if year >= 2000:
                continue

            if thingmap.get(thing) is not None:
                thing = thingmap[thing]

            thing = thing.lower()
            if years.get(thing) is None:
                years[thing] = {}
            if years[thing].get(year) is None:
                years[thing][year] = []
            if local_count.get(thing) is None:
                local_count[thing] = {}
            local_count[thing][year] = local_count[thing].get(year,0) + 1

            if local_count[thing][year] < 5 or keepallthings.get(thing) is not None:
                years[thing][year].append([ia_id, leaf, sentence])

            count = len(years[thing][year])
            if count > 100 and keepallthings.get(thing) is None:
                print("thing", thing, "year", year, "count is", count, "trimming.")
                years[thing][year] = randn(30, years[thing][year])

def add_titles():
    with open('titles/titles.csv', 'r', newline='') as csvfile:
        years['titles of the books'] = {}
        r = csv.reader(csvfile, delimiter='\t')
        for row in r:
            ia_id, title = row
            years['titles of the books'][ia_id] = title
            print("title of", ia_id,"is", title)

print("Reading", len(files), "files")

count = 0

for file in files:
    process_one_file(file)
    count += 1
    if count % 1 == 0:
        print("processed", count, "files")

print("Finished reading input; trimming and shuffling output")

for thing in years:
    for year in years[thing]:
        years[thing][year] = randn(10, years[thing][year])

add_titles()

print("pickling")

f = open("sentences_pickle", 'wb') # utf-8?                                       
pickle.dump(years, f)

