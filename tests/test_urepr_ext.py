
def test_scriptconfig_repr():
    import scriptconfig as scfg
    import ubelt as ub
    class MyConfig(scfg.DataConfig):
        arg1 = 1
        arg2 = 2

    c = MyConfig()
    text = ub.urepr(c, nl=1)
    assert text == ub.codeblock(
        '''
        MyConfig(**{
            'arg1': 1,
            'arg2': 2,
        })
        ''')

    class MyConfig(scfg.Config):
        __default__ = dict(
            arg1=1,
            arg2=2,
        )

    c = MyConfig()
    text = ub.urepr(c, nl=1)
    assert text == ub.codeblock(
        '''
        MyConfig({
            'arg1': 1,
            'arg2': 2,
        })
        ''')
