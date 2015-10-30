#!/usr/bin/env python3

import shelve
import os
import sys
ids = sys.argv[1:]

with shelve.open(os.environ.get('VISIGOTH_DATA','')+'/book_metadata_shelf', flag='r') as metadata:
    for ia_id in ids:
        print(ia_id, ':', metadata.get(ia_id, {}))
