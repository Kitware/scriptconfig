"""
The difference between data and default is that default will update the
defaults and persist between multiple load operations whereas data will
only set the immediate values and not persist over multiple loads.
"""
import scriptconfig as scfg
import pytest


def generate_dataconfig_instance_variants():
    # In its simplest incarnation, the config class specifies default values.
    # For each configuration parameter.
    class ExampleConfig1(scfg.DataConfig):
        num = 1
        mode = 'bar'
        ignore = ['baz', 'biz']

    # Test with data configs
    config = ExampleConfig1()
    yield config, 'dataconfig'

    class ExampleConfig2(scfg.Config):
        __default__ = dict(
            num=1,
            mode='bar',
            ignore=['baz', 'biz'],
        )
    # Test with original configs
    config = ExampleConfig2()
    yield config, 'orig-dunder-default'

    with pytest.warns(Warning):
        class ExampleConfig3(scfg.Config):
            default = dict(
                num=1,
                mode='bar',
                ignore=['baz', 'biz'],
            )
    config = ExampleConfig3()
    yield config, 'orig-default'


@pytest.mark.parametrize('config, test_name', generate_dataconfig_instance_variants())
def test_data_vs_default(config, test_name):
    assert config['num'] == 1

    # Using load(data=kwargs) unions kwargs with the existing defaults
    # but does not change the defaults
    kwargs = {'num': 2}
    config = config.load(data=kwargs)
    assert config['num'] == 2
    assert config['mode'] == 'bar'

    # Calling load again will reset any unspecified params to the defaults
    kwargs = {'mode': 'foo'}
    config = config.load(data=kwargs)
    assert config['num'] == 1
    assert config['mode'] == 'foo'

    # Using load(default=kwargs) changes the defaults and then does the same
    # process.
    kwargs = {'num': 2}
    config = config.load(default=kwargs)
    assert config['num'] == 2
    assert config['mode'] == 'bar'

    # Calling again will show the defaults are changed
    kwargs = {'mode': 'foo'}
    config = config.load(default=kwargs)
    assert config['num'] == 2
    assert config['mode'] == 'foo'

    config = config.load()
    assert config['num'] == 2
    assert config['mode'] == 'foo'

    # Test that cmdline will overload a default
    config = config.load(cmdline='--num=3', default={'num': 4})
    assert config['num'] == 3
    # But the new default should persist
    config = config.load()
    assert config['num'] == 4

    # Test that data will overload a default
    config = config.load(data=dict(num=10), default={'num': 5})
    assert config['num'] == 10
    # But the new default should persist
    config = config.load()
    assert config['num'] == 5
