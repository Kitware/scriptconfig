"""
mkinit ~/code/scriptconfig/scriptconfig/__init__.py
"""

__version__ = '0.3.0.dev0'

from .config import (Config, DataInterchange, scfg_isinstance,)
from .dict_like import (DictLike,)
from .file_like import (FileLike,)
from .smartcast import (BooleanType, NoneType, smartcast,)
from .value import (Path, PathList, Value,)

__all__ = ['BooleanType', 'Config', 'DataInterchange', 'DictLike', 'FileLike',
           'NoneType', 'Path', 'PathList', 'Value', 'scfg_isinstance',
           'smartcast']
