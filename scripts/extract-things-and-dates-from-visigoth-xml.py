#!/usr/bin/env python3

import sys
files = sys.argv[1:]

import xml.etree.ElementTree as ET
import os.path
import re
import gzip
import csv
import time

import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from visigoth.findthings import findthings # XXX what did I screw up here?
from visigoth.dateparse import dateparse # XXX what did I screw up here?

def process_one_file(file):

    if not os.path.isfile(file):
        print("Skipping", file, "because it does not exist.")
        return

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

    print("page loaded, elapsed =", time.time() - t0)

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

    print("hyphen unsplit, elapsed =", time.time() - t0)

    # poor man's sentence split (ought to use that dict)

    dot_dict = {}
    f = open(os.environ.get('VISIGOTH_DATA', '.') + '/linux.words.centos7.dotend.edited', 'r')
    for line in f:
       dot_dict[line.rstrip()] = 1
    f.close()

    newpages = []
    for page in pages:
        newpars = []
        for par in page:
            s = par[0] # we know there is exactly one

            # one thing this doesn't catch is ).
            candidates = re.findall('\w+\.[\)\'\"]?\.? {1,5}[A-Z]\w*', s)

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

    print("sentence split, elapsed =", time.time() - t0)

    pagecount = 0
    people = {}
    decile = '0'
    decile_people = {}

    people_date = {}

    def insert_person(person, decile):
        people[person] = people.get(person,0) + 1
        if decile_people.get(decile) is None:
            decile_people[decile] = {}
        decile_people[decile][person] = decile_people[decile].get(person,0) + 1

    def insert_person_date(person, date):
        if people_date.get(date) is None:
            people_date[date] = {}
        people_date[date][person] = people_date[date].get(person,0) + 1

    total_tft = 0
    total_tfd = 0
    total_sentences = 0

    for page in pages:
        pagecount += 1
        decile = str(int(pagecount / 10))
        #print("Page number", pagecount, "decile", decile)

        for par in page:
            for sentence in par:
                total_sentences += 1
                tft = time.time()
                found_things = ft.find_things(sentence)
                total_tft += time.time() - tft
                for t in found_things:
                    insert_person(t, decile)
                tfd = time.time()
                found_dates = dp.extract_dates(sentence)
                total_tfd += time.time() - tfd
                # probably bad to multi-insert, so let's use the date only if there is exactly one
                if len(found_dates) == 1:
                    d = found_dates[0]
                    for t in found_things:
                        insert_person_date(t, d)

    print(pagecount, "pages and", total_sentences, "sentences,", total_tft, "total found_things and", total_tfd, "total find_dates")

    print("dates and things extracted, elapsed =", time.time() - t0)

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

    print("deciles accumulated, elapsed =", time.time() - t0)

    outfile = file.replace('.xml', '.things.csv')
    outfile = outfile.replace('.0.', '.')
    if outfile == file:
        raise NameError('could not form the name of the outfile')

    o = open(outfile, "w", encoding="utf-8")

    ia_id = os.path.basename(outfile).replace('_visigoth.things.csv', '')

    print('person', 'score', 'breadth', 'depth', 'ia_id', file=o, sep='\t')

    sorted_list = ((k, scores[k]) for k in sorted(scores, key=scores.get, reverse=True))

    for k, v in sorted_list:
        print(k, v, '\t'.join(str(d) for d in details[k]), ia_id, file=o, sep='\t')
    o.close()

    # now output the thing-date table

    outfile = file.replace('.xml', '.thing-date.csv')
    outfile = outfile.replace('.0.', '.')
    if outfile == file:
        raise NameError('could not form the name of the outfile')

    o = open(outfile, "w", encoding="utf-8")

    print('year', 'thing', 'score', file=o, sep='\t')

    # XXX this doesn't sort on the scores, ah well.
    for d in sorted(people_date):
        sorted_things = ((t, people_date[d][t]) for t in sorted(people_date[d], key=people_date[d].get, reverse=True))
        for t, tv in sorted_things:
            print(d, t, people_date[d][t], file=o, sep='\t')
    o.close()

t0 = time.time()

ft = findthings()
dp = dateparse()

print("Created ft and dp objects, elapsed =", time.time() - t0)

for file in files:
    process_one_file(file)
    print("File", file, "finished, elapsed =", time.time() - t0)
