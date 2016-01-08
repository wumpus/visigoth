#!/usr/bin/env python3

# ./query-sentence-shelf.py 'Pope Gregory XIII' 1872

import sys
import os
import shelve
import re

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from visigoth.redirs import redirs # XXX what did I screw up here?

thing = sys.argv[1]
if len(sys.argv) > 2:
    year = sys.argv[2]
else:
    year = None

redir = redirs()
years = shelve.open(os.environ.get('VISIGOTH_DATA','')+'/year_shelf.eq.4', flag='r')
sentence = shelve.open(os.environ.get('VISIGOTH_DATA','')+'/sentence_shelf.eq.4', flag='r')

print("getting canon")
canon = redir.forward(thing)
print("got canon")

if year is None:
    print("No year specified. Checking years for you.")
    y = years.get(canon)
    print("got years")
    if not y:
        print(canon, "is not in the years shelf.")
    else:
        # sort dict by value
        sorted_list = ((k, y[k]) for k in sorted(y, key=y.get, reverse=True))
        k, v = list(sorted_list)[0]
        print("Most popular year for", canon, "is", k)
        k, v = list(sorted_list)[1]
        print("Second most popular year for", canon, "is", k)
    sys.exit(0)

key = canon + " " + year

sentences = sentence.get(key)

if sentences is None:
    print("Did not find any sentences for", key)
    sys.exit(0)

for s in sentences:
    # ia_id, s, rank, title, leaf
    for k in s:
        if k == 's':
            # boldface canon if there is no <b> XXX
            if '<b>' not in s['s']:
                s['s'] = re.sub(r'('+canon+')', r'<b>\1</b>', s['s'], flags=re.I)
        print(k, ":", s[k])
    print("-------------------")
