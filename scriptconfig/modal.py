import argparse as argparse_mod
import ubelt as ub
# from scriptconfig.config import MetaConfig


DEFAULT_GROUP = 'commands'


class class_or_instancemethod(classmethod):
    """
    Allows a method to behave as a class or instance method [SO28237955]_.

    References:
        .. [SO28237955] https://stackoverflow.com/questions/28237955/same-name-for-classmethod-and-instancemethod

    Example:
        >>> class X:
        ...     @class_or_instancemethod
        ...     def foo(self_or_cls):
        ...         if isinstance(self_or_cls, type):
        ...             return f"bound to the class"
        ...         else:
        ...             return f"bound to the instance"
        >>> print(X.foo())
        bound to the class
        >>> print(X().foo())
        bound to the instance
    """
    def __get__(self, instance, type_):
        descr_get = super().__get__ if instance is None else self.__func__.__get__
        return descr_get(instance, type_)


class MetaModalCLI(type):
    """
    A metaclass to help minimize boilerplate when defining a ModalCLI
    """

    @staticmethod
    def __new__(mcls, name, bases, namespace, *args, **kwargs):

        # Iterate over class attributes and register any Configs in the
        # __subconfigs__ dictionary.
        attr_subconfigs = {}
        for k, v in namespace.items():
            if not k.startswith('_') and isinstance(v, type):
                attr_subconfigs[k] = v

        final_subconfigs = list(attr_subconfigs.values())
        cls_subconfigs = namespace.get('__subconfigs__', [])
        final_subconfigs.extend(cls_subconfigs)

        # Helps make the class pickleable. Pretty hacky though.
        for k in attr_subconfigs:
            namespace.pop(k)
        namespace['__subconfigs__'] = final_subconfigs

        cls = super().__new__(mcls, name, bases, namespace, *args, **kwargs)
        return cls


