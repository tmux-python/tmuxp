# -*- coding: utf8 -*-
# flake8: NOQA
import sys

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
PYMINOR = sys.version_info[1]
PYPATCH = sys.version_info[2]

_identity = lambda x: x


if PY3 and PYMINOR >= 7:
    breakpoint = breakpoint
else:
    import pdb

    breakpoint = pdb.set_trace


if PY2:
    unichr = unichr
    text_type = unicode
    string_types = (str, unicode)
    integer_types = (int, long)
    from urllib import urlretrieve

    text_to_native = lambda s, enc: s.encode(enc)

    iterkeys = lambda d: d.iterkeys()
    itervalues = lambda d: d.itervalues()
    iteritems = lambda d: d.iteritems()

    from itertools import imap, izip

    import ConfigParser as configparser
    import cPickle as pickle
    from cStringIO import StringIO as BytesIO
    from StringIO import StringIO

    range_type = xrange

    cmp = cmp

    input = raw_input
    from string import lower as ascii_lowercase

    import urlparse

    exec('def reraise(tp, value, tb=None):\n raise tp, value, tb')

    def implements_to_string(cls):
        cls.__unicode__ = cls.__str__
        cls.__str__ = lambda x: x.__unicode__().encode('utf-8')
        return cls

    def console_to_str(s):
        return s.decode('utf_8')


else:
    unichr = chr
    text_type = str
    string_types = (str,)
    integer_types = (int,)

    text_to_native = lambda s, enc: s

    iterkeys = lambda d: iter(d.keys())
    itervalues = lambda d: iter(d.values())
    iteritems = lambda d: iter(d.items())

    import configparser
    import pickle
    from io import BytesIO, StringIO

    izip = zip
    imap = map
    range_type = range

    cmp = lambda a, b: (a > b) - (a < b)

    input = input
    import urllib.parse as urllib
    import urllib.parse as urlparse
    from string import ascii_lowercase
    from urllib.request import urlretrieve

    console_encoding = sys.__stdout__.encoding

    implements_to_string = _identity

    def console_to_str(s):
        """ From pypa/pip project, pip.backwardwardcompat. License MIT. """
        try:
            return s.decode(console_encoding)
        except UnicodeDecodeError:
            return s.decode('utf_8')

    def reraise(tp, value, tb=None):
        if value.__traceback__ is not tb:
            raise (value.with_traceback(tb))
        raise value


number_types = integer_types + (float,)
