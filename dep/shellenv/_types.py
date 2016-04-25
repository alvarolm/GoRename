# coding: utf-8
from __future__ import unicode_literals, division, absolute_import, print_function

import sys


if sys.version_info < (3,):
    str_cls = unicode  # noqa
    byte_cls = str

else:
    str_cls = str
    byte_cls = bytes


def type_name(value):
    """
    Returns a user-readable name for the type of an object

    :param value:
        A value to get the type name of

    :return:
        A unicode string of the object's type name
    """

    cls = value.__class__
    if cls.__module__ in set(['builtins', '__builtin__']):
        return cls.__name__
    return '%s.%s' % (cls.__module__, cls.__name__)
