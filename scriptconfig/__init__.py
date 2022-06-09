# -*- coding: utf-8 -*-
"""
ScriptConfig
============

The goal of ``scriptconfig`` is to make it easy to be able to define a CLI by
**simply defining a dictionary**. Thie enables you to write simple configs and
update from CLI, kwargs, and/or json.

See the :mod:`scriptconfig.config` module docs for details and examples on
getting started.
"""

__autogen__ = """
Ignore:
    mkinit ~/code/scriptconfig/scriptconfig/__init__.py --nomods --relative --diff
    mkinit ~/code/scriptconfig/scriptconfig/__init__.py --nomods --relative -w
"""

__version__ = '0.6.1'

__submodules__ = ['config', 'value', 'cli']

from .config import (Config, define,)
from .value import (Path, PathList, Value,)
from .cli import (quick_cli,)

__all__ = ['Config', 'Path', 'PathList', 'Value', 'define', 'quick_cli']
