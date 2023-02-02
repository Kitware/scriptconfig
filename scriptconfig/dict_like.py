"""
Defines :class:`DictLike` which is a mixin class that makes it easier for
objects to duck-type dictionaries.
"""


class DictLike:
    """
    An inherited class must specify the ``getitem``, ``setitem``, and
      ``keys`` methods.

    A class is dictionary like if it has:

    ``__iter__``, ``__len__``, ``__contains__``, ``__getitem__``, ``items``,
    ``keys``, ``values``, ``get``,

    and if it should be writable it should have:
    ``__delitem__``, ``__setitem__``, ``update``,

    And perhaps: ``copy``,


    ``__iter__``, ``__len__``, ``__contains__``, ``__getitem__``, ``items``,
    ``keys``, ``values``, ``get``,

    and if it should be writable it should have:
    ``__delitem__``, ``__setitem__``, ``update``,

    And perhaps: ``copy``,


    Example:
        from scriptconfig.dict_like import DictLike
        class DuckDict(DictLike):
            def __init__(self, _data=None):
                if _data is None:
                    _data = {}
                self._data = _data

            def getitem(self, key):
                return self._data[key]

            def keys(self):
                return self._data.keys()

        self = DuckDict({1: 2, 3: 4})
        print(f'self._data={self._data}')
        cast = dict(self)
        print(f'cast={cast}')
        print(f'self={self}')

    """

    def getitem(self, key):
        """
        Args:
            key (Any): the key

        Returns:
            Any : the associated value
        """
        raise NotImplementedError('abstract getitem function')

    def setitem(self, key, value):
        raise NotImplementedError('abstract setitem function')

    def delitem(self, key):
        raise NotImplementedError('abstract delitem function')

    def keys(self):
        """
        Yields:
            str:
        """
        raise NotImplementedError('abstract keys function')

    def __repr__(self):
        return repr(self.asdict())

    def __str__(self):
        return str(self.asdict())

    def __len__(self):
        return len(list(self.keys()))

    def __iter__(self):
        return iter(self.keys())

    def __contains__(self, key):
        return key in self.keys()

    def __delitem__(self, key):
        return self.delitem(key)

    def __getitem__(self, key):
        return self.getitem(key)

    def __setitem__(self, key, value):
        return self.setitem(key, value)

    def items(self):
        return ((key, self[key]) for key in self.keys())

    def values(self):
        return (self[key] for key in self.keys())

    def copy(self):
        return dict(self.items())

    def asdict(self):
        # Alias for to_dict
        return dict(self.items())

    def to_dict(self):
        # pandas like API
        return dict(self.items())

    def update(self, other):
        for k, v in other.items():
            self[k] = v

    def iteritems(self):
        import ubelt as ub
        ub.schedule_deprecation(
            'scriptconfig', 'iteritems', 'use items instead')
        return ((key, self[key]) for key in self.keys())

    def itervalues(self):
        import ubelt as ub
        ub.schedule_deprecation(
            'scriptconfig', 'itervalues', 'use items instead')
        return (self[key] for key in self.keys())

    def iterkeys(self):
        import ubelt as ub
        ub.schedule_deprecation(
            'scriptconfig', 'iterkeys', 'use items instead')
        return (key for key in self.keys())

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default
