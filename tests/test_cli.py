import scriptconfig as scfg


def test_cli_dataconfig():

    class ConfigCls(scfg.DataConfig):
        x: int = 0
        y: str = 3

    _test_common_cli_classmethod(ConfigCls)


def test_cli_dataconfig_with_alias():

    class ConfigCls(scfg.DataConfig):
        foo = scfg.Value(0, alias=['x'], type=int)
        y: str = 3

    _test_common_cli_classmethod(ConfigCls)


def test_cli_config_with_alias():

    class ConfigCls(scfg.DataConfig):
        __default__ = dict(
            foo=scfg.Value(0, alias=['x'], type=int),
            y=3,
        )

    _test_common_cli_classmethod(ConfigCls)


def test_cli_config():

    class ConfigCls(scfg.Config):
        __default__ = {
            'x': 0,
            'y': 3,
        }
    _test_common_cli_classmethod(ConfigCls)


def _test_common_cli_classmethod(ConfigCls):

    config = ConfigCls.cli(argv=[])
    assert config['x'] == 0

    config = ConfigCls.cli(argv=['--x', '3'])
    assert config['x'] == 3

    config = ConfigCls.cli(argv=['--z', '3'], strict=False)
    assert config['x'] == 0

    import pytest
    with pytest.raises(SystemExit):
        config = ConfigCls.cli(argv=['--z', '3'], strict=True)

    config = ConfigCls.cli(default={'x': 4}, argv=[])
    assert config['x'] == 4

    config = ConfigCls.cli(data={'x': 4}, argv=[])
    assert config['x'] == 4

    config = ConfigCls.cli(default={'x': 4}, argv=['--x=5'])
    assert config['x'] == 5

    config = ConfigCls.cli(data={'x': 4}, argv=['--x=5'])
    assert config['x'] == 5
