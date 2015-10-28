#!/usr/bin/env python3

from sys import argv
import re

file = argv[1] # just one file processed

import xml.etree.ElementTree as ET

stage_string = 'next-pipeline-stage'
version_string = '1.0' # should also include a git id
pipeline_stats = {}

outname = re.asdfadfasdf


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
      lines = par.text.split('\n')
      pars.append(lines)
   pages.append(pars) # this may be empty

# do some transformation

pipeline_stats['some stat'] = 42

# write it back out

# add the new stage to the top of the old tree
stage = ET.SubElement(visigoth, 'stage')
stage.text = stage_string
version = ET.SubElement(stage, 'version')
version.text = version_string
stats = ET.SubElement(stage, 'stats')
for s in pipeline_stats:
    name = s.replace(' ', '-')
    newstat = ET.SubElement(stats, 'stat', { 'name' : name, 'value' : str(pipeline_stats[s]) } )

# and attach that to the new document
document = ET.Element('document')
document.append(visigoth)

for page in pages:
    outpage = ET.SubElement(document, 'page')
    for par in page:
        outpar = ET.SubElement(outpage, 'par')
        outpar.text = u"\n".join(par)

out = ET.ElementTree(document)
out.write('foo.xml', short_empty_elements=False)
