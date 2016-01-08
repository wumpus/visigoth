#!/usr/bin/env python3

# rm $VISIGOTH_DATA/sentence_shelf # or not, this script is incremental
# ./build-sentence-shelf.py *.thing-date-sentence.csv

# this script will double-count, so don't send in any books twice

import sys
import os
import csv
import shelve
from random import shuffle
from operator import itemgetter

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from visigoth.redirs import redirs # XXX what did I screw up here?

def randn(n, l):
    """                                                                                                                                                        
    trim list down to up to n randomly-chosen items.
    do not use if you have ranking information.
    """
    shuffle(l)
    return l[0:min(len(l), n)]

def process_one_file(file):

    if not os.path.isfile(file):
        print("Skipping", file, "because it does not exist.")
        return

    present = {}

    (ia_id, rest) = file.split(sep='_', maxsplit=1)
    print("Got ia_id of", ia_id,"from file", file)

    m = metadata.get(ia_id)
    if m is None:
        print("Could not find metadata for", file, "skipping")
        return
    rank = m.get('rank', 0)
    title = m.get('title', '{ no title }') # should not happen
    # fixups for issues I noticed
    title.replace('\n', ' ')
    title.replace('  ', ' ')

    print("processing", file,"rank", rank)

    with open(file, 'r', newline='') as csvfile:
        r = csv.reader(csvfile, delimiter='\t')
        for row in r:
            year, thing, ia_id, leaf, sent = row
            if year == 'date': # header line
                continue

            year = int(year)
            if year >= 2015: # unlikely to be accurate
                continue

            canon = redir.forward(thing)

            # bold thing in the sent
            if thing in sent:
                sent.replace(thing, "<b>"+thing+"</b>")
            elif thing.lower() in sent:
                sent.replace(thing.lower(), "<b>"+thing.lower()+"</b>")
            else:
                print("Failed to bold", thing, "in sentence", sent)
                # XXX this is seeing 'foo' when 'Foo' is in the sentence.

            # sentence needs a 2D key (thing, year) to reduce pickle cpu burn & i/o when serving
            key = canon + " " + str(year)

            # reduce rank if there's more than 1 sentence from this book
            myrank = rank
            p = present.get(key, 0)
            if p:
                myrank -= 2 * p
                print("rank reduced from", rank, "to", myrank, "because of dup sentences.")
            present[key] = p + 1

            s = sentence.get(key, [])
            s.append({ "ia_id": ia_id,
                       "s": sent,
                       "rank": myrank,
                       "title": title,
                       "leaf": leaf,
                   })

            if len(s) > 10:
                # to make the sort stable, first sort by ia_id
                s = sorted(s, key=lambda x: x.get('ia_id'))
                s = sorted(s, key=lambda x: x.get('rank'), reverse=True)

                s = s[0:10]

            # write back into the shelf
            sentence[key] = s

# create if does not exist
print("opening sentence shelf")
sentence = shelve.open(os.environ.get('VISIGOTH_DATA','')+'/sentence_shelf', flag='c')

# source of book rank, title
print("opening metadata shelf")
metadata = shelve.open(os.environ.get('VISIGOTH_DATA','')+'/book_metadata_shelf', flag='r')

# source of redir information
print("opening redir shelf")
redir = redirs()

count = 0

files = sys.argv[1:]
print("Reading", len(files), "files")

for file in files:
    process_one_file(file)
    count += 1
    if count % 10 == 0:
        print("processed", count, "files")

print("Beginning writeback")
sentence.close()

