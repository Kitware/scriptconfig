from typing import Union
from typing import Any

BooleanType: Any
BooleanType = bool
NoneType: Any


def smartcast(item: Union[str, object],
              astype: type = ...,
              strict: bool = ...,
              allow_split: bool = ...) -> object:
    ...
