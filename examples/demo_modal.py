#!/usr/bin/env python
"""
Demo for a simple Modal CLI
"""
import scriptconfig as scfg


class FooCLI(scfg.DataConfig):
    __command__ = 'foo'

    option1 = scfg.Value(None, help='option1')

    @classmethod
    def main(cls, cmdline=1, **kwargs):
        self = cls.cli(cmdline=cmdline, data=kwargs)
        print('Called Foo with: ' + str(self))


class BarCLI(scfg.DataConfig):
    __alias__ = ['b', 'baz']
    __command__ = 'bar'
    __allow_abbrev__ = True

    option1 = scfg.Value(None, help='option1')

    @classmethod
    def main(cls, cmdline=1, **kwargs):
        self = cls.cli(cmdline=cmdline, data=kwargs)
        print('Called Bar with: ' + str(self))


class MyModalCLI(scfg.ModalCLI):

    __version__ = '1.2.3'
    __epilog__ = "This is an optional epilog"
    # __allow_abbrev__ = True   # Note: does not seem to work for modal subparsers

    foo = FooCLI
    bar = BarCLI


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/scriptconfig/examples/demo_modal.py --help
        python ~/code/scriptconfig/examples/demo_modal.py bar --help
        python ~/code/scriptconfig/examples/demo_modal.py bar --o f
        python ~/code/scriptconfig/examples/demo_modal.py bar --o f
        python ~/code/scriptconfig/examples/demo_modal.py f
    """
    MyModalCLI.main()
