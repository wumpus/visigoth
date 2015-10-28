#!/usr/bin/env python3

import sys
file = sys.argv[1] # just one file processed

import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import xml.etree.ElementTree as ET
import re

from visigoth.dateparse import dateparse # XXX what did I screw up here?

stage_string = 'visigoth-me-harder-extract'
version_string = '0.0' # should also include a git id
pipeline_stats = {}

tree = ET.parse(file)
root = tree.getroot()

# grab the visigoth stuff off the top and save it for later
visigoth = root.find('visigoth')

# eventually I'm going to switch page -> chapter in the middle of the pipeline, but not yet

ipages = root.findall('page')

pages = []
for page in ipages:
    pars = []
    for par in page.iter('par'):
        if par.text:
            lines = par.text.split('\n')
            pars.append(lines)
    pages.append(pars) # this may be empty

# poor man's hyphen unsplit (don't bother with a dict, just join up -\n)

pipeline_stats['paragraphs'] = 0
pipeline_stats['pages'] = 0
pipeline_stats['upper split'] = 0
pipeline_stats['upper split veto'] = 0
pipeline_stats['upper split fail'] = 0
pipeline_stats['upper split replace fail'] = 0

newpages = []
for page in pages:
    newpars = []
    for par in page:
        string = '\n'.join(lines for lines in par)
        string = string.replace('-\n', '')
        string = string.replace('\n', ' ')
        # TODO clean up some leftovers related to italics: </i>\s*</i> and ... (orig.py)
        newpars.append([string]) # make it a list
        pipeline_stats['paragraphs'] += 1
    newpages.append(newpars)
    pipeline_stats['pages'] += 1

pages = newpages

# poor man's sentence split (ought to use that dict)

dot_dict = {}
f = open(os.path.expanduser('~/linux.words.centos7.dotend.edited'), 'r')
for line in f:
   dot_dict[line.rstrip()] = 1
f.close()

newpages = []
for page in pages:
    newpars = []
    for par in page:
        s = par[0] # we know there is exactly one

        # one thing this doesn't catch is ).
        # also fails for next sentence starting with italics
        candidates = re.findall('\w+\.[\)\'\"]? {1,5}[A-Z]\w*', s)

        for c in candidates:
            left, right = c.split()
            #print("Trying a candidate, left and right are", left, right)
            if dot_dict.get(left) is None:
                pipeline_stats['upper split'] += 1
                new = re.sub(r'\.([\)\'\"]?) {1,5}', r'.\1\n', c) # can match multiple times 
                if new == c:
                    pipeline_stats['upper split fail'] += 1
                olds = s
                s = s.replace(c, new) # can match multiple times 
                if s == olds:
                    # this can happen because a replacement happens twice, i.e. a paragraph has duplicate left,right XXX
                    pipeline_stats['upper split replace fail'] += 1
            else:
                pipeline_stats['upper split veto'] += 1
        sentences = s.split('\n')
        newpars.append(sentences)
    newpages.append(newpars)

pages = newpages

# Actual payload

#import visigoth.dateparse
#dp = visigoth.dateparse()
#from visigoth.dateparse import dateparse

#dp = visigoth.dateparse()
dp = dateparse()

date_table = {}

for page in pages:

    for par in page:
        for sentence in par:
            dates = dp.extract_dates(sentence)
            if len(dates):
                print("Found dates of", dates, "in sentence <", sentence, ">")
                for date in dates:
                    date_table[date] = date_table.get(date,0) + 1

# to do a stable sort, sort by a secondary key first XXX
# and then by the primary
sorted_list = ((k, date_table[k]) for k in sorted(date_table, key=date_table.get, reverse=True))

outfile = file.replace('.xml', '.dates.csv')
if outfile == file:
    raise NameError('could not form the name of the outfile')

o = open(outfile, "w", encoding="utf-8")

print('date', 'score', file=o, sep='\t')

for k, v in sorted_list:
    print(k, v, file=o, sep='\t')
