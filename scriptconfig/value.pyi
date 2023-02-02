from typing import Any
from typing import Union
from typing import List
import ubelt as ub
from _typeshed import Incomplete
from typing import Any


class Value(ub.NiceRepr):
    __scfg_class__: str
    value: Any
    type: Union[type, None]
    parsekw: dict
    position: Union[None, int]
    isflag: bool
    alias: Union[List[str], None]
    short_alias: Union[List[str], None]
    group: Union[str, None]
    mutex_group: Union[str, None]
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
                 mutex_group: Incomplete | None = ...) -> None:
        ...

    def __nice__(self):
        ...

    def update(self, value):
        ...

    def cast(self, value):
        ...

    def copy(self):
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
