import argparse as argparse_mod
import ubelt as ub


class RawDescriptionDefaultsHelpFormatter(
        argparse_mod.RawDescriptionHelpFormatter,
        argparse_mod.ArgumentDefaultsHelpFormatter):
    pass


class ModalCLI(object):
    """
    Contains multiple scriptconfig.Config items with corresponding `main`
    functions.

    CommandLine:
        xdoctest -m scriptconfig.modal ModalCLI

    Example:
        >>> from scriptconfig.modal import *  # NOQA
        >>> import scriptconfig as scfg
        >>> self = ModalCLI(description='A modal CLI')
        >>> #
        >>> @self.register
        >>> class Command1Config(scfg.Config):
        >>>     __command__ = 'command1'
        >>>     __default__ = {
        >>>         'foo': 'spam'
        >>>     }
        >>>     @classmethod
        >>>     def main(cls, cmdline=1, **kwargs):
        >>>         config = cls(cmdline=cmdline, data=kwargs)
        >>>         print('config1 = {}'.format(ub.urepr(dict(config), nl=1)))
        >>> #
        >>> @self.register
        >>> class Command2Config(scfg.DataConfig):
        >>>     __command__ = 'command2'
        >>>     foo = 'eggs'
        >>>     baz = 'biz'
        >>>     @classmethod
        >>>     def main(cls, cmdline=1, **kwargs):
        >>>         config = cls.cli(cmdline=cmdline, data=kwargs)
        >>>         print('config2 = {}'.format(ub.urepr(dict(config), nl=1)))
        >>> #
        >>> parser = self.argparse()
        >>> parser.print_help()
        ...
        A modal CLI
        ...
        options:
          -h, --help           show this help message and exit
        ...
        commands:
          {command1,command2}  specify a command to run
            command1           argparse CLI generated by scriptconfig
            command2           argparse CLI generated by scriptconfig
        >>> self.run(argv=['command1'])
        config1 = {
            'foo': 'spam',
        }
        >>> self.run(argv=['command2', '--baz=buz'])
        config2 = {
            'foo': 'eggs',
            'baz': 'buz',
        }
    """

    def __init__(self, description='', sub_clis=None, version=None):
        if sub_clis is None:
            sub_clis = []
        self.description = description
        self.sub_clis = sub_clis
        self.version = version

    def __call__(self, cli_cls):
        """ alias of register """
        return self.register(cli_cls)

    def register(self, cli_cls):
        # Note: the order or registration is how it will appear in the CLI help
        # Hack for older scriptconfig
        if not hasattr(cli_cls, 'default'):
            cli_cls.default = cli_cls.__default__
        self.sub_clis.append(cli_cls)
        return cli_cls

    def _build_subcmd_infos(self):
        cmdinfo_list = []
        for cli_cls in self.sub_clis:
            cmdname = getattr(cli_cls, '__command__', None)
            if cmdname is None:
                raise ValueError(ub.paragraph(
                    f'''
                    The ModalCLI expects that registered subconfigs have a
                    ``__command__: str`` attribute, but {cli_cls} is missing one.
                '''))
            subconfig = cli_cls()
            parserkw = {}
            __alias__ = getattr(cli_cls, '__alias__', [])
            if __alias__:
                parserkw['aliases']  = __alias__
            parserkw.update(subconfig._parserkw())
            parserkw['help'] = parserkw['description'].split('\n')[0]
            if not hasattr(cli_cls, 'main'):
                raise ValueError(ub.paragraph(
                    f'''
                    The ModalCLI expects that registered subconfigs have a
                    ``main`` classmethod with the signature
                    ``main(cls, cmdline: bool, **kwargs)``,
                    but {cli_cls} is missing one.
                '''))
            cmdinfo_list.append({
                'cmdname': cmdname,
                'parserkw': parserkw,
                'main_func': cli_cls.main,
                'subconfig': subconfig,
            })
        return cmdinfo_list

    def argparse(self):
        parser = argparse_mod.ArgumentParser(
            description=self.description,
            formatter_class=RawDescriptionDefaultsHelpFormatter,
        )

        if self.version is not None:
            parser.add_argument('--version', action='store_true',
                                help='show version number and exit')

        # Prepare information to be added to the subparser before it is created
        cmdinfo_list = self._build_subcmd_infos()

        # Build a list of primary command names to display as the valid options
        # for subparsers. This avoids cluttering the screen with all aliases
        # which happens by default.
        command_choices = [d['cmdname'] for d in cmdinfo_list]
        metavar = '{' + ','.join(command_choices) + '}'

        # The subparser is what enables the modal CLI. It will redirect a
        # command to a chosen subparser.
        subparser_group = parser.add_subparsers(
            title='commands', help='specify a command to run', metavar=metavar)

        for cmdinfo in cmdinfo_list:
            # Add a new command to subparser_group
            subparser = subparser_group.add_parser(
                cmdinfo['cmdname'], **cmdinfo['parserkw'])
            subparser = cmdinfo['subconfig'].argparse(subparser)
            subparser.set_defaults(main=cmdinfo['main_func'])
        return parser

    build_parser = argparse

    def run(self, argv=None):
        parser = self.argparse()

        try:
            import argcomplete
            # Need to run: "$(register-python-argcomplete xdev)"
            # or activate-global-python-argcomplete --dest=-
            # activate-global-python-argcomplete --dest ~/.bash_completion.d
            # To enable this.
        except ImportError:
            argcomplete = None

        if argcomplete is not None:
            argcomplete.autocomplete(parser)

        ns = parser.parse_args(args=argv)
        kw = ns.__dict__

        if kw.pop('version', None):
            print(self.version)
            return 0

        sub_main = kw.pop('main', None)
        if sub_main is None:
            parser.print_help()
            raise ValueError('no command given')
            return 1

        try:
            ret = sub_main(cmdline=False, **kw)
        except Exception as ex:
            print('ERROR ex = {!r}'.format(ex))
            raise
            return 1
        else:
            if ret is None:
                ret = 0
            return ret
