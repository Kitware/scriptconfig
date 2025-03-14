"""
Write simple configs and update from CLI, kwargs, and/or json.

The ``scriptconfig`` provides a simple way to make configurable scripts using a
combination of config files, command line arguments, and simple Python keyword
arguments. A script config object is defined by creating a subclass of
``Config`` with a ``default`` dict class attribute. An instance of a custom
``Config`` object will behave similar a dictionary, but with a few
conveniences.

Note:
    * This class implements the old-style legacy Config class, new applications
      should favor using DataConfig instead, which has simpler boilerplate.

To get started lets consider some example usage:

Example:
    >>> import scriptconfig as scfg
    >>> # In its simplest incarnation, the config class specifies default values.
    >>> # For each configuration parameter.
    >>> class ExampleConfig(scfg.Config):
    >>>     __default__ = {
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
    >>> # It is possible to load only from CLI by setting cmdline=True
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
    >>>     __default__ = {
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
    >>>     __default__ = {
    >>>         'item1': [],
    >>>         'item2': scfg.Value([], list),
    >>>         'item3': scfg.Value([]),
    >>>     }
    >>> config = ExampleConfig()
    >>> # IDEALLY BOTH CASES SHOULD WORK
    >>> config.load(cmdline=['--item1', 'spam', 'eggs', '--item2', 'spam', 'eggs', '--item3', 'spam', 'eggs'])
    >>> print(ub.urepr(config, nl=1))
    >>> config.load(cmdline=['--item1=spam,eggs', '--item2=spam,eggs', '--item3=spam,eggs'])
    >>> print(ub.urepr(config, nl=1))

TODO:
    - [ ] Handle Nested Configs?
    - [ ] Integrate with Hyrda
    - [x] Dataclass support - See DataConfig
"""
import ubelt as ub
import itertools as it
from collections import OrderedDict
from scriptconfig import _ubelt_repr_extension
from scriptconfig import smartcast
from scriptconfig.dict_like import DictLike
from scriptconfig.file_like import FileLike
from scriptconfig.value import Value
# from scriptconfig.util.util_class import class_or_instancemethod

__all__ = ['Config', 'define']

