import scriptconfig as scfg


class DemoConfig(scfg.Config):
    default = {
        'num': 1,
        'mode': 'bar',
        'mode2': scfg.Value('bar', str),
        'ignore': ['baz', 'biz'],
    }


def test_cast_set():
    config = DemoConfig()
    keys = set(config)
    assert keys == set(config.keys())
