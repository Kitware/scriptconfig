#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
import scriptconfig as scfg
import ubelt as ub


class TemplateCLI(scfg.DataConfig):
    """
    Generate boilerplate for a template CLI script.
    """
    __command__ = 'template'

    type = scfg.Value('single', help='The type of CLI to make', choices=['single', 'modal'], position=1)

    name = scfg.Value('Template', help='The name of the config', position=2)

    verbose = scfg.Value(False)

    @classmethod
    def main(cls, argv=1, **kwargs):
        """
        Example:
            >>> # xdoctest: +SKIP
            >>> from scriptconfig._cli.template import *  # NOQA
            >>> argv = 0
            >>> kwargs = dict()
            >>> cls = TemplateCLI
            >>> config = cls(**kwargs)
            >>> cls.main(argv=argv, **config)
        """
        config = cls.cli(argv=argv, data=kwargs, strict=True, verbose='auto')
        if config.type == 'single':
            text = _build_single_template(config)
        elif config.type == 'modal':
            text = _build_modal_template(config)
        print(ub.highlight_code(text, 'python'))


def _build_single_template(config):

    classname = f'{config.name}Config'

    text = ub.codeblock(
        f'''
        #!/usr/bin/env python3
        # PYTHON_ARGCOMPLETE_OK
        import scriptconfig as scfg


        class {classname}(scfg.DataConfig):
            """
            Write your documentation here
            """

            # List your default parameters here
            # param1 = scfg.Value(None, help='your parameter help string')

            @classmethod
            def main(cls, argv=1, **kwargs):
                """
                Example:
                    >>> # xdoctest: +SKIP
                    >>> # It's a good idea to setup a doctest.
                    >>> argv = False
                    >>> kwargs = dict()
                    >>> cls = {classname}
                    >>> config = cls(**kwargs)
                    >>> cls.main(argv=argv, **config)
                """
                config = cls.cli(argv=argv, data=kwargs, strict=True, verbose='auto')

        __cli__ = {classname}

        if __name__ == '__main__':
            __cli__.main()
        ''')
    return text


def _build_modal_template(config):

    classname = f'{config.name}Modal'

    text = ub.codeblock(
        f'''
        #!/usr/bin/env python3
        # PYTHON_ARGCOMPLETE_OK
        import scriptconfig as scfg
        # from module.cli.script import ScriptCLI

        class {classname}(scfg.ModalCLI):
            """
            Your description here
            """
            # Either add other scriptconfig clis as class variables here
            # from module.cli.script import ScriptCLI as script

        # Or register them here.
        # {classname}.register(ScriptCLI)

        __cli__ = {classname}
        main = __cli__.main


        if __name__ == '__main__':
            main()

        ''')
    return text

__cli__ = TemplateCLI

if __name__ == '__main__':
    """

    CommandLine:
        python ~/code/scriptconfig/scriptconfig/_cli/template.py
        python -m scriptconfig._cli.template
    """
    __cli__.main()
