from _typeshed import Incomplete


class FileLike:
    mode: Incomplete

    def __init__(self, path_or_file, mode: str = ...) -> None:
        ...

    def __enter__(self):
        ...

    def __exit__(self, *args) -> None:
        ...
