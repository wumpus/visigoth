#!/usr/bin/env python3

import os
import pickle

class findthings:
    """
    Find things from a string
    """

    def __init__(self):
        picklename = os.environ.get('VISIGOTH_DATA','.')+'/things_pickle'
        f = open(picklename, 'rb')
        self.things = pickle.load(f)
        f.close()
        return

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
        print("results are", results, "sentence is:", "Charles Darwin and Prince went to the movie about NASA." )
        results = self.find_things("NASA.")
        print("results are", results, "sentence is:", "NASA." )
                
if __name__ == "__main__":
    ft = findthings()
    ft.run_tests()

