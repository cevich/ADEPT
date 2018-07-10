#!/usr/bin/env python

"""
Unit tests for VerboseFilter, a logging helper in adept_openstack.py
"""

import logging
import sys
from mock import Mock
from unittest2 import TestCase, main

sys.modules['virtualenv'] = Mock()      # module not needed for this test

sys.path.insert(0, 'kommandir/bin')


class MyHandler(logging.Handler):
    """
    Output handler for logging messages. No output; just push onto list.
    """
    def __init__(self, message_list):
        logging.Handler.__init__(self)
        self.message_list = message_list

    def emit(self, record):
        self.message_list.append(record.getMessage())


class TestVerboseFilter(TestCase):
    """
    General test class. Defines only one test function, used by
    test generator to create tests for all combinations of levels
    and verbose flags.
    """

    def setUp(self):
        import adept_openstack  # pylint: disable=E0401
        self.a_o = adept_openstack
        self.logger = logging.getLogger()
        self.message_list = []

    def _test_init(self, level, verbose):
        # Grrr. The Logger thing is a global, and there doesn't seem to be
        # a way to get a new one each time. For addHandler() and addFilter()
        # to work, we need to delve into internals.
        self.logger.handlers = []
        self.logger.filters = []

        # Now we can set up our desired handler and filter
        self.logger.setLevel(level)
        self.message_list = []
        self.logger.addHandler(MyHandler(self.message_list))
        self.logger.addFilter(self.a_o.VerboseFilter(level, verbose))

    def _test_basic(self, level, verbose, expect):
        self._test_init(level, verbose)

        # Always log the same messages...     pylint: disable=C0326
        logging.debug( "this is DEBUG")
        logging.info(  "this is INFO")
        logging.info( ">this is VERBOSE-INFO")
        logging.warn(  "this is WARN")
        logging.error( "this is ERROR")

        # ...the difference is what we expect to see.
        expect_list = []
        for level_name in ['DEBUG', 'INFO', 'VERBOSE-INFO', 'WARN', 'ERROR']:
            if level_name[0] in expect:
                expect_list.append('this is {}'.format(level_name))

        self.assertEqual(self.message_list, expect_list)

    def test_exception(self):
        """
        logger can be invoked with non-string messages; make sure our
        filter doesn't choke on those.
        """
        self._test_init(logging.DEBUG, False)

        import exceptions
        exception_arg = exceptions.IndexError
        logging.error(exception_arg)
        self.assertEqual(self.message_list, [str(exception_arg)])

    def test_reformatting(self):
        """
        2018-07-10 fixes issue seen by cevich in production: if message
        is a format string (with percent sign), and includes further
        arguments, an earlier version of our filter would crash
        with 'not all arguments converted' because we replaced
        the format string with the *formatted* one. This subtest
        fails under that earlier revision.
        """
        self._test_init(logging.DEBUG, True)
        logging.info(">string with %s", "extra args")
        self.assertEqual(self.message_list, ["string with extra args"])

def test_generator(test_info):
    """
    Generate a test for this combination. Returns test name and code ref.
    """
    (level, verbose, expect) = test_info

    name = 'test_' + logging.getLevelName(level).lower()
    if verbose:
        name += '_verbose'

    def _run_test(self):
        self._test_basic(level, verbose, expect.strip()) # pylint: disable=W0212

    return [name, _run_test]


# Actual set of tests. Each row defines a tuple of (level, verbose, expect)
# from which we generate an actual test. The only unusual rows are the INFO
# ones: with verbose we expect to see INFO-level messages with the '>' prefix,
# without verbose we expect not to see those. In all other cases we want
# to see messages of that level and above.
# pylint: disable=C0326
TESTS = [
    (logging.DEBUG, False, 'DIVWE'),
    (logging.DEBUG, True,  'DIVWE'),
    (logging.INFO,  False, ' I WE'),
    (logging.INFO,  True,  ' IVWE'),
    (logging.WARN,  False, '   WE'),
    (logging.WARN,  True,  '   WE'),
    (logging.ERROR, False, '    E'),
    (logging.ERROR, True,  '    E'),
]

# Generate tests. This needs to happen outside of the __main__ code, otherwise
# 'unit2 discover' will import, see no 'test_*' functions, and silently quit.
for test_info_tuple in TESTS:
    test_ref = test_generator(test_info_tuple)
    setattr(TestVerboseFilter, test_ref[0], test_ref[1])

if __name__ == '__main__':
    main()
