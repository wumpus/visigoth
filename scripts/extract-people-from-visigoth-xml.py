#!/usr/bin/env python3

from sys import argv
file = argv[1] # just one file processed

import xml.etree.ElementTree as ET
import os.path
import re

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

# Find runs of words That Are All Capitalized r'\b(?:[A-Z][a-z]*\b\s*){1,}'
#  note that this disallows John Q. Public
#  this does handle "Darwin's Origin of the Species" properly - 2 entities
# what to do with first word in the sentence?
#  downcase if it's in the dictionary (but names are in the Linux dictionary :-()
#  make a list of words that commonly start sentences in this book?
#  Eh, ignore the issue for now
# dbpedia/persondata_name.name
# Once a person has been spotted once, the last word in their name becomes a reference

name_entities = {}
last_name_map = {}
f = open(os.path.expanduser('~/persondata_name.final'), 'r')
for line in f:
   name_entities[line.rstrip()] = 1
f.close()
count = 0
people = {}
decile = '0'
decile_people = {}

def insert_person(person):
    people[person] = people.get(person,0) + 1
    decile_people[decile][person] = decile_people[decile].get(person,0) + 1

for page in pages:
    count += 1
    decile = str(int(count / 10))
    #print("Page number", count, "decile", decile)

    # is this how you do this?
    if decile_people.get(decile,None) is None:
        decile_people[decile] = {}

    for par in page:
        for sentence in par:
            candidates = re.findall(r'\b(?:[A-Z][a-z]*\b\.?\s*){1,}', sentence)
            for c in candidates:

                # poor man's attempt to throw away titles
                c = re.sub(r'\A(?:(?:Mr|Ms|Mrs|Dr|Prof|Rev)\.|Miss|Professor|Reverend|Sir)\s+','', c)

                # drop a trailing ., helps at the end of sentences.
                c = re.sub(r'\.\Z','', c)

                c = c.rstrip()
                if last_name_map.get(c) is not None:
                    # allow the most recent last name to get priority, i.e. George Abraham means next Abraham becomes George Abraham
                    #print(" Found entity", c, "=>", last_name_map[c], "in sentence", sentence)
                    insert_person(last_name_map[c])
                elif name_entities.get(c) is not None:
                    #print(" Found entity '", c, "' in sentence", sentence)
                    insert_person(c)
                    # is it multi-word? then map the last word to this name
                    if ' ' in c:
                        parts = c.rsplit(' ', maxsplit=1)
                        last = parts[1]
                        #print("Checking to see if last", last, "is in my dict")
                        #if last_name_map.get(last, c) != c:
                            #print("Got a conflicting last name match, previous", last_name_map[last], "new", c)
                        # use the most recent last name, i.e. a book at Darwin and sons will have several Foo Darwins
                        last_name_map[last] = c

# accumulate references per page and per book.
# accumulate references per 10-page segment?
# compute a score 0-1
#  half for total # of references -- cap at 100?
#  half for what fraction of 10-page segments have that reference

scores = {}
details = {}
decile_count = len(decile_people)

for person in people:
    count = 0
    for decile in decile_people:
        if person in decile_people[decile]:
            count += 1
    breadth = count / decile_count
    breadth = int(breadth*1000)/1000
    depth = min(people[person],200)/200.
    depth= int(depth*1000)/1000
    score = 0.5*breadth + 0.5*depth
    score = int(score*1000)/1000
    scores[person] = score
    details[person] = [breadth, depth]

# to do a stable sort, sort by a secondary key first XXX
# and then by the primary
sorted_list = ((k, scores[k]) for k in sorted(scores, key=scores.get, reverse=True))

outfile = file.replace('.xml', '.people.csv')
outfile = outfile.replace('.0.', '.')
if outfile == file:
    raise NameError('could not form the name of the outfile')

o = open(outfile, "w", encoding="utf-8")

ia_id = os.path.basename(outfile).replace('_visigoth.people', '')

# XXX I'm printing the same filename over and over? really?
print('person', 'score', 'breadth', 'depth', 'ia_id', file=o, sep='\t')

for k, v in sorted_list:
    print(k, v, '\t'.join(str(d) for d in details[k]), ia_id, file=o, sep='\t')
