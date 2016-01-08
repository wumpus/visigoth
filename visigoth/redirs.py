#!/usr/bin/env python3

import shelve
import os
import unittest

class redirs:
    """
    Do things related to Wikipedia redirects, following
    them forwards and backwards.
    """

    def __init__(self):
        self.backwards = shelve.open(os.environ.get('VISIGOTH_DATA','.')+'/redir_backward_shelf', flag='r')
        self.forwards = shelve.open(os.environ.get('VISIGOTH_DATA','.')+'/redir_forward_shelf', flag='r')

    def forward(self, thing):
        """
        Follow redirects forward to find the canonical name for a thing.
        We currently do at most 2 hops.
        """

        f = self.forwards.get(thing)
        if f == '':
            if not thing.islower():
                f = thing
            else:
                # XXX to fix a bug in previous build-redir-shelf version
                mixed = thing[0].upper() + thing[1:]
                f = self.forwards.get(mixed, thing)
                if f == '':
                    f = mixed
        if f is None:
            f = self.forwards.get(thing.lower())
            if f == '':
                if not thing.islower():
                    f = thing
                else:
                    # XXX fix a bug in previous build-redir-shelf version
                    mixed = thing[0].upper() + thing[1:]
                    f = self.forwards.get(mixed, thing)
                    if f == '':
                        f = mixed

        # already canon
        if f == thing or f == thing.lower():
            return f

        ff = self.forwards.get(f)
        if ff == '':
            return f
        if ff is None:
            ff = self.forwards.get(f.lower())
        if ff == '':
            return f

        if ff is None:
            return thing
        else:
            return ff

    def backward(self, canon):
        """
        Given a canonical name, return a list of articles that redirect there
        Returns an empty list if there are no redirects. XXX is this pythonic?
        """
        b = self.backwards.get(canon)
        if b is None:
            b = self.backwards.get(canon.lower())

        return b or []

class test_redirs(unittest.TestCase):

        def test_not_data_dependent(self):
            self.assertNotEqual(r.forward('dog'), 'dog' ) # Might be Dog or Dog (disambiguation)

        def test_data_dependent(self):
            self.assertEqual(r.forward('Doggie'), 'Dog' )
            self.assertTrue(len(r.backward('Dog')) > 2)
            self.assertIsNotNone(r.backward('doesnotexist'))
            self.assertIsInstance(r.backward('doesnotexist'), list)

if __name__ == "__main__":
    r = redirs()
    unittest.main()


