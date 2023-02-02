from typing import Union
from _typeshed import Incomplete

NoneType: Incomplete


def smartcast(item: Union[str, object],
              astype: Union[type, None] = None,
              strict: bool = False,
              allow_split: bool = False) -> object:
    ...
