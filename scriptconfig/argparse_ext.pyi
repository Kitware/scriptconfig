import argparse
from _typeshed import Incomplete

import argparse

_Base = argparse._StoreAction
__docstubs__: str


class BooleanFlagOrKeyValAction(_Base):

    def __init__(self,
                 option_strings,
                 dest,
                 default: Incomplete | None = ...,
                 required: bool = ...,
                 help: Incomplete | None = ...) -> None:
        ...

    def format_usage(self):
        ...

    def __call__(action,
                 parser,
                 namespace,
                 values,
                 option_string: Incomplete | None = ...) -> None:
        ...


class RawDescriptionDefaultsHelpFormatter(
        argparse.RawDescriptionHelpFormatter,
        argparse.ArgumentDefaultsHelpFormatter):
    ...


class CompatArgumentParser(argparse.ArgumentParser):
    exit_on_error: Incomplete

    def __init__(self, *args, **kwargs) -> None:
        ...

    def parse_known_args(self,
                         args: Incomplete | None = ...,
                         namespace: Incomplete | None = ...):
        ...
