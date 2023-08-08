"""
Test porting back and forth to / from argparse
"""
import scriptconfig as scfg
import ubelt as ub
import argparse


def port_scriptconfig_from_argparse():
    """
    xdoctest ~/code/scriptconfig/tests/test_argparse_roundtrip.py port_scriptconfig_from_argparse
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--flag1', action='count')
    parser.add_argument('--flag2', action='store_true')
    parser.add_argument('--flag3', action='count', help='specified looooooooooooooooooooooonggg help ')
    parser.add_argument('--flag4', action='store_true', help='specified help')

    text = scfg.Config.port_argparse(parser)
    print(text)

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


def port_argparse_from_scriptconfig():
    """
    xdoctest ~/code/scriptconfig/tests/test_argparse_roundtrip.py port_argparse_from_scriptconfig
    """

    class MyConfig(scfg.DataConfig):
        param1 = scfg.Value(None, type=str, help='help text')

    argparse_text = MyConfig().port_to_argparse()

    want = ub.codeblock(
        """
        import argparse
        parser = argparse.ArgumentParser(
            description='argparse CLI generated by scriptconfig 0.7.11',
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        parser.add_argument('--param1', help='help text', type=str, dest='param1', required=False)
        """).replace('$', '')
    print(argparse_text)
    print(want)
    assert argparse_text == want
