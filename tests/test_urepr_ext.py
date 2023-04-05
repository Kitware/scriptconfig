
def test_scriptconfig_repr():
    # TODO: maybe this extension lives in scriptconfig itself instead?
    import scriptconfig as scfg
    import ubelt as ub
    class MyConfig(scfg.DataConfig):
        arg1 = 1
        arg2 = 2

    c = MyConfig()
    text = ub.urepr(c, nl=1)
    assert text == ub.codeblock(
        '''
        MyConfig({
            'arg1': 1,
            'arg2': 2,
        })
        ''')
