"""
mkinit ~/code/scriptconfig/scriptconfig/__init__.py --nomods --relative
"""

__version__ = '0.5.1'

from .config import (Config,)
from .value import (Path, PathList, Value,)

__all__ = ['Config', 'Path', 'PathList', 'Value']
