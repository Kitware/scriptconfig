"""
Experimental module

Notes:

    https://docs.python.org/3/library/dataclasses.html

    __post_init__ corresponds to normalize

"""
from scriptconfig.config import Config


def dataconf(cls):
    """
    Aims to be simlar to the dataclass decorator

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
        if not k.startswith('_') and not callable(v):
            attr_default[k] = v
    default = attr_default.copy()
    cls_default = getattr(cls, '__default__', None)
    if cls_default is None:
        cls_default = {}
    default.update(cls_default)

    if issubclass(cls, DataConfig):
        # Helps make the class pickleable. Pretty hacky though.
        # TODO: Remove. This should no longer be necessary. Given the metaclass.
        SubConfig = cls
        SubConfig.__default__ = default
        for k in attr_default:
            delattr(SubConfig, k)
    else:
        # dynamic subclass, this has issues with pickle It would be nice if we
        # could improve this. There must be a way that dataclasses does it that
        # we could follow.
        class SubConfig(DataConfig):
            __doc__ = getattr(cls, '__doc__', {})
            __name__ = getattr(cls, '__name__', {})
            __default__ = default
            __description__ = getattr(cls, '__description__', {})
            __epilog__ = getattr(cls, '__epilog__', {})
            __qualname__ = cls.__qualname__
            __module__ = cls.__module__
    return SubConfig


class MetaDataConfig(type):
    """
    This metaclass allows us to call `dataconf` when a new subclass is defined
    without the extra boilerplate.
    """
    @staticmethod
    def __new__(mcls, name, bases, namespace, *args, **kwargs):
        # Defining a new class that inherits from DataConfig
        # print(f'Meta.__new__ called: {mcls=} {name=} {bases=} {namespace=} {args=} {kwargs=}')

        # Only do this for children of DataConfig, skip this for DataConfig
        # itself. This is a hacky way to do that.
        if namespace['__module__'] != 'scriptconfig.dataconfig' or name != 'DataConfig':
            # Cant call datconf directly, but we can simulate
            # We can modify the namespace before the class gets constructed
            # too, which is slightly cleaner.
            attr_default = {}
            for k, v in namespace.items():
                if not k.startswith('_') and not callable(v):
                    attr_default[k] = v
            default = attr_default.copy()
            cls_default = namespace.get('__default__', None)
            if cls_default is None:
                cls_default = {}
            default.update(cls_default)
            # Helps make the class pickleable. Pretty hacky though.
            for k in attr_default:
                namespace.pop(k)
            namespace['__default__'] = default
            namespace['__did_dataconfig_init__'] = True
        cls = super().__new__(mcls, name, bases, namespace, *args, **kwargs)
        # print(f'Meta.__new__ returns: {cls=}')
        return cls


# class DataConfig(Config, metaclass=MetaDataConfig):
class DataConfig(Config, metaclass=MetaDataConfig):
    __default__ = None
    __description__ = None
    __epilog__ = None

    def __init__(self, *args, **kwargs):
        import ubelt as ub
        self._data = None
        self._default = ub.odict()
        if getattr(self, '__default__', None):
            # allow for class attributes to specify the default
            self._default.update(self.__default__)
        argkeys = list(self._default.keys())[0:len(args)]
        new_defaults = ub.dzip(argkeys, args)
        new_defaults.update(kwargs)
        unknown_args = ub.dict_diff(new_defaults, self._default)
        if unknown_args:
            raise ValueError("Unknown Arguments: {}".format(unknown_args))
        self._default.update(new_defaults)
        self._data = self._default.copy()
        self.normalize()

    def __getattr__(self, key):
        # Note: attributes that mirror the public API will be supressed
        # It is gennerally better to use the dictionary interface instead
        # But we want this to be data-classy, so...
        if key.startswith('_'):
            # config vars cant start with '_'. Thats only for us
            raise AttributeError(key)
        if key in self:
            try:
                return self[key]
            except KeyError:
                raise AttributeError(key)
        raise AttributeError(key)

    @classmethod
    def legacy(cls, cmdline=False, data=None, default=None):
        if default is None:
            default = {}
        self = cls(**default)
        self.load(data, cmdline=cmdline, default=default)
        return self

    @classmethod
    def cli(cls, data=None, default=None, argv=None):
        if argv is None:
            cmdline = 1
        else:
            cmdline = argv
        return cls.legacy(cmdline=cmdline, data=data, default=default)

    @property
    def default(self):
        return self.__default__


def __example__():
    import scriptconfig as scfg
    try:
        import dataclasses
    except ImportError:
        dataclasses = None

    @dataclasses.dataclass
    class ExampleDataConfig0:
        x: int = 0
        y: str = 3

    ### Different varaints of the same basic configuration (varying amounts of metadata)
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
        time_dim: int = scfg.Value(3, help='number of time steps')
        channels: str = scfg.Value('*:(red|green|blue)', help='sensor / channel code')
        time_sampling: str = scfg.Value('soft2')

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
