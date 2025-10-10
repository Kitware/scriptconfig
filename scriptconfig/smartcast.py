__all__ = ['smartcast']

NoneType = type(None)


def smartcast(item, astype=None, strict=False, allow_split='auto'):
    r"""
    Converts a string into a standard python type.

    In many cases this is a simple alternative to `eval`. However, the syntax
    rules use here are more permissive and forgiving.

    The `astype` can be specified to provide a type hint, otherwise we try to
    cast to the following types in this order: int, float, complex, bool, none,
    list, tuple.

    Args:
        item (str | Any):
            represents some data of another type.

        astype (type | None):
            if None, try infer what the best type is, if astype == 'eval' then
            try to return `eval(item)`, Otherwise, try to cast to this type.
            Default to None.

        strict (bool):
            if True raises a TypeError if conversion fails.
            Default to False.

        allow_split (bool):
            if True will interpret strings with commas as sequences.
            Defaults to "auto", which pre 1.0 will default to True and warn the
            user. In version 1.0 we will change the default to False.

    Returns:
        Any: some item

    Raises:
        TypeError: if we cannot determine the type

    Example:
        >>> # Simple cases
        >>> print(repr(smartcast('?')))
        >>> print(repr(smartcast('1')))
        >>> print(repr(smartcast('1,2,3')))
        >>> print(repr(smartcast('abc')))
        >>> print(repr(smartcast('[1,2,3,4]')))
        >>> print(repr(smartcast('foo.py,/etc/conf.txt,/baz/biz,blah')))
        '?'
        1
        [1, 2, 3]
        'abc'
        [1, 2, 3, 4]
        ['foo.py', '/etc/conf.txt', '/baz/biz', 'blah']

        >>> # Weird cases
        >>> print(repr(smartcast('[1],2,abc,4')))
        ['[1]', 2, 'abc', 4]

    Example:
        >>> from scriptconfig.smartcast import *
        >>> assert smartcast('?') == '?'
        >>> assert smartcast('1') == 1
        >>> assert smartcast('1.0') == 1.0
        >>> assert smartcast('1.2') == 1.2
        >>> assert smartcast('True') is True
        >>> assert smartcast('false') is False
        >>> assert smartcast('None') is None
        >>> assert smartcast('1', str) == '1'
        >>> assert smartcast('1', eval) == 1
        >>> assert smartcast('1', bool) is True
        >>> assert smartcast('[1,2]', eval) == [1, 2]
        >>> assert smartcast('a,b', allow_split=False) == 'a,b'
        >>> assert smartcast('a,b', allow_split=True) == ['a', 'b']

    Example:
        >>> def check_typed_value(item, want, astype=None):
        >>>     got = smartcast(item, astype)
        >>>     assert got == want and isinstance(got, type(want)), (
        >>>         'Cast {!r} to {!r}, but got {!r}'.format(item, want, got))
        >>> check_typed_value('?', '?')
        >>> check_typed_value('1', 1)
        >>> check_typed_value('1.0', 1.0)
        >>> check_typed_value('1.2', 1.2)
        >>> check_typed_value('True', True)
        >>> check_typed_value('None', None)
        >>> check_typed_value('1', 1, int)
        >>> check_typed_value('1', True, bool)
        >>> check_typed_value('1', 1.0, float)
        >>> check_typed_value(1, 1.0, float)
        >>> check_typed_value(1.0, 1.0)
        >>> check_typed_value([1.0], (1.0,), 'tuple')
    """
    if callable(astype):
        if getattr(astype, '__name__', '') in {'smartcast', '_smart_type'}:
            astype = None
        else:
            _strastype = str(astype)
            # Pathological case, where we have astype specified as a partial
            # version of ourself, which happens with boolean values.
            # need to fix this more robustly.
            if '.partial' in _strastype and 'smartcast' in _strastype:
                return astype(item)

    # Hack handling the smartcast:v1 type should have been taken care of
    # elsewhere, but it is apparently not, so do it here too as a quick fix.
    if isinstance(astype, str) and astype == 'smartcast:v1':
        if allow_split == 'auto':
            allow_split = False
            astype = None
        else:
            raise Exception

    if isinstance(item, str):
        if astype is None:
            candidate_type_list = [int, float, complex, bool, NoneType]
            if ',' in item:
                # NOTE: THIS TRIES TO BE TOO CLEVER AND FAILS. We need to
                # depreate this behavior where it will automagically split
                # commas. We need to simplify the behavior and have the user
                # explicitly enable similar behavior.

                # The auto int / float / bool parts are fine. The auto list
                # part is what is causing the problem. Perhaps we should just
                # use YAML.

                # Plan:
                # 1. Add a allow_split flag that defaults to 'auto' and if this case
                # is hit.
                # 2. If this case is hit and the allow_split flag is auto, warn the
                # user that the behavior will change in the future.
                # 3. For now have auto default to True.
                # 4. In the future change the default to False.

                if allow_split == 'auto':
                    import warnings
                    warnings.warn(
                        'smartcast has been given a string with commas and the '
                        'allow_split="auto". Currently this will default to True and split the string into a list. '
                        'After version 1.0 the default will change to False and strings will not be split into lists by default '
                        'To disable this warning explicitly set allow_split=True to keep the string splitting behavior or allow_split=False '
                        'to disable it and use the new default behavior. '
                        'If using this in a Value object, you can prevent future incompatibility by '
                        'setting type=str and handling casting in the __post_init__ method of the DataConfig'
                    )
                    allow_split = True
                if allow_split:
                    candidate_type_list += [list, tuple, set]

            # Try each candidate in the type list until something works
            for astype in candidate_type_list:
                try:
                    return _as_smart_type(item, astype)
                except (TypeError, ValueError):
                    pass

            if strict:
                raise TypeError('Could not smartcast item={!r}'.format(item))
            else:
                return item
        else:
            return _as_smart_type(item, astype)
    else:
        # Note this is not a common case, the input is typically a string
        # Might want to rethink behavior in this case.
        if astype is None:
            return item
        else:
            if astype == eval:
                return item
            elif isinstance(astype, str):
                if astype == 'eval':
                    _astype = _identity
                elif astype == 'int':
                    _astype = int
                elif astype == 'bool':
                    _astype = bool
                elif astype == 'float':
                    _astype = float
                elif astype == 'complex':
                    _astype = complex
                elif astype == 'str':
                    _astype = str
                elif astype == 'tuple':
                    _astype = tuple
                elif astype == 'list':
                    _astype = list
                elif astype == 'set':
                    _astype = set
                elif astype == 'frozenset':
                    _astype = frozenset
                else:
                    raise KeyError('unknown string astype={!r}'.format(astype))
                return _astype(item)
            else:
                return astype(item)