__docstubs__ = """
from typing import Any

KT = Any
omegaconf: Any
OmegaConf: object
"""


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

    Example:
        >>> from scriptconfig.config import define, Value
        >>> cls = define({'k1': Value('v1'), 'k2': 'v2'}, 'MyConfig')
        >>> instance = cls()
        >>> assert instance.to_dict() == {'k1': 'v1', 'k2': 'v2'}
        >>> print(instance)
        <MyConfig({'k1': 'v1', 'k2': 'v2'})>
    """
    import uuid
    from textwrap import dedent
    if name is None:
        hashid = str(uuid.uuid4()).replace('-', '_')
        name = 'Config_{}'.format(hashid)
    vals = {'default': default}
    code = dedent(
        '''
        import scriptconfig as scfg
        class {name}(scfg.Config):
            __default__ = default
        '''.strip('\n').format(name=name))
    exec(code, vals)
    cls = vals[name]
    return cls


class MetaConfig(type):
    """
    A metaclass for Config to help make usage between Config and DataConfig
    consistent.

    Ensures that class attributes are mirrored:
        * __default__ mirrors default
        * __post_init__ mirrors normalize
    """

    @staticmethod
    def __new__(mcls, name, bases, namespace, *args, **kwargs):
        # print(f'MetaConfig.__new__ called: {mcls=} {name=} {bases=} {namespace=} {args=} {kwargs=}')

        if 'default' in namespace and '__default__' not in namespace:
            # Ensure the user updates to the newer "__default__" paradigm
            this_default = namespace['__default__'] = namespace['default']
            ub.schedule_deprecation(
                'scriptconfig', 'default', f'class attribute of {name}',
                migration='Use __default__ instead',
                deprecate='0.7.6', error='0.10.0', remove='1.0.0',
            )

        HANDLE_INHERITENCE = 1
        if HANDLE_INHERITENCE:
            # Handle inheritance, add in defaults from base classes
            # Not sure this is exactly correct. Experimental.
            this_default = namespace.get('__default__', {})
            if this_default is None:
                this_default = {}
            this_default = ub.udict(this_default)

            inheritence_default = {}
            for base in bases:
                if hasattr(base, '__default__'):
                    inheritence_default.update(base.__default__)
                    # unseen = base.__default__ - this_default
                    # this_default.update(unseen)
            inheritence_default.update(this_default)
            this_default = inheritence_default
            namespace['__default__'] = namespace['default'] = this_default

        if '__default__' in namespace and 'default' not in namespace:
            # Backport to the older non-dunder __default__
            namespace['default'] = namespace['__default__']

        if 'normalize' in namespace and '__post_init__' not in namespace:
            # Ensure the newer __post_init__ is specified
            namespace['__post_init__'] = namespace['normalize']
            ub.schedule_deprecation(
                'scriptconfig', 'normalize', f'class attribute of {name}',
                migration='Use __post_init__ instead',
                deprecate='0.7.6', error='0.10.0', remove='1.0.0',
            )

        if '__post_init__' in namespace and 'normalize' not in namespace:
            # Backport to the older non-dunder normalize
            namespace['normalize'] = namespace['__post_init__']

        # print('FINAL namespace = {}'.format(ub.urepr(namespace, nl=2)))
        cls = super().__new__(mcls, name, bases, namespace, *args, **kwargs)
        return cls


class Config(ub.NiceRepr, DictLike, metaclass=MetaConfig):
    """
    Base class for custom configuration objects

    A configuration that can be specified by commandline args, a yaml config
    file, and / or a in-code dictionary. To use, define a class variable named
    ``__default__`` and passing it to a dict of default values. You can also
    use special ``Value`` classes to denote types. You can also define a method
    ``__post_init__``, to postprocess the arguments after this class receives
    them.

    Basic usage is as follows.

    Create a class that inherits from this class.

    Assign the "__default__" class-level variable as a dictionary of options

    The keys of this dictionary must be command line friendly strings.

    The values of the "defaults dictionary" can be literal values or
    instances of the :class:`scriptconfig.Value` class, which allows
    for specification of default values, type information, help strings,
    and aliases.

    You may also implement ``__post_init__`` (function with that takes no args
    and has no return) to postprocess your results after initialization.

    When creating an instance of the class the defaults variable is used
    to make a dictionary-like object. You can override defaults by
    specifying the ``data`` keyword argument to either a file path or
    another dictionary. You can also specify ``cmdline=True`` to allow
    the contents of ``sys.argv`` to influence the values of the new
    object.

    An instance of the config class behaves like a dictionary, except that
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

    SeeAlso:
        :class:`scriptconfig.DataConfig`

    Example:
        >>> # Inherit from `Config` and assign `__default__`
        >>> import scriptconfig as scfg
        >>> class MyConfig(scfg.Config):
        >>>     __default__ = {
        >>>         'option1': scfg.Value((1, 2, 3), tuple),
        >>>         'option2': 'bar',
        >>>         'option3': None,
        >>>     }
        >>> # You can now make instances of this class
        >>> config1 = MyConfig()
        >>> config2 = MyConfig(default=dict(option1='baz'))
    """
    __scfg_class__ = 'Config'
    __default__ = {}
    # __allow_newattr__ = False

    def __init__(self, data=None, default=None, cmdline=False,
                 _dont_call_post_init=False):
        """
        Args:
            data (object): filepath, dict, or None

            default (dict | None): overrides the class defaults

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

        Note:
            Avoid setting ``cmdline`` parameter here.  Instead prefer
            to use the ``cli`` classmethod to create a command line
            aware config instance..
        """
        # The _data attribute holds
        self._data = None
        self._default = OrderedDict()
        cls_default = getattr(self, '__default__', getattr(self, 'default', None))
        if cls_default:
            # allow for class attributes to specify the default
            self._default.update(cls_default)
        self._alias_map = None
        self.load(data, cmdline=cmdline, default=default,
                  _dont_call_post_init=_dont_call_post_init)

    @classmethod
    def cli(cls, data=None, default=None, argv=None, strict=True,
            cmdline=True, autocomplete='auto', special_options=True,
            transition_helpers=True, verbose=False):
        """
        Create a command-line aware config instance.

        Calls the original "load" way of creating non-dataclass config objects.
        This may be refactored in the future.

        Args:
            data (dict | str | None):
                Values to update the configuration with. This can be a
                regular dictionary or a path to a yaml / json file.

            default (dict | None):
                Values to update the defaults with (not the actual
                configuration). Note: anything passed to default will be deep
                copied and can be updated by argv or data if it is specified.
                Generally prefer to pass directly to data instead.

            cmdline (bool):
                Defaults to True, which creates and uses an argparse object to
                interact with the command line. If set to False, then the
                argument parser is bypassed (useful for invoking a CLI
                programmatically with kwargs and ignoring sys.argv).
                NOTE: this will be deprecated in favor of "argv" in the future.

            argv (List[str] | None | bool):
                if specified as a list or string, ignore sys.argv and parse
                this instead. Otherwise,
                if True, then parse ``sys.argv``.
                if False, then ignore ``sys.argv``.

            strict (bool):
                if True use ``parse_args`` otherwise use ``parse_known_args``.
                Defaults to True.

            autocomplete (bool | str):
                if True try to enable argcomplete.

            transition_helpers (bool):
                if True, we perform special munging to help transition to new
                versions (e.g. cmdline->argv transition). This will cause
                issues if your config has a key named "cmdline", otherwise it
                is safe to keep on.

            special_options (bool, default=True):
                adds special scriptconfig options, namely: --config, --dumps,
                and --dump. In the future this default will change to False.

            verbose (bool | str):
                If true, then perform a rich print of the config after it is
                parsed. This is a convenience to reduce script boilerplate.
                If "auto", it will default to true in most cases, except when
                we can infer special behavior from the user-defined config via
                standard keys: verbose, quiet, and silent.

        Example:
            >>> import scriptconfig as scfg
            >>> class MyConfig(scfg.Config):
            >>>     __default__ = {
            >>>         'option1': scfg.Value((1, 2, 3), tuple),
            >>>         'option2': 'bar',
            >>>         'option3': None,
            >>>         'verbose': False,
            >>>     }
            >>> # You can now make instances of this class
            >>> config = MyConfig.cli(argv=False, verbose='auto')
            >>> config = MyConfig.cli(argv=False, data=dict(verbose=1), verbose='auto')
        """
        if transition_helpers and hasattr(data, 'pop'):
            argv = data.pop('cmdline', argv)  # helper for cmdline->argv transition
        if cmdline and argv is not None:
            cmdline = argv
        if default is None:
            default = {}
        # Note: hack to avoid calling  __post_init__ twice
        # We may want to refactor this to be a bit nicer.
        # Might require a major version bump and breaking of backwards compat.
        # avoid this. The thing that makes this difficult is the DataConfig
        # init method taking in keyword args corresponding to the config which
        # prevents adding clean options for control flow.
        self = cls(_dont_call_post_init=True)
        self.load(data, cmdline=cmdline, default=default, strict=strict,
                  autocomplete=autocomplete, special_options=special_options)

        if isinstance(verbose, str) and verbose == 'auto':
            verbose = self.get('verbose', verbose)
            verbose = not self.get('quiet', not verbose)
            verbose = not self.get('silent', not verbose)

        if verbose:
            try:
                import rich
                from rich.markup import escape
            except ImportError:
                print('config = ' + ub.urepr(self, nl=1))
            else:
                rich.print('config = ' + escape(ub.urepr(self, nl=1)))
        return self

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
            self = <DemoConfig({...'option1': ...}...)...>...
            >>> self.argparse().print_help()
            >>> # xdoc: +REQUIRES(--cli)
            >>> self.load(cmdline=True)
            >>> print(ub.urepr(self, nl=1))
        """
        import scriptconfig as scfg
        class DemoConfig(scfg.Config):
            """
            This was generated by scriptconfig.Config.demo
            """
            __default__ = {
                'option1': scfg.Value('bar', help='an option'),
                'option2': scfg.Value((1, 2, 3), tuple, help='another option'),
                'option3': None,
                'option4': 'foo',
                'discrete': scfg.Value(None, choices=['a', 'b', 'c']),
                'apath': scfg.Path(help='a path'),
            }
        self = DemoConfig()
        return self

    def __json__(self):
        """
        Creates a JSON serializable representation of this config object.

        Raises:
            TypeError: if any non-builtin python objects without a __json__
                method are encountered.

        Returns:
            dict

        Example:
            >>> self = Config.demo()
            >>> self.__json__()
            >>> self['option1'] = {1, 2, 3}
            >>> self['option2'] = {(1, 2): 'fds'}
            >>> self.__json__()
        """
        try:
            import numpy
        except ImportError:
            numpy = None
        data = self.asdict()

        BUILTIN_SCALAR_TYPES = (str, int, float, complex)
        BUILTIN_VECTOR_TYPES = (set, frozenset, list, tuple)

        # The walker method should be more efficient.
        walker = ub.IndexableWalker(data, list_cls=BUILTIN_VECTOR_TYPES)
        for path, item in walker:
            if item is None or isinstance(item, BUILTIN_SCALAR_TYPES):
                ...
            elif isinstance(item, list):
                ...
            elif isinstance(item, (set, tuple)):
                walker[path] = list(item)
            elif numpy is not None and isinstance(item, numpy.ndarray):
                walker[path] = item.tolist()
            elif isinstance(item, OrderedDict):
                ...
            elif isinstance(item, dict):
                walker[path] = OrderedDict(sorted(item.items()))
            else:
                if hasattr(item, '__json__'):
                    return item.__json__()
                else:
                    raise TypeError(
                        'Unknown JSON serialization for type {!r}'.format(type(item)))
        return data

    def __nice__(self):
        return str(self.asdict())

    def getitem(self, key):
        """
        Dictionary-like method to get the value of a key.

        Args:
            key (str): the key

        Returns:
            Any : the associated value
        """
        try:
            value = self._data[key]
        except KeyError:
            # Attempt alias
            key = self._normalize_alias_key(key)
            value = self._data[key]

        if scfg_isinstance(value, Value):
            value = value.value
        return value

    def setitem(self, key, value):
        """
        Dictionary-like method to set the value of a key.

        Args:
            key (str): the key
            value (Any): the new value
        """
        if key not in self._data:
            key = self._normalize_alias_key(key)
            if key not in self._data:
                if not getattr(self, '__allow_newattr__', False):
                    raise Exception(
                        'Cannot add keys to scriptconfig.Config objects unless '
                        'self.__allow_newattr__ is True'
                    )
        if scfg_isinstance(value, Value):
            # If the new item is a Value object simply overwrite the old one
            self._data[key] = value
        else:
            template = self.__default__.get(key, None)
            if template is not None and scfg_isinstance(template, Value):
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
            str:
        """
        return self._data.keys()

    def update_defaults(self, default):
        """
        Update the instance-level default values

        Args:
            default (dict): new defaults
        """
        import copy
        default = self._normalize_alias_dict(default)

        # The user might pass raw values in which case we should keep the
        # metadata from the existing wrapped Values and just update the .value
        # attribute.
        for k, v in default.items():
            old_default = self._default[k]
            if scfg_isinstance(old_default, Value) and not scfg_isinstance(v, Value):
                new_default = copy.deepcopy(old_default)
                new_default.value = v
                default[k] = new_default

        self._default.update(default)
        self._alias_map = None

    def load(self, data=None, cmdline=False, mode=None, default=None,
             strict=False, autocomplete=False, _dont_call_post_init=False,
             special_options=True):
        """
        Updates the configuration from a given data source.

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
                DO NOT USE dictionary form. It is deprecated.
                If a dictionary grants fine grained controls over the args
                passed to :func:`Config._read_argv`. Can contain:
                    * strict (bool): defaults to False
                    * argv (List[str]): defaults to None
                    * special_options (bool): defaults to True
                    * autocomplete (bool): defaults to False
                Defaults to False.
                NOTE: will be deprecated renamed to "argv" in the future.

            mode (str | None):
                Either json or yaml.

            default (dict | None):
                updated defaults. Note: anything passed to default will be deep
                copied and can be updated by argv or data if it is specified.
                Generally prefer to pass directly to data instead.

            strict (bool):
                if True an error will be raised if the command line
                contains unknown arguments.

            autocomplete (bool):
                if True, attempts to use the autocomplete package if it is
                available if reading from sys.argv. Defaults to False.

            special_options (bool, default=False):
                adds special scriptconfig options, namely: --config, --dumps,
                and --dump. Prefer using this over cmdline.

        Note:
            if cmdline=True, this will create an argument parser.

        Example:
            >>> # Test load works correctly in cmdline True and False mode
            >>> import scriptconfig as scfg
            >>> class MyConfig(scfg.Config):
            >>>     __default__ = {
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
            >>> assert self['src'] == 'hi', f'Got: {self}'

        Example:
            >>> # Test load works correctly in strict mode
            >>> import scriptconfig as scfg
            >>> class MyConfig(scfg.Config):
            >>>     __default__ = {
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
            >>>     __default__ = {
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

        Example:
            >>> # Test load works correctly with alias
            >>> import scriptconfig as scfg
            >>> class MyConfig(scfg.Config):
            >>>     __default__ = {
            >>>         'opt1': scfg.Value(None),
            >>>         'opt2': scfg.Value(None, alias=['arg2']),
            >>>     }
            >>> config1 = MyConfig(data={'opt2': 'foo'})
            >>> assert config1['opt2'] == 'foo'
            >>> config2 = MyConfig(data={'arg2': 'bar'})
            >>> assert config2['opt2'] == 'bar'
            >>> assert 'arg2' not in config2
        """
        if default:
            self.update_defaults(default)

        # Maybe this shouldn't be a deep copy?
        import copy
        _default = copy.deepcopy(self._default)

        if mode is None:
            if isinstance(data, str):
                if data.lower().endswith('.json'):
                    mode = 'json'
        if mode is None:
            # Default to yaml
            mode = 'yaml'

        if data is None:
            user_config = {}
        elif isinstance(data, str) or hasattr(data, 'readable'):
            import yaml
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
        indirect_keys = set(user_config) - set(_default)
        if indirect_keys:
            # Check if unknown keys are aliases
            unknown_keys = []
            _alias_map = self._build_alias_map()
            for a in indirect_keys:
                if a in _alias_map:
                    k = _alias_map[a]
                    user_config[k] = user_config.pop(a)
                else:
                    unknown_keys.append(a)
            if unknown_keys:
                raise KeyError('Unknown data options {}'.format(unknown_keys))

        self._data = _default.copy()
        self.update(user_config)

        if isinstance(cmdline, str):
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
                'special_options': special_options,
                'strict': strict,
                'autocomplete': autocomplete,
                'argv': None,
            }
            if isinstance(cmdline, dict):
                ub.schedule_deprecation('scriptconfig', 'cmdline', 'parameter as a dictionary',
                                        migration='The API should expose any special params explicitly',
                                        deprecate='0.7.15', error='0.10.0', remove='1.0.0')
                read_argv_kwargs.update(cmdline)
            elif ub.iterable(cmdline) or isinstance(cmdline, str):
                read_argv_kwargs['argv'] = cmdline
            self._read_argv(**read_argv_kwargs)

        if not _dont_call_post_init:
            if 1:
                # Check that all required variables are not the same as defaults
                # Probably a way to make this check nicer
                for k, v in self._default.items():
                    if scfg_isinstance(v, Value):
                        if v.required:
                            if self[k] == v.value:
                                raise Exception('Required variable {!r} still has default value'.format(k))
            self.__post_init__()
        return self

    def _normalize_alias_key(self, key):
        """
        normalizes a single aliased key
        """
        if getattr(self, '_alias_map', None) is None:
            self._alias_map = self._build_alias_map()
        return self._alias_map.get(key, key)

    def _normalize_alias_dict(self, data):
        """
        Args:
            data (dict): dictionary with keys that could be aliases

        Returns:
            dict: keys are normalized to be primary keys.
        """
        if getattr(self, '_alias_map', None) is None:
            self._alias_map = self._build_alias_map()
        norm = {self._alias_map.get(k, k): v for k, v in data.items()}
        return norm

    def _build_alias_map(self):
        _alias_map = {}
        for k, v in self._default.items():
            alias = getattr(v, 'alias', None)
            if alias:
                if not ub.iterable(alias):
                    alias = [alias]
                for a in alias:
                    _alias_map[a] = k
        return _alias_map

    def _read_argv(self, argv=None, special_options=True, strict=False, autocomplete=False):
        """
        Example:
            >>> import scriptconfig as scfg
            >>> class MyConfig(scfg.Config):
            >>>     description = 'my CLI description'
            >>>     __default__ = {
            >>>         'src':  scfg.Value(['foo'], position=1, nargs='+'),
            >>>         'dry':  scfg.Value(False),
            >>>         'approx':  scfg.Value(False, isflag=True, alias=['a1', 'a2']),
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
            >>> self = MyConfig()
            >>> self._read_argv(argv='--src [,] --a1')
            >>> print('self = {}'.format(self))
            self = <MyConfig({'src': ['foo'], 'dry': False, 'approx': False})>
            self = <MyConfig({'src': [], 'dry': False, 'approx': False})>
            self = <MyConfig({'src': [], 'dry': False, 'approx': True})>

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

        Example:
            >>> import scriptconfig as scfg
            >>> import pytest
            >>> class EmptyConfig(scfg.Config):
            >>>     ...
            >>> self = EmptyConfig()
            >>> with pytest.raises(Exception) as ex:
            >>>     self._read_argv(argv=32132)

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
        if isinstance(argv, str):
            import shlex
            argv = shlex.split(argv)

        # TODO: warn about any unused flags
        parser = self.argparse(special_options=special_options)

        if autocomplete:
            try:
                import argcomplete as argcomplete_mod
            except ImportError:
                if autocomplete != 'auto':
                    raise
            else:
                argcomplete_mod.autocomplete(parser)

        try:
            if strict:
                ns = parser.parse_args(argv).__dict__
            else:
                ns = parser.parse_known_args(argv)[0].__dict__
        except (ValueError, TypeError) as ex:
            # For errors (like ValueError) where its probably a programmer
            # error and not a user error, give the debugger some information
            # about the scriptconfig object.
            from scriptconfig.util import util_exception
            # TODO: figure out argv that triggers a value error so we can add a test
            note = ub.codeblock(
                f'''
                Error while attempting to parse arguments in _read_argv

                Context:
                    argv = {argv!r}
                    special_options = {special_options!r}
                    strict = {strict!r}
                    autocomplete = {autocomplete!r}
                    self = {self!r}
                ''')
            print(note)
            ex = util_exception.add_exception_note(ex, note)
            raise ex

        special_ns_keys = ['config', 'dump', 'dumps']
        if special_options:
            special_ns = {k: ns.pop(k, None) for k in special_ns_keys}
        else:
            special_ns = {}

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
            # Currently the .__default__ .default, ._default, and ._data
            # attributes can all be Value objects, but this gets messy when the
            # "default" constructor argument is used. We should refactor so
            # _data and _default only store the raw current values,
            # post-casting.
            if key not in self.__default__:
                # probably an alias
                continue

            if not RELY_ON_ACTION_SMARTCAST:
                # Old way that we did smartcast. Hopefully the action class
                # takes care of this.
                template = self.__default__[key]
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
            config_fpath = special_ns['config']
            if config_fpath is not None:
                self.load(config_fpath, cmdline=False,
                          _dont_call_post_init=True)

        # Finally load explicit CLI values
        for key in parser._explicitly_given:
            if key not in special_ns:
                value = ns[key]

                if not RELY_ON_ACTION_SMARTCAST:
                    # Old way that we did smartcast. Hopefully the action class
                    # takes care of this.

                    template = self.__default__[key]

                    # print('value = {!r}'.format(value))
                    # print('template = {!r}'.format(template))
                    if not isinstance(template, Value):
                        # smartcast non-valued params from commandline
                        value = smartcast.smartcast(value)

                # if value is not None:
                self[key] = value

        # We dont want this here right?
        # self.__post_init__()

        if special_options:
            import sys
            dump_fpath = special_ns['dump']
            do_dumps = special_ns['dumps']
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

    def __post_init__(self):
        """ overloadable function called after each load """
        ...

    def dump(self, stream=None, mode=None):
        """
        Write configuration file to a file or stream

        Args:
            stream (FileLike | None): the stream to write to
            mode (str | None): can be 'yaml' or 'json' (defaults to 'yaml')
        """
        if mode is None:
            mode = 'yaml'
        if mode == 'yaml':
            import yaml
            def order_rep(dumper, data):
                return dumper.represent_mapping('tag:yaml.org,2002:map', data.items(), flow_style=False)
            yaml.add_representer(OrderedDict, order_rep)
            return yaml.safe_dump(dict(self.items()), stream)
        elif mode == 'json':
            import json
            json_text = json.dumps(OrderedDict(self.items()), indent=4)
            return json_text
        else:
            raise KeyError(mode)

    def dumps(self, mode=None):
        """
        Write the configuration to a text object and return it

        Args:
            mode (str | None): can be 'yaml' or 'json' (defaults to 'yaml')

        Returns:
            str - the configuration as a string
        """
        return self.dump(mode=mode)

    def __getattr__(self, key):
        # Handle aliasing of old "default" and new "__default__"
        if key == 'default' and hasattr(self, '__default__'):
            return self.__default__
        elif key == '__default__' and hasattr(self, 'default'):
            return self.default
        raise AttributeError(key)

    @property
    def _description(self):
        if hasattr(self, 'description'):
            ub.schedule_deprecation(
                'scriptconfig', 'description', 'attribute of Config classes',
                migration='Use __description__ or the docstring instead',
                deprecate='0.7.11', error='0.10.0', remove='1.0.0')

        description = getattr(self, '__description__',
                              getattr(self, 'description', None))
        if description is None:
            description = self.__class__.__doc__
        if description is None:
            import scriptconfig
            description = f'argparse CLI generated by scriptconfig {scriptconfig.__version__}'
        if description is not None:
            description = ub.codeblock(description)
        return description

    @property
    def _epilog(self):
        if hasattr(self, 'epilog'):
            ub.schedule_deprecation(
                'scriptconfig', 'epilog', 'attribute of Config classes',
                migration='Use __epilog__ instead',
                deprecate='0.7.11', error='0.10.0', remove='1.0.0')

        epilog = getattr(self, '__epilog__', getattr(self, 'epilog', None))
        if epilog is not None:
            epilog = ub.codeblock(epilog)
        return epilog

    @property
    def _prog(self):
        if hasattr(self, 'prog'):
            ub.schedule_deprecation(
                'scriptconfig', 'prog', 'attribute of Config classes',
                migration='Use __prog__ instead',
                deprecate='0.7.11', error='0.10.0', remove='1.0.0')
        prog = getattr(self, '__prog__', getattr(self, 'prog', None))
        if prog is None:
            prog = self.__class__.__name__
        return prog

    def _parserkw(self):
        """
        Generate the kwargs for making a new argparse.ArgumentParser
        """
        from scriptconfig import argparse_ext
        parserkw = dict(
            prog=self._prog,
            description=self._description,
            epilog=self._epilog,
            # formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            # formatter_class=argparse.RawDescriptionHelpFormatter,
            formatter_class=argparse_ext.RawDescriptionDefaultsHelpFormatter,
            # exit_on_error=False,
        )
        if hasattr(self, '__allow_abbrev__'):
            parserkw['allow_abbrev'] = self.__allow_abbrev__
        return parserkw

    def port_to_dataconf(self, style='dataconf'):
        """
        Helper that will write the code to express this config as a DataConfig.

        TODO: In the future perhaps rename to something that indicates we can
            write a code representation of this object in either config or data
            config style?

        CommandLine:
            xdoctest -m scriptconfig.config Config.port_to_dataconf

        Example:
            >>> import scriptconfig as scfg
            >>> self = scfg.Config.demo()
            >>> print(self.port_to_dataconf())
        """
        entries = []
        for key, value in self.__default__.items():
            if not scfg_isinstance(value, Value):
                value_kw = Value(value)._to_value_kw()
            else:
                value_kw = value._to_value_kw()
            entries.append((key, value_kw))
        description = self._description
        name = self.__class__.__name__
        text = self._write_code(entries, name, style, description)
        return text

    @classmethod
    def _write_code(self, entries, name='MyConfig', style='dataconf', description=None):

        if style == 'dataconf':
            indent = ' ' * 4
        else:
            indent = ' ' * 8

        if style == 'orig':
            recon_str = [
                'import ubelt as ub',
                'import scriptconfig as scfg',
                '',
                'class ' + name + '(scfg.Config):',
                '    """',
                ub.indent(description or ''),
                '    """',
                '    __default__ = {',
            ]
        elif style == 'dataconf':
            recon_str = [
                'import ubelt as ub',
                'import scriptconfig as scfg',
                '',
                'class ' + name + '(scfg.DataConfig):',
                '    """',
                ub.indent(description or ''),
                '    """',
            ]
        else:
            raise KeyError(style)

        for (key, value_kw) in entries:
            _value_kw = value_kw.copy()

            default = _value_kw.pop('default')
            value_args = [
                repr(default),
            ]
            value_args.extend(['{}={}'.format(k, repr(v)) for k, v in _value_kw.items() if v is not None])
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

    @classmethod
    def port_from_click(cls, click_main, name=None, style='dataconf'):
        """
        Prints scriptconfig code that roughly implements some click CLI.

        Args:
            click_main (click.core.Command): command to port

            name (str | None): the name of the new class, if None then
               uses the name of the CLI command.

            style (str): either dataconf or orig

        Returns:
            str : The code that roughly implements the config class.

        CommandLine:
            xdoctest -m scriptconfig.config Config.port_from_click

        Example:
            >>> # xdoctest: +REQUIRES(module:click)
            >>> from scriptconfig.config import *  # NOQA
            >>> import click
            >>> import scriptconfig as scfg
            >>> @click.command()
            >>> @click.option('--dataset', required=True, type=click.Path(exists=True), help='input dataset')
            >>> @click.option('--deployed', required=True, type=click.Path(exists=True), help='weights file')
            >>> @click.option('--key1', default=123, type=click.Path(exists=True), help='weights file')
            >>> @click.option('--key2', default='456', type=click.Path(exists=True), help='weights file')
            >>> def click_main(dataset, deployed):
            >>>     ...
            >>> text = scfg.Config.port_from_click(click_main)
            >>> print(text)
            import ubelt as ub
            import scriptconfig as scfg
            ...
            class click_main(scfg.DataConfig):
                ...
                argparse CLI generated by scriptconfig ...
                ...
                dataset = scfg.Value(None, required=True, help='input dataset')
                deployed = scfg.Value(None, required=True, help='weights file')
                key1 = scfg.Value(123, help='weights file')
                key2 = scfg.Value(456, help='weights file')
        """
        import click
        ctx = click.Context(click.Command(''))
        info_dict = click_main.to_info_dict(ctx)  # NOQA
        default = {}
        blocklist = {'help'}
        for param in info_dict['params']:
            if param['name'] in blocklist:
                continue
            default[param['name']] = Value(
                param['default'],
                required=param['required'],
                isflag=param['is_flag'], help=param['help'])
        if name is None:
            name = info_dict['name'].replace('-', '_')
        config_cls = define(default, name)
        instance = config_cls(_dont_call_post_init=True)
        return instance.port_to_dataconf(style=style)

    @classmethod
    def port_from_argparse(cls, parser, name='MyConfig', style='dataconf'):
        """
        Generate the corresponding scriptconfig code from an existing argparse
        instance.

        Args:
            parser (argparse.ArgumentParser):
                existing argparse parser we want to port
            name (str): the name of the config class
            style (str): either 'orig' or 'dataconf'

        Returns:
            str :
                code to create a scriptconfig object that should work similarly
                to the existing argparse object.

        Note:
            The correctness of this function is not guaranteed.  This only
            works perfectly in simple cases, but in complex cases it may not
            produce 1-to-1 results, however it will provide a useful starting
            point.

        TODO:
            - [X] Handle "store_true".
            - [ ] Argument groups.
            - [ ] Handle mutually exclusive groups

        Example:
            >>> import scriptconfig as scfg
            >>> import argparse
            >>> parser = argparse.ArgumentParser(description='my argparse')
            >>> parser.add_argument('pos_arg1')
            >>> parser.add_argument('pos_arg2', nargs='*')
            >>> parser.add_argument('-t', '--true_dataset', '--test_dataset', help='path to the groundtruth dataset', required=True)
            >>> parser.add_argument('-p', '--pred_dataset', help='path to the predicted dataset', required=True)
            >>> parser.add_argument('--eval_dpath', help='path to dump results')
            >>> parser.add_argument('--draw_curves', default='auto', help='flag to draw curves or not')
            >>> parser.add_argument('--score_space', default='video', help='can score in image or video space')
            >>> parser.add_argument('--workers', default='auto', help='number of parallel scoring workers')
            >>> parser.add_argument('--draw_workers', default='auto', help='number of parallel drawing workers')
            >>> group1 = parser.add_argument_group('mygroup1')
            >>> group1.add_argument('--group1_opt1', action='store_true')
            >>> group1.add_argument('--group1_opt2')
            >>> group2 = parser.add_argument_group()
            >>> group2.add_argument('--group2_opt1', action='store_true')
            >>> group2.add_argument('--group2_opt2')
            >>> mutex_group3 = parser.add_mutually_exclusive_group()
            >>> mutex_group3.add_argument('--mgroup3_opt1')
            >>> mutex_group3.add_argument('--mgroup3_opt2')
            >>> text = scfg.Config.port_from_argparse(parser, name='PortedConfig', style='dataconf')
            >>> print(text)
            >>> # Make an instance of the ported class
            >>> vals = {}
            >>> exec(text, vals)
            >>> cls = vals['PortedConfig']
            >>> self = cls(**{'true_dataset': 1, 'pred_dataset': 1})
            >>> recon = self.argparse()
            >>> print('recon._actions = {}'.format(ub.urepr(recon._actions, nl=1)))
        """
        entries = cls._values_from_argparse(parser)
        description = parser.description
        text = cls._write_code(entries, name, style, description)
        return text

    @classmethod
    def cls_from_argparse(cls, parser, name=None, description=None):
        """
        Create a full configuration class from an existing argparse parser.

        Args:
            parser (argparse.ArgumentParser):
                The parser we will use to dynamically create a scriptconfig class

            name (str): the name of the new class.
                If unspecified, the name will be ``"Dynamic" + cls.__name__``

            description (None | str):
                if specified override the description from the parser.

        Returns:
            Config: a subclass of the Config or DataConfig class.

        SeeAlso:
            :func:`Config.port_from_argparse` - like this function, but returns
                the text that could be executed to define the new class
                statically.  In constrat this creates the clas dynamically.

        CommandLine:
            xdoctest -m scriptconfig.config Config.cls_from_argparse

        Example:
            >>> import scriptconfig as scfg
            >>> import argparse
            >>> parser = argparse.ArgumentParser(description='my argparse')
            >>> parser.add_argument('pos_arg1')
            >>> parser.add_argument('pos_arg2', nargs='*')
            >>> parser.add_argument('-t', '--true_dataset', '--test_dataset', help='path to the groundtruth dataset', required=True)
            >>> parser.add_argument('-p', '--pred_dataset', help='path to the predicted dataset', required=True)
            >>> parser.add_argument('--eval_dpath', help='path to dump results')
            >>> parser.add_argument('--draw_curves', default='auto', help='flag to draw curves or not')
            >>> parser.add_argument('--score_space', default='video', help='can score in image or video space')
            >>> parser.add_argument('--workers', default='auto', help='number of parallel scoring workers')
            >>> parser.add_argument('--draw_workers', default='auto', help='number of parallel drawing workers')
            >>> group1 = parser.add_argument_group('mygroup1')
            >>> group1.add_argument('--group1_opt1', action='store_true')
            >>> group1.add_argument('--group1_opt2')
            >>> group2 = parser.add_argument_group()
            >>> group2.add_argument('--group2_opt1', action='store_true')
            >>> group2.add_argument('--group2_opt2')
            >>> mutex_group3 = parser.add_mutually_exclusive_group()
            >>> mutex_group3.add_argument('--mgroup3_opt1')
            >>> mutex_group3.add_argument('--mgroup3_opt2')
            >>> DynamicClass = scfg.DataConfig.cls_from_argparse(parser)
            >>> print(f'DynamicClass.__default__ = {ub.urepr(DynamicClass.__default__, nl=1)}')
            >>> self = DynamicClass()
            >>> print(f'self = {ub.urepr(self, nl=1)}')
            >>> # Check to see if ithis roundtrips nicelyprint(self.port_to_argparse())
            >>> print(self.port_to_argparse())
            >>> parser = self.argparse()
        """

        if name is None:
            name = 'Dynamic' + cls.__name__

        # Extract the appropriate values from the parser
        values = cls._values_from_argparse(parser, for_text=False)

        bases = (cls,)  # Base classes, object is the default base class
        attributes = {
            '__doc__': description or parser.description,
            '__default__': dict(values),
        }

        # Dynamically create the class (
        # note, cls.__class__ should be MetaConfig)
        DynamicClass = cls.__class__(name, bases, attributes)
        return DynamicClass

    @classmethod
    def _values_from_argparse(cls, parser, for_text=True):
        """
        Port argparse options to a list of key / values.
        """
        # This logic should be able to be used statically or dynamically
        # to transition argparse to ScriptConfig code.
        pos_counter = it.count(1)

        # Determine if the parser has groups / mutex groups. Build mappings so
        # we can lookup which action is associated with which group later.
        group_counter = it.count(1)
        mgroup_counter = it.count(1)
        annon_groupid_to_key = {}
        annon_mgroupid_to_key = {}
        default_groups = {'positional arguments', 'options', 'required'}
        actionid_to_groupkey = {}
        actionid_to_mgroupkey = {}
        # Build group lookups table
        for group in parser._action_groups:
            if group.title not in default_groups:
                if group.title is not None:
                    group_key = group.title
                else:
                    group_id = id(group)
                    if group_id not in annon_groupid_to_key:
                        annon_groupid_to_key[group_id] = next(group_counter)
                    group_key = annon_groupid_to_key[group_id]
                for action in group._group_actions:
                    action_id = id(action)
                    actionid_to_groupkey[action_id] = group_key
        # Build mutex group lookups table
        for mutex_group in parser._mutually_exclusive_groups:
            mgroup_id = id(mutex_group)
            if mgroup_id not in annon_mgroupid_to_key:
                annon_mgroupid_to_key[mgroup_id] = next(mgroup_counter)
            mgroup_key = annon_mgroupid_to_key[mgroup_id]
            for action in mutex_group._group_actions:
                action_id = id(action)
                actionid_to_mgroupkey[action_id] = mgroup_key

        # Iterate over all of the actions and build the appropriate value to be
        # placed in the scriptconfig class.
        entries = []
        for action in parser._actions:
            key = action.dest
            if key == 'help':
                # scriptconfig takes care of help for us
                continue
            value = Value._from_action(
                action, actionid_to_groupkey, actionid_to_mgroupkey, pos_counter)
            if for_text:
                # Use for the text reconstruction of the argparser, this is
                # very hacky.
                value_kw = value._to_value_kw()
                entries.append((key, value_kw))
            else:
                entries.append((key, value))
        return entries

    # Backwards compatibility, deprecate and remove
    port_argparse = port_from_argparse

    def port_to_argparse(self):
        """
        Attempt to make code for a nearly-equivalent argparse object.

        This code only handles basic cases. Some of the scriptconfig magic is
        dropped so we dont need to rely on custom actions.

        The idea is that sometimes we can't depend on scriptconfig, so it would
        be nice to be able to translate an existing scriptconfig class to the
        nearly equivalent argparse code.

        SeeAlso:
            :meth:`Config.argparse` - creates a real argparse object

        Returns:
            str: code to construct a similar argparse object

        CommandLine:
            xdoctest -m scriptconfig.config Config.port_to_argparse

        Example:
            >>> import scriptconfig as scfg
            >>> class SimpleCLI(scfg.DataConfig):
            >>>     data = scfg.Value(None, help='input data', position=1)
            >>> self_or_cls = SimpleCLI()
            >>> text = self_or_cls.port_to_argparse()
            >>> print(text)
            >>> # Test that the generated code is executable
            >>> ns = {}
            >>> exec(text, ns, ns)
            >>> parser = ns['parser']
            >>> args1 = parser.parse_args(['foobar'])
            >>> assert args1.data == 'foobar'
            >>> # Looks like we can't do positional or key/value easily
            >>> #args1 = parser.parse_args(['--data=blag'])
            >>> #print('args1 = {}'.format(ub.urepr(args1, nl=1)))

        """
        parserkw = self._parserkw()
        to_pop = {k for k, v in parserkw.items() if v is None}
        parserkw = ub.udict(parserkw) - to_pop
        parserkw.pop('formatter_class', None)

        constructor_body = ub.indent(ub.urepr(parserkw, explicit=True, nobr=1))

        lines = []
        lines.append(ub.codeblock(
            '''
            import argparse
            parser = argparse.ArgumentParser(
            {constructor_body}
                formatter_class=argparse.RawDescriptionHelpFormatter,
            )
            ''').format(
                constructor_body=constructor_body,
            ))

        from scriptconfig import value as value_mod
        for key, _value in self._data.items():
            if isinstance(_value, value_mod.Value):
                value = _value.value
            else:
                value = _value
                _value = self._default[key]
                if not isinstance(_value, value_mod.Value):
                    # hack
                    _value = value_mod.Value(_value)

            invocations = value_mod._value_add_argument_kw(value, _value, self, key)
            for arg_type, t in invocations.items():
                meth, args, kwargs = t
                if not isinstance(kwargs.get('action'), str):
                    kwargs.pop('action')
                if kwargs.get('type', None) is not None:
                    kwargs['type'] = value_mod.CodeRepr(kwargs['type'].__name__)
                to_pop = {k for k, v in kwargs.items() if v is None}
                kwargs = ub.udict(kwargs) - to_pop
                args_body = ub.urepr(args, explicit=1, nobr=1, trailsep=0).strip().strip(',')
                kwargs_body = ub.urepr(kwargs, explicit=1, nobr=1, trailsep=0, nl=0).strip(',')
                if args_body and kwargs_body:
                    args_body += ', '
                lines.append(f'parser.{meth}({args_body}{kwargs_body})')

        text = '\n'.join(lines)
        return text

    # @classmethod
    # def _construct_config_text(cls):
    #     ...

    @property
    def namespace(self):
        """
        Access a namespace like object for compatibility with argparse

        Returns:
            argparse.Namespace
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
            # given as a comma separated string with optional square brackets at
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
            >>>     __description__ = 'my CLI description'
            >>>     __default__ = {
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
            >>>     __description__ = 'my CLI description'
            >>>     __default__ = {
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

        Example:
            >>> # Is it possible to the CLI as a key/val pair or an exist bool flag?
            >>> import scriptconfig as scfg
            >>> class MyConfig(scfg.Config):
            >>>     __default__ = {
            >>>         'path1':  scfg.Value(None, position=1, alias='src'),
            >>>         'path2':  scfg.Value(None, position=2, alias='dst'),
            >>>         'flag':  scfg.Value(None, isflag=True),
            >>>     }
            >>> self = MyConfig()
            >>> special_options = True
            >>> parser = None
            >>> parser = self.argparse(special_options=special_options)
            >>> parser.print_help()
            >>> print(self._read_argv(argv=[], strict=True))
            >>> # Test that we can specify the flag as a pure flag
            >>> print(self._read_argv(argv=['--flag']))
            >>> print(self._read_argv(argv=['--no-flag']))
            >>> # Test that we can specify the flag with a key/val pair
            >>> print(self._read_argv(argv=['--flag', 'TRUE']))
            >>> print(self._read_argv(argv=['--flag=1']))
            >>> print(self._read_argv(argv=['--flag=0']))
            >>> # Test flag and positional
            >>> self = MyConfig()
            >>> print(self._read_argv(argv=['--flag', 'TRUE', 'SUFFIX']))
            >>> self = MyConfig()
            >>> print(self._read_argv(argv=['PREFIX', '--flag', 'TRUE']))
            >>> self = MyConfig()
            >>> print(self._read_argv(argv=['--path2=PREFIX', '--flag', 'TRUE']))

        Example:
            >>> # Test groups
            >>> import scriptconfig as scfg
            >>> class MyConfig(scfg.Config):
            >>>     __description__ = 'my CLI description'
            >>>     __default__ = {
            >>>         'arg1':  scfg.Value(None, group='a'),
            >>>         'arg2':  scfg.Value(None, group='a', alias='a2'),
            >>>         'arg3':  scfg.Value(None, group='b'),
            >>>         'arg4':  scfg.Value(None, group='b', alias='a4'),
            >>>         'arg5':  scfg.Value(None, mutex_group='b', isflag=True),
            >>>         'arg6':  scfg.Value(None, mutex_group='b', alias='a6'),
            >>>     }
            >>> self = MyConfig()
            >>> parser = self.argparse()
            >>> parser.print_help()
            >>> print(self.port_argparse(parser))
            >>> import pytest
            >>> import argparse
            >>> with pytest.raises(SystemExit):
            >>>     self._read_argv(argv=['--arg6', '42', '--arg5', '32'])
            >>> # self._read_argv(argv=['--arg6', '42', '--arg5']) # Strange, this does not cause an mutex error
            >>> self._read_argv(argv=['--arg6', '42'])
            >>> self._read_argv(argv=['--arg5'])
            >>> self._read_argv(argv=[])
        """
        from scriptconfig import argparse_ext

        if parser is None:
            parserkw = self._parserkw()
            # parser = argparse.ArgumentParser(**parserkw)
            parser = argparse_ext.ExtendedArgumentParser(**parserkw)

        # Use custom action used to mark which values were explicitly set on
        # the commandline
        parser._explicitly_given = set()

        # IRC: this ensures each key has a real Value class
        # This is messy and needs to be rethought
        _metadata = {
            key: self._data[key]
            for key, value in self._default.items()
            if isinstance(self._data[key], Value)
        }  # :type: Dict[str, Value]
        for k, v in self._default.items():
            # If the _data did not have value information but the _default
            # does, use that. This is very ugly.
            if k not in _metadata:
                if isinstance(v, Value):
                    _metadata[k] = v.copy().update(self._data[k])
        _positions = {k: v.position for k, v in _metadata.items()
                      if v.position is not None}
        if _positions:
            if ub.find_duplicates(_positions.values()):
                # TODO: make this a warning in 3.7+ and ensure there is a good
                # API for just indicating that a value is supposed to be
                # positional, and using its order in the dictionary as that
                # position. Need to account for inheritance though.
                raise Exception('two values have the same position')
            _keyorder = ub.oset(ub.argsort(_positions))
            _keyorder |= (ub.oset(self._default) - _keyorder)
        else:
            _keyorder = list(self._default.keys())

        FUZZY_HYPHENS = getattr(self, '__fuzzy_hyphens__', 1)

        # Need to clean this up, metadata probably isn't necessary.
        for key, value in self._data.items():
            if key in _metadata:
                # Use the metadata in the Value class to enhance argparse
                _value = _metadata[key]
            else:
                # _value = value if scfg_isinstance(value, Value) else None
                if scfg_isinstance(value, Value):
                    raise AssertionError('Did not expect {value=} to be a Value')
                else:
                    # In this case the user did not wrap the default with a
                    # Value, so we can only infer so much about it, but we can
                    # make some educated guesses.
                    _autokw = {
                        'help': '',
                    }
                    if isinstance(value, bool) or isinstance(value, int) and value in {0, 1}:
                        # In this case they probably wanted a boolean flag
                        # In any case it restrict functionality to set isflag=1
                        _autokw['isflag'] = True
                    _value = Value(value, **_autokw)

            from scriptconfig import value as value_mod
            value_mod._value_add_argument_to_parser(
                value, _value, self, parser, key, fuzzy_hyphens=FUZZY_HYPHENS)

        if special_options:
            special_group = parser.add_argument_group(
                'scriptconfig options')
            special_group.add_argument('--config', default=None, help=ub.codeblock(
                '''
                special scriptconfig option that accepts the path to a on-disk
                configuration file, and loads that into this {!r} object.
                ''').format(self.__class__.__name__))

            special_group.add_argument('--dump', default=None, help=ub.codeblock(
                '''
                If specified, dump this config to disk.
                ''').format(self.__class__.__name__))

            special_group.add_argument(
                '--dumps', action=argparse_ext.BooleanFlagOrKeyValAction,
                help=ub.codeblock(
                    '''
                    If specified, dump this config stdout
                    ''').format(self.__class__.__name__))

        return parser


__notes__ = """
export _ARC_DEBUG=1
pip install argcomplete
activate-global-python-argcomplete --dest=$HOME/.bash_completion.d --user
eval "$(register-python-argcomplete xdev)"
complete -r xdev
"""

_ubelt_repr_extension._register_ubelt_repr_extensions()
