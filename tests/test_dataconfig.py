import scriptconfig as scfg


def test_dataconfig_setattr_simple():
    import pytest

    class ExampleDataConfig(scfg.DataConfig):
        x: int = 0
        y: str = 3

    self = ExampleDataConfig()

    print(f'self.__dict__={self.__dict__}')
    print(f'self.x={self.x}')
    new_val = 432
    self['x'] = new_val
    assert 'x' not in self.__dict__
    assert self['x'] == new_val
    assert self.x == new_val

    new_val = 433
    self.x = new_val
    assert 'x' not in self.__dict__
    assert self['x'] == new_val
    assert self.x == new_val

    new_val = 434
    self['x'] = new_val
    assert 'x' not in self.__dict__
    assert self['x'] == new_val
    assert self.x == new_val

    new_val = 435
    self.x = new_val
    assert 'x' not in self.__dict__
    assert self['x'] == new_val
    assert self.x == new_val

    with pytest.raises(AttributeError):
        self.notakey
    self.notakey = 100
    assert 'notakey' not in self
    assert 'notakey' in self.__dict__
    with pytest.raises(AttributeError):
        self['notakey']
    assert self.notakey == 100


def test_dataconfig_setattr_combos():

    class ExampleDataConfig(scfg.DataConfig):
        x: int = 0
        y: str = 3

    self = ExampleDataConfig()

    def setmethod_item(self, key, value):
        # Test setting the value by using __setitem__
        self[key] = value

    def setmethod_attr(self, key, value):
        # Test setting the value by using __setattr__
        setattr(self, key, value)

    def getmethod_item(self, key):
        return self[key]

    def getmethod_attr(self, key):
        return getattr(self, key)

    import ubelt as ub
    import itertools as it
    grid = list(ub.named_product({
        'key': ['x'],
        'setmethod': [setmethod_item, setmethod_attr],
        'getmethod': [getmethod_item, getmethod_attr],
    }))
    tasks = list(ub.flatten(it.permutations(grid, len(grid))))
    for new_value, task in enumerate(tasks, start=101):
        task['new_value'] = new_value

    for task in tasks:
        key = task['key']
        setmethod = task['setmethod']
        getmethod = task['getmethod']
        new_val = task['key']
        old_val = getmethod(self, key)
        assert new_val != old_val
        assert key in self
        assert key not in self.__dict__
        setmethod(self, key, new_value)
        assert getmethod(self, key) == new_value
        assert key in self
        assert key not in self.__dict__


class test_dataconfig_warning():
    """
    Test that the user gets a warning if they make this common mistake
    """
    import scriptconfig as scfg
    import pytest
    with pytest.warns(UserWarning):
        class ExampleDataConfig(scfg.DataConfig):
            x = scfg.Value(None),
