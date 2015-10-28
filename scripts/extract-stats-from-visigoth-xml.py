#!/usr/bin/env python3

# incrementally parse visigoth xml

from sys import argv
file = argv[1] # just one file processed

import xml.etree.ElementTree as ET

out = []
version = ''

for event, elem in ET.iterparse(file):
    if elem.tag == 'stage':
        print('# Stage {0} version {1}'.format(elem.text, version))
        out = sorted(out)
        for l in out:
            print(u'.'.join((elem.text, l)))
        out = []
    elif elem.tag == 'version':
        version = elem.text
    elif elem.tag == 'stat':
        out.append('{name} = {value}'.format(**elem.attrib))
    elif elem.tag == 'visigoth':
        break


