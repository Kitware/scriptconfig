#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""
CommandLine:
    cd ~/code/scriptconfig
    python examples/basic.py --help

    # The command line if flexible by default
    python examples/basic.py --my-option1=3
    python examples/basic.py --my_option1=4
    python examples/basic.py "a positional arg"
    python examples/basic.py --position-arg "positional args can always be given as key/value pairs"
"""
import scriptconfig as scfg
import ubelt as ub
import rich
import rich.markup


class MyConfig(scfg.DataConfig):
    position_arg = scfg.Value(None, help='position argument', position=1)
    my_option1 = scfg.Value(None, help='option1')
    my_option2 = scfg.Value(None, help='option2')

    @classmethod
    def main(cls, cmdline=1, **kwargs):
        self = cls.cli(cmdline=cmdline, data=kwargs)
        rich.print('Called My Script With: ' + rich.markup.escape(ub.urepr(self)))


if __name__ == '__main__':
    MyConfig().main()
