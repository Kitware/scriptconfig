from typing import Any
from typing import List
import ubelt as ub
from _typeshed import Incomplete

long_prefix_pat: Incomplete
short_prefix_pat: Incomplete


def normalize_option_str(s):
    ...


__note__: str


class Value(ub.NiceRepr):
    __scfg_class__: str
    value: Any
    type: type | None
    parsekw: dict
    position: None | int
    isflag: bool
    alias: List[str] | None
    short_alias: List[str] | None
    group: str | None
    mutex_group: str | None
    tags: Any
    required: Incomplete

    def __init__(self,
                 value: Incomplete | None = ...,
                 type: Incomplete | None = ...,
                 help: Incomplete | None = ...,
                 choices: Incomplete | None = ...,
                 position: Incomplete | None = ...,
                 isflag: bool = ...,
                 nargs: Incomplete | None = ...,
                 alias: Incomplete | None = ...,
                 required: bool = ...,
                 short_alias: Incomplete | None = ...,
                 group: Incomplete | None = ...,
                 mutex_group: Incomplete | None = ...,
                 tags: Incomplete | None = ...) -> None:
        ...

    def __nice__(self):
        ...

    def update(self, value):
        ...

    def cast(self, value):
        ...

    def copy(self):
        ...


class Flag(Value):

    def __init__(self, value: bool = ..., **kwargs) -> None:
        ...


class Path(Value):

    def __init__(self,
                 value: Incomplete | None = ...,
                 help: Incomplete | None = ...,
                 alias: Incomplete | None = ...) -> None:
        ...

    def cast(self, value):
        ...


class PathList(Value):

    def cast(self, value: Incomplete | None = ...):
        ...


def scfg_isinstance(item: object, cls: type) -> bool:
    ...


class CodeRepr(str):
    ...
