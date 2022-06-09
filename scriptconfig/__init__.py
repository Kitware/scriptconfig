# -*- coding: utf-8 -*-
"""
mkinit ~/code/scriptconfig/scriptconfig/__init__.py --nomods --relative --diff
mkinit ~/code/scriptconfig/scriptconfig/__init__.py --nomods --relative -w
"""

__version__ = '0.6.1'

__submodules__ = ['config', 'value', 'cli']

from .config import (Config, define,)
from .value import (Path, PathList, Value,)
from .cli import (quick_cli,)

__all__ = ['Config', 'Path', 'PathList', 'Value', 'define', 'quick_cli']
