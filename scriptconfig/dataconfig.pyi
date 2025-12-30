from _typeshed import Incomplete
from scriptconfig.config import Config, MetaConfig
from scriptconfig.subconfig import SubConfig
from typing import Dict, Type, Any


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

    @classmethod
    def cli(cls, data=None, default=None, argv=None, strict: bool = ...,
            cmdline: bool = ..., autocomplete='auto', special_options: bool = ...,
            transition_helpers: bool = ..., verbose=False, allow_import: bool = ...) -> "DataConfig":
        ...

    def load(self, data=None, cmdline=False, mode=None, default=None,
             strict=False, autocomplete=False, _dont_call_post_init=False,
             special_options=True, allow_import=False):
        ...

    def asdict(self) -> Dict[str, Any]:
        ...

    def to_dict(self) -> Dict[str, Any]:
        ...

    def dump(self, stream=None, mode=None):
        ...

    def dumps(self, mode=None):
        ...

    @property
    def default(self):
        ...


def __example__() -> None:
    ...
