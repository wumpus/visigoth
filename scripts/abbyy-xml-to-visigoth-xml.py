#!/usr/bin/env python3

from sys import argv
file = argv[1] # just one file processed

import re
import gzip

import xml.etree.ElementTree as ET

stage_string = 'abbyy-xml-to-visigoth-xml'
version_string = '1.0' # should also include a git id
abbyy_stats = { 'found italic hunk': 0,
                'moved punctuation outside italics': 0,
                'paragraphs': 0,
                'lines': 0,
                'pages': 0
}

# if the filename ends in .gz, assume it's a gzip file

input = file
if file[-3:] == '.gz':
    input = gzip.open(file, mode='rt', encoding='utf-8')
else:
    input = open(file, 'r', encoding='utf-8')

# If I use ET.parse(), a book with 10 megabytes of text has 2
# gigabytes of abbyy xml, almost all of which are the attributes of
# charParams, which I am ignoring. It takes 15 gigabytes of ram at
# peak. Attempting to ET.interparse() and deleting the charParams
# attributes didn't change much. The following code, which
# preprocesses th XML to regex out the <charParams> attributes, and
# then parses it, is twice as fast and peaks at 2.6 gigabytes.

raw = u''
for line in input:
    line = re.sub(r'\<charParams.*?\>', '<charParams>', line)
    raw += line

root = ET.fromstring(raw)

# there's probably a much more elegant way to express this
# this is the default namespace (always?)
# is the xsi: namespace ever used? not in the examples so far
# TODO: fetch <document> and get the default xmlns and use default:
#   (see 20.5.1.7) https://docs.python.org/3/library/xml.etree.elementtree.html

ns = '{http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml}'

# convert from raw ABBYY Finereader output to lines in paragraphs in pages

pages = []

# TODO preserve pagecount of <document>
# TODO examine <page resolution="">, see if it's always 400
# TODO panic if originalCoords != 'true' ?
# TODO: add notation for indented paragraphs
# TODO: mark centered things

for ipage in root: # I wonder why this doesn't get the <document> ? it so happens finereader outputs only <page> at this level
   pars = []
   for ipar in ipage.iter(ns + 'par'):
      lines = []
      for iline in ipar.iter(ns + 'line'):
         line = ''
         for ihunk in iline.iter(ns + 'formatting'):
            hunk = ''.join(ichar.text for ichar in ihunk.iter(ns + 'charParams'))
            if (ihunk.attrib.get('italic') == 'true'):
               abbyy_stats['found italic hunk'] += 1
               hunk = '<i>' + hunk + '</i>'
               # move trailing </i> inside of spaces and punctuation XXX does this work once? or does it match all?
               new = re.sub(r'([\'\"\.\,\ \-]+)\</i\>', r'</i>\1', hunk)
               if new != hunk:
                  abbyy_stats['moved punctuation outside italics'] += 1
                  hunk = new
            #add_words_to_dict(hunk)
            line += hunk
         line = line.rstrip() # ABBYY leaves trailing spaces
         lines.append(line)
      if len(lines) > 0:
          pars.append(lines) # do not append output paragraphs which appear to be empty
          abbyy_stats['paragraphs'] += 1
          abbyy_stats['lines'] += len(lines)
   pages.append(pars) # this may be empty
   abbyy_stats['pages'] += 1

# generate the top stuff: version info, stats

# now spit it out as xml
# XXX how should I represent lines? Abbyy is <line></line>, do I want to switch to <br /> ? or \n?
# Since I'm passing in <i> the xml lib is quoting it, I suppose that's OK

outfile = file.replace('.gz', '')
outfile = outfile.replace('_abbyy', '_visigoth.0.xml')

document = ET.Element('document')

visigoth = ET.SubElement(document, 'visigoth')
stage = ET.SubElement(visigoth, 'stage')
stage.text = stage_string
version = ET.SubElement(stage, 'version')
version.text = version_string
stats = ET.SubElement(stage, 'stats')
for s in abbyy_stats:
    name = s.replace(' ', '-')
    newstat = ET.SubElement(stats, 'stat', { 'name' : name, 'value' : str(abbyy_stats[s]) } )

# now output the actual document

for page in pages:
    outpage = ET.SubElement(document, 'page')
    for par in page:
        outpar = ET.SubElement(outpage, 'par')
        outpar.text = u"\n".join(par)

out = ET.ElementTree(document)
out.write(outfile, short_empty_elements=False)
