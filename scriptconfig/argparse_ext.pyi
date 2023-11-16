import argparse
from _typeshed import Incomplete

import argparse

_Base = argparse._StoreAction

_RawDescriptionHelpFormatter = argparse.RawDescriptionHelpFormatter
_ArgumentDefaultsHelpFormatter = argparse.ArgumentDefaultsHelpFormatter
SCRIPTCONFIG_NORICH: Incomplete
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


class CounterOrKeyValAction(BooleanFlagOrKeyValAction):

    def __call__(action,
                 parser,
                 namespace,
                 values,
                 option_string: Incomplete | None = ...) -> None:
        ...


class RawDescriptionDefaultsHelpFormatter(_RawDescriptionHelpFormatter,
                                          _ArgumentDefaultsHelpFormatter):
    group_name_formatter = str


class CompatArgumentParser(argparse.ArgumentParser):
    exit_on_error: Incomplete

    def __init__(self, *args, **kwargs) -> None:
        ...

    def parse_known_args(self,
                         args: Incomplete | None = ...,
                         namespace: Incomplete | None = ...):
        ...
