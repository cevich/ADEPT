#!/usr/bin/env python

"""
Unittests for included adept files

Dependencies:
    - python-2.7
    - python-unittest2
    - PyYAML
    - pylint
"""

import sys
import os
import os.path
from pdb import Pdb
import mmap
import re
from glob import glob

# ref: https://docs.python.org/dev/library/unittest.html
import unittest2 as unittest
import test_adept

# Prefer to keep number of extra files/modules low
# pylint: disable=C0302

class TestCaseBase(unittest.TestCase):

    """Base class for all other test classes to use"""

    def setUp(self):
        # Keep Debugger close at hand
        self.pdb = Pdb()

    def trace(self):
        """Enter the pdb debugger, 'n' will step back to self.trace() caller"""
        return self.pdb.set_trace()

    def subtests(self, items):
        """
        Return each item's value inside an active context manager

        :param tuple items: Tuple or list of items to create contexts for
        :returns: Each item's value inside an active context manager
        :rtype: type(item)
        """
        for item in items:
            ctxmgr = self.subTest(item=item)
            with ctxmgr:
                yield item

class TestPylint(test_adept.TestPylint):

    """Run pylint over this unittest"""

    def setUp(self):
        """Override test_adept.TestCaseBase method"""
        pass

    def tearDown(self):
        """Override test_adept.TestCaseBase method"""
        pass

    def test_unittest_pylint(self):
        "Run pylint on the unittest module itself"
        self._pylintrun(os.path.basename(__file__))

    @unittest.skip("Not relevant")
    def test_uut_pylint(self):
        pass


class TestContentRegexs(TestCaseBase):

    """
    Iterate over files from a glob, matching forbidden regular expressions
    """

    globs = ('files/*.yml',)
    regexes = (re.compile(r'/usr/bin/bash'),
               re.compile(r'/usr/bin/sh'),
               re.compile(r'/usr/bin/cp'),
               re.compile(r' /bin/test'),
               re.compile(r'/usr/bin/mkdir'),
               re.compile(r'/usr/bin/python'),
              )
    # If non-None, contain iterable of relative paths to files
    check_files = None

    def setUp(self):
        super(TestContentRegexs, self).setUp()
        self.check_files = []
        here = os.path.dirname(sys.modules[__name__].__file__)
        here = os.path.abspath(here)
        for _glob in self.globs:
            self.check_files += glob(os.path.join(here, _glob))
        if not self.check_files:
            self.check_files = None

    @staticmethod
    def regexs_not_in(regexes, openfile):
        """
        Return non-empty details-string if any regex found anywhere in openfile
        """
        # No context manager for this :(
        mmfile = None
        found_one = ''
        try:
            mmfile = mmap.mmap(openfile.fileno(), 0,
                               mmap.MAP_PRIVATE, mmap.PROT_READ)
            for regex in regexes:
                # Only care about first one found
                for found in regex.finditer(mmfile):
                    if bool(found):
                        found_one = ('Matched forbidden r"%s" in %s'
                                     % (regex.pattern, openfile.name))
                        break
                if found_one:
                    break
        finally:
            mmfile.close()
        return found_one

    def test_regexes(self):
        """Verify no globbed file matches any regex"""
        self.assertTrue(self.check_files, "glob did not match any files")
        for filename in self.subtests(self.check_files):
            with open(filename, 'r+') as openfile:
                # The value is it's own test-failure message
                found_one = self.regexs_not_in(self.regexes, openfile)
                self.assertEqual('', found_one, found_one)


if __name__ == '__main__':
    unittest.main(failfast=True, catchbreak=True, verbosity=2)
