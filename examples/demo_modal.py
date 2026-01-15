#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
import scriptconfig as scfg


class DoFooCLI(scfg.DataConfig):
    option1 = scfg.Value(None, help='option1')

    @classmethod
    def main(cls, argv=1, **kwargs):
        self = cls.cli(argv=argv, data=kwargs)
        print('Called Foo with: ' + str(self))


class DoBarCLI(scfg.DataConfig):
    option1 = scfg.Value(None, help='option1')

    @classmethod
    def main(cls, argv=1, **kwargs):
        self = cls.cli(argv=argv, data=kwargs)
        print('Called Bar with: ' + str(self))


class MyModalCLI(scfg.ModalCLI):
    __version__ = '1.2.3'
    do_foo = DoFooCLI
    do_bar = DoBarCLI


if __name__ == '__main__':
    MyModalCLI().main()
