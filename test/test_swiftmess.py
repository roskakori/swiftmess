'''Tests for `swiftmess`.
'''
# Copyright (c) 2012, Thomas Aglassinger
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import with_statement

import logging
import os
import unittest
import swiftmess

_log = logging.getLogger('swift')


def _testFilePath(name):
    basePath = os.path.dirname(__file__)
    return os.path.join(basePath, name)


class TestSwiftmess(unittest.TestCase):

    def testCanReadMessageItems(self):
        ExpectedItems = [
            (1, 'block', 1L),
            (1, 'value', 'F01XXXXXXXXXXXX0000999999'),
            (1, 'block', 2L),
            (1, 'value', 'O5981519051128XXXXXXXXXXXX000099999905112815 19N'),
            (1, 'block', 3L),
            (2, 'block', 108L),
            (1, 'block', 4L),
            (1, 'value', ''),
            (1, 'field', '20'),
            (1, 'value', '99990212189999'),
            (1, 'field', '12'),
            (1, 'value', '001'),
            (1, 'field', '77E'),
            (1, 'value', '/TREF XXXXXXXXXXXXXXXX'),
            (1, 'value', '/NOIM 000000'),
            (1, 'value', '/NOII 000000'),
            (1, 'value', '/NOVM 000000'),
            (1, 'value', '/NOVI 000000'),
            (1, 'value', '/TRNA RAWCE290'),
            (1, 'value', '-'),
            (0, 'message', None),
            (1, 'block', 1L),
            (1, 'value', 'F01XXXXXXXXXXXX0000999999'),
            (1, 'block', 2L),
            (1, 'value', 'O5981519051128XXXXXXXXXXXX000099999905112815 19N'),
            (1, 'block', 3L),
            (2, 'block', 108L),
            (1, 'block', 4L),
            (1, 'value', ''),
            (1, 'field', '20'),
            (1, 'value', '99990212189999'),
            (1, 'field', '12'),
            (1, 'value', '099'),
            (1, 'field', '77E'),
            (1, 'value', '/NOMS 000001'),
            (1, 'value', '-'),
            (0, 'message', None)
        ]
        with open(_testFilePath('rawce290.txt')) as testFile:
            actualItems = list(swiftmess.messageItems(testFile))
            self.assertEqual(actualItems, ExpectedItems)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
