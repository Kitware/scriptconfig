from typing import Any


class FileLike:
    mode: Any

    def __init__(self, path_or_file, mode: str = ...) -> None:
        ...

    def __enter__(self):
        ...

    def __exit__(self, *args) -> None:
        ...
