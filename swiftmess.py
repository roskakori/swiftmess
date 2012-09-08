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
import decimal
import logging
import re
from datetime import date, datetime

_log = logging.getLogger('swift')

__version__ = '0.2'


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


def structuredItems(messageToRead):
    assert messageToRead is not None
    block = None
    field = None
    value = None
    valuesSoFar = []
    for level, kind, value in messageItems(messageToRead):
        # TODO: remove: print u'    %d, %s, %s' % (level, kind, value)
        if kind == 'block':
            if block is not None:
                yield (level, block, field, valuesSoFar)
            block = value
            field = None
            valuesSoFar = []
        elif kind == 'field':
            if block is None:
                raise Error(u'block for field "%s" must be specified' % value)
            yield (level, block, field, valuesSoFar)
            field = value
            valuesSoFar = []
        elif kind == 'value':
            valuesSoFar.append(value)
        else:
            assert False, u'kind=%r' % kind
    # Yield the last item.
    if valuesSoFar:
        yield (level, block, field, valuesSoFar)


class Report(object):
    def __init__(self, messageToRead):
        assert messageToRead is not None
        self.report = None
        for item in structuredItems(messageToRead):
            _log.debug(u'item: %s', item)
            level, block, field, values = item
            leveBlockField = item[:3]
            if self.report is None:
                if leveBlockField == (1, 4, '77E'):
                    report = self._valueFor(item, '/TRNA')
                    if self.report is None:
                        self.report = report
                    else:
                        raise Error(u'cannot set report to "%s" because it already is "%s"' % (report, self.report))
            elif self.report == u'RAWCE260':
                self._processCe260(item)
            else:
                raise Error(u'cannot (yet) read reports of type "%s"' % self.report)

    def _valueFor(self, item, valuePrefix, strip=True, required=True, defaultValue=None):
        assert item is not None
        assert valuePrefix
        if required:
            assert defaultValue is None

        result = None
        _, block, field, values = item
        valueIndex = 0
        valueCount = len(values)
        while (result is None) and (valueIndex < valueCount):
            value = values[valueIndex]
            if value.startswith(valuePrefix):
                result = value[len(valuePrefix):]
                if strip:
                    result = result.strip()
            else:
                valueIndex += 1
        if result is None:
            if required:
                raise Error(u'block %d, field "%s" must contain %s but found only: %s' % (block, field, valuePrefix, values))
            else:
                result = defaultValue
        return result

    def _slashedNameValue(self, item):
        assert item is not None
        _, block, field, values = item
        if len(values) != 1:
            raise Error(u'value in block "%s", field "%s" must fit into one line but is: %r' % (block, field, values))
        # TODO: compile regex.
        finding = re.match(r'[:](?P<name>.+)//(?P<value>.*)', values[0])
        if finding is None:
            raise Error(u'value in block "%s", field "%s" must contain text matching ":<NAME>//<VALUE>" but is: %r' % (block, field, values))
        name = finding.group('name')
        value = finding.group('value')
        return (name, value)

    def _dateFromIsoText(self, item, name, text):
        assert item is not None
        assert text is not None

        _, block, field, _ = item
        try:
            textAsTime = datetime.strptime(text, '%Y%m%d')
        except ValueError, error:
            message = u'cannot convert "%s" in block "%s", field "%s"' % (text, block, field)
            if name is not None:
                message += u', item "%s"' % name
            message += u' to date: %s' % error
            raise Error(message)
        result = date(textAsTime.year, textAsTime.month, textAsTime.day)
        return result

    def _decimalFrom(self, item, name, value):
        '''
        A ``decimal.Decimal`` from ``value`` properly handling all kinds of separators.

        Examples:

        * _decimalFrom(..., '1') --> 1
        * _decimalFrom(..., '123.45') --> 123.45
        * _decimalFrom(..., '123,45') --> 123.45
        * _decimalFrom(..., '123456.78') --> 123456.78
        * _decimalFrom(..., '123,456.78') --> 123456.78
        * _decimalFrom(..., '123.456,78') --> 123456.78
        '''
        assert item is not None
        assert value is not None

        isGermanNumeric = False
        firstCommaIndex = value.find(',')
        if firstCommaIndex >= 0:
            firstDotIndex = value.find('.')
            if firstCommaIndex > firstDotIndex:
                isGermanNumeric = True
        if isGermanNumeric:
            unifiedValue = value.replace('.', '').replace(',', '.')
        else:
            unifiedValue = value.replace(',', '')
        try:
            result = decimal.Decimal(unifiedValue)
        except Exception, error:
            _, block, field, _ = item
            message = u'cannot convert "%s" in block "%s", field "%s"' % (value, block, field)
            if name is not None:
                message += u', item "%s"' % name
            message += u' to decimal: %s' % error
            raise Error(message)

        return result

    def _currencyAndAmountFrom(self, item, name, value):
        '''
        tuple with currency (as ISO code) and amount extracted from ``value``.

        Example: 'EUR123,45' --> (u'EUR', 123.45)
        '''
        assert item is not None
        assert value is not None

        def errorMessage(details):
            _, block, field, _ = item
            result = u'cannot convert "%s" in block "%s", field "%s"' % (value, block, field)
            if name is not None:
                result += u', item "%s"' % name
            result += u' to currency and amount: %s' % details
            return result

        if len(value) < 4:
            raise Error(errorMessage(u'value must have at least 4 characters'))
        currency = value[:3]
        try:
            amount = self._decimalFrom(item, name, value[3:])
        except Exception, error:
            raise Error(errorMessage(error))
        return (currency, amount)

    def _initCe260(self):
        self.clearingMember = None
        self.financialInstrument = None
        self.safekeepingAccount = None
        self.transactionDetails = None

        # Transaction details
        self.accrInterest = None
        self.ca = None
        self.ccpStatus = None
        self.clearingMember = None
        self.exchangeMember = None
        self.leg = None
        self.orderNettingType = None
        self.orderNumber = None
        self.originType = None
        self.settlementDate = None
        self.tradeDate = None
        self.tradeLocation = None
        self.tradeNumber = None
        self.tradeSettlement = None
        self.tradeType = None
        self.transactionType = None

    def _processCe260(self, item):
        def createTransactionDetailsNameToValueMap(item):
            level, block, field, values = item
            assert level == 1
            assert block == 4
            assert field == '70E'
            assert values

            result = {}
            TrDeHeader = ':TRDE//'
            if values[0].startswith(TrDeHeader):
                transactionDetails = [values[0][len(TrDeHeader):]]
                transactionDetails.extend(values[1:])
                detailsText = u' '.join(transactionDetails)
                for detail in detailsText.split(u'/'):
                    detail = detail.rstrip()
                    if detail != '':
                        indexOfFirstSpace = detail.find(' ')
                        if indexOfFirstSpace >= 0:
                            name = detail[:indexOfFirstSpace]
                            value = detail[indexOfFirstSpace + 1:].lstrip()
                        else:
                            name = detail
                            value = None
                        if name in result:
                            raise Error(u'duplicate transaction detail "%s" must be removed: %s' % (name, transactionDetails))
                        result[name] = value
            else:
                raise Error(u'transaction details in field "%s" must start with "%s" but are: %s' % (field, TrDeHeader, values))
            return result

        level, block, field, values = item
        if (level == 1) and (block == 4):
            if field == '19A':
                name, value = self._slashedNameValue(item)
                if name == 'ACRU':
                    self.accrInterest = self._currencyAndAmountFrom(item, name, value)
                elif name == 'PSTA':
                    self.tradeSettlement = self._currencyAndAmountFrom(item, name, value)
            elif field == '20C':
                name, value = self._slashedNameValue(item)
                if name == 'PREV':
                    self.tradeNumber = value
            elif field == '35B':
                self.financialInstrument = values
            if field == '36B':
                name, value = self._slashedNameValue(item)
                if name == 'ACRU':
                    self.accrInterest = self._currencyAndAmountFrom(item, name, value)
            elif field == '70E':
                self.transactionDetails = createTransactionDetailsNameToValueMap(item)
                self.ca = self.transactionDetails.get('CA')
                self.ccpStatus = self.transactionDetails.get('CCPSTAT')
                self.clearingMember = self.transactionDetails.get('CLGM')
                self.exchangeMember = self.transactionDetails.get('EXCH')
                self.leg = self.transactionDetails.get('LN')
                self.orderNettingType = self.transactionDetails.get('ORDNETT')
                self.orderNumber = self.transactionDetails.get('ORDNB')
                self.originType = self.transactionDetails.get('OT')
                self.tradeType = self.transactionDetails.get('TTYP')
                self.transactionType = self.transactionDetails.get('TYPE')
            elif field == '94B':
                name, value = self._slashedNameValue(item)
                if name == 'TRAD':
                    ExchHeader = 'EXCH/'
                    if value.startswith(ExchHeader):
                        self.tradeLocation = value[len(ExchHeader):]
            elif field == '97A':
                self.safekeepingAccount = self._valueFor(item, ':SAFE//')
            elif field == '98A':
                name, value = self._slashedNameValue(item)
                if name == 'SETT':
                    self.settlementDate = self._dateFromIsoText(item, name, value)
                elif name == 'TRAD':
                    self.tradeDate = self._dateFromIsoText(item, name, value)
