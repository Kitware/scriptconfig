
def quick_cli(default, name=None):
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
    vals = {}
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
