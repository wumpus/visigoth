#!/usr/bin/env python3

import re
import sys

# All captures are currently in building_blocks. That probably has to change to fix the following limitations:
# XXX currently only capturing the year.
# XXX currently only capturing only one year, not decades and centuries
# XXX currently not capturing AD vs BC
building_blocks = [
    { 'name': 'CALENDAR', 'pat': '(?:A\\.D\\.|AD|C\\.E\\.|CE|B\\.C\\.|BC|B\\.C\\.E\\.|BCE)' },
    { 'name': '1to3DIGIT', 'pat': '(\\d{1,3})' },
    { 'name': '1to4DIGIT', 'pat': '([1-9]\\d{0,3})' },
    { 'name': '4DIGIT', 'pat': '([1-9]\\d{3})' },
    { 'name': 'MTH', 'pat': '(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?' },
    { 'name': 'MONTH', 'pat': '(?:January|February|March|April|May|June|July|August|September|October|November|December)' },
    { 'name': 'DAY', 'pat': '\\d{1,2}' },
    { 'name': 'DECADE', 'pat': '([1-9]\d\d0)' },
    { 'name': 'MILLENIUM', 'pat': '([1-9]\d00)' } # XXX add in "sixteenth century", "16th century"
]

strong_dates = [
    { 'name': '4DIGIT CALENDAR', 'test': '1601 AD' },
    { 'name': '1to3DIGIT CALENDAR', 'test': '667 BC', 'answer': '667' }, # XXX not capturing AD vs BC
    { 'name': '4DIGIT-1to4DIGIT CALENDAR', 'test': '1601-2 AD' }, # XXX not capturing ranges correctly
    { 'name': '1to3DIGIT-1to4DIGIT CALENDAR', 'test': '542-1099 BCE', 'answer': '542' }, # XXX not capturing ranges correctly
    { 'name': 'CALENDAR 4DIGIT', 'test': 'CE 1601' },
    { 'name': 'CALENDAR 1to3DIGIT', 'test': 'A.D. 542', 'answer': '542' }, # Negative: UTP is aminated to CTP by CTP synthase [UTPiammonia ligase (ADP-forming), B.C. 6.3.4.2]
    { 'name': 'CALENDAR 4DIGIT-1to4DIGIT', 'test': 'AD 1601-52' },
    { 'name': 'CALENDAR 1to3DIGIT-1to4DIGIT', 'test': 'BCE 22-55', 'answer': '22' },
    { 'name': 'MTH 4DIGIT', 'test': 'Jan 1601' }, # XXX not capturing full dates
    { 'name': 'MTH of 4DIGIT', 'test': 'Jan. of 1601' },
    { 'name': 'MTH, 4DIGIT', 'test': 'Jan, 1601' },
    { 'name': 'MONTH 4DIGIT', 'test': 'January 1601' },
    { 'name': 'MONTH of 4DIGIT', 'test': 'January of 1601' },
    { 'name': 'MONTH, 4DIGIT', 'test': 'January, 1601' },
    { 'name': 'MTH DAY 4DIGIT', 'test': 'Jan 20 1601' },
    { 'name': 'MTH DAY, 4DIGIT', 'test': 'Jan 20, 1601' },
    { 'name': 'MONTH DAY 4DIGIT', 'test': 'January 20 1601' },
    { 'name': 'MONTH DAY, 4DIGIT', 'test': 'January 20, 1601' },
    { 'name': 'in 4DIGIT', 'test': 'in 1601' },
    { 'name': 'early 4DIGIT', 'test': 'early 1601' },
    { 'name': 'late 4DIGIT', 'test': 'late 1601' },
    { 'name': 'end of 4DIGIT', 'test': 'end of 1601' },
    { 'name': 'start of 4DIGIT', 'test': 'start of 1601' },
    { 'name': 'beginning of 4DIGIT', 'test': 'beginning of 1601' },
    { 'name': 'around 4DIGIT', 'test': 'around 1601' },
    { 'name': 'mid-4DIGIT', 'test': 'mid-1601' },
    { 'name': 'middle of 4DIGIT', 'test': 'middle of 1601' },
    { 'name': 'pre-4DIGIT', 'test': 'pre-1601' },
    { 'name': 'post-4DIGIT', 'test': 'post-1601' },
    { 'name': 'before 4DIGIT', 'test': 'before 1601' },
    { 'name': 'until 4DIGIT', 'test': 'until 1601' },
    { 'name': 'after 4DIGIT', 'test': 'after 1601' },
    { 'name': 'since 4DIGIT', 'test': 'since 1601' },
    # first quarter of 1601
    # circas: ca. 1520, circa 1400
    # year 1582
]

