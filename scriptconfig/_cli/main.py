#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
import scriptconfig as scfg
from scriptconfig import __version__


class ScriptConfigModal(scfg.ModalCLI):
    """
    Top level modal CLI for scriptconfig helpers
    """
    __version__ = __version__
    from scriptconfig._cli.template import TemplateCLI as template


__cli__ = ScriptConfigModal
main = __cli__.main


if __name__ == '__main__':
    """
    CommandLine:
        python -m scriptconfig
    """
    main()
