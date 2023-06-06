from typing import List
from typing import Any
from os import PathLike
import argparse
import ubelt as ub
from _typeshed import Incomplete
from collections.abc import Generator
from scriptconfig.dict_like import DictLike
from scriptconfig.file_like import FileLike
from typing import Any

from typing import Any

KT = Any
omegaconf: Any
OmegaConf: object
__docstubs__: str


def scfg_isinstance(item: object, cls: type) -> bool:
    ...


def define(default=..., name: Incomplete | None = ...):
    ...


class MetaConfig(type):

    @staticmethod
    def __new__(mcls, name, bases, namespace, *args, **kwargs):
        ...


class Config(ub.NiceRepr, DictLike, metaclass=MetaConfig):
    __scfg_class__: str
    __default__: Incomplete
    epilog: str

    def __init__(self,
                 data: object | None = None,
                 default: dict | None = None,
                 cmdline: bool = ...) -> None:
        ...

    @classmethod
    def cli(cls,
            data: dict | str | None = None,
            default: dict | None = None,
            argv: List[str] | None = None,
            strict: bool = True,
            cmdline: bool = True,
            autocomplete: bool | str = 'auto'):
        ...

    @classmethod
    def demo(cls):
        ...

    def __json__(self) -> dict:
        ...

    def __nice__(self):
        ...

    def getitem(self, key: str) -> Any:
        ...

    def setitem(self, key: str, value: Any) -> None:
        ...

    def delitem(self, key) -> None:
        ...

    def keys(self) -> Generator[str, None, Any]:
        ...

    def update_defaults(self, default: dict) -> None:
        ...

    def load(self,
             data: PathLike | dict | None = None,
             cmdline: bool | List[str] | str = False,
             mode: str | None = None,
             default: dict | None = None,
             strict: bool = False,
             autocomplete: bool = False):
        ...

    def __post_init__(self) -> None:
        ...

    def dump(self, stream: FileLike | None = None, mode: str | None = None):
        ...

    def dumps(self, mode: str | None = None):
        ...

    def __getattr__(self, key):
        ...

    def port_to_dataconf(self):
        ...

    @classmethod
    def port_click(cls, click_main, name: str = ..., style: str = ...) -> None:
        ...

    @classmethod
    def port_argparse(cls,
                      parser: argparse.ArgumentParser,
                      name: str = 'MyConfig',
                      style: str = 'dataconf') -> str:
        ...

    @property
    def namespace(self):
        ...

    def to_omegaconf(self) -> omegaconf.OmegaConf:
        ...

    def argparse(self,
                 parser: None | argparse.ArgumentParser = None,
                 special_options: bool = False) -> argparse.ArgumentParser:
        ...


__notes__: str
