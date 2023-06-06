from _typeshed import Incomplete
from scriptconfig.config import Config, MetaConfig


def dataconf(cls):
    ...


class MetaDataConfig(MetaConfig):

    @staticmethod
    def __new__(mcls, name, bases, namespace, *args, **kwargs):
        ...


class DataConfig(Config, metaclass=MetaDataConfig):
    __default__: Incomplete
    __description__: Incomplete
    __epilog__: Incomplete

    def __init__(self, *args, **kwargs) -> None:
        ...

    def __getattr__(self, key):
        ...

    def __dir__(self):
        ...

    def __setattr__(self, key, value) -> None:
        ...

    @classmethod
    def legacy(cls,
               cmdline: bool = ...,
               data: Incomplete | None = ...,
               default: Incomplete | None = ...,
               strict: bool = ...):
        ...

    @classmethod
    def parse_args(cls,
                   args: Incomplete | None = ...,
                   namespace: Incomplete | None = ...):
        ...

    @classmethod
    def parse_known_args(cls,
                         args: Incomplete | None = ...,
                         namespace: Incomplete | None = ...):
        ...

    @property
    def default(self):
        ...


def __example__() -> None:
    ...
