#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
import scriptconfig as scfg


class DoFooCLI(scfg.DataConfig):
    __command__ = 'do_foo'
    option1 = scfg.Value(None, help='option1')

    @classmethod
    def main(cls, cmdline=1, **kwargs):
        self = cls.cli(cmdline=cmdline, data=kwargs)
        print('Called Foo with: ' + str(self))


class DoBarCLI(scfg.DataConfig):
    __command__ = 'do_bar'
    option1 = scfg.Value(None, help='option1')

    @classmethod
    def main(cls, cmdline=1, **kwargs):
        self = cls.cli(cmdline=cmdline, data=kwargs)
        print('Called Bar with: ' + str(self))


class MyModalCLI(scfg.ModalCLI):
    __version__ = '1.2.3'
    foo = DoFooCLI
    bar = DoBarCLI


if __name__ == '__main__':
    MyModalCLI().main()
