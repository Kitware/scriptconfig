# -*- coding: utf-8 -*-
"""
Write simple configs and update from CLI, kwargs, and/or json.

The ``scriptconfig`` provides a simple way to make configurable scripts using a
combination of config files, command line arguments, and simple Python keyword
arguments. A script config object is defined by creating a subclass of
``Config`` with a ``default`` dict class attribute. An instance of a custom
``Config`` object will behave similar a dictionary, but with a few
conveniences.

To get started lets consider some example usage:

Example:
    >>> import scriptconfig as scfg
    >>> # In its simplest incarnation, the config class specifies default values.
    >>> # For each configuration parameter.
    >>> class ExampleConfig(scfg.Config):
    >>>     default = {
    >>>         'num': 1,
    >>>         'mode': 'bar',
    >>>         'ignore': ['baz', 'biz'],
    >>>     }
    >>> # Creating an instance, starts using the defaults
    >>> config = ExampleConfig()
    >>> # Typically you will want to update default from a dict or file.  By
    >>> # specifying cmdline=True you denote that it is ok for the contents of
    >>> # `sys.argv` to override config values. Here we pass a dict to `load`.
    >>> kwargs = {'num': 2}
    >>> config.load(kwargs, cmdline=False)
    >>> assert config['num'] == 2
    >>> # The `load` method can also be passed a json/yaml file/path.
    >>> import tempfile
    >>> config_fpath = tempfile.mktemp()
    >>> open(config_fpath, 'w').write('{"num": 3}')
    >>> config.load(config_fpath, cmdline=False)
    >>> assert config['num'] == 3
    >>> # It is possbile to load only from CLI by setting cmdline=True
    >>> # or by setting it to a custom sys.argv
    >>> config.load(cmdline=['--num=4', '--mode' ,'fiz'])
    >>> assert config['num'] == 4
    >>> assert config['mode'] == 'fiz'
    >>> # You can also just use the command line string itself
    >>> config.load(cmdline='--num=4 --mode fiz')
    >>> assert config['num'] == 4
    >>> assert config['mode'] == 'fiz'
    >>> # Note that using `config.load(cmdline=True)` will just use the
    >>> # contents of sys.argv

Ignore:
    >>> class ExampleConfig(scfg.Config):
    >>>     default = {
    >>>         'num': 1,
    >>>         'mode': 'bar',
    >>>         'mode2': scfg.Value('bar', str),
    >>>         'ignore': ['baz', 'biz'],
    >>>     }
    >>> config = ExampleConfig()
    >>> # smartcast can handle lists as long as there are no spaces
    >>> config.load(cmdline=['--ignore=spam,eggs'])
    >>> assert config['ignore'] == ['spam', 'eggs']
    >>> # Note that the Value type can influence how data is parsed
    >>> config.load(cmdline=['--mode=spam,eggs', '--mode2=spam,eggs'])

    >>> # FIXME: We need make parsing lists a bit more intuitive
    >>> class ExampleConfig(scfg.Config):
    >>>     default = {
    >>>         'item1': [],
    >>>         'item2': scfg.Value([], list),
    >>>         'item3': scfg.Value([]),
    >>>     }
    >>> config = ExampleConfig()
    >>> # IDEALLY BOTH CASES SHOULD WORK
    >>> config.load(cmdline=['--item1', 'spam', 'eggs', '--item2', 'spam', 'eggs', '--item3', 'spam', 'eggs'])
    >>> print(ub.repr2(config.asdict(), nl=1))
    >>> config.load(cmdline=['--item1=spam,eggs', '--item2=spam,eggs', '--item3=spam,eggs'])
    >>> print(ub.repr2(config.asdict(), nl=1))

TODO:
    - [ ] Handle Nested Configs?
    - [ ] Integrate with Hyrda
    - [ ] Dataclass support
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import ubelt as ub
import yaml
import six
import copy
import io
import json
from scriptconfig.dict_like import DictLike
from scriptconfig import smartcast
from scriptconfig.file_like import FileLike
from scriptconfig.value import Value

__all__ = ['Config', 'define']


# def _is_autoreload_enabled():
#     """
#     Detect if IPython has autoreloaded this module
#     https://stackoverflow.com/questions/63469147/programmatically-check-for-and-disable-ipython-autoreload-extension
#     """
#     try:
#         __IPYTHON__
#     except NameError:
#         return False
#     else:
#         from IPython import get_ipython
#         ipy = get_ipython()
#         return ipy.magics_manager.magics['line']['autoreload'].__self__._reloader.enabled


def scfg_isinstance(item, cls):
    """
    use instead isinstance for scfg types when reloading

    Args:
        item (object): instance to check
        cls (type): class to check against

    Returns:
        bool
    """
    # Note: it is safe to simply use isinstance(item, cls) when
    # not reloading
    if hasattr(item, '__scfg_class__')  and hasattr(cls, '__scfg_class__'):
        return item.__scfg_class__ == cls.__scfg_class__
    else:
        return isinstance(item, cls)


def define(default={}, name=None):
    """
    Alternate method for defining a custom Config type
    """
    import uuid
    if name is None:
        hashid = str(uuid.uuid4()).replace('-', '_')
        name = 'Config_{}'.format(hashid)
    from textwrap import dedent
    vals = {}
    code = dedent(
        '''
        import scriptconfig as scfg
        class {name}(scfg.Config):
            pass
        '''.strip('\n').format(name=name))
    exec(code, vals)
    cls = vals[name]
    return cls


