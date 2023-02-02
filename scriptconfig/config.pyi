from typing import Union
from typing import Any
from os import PathLike
from typing import List
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


class Config(ub.NiceRepr, DictLike):
    __scfg_class__: str
    epilog: str

    def __init__(self,
                 data: Union[object, None] = None,
                 default: Union[dict, None] = None,
                 cmdline: bool = ...) -> None:
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
             data: Union[PathLike, dict, None] = None,
             cmdline: Union[bool, List[str], str] = False,
             mode: Union[str, None] = None,
             default: Union[dict, None] = None,
             strict: bool = False):
        ...

    def normalize(self) -> None:
        ...

    def dump(self,
             stream: Union[FileLike, None] = None,
             mode: Union[str, None] = None):
        ...

    def dumps(self, mode: Union[str, None] = None):
        ...

    @classmethod
    def port_argparse(cls,
                      parser: argparse.ArgumentParser,
                      name: str = 'MyConfig',
                      style: str = 'orig') -> str:
        ...

    @property
    def namespace(self):
        ...

    def to_omegaconf(self) -> omegaconf.OmegaConf:
        ...

    required: bool
    type: Incomplete

    def argparse(self,
                 parser: Union[None, argparse.ArgumentParser] = None,
                 special_options: bool = False) -> argparse.ArgumentParser:
        ...

    def __getattr__(self, key):
        ...


__notes__: str
