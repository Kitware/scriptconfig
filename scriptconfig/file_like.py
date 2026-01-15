from __future__ import annotations

import os
from os.path import exists
from typing import IO, Any, Optional, Union


class FileLike:
    """
    Allows input to be a path or a file object
    """
    def __init__(self, path_or_file: Union[str, os.PathLike, IO[Any]],
                 mode: str = 'r') -> None:
        self._file: IO[Any]
        self._path: Optional[Union[str, os.PathLike]] = None
        self._file_obj: Optional[IO[Any]] = None
        if isinstance(path_or_file, (str, os.PathLike)):
            _input_type = 'path'
            if not exists(path_or_file):
                raise ValueError('Path {} does not exist'.format(path_or_file))
            self._path = path_or_file
        else:
            if hasattr(path_or_file, 'readable'):
                _input_type = 'file'
                if not path_or_file.readable():
                    raise ValueError('file must be readable')
                self._file_obj = path_or_file
            else:
                raise TypeError('input must be a path or readable file')
        if 'r' not in mode:
            raise ValueError('file must be readable')
        self.mode = mode
        self._input_type = _input_type

    def __enter__(self) -> IO[Any]:
        if self._input_type == 'path':
            if self._path is None:
                raise AssertionError('Expected a file path')
            self._file = open(self._path, self.mode)
        else:
            if self._file_obj is None:
                raise AssertionError('Expected a readable file')
            self._file = self._file_obj
        return self._file

    def __exit__(self, *args: Any) -> None:
        if self._input_type == 'path':
            self._file.close()
