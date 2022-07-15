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
        >>> self = PathologicalConfig(1, 2, 3)
        >>> print(f'self={self}')
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
    default = {}
    for k, v in vars(cls).items():
        if not k.startswith('_'):
            default[k] = v
    default.update(getattr(cls, '__default__', {}))

    # dynamic subclass
    class SubConfig(DataConfig):
        __doc__ = getattr(cls, '__doc__', {})
        __name__ = getattr(cls, '__name__', {})
        __default__ = default
        __description__ = getattr(cls, '__description__', {})
        __epilog__ = getattr(cls, '__epilog__', {})
    return SubConfig


class DataConfig(Config):
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
        if key in self:
            return self[key]
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
