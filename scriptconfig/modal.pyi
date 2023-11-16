from _typeshed import Incomplete

DEFAULT_GROUP: str


class MetaModalCLI(type):

    @staticmethod
    def __new__(mcls, name, bases, namespace, *args, **kwargs):
        ...


class ModalCLI(metaclass=MetaModalCLI):
    __subconfigs__: Incomplete
    description: Incomplete
    version: Incomplete

    def __init__(self,
                 description: str = ...,
                 sub_clis: Incomplete | None = ...,
                 version: Incomplete | None = ...) -> None:
        ...

    def __call__(self, cli_cls):
        ...

    @property
    def sub_clis(self):
        ...

    def register(cls_or_self, cli_cls):
        ...

    def argparse(self, parser: Incomplete | None = ..., special_options=...):
        ...

    build_parser = argparse

    def main(self, argv: Incomplete | None = ..., strict: bool = ...):
        ...

    run = main
