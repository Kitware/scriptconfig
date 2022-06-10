from typing import List
from typing import Union
from os import PathLike
import argparse
import ubelt as ub
from scriptconfig.dict_like import DictLike
from scriptconfig.file_like import FileLike
from typing import Any, TypeVar

VT = TypeVar("VT")


def scfg_isinstance(item: object, cls: type):
    ...


def define(default=..., name: Any | None = ...):
    ...


class Config(ub.NiceRepr, DictLike):
    __scfg_class__: str

    def __init__(self,
                 data: object = ...,
                 default: dict = ...,
                 cmdline: Union[bool, List[str], str] = ...) -> None:
        ...

    @classmethod
    def demo(cls):
        ...

    def __json__(self):
        ...

    def __nice__(self):
        ...

    def getitem(self, key: str) -> VT:
        ...

    def setitem(self, key: str, value: VT) -> None:
        ...

    def delitem(self, key) -> None:
        ...

    def keys(self):
        ...

    def update_defaults(self, default: dict) -> None:
        ...

    def load(self,
             data: Union[PathLike, dict] = ...,
             cmdline: Union[bool, List[str], str] = ...,
             mode: Any | None = ...,
             default: Any | None = ...):
        ...

    def normalize(self) -> None:
        ...

    def dump(self,
             stream: Union[FileLike, None] = ...,
             mode: Union[str, None] = ...):
        ...

    def dumps(self, mode: Union[str, None] = ...):
        ...

    @classmethod
    def port_argparse(cls,
                      parser: argparse.ArgumentParser,
                      name: str = ...) -> str:
        ...

    @property
    def namespace(self):
        ...

    required: Any
    type: Any

    def argparse(self,
                 parser: Union[None, argparse.ArgumentParser] = ...,
                 special_options: bool = ...) -> argparse.ArgumentParser:
        ...


class DataInterchange:
    mode: Any
    strict: Any

    def __init__(self,
                 mode: Any | None = ...,
                 strict: Any | None = ...) -> None:
        ...

    @classmethod
    def load(cls, fpath):
        ...

    @classmethod
    def dumps(cls, data, mode: str = ...):
        ...