class Config(ub.NiceRepr, DictLike):
    """
    Base class for custom configuration objects

    A configuration that can be specified by commandline args, a yaml config
    file, and / or a in-code dictionary. To use, define a class variable named
    "default" and assing it to a dict of default values. You can also use
    special `Value` classes to denote types. You can also define a method
    `normalize`, to postprocess the arguments after this class receives them.

    Basic usage is as follows.

    Create a class that herits from this class.

    Assign the "default" class-level variable as a dictionary of options

    The keys of this dictionary must be command line friendly strings.

    The values of the "defaults dictionary" can be literal values or
    instances of the :class:`scriptconfig.Value` class, which allows
    for specification of default values, type information, help strings,
    and aliases.

    You may also implement normalize (function with that takes no args and
    has no return) to postprocess your results after initialization.

    When creating an instance of the class the defaults variable is used
    to make a dictionary-like object. You can override defaults by
    specifying the ``data`` keyword argument to either a file path or
    another dictionary. You can also specify ``cmdline=True`` to allow
    the contents of ``sys.argv`` to influence the values of the new
    object.

    An instance of the config class behaves like a dictinary, except that
    you cannot set keys that do not already exist (as specified in the
    defaults dict).

    Key Methods:

        * dump - dump a json representation to a file

        * dumps - dump a json representation to a string

        * argparse - create an :class:`argparse.ArgumentParser` object that is defined by the defaults of this config.

        * load - rewrite the values based on a filepath, dictionary, or command line contents.

    Attributes:
        _data : this protected variable holds the raw state of the config
            object and is accessed by the dict-like

        _default : this protected variable maintains the default values for
            this config.

        epilog (str): A class attribute that if specified will add an epilog
            section to the help text.

    Example:
        >>> # Inherit from `Config` and assign `default`
        >>> import scriptconfig as scfg
        >>> class MyConfig(scfg.Config):
        >>>     default = {
        >>>         'option1': scfg.Value((1, 2, 3), tuple),
        >>>         'option2': 'bar',
        >>>         'option3': None,
        >>>     }
        >>> # You can now make instances of this class
        >>> config1 = MyConfig()
        >>> config2 = MyConfig(default=dict(option1='baz'))
    """
    __scfg_class__ = 'Config'

    def __init__(self, data=None, default=None, cmdline=False):
        """
        Args:
            data (object): filepath, dict, or None

            default (dict, default=None): overrides the class defaults

            cmdline (bool | List[str] | str | dict)
                If False, then no command line information is used.
                If True, then sys.argv is parsed and used.
                If a list of strings that used instead of sys.argv.
                If a string, then that is parsed using shlex and used instead
                    of sys.argv.
                If a dictionary grants fine grained controls over the args
                passed to :func:`Config._read_argv`. Can contain:
                    * strict (bool): defaults to False
                    * argv (List[str]): defaults to None
                    * special_options (bool): defaults to True
                    * autocomplete (bool): defaults to False
                Defaults to False.
        """
        # The _data attribute holds
        self._data = None
        self._default = ub.odict()
        cls_default = getattr(self, 'default', None)
        if cls_default:
            # allow for class attributes to specify the default
            self._default.update(cls_default)
        self.load(data, cmdline=cmdline, default=default)

    @classmethod
    def demo(cls):
        """
        Create an example config class for test cases

        CommandLine:
            xdoctest -m scriptconfig.config Config.demo
            xdoctest -m scriptconfig.config Config.demo --cli --option1 fo

        Example:
            >>> from scriptconfig.config import *
            >>> self = Config.demo()
            >>> print('self = {}'.format(self))
            self = <MyConfig({...'option1': ...}...)...>...
            >>> self.argparse().print_help()
            >>> # xdoc: +REQUIRES(--cli)
            >>> self.load(cmdline=True)
            >>> print(ub.repr2(dict(self), nl=1))
        """
        import scriptconfig as scfg
        class MyConfig(scfg.Config):
            default = {
                'option1': scfg.Value('bar', help='an option'),
                'option2': scfg.Value((1, 2, 3), tuple, help='another option'),
                'option3': None,
                'option4': 'foo',
                'discrete': scfg.Value(None, choices=['a', 'b', 'c']),
                'apath': scfg.Path(help='a path'),
            }
        self = MyConfig()
        return self

    def __json__(self):
        """
        Creates a JSON serializable representation of this config object.

        Raises:
            TypeError: if any non-builtin python objects without a __json__
                method are encountered.

        Returns:
            dict
        """
        try:
            import numpy
        except ImportError:
            numpy = None
        data = self.asdict()

        BUILTIN_SCALAR_TYPES = (str, int, float, complex)
        BUILTIN_VECTOR_TYPES = (set, frozenset, list, tuple)

        def _rectify(item):
            if item is None:
                return item
            elif isinstance(item, BUILTIN_SCALAR_TYPES):
                return item
            elif isinstance(item, BUILTIN_VECTOR_TYPES):
                return [_rectify(v) for v in item]
            elif numpy is not None and isinstance(item, numpy.ndarray):
                return item.tolist()
            elif isinstance(item, ub.odict):
                return ub.odict([
                    (_rectify(k), _rectify(v)) for k, v in item.items()
                ])
            elif isinstance(item, dict):
                return ub.odict(sorted([
                    (_rectify(k), _rectify(v)) for k, v in item.items()
                ]))
            else:
                if hasattr(item, '__json__'):
                    return item.__json__()
                else:
                    raise TypeError(
                        'Unknown JSON serialization for type {!r}'.format(type(item)))
        return _rectify(data)

    def __nice__(self):
        return str(self.asdict())

    def getitem(self, key):
        """
        Dictionary-like method to get the value of a key.

        Args:
            key (str): the key

        Returns:
            VT : the associated value
        """
        value = self._data[key]
        if scfg_isinstance(value, Value):
            value = value.value
        return value

    def setitem(self, key, value):
        """
        Dictionary-like method to set the value of a key.

        Args:
            key (str): the key
            value (VT): the new value
        """
        if key not in self._data:
            raise Exception('Cannot add keys to ScriptConfig objects')
        if scfg_isinstance(value, Value):
            # If the new item is a Value object simply overwrite the old one
            self._data[key] = value
        else:
            template = self.default[key]
            if scfg_isinstance(template, Value):
                # If the new value is raw data, and we have a underlying Value
                # object update it.
                self._data[key] = template.cast(value)
            else:
                # If we don't have an underlying Value object simply set the
                # raw data.
                self._data[key] = value

    def delitem(self, key):
        raise Exception('cannot delete items from a config')

    def keys(self):
        """
        Dictionary-like keys method

        Yields:
            KT
        """
        return self._data.keys()

    def update_defaults(self, default):
        """
        Update the instance-level default values

        Args:
            default (dict): new defaults
        """
        self._default.update(default)

    def load(self, data=None, cmdline=False, mode=None, default=None):
        """
        Updates the default configuration from a given data source.

        Any option can be overwritten via the command line if ``cmdline`` is
        truthy.

        Args:
            data (PathLike | dict):
                Either a path to a yaml / json file or a config dict

            cmdline (bool | List[str] | str | dict)
                If False, then no command line information is used.
                If True, then sys.argv is parsed and used.
                If a list of strings that used instead of sys.argv.
                If a string, then that is parsed using shlex and used instead
                    of sys.argv.
                If a dictionary grants fine grained controls over the args
                passed to :func:`Config._read_argv`. Can contain:
                    * strict (bool): defaults to False
                    * argv (List[str]): defaults to None
                    * special_options (bool): defaults to True
                    * autocomplete (bool): defaults to False
                Defaults to False.

            mode (str | None):
                Either json or yaml.

            cmdline (bool | List[str] | str):
                If False, then no command line information is used.
                If True, then sys.argv is parsed and used.
                If a list of strings that used instead of sys.argv.
                If a string, then that is parsed using shlex and used instead
                of sys.argv. Defaults to False.

            default (dict | None):
                updated defaults

        Example:
            >>> # Test load works correctly in cmdline True and False mode
            >>> import scriptconfig as scfg
            >>> class MyConfig(scfg.Config):
            >>>     default = {
            >>>         'src': scfg.Value(None, help=('some help msg')),
            >>>     }
            >>> data = {'src': 'hi'}
            >>> self = MyConfig(data=data, cmdline=False)
            >>> assert self['src'] == 'hi'
            >>> self = MyConfig(default=data, cmdline=True)
            >>> assert self['src'] == 'hi'
            >>> # In 0.5.8 and previous src fails to populate!
            >>> # This is because cmdline=True overwrites data with defaults
            >>> self = MyConfig(data=data, cmdline=True)
            >>> assert self['src'] == 'hi'

        Example:
            >>> # Test load works correctly in strict mode
            >>> import scriptconfig as scfg
            >>> class MyConfig(scfg.Config):
            >>>     default = {
            >>>         'src': scfg.Value(None, help=('some help msg')),
            >>>     }
            >>> data = {'src': 'hi'}
            >>> cmdlinekw = {
            >>>     'strict': True,
            >>>     'argv': '--src=hello',
            >>> }
            >>> self = MyConfig(data=data, cmdline=cmdlinekw)
            >>> cmdlinekw = {
            >>>     'strict': True,
            >>>     'special_options': False,
            >>>     'argv': '--src=hello --extra=arg',
            >>> }
            >>> import pytest
            >>> with pytest.raises(SystemExit):
            >>>     self = MyConfig(data=data, cmdline=cmdlinekw)

        Example:
            >>> # Test load works correctly with required
            >>> import scriptconfig as scfg
            >>> class MyConfig(scfg.Config):
            >>>     default = {
            >>>         'src': scfg.Value(None, help=('some help msg'), required=True),
            >>>     }
            >>> cmdlinekw = {
            >>>     'strict': True,
            >>>     'special_options': False,
            >>>     'argv': '',
            >>> }
            >>> import pytest
            >>> with pytest.raises(Exception):
            ...   self = MyConfig(cmdline=cmdlinekw)
        """
        if default:
            self.update_defaults(default)

        # Maybe this shouldn't be a deep copy?
        _default = copy.deepcopy(self._default)

        if mode is None:
            if isinstance(data, six.string_types):
                if data.lower().endswith('.json'):
                    mode = 'json'
        if mode is None:
            # Default to yaml
            mode = 'yaml'

        if data is None:
            user_config = {}
        elif isinstance(data, six.string_types) or hasattr(data, 'readable'):
            with FileLike(data, 'r') as file:
                user_config = yaml.load(file, Loader=yaml.SafeLoader)
            user_config.pop('__heredoc__', None)  # ignore special heredoc key
        elif isinstance(data, dict):
            user_config = data
        elif scfg_isinstance(data, Config):
            user_config = data.asdict()
        else:
            raise TypeError(
                'Expected path or dict, but got {}'.format(type(data)))

        # check for unknown values
        unknown_keys = set(user_config) - set(_default)
        if unknown_keys:
            raise KeyError('Unknown data options {}'.format(unknown_keys))

        self._data = _default.copy()
        self.update(user_config)

        if isinstance(cmdline, six.string_types):
            # allow specification using the actual command line arg string
            import shlex
            import os
            cmdline = shlex.split(os.path.expandvars(cmdline))

        if cmdline or ub.iterable(cmdline):
            # TODO: if user_config is specified, then we should probably not
            # override any values in user_config with the defaults? The CLI
            # should override them IF they exist on in sys.argv, but not if
            # they don't?
            read_argv_kwargs = {
                'special_options': True,
                'strict': False,
                'autocomplete': False,
                'argv': None,
            }
            if isinstance(cmdline, dict):
                read_argv_kwargs.update(cmdline)
            elif ub.iterable(cmdline) or isinstance(cmdline, str):
                read_argv_kwargs['argv'] = cmdline
            self._read_argv(**read_argv_kwargs)

        if 1:
            # Check that all required variables are not the same as defaults
            # Probably a way to make this check nicer
            for k, v in self._default.items():
                if scfg_isinstance(v, Value):
                    if v.required:
                        if self[k] == v.value:
                            raise Exception('Required variable {!r} still has default value'.format(k))
        self.normalize()
        return self

    def _read_argv(self, argv=None, special_options=True, strict=False, autocomplete=False):
        """
        Example:
            >>> import scriptconfig as scfg
            >>> class MyConfig(scfg.Config):
            >>>     description = 'my CLI description'
            >>>     default = {
            >>>         'src':  scfg.Value(['foo'], position=1, nargs='+'),
            >>>         'dry':  scfg.Value(False),
            >>>         'approx':  scfg.Value(False, isflag=False, alias=['a1', 'a2']),
            >>>     }
            >>> self = MyConfig()
            >>> # xdoctest: +REQUIRES(PY3)
            >>> # Python2 argparse does a hard sys.exit instead of raise
            >>> import sys
            >>> if sys.version_info[0:2] < (3, 6):
            >>>     # also skip on 3.5 because of dict ordering
            >>>     import pytest
            >>>     pytest.skip()
            >>> self._read_argv(argv='')
            >>> print('self = {}'.format(self))
            >>> self = MyConfig()
            >>> self._read_argv(argv='--src [,]')
            >>> print('self = {}'.format(self))
            self = <MyConfig({'src': ['foo'], 'dry': False, 'approx': False})>
            self = <MyConfig({'src': [], 'dry': False, 'approx': False})>


            >>> self = MyConfig()
            >>> self._read_argv(argv='p1 p2 p3')
            >>> print('self = {}'.format(self))
            >>> self = MyConfig()
            >>> self._read_argv(argv='--src=p4,p5,p6!')
            >>> print('self = {}'.format(self))
            >>> self = MyConfig()
            >>> self._read_argv(argv='p1 p2 p3 --src=p4,p5,p6!')
            >>> print('self = {}'.format(self))
            self = <MyConfig({'src': ['p1', 'p2', 'p3'], 'dry': False, 'approx': False})>
            self = <MyConfig({'src': ['p4', 'p5', 'p6!'], 'dry': False, 'approx': False})>
            self = <MyConfig({'src': ['p4', 'p5', 'p6!'], 'dry': False, 'approx': False})>

            >>> self = MyConfig()
            >>> self._read_argv(argv='p1')
            >>> print('self = {}'.format(self))
            >>> self = MyConfig()
            >>> self._read_argv(argv='--src=p4')
            >>> print('self = {}'.format(self))
            >>> self = MyConfig()
            >>> self._read_argv(argv='p1 --src=p4')
            >>> print('self = {}'.format(self))
            self = <MyConfig({'src': ['p1'], 'dry': False, 'approx': False})>
            self = <MyConfig({'src': ['p4'], 'dry': False, 'approx': False})>
            self = <MyConfig({'src': ['p4'], 'dry': False, 'approx': False})>

            >>> special_options = False
            >>> parser = self.argparse(special_options=special_options)
            >>> parser.print_help()
            >>> x = parser.parse_known_args()

        Ignore:
            >>> # Weird cases
            >>> self = MyConfig()
            >>> self._read_argv(argv='--src=[p4,p5,p6!] f of')
            >>> print('self = {}'.format(self))

            >>> self = MyConfig()
            >>> self._read_argv(argv='--src=p4,')
            >>> print('self = {}'.format(self))

            >>> self = MyConfig()
            >>> self._read_argv(argv='a b --src p4 p5 p6!')
            >>> print('self = {}'.format(self))

            >>> self = MyConfig()
            >>> self._read_argv(argv='--src=p4 p5 p6!')
            >>> print('self = {}'.format(self))

            >>> self = MyConfig()
            >>> self._read_argv(argv='p1 p2 p3!')
            >>> print('self = {}'.format(self))
        """
        # print('---')
        if isinstance(argv, six.string_types):
            import shlex
            argv = shlex.split(argv)

        # TODO: warn about any unused flags
        parser = self.argparse(special_options=special_options)

        if autocomplete:
            # TODO: make this work
            # print(f'autocomplete={autocomplete}')
            try:
                import argcomplete
            except ImportError:
                raise
            else:
                argcomplete.autocomplete(parser)

        if strict:
            ns = parser.parse_args(argv).__dict__
        else:
            ns = parser.parse_known_args(argv)[0].__dict__

        if special_options:
            config_fpath = ns.pop('config', None)
            dump_fpath = ns.pop('dump', None)
            do_dumps = ns.pop('dumps', None)

        # We might remove code under this if using action casting proves to be
        # stable.
        RELY_ON_ACTION_SMARTCAST = True

        # First load argparse defaults in first
        _not_given = set(ns.keys()) - parser._explicitly_given
        # print('_not_given = {!r}'.format(_not_given))
        # print('parser._explicitly_given = {!r}'.format(parser._explicitly_given))
        for key in _not_given:
            value = ns[key]
            # NOTE: this implementation is messy and needs refactor.
            # Currently the .default, ._default, and ._data attributes can all
            # be Value objects, but this gets messy when the "default"
            # constructor argument is used. We should refactor so _data and
            # _default only store the raw current values, post-casting.
            if key not in self.default:
                # probably an alias
                continue

            if not RELY_ON_ACTION_SMARTCAST:
                # Old way that we did smartcast. Hopefully the action class
                # takes care of this.
                template = self.default[key]
                # print('template = {!r}'.format(template))
                if not isinstance(template, Value):
                    # smartcast non-valued params from commandline
                    value = smartcast.smartcast(value)
                else:
                    value = template.cast(value)

            # if value is not None:
            self[key] = value

        # Then load config file defaults
        if special_options:
            if config_fpath is not None:
                self.load(config_fpath, cmdline=False)

        # Finally load explicit CLI values
        for key in parser._explicitly_given:
            value = ns[key]

            if not RELY_ON_ACTION_SMARTCAST:
                # Old way that we did smartcast. Hopefully the action class
                # takes care of this.

                template = self.default[key]

                # print('value = {!r}'.format(value))
                # print('template = {!r}'.format(template))
                if not isinstance(template, Value):
                    # smartcast non-valued params from commandline
                    value = smartcast.smartcast(value)

            # if value is not None:
            self[key] = value

        self.normalize()

        if special_options:
            import sys
            if dump_fpath or do_dumps:
                if dump_fpath:
                    # Infer config format from the extension
                    if dump_fpath.lower().endswith('.json'):
                        mode = 'json'
                    elif dump_fpath.lower().endswith('.yaml'):
                        mode = 'yaml'
                    else:
                        mode = 'yaml'
                    text = self.dumps(mode=mode)
                    with open(dump_fpath, 'w') as file:
                        file.write(text)

                if do_dumps:
                    # Always use yaml to dump to stdout
                    text = self.dumps(mode='yaml')
                    print(text)

                sys.exit(1)
        return self

    def normalize(self):
        """ overloadable function called after each load """
        pass

    def dump(self, stream=None, mode=None):
        """
        Write configuration file to a file or stream

        Args:
            stream (FileLike | None): the stream to write to
            mode (str | None): can be 'yaml' or 'json' (defaults to 'yaml')
        """
        # import six
        # if isinstance(stream, six.string_types):
        #     _stream_path = stream
        #     print('Writing to _stream_path = {!r}'.format(_stream_path))
        #     _stream = stream = open(_stream_path, 'w')
        # else:
        #     _stream_path = None
        # try:
        if mode is None:
            mode = 'yaml'
        if mode == 'yaml':
            def order_rep(dumper, data):
                return dumper.represent_mapping('tag:yaml.org,2002:map', data.items(), flow_style=False)
            yaml.add_representer(ub.odict, order_rep)
            return yaml.safe_dump(dict(self.items()), stream)
        elif mode == 'json':
            json_text = json.dumps(ub.odict(self.items()), indent=4)  # NOQA
            return json_text
        else:
            raise KeyError(mode)
            return yaml.safe_dump(dict(self.items()), stream)
        # except Exception:
        #     raise
        # finally:
        #     if _stream_path is not None:
        #         _stream_path
        #         _stream.close()

    def dumps(self, mode=None):
        """
        Write the configuration to a text object and return it

        Args:
            mode (str | None): can be 'yaml' or 'json' (defaults to 'yaml')

        Returns:
            str - the configuration as a string
        """
        return self.dump(mode=mode)

    def _parserkw(self):
        """
        Generate the kwargs for making a new argparse.ArgumentParser
        """
        import argparse

        prog = getattr(self, 'prog', None)

        description = getattr(self, 'description', None)
        if description is None:
            description = self.__class__.__doc__
        if description is None:
            description = 'argparse CLI generated by scriptconfig'
        if description is not None:
            description = ub.codeblock(description)

        epilog = getattr(self, 'epilog', None)
        if epilog is not None:
            epilog = ub.codeblock(epilog)

        if prog is None:
            prog = self.__class__.__name__

        class RawDescriptionDefaultsHelpFormatter(
                argparse.RawDescriptionHelpFormatter,
                argparse.ArgumentDefaultsHelpFormatter):
            pass

        parserkw = dict(
            prog=prog,
            description=description,
            epilog=epilog,
            # formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            # formatter_class=argparse.RawDescriptionHelpFormatter,
            formatter_class=RawDescriptionDefaultsHelpFormatter,
        )
        return parserkw

    # TODO:
    @classmethod
    def port_argparse(cls, parser, name='MyConfig', style='orig'):
        """
        Create an instance from an existing argparse.

        Args:
            parser (argparse.ArgumentParser):
                existing argparse parser we want to port

        Returns:
            str :
                code to create a scriptconfig object that should work similarly
                to the existing argparse object.

        Note:
            The correctness of this function is not guarenteed.  This only
            works perfectly in simple cases, but in complex cases it may not
            produce 1-to-1 results, however it will provide a useful starting
            point.


        Example:
            >>> import scriptconfig as scfg
            >>> import argparse
            >>> parser = argparse.ArgumentParser()
            >>> parser.add_argument('-t', '--true_dataset', '--test_dataset', help='path to the groundtruth dataset', required=True)
            >>> parser.add_argument('-p', '--pred_dataset', help='path to the predicted dataset', required=True)
            >>> parser.add_argument('--eval_dpath', help='path to dump results')
            >>> parser.add_argument('--draw_curves', default='auto', help='flag to draw curves or not')
            >>> parser.add_argument('--draw_heatmaps', default='auto', help='flag to draw heatmaps or not')
            >>> parser.add_argument('--score_space', default='video', help='can score in image or video space')
            >>> parser.add_argument('--workers', default='auto', help='number of parallel scoring workers')
            >>> parser.add_argument('--draw_workers', default='auto', help='number of parallel drawing workers')
            >>> text = scfg.Config.port_argparse(parser, name='PortedConfig')
            >>> print(text)
            >>> # Make an instance of the ported class
            >>> vals = {}
            >>> exec(text, vals)
            >>> cls = vals['PortedConfig']
            >>> self = cls(data={'true_dataset': 1, 'pred_dataset': 1})
            >>> recon = self.argparse()
            >>> print('recon._actions = {}'.format(ub.repr2(recon._actions, nl=1)))
        """
        # raise NotImplementedError
        # This logic should be able to be used statically or dynamically
        # to transition argparse to ScriptConfig code.
        if style == 'orig':
            recon_str = [
                'import scriptconfig as scfg',
                '',
                'class ' + name + '(scfg.Config):',
                '    """',
                ub.indent(parser.description or ''),
                '    """',
                '    default = {',
            ]
        elif style == 'dataconf':
            recon_str = [
                'import scriptconfig as scfg',
                '',
                '@scfg.dataconf',
                'class ' + name + ':',
                '    """',
                ub.indent(parser.description or ''),
                '    """',
            ]
        else:
            raise KeyError(style)

        def normalize_option_str(s):
            return s.lstrip('-').replace('-', '_')

        for action in parser._actions:
            import re
            long_prefix_pat = re.compile('--[^-].*')
            short_prefix_pat = re.compile('-[^-].*')

            key = action.dest
            if key == 'help':
                # scriptconfig takes care of help for us
                continue

            long_option_strings = [
                s for s in action.option_strings
                if long_prefix_pat.match(s)
            ]
            short_option_strings = [
                s for s in action.option_strings
                if short_prefix_pat.match(s)
            ]

            alias = ub.oset(normalize_option_str(s)
                            for s in long_option_strings)
            alias = list(alias - {key})

            short_alias = ub.oset(normalize_option_str(s)
                                  for s in short_option_strings)
            short_alias = list(short_alias - {key})

            if style == 'dataconf':
                indent = ' ' * 4
            else:
                indent = ' ' * 8
            value_args = [
                repr(action.default),
            ]

            value_kw = {
                'type': '{}'.format(action.type.__name__) if action.type else None,
                'alias': '{}'.format(alias) if alias else None,
                'short_alias': '{}'.format(short_alias) if short_alias else None,
                'required': '{}'.format(action.required) if action.required else None,
                'choices': '{}'.format(action.choices) if action.choices else None,
                'help': '{!r}'.format(action.help) if action.help else None,
            }
            HACKS = 1
            if HACKS:
                if value_kw['type'] == 'smartcast':
                    value_kw.pop('type')
                if action.help and len(action.help) > 40:
                    import textwrap
                    wrapped = ub.indent('\n'.join(textwrap.wrap(action.help, width=60)), ' ' * 4)
                    block = ub.codeblock(
                        """
                        ub.paragraph(
                            '''
                        {}
                            ''')
                        """
                    ).format(wrapped)
                    value_kw['help'] = ub.indent(block, ' ' * 8).lstrip()
                    # "ub.paragraph(\n'''\n{}\n''')".format(ub.indent(action.help, ' ' * 16))
            value_args.extend(['{}={}'.format(k, v) for k, v in value_kw.items() if v is not None])

            if 0:
                val_body = ', '.join(value_args)
            else:
                if 0:
                    arg_indent = '{}    '.format(indent)
                    arg_prefix = '\n{}'.format(arg_indent)
                    arg_sep = ',{}'.format(arg_prefix)
                    arg_tail = '\n{}'.format(indent)
                    val_body = arg_prefix + arg_sep.join(value_args) + arg_tail
                else:
                    val_body = ', '.join(value_args)

            if style == 'orig':
                recon_str.append("{}'{}': scfg.Value({}),".format(indent, key, val_body))
            elif style ==  'dataconf':
                recon_str.append("{}{} = scfg.Value({})".format(indent, key, val_body))
            else:
                raise KeyError(style)

        if style == 'orig':
            recon_str.append('    }')
        elif style ==  'dataconf':
            ...
        else:
            raise KeyError(style)
        text = '\n'.join(recon_str)
        if 0:
            try:
                import black
                text = black.format_str(
                    text, mode=black.Mode(string_normalization=True)
                )
            except Exception:
                pass
        return text

    @property
    def namespace(self):
        """
        Access a namespace like object for compatibility with argparse
        """
        from argparse import Namespace
        return Namespace(**dict(self))

    def to_omegaconf(self):
        """
        Creates an omegaconfig version of this.

        Returns:
            omegaconf.OmegaConf:

        Example:
            >>> # xdoctest: +REQUIRES(module:omegaconf)
            >>> import scriptconfig
            >>> self = scriptconfig.Config.demo()
            >>> oconf = self.to_omegaconf()
        """
        from omegaconf import OmegaConf
        oconf = OmegaConf.create(self.to_dict())
        return oconf

    def argparse(self, parser=None, special_options=False):
        """
        construct or update an argparse.ArgumentParser CLI parser

        Args:
            parser (None | argparse.ArgumentParser): if specified this
                parser is updated with options from this config.

            special_options (bool, default=False):
                adds special scriptconfig options, namely: --config, --dumps,
                and --dump.

        Returns:
            argparse.ArgumentParser : a new or updated argument parser

        CommandLine:
            xdoctest -m scriptconfig.config Config.argparse:0
            xdoctest -m scriptconfig.config Config.argparse:1

        TODO:
            A good CLI spec for lists might be

            # In the case where ``key`` ends with and ``=``, assume the list is
            # given as a comma separated string with optional square brakets at
            # each end.

            --key=[f]

            # In the case where ``key`` does not end with equals and we know
            # the value is supposd to be a list, then we consume arguments
            # until we hit the next one that starts with '--' (which means
            # that list items cannot start with -- but they can contains
            # commas)

        FIXME:

            * In the case where we have an nargs='+' action, and we specify
              the option with an `=`, and then we give position args after it
              there is no way to modify behavior of the action to just look at
              the data in the string without modifying the ArgumentParser
              itself. The action object has no control over it. For example
              `--foo=bar baz biz` will parse as `[baz, biz]` which is really
              not what we want. We may be able to overload ArgumentParser to
              fix this.

        Example:
            >>> # You can now make instances of this class
            >>> import scriptconfig
            >>> self = scriptconfig.Config.demo()
            >>> parser = self.argparse()
            >>> parser.print_help()
            >>> # xdoctest: +REQUIRES(PY3)
            >>> # Python2 argparse does a hard sys.exit instead of raise
            >>> ns, extra = parser.parse_known_args()

        Example:
            >>> # You can now make instances of this class
            >>> import scriptconfig as scfg
            >>> class MyConfig(scfg.Config):
            >>>     description = 'my CLI description'
            >>>     default = {
            >>>         'path1':  scfg.Value(None, position=1, alias='src'),
            >>>         'path2':  scfg.Value(None, position=2, alias='dst'),
            >>>         'dry':  scfg.Value(False, isflag=True),
            >>>         'approx':  scfg.Value(False, isflag=False, alias=['a1', 'a2']),
            >>>     }
            >>> self = MyConfig()
            >>> special_options = True
            >>> parser = None
            >>> parser = self.argparse(special_options=special_options)
            >>> parser.print_help()
            >>> self._read_argv(argv=['objection', '42', '--path1=overruled!'])
            >>> print('self = {!r}'.format(self))

        Example:
            >>> # Test required option
            >>> import scriptconfig as scfg
            >>> class MyConfig(scfg.Config):
            >>>     description = 'my CLI description'
            >>>     default = {
            >>>         'path1':  scfg.Value(None, position=1, alias='src'),
            >>>         'path2':  scfg.Value(None, position=2, alias='dst'),
            >>>         'dry':  scfg.Value(False, isflag=True),
            >>>         'important':  scfg.Value(False, required=True),
            >>>         'approx':  scfg.Value(False, isflag=False, alias=['a1', 'a2']),
            >>>     }
            >>> self = MyConfig(data={'important': 1})
            >>> special_options = True
            >>> parser = None
            >>> parser = self.argparse(special_options=special_options)
            >>> parser.print_help()
            >>> self._read_argv(argv=['objection', '42', '--path1=overruled!', '--important=1'])
            >>> print('self = {!r}'.format(self))

        Ignore:
            >>> self._read_argv(argv=['hi','--path1=foobar'])
            >>> self._read_argv(argv=['hi', 'hello', '--path1=foobar'])
            >>> self._read_argv(argv=['hi', 'hello', '--path1=foobar', '--help'])
            >>> self._read_argv(argv=['--path1=foobar', '--path1=baz'])
            >>> print('self = {!r}'.format(self))
        """
        import argparse

        if parser is None:
            parserkw = self._parserkw()
            parser = argparse.ArgumentParser(**parserkw)

        # Use custom action used to mark which values were explicitly set on
        # the commandline
        parser._explicitly_given = set()

        parent = self

        class ParseAction(argparse.Action):
            def __init__(self, *args, **kwargs):
                # required = kwargs.pop('required', False)
                super(ParseAction, self).__init__(*args, **kwargs)
                # with script config nothing should be required by default
                # (unless specified) all positional arguments should have
                # keyword arg variants Setting required=False here will prevent
                # positional args from erroring if they are not specified. I
                # dont think there are other side effects, but we should make
                # sure that is actually the case.
                self.required = required
                self.required = False  # hack

                if self.type is None:
                    # Is this the right place to put this?
                    def _mytype(value):
                        key = self.dest
                        template = parent.default[key]
                        if not isinstance(template, Value):
                            # smartcast non-valued params from commandline
                            value = smartcast.smartcast(value)
                        else:
                            value = template.cast(value)
                        return value

                    self.type = _mytype

                # print('self.type = {!r}'.format(self.type))

            def __call__(action, parser, namespace, values, option_string=None):
                # print('CALL action = {!r}'.format(action))
                # print('option_string = {!r}'.format(option_string))
                # print('values = {!r}'.format(values))

                if isinstance(values, list) and len(values):
                    # We got a list of lists, which we hack into a flat list
                    if isinstance(values[0], list):
                        import itertools as it
                        values = list(it.chain(*values))

                setattr(namespace, action.dest, values)
                if not hasattr(parser, '_explicitly_given'):
                    # We might be given a subparser / parent parser
                    # and not the original one we created.
                    parser._explicitly_given = set()
                parser._explicitly_given.add(action.dest)

        # IRC: this ensures each key has a real Value class
        _metadata = {
            key: self._data[key]
            for key, value in self._default.items()
            if isinstance(self._data[key], Value)
        }  # :type: Dict[str, Value]
        _positions = {k: v.position for k, v in _metadata.items()
                      if v.position is not None}
        if _positions:
            if ub.find_duplicates(_positions.values()):
                raise Exception('two values have the same position')
            _keyorder = ub.oset(ub.argsort(_positions))
            _keyorder |= (ub.oset(self._default) - _keyorder)
        else:
            _keyorder = list(self._default.keys())

        def _add_arg(parser, name, argkw, positional, isflag, required=False,
                     aliases=None, short_aliases=None):
            _argkw = argkw.copy()

            long_names = [name] + list((aliases or []))
            short_names = list(short_aliases or [])

            if positional:
                parser.add_argument(name, **_argkw)

            _argkw['dest'] = name

            if isflag:
                # Can we support both flag and setitem methods of cli
                # parsing?
                if not isinstance(_argkw.get('default', None), bool):
                    raise ValueError('can only use isflag with bools')
                _argkw.pop('type', None)
                _argkw.pop('choices', None)
                _argkw.pop('action', None)
                _argkw.pop('nargs', None)
                _argkw['dest'] = name

                _argkw_true = _argkw.copy()
                _argkw_true['action'] = 'store_true'

                _argkw_false = _argkw.copy()
                _argkw_false['action'] = 'store_false'
                _argkw_false.pop('help', None)

                short_pos_option_strings = ['-' + n for n in short_names]
                pos_option_strings = ['--' + n for n in long_names]
                neg_option_strings = ['--no-' + n for n in long_names]
                parser.add_argument(*short_pos_option_strings,
                                    *pos_option_strings, **_argkw_true)
                parser.add_argument(*neg_option_strings, **_argkw_false)
            else:
                short_option_strings = ['-' + n for n in short_names]
                long_option_strings = ['--' + n for n in long_names]
                option_strings = short_option_strings + long_option_strings
                parser.add_argument(*option_strings, required=required, **_argkw)

        for key, value in self._data.items():
            # key: str
            # value: Any | Value
            name = key
            argkw = {}
            argkw['help'] = ''
            positional = None
            isflag = False
            required = False
            if name in _metadata:
                # Use the metadata in the Value class to enhance argparse
                _value = _metadata[name]
                argkw.update(_value.parsekw)
                required = _value.required
                value = _value.value
                isflag = _value.isflag
                positional = _value.position
            else:
                _value = value if scfg_isinstance(value, Value) else None
                # _value = value if isinstance(value, Value) else None

            if not argkw['help']:
                argkw['help'] = '<undocumented>'

            argkw['default'] = value
            argkw['action'] = ParseAction

            aliases = None
            short_aliases = None
            if _value is not None:
                aliases = _value.alias
                short_aliases = _value.short_alias
            if isinstance(aliases, str):
                aliases = [aliases]
            if isinstance(short_aliases, str):
                short_aliases = [short_aliases]

            _add_arg(parser, name, argkw, positional, isflag,
                     required=required, aliases=aliases,
                     short_aliases=short_aliases)

        if special_options:
            parser.add_argument('--config', default=None, help=ub.codeblock(
                '''
                special scriptconfig option that accepts the path to a on-disk
                configuration file, and loads that into this {!r} object.
                ''').format(self.__class__.__name__))

            parser.add_argument('--dump', default=None, help=ub.codeblock(
                '''
                If specified, dump this config to disk.
                ''').format(self.__class__.__name__))

            parser.add_argument('--dumps', action='store_true', help=ub.codeblock(
                '''
                If specified, dump this config stdout
                ''').format(self.__class__.__name__))

        return parser