class ModalCLI(metaclass=MetaModalCLI):
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
        commands:
          {command1,command2}  specify a command to run
            command1           argparse CLI generated by scriptconfig...
            command2           argparse CLI generated by scriptconfig...
        >>> self.run(argv=['command1'])
        config1 = {
            'foo': 'spam',
        }
        >>> self.run(argv=['command2', '--baz=buz'])
        config2 = {
            'foo': 'eggs',
            'baz': 'buz',
        }

    CommandLine:
        xdoctest -m scriptconfig.modal ModalCLI:1

    Example:
        >>> # Declarative modal CLI (new in 0.7.9)
        >>> import scriptconfig as scfg
        >>> class MyModalCLI(scfg.ModalCLI):
        >>>     #
        >>>     class Command1(scfg.DataConfig):
        >>>         __command__ = 'command1'
        >>>         foo = scfg.Value('spam', help='spam spam spam spam')
        >>>         @classmethod
        >>>         def main(cls, cmdline=1, **kwargs):
        >>>             config = cls.cli(cmdline=cmdline, data=kwargs)
        >>>             print('config1 = {}'.format(ub.urepr(dict(config), nl=1)))
        >>>     #
        >>>     class Command2(scfg.DataConfig):
        >>>         __command__ = 'command2'
        >>>         foo = 'eggs'
        >>>         baz = 'biz'
        >>>         @classmethod
        >>>         def main(cls, cmdline=1, **kwargs):
        >>>             config = cls.cli(cmdline=cmdline, data=kwargs)
        >>>             print('config2 = {}'.format(ub.urepr(dict(config), nl=1)))
        >>> #
        >>> MyModalCLI.main(argv=['command1'])
        >>> MyModalCLI.main(argv=['command2', '--baz=buz'])

    Example:
        >>> # Declarative modal CLI (new in 0.7.9)
        >>> import scriptconfig as scfg
        >>> class MyModalCLI(scfg.ModalCLI):
        >>>     ...
        >>> #
        >>> @MyModalCLI.register
        >>> class Command1(scfg.DataConfig):
        >>>     __command__ = 'command1'
        >>>     foo = scfg.Value('spam', help='spam spam spam spam')
        >>>     @classmethod
        >>>     def main(cls, cmdline=1, **kwargs):
        >>>         config = cls.cli(cmdline=cmdline, data=kwargs)
        >>>         print('config1 = {}'.format(ub.urepr(dict(config), nl=1)))
        >>> #
        >>> @MyModalCLI.register
        >>> class Command2(scfg.DataConfig):
        >>>     __command__ = 'command2'
        >>>     foo = 'eggs'
        >>>     baz = 'biz'
        >>>     @classmethod
        >>>     def main(cls, cmdline=1, **kwargs):
        >>>         config = cls.cli(cmdline=cmdline, data=kwargs)
        >>>         print('config2 = {}'.format(ub.urepr(dict(config), nl=1)))
        >>> #
        >>> MyModalCLI.main(argv=['command1'])
        >>> MyModalCLI.main(argv=['command2', '--baz=buz'])
    """
    __subconfigs__ = []

    def __init__(self, description='', sub_clis=None, version=None):
        if sub_clis is None:
            sub_clis = []

        if self.__class__.__name__ != 'ModalCLI':
            self.description = description or ub.codeblock(self.__doc__ or '')
        else:
            self.description = description

        self._instance_subconfigs = sub_clis + self.__subconfigs__
        self.version = version

    def __call__(self, cli_cls):
        """ alias of register """
        return self.register(cli_cls)

    @property
    def sub_clis(self):
        # backwards compat
        return self._instance_subconfigs

    @class_or_instancemethod
    def register(cls_or_self, cli_cls):
        """
        Args:
            cli_cli (scriptconfig.Config):
                A CLI-aware config object to register as a sub CLI
        """
        # Note: the order or registration is how it will appear in the CLI help
        # Hack for older scriptconfig
        # if not hasattr(cli_cls, 'default'):
        #     cli_cls.default = cli_cls.__default__
        if isinstance(cls_or_self, type):
            # Called as a class method
            cls_or_self.__subconfigs__.append(cli_cls)
        else:
            # Called as an instance method
            cls_or_self._instance_subconfigs.append(cli_cls)
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

            if not hasattr(cli_cls, 'main'):
                raise ValueError(ub.paragraph(
                    f'''
                    The ModalCLI expects that registered subconfigs have a
                    ``main`` classmethod with the signature
                    ``main(cls, cmdline: bool, **kwargs)``,
                    but {cli_cls} is missing one.
                '''))

            parserkw = {}
            __alias__ = getattr(cli_cls, '__alias__', [])
            if __alias__:
                parserkw['aliases']  = __alias__

            group = getattr(cli_cls, '__group__', DEFAULT_GROUP)
            # group = 'FOO'

            if isinstance(cli_cls, ModalCLI):
                # Another modal layer
                modal = cli_cls
                cmdinfo_list.append({
                    'cmdname': cmdname,
                    'parserkw': parserkw,
                    'main_func': cli_cls.main,
                    'subconfig': modal,
                    'group': group,
                })
            else:
                # A leaf Config CLI
                subconfig = cli_cls()
                parserkw.update(subconfig._parserkw())
                parserkw['help'] = parserkw['description'].split('\n')[0]
                cmdinfo_list.append({
                    'cmdname': cmdname,
                    'parserkw': parserkw,
                    'main_func': cli_cls.main,
                    'subconfig': subconfig,
                    'group': group,
                })
        return cmdinfo_list

    def argparse(self, parser=None, special_options=...):

        from scriptconfig.argparse_ext import RawDescriptionDefaultsHelpFormatter
        if parser is None:
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

        # The subparser is what enables the modal CLI. It will redirect a
        # command to a chosen subparser.
        # group_to_cmdinfos = ub.group_items(cmdinfo_list, key=lambda x: x['group'])

        # TODO: groups?
        # https://stackoverflow.com/questions/32017020/grouping-argparse-subparser-arguments

        _command_choices = [d['cmdname'] for d in cmdinfo_list]
        _metavar = '{' + ','.join(_command_choices) + '}'
        command_subparsers = parser.add_subparsers(
            title='commands', help='specify a command to run', metavar=_metavar)

        # group_to_subparser = {}
        # for group, cmdinfos in group_to_cmdinfos.items():
        #     ...

        for cmdinfo in cmdinfo_list:
            # group = cmdinfo['group']
            # Add a new command to subparser_group
            subparser = command_subparsers.add_parser(
                cmdinfo['cmdname'], **cmdinfo['parserkw'])
            subparser = cmdinfo['subconfig'].argparse(subparser)
            subparser.set_defaults(main=cmdinfo['main_func'])
        return parser

    build_parser = argparse

    @class_or_instancemethod
    def main(self, argv=None, strict=True):
        """
        Execute the modal CLI as the main script
        """
        if isinstance(self, type):
            self = self()

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

        if strict:
            ns = parser.parse_args(args=argv)
        else:
            ns, _ = parser.parse_known_args(args=argv)

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

    run = main  # alias for backwards compatiability
