'''
Swiftmess is a Python module to parse SWIFT messages used for financial transactions in banking.
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
import logging

_log = logging.getLogger('swift')

__version__ = '0.1'


class Error(Exception):
    pass


def messageItems(readable):
    '''
    Message items found in ``readable`` as tuples of the form ``(nestingLevel, type, value)`` with:

    * nestingLevel: level of nested blocks
    * type: one of: 'message', 'block', 'field', 'value'
    * value: for 'block' this is the block key, for 'field' this is the field name, 'value' this is the value
      and for 'message' this is ``None``.

    The messages have to be stored in EDIFACT / ISO 15022 format.
    '''
    assert readable is not None

    # Possible values for ``state``.
    _BeforeStartOfBlock = 'BeforeStartOfBlock'
    _InBlockKey = 'InBlockKey'
    _InLine = 'InLine'
    _InFieldKey = 'InFieldKey'
    _InFieldValue = 'InFieldValue'
    _InValue = 'InValue'

    state = _BeforeStartOfBlock
    text = None
    blockKey = None
    fieldKey = None
    level = 0

    char = readable.read(1)
    while (char != ''):
        _log.debug('level=%d, char=%r, state=%s, text=%r', level, char, state, text)
        if char == '\r':
            pass
        elif state == _BeforeStartOfBlock:
            if char == '{':
                state = _InBlockKey
                level += 1
                text = ''
            elif char == '}':
                if level == 0:
                    raise Error('unmatched %r outside of any block must be removed' % char)
                level -= 1
            elif char == '\n':
                if level != 0:
                    raise Error(u'nested block must be closed (state=%r, level=%d)' % (state, level))
                yield (level, 'message', None)
            elif char != '\r':
                raise Error('block must start with %r instead of %r' % ('{', char))
        elif state == _InBlockKey:
            if char == ':':
                state = _InLine
                blockKey = long(text)
                yield (level, 'block', blockKey)
                text = None
            elif char.isdigit():
                text += char
            else:
                raise Error('block id must consist of decimal digits bug encountered %r' % char)
        elif state == _InLine:
            if char == '{':
                state = _InBlockKey
                level += 1
                text = ''
            elif char == '}':
                state = _BeforeStartOfBlock
                level -= 1
                assert level >= 0
            elif char == ':':
                state = _InFieldKey
                text = ''
            elif char == '\n':
                yield (level, 'value', '')
            else:
                state = _InValue
                text = char
        elif state == _InFieldKey:
            if char == ':':
                state = _InFieldValue
                fieldKey = text
                text = ''
            else:
                text += char
        elif state == _InFieldValue:
            if (char == '\n') or char == '}':
                yield (level, 'field', fieldKey)
                yield (level, 'value', text)
                fieldKey = None
                text = None
                if char == '}':
                    state = _BeforeStartOfBlock
                    level -= 1
                    assert level >= 0
                else:
                    state = _InLine
            else:
                text += char
        elif state == _InValue:
            if (char == '\n') or char == '}':
                yield (level, 'value', text)
                text = None
                if char == '}':
                    state = _BeforeStartOfBlock
                    level -= 1
                    assert level >= 0
                else:
                    state = _InLine
            else:
                text += char
        char = readable.read(1)
    if state != _BeforeStartOfBlock:
        raise Error(u'block must be closed (state=%r)' % state)
    if level != 0:
        raise Error(u'nested block must be closed (state=%r, level=%d)' % (state, level))
