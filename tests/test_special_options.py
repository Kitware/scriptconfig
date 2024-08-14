def test_without_special_options():
    """
    The "special options" of "config", "dump", and "dumps" are useful but they
    prevent the user from being able to use them as official config args.
    """
    import scriptconfig as scfg
    class MyConfig(scfg.DataConfig):
        config = None

    # Without using the ``cli`` classmethod there should be no issue with using
    # these "special options".
    config = MyConfig()
    assert config.config is None

    # But, if special options are enabled we cannot have options that conflict
    import pytest
    with pytest.raises(Exception):
        config = MyConfig.cli(argv=['--config=foo'], special_options=True)

    # But setting special_options=False will allow for this
    config = MyConfig.cli(argv=['--config=foo'], special_options=False)
    assert config.config == 'foo'