def _as_smart_type(item, astype):
    """
    casts item to type, and tries to be clever when item is a string, otherwise
    it simply calls `astype(item)`.

    Args:
        item (str): represents some data of another type.
        astype (type | str): type to attempt to cast to

    Returns:
        object:

    Example:
        >>> assert _as_smart_type('1', int) == 1
        >>> assert _as_smart_type('1', str) == '1'
        >>> assert _as_smart_type('1', bool) is True
        >>> assert _as_smart_type('0', bool) is False
        >>> assert _as_smart_type('1', float) == 1.0
        >>> assert _as_smart_type('1', list) == [1]
        >>> assert _as_smart_type('(1,3)', 'eval') == (1, 3)
        >>> assert _as_smart_type('(1,3)', eval) == (1, 3)
        >>> assert _as_smart_type('1::3', slice) == slice(1, None, 3)
    """
    if not isinstance(item, str):
        raise TypeError('item must be a string')

    if astype is NoneType:
        return _smartcast_none(item)
    elif astype is bool:
        return _smartcast_bool(item)
    elif astype is slice:
        return _smartcast_slice(item)
    elif astype in [int, float, complex]:
        return astype(item)
    elif astype is str:
        return item
    elif astype is eval:
        import ast
        return ast.literal_eval(item)
    elif astype in [list, tuple, set, frozenset]:
        # TODO:
        # use parse_nestings to smartcast complex lists/tuples/sets
        return _smartcast_simple_sequence(item, astype)
    elif isinstance(astype, str):
        # allow types to be given as strings
        astype = {
            'bool': bool,
            'int': int,
            'float': float,
            'complex': complex,
            'str': str,
            'eval': eval,
            'none': NoneType,
        }[astype.lower()]
        return _as_smart_type(item, astype)
    raise NotImplementedError('Unknown smart astype=%r' % (astype,))


def _smartcast_slice(item):
    args = [int(p) if p else None for p in item.split(':')]
    return slice(*args)


def _smartcast_none(item):
    """
    Casts a string to None.
    """
    if item.lower() == 'none':
        return None
    else:
        raise TypeError('string does not represent none')


def _smartcast_bool(item):
    """
    Casts a string to a boolean.
    Setting strict=False allows '0' and '1' to be used as a bool
    """
    lower = item.lower()
    if lower == 'true':
        return True
    elif lower == 'false':
        return False
    else:
        try:
            return bool(int(item))
        except TypeError:
            pass
        raise TypeError('item does not represent boolean')


def _smartcast_simple_sequence(item, astype=list):
    """
    Casts only the simplest strings to a sequence. Cannot handle any nesting.

    Example:
        >>> assert _smartcast_simple_sequence('1') == [1]
        >>> assert _smartcast_simple_sequence('[1]') == [1]
        >>> assert _smartcast_simple_sequence('[[1]]') == ['[1]']
        >>> item = "[1,2,3,]"
        >>> _smartcast_simple_sequence(item)
    """
    nesters = {list: '[]', tuple: '()', set: '{}', frozenset: '{}'}
    nester = nesters.pop(astype)
    item = item.strip()
    if item.startswith(nester[0]) and item.endswith(nester[1]):
        item = item[1:-1]
    elif any(item.startswith(nester[0]) and item.endswith(nester[1])
             for nester in nesters.values()):
        raise ValueError('wrong nester')
    parts = [p.strip() for p in item.split(',')]
    parts = [p for p in parts if p]
    return astype(smartcast(p) for p in parts)


def _identity(arg):
    """ identity function """
    return arg


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/scriptconfig/scriptconfig/smartcast.py
    """
    import xdoctest
    xdoctest.doctest_module(__file__)
