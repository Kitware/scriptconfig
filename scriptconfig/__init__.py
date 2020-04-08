# -*- coding: utf-8 -*-
"""
mkinit ~/code/scriptconfig/scriptconfig/__init__.py --nomods --relative
"""

__version__ = '0.5.6'

from .config import (Config,)
from .value import (Path, PathList, Value,)
from .cli import (quick_cli,)

__all__ = ['Config', 'Path', 'PathList', 'Value', 'quick_cli']
