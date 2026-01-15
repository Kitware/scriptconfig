"""
Note: this module may be deprecated / repurposed for the actual command line
interface scriptconfig will use.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional


def quick_cli(default: Mapping[str, Any], name: Optional[str] = None) -> Any:
    """
    Quickly create a CLI

    New in 0.5.2

    Example:
        >>> # SCRIPT
        >>> import scriptconfig as scfg
        >>> default = {
        >>>     'fpath': scfg.Path(None),
        >>>     'modnames': scfg.Value([]),
        >>> }
        >>> config = scfg.quick_cli(default)
        >>> print('config = {!r}'.format(config))
    """
    if name is None:
        import uuid
        hashid = str(uuid.uuid4()).replace('-', '_')
        name = 'ExpressCLI_{}'.format(hashid)

    from textwrap import dedent
    vals: dict[str, Any] = {}
    code = dedent(
        '''
        import scriptconfig as scfg
        class {name}(scfg.Config):
            pass
        '''.strip('\n').format(name=name))
    exec(code, vals)
    cls = vals[name]
    cls.default = default
    config = cls(cmdline=True)
    return config


__all__ = ['quick_cli']
