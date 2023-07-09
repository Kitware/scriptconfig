import scriptconfig as scfg


# Using inheritance and the decorator lets you pickle the object
# verify legacy configs are pickleable


#@dataconf
class Legacy(scfg.Config):
    __default__ = {
        'default': scfg.Value((256, 256), help='chip size'),
        'keys0': [1, 2, 3],
        '__default__': {'argparse': 3.3, 'keys0': [4, 5]},
        'time_sampling': scfg.Value('soft2'),
    }


def test_legacy_pickle():
    print(f'Legacy.__module__={Legacy.__module__}')
    config = Legacy()
    import pickle
    serial = pickle.dumps(config)
    recon = pickle.loads(serial)
    assert recon.to_dict() == config.to_dict()
    assert 'locals' not in str(Legacy)
    assert 'recon' not in str(Legacy)


class SimpleData(scfg.DataConfig):
    __default__ = {
        'a': scfg.Value((256, 256), help='chip size'),
        'b': [1, 2, 3],
        'c': {'argparse': 3.3, 'keys0': [4, 5]},
        'd': scfg.Value('soft2'),
    }


def test_pickle2():
    config = SimpleData()
    import pickle
    serial = pickle.dumps(config)
    recon = pickle.loads(serial)
    assert recon.to_dict() == config.to_dict()
    assert 'locals' not in str(SimpleData)
    assert 'recon' not in str(SimpleData)


# With extra
@scfg.dataconf
class DecorDataConf1(scfg.DataConfig):
    __default__ = {
        'a': scfg.Value((256, 256), help='chip size'),
        'b': [1, 2, 3],
        'c': {'argparse': 3.3, 'keys0': [4, 5]},
        'd': scfg.Value('soft2'),
    }


def test_pickle3():
    config = DecorDataConf1()
    import pickle
    serial = pickle.dumps(config)
    recon = pickle.loads(serial)
    assert recon.to_dict() == config.to_dict()
    assert 'locals' not in str(DecorDataConf1)
    assert 'recon' not in str(DecorDataConf1)


class DecorDataConf2_(scfg.DataConfig):
    a = scfg.Value((256, 256), help='chip size')
    b = [1, 2, 3]
    c = {'argparse': 3.3, 'keys0': [4, 5]}
    d = scfg.Value('soft2')


def test_pickle4():
    DecorDataConf2 = scfg.dataconf(DecorDataConf2_)
    print(sorted(vars()))
    print(f'__name__={__name__}')
    print(f'__package__={__package__}')
    print(f'__module__={__name__}')
    print(f'DecorDataConf2_.__module__={DecorDataConf2_.__module__}')
    print(f'DecorDataConf2.__module__={DecorDataConf2.__module__}')
    config = DecorDataConf2()
    import pickle
    serial = pickle.dumps(config)
    recon = pickle.loads(serial)
    assert recon.to_dict() == config.to_dict()
    assert 'locals' not in str(DecorDataConf2)
    assert 'recon' not in str(DecorDataConf2)
