"""
Test that class attributes are correctly initialized.
"""


def test_class_inst_default_attr():
    """
    There are a lot of ways to access the defaults. We have

    default : class attribute
    __default__ : class attribute

    default : instance attribute
    __default__ : instance attribute

    _default : instance attribute
    """
    import scriptconfig as scfg
    import pytest

    with pytest.warns(Warning):
        class Config1(scfg.Config):
            default = {
                'option1': scfg.Value((1, 2, 3), tuple, alias='a'),
                'option2': 'bar',
                'option3': None,
            }

    class Config2(scfg.Config):
        __default__ = {
            'option1': scfg.Value((1, 2, 3), tuple, alias='a'),
            'option2': 'bar',
            'option3': None,
        }

    class DataConfig3(scfg.DataConfig):
        __default__ = {
            'option1': scfg.Value((1, 2, 3), tuple, alias='a'),
            'option2': 'bar',
            'option3': None,
        }

    class DataConfig4(scfg.DataConfig):
        # Note: in a data config you have to use "__default__", so we expect
        # this to fail.
        default = {
            'option1': scfg.Value((1, 2, 3), tuple, alias='a'),
            'option2': 'bar',
            'option3': None,
        }

    config1 = Config1()
    config2 = Config2()
    config3 = DataConfig3()
    config4 = DataConfig4()

    a = config1.to_dict()
    b = config2.to_dict()
    c = config3.to_dict()
    d = config4.to_dict()
    assert a == b == c
    assert a != d

    config_instances = [config1, config2, config3]

    import ubelt as ub
    for config in config_instances:
        defaults = ub.udict({
            'self._default': config._default,
            'self.__default__': config.__default__,
            'self.default': config.default,
            'cls.__default__': config.__class__.__default__,
            'cls.default': config.__class__.default,
        })
        default_ids = defaults.map_values(id)
        print('default_ids = {}'.format(ub.urepr(default_ids, nl=1, align=':')))
        assert ub.allsame((default_ids - {'self._default'}).values()), (
            'All default containers except for _default should be the same'
        )
        assert default_ids['self._default'] != default_ids['self.__default__']


def test_class_inst_normalize_attr():
    """
    The normalize and __post_init__ methods should function equivalently
    """
    import scriptconfig as scfg
    import ubelt as ub
    import pytest

    test_state = ub.ddict(lambda: 0)

    config_classes = []

    common_default = {
        'opt1': scfg.Value(None, alias=['option1']),
        'opt2': scfg.Value(None, alias=['option2', 'old_name']),
    }

    with pytest.warns(Warning):
        @config_classes.append
        class Config1A(scfg.Config):
            __default__ = common_default
            def normalize(self):
                test_state[self.__class__.__name__ + '.normalize'] += 1
                self['opt1'] = 'normalized'

    @config_classes.append
    class Config1B(scfg.Config):
        __default__ = common_default
        def __post_init__(self):
            test_state[self.__class__.__name__ + '.__post_init__'] += 1
            self['opt1'] = 'post-initialized'

    @config_classes.append
    class Config1C(scfg.Config):
        __default__ = common_default

        def __post_init__(self):
            test_state[self.__class__.__name__ + '.__post_init__'] += 1
            self['opt1'] = 'post-initialized'

        def normalize(self):
            test_state[self.__class__.__name__ + '.normalize'] += 1
            self['opt1'] = 'normalized'

    with pytest.warns(Warning):
        @config_classes.append
        class DataConfig2A(scfg.DataConfig):
            __default__ = common_default
            def normalize(self):
                test_state[self.__class__.__name__ + '.normalize'] += 1
                self['opt1'] = 'normalized'

    @config_classes.append
    class DataConfig2B(scfg.DataConfig):
        __default__ = common_default
        def __post_init__(self):
            test_state[self.__class__.__name__ + '.__post_init__'] += 1
            self['opt1'] = 'post-initialized'

    @config_classes.append
    class DataConfig2C(scfg.DataConfig):
        __default__ = common_default

        def __post_init__(self):
            test_state[self.__class__.__name__ + '.__post_init__'] += 1
            self['opt1'] = 'post-initialized'

        def normalize(self):
            test_state[self.__class__.__name__ + '.normalize'] += 1
            self['opt1'] = 'normalized'

    instances = {}
    for cls in config_classes:
        instances[cls.__name__] = cls()

    assert len(instances) == len(test_state) == 6
    assert all(v == 1 for v in test_state.values()), (
        'Only normalize or __post_init__ should be called, depending on '
        'which one is defined.'
    )

    # post-init should be used over normalize when available
    assert instances['Config1A']['opt1'] == 'normalized'
    assert instances['Config1B']['opt1'] == 'post-initialized'
    assert instances['Config1C']['opt1'] == 'post-initialized'
    assert instances['DataConfig2A']['opt1'] == 'normalized'
    assert instances['DataConfig2B']['opt1'] == 'post-initialized'
    assert instances['DataConfig2C']['opt1'] == 'post-initialized'