class DataInterchange:
    """
    Seraializes / Loads / Dumps YAML or json

    UNUSED:
    """
    def __init__(self, mode=None, strict=None):
        self.mode = mode
        self.strict = strict

    def _rectify_mode(self, data):
        if self.mode is None:
            if isinstance(data, six.string_types):
                if data.lower().endswith('.json'):
                    self.mode = 'json'
                elif data.lower().endswith('.yml'):
                    self.mode = 'yml'
                else:
                    if self.strict:
                        raise Exception('unknown mode')
        if self.mode is None:
            # Default to yaml
            if self.strict:
                raise Exception('unknown mode')
            else:
                self.mode = 'yaml'

    @classmethod
    def load(cls, fpath):
        self = cls()
        self._rectify_mode(fpath)
        if self.mode == 'yml':
            with open(fpath, 'r') as file:
                data = yaml.load(file)
        elif self.mode == 'json':
            with open(fpath, 'r') as file:
                data = json.load(file)
        return data

    @classmethod
    def dumps(cls, data, mode='yml'):
        self = cls(mode=mode)
        if self.mode == 'yml':
            def order_rep(dumper, data):
                return dumper.represent_mapping('tag:yaml.org,2002:map', data.items(), flow_style=False)
            yaml.add_representer(ub.odict, order_rep)
            stream = io.StringIO()
            yaml.safe_dump(dict(self.items()), stream)
            stream.seek(0)
            text = stream.read()
        elif self.mode == 'json':
            text = json.dumps(ub.odict(self.items()), indent=4)
        return text


__notes__ = """

export _ARC_DEBUG=1
pip install argcomplete
activate-global-python-argcomplete --dest=$HOME/.bash_completion.d --user
eval "$(register-python-argcomplete xdev)"
complete -r xdev



"""
