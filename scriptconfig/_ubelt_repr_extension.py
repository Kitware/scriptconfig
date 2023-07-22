
def _register_ubelt_repr_extensions():
    import ubelt as ub
    try:
        _REPR_EXTENSIONS = ub.util_repr._REPR_EXTENSIONS
    except AttributeError:
        _REPR_EXTENSIONS = ub.util_format._FORMATTER_EXTENSIONS

    def _register_scriptconfig_extensions():
        import scriptconfig as scfg
        @_REPR_EXTENSIONS.register(scfg.Config)
        def format_scriptconfig(data, **kwargs):
            name = data.__class__.__name__
            body = ub.urepr(data.to_dict(), **kwargs)
            text = f'{name}(**{body})'
            return text

    _REPR_EXTENSIONS._lazy_queue.append(_register_scriptconfig_extensions)
