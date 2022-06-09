import ubelt as ub
from typing import Any


class Value(ub.NiceRepr):
    __scfg_class__: str
    value: Any
    type: Any
    alias: Any
    position: Any
    isflag: Any
    parsekw: Any
    required: Any
    short_alias: Any

    def __init__(self,
                 value: Any | None = ...,
                 type: Any | None = ...,
                 help: Any | None = ...,
                 choices: Any | None = ...,
                 position: Any | None = ...,
                 isflag: bool = ...,
                 nargs: Any | None = ...,
                 alias: Any | None = ...,
                 required: bool = ...,
                 short_alias: Any | None = ...) -> None:
        ...

    def __nice__(self):
        ...

    def update(self, value) -> None:
        ...

    def cast(self, value):
        ...


class Path(Value):

    def __init__(self,
                 value: Any | None = ...,
                 help: Any | None = ...,
                 alias: Any | None = ...) -> None:
        ...

    def cast(self, value):
        ...


class PathList(Value):

    def cast(self, value: Any | None = ...):
        ...
