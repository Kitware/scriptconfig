"""
The new way to declare configurations.

Similar to the old-style Config objects, you simply declare a class that
inherits from :class:`scriptconfig.DataConfig` (or is wrapped by
:func:`scriptconfig.datconf`) and declare the class variables as the config
attributes much like you would write a dataclass.


Creating an instance of a ``DataConfig`` class works just like a regular
dataclass, and nothing special happens. You can create the argument parser by
using the :func:``DataConfig.cli`` classmethod, which works similarly to the
old-style :class:`scriptconfig.Config` constructor.

The following is the same top-level example as in :mod:`scriptconfig.config`,
but using ``DataConfig`` instead. It works as a drop-in replacement.


Example:
    >>> import scriptconfig as scfg
    >>> # In its simplest incarnation, the config class specifies default values.
    >>> # For each configuration parameter.
    >>> class ExampleConfig(scfg.DataConfig):
    >>>      num = 1
    >>>      mode = 'bar'
    >>>      ignore = ['baz', 'biz']
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

Notes:
    https://docs.python.org/3/library/dataclasses.html
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Type, cast
import inspect

from scriptconfig.config import Config, MetaConfig
from scriptconfig.value import Value
import warnings
import ubelt as ub
from scriptconfig import diagnostics
from scriptconfig.subconfig import SubConfig, wrap_subconfig_defaults


__all__ = ['dataconf', 'DataConfig', 'MetaDataConfig', 'SubConfig']


def dataconf(cls: Type[Any]) -> Type[Any]:
    """
    Aims to be similar to the dataclass decorator

    Note:
        It is currently recommended to extend from the :class:`DataConfig`
        object instead of decorating with ``@dataconf``. These have slightly
        different behaviors and the former is more well-tested.

    Example:
        >>> from scriptconfig.dataconfig import *  # NOQA
        >>> import scriptconfig as scfg
        >>> @dataconf
        >>> class ExampleDataConfig2:
        >>>     chip_dims = scfg.Value((256, 256), help='chip size')
        >>>     time_dim = scfg.Value(3, help='number of time steps')
        >>>     channels = scfg.Value('*:(red|green|blue)', help='sensor / channel code')
        >>>     time_sampling = scfg.Value('soft2')
        >>> cls = ExampleDataConfig2
        >>> print(f'cls={cls}')
        >>> self = cls()
        >>> print(f'self={self}')

    Example:
        >>> from scriptconfig.dataconfig import *  # NOQA
        >>> import scriptconfig as scfg
        >>> @dataconf
        >>> class PathologicalConfig:
        >>>     default0 = scfg.Value((256, 256), help='chip size')
        >>>     default = scfg.Value((256, 256), help='chip size')
        >>>     keys = [1, 2, 3]
        >>>     __default__ = {
        >>>         'argparse': 3.3,
        >>>         'keys': [4, 5],
        >>>     }
        >>>     default = None
        >>>     time_sampling = scfg.Value('soft2')
        >>>     def foobar(self):
        >>>         ...
        >>> self = PathologicalConfig(1, 2, 3)
        >>> print(f'self={self}')

    # FIXME: xdoctest problem. Need to be able to simulate a module global scope
    # Example:
    #     >>> # Using inheritance and the decorator lets you pickle the object
    #     >>> from scriptconfig.dataconfig import *  # NOQA
    #     >>> import scriptconfig as scfg
    #     >>> @dataconf
    #     >>> class PathologicalConfig2(scfg.DataConfig):
    #     >>>     default0 = scfg.Value((256, 256), help='chip size')
    #     >>>     default2 = scfg.Value((256, 256), help='chip size')
    #     >>>     #keys = [1, 2, 3] : Too much
    #     >>>     __default__3 = {
    #     >>>         'argparse': 3.3,
    #     >>>         'keys2': [4, 5],
    #     >>>     }
    #     >>>     default2 = None
    #     >>>     time_sampling = scfg.Value('soft2')
    #     >>> config = PathologicalConfig2()
    #     >>> import pickle
    #     >>> serial = pickle.dumps(config)
    #     >>> recon = pickle.loads(serial)
    #     >>> assert 'locals' not in str(PathologicalConfig2)

    """
    # if not dataclasses.is_dataclass(cls):
    #     dcls = dataclasses.dataclass(cls)
    # else:
    #     dcls = cls

    # fields = dataclasses.fields(cls)
    # for field in fields:
    #     field.type
    #     field.name
    #     field.default

    if getattr(cls, '__did_dataconfig_init__', False):
        # The metaclass took care of this.
        # TODO: let the metaclass take care of most everything.
        return cls

    attr_default = {}
    for k, v in vars(cls).items():
        if not k.startswith('_') and not isinstance(v, classmethod) and not isinstance(v, staticmethod):
            if not callable(v) or (inspect.isclass(v) and issubclass(v, Config)):
                attr_default[k] = v
    default = attr_default.copy()
    cls_default = getattr(cls, '__default__', None)
    if cls_default is None:
        cls_default = {}
    default.update(cls_default)

    if issubclass(cls, DataConfig):
        # Helps make the class pickleable. Pretty hacky though.
        # TODO: Remove. This should no longer be necessary. Given the metaclass.
        subconfig_type = cls
        subconfig_type.__default__ = default
        for k in attr_default:
            delattr(subconfig_type, k)
    else:
        # dynamic subclass, this has issues with pickle. It would be nice if we
        # could improve this. There must be a way that dataclasses does it that
        # we could follow.
        class SubConfig(DataConfig):
            __doc__ = getattr(cls, '__doc__', None)
            __name__ = getattr(cls, '__name__', None)
            __default__ = default
            __description__ = getattr(cls, '__description__', None)
            __epilog__ = getattr(cls, '__epilog__', None)
            __qualname__ = cls.__qualname__
            __module__ = cls.__module__
        subconfig_type = SubConfig
    return subconfig_type


class MetaDataConfig(MetaConfig):
    """
    This metaclass allows us to call `dataconf` when a new subclass is defined
    without the extra boilerplate.
    """
    @staticmethod
    def __new__(mcls: type,
                name: str,
                bases: Tuple[type, ...],
                namespace: Dict[str, Any],
                *args: Any,
                **kwargs: Any) -> type:
        # Defining a new class that inherits from DataConfig
        if diagnostics.DEBUG_META_DATA_CONFIG:
            print(f'MetaDataConfig.__new__ called: {mcls=} {name=} {bases=} {namespace=} {args=} {kwargs=}')

        # Only do this for children of DataConfig, skip this for DataConfig
        # itself. This is a hacky way to do this. Can we make this check more
        # robust? The problem is the `DataConfig` attribute isn't defined when
        # this runs, so we can't check for equality to it, otherwise we could
        # just check that bases included `DataConfig`.
        if namespace.get('__module__', None) != 'scriptconfig.dataconfig' or name != 'DataConfig':
            # Cant call datconf directly, but we can simulate
            # We can modify the namespace before the class gets constructed
            # too, which is slightly cleaner.
            attr_default = {}
            for k, v in namespace.items():
                if not k.startswith('_') and not isinstance(v, classmethod) and not isinstance(v, staticmethod):
                    if not callable(v) or (inspect.isclass(v) and issubclass(v, Config)):
                        attr_default[k] = v
            this_default = attr_default.copy()
            cls_default = namespace.get('__default__', None)
            if cls_default is None:
                cls_default = {}

            this_default.update(cls_default)

            if '__class__' in this_default:
                raise ValueError('The name "__class__" is reserved for nested DataConfig meta keys')
            # Helps make the class pickleable. Pretty hacky though.
            for k in attr_default:
                namespace.pop(k)
            namespace['__default__'] = this_default
            # print(f'this_default={this_default}')
            namespace['__did_dataconfig_init__'] = True

            for k, v in this_default.items():
                if isinstance(v, tuple) and len(v) == 1 and isinstance(v[0], Value):
                    warnings.warn(ub.paragraph(
                        f'''
                        It looks like you have a trailing comma in your
                        {name} DataConfig.  The variable {k!r} has a value of
                        {v!r}, which is a Tuple[Value]. Typically it should be
                        a Value.
                        '''), UserWarning)
        cls = super().__new__(mcls, name, bases, namespace, *args, **kwargs)  # type: ignore[misc]

        # Modify the docstring to include information about the defaults
        if cls.__init__.__doc__ == '__autogenerateme__':
            valid_keys = list(cls.__default__.keys())
            cls.__init__.__doc__ = ub.codeblock(
                f'''
                Valid options: {valid_keys}

                Args:
                    *args: positional arguments for this data config
                    **kwargs: keyword arguments for this data config
                ''')
        return cls


class DataConfig(Config, metaclass=MetaDataConfig):
    """
    Base class for dataconfig-style configs.
    Overwrite this docstr with a description.

    To use, create a class (e.g. MyConfig) that inherits from DataConfig.  The
    configuration keys and their default values are specified by class level
    attributes. Metadata for keys can be given by specifying the default values
    as a :class:`scriptconfig.Value`.

    An instance can be created programmatically with keyword arguments
    specifying updates to default values.

    The :func:`DataConfig.cli` classmethod can be used to create an instance
    where the values are optionally populated from command line arguments in
    ``sys.argv`` or a custom ``argv``.

    Usage of the config is flexible.  It can be used as a dictionary or as a
    namespace. That is, you can either use ``config['key']`` or ``config.key``
    to access values for ``key``. The only incompatibility between this and a
    normal dictionary is that this does not allow new keys to be added,
    otherwise it can be treated exactly as a dictionary.

    Example:
        >>> import scriptconfig as scfg
        >>> class MyConfig(scfg.DataConfig):
        >>>     key1 = 'default-value1'
        >>>     key2 = 'default-value2'
        >>>     key3 = scfg.Value('default-value3', help='extra metadata!')
        >>> # Create a programmatic instance
        >>> config = MyConfig()
        >>> print(f'config={config}')
        config=<MyConfig({'key1': 'default-value1', 'key2': 'default-value2', 'key3': 'default-value3'})>
        >>> # Create an instance via command line args
        >>> # (note the default "smartcasting")
        >>> config = MyConfig.cli(argv=['--key1', '123', '--key2=345', '--key3=abc'])
        >>> print(f'config={config}')
        config=<MyConfig({'key1': 123, 'key2': 345, 'key3': 'abc'})>

    For fine-grained control overwrite the following attributes:

        * ``__epilog__`` (str):  documentation for the epilog of the argparse help string

        * ``__post_init__`` (callable): function that normalizes values on instance creation.

        * ``__default__`` (Dict[str, Any]): an alternate way to specify key/default-values based on an existing dictionary. Specifying an item in this dictionary has the same effect as specifying a class-attribute.

    SeeAlso:
        :class:`scriptconfig.Config`
    """
    # Not sure if having a docstring for this will break user-configs.
    # No docstring, because user-specified docstring will define the default
    # __description__.
    # Note: class attributes may be raw literals; the metaclass normalizes
    # them into Value/SubConfig instances after class creation.
    __default__: Dict[str, Any] = {}
    __description__: Optional[str] = None
    __epilog__: Optional[str] = None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        "__autogenerateme__"
        # Private internal hack to prevent __post_init__ from being called
        # if we are immediately going to load and call it again.
        _dont_call_post_init = kwargs.pop('_dont_call_post_init', False)

        self._data: Dict[str, Any] = {}
        self._default: Dict[str, Value] = {}
        if getattr(self, '__default__', None):
            # allow for class attributes to specify the default
            self._default.update(self.__default__)
        argkeys = list(self._default.keys())[0:len(args)]
        new_defaults = ub.dzip(argkeys, args)
        kwargs = self._normalize_alias_dict(kwargs)
        new_defaults.update(kwargs)
        unknown_args: Dict[str, Any] = ub.dict_diff(new_defaults, self._default)  # type: ignore[arg-type]
        if unknown_args:
            raise ValueError((
                "Unknown Arguments: {}. Expected arguments are: {}"
            ).format(unknown_args, list(self._default)))
        for key, value in new_defaults.items():
            template = self._default.get(key)
            if isinstance(template, Value) and not isinstance(value, Value):
                new_template = template.copy()
                new_template.value = value
                new_defaults[key] = new_template
        self._default.update(new_defaults)
        self._data = {
            key: (value.value if isinstance(value, Value) else value)
            for key, value in self._default.items()
        }
        self._subconfig_meta = {}
        self._has_subconfigs = False
        wrap_subconfig_defaults(self, _dont_call_post_init=_dont_call_post_init)
        self._enable_setattr = True
        self._scfg_post_init_done = False
        if not _dont_call_post_init:
            self.__post_init__()
            self._scfg_post_init_done = True

    def __getattr__(self, key: str) -> Any:
        # Note: attributes that mirror the public API will be suppressed
        # It is generally better to use the dictionary interface instead
        # But we want this to be data-classy, so...
        if key.startswith('_'):
            # config vars must not start with '_'. That is only for us
            raise AttributeError(key)
        if key in self:
            try:
                return self[key]
            except KeyError:
                raise AttributeError(key)
        raise AttributeError(key)

    def __dir__(self) -> List[str]:
        initial = cast(List[str], super().__dir__())
        return initial + list(self.keys())

    def __setattr__(self, key: str, value: Any) -> None:
        """
        Forwards setattrs in the configuration to the dictionary interface,
        otherwise passes it through.
        """
        if key.startswith('_'):
            # Currently we do not allow leading underscores to be config
            # values to give us some flexibility for API changes.
            self.__dict__[key] = value
        else:
            can_setattr = (getattr(self, '__allow_newattr__', False))  # case where user can add new keys on the fly
            can_setattr |= (getattr(self, '_enable_setattr', False) and key in self)  # internal usage for initialization
            if can_setattr:
                # After object initialization allow the user to use setattr on any
                # value in the underlying dictionary. Everything else uses the
                # normal mechanism.
                try:
                    self[key] = value
                except KeyError:
                    raise AttributeError(key)
            else:
                self.__dict__[key] = value

    @classmethod
    def legacy(cls,
               cmdline: bool = False,
               data: Optional[Any] = None,
               default: Optional[Dict[str, Any]] = None,
               strict: bool = False) -> "DataConfig":
        """
        Calls the original "load" way of creating non-dataclass config objects.
        This may be refactored in the future.
        """
        import ubelt as ub
        ub.schedule_deprecation(
            'scriptconfig', 'legacy', 'classmethod',
            migration='use the cli classmethod instead.',
            deprecate='0.7.2', error='1.0.0', remove='1.0.1',
        )
        if default is None:
            default = {}
        self = cls(**default)
        self.load(data, cmdline=cmdline, default=default, strict=strict)
        return self

    @classmethod
    def parse_args(cls,
                   args: Optional[List[str]] = None,
                   namespace: Optional[Any] = None) -> "DataConfig":
        """
        Mimics argparse.ArgumentParser.parse_args
        """
        if namespace is not None:
            raise NotImplementedError(
                'namespaces are not handled in scriptconfig')
        return cast("DataConfig", cls.cli(argv=args, strict=True))

    @classmethod
    def parse_known_args(cls,
                         args: Optional[List[str]] = None,
                         namespace: Optional[Any] = None) -> "DataConfig":
        """
        Mimics argparse.ArgumentParser.parse_known_args
        """
        if namespace is not None:
            raise NotImplementedError(
                'namespaces are not handled in scriptconfig')
        return cast("DataConfig", cls.cli(argv=args, strict=False))

    @property
    def default(self) -> Dict[str, Any]:
        import ubelt as ub
        ub.schedule_deprecation(
            'scriptconfig', 'default', 'attribute',
            migration='use the __default__ instead.',
            deprecate='0.7.7', error='1.0.0', remove='1.0.1',
        )
        return self.__default__

    @classmethod
    def _register_main(cls, func):
        """
        Register a function as the main method for this dataconfig CLI
        """
        cls.main = func
        return func


def __example__() -> None:
    """
    Doctests are broken for DataConfigs, so putting them here.
    """
    import scriptconfig as scfg
    dataclasses: Any
    try:
        import dataclasses
    except ImportError:
        dataclasses = None

    if dataclasses is None:
        return

    @dataclasses.dataclass
    class ExampleDataConfig0:
        x: int = 0
        y: str = '3'

    ### Different variants of the same basic configuration (varying amounts of metadata)
    class ExampleDataConfig1:
        chip_dims = (256, 256)
        time_dim = 5
        channels = 'red|green|blue'
        time_sampling = 'soft2'

    ExampleDataConfig1d = dataclasses.dataclass(ExampleDataConfig1)

    @dataclasses.dataclass
    class ExampleDataConfig2:
        chip_dims = scfg.Value((256, 256), help='chip size')
        time_dim = scfg.Value(3, help='number of time steps')
        channels = scfg.Value('*:(red|green|blue)', help='sensor / channel code')
        time_sampling = scfg.Value('soft2')

    @dataclasses.dataclass
    class ExampleDataConfig2d:
        chip_dims = scfg.Value((256, 256), help='chip size')
        time_dim: Any = scfg.Value(3, help='number of time steps')
        channels: Any = scfg.Value('*:(red|green|blue)', help='sensor / channel code')
        time_sampling: Any = scfg.Value('soft2')

    class ExampleDataConfig3:
        __default__ = {
            'chip_dims': scfg.Value((256, 256), help='chip size'),
            'time_dim': scfg.Value(3, type=int, help='number of time steps'),
            'channels': scfg.Value('*:(red|green|blue)', type=str, help='sensor / channel code'),
            'time_sampling': scfg.Value('soft2', type=str),
        }

    classes = [ExampleDataConfig0, ExampleDataConfig1, ExampleDataConfig1d,
               ExampleDataConfig2, ExampleDataConfig2d, ExampleDataConfig3]
    for cls in classes:
        dcls = dataconf(cls)
        self = dcls()
        print(f'self={self}')

    # cls = ExampleDataConfig2
    # cls.__annotations__['channels'].__dict__
    # cls.__annotations__['set_cover_algo'].__dict__
    # # @scfg.dataconfig
