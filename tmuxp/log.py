#!/usr/bin/env python
# Pieces of this code are from Tornado, they are being phased out.
#
# Copyright 2012 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from __future__ import absolute_import, division, print_function, with_statement

import logging
import logging.handlers
import sys
import time
from colorama import init
init()
from colorama import Fore, Back, Style

try:
    import curses
except ImportError:
    curses = None

# From tornado/util.py:
# Fake unicode literal support:  Python 3.2 doesn't have the u'' marker for
# literal strings, and alternative solutions like "from __future__ import
# unicode_literals" have other problems (see PEP 414).  u() can be applied
# to ascii strings that include \u escapes (but they must not contain
# literal non-ascii characters).
if not isinstance('', type(b'')):
    def u(s):
        return s
    bytes_type = bytes
    unicode_type = str
    basestring_type = str
else:
    def u(s):
        return s.decode('unicode_escape')
    bytes_type = str
    unicode_type = unicode
    basestring_type = basestring


_UTF8_TYPES = (bytes_type, type(None))
_TO_UNICODE_TYPES = (unicode_type, type(None))


def utf8(value):
    """Converts a string argument to a byte string.

    If the argument is already a byte string or None, it is returned unchanged.
    Otherwise it must be a unicode string and is encoded as utf8.
    """
    if isinstance(value, _UTF8_TYPES):
        return value
    assert isinstance(value, unicode_type), \
        "Expected bytes, unicode, or None; got %r" % type(value)
    return value.encode("utf-8")


def to_unicode(value):
    """Converts a string argument to a unicode string.

    If the argument is already a unicode string or None, it is returned
    unchanged.  Otherwise it must be a byte string and is decoded as utf8.
    """
    if isinstance(value, _TO_UNICODE_TYPES):
        return value
    assert isinstance(value, bytes_type), \
        "Expected bytes, unicode, or None; got %r" % type(value)
    return value.decode("utf-8")

# to_unicode was previously named _unicode not because it was private,
# but to avoid conflicts with the built-in unicode() function/type
_unicode = to_unicode

# When dealing with the standard library across python 2 and 3 it is
# sometimes useful to have a direct conversion to the native string type
if str is unicode_type:
    native_str = to_unicode
else:
    native_str = utf8


def _stderr_supports_color():
    color = False
    if curses and sys.stderr.isatty():
        try:
            curses.setupterm()
            if curses.tigetnum("colors") > 0:
                color = True
        except Exception:
            pass
    return color

# Encoding notes:  The logging module prefers to work with character
# strings, but only enforces that log messages are instances of
# basestring.  In python 2, non-ascii bytestrings will make
# their way through the logging framework until they blow up with
# an unhelpful decoding error (with this formatter it happens
# when we attach the prefix, but there are other opportunities for
# exceptions further along in the framework).
#
# If a byte string makes it this far, convert it to unicode to
# ensure it will make it out to the logs.  Use repr() as a fallback
# to ensure that all byte strings can be converted successfully,
# but don't do it by default so we don't add extra quotes to ascii
# bytestrings.  This is a bit of a hacky place to do this, but
# it's worth it since the encoding errors that would otherwise
# result are so useless (and tornado is fond of using utf8-encoded
# byte strings whereever possible).


def safe_unicode(s):
    try:
        return _unicode(s)
    except UnicodeDecodeError:
        return repr(s)

NORMAL = Fore.RESET + Style.RESET_ALL + Back.RESET

LEVEL_COLORS = {
    'DEBUG': Fore.BLUE,  # Blue
    'INFO': Fore.GREEN,  # Green
    'WARNING': Fore.YELLOW,
    'ERROR': Fore.RED,
    'CRITICAL': Fore.RED
}


class LogFormatter(logging.Formatter):

    """Log formatter used in Tornado.

    Key features of this formatter are:

    * Color support when logging to a terminal that supports it.
    * Timestamps on every log line.
    * Robust against str/bytes encoding problems.

    This formatter is enabled automatically by
    `tornado.options.parse_command_line` (unless ``--logging=none`` is
    used).
    """

    def prefix_template(self, record):
        ''' this is available as a definition instead of a class
        variable so it can access to instance. it also accepts the record
        parameter.

        :param: record: :py:class:`logging.LogRecord` object. this is passed in
        from inside the :py:meth:`logging.Formatter.format` record.
        '''

        prefix_template = ''
        prefix_template += NORMAL
        prefix_template += LEVEL_COLORS.get(record.levelname) + Style.BRIGHT + '(%(levelname)s)' + NORMAL + ' '
        prefix_template += '[' + Fore.BLACK + Style.DIM + Style.BRIGHT + '%(asctime)s' + Fore.RESET + Style.RESET_ALL + ']'
        prefix_template += ' ' + Fore.WHITE + Style.DIM + Style.BRIGHT + '%(name)s' + Fore.RESET + Style.RESET_ALL + ' '
        prefix_template += NORMAL

        return prefix_template

    def __init__(self, color=True, *args, **kwargs):
        logging.Formatter.__init__(self, *args, **kwargs)
        self._color = color and _stderr_supports_color()

    def format(self, record):
        try:
            record.message = record.getMessage()
        except Exception as e:
            record.message = "Bad message (%r): %r" % (e, record.__dict__)
        assert isinstance(
            record.message, basestring_type)  # guaranteed by logging

        date_format = '%H:%m:%S'
        record.asctime = time.strftime(date_format, self.converter(record.created))

        prefix = self.prefix_template(record) % record.__dict__

        formatted = prefix + " " + safe_unicode(record.message)
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            # exc_text contains multiple lines.  We need to safe_unicode
            # each line separately so that non-utf8 bytes don't cause
            # all the newlines to turn into '\n'.
            lines = [formatted.rstrip()]
            lines.extend(safe_unicode(ln)
                         for ln in record.exc_text.split('\n'))
            formatted = '\n'.join(lines)
        return formatted.replace("\n", "\n    ")


class DebugLogFormatter(LogFormatter):

    def prefix_template(self, record):
        ''' this is available as a definition instead of a class
        variable so it can access to instance. it also accepts the record
        argument.

        :param: record: :py:class:`logging.LogRecord` object. this is passed in
        from inside the :py:meth:`logging.Formatter.format` record.
        '''

        prefix_template = ''
        prefix_template += NORMAL
        prefix_template += LEVEL_COLORS.get(record.levelname) + Style.BRIGHT + '(%(levelname)1.1s)' + NORMAL + ' '
        prefix_template += '[' + Fore.BLACK + Style.DIM + Style.BRIGHT + '%(asctime)s' + Fore.RESET + Style.RESET_ALL + ']'
        prefix_template += ' ' + Fore.WHITE + Style.DIM + Style.BRIGHT + '%(name)s' + Fore.RESET + Style.RESET_ALL + ' '
        prefix_template += Fore.GREEN + Style.BRIGHT + '%(module)s.%(funcName)s()'
        prefix_template += Fore.BLACK + Style.DIM + Style.BRIGHT + ':' + NORMAL + Fore.CYAN + '%(lineno)d'
        prefix_template += NORMAL

        return prefix_template

