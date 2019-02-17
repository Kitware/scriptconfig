from os.path import exists
import six


class FileLike(object):
    """
    Allows input to be a path or a file object
    """
    def __init__(self, path_or_file, mode='r'):
        if isinstance(path_or_file, six.string_types):
            _input_type = 'path'
            if not exists(path_or_file):
                raise ValueError('Path {} does not exist'.format(path_or_file))
        else:
            if hasattr(path_or_file, 'readable'):
                _input_type = 'file'
                if not path_or_file.readable():
                    raise ValueError('file must be readable')
            else:
                raise TypeError('input must be a path or readable file')
        if 'r' not in mode:
            raise ValueError('file must be readable')
        self.mode = mode
        self._input_type = _input_type
        self._path_or_file = path_or_file

    def __enter__(self):
        if self._input_type == 'path':
            self._file = open(self._path_or_file, self.mode)
        else:
            self._file = self._path_or_file
        return self._file

    def __exit__(self, *args):
        if self._input_type == 'path':
            self._file.close()
