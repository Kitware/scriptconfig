
def test_post_init_not_called_twice():
    """
    xdoctest ~/code/scriptconfig/tests/test_post_init.py test_post_init_not_called_twice
    """
    import scriptconfig as scfg
    import ubelt as ub

    default = {
        'option1': scfg.Value((1, 2, 3), type=tuple, alias='a'),
        'option2': 'bar',
        'option3': None,
    }

    def postinit(self):
        print('Call PostInit For: self = {}, id={}'.format(ub.urepr(self, nl=1), id(self)))
        # import traceback
        # import sys
        # traceback.print_stack(file=sys.stdout)
        if not hasattr(self, '_post_init_count'):
            self._post_init_count  = 0
        self._post_init_count += 1

    class MyConfig(scfg.Config):
        __default__ = default
        __post_init__ = postinit

    class MyDataConfig(scfg.DataConfig):
        __default__ = default
        __post_init__ = postinit

    # Single initialization worked correctly in 0.7.10
    print('-- CONFIG 1 ---')
    config1 = MyDataConfig()
    assert config1._post_init_count == 1

    print('-- CONFIG 2 ---')
    config2 = MyConfig()
    assert config2._post_init_count == 1

    # However, in 0.7.10 calling cli caused a double call to __post_init__
    # Because it initializes the object and then calls load.
    print('-- CONFIG 3 ---')
    config3 = MyDataConfig.cli(argv=[])
    assert config3._post_init_count == 1

    print('-- CONFIG 4 ---')
    config4 = MyConfig.cli(argv=[])
    assert config4._post_init_count == 1

    # We do expect the load method to call post init a second time if the user
    # calls it, but internally we should prevent it.
    config4.load(data={})
    assert config4._post_init_count == 2

    config3.load(data={})
    assert config4._post_init_count == 2
