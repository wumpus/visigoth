#!/usr/bin/env python3

import os
import os.path # is this redundant?
import csv
import gzip
import pickle

class findthings:
    """
    Find things from a string
    """

    def __init__(self):
        # if pickle file exists, load things out of it
        picklename = os.path.expanduser('~/things.pickle')
        if os.path.isfile(picklename):
            f = open(picklename, 'rb')
            self.things = pickle.load(f) # utf8?
            f.close()
            return

        self.load_linux_dictionary()
        self.load_wikipedia_titles()
        self.apply_blacklist()

        f = open(picklename + '.new', 'wb') # utf8?
        pickle.dump(self.things, f)
        f.close()
        os.rename(picklename + '.new', picklename)
        # by the way, this pickle file reduces startup time from 70-90s to 8-17s

    def load_linux_dictionary(self):
        self.lowercase_word_dict = {}
        self.mixedcase_word_dict = {}
        self.titlecase_word_dict = {}
        f = open(os.path.expanduser('~/linux.words.centos7'), 'r')
        for line in f:
            word = line.rstrip()
            rest = word[1:]
            if word.lower() == word:
                self.lowercase_word_dict[word] = 1
            elif rest.lower() == rest:
                self.titlecase_word_dict[word.lower()] = word # first letter upper, rest lower
            else:
                self.mixedcase_word_dict[word.lower()] = word # more than just first letter upper
        f.close()

    def load_wikipedia_titles(self):

#        file = os.path.expanduser("~/wikipedia_articles_all.csv.gz")
        file = os.path.expanduser("~/wikipedia_articles_all.csv")

        if file[-3:] == '.gz':
            input = gzip.open(file, mode='rt', encoding='utf-8', newline='')
        else:
            input = open(file, 'r', encoding='utf-8', newline='')

        self.things = {}

        with input as f:
            reader = csv.reader(f)
            for row in reader:
                [ spaces, title, redir ] = row
                if int(spaces) > 4:
                    # keep up to 5-word phrases, discard longer
                    continue
                if title.lower() == redir.lower():
                    # nothing but a case-changing redir. drop. we'll use the non-redir case.
                    # XXX doesn't catch case where several mixed-case titles refer to the same redir
                    continue
                if title.startswith('List of '):
                    continue
                if title.startswith('The '): # *sigh*
                    continue
                if title.isdecimal():
                    continue
                if int(spaces) > 0:
                    first = title[0] # we know this is uppercase
                    rest = title[1:]
                    if rest.lower() == rest:
                        # Foo bar -> foo bar
                        self.things[title.lower()] = redir
                    else:
                        # something is upper, keep the existing case
                        self.things[title] = redir
                else:
                    # we have a single word. wikipedia has title-cased it if it was all-lower... we
                    # want to keep proper nouns and drop wikiwords, but wikipedia doesn't help much
                    # XXX use wikiwords?
                    mixedc = self.mixedcase_word_dict.get(title.lower())
                    titlec = self.titlecase_word_dict.get(title.lower())
                    lowerc = self.lowercase_word_dict.get(title.lower())
                    if mixedc is not None:
                        # mixed-case in Linux dict. Keep Linux dict case, forget Wikipedia case.
                        self.things[mixedc] = redir
                    elif titlec is not None and lowerc is None:
                        # titlecase-only in linux dict. ok, let's keep it like that.
                        self.things[titlec] = redir
                    elif titlec is None and lowerc is not None:
                        # lowercase-only in linux dict. drop it: wikiword entry
                        continue
                    else:
                        # titlecase and lowercase in Linux dict.
                        # this happens for proper nouns Darwin/darwin and also
                        # for words commonly in titles: An The etc.
                        # keep it as titlecase; use blacklist to get rid of words commonly in titles
                        self.things[titlec] = redir

    def apply_blacklist(self):
        f = open(os.path.expanduser('~/things-blacklist'), 'r')
        for line in f:
            word = line.rstrip()
            if word.istitle():
                word = word.lower()
            self.things.pop(word, None)
            title_word = word[0].upper()
            if len(word) > 1:
                title_word += word[1:]
            self.things.pop(title_word, None)
        f.close()

    def find_things(self,sentence):
        ret = []
        words = sentence.split(sep=' ')
        while 1:
            if len(words) == 0:
                break

            # we use look-forward because we want the longest matches possible                                                                                     
            for count in range(5, 0, -1):
                if len(words) >= count:
                    match = " ".join(words[0:count])
                    got_match = 0
                    match = match.rstrip(',)')
                    match = match.lstrip('(')
                    sans_punct_match = match.rstrip('.?!')

                    # try actual case first
                    if self.things.get(sans_punct_match) is not None:
                        ret.append(sans_punct_match)
                        got_match = 1
                    elif self.things.get(match) is not None:
                        ret.append(match)
                        got_match = 1

                    # then try lowercase
                    elif self.things.get(sans_punct_match.lower()) is not None:
                        ret.append(sans_punct_match.lower())
                        got_match = 1
                    elif self.things.get(match.lower()) is not None:
                        ret.append(match.lower())
                        got_match = 1

                    if got_match:
                        # pop off all words associated with the match, i.e. "Charles Darwin" match pops one here and one outside
                        for blah in range(0, count-1):
                            words.pop(0)
                        break
            words.pop(0)
        return ret

    def run_tests(self):
        results = self.find_things("Charles Darwin and Prince went to the movie about NASA.")
        print("results are", results, "sentence is", "Charles Darwin and Prince went to the movie about NASA." )
        results = self.find_things("NASA.")
        print("results are", results, "sentence is", "NASA." )
                
if __name__ == "__main__":
    ft = findthings()
    ft.run_tests()