weak_dates = [
    { 'name': 'DECADEs', 'test': '1610s', 'answer': '1610' }, # XXX not capturing that it's a decade
    { 'name': "DECADE's", 'test': "1610's", 'answer': '1610' },
    { 'name': 'MILLENIUMs', 'test': '1600s', 'answer': '1600' }, # XXX not capturing that it's a millenium
    { 'name': "MILLENIUM's", 'test': "1600's", 'answer': '1600' },
    { 'name': '\\(4DIGIT\\)', 'test': '(1601)' }, # XXX probably needs some negative patterns: This section (2041) blah blah
    # negative pattern: Nature 434(7032)
    # first decade of the 20th century
    # the 20th century
    # the fifth century
]

# www.peterbe.com/plog/uniqifiers-benchmark
def f5(seq): # Alex Martelli ******* order preserving
    # for humor value, this is the way you do this "by hand" in perl. but see Lists::MoreUtils qw{uniq}
    seen = {}
    result = []
    for item in seq:
        if item in seen: continue
        seen[item] = 1
        result.append(item)
    return result

class dateparse:
    """
    A flexible parser of dates found in strings
    """

    def __init__(self):
        self.strong_dates = strong_dates
        self.weak_dates = weak_dates
        self.strong_dates_combined = self.preprocess_one(self.strong_dates)
        self.weak_dates_combined = self.preprocess_one(self.weak_dates)

    def run_builtin_tests(self):
        somefail = 0
        for dates in (self.strong_dates, self.weak_dates):
            for item in dates:
                if 'test' in item:
                    result = self.extract_some_dates([ item ], item['test'])
                    fail = 0
                    if len(result) < 1:
                        fail = 1
                        result = [ "result was empty" ] # to prevent additional fail in the next couple of lines
                    if result[0] != item['answer']: # XXX note that we aren't checking the ones that have 2 results like 1601-2
                        fail = 1
                    if fail:
                        print("pattern", item['pat'], "failed selftest, test=", item['test'], file=sys.stderr)
                        print(" result was", result[0], file=sys.stderr)
                        somefail += 1
        if somefail:
            print(somefail, "failures", file=sys.stderr)
            sys.exit(1)

    def preprocess_one(self, dates):
        """
        Preprocesses a dates structure to make it usable by extract_some_dates()
        """

        for item in dates:
            item['pat'] = item['name']

            if 'answer' not in item:
                item['answer'] = '1601'
            if 'test' not in item:
                print("item", item['name'], "lacks a test", file=sys.stderr) # XXX make this raise an exception, to ensure 100% coverage

            if item['pat'][0].isalnum():
                item['pat'] = '\\b' + item['pat']
            if item['pat'][-1].isalnum():
                item['pat'] = item['pat'] + '\\b'

            for b in building_blocks:
                item['pat'] = re.sub(b['name'], b['pat'], item['pat'])
            item['count'] = 0

#            item['pat'] = re.compile(item['pat'], re.I) # dont do this, because we're going to combine them all

        comb_pat = "|".join(item['pat'] for item in dates)
        return re.compile(comb_pat, re.I)

    def extract_some_dates(self, dates, string):
        """
        Returns a list of unique dates found in string, based on the list of patterns in dates
        """

        found = []

        for item in dates:
            for match in re.finditer(item['pat'], string):
                matches = match.groups()
                for date in matches:
                    if date is not None:
                        found.append(date)

        return f5(found)

    def extract_dates(self, string):
        """
        Returns a list of unique data found in string, based on a built-in list of patterns
        """

        retlist = []

        # a little convoluted, but the calling sequence is shared with the test system XXX fixme
        for pat in ( [ { 'pat': self.strong_dates_combined } ], [ { 'pat': self.weak_dates_combined } ] ):
            ret = self.extract_some_dates(pat, string)
            retlist.extend(ret)

        return f5(retlist)
                
if __name__ == "__main__":
    dp = dateparse()
    dp.run_builtin_tests()
    ret = dp.extract_dates("Queen Elizabeth I died in 1603.")
    print("Got", ret)
