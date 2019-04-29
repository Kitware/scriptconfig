# -*- coding: utf-8 -*-
"""
Write simple configs and update from CLI, kwargs, and/or json.

The ``scriptconfig`` provides a simple way to make configurable scripts using a
combination of config files, command line arguments, and simple Python keyword
arguments. A script config object is defined by creating a subclass of
``Config`` with a ``default`` dict class attribute. An instance of a custom
``Config`` object will behave similar a dictionary, but with a few
conviniences.

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
    >>> config_fpath = '/tmp/foo'
    >>> open(config_fpath, 'w').write('{"num": 3}')
    >>> config.load(config_fpath, cmdline=False)
    >>> assert config['num'] == 3
    >>> # It is possbile to load only from CLI by setting cmdline=True
    >>> # or by setting it to a custom sys.argv
    >>> config.load(cmdline=['--num=4'])
    >>> assert config['num'] == 4
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


TODO
    - [X] Rename
    - [ ] Handle Nested Configs?
    - [X] Write docs?
    - [ ] Public Release?
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import ubelt as ub
import yaml
import six
import copy
import io
import json
import numpy as np
from .dict_like import DictLike
from .file_like import FileLike
from .value import Value
from .smartcast import smartcast


def scfg_isinstance(item, cls):
    """
    use instead isinstance for scfg types when reloading
    """
    # Note: it is safe to simply use isinstance(item, cls) when
    # not reloading
    if hasattr(item, '__scfg_class__')  and hasattr(cls, '__scfg_class__'):
        return item.__scfg_class__ == cls.__scfg_class__
    else:
        return isinstance(item, cls)


class Config(ub.NiceRepr, DictLike):
    """
    A configuration that can be specified by commandline args, a yaml config
    file, and / or a in-code dictionary. To use, define a class variable named
    "default" and assing it to a dict of default values. You can also use
    special `Value` classes to denote types. You can also define a method
    `normalize`, to postprocess the arguments after this class receives them.

    Example:
        >>> # Inherit from `Config` and assign `default`
        >>> class MyConfig(Config):
        >>>     default = {
        >>>         'option1': Value((1, 2, 3), tuple),
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
            default (dict, optional): overrides the class defaults
            cmdline (bool or List[str]): if True, then command line arguments
                will overwrite any specified or default values. If cmdline is
                True, then sys.argv is used otherwise cmdline is parsed.
                Defaults to False.
        """
        self._data = None
        self._default = ub.odict()
        if hasattr(self, 'default'):
            # allow for class attributes to specify the default
            self._default.update(self.default)
        self.load(data, cmdline=cmdline, default=default)

    @classmethod
    def demo(cls):
        """
        CommandLine:
            xdoctest -m scriptconfig.config Config.demo

        Example:
            >>> from scriptconfig.config import *
            >>> self = Config.demo()
            >>> print('self = {}'.format(self))
            self = <MyConfig({...'option1': ...}...)...>...
            >>> self.argparse().print_help()
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
        """
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
            elif isinstance(item, np.ndarray):
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
        value = self._data[key]
        if scfg_isinstance(value, Value):
            value = value.value
        return value

    def setitem(self, key, value):
        if key not in self._data:
            raise Exception('Cannot add keys to ScriptConfig objects')
        if scfg_isinstance(value, Value):
            self._data[key] = value
        else:
            current = self._data[key]
            if scfg_isinstance(current, Value):
                current.update(value)
            else:
                self._data[key] = value

    def delitem(self, key):
        raise Exception('cannot delete items from a config')

    def keys(self):
        return self._data.keys()

    def update_defaults(self, default):
        self._default.update(default)

    def load(self, data=None, cmdline=False, mode=None, default=None):
        """
        Updates the default configuration from a given data source.

        Any option can be overwritten via the command line if `cmdline` is
        truthy.

        Args:
            data (str or dict):
                Either a path to a yaml / json file or a config dict

            cmdline (bool | List[str]): if truthy then the command line
                will be parsed and specified values will be overwritten.  Can
                either pass `cmdline` as a `List[str]` to specify a custom
                `argv` or `cmdline=True` to indicate that we should parse
                `sys.argv`.
        """
        if default:
            self.update_defaults(default)

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
                user_config = yaml.load(file)
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

        # should command line flags be allowed to overwrite data?
        if cmdline is True or ub.iterable(cmdline):
            argv = cmdline if ub.iterable(cmdline) else None
            self._read_argv(argv=argv)

        self.normalize()
        return self

    def _read_argv(self, argv=None, special_options=True):
        # TODO: warn about any unused flags
        parser = self.argparse()

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

        ns = parser.parse_known_args(argv)[0].__dict__

        if special_options:

            config_fpath = ns.pop('config', None)

            dump_fpath = ns.pop('dump', None)
            do_dumps = ns.pop('dumps', None)

            if config_fpath is not None:
                self.load(config_fpath, cmdline=False)

        for key, value in ns.items():
            current = self._data[key]
            if not isinstance(current, Value):
                # smartcast non-valued params from commandline
                value = smartcast(value)
            if value is not None:
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

    def normalize(self):
        """ overloadable function called after each load """
        pass

    def dump(self, stream=None, mode=None):
        """
        Write configuration file to a file or stream
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
        return self.dump(mode=mode)

    def argparse(self, parser=None):
        """
        construct or update an argparse.ArgumentParser CLI parser

        CommandLine:
            xdoctest -m scriptconfig.config Config.argparse

        Example:
            >>> # You can now make instances of this class
            >>> self = Config.demo()
            >>> parser = self.argparse()
            >>> parser.print_help()
        """
        import argparse
        if parser is None:
            parser = argparse.ArgumentParser(
                description='argparse CLI autogenerated by scriptconfig',
                formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            )

        for key, value in self._default.items():
            argkw = {}
            argkw['help'] = '<todo>'
            if isinstance(self._data[key], Value):
                # Use the metadata in the Value class to enhance argparse
                _value = self._data[key]
                argkw.update(_value.parsekw)
                value = _value.value
            argkw['default'] = value
            parser.add_argument('--' + key, **argkw)

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
