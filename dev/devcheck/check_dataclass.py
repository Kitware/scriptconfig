from dataclasses import dataclass
from scriptconfig import DataConfig
import ubelt as ub


@dataclass
class Data1:
    arg1 = 1
    arg2 = 2
    arg3 = 3


class Data2(Data1):
    arg4 = 4
    arg5 = 5
    arg6 = 6


class Data3(Data2):
    arg2 = 22
    arg3 = 33
    arg5 = 55


class Config1(DataConfig):
    arg1 = 1
    arg2 = 2
    arg3 = 3


class Config2(Config1):
    arg4 = 4
    arg5 = 5
    arg6 = 6


class Config3(Config2):
    arg2 = 22
    arg3 = 33
    arg5 = 55


def dc_dict(d):
    return {k: getattr(d, k) for k in dir(d) if not k.startswith('_')}


def main():
    from rich import print
    d1 = Data1()
    d2 = Data2()
    d3 = Data3()

    print('d1 = {}'.format(ub.urepr(dc_dict(d1), nl=1)))
    print('d2 = {}'.format(ub.urepr(dc_dict(d2), nl=1)))
    print('d3 = {}'.format(ub.urepr(dc_dict(d3), nl=1)))

    c1 = Config1()
    c2 = Config2()
    c3 = Config3()
    print('c1 = {}'.format(ub.urepr(c1, nl=1)))
    print('c2 = {}'.format(ub.urepr(c2, nl=1)))
    print('c3 = {}'.format(ub.urepr(c3, nl=1)))


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/scriptconfig/dev/devcheck/check_dataclass.py
    """
    main()
