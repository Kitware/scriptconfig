# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import glob
import six
import ubelt as ub
from . import smartcast


class Value(ub.NiceRepr):
    """
    You may set any item in the config's default to an instance of this class.
    Using this class allows you to declare the desired default value as well as
    the type that the value should be (Used when parsing sys.argv).

    Attributes:
        value (object): A float, int, etc...
        type (Type): the "type" of the value. This is usually used if the
            value specified is not the type that `self.value` would usually
            be set to.

    Example:
        >>> self = Value(None, type=float)
        >>> print('self.value = {!r}'.format(self.value))
        self.value = None
        >>> self.update('3.3')
        >>> print('self.value = {!r}'.format(self.value))
        self.value = 3.3
    """

    # hack to work around isinstance with IPython %autoreload magic
    __scfg_class__ = 'Value'

    def __init__(self, value=None, type=None):
        self.value = None
        self.type = type
        self.update(value)

    def __nice__(self):
        return '{!r}: {!r}'.format(self.type, self.value)

    def update(self, value):
        if value is None:
            self.value = value
        elif isinstance(value, six.string_types):
            self.value = smartcast.smartcast(value, self.type)
        else:
            self.value = value


class Path(Value):
    """
    Note this is mean to be used only with kwil.Config.
    It does NOT represent a pathlib object.
    """
    def __init__(self, value=None):
        super(Path, self).__init__(value, str)

    def update(self, value):
        if isinstance(value, six.string_types):
            self.value = ub.expandpath(value)
        else:
            self.value = value


class PathList(Value):
    """
    Can be specified as a list or as a globstr

    FIXME:
        will fail if there are any commas in the path name

    Example:
        >>> from os.path import join
        >>> path = ub.modname_to_modpath('torch', hide_init=True)
        >>> globstr = join(path, '*.py')
        >>> PathList(globstr)
        >>> PathList('/a,/b')
        >>> PathList(['/a', '/b'])
    """
    def update(self, value=None):
        if isinstance(value, six.string_types):
            paths1 = sorted(glob.glob(ub.truepath(value)))
            paths2 = smartcast.smartcast(value)
            if paths1:
                self.value = paths1
            else:
                self.value = paths2
        else:
            self.value = value
