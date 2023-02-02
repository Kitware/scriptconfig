from typing import Any
from _typeshed import Incomplete
from collections.abc import Generator
from typing import Any


class DictLike:

    def getitem(self, key: Any) -> Any:
        ...

    def setitem(self, key, value) -> None:
        ...

    def delitem(self, key) -> None:
        ...

    def keys(self) -> Generator[str, None, None]:
        ...

    def __len__(self):
        ...

    def __iter__(self):
        ...

    def __contains__(self, key):
        ...

    def __delitem__(self, key):
        ...

    def __getitem__(self, key):
        ...

    def __setitem__(self, key, value):
        ...

    def items(self):
        ...

    def values(self):
        ...

    def copy(self):
        ...

    def asdict(self):
        ...

    def to_dict(self):
        ...

    def update(self, other) -> None:
        ...

    def iteritems(self):
        ...

    def itervalues(self):
        ...

    def iterkeys(self):
        ...

    def get(self, key, default: Incomplete | None = ...):
        ...
