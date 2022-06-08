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
        value (object):
            A float, int, etc...

        type (Type):
            the "type" of the value. This is usually used if the value
            specified is not the type that `self.value` would usually be set
            to.

        parsekw (dict):
            kwargs for to argparse add_argument

        position (None | int):
            if an integer, then we allow this value to be a positional argument
            in the argparse CLI. Note, that values with the same position index
            will cause conflicts. Also note: positions indexes should start
            from 1.

        isflag (bool, default=False): if True, args will be parsed as booleans

        alias (List[str]):
            other long names (that will be prefixed with '--') that will be
            accepted by the argparse CLI.

        short_alias (List[str]):
            other short names (that will be prefixed with '-') that will be
            accepted by the argparse CLI.

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

    def __init__(self, value=None, type=None, help=None, choices=None,
                 position=None, isflag=False, nargs=None, alias=None,
                 required=False, short_alias=None):
        self.value = None
        self.type = type
        self.alias = alias
        self.position = position
        self.isflag = isflag
        self.parsekw = {
            'help': help,
            'type': type,
            'choices': choices,
            'nargs': nargs,
        }
        self.required = required
        self.short_alias = short_alias
        self.update(value)

    def __nice__(self):
        return '{!r}: {!r}'.format(self.type, self.value)

    def update(self, value):
        self.value = self.cast(value)

    def cast(self, value):
        if isinstance(value, six.string_types):
            value = smartcast.smartcast(value, self.type)
        return value


class Path(Value):
    """
    Note this is mean to be used only with scriptconfig.Config.
    It does NOT represent a pathlib object.
    """
    def __init__(self, value=None, help=None, alias=None):
        super(Path, self).__init__(value, str, help=help, alias=alias)

    def cast(self, value):
        if isinstance(value, six.string_types):
            value = ub.expandpath(value)
        return value


class PathList(Value):
    """
    Can be specified as a list or as a globstr

    FIXME:
        will fail if there are any commas in the path name

    Example:
        >>> from os.path import join
        >>> path = ub.modname_to_modpath('scriptconfig', hide_init=True)
        >>> globstr = join(path, '*.py')
        >>> # Passing in a globstr is accepted
        >>> assert len(PathList(globstr).value) > 0
        >>> # Smartcast should separate these
        >>> assert len(PathList('/a,/b').value) == 2
        >>> # Passing in a list is accepted
        >>> assert len(PathList(['/a', '/b']).value) == 2
    """

    def cast(self, value=None):
        if isinstance(value, six.string_types):
            paths1 = sorted(glob.glob(ub.expandpath(value)))
            paths2 = smartcast.smartcast(value)
            if paths1:
                value = paths1
            else:
                value = paths2
        return value
