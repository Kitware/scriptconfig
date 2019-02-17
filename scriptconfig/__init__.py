"""
mkinit ~/code/scriptconfig/scriptconfig/__init__.py
"""

__version__ = '0.0.1'

from .config import (Config,)
from .dict_like import (DictLike,)
from .file_like import (FileLike,)
from .value import (Path, PathList, Value,)

__all__ = ['Config', 'DictLike', 'FileLike',
           'Path', 'PathList', 'Value']
