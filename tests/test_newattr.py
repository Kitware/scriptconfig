def test_newattr():
    """
    Create an empty config and test different ways of adding new attributes.
    Test allowed and disallowed cases.
    """

    import scriptconfig as scfg
    import pytest
    class TestNewattrCLI(scfg.DataConfig):
        ...

    config = TestNewattrCLI()

    # By default new attributes are not allowed via the dictionary interface
    with pytest.raises(Exception):
        config['newattr1'] = 123

    # Quirk: they are allowed via setattr, but they do not become part of the
    # config. This is something we could change.
    config.newattr2 = 456
    assert 'newattr2' in config.__dict__
    assert 'newattr2' not in config
    assert config.newattr2 == 456, (
        'even though it is not in the config, you can still access it '
        'to cary info around')
    print(f'config={config}')
    print(f'config.__dict__={config.__dict__}')

    config = TestNewattrCLI()
    # Enable experimental newattr
    config.__allow_newattr__ = True

    config['newattr1'] = 123
    config.newattr2 = 456

    assert 'newattr2' in config
    assert 'newattr1' in config
    print(f'config={config}')


if __name__ == '__main__':
    """

    CommandLine:
        python ~/code/scriptconfig/tests/test_newattr.py
    """
    test_newattr()
