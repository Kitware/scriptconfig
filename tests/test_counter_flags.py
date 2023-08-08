

def test_counter_flags():
    import scriptconfig as scfg

    class MyConfig(scfg.DataConfig):
        flag0 = scfg.Value(False, short_alias=['e'], isflag=True)
        flag1 = scfg.Value(0, short_alias=['f'], isflag='counter')

    config = MyConfig.cli(argv=[])
    assert config.flag0 is False
    assert config.flag1 == 0

    config = MyConfig.cli(argv=['--flag0'])
    assert config.flag0 is True

    config = MyConfig.cli(argv=['-e'])
    assert config.flag0 is True

    config = MyConfig.cli(argv=['-f'])
    assert config.flag1 == 1

    # Double specifying normal flags does nothing
    config = MyConfig.cli(argv=['-e', '-e'])
    assert config.flag0 is True

    # Double specifying counter flags increments
    config = MyConfig.cli(argv=['-f', '-f'])
    assert config.flag1 == 2

    # Double specifying counter flags increments
    config = MyConfig.cli(argv=['-f', '-f', '--flag1'])
    assert config.flag1 == 3

    # Hard specifications overwrite the value
    config = MyConfig.cli(argv=['-f', '-f', '--flag1', '--flag1=231'])
    assert config.flag1 == 231

    # Hard specifications can be incremented after the fact
    config = MyConfig.cli(argv=['-f', '-f', '--flag1', '--flag1=231', '-f'])
    assert config.flag1 == 232

    if 0:
        # TODO: Can we fix the implementation to allow for this?
        # Hard specifications can be incremented after the fact
        config = MyConfig.cli(argv=['-fff'])
        assert config.flag1 == 3


def port_argparse_counter_to_scriptconfig():
    """
    xdoctest ~/code/scriptconfig/tests/test_counter_flags.py port_argparse_counter_to_scriptconfig
    """
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--flag1', action='count')
    parser.add_argument('--flag2', action='store_true')
    parser.add_argument('--flag3', action='count', help='specified looooooooooooooooooooooonggg help ')
    parser.add_argument('--flag4', action='store_true', help='specified help')

    import scriptconfig as scfg
    text = scfg.Config.port_argparse(parser)
    print(text)
    import ubelt as ub

    tq = '"""'

    want = ub.codeblock(
        """
        import ubelt as ub
        import scriptconfig as scfg

        class MyConfig(scfg.DataConfig):
            """ + tq + """
            $
            """ + tq + """
            flag1 = scfg.Value(None, isflag='counter', help=None)
            flag2 = scfg.Value(False, isflag=True, help=None)
            flag3 = scfg.Value(None, isflag='counter', help=ub.paragraph(
                    '''
                    specified looooooooooooooooooooooonggg help
                    '''))
            flag4 = scfg.Value(False, isflag=True, help='specified help')
        """).replace('$', '')
    print(text)
    print(want)
    assert text == want

    ns = {}
    exec(text, ns, ns)
    MyConfig = ns['MyConfig']

    # Note: we currently can't create argparse objects with the same flexible
    # flag or key/value specification. Future work may fix this.
    recon = MyConfig().port_to_argparse()
    print(recon)
