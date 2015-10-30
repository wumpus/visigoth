#!/usr/bin/env python3

import shelve
import csv
import os

metadata = shelve.open(os.environ.get('VISIGOTH_DATA','')+'/book_metadata_shelf', flag='n', writeback=True)

with open(os.environ.get('VISIGOTH_DATA','')+'/titles.csv', 'r', newline='') as csvfile:
    r = csv.reader(csvfile, delimiter='\t')
    for row in r:
        ia_id, title = row
        metadata[ia_id] = { 'title': title }


