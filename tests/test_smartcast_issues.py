

def test_smartcast_interaction_with_isflag_type_is_respected():
    """
    In 0.8.1, when isflag=True, the type parameter was not respected.

    CommandLine:
        xdoctest -m tests/test_smartcast_issues.py test_smartcast_interaction_with_isflag_type_is_respected
    """
    import scriptconfig as scfg
    import ubelt as ub

    class MyConfig(scfg.DataConfig):
        param1 = scfg.Value(1, type=str, isflag=True)
        param2 = scfg.Value(2, type=str)
        param3 = scfg.Value(3, type='smartcast:legacy', isflag=True)
        param4 = scfg.Value(4, type='smartcast:legacy')

    # Check that no splitting occurs when type=str and isflag=True
    config1 = MyConfig.cli(argv='--param1=1,2,3 --param2=1,2,3 --param3=1,2,3 --param4=1,2,3')
    types1 = ub.udict(config1).map_values(lambda x: type(x).__name__)
    print(f'types = {ub.urepr(types1, nl=1)}')
    assert types1 == {'param1': 'str', 'param2': 'str', 'param3': 'list', 'param4': 'list'}


def test_smartcast_interaction_with_isflag_flagform_still_works():
    """
    Make sure that specifying a type of str does not impact the flagform of a CLI.

    CommandLine:
        xdoctest -m tests/test_smartcast_issues.py test_smartcast_interaction_with_isflag_flagform_still_works
    """
    # Check that no splitting occurs when type=str and isflag=True
    import scriptconfig as scfg
    import ubelt as ub

    class MyConfig(scfg.DataConfig):
        param1 = scfg.Value(0, type=str, isflag=True)
        param3 = scfg.Value(0, type='smartcast:legacy', isflag=True)
    config = dict(MyConfig.cli(argv=''))
    print(f'config = {ub.urepr(config, nl=1)}')
    assert config == {'param1': 0, 'param3': 0}

    config = dict(MyConfig.cli(argv='--param1 --param3'))
    print(f'config = {ub.urepr(config, nl=1)}')
    assert config == {'param1': True, 'param3': True}

    config = dict(MyConfig.cli(argv='--no-param1 --no-param3'))
    print(f'config = {ub.urepr(config, nl=1)}')
    assert config == {'param1': False, 'param3': False}


def test_smartcast_v1_respected():
    import scriptconfig as scfg
    import ubelt as ub

    class MyConfig(scfg.DataConfig):
        param1 = scfg.Value(0, type='smartcast:legacy')
        param2 = scfg.Value(0, type='smartcast:v1')
        param3 = scfg.Value(0, type='smartcast:legacy', isflag=True)
        param4 = scfg.Value(0, type='smartcast:v1', isflag=True)
    config = dict(MyConfig.cli(argv=' '.join([
        '--param1 "foo,bar"',
        '--param2 "foo,bar"',
        '--param3 "foo,bar"',
        '--param4 "foo,bar"',
    ])))
    print(f'config = {ub.urepr(config, nl=1)}')
    assert config == {
        'param1': ['foo', 'bar'],
        'param2': 'foo,bar',
        'param3': ['foo', 'bar'],
        'param4': 'foo,bar',
    }
