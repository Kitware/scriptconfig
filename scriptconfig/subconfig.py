"""
Helpers for nested configuration nodes built from Config / DataConfig objects.

The :class:`SubConfig` wrapper marks a nested :class:`Config` (or subclass)
and optionally exposes a registry of valid choices or a permissive import
mechanism for dynamically specified class paths.

The rest of this module contains utilities that both :class:`Config` and
:class:`DataConfig` can use to realize nested configuration trees from
defaults, files, kwargs, and staged CLI parsing.

Example:
    >>> import scriptconfig as scfg
    >>> class Inner(scfg.DataConfig):
    ...     depth = 1
    >>> class Outer(scfg.DataConfig):
    ...     inner = scfg.SubConfig(Inner, choices={'inner': Inner})
    >>> cfg = Outer.cli(argv=['--inner.depth=3'])
    >>> assert cfg.inner.depth == 3
    >>> cfg2 = Outer.cli(argv=['--inner=inner', '--inner.depth=4'])
    >>> assert isinstance(cfg2.inner, Inner) and cfg2.inner.depth == 4
"""
from __future__ import annotations

import inspect
from collections.abc import Mapping
import ubelt as ub

from scriptconfig.config import Config
from scriptconfig.value import Value

__all__ = [
    'SubConfig',
    'add_forbidden_selector_args',
    'apply_dot_updates',
    'config_to_nested_dict',
    'expand_multipass_parser',
    'ensure_subconfigs_instantiated',
    'find_subconfig_paths',
    'finalize_post_init',
    'flat_config_from_tree',
    'resolve_localns',
    'scan_config_path',
    'wrap_subconfig_defaults',
]


import argparse


def get_stack_frame(stacklevel=0):
    """
    Gets the current stack frame or any of its ancestors dynamically.

    Args:
        stacklevel (int): stacklevel=0 means the frame you called this
            function in. stacklevel=1 is the parent frame.

    Returns:
        FrameType: frame_cur

    Example:
        >>> frame_cur = get_stack_frame(stacklevel=0)
        >>> print('frame_cur = %r' % (frame_cur,))
        >>> assert frame_cur.f_globals['frame_cur'] is frame_cur
    """
    frame_cur = inspect.currentframe()
    # Use stacklevel+1 to always skip the frame of this function.
    for ix in range(stacklevel + 1):
        frame_next = frame_cur.f_back
        if frame_next is None:  # nocover
            raise AssertionError(f'Frame level {ix} is root')
        frame_cur = frame_next
    return frame_cur


def resolve_localns(localns, stacklevel):
    """
    Resolve the namespace for selector evaluation, if needed.

    Args:
        localns (dict | None): namespace to use when resolving class names.
        stacklevel (int | None): stack offset for caller introspection.

    Returns:
        dict | None: resolved namespace.

    Example:
        >>> ns = resolve_localns({'demo_value': 5}, stacklevel=None)
        >>> assert ns['demo_value'] == 5
    """
    if localns is None and stacklevel is not None:
        frame = get_stack_frame(stacklevel=stacklevel + 2)
        localns = dict(frame.f_globals)
        localns.update(frame.f_locals)
    return localns


class _ForbiddenSelectorAction(argparse.Action):
    """
    argparse action that errors when subconfig selectors are disallowed.
    """
    def __init__(self, option_strings, dest, **kwargs):
        self._message = kwargs.pop('_message', None)
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        message = self._message or (
            'SubConfig selection overrides require allow_subconfig_overrides=True'
        )
        parser.error(message)


def add_forbidden_selector_args(parser, cfg):
    """
    Add selector options that always error when used.

    Example:
        >>> import argparse
        >>> import scriptconfig as scfg
        >>> class Inner(scfg.Config):
        ...     __default__ = {'x': 1}
        >>> class Outer(scfg.Config):
        ...     __default__ = {'inner': scfg.SubConfig(Inner)}
        >>> parser = argparse.ArgumentParser()
        >>> add_forbidden_selector_args(parser, Outer())
        >>> assert '--inner' in parser._option_string_actions
    """
    import argparse
    message = (
        'SubConfig selection overrides require allow_subconfig_overrides=True'
    )
    for path in find_subconfig_paths(cfg):
        for opt in (f'--{path}', f'--{path}.__class__'):
            parser.add_argument(
                opt,
                action=_ForbiddenSelectorAction,
                help=argparse.SUPPRESS,
                _message=message,
            )


class SubConfig(Value):
    """
    Wrapper used to declare nested :class:`Config` / :class:`DataConfig` nodes.

    Args:
        default (Type[Config] | Config): a Config subclass or instance.
        choices (dict | None): optional registry mapping selector keys to
            Config subclasses.
        allow_import (bool): if True, allow class-path selectors
            (``module.qualname.Class``) to be dynamically imported.

    Example:
        >>> import scriptconfig as scfg
        >>> class Inner(scfg.Config):
        ...     __default__ = {'x': 1}
        >>> meta = SubConfig(Inner)
        >>> inst = meta.instantiate()
        >>> assert isinstance(inst, Inner)
    """

    def __init__(self, default, *, choices=None, allow_import=None, help=None):
        if inspect.isclass(default):
            if not issubclass(default, Config):
                raise TypeError('SubConfig default must be a Config subclass or instance')
            default_inst = default
        elif isinstance(default, Config):
            default_inst = default
        else:
            raise TypeError('SubConfig default must be a Config subclass or instance')

        super().__init__(value=default_inst, help=help)
        self.allow_import = allow_import
        self.choices = dict(choices) if choices is not None else None
        if self.choices is not None:
            for key, cls in self.choices.items():
                if not inspect.isclass(cls) or not issubclass(cls, Config):
                    raise TypeError(f'SubConfig choices must map to Config subclasses. {key!r} -> {cls!r}')

    def __nice__(self):
        default_cls = self.value if inspect.isclass(self.value) else self.value.__class__
        return f'{default_cls.__name__}'

    def instantiate(self, *, _dont_call_post_init=False):
        """
        Return a fresh instance of the wrapped config.
        """
        import copy
        if inspect.isclass(self.value):
            instance = self.value(_dont_call_post_init=_dont_call_post_init)
        else:
            instance = copy.deepcopy(self.value)
            if _dont_call_post_init and hasattr(instance, '_enable_setattr'):
                instance._enable_setattr = True
        return instance


def wrap_subconfig_defaults(cfg, _dont_call_post_init=False):
    """
    Normalize any SubConfig / Config defaults into tracked metadata.

    Example:
        >>> import scriptconfig as scfg
        >>> class Inner(scfg.Config):
        ...     __default__ = {'x': 1}
        >>> class Outer(scfg.Config):
        ...     __default__ = {'inner': Inner()}
        >>> cfg = Outer(_dont_call_post_init=True)
        >>> wrap_subconfig_defaults(cfg, _dont_call_post_init=True)
        >>> assert cfg._has_subconfigs
        >>> class OuterValue(scfg.Config):
        ...     __default__ = {'inner': scfg.Value(Inner())}
        >>> cfg = OuterValue(_dont_call_post_init=True)
        >>> wrap_subconfig_defaults(cfg, _dont_call_post_init=True)
        >>> assert isinstance(cfg._subconfig_meta['inner'], scfg.SubConfig)
    """
    cfg._subconfig_meta = {}
    cfg._has_subconfigs = False
    for k, v in list(cfg._default.items()):
        meta = None
        if isinstance(v, SubConfig):
            meta = v
        elif isinstance(v, Value) and not isinstance(v, SubConfig):
            inner = v.value
            if isinstance(inner, SubConfig):
                if v.help and not inner.help:
                    inner.parsekw['help'] = v.help
                meta = inner
            elif isinstance(inner, Config):
                meta = SubConfig(inner, help=v.help)
                cfg._default[k] = meta
            elif inspect.isclass(inner) and issubclass(inner, Config):
                meta = SubConfig(inner, help=v.help)
                cfg._default[k] = meta
        elif isinstance(v, Config):
            meta = SubConfig(v)
            cfg._default[k] = meta
        elif inspect.isclass(v) and issubclass(v, Config):
            meta = SubConfig(v)
            cfg._default[k] = meta
        if meta is not None:
            cfg._has_subconfigs = True
            cfg._subconfig_meta[k] = meta
            cfg._data[k] = meta.instantiate(_dont_call_post_init=_dont_call_post_init)


def ensure_subconfigs_instantiated(cfg, _dont_call_post_init=False):
    """
    Ensure SubConfig values are instantiated on the config.

    Example:
        >>> import scriptconfig as scfg
        >>> class Inner(scfg.Config):
        ...     __default__ = {'x': 1}
        >>> class Outer(scfg.Config):
        ...     __default__ = {'inner': scfg.SubConfig(Inner)}
        >>> cfg = Outer(_dont_call_post_init=True)
        >>> cfg._data['inner'] = None
        >>> ensure_subconfigs_instantiated(cfg, _dont_call_post_init=True)
        >>> assert isinstance(cfg._data['inner'], Inner)
    """
    if not getattr(cfg, '_has_subconfigs', False):
        return
    for key, meta in getattr(cfg, '_subconfig_meta', {}).items():
        if not isinstance(cfg._data.get(key), Config):
            cfg._data[key] = meta.instantiate(_dont_call_post_init=_dont_call_post_init)


def coerce_argv(cmdline):
    """
    Normalize cmdline inputs into an argv list and help flag.

    Example:
        >>> argv, want_help = coerce_argv('--foo=bar --help')
        >>> assert argv == ['--foo=bar', '--help']
        >>> assert want_help
    """
    import shlex
    import sys
    if not cmdline:
        return [], False
    if cmdline is True:
        argv = sys.argv[1:]
    elif isinstance(cmdline, str):
        argv = shlex.split(cmdline)
    elif ub.iterable(cmdline):
        argv = list(cmdline)
    else:
        raise TypeError(f'Unsupported argv={cmdline!r}')
    want_help = any(a in {'-h', '--help'} for a in argv)
    return argv, want_help


def scan_config_path(argv):
    """
    Extract a --config value from argv if present.

    Example:
        >>> scan_config_path(['--config', 'demo.yaml'])
        'demo.yaml'
        >>> scan_config_path(['--config=demo.yaml'])
        'demo.yaml'
    """
    config_fpath = None
    for i, tok in enumerate(argv):
        if tok == '--config':
            if i + 1 >= len(argv):
                raise ValueError('--config requires a value')
            config_fpath = argv[i + 1]
        elif tok.startswith('--config='):
            config_fpath = tok.split('=', 1)[1]
    return config_fpath


def coerce_data_updates(data, mode=None):
    """
    Convert a data source (dict or filepath) into dotted updates.

    Example:
        >>> updates = coerce_data_updates({'a': 1, 'b': {'c': 2}})
        >>> assert updates['a'] == 1
        >>> assert updates['b.c'] == 2
    """
    if data is None:
        return {}

    import os
    from scriptconfig.file_like import FileLike

    if isinstance(data, (str, os.PathLike)) or hasattr(data, 'readable'):
        if isinstance(data, str) and ('\n' in data or not os.path.exists(data)):
            import json
            try:
                user_config = json.loads(data)
            except Exception:
                import yaml  # type: ignore[import-untyped]
                import io
                file = io.StringIO(data)
                user_config = yaml.load(file, Loader=yaml.SafeLoader)
        else:
            if mode is None and isinstance(data, (str, os.PathLike)):
                if str(data).lower().endswith('.json'):
                    mode = 'json'
            if mode is None:
                mode = 'yaml'
            with FileLike(data, 'r') as file:
                if mode == 'yaml':
                    import yaml
                    user_config = yaml.load(file, Loader=yaml.SafeLoader)
                elif mode == 'json':
                    import json
                    user_config = json.load(file)
                else:
                    raise KeyError(mode)
    elif isinstance(data, Mapping):
        user_config = data
    elif isinstance(data, Config):
        user_config = data.to_dict()
    else:
        raise TypeError(f'Expected path or dict, but got {type(data)}')

    flat = {}
    for k, v in _flatten_nested(user_config):
        flat[k] = v
    return flat


def _flatten_nested(mapping):
    """
    Flatten a nested mapping into dotted key/value pairs.

    Example:
        >>> list(_flatten_nested({'a': {'b': 1}, 'c': 2}))
        [('a.b', 1), ('c', 2)]
    """
    if not isinstance(mapping, Mapping):
        raise TypeError('Expected mapping')
    stack = [(iter(mapping.items()), ())]
    while stack:
        iterator, prefix = stack[-1]
        try:
            k, v = next(iterator)
        except StopIteration:
            stack.pop()
            continue
        next_prefix = prefix + (k,)
        if isinstance(v, Mapping):
            stack.append((iter(v.items()), next_prefix))
        else:
            yield '.'.join(next_prefix), v


def _split_option_token(argv, idx):
    """
    Split an argv token into (key, value, consumed).

    Example:
        >>> _split_option_token(['--a=1'], 0)
        ('a', '1', 1)
    """
    tok = argv[idx]
    if not tok.startswith('--'):
        return None, None, 1
    key = tok[2:]
    if '=' in key:
        key, val = key.split('=', 1)
        return key, val, 1
    if idx + 1 < len(argv):
        nxt = argv[idx + 1]
        if not nxt.startswith('-') or nxt == '-':
            return key, nxt, 2
    return key, None, 1


def _path_is_subconfig(cfg, parts):
    """
    Determine if a dotted path refers to a SubConfig node.

    Example:
        >>> import scriptconfig as scfg
        >>> class Inner(scfg.Config):
        ...     __default__ = {'x': 1}
        >>> class Outer(scfg.Config):
        ...     __default__ = {'inner': scfg.SubConfig(Inner)}
        >>> cfg = Outer(_dont_call_post_init=True)
        >>> wrap_subconfig_defaults(cfg, _dont_call_post_init=True)
        >>> _path_is_subconfig(cfg, ['inner'])
        True
    """
    node = cfg
    for idx, part in enumerate(parts):
        if part == '__class__':
            return False
        if not isinstance(node, Config):
            return False
        if part in getattr(node, '_subconfig_meta', {}):
            if idx == len(parts) - 1:
                return True
            child = node._data.get(part)
            if isinstance(child, Config):
                node = child
            else:
                return False
        elif part in node._data and isinstance(node._data[part], Config):
            node = node._data[part]
        else:
            return False
    return False


def extract_selector_overrides(cfg, argv, allow_import=True, localns=None, stacklevel=None):
    """
    Extract and apply selector-like arguments from argv in a staged manner.

    Example:
        >>> import scriptconfig as scfg
        >>> class Adam(scfg.Config):
        ...     __default__ = {'lr': 1e-3}
        >>> class Sgd(scfg.Config):
        ...     __default__ = {'momentum': 0.9}
        >>> class Train(scfg.Config):
        ...     __default__ = {'optim': scfg.SubConfig(Adam, choices={'adam': Adam, 'sgd': Sgd})}
        >>> cfg = Train(_dont_call_post_init=True)
        >>> wrap_subconfig_defaults(cfg, _dont_call_post_init=True)
        >>> selectors, _ = extract_selector_overrides(cfg, ['--optim=sgd'])
        >>> assert selectors['optim'] == 'sgd'
    """
    if stacklevel is not None:
        localns = resolve_localns(localns, stacklevel)
    working = list(argv)
    collected = {}
    changed = True
    max_iter = 20
    guard = 0
    while changed:
        guard += 1
        if guard > max_iter:
            raise RuntimeError('Selector resolution did not converge')
        changed = False
        new_selectors = {}
        kept = []
        i = 0
        while i < len(working):
            tok = working[i]
            key, val, consumed = _split_option_token(working, i)
            if key is None:
                kept.append(tok)
                i += 1
                continue
            if key.endswith('.__class__'):
                sel_key = key[:-len('.__class__')]
                if val is None:
                    raise ValueError(f'Missing value for selector {key}')
                new_selectors[sel_key] = val
                changed = True
                i += consumed
                continue
            if _path_is_subconfig(cfg, key.split('.')):
                if val is None:
                    raise ValueError(f'Missing value for selector {key}')
                new_selectors[key] = val
                changed = True
                i += consumed
                continue
            kept.append(tok)
            i += 1
        if new_selectors:
            collected.update(new_selectors)
            working = kept
            apply_dot_updates(
                cfg,
                new_selectors,
                allow_import=allow_import,
                localns=localns,
                stacklevel=None,
            )
        else:
            working = kept
    return collected, working


def _ensure_parent_node(cfg, parts):
    """
    Traverse a dotted path and return the parent node.

    Example:
        >>> import scriptconfig as scfg
        >>> class Inner(scfg.Config):
        ...     __default__ = {'x': 1}
        >>> class Outer(scfg.Config):
        ...     __default__ = {'inner': scfg.SubConfig(Inner)}
        >>> cfg = Outer(_dont_call_post_init=True)
        >>> wrap_subconfig_defaults(cfg, _dont_call_post_init=True)
        >>> parent = _ensure_parent_node(cfg, ['inner'])
        >>> assert isinstance(parent, Inner)
    """
    node = cfg
    for part in parts:
        if not isinstance(node, Config):
            raise KeyError('.'.join(parts))
        if part in getattr(node, '_subconfig_meta', {}):
            child = node._data.get(part)
            if not isinstance(child, Config):
                child = node._subconfig_meta[part].instantiate(_dont_call_post_init=True)
                node._data[part] = child
            node = child
        elif part in node._data and isinstance(node._data[part], Config):
            node = node._data[part]
        else:
            raise KeyError('.'.join(parts))
    return node


def _resolve_class_spec(meta: SubConfig, spec, allow_import, localns=None):
    """
    Resolve a selector spec into a Config subclass.

    Precedence:
        1. SubConfig registry choices (if provided)
        2. Local namespace class names (bare identifiers)
        3. Importable module paths (if allow_import), using
           ``module.qualname.Class``.

    Example:
        >>> import scriptconfig as scfg
        >>> class Inner(scfg.Config):
        ...     __default__ = {'x': 1}
        >>> meta = SubConfig(Inner, choices={'inner': Inner})
        >>> assert _resolve_class_spec(meta, 'inner', True) is Inner
    """
    if meta.choices and spec in meta.choices:
        return meta.choices[spec]
    if inspect.isclass(spec) and issubclass(spec, Config):
        return spec
    if isinstance(spec, str):
        if localns is not None and spec.isidentifier():
            candidate = localns.get(spec)
            if inspect.isclass(candidate) and issubclass(candidate, Config):
                return candidate
        if not (meta.allow_import or allow_import):
            raise ValueError(f'Importing {spec!r} not allowed for this SubConfig')
        if ':' in spec:
            modname, clsname = spec.split(':', 1)
        else:
            modname, clsname = spec.rsplit('.', 1)
            if not modname or not clsname:
                raise ValueError(f'Cannot interpret class spec {spec!r}')
        import importlib
        mod = importlib.import_module(modname)
        if not hasattr(mod, clsname):
            raise ValueError(f'Module {modname!r} has no attribute {clsname!r}')
        cls = getattr(mod, clsname)
        if not inspect.isclass(cls) or not issubclass(cls, Config):
            raise TypeError(f'Specified class {cls!r} is not a Config/DataConfig')
        return cls
    raise ValueError(f'Unknown selector spec {spec!r}')


def _apply_selectors_fixpoint(cfg, selectors, allow_import=True, localns=None):
    """
    Apply selector overrides until a fixed point is reached.

    Example:
        >>> import scriptconfig as scfg
        >>> class Adam(scfg.Config):
        ...     __default__ = {'lr': 1e-3}
        >>> class Sgd(scfg.Config):
        ...     __default__ = {'momentum': 0.9}
        >>> class Train(scfg.Config):
        ...     __default__ = {'optim': scfg.SubConfig(Adam, choices={'adam': Adam, 'sgd': Sgd})}
        >>> cfg = Train(_dont_call_post_init=True)
        >>> wrap_subconfig_defaults(cfg, _dont_call_post_init=True)
        >>> _apply_selectors_fixpoint(cfg, {'optim': 'sgd'})
        >>> assert isinstance(cfg['optim'], Sgd)
    """
    remaining = dict(selectors)
    applied_any = True
    max_iter = 32
    iter_idx = 0
    while applied_any:
        iter_idx += 1
        if iter_idx > max_iter:
            raise RuntimeError('Selector resolution failed to converge')
        applied_any = False
        for path, spec in list(remaining.items()):
            parts = tuple(p for p in path.split('.') if p)
            if not parts:
                raise ValueError('Empty selector path')
            parent_parts, leaf = parts[:-1], parts[-1]
            try:
                parent = _ensure_parent_node(cfg, parent_parts)
            except KeyError:
                continue
            if not isinstance(parent, Config):
                continue
            meta = getattr(parent, '_subconfig_meta', {}).get(leaf, None)
            if meta is None:
                continue
            cls = _resolve_class_spec(meta, spec, allow_import, localns=localns)
            parent._data[leaf] = cls(_dont_call_post_init=True)
            applied_any = True
            remaining.pop(path, None)
    if remaining:
        raise KeyError(f'Could not resolve selectors for: {sorted(remaining)}')


def apply_dot_updates(cfg, updates, *, allow_import=True, localns=None, stacklevel=None):
    """
    Apply dotted-path updates and selectors to a nested Config / DataConfig.

    Example:
        >>> import scriptconfig as scfg
        >>> class Inner(scfg.Config):
        ...     __default__ = {'x': 1}
        >>> class Outer(scfg.Config):
        ...     __default__ = {'inner': scfg.SubConfig(Inner)}
        >>> cfg = Outer(_dont_call_post_init=True)
        >>> wrap_subconfig_defaults(cfg, _dont_call_post_init=True)
        >>> apply_dot_updates(cfg, {'inner.x': 5})
        >>> assert cfg['inner']['x'] == 5
    """
    if not updates:
        return cfg

    if stacklevel is not None:
        localns = resolve_localns(localns, stacklevel)

    flat_updates = {}
    if isinstance(updates, Mapping):
        for k, v in _flatten_nested(updates):
            flat_updates[k] = v
    else:
        raise TypeError('updates must be a mapping')

    selectors = {}
    leaf_updates = {}
    for key, value in flat_updates.items():
        if key.endswith('.__class__'):
            selectors[key[:-len('.__class__')]] = value
        else:
            leaf_updates[key] = value

    _apply_selectors_fixpoint(cfg, selectors, allow_import=allow_import, localns=localns)

    sugar = {}
    for key, value in list(leaf_updates.items()):
        parts = key.split('.')
        try:
            parent = _ensure_parent_node(cfg, parts[:-1])
        except KeyError:
            continue
        if isinstance(parent, Config) and parts[-1] in getattr(parent, '_subconfig_meta', {}):
            if key not in selectors:
                sugar[key] = value
                leaf_updates.pop(key, None)
    if sugar:
        _apply_selectors_fixpoint(cfg, sugar, allow_import=allow_import, localns=localns)

    for key, value in leaf_updates.items():
        parts = key.split('.')
        parent = _ensure_parent_node(cfg, parts[:-1])
        leaf = parts[-1]
        if leaf == '__class__':
            raise KeyError('The name "__class__" is reserved for selector metadata')
        if leaf not in parent._data:
            leaf = parent._normalize_alias_key(leaf)
        if leaf not in parent._data:
            raise KeyError(f'Unknown configuration key: {key}')
        parent[leaf] = value
    return cfg


def has_selector_overrides(cfg, updates):
    """
    Determine if updates contain selector overrides for SubConfig nodes.

    Example:
        >>> import scriptconfig as scfg
        >>> class Inner(scfg.Config):
        ...     __default__ = {'x': 1}
        >>> class Outer(scfg.Config):
        ...     __default__ = {'inner': scfg.SubConfig(Inner)}
        >>> cfg = Outer(_dont_call_post_init=True)
        >>> wrap_subconfig_defaults(cfg, _dont_call_post_init=True)
        >>> assert has_selector_overrides(cfg, {'inner.__class__': 'inner'})
    """
    if not updates:
        return False
    flat_updates = {}
    if isinstance(updates, Mapping):
        for k, v in _flatten_nested(updates):
            flat_updates[k] = v
    else:
        return False
    subconfig_paths = set(find_subconfig_paths(cfg))
    for key in flat_updates:
        if key.endswith('.__class__'):
            return True
        if key in subconfig_paths:
            return True
    return False


def flatten_defaults(cfg, prefix=(), include_class_options=False):
    """
    Flatten config defaults into dotted keys.

    Example:
        >>> import scriptconfig as scfg
        >>> class Inner(scfg.Config):
        ...     __default__ = {'x': 1}
        >>> class Outer(scfg.Config):
        ...     __default__ = {'inner': scfg.SubConfig(Inner)}
        >>> cfg = Outer(_dont_call_post_init=True)
        >>> wrap_subconfig_defaults(cfg, _dont_call_post_init=True)
        >>> flat = flatten_defaults(cfg)
        >>> assert 'inner.x' in flat
    """
    flat = {}
    for key, value in cfg._data.items():
        if key in getattr(cfg, '_subconfig_meta', {}):
            if include_class_options:
                selector_key = '.'.join(prefix + (key,))
                class_key = '.'.join(prefix + (key, '__class__'))
                flat[selector_key] = Value(None, help=f'{key} implementation selector')
                flat[class_key] = Value(None, help=f'{key} implementation selector')
            if isinstance(value, Config):
                flat.update(flatten_defaults(value, prefix + (key,), include_class_options))
        elif isinstance(value, Config):
            flat.update(flatten_defaults(value, prefix + (key,), include_class_options))
        else:
            meta = cfg._default.get(key)
            leaf_key = '.'.join(prefix + (key,))
            if isinstance(meta, Value):
                flat[leaf_key] = meta
            else:
                flat[leaf_key] = value
    return flat


def flat_config_from_tree(cfg, include_class_options=False):
    """
    Build a temporary Config instance to parse realized leaf arguments.

    Example:
        >>> import scriptconfig as scfg
        >>> class Inner(scfg.Config):
        ...     __default__ = {'x': 1}
        >>> class Outer(scfg.Config):
        ...     __default__ = {'inner': scfg.SubConfig(Inner)}
        >>> cfg = Outer(_dont_call_post_init=True)
        >>> wrap_subconfig_defaults(cfg, _dont_call_post_init=True)
        >>> flat = flat_config_from_tree(cfg)
        >>> assert 'inner.x' in flat.__default__
    """
    defaults = flatten_defaults(cfg, include_class_options=include_class_options)
    name = f'_Flat_{cfg.__class__.__name__}'
    FlatCls = type(name, (Config,), {'__default__': defaults})
    return FlatCls(_dont_call_post_init=True)


def expand_multipass_parser(cfg, parser, argv=None, special_options=True,
                            allow_import=True, allow_subconfig_overrides=True,
                            pending_updates=None, localns=None, stacklevel=None):
    """
    Expand an argparse parser for configs with nested SubConfig nodes.

    This staged parse realizes selector overrides first, then rebuilds a
    parser for the realized tree so the full argv can be parsed in a
    single pass with the standard logic in _read_argv.

    Example:
        >>> import argparse
        >>> import scriptconfig as scfg
        >>> class Inner(scfg.Config):
        ...     __default__ = {'x': 1}
        >>> class Outer(scfg.Config):
        ...     __default__ = {'inner': scfg.SubConfig(Inner)}
        >>> cfg = Outer(_dont_call_post_init=True)
        >>> wrap_subconfig_defaults(cfg, _dont_call_post_init=True)
        >>> parser = argparse.ArgumentParser()
        >>> parser, argv = expand_multipass_parser(cfg, parser, argv=['--inner.x=2'])
        >>> assert '--inner.x' in parser._option_string_actions
    """
    argv_list, _want_help = coerce_argv(True if argv is None else argv)

    if special_options:
        config_fpath = scan_config_path(argv_list)
        if config_fpath is not None:
            cfg_updates = coerce_data_updates(config_fpath)
            if not allow_subconfig_overrides and has_selector_overrides(cfg, cfg_updates):
                raise ValueError(
                    'SubConfig selection overrides require allow_subconfig_overrides=True'
                )
            apply_dot_updates(
                cfg,
                cfg_updates,
                allow_import=allow_import,
                localns=localns,
                stacklevel=stacklevel,
            )

    if pending_updates is not None:
        cfg_updates = pending_updates
        if not allow_subconfig_overrides and has_selector_overrides(cfg, cfg_updates):
            raise ValueError(
                'SubConfig selection overrides require allow_subconfig_overrides=True'
            )
        apply_dot_updates(
            cfg,
            cfg_updates,
            allow_import=allow_import,
            localns=localns,
            stacklevel=stacklevel,
        )

    if allow_subconfig_overrides:
        selector_updates, _stage2_argv = extract_selector_overrides(
            cfg,
            argv_list,
            allow_import=allow_import,
            localns=localns,
            stacklevel=stacklevel,
        )
        if selector_updates:
            apply_dot_updates(
                cfg,
                selector_updates,
                allow_import=allow_import,
                localns=localns,
                stacklevel=stacklevel,
            )
        flat_helper = flat_config_from_tree(cfg, include_class_options=True)
        parser = flat_helper.argparse(special_options=special_options)
    else:
        # Static parse path: disallow selector overrides and fail early.
        flat_helper = flat_config_from_tree(cfg, include_class_options=False)
        parser = flat_helper.argparse(special_options=special_options)
        add_forbidden_selector_args(parser, cfg)
    return parser, argv_list


def finalize_post_init(cfg):
    """
    Run __post_init__ once on a nested config tree.

    Example:
        >>> import scriptconfig as scfg
        >>> class Inner(scfg.Config):
        ...     __default__ = {'x': 1}
        >>> class Outer(scfg.Config):
        ...     __default__ = {'inner': scfg.SubConfig(Inner)}
        >>> cfg = Outer(_dont_call_post_init=True)
        >>> wrap_subconfig_defaults(cfg, _dont_call_post_init=True)
        >>> finalize_post_init(cfg)
    """
    if isinstance(cfg, Config):
        if not getattr(cfg, '_scfg_post_init_done', False):
            cfg.__post_init__()
            cfg._scfg_post_init_done = True
    if isinstance(cfg, Config):
        for value in cfg._data.values():
            if isinstance(value, Config):
                finalize_post_init(value)


def _class_identifier(cls):
    """
    Return a module-qualified class identifier.

    Example:
        >>> import scriptconfig as scfg
        >>> assert _class_identifier(scfg.Config).endswith('.Config')
    """
    return f'{cls.__module__}.{cls.__name__}'


def find_subconfig_paths(cfg):
    """
    Yield dotted paths to SubConfig nodes in the realized tree.

    Example:
        >>> import scriptconfig as scfg
        >>> class Inner(scfg.Config):
        ...     __default__ = {'x': 1}
        >>> class Outer(scfg.Config):
        ...     __default__ = {'inner': scfg.SubConfig(Inner)}
        >>> cfg = Outer(_dont_call_post_init=True)
        >>> wrap_subconfig_defaults(cfg, _dont_call_post_init=True)
        >>> assert 'inner' in find_subconfig_paths(cfg)
    """
    paths = []
    stack = [([], cfg)]
    while stack:
        prefix, node = stack.pop()
        for key, value in node._data.items():
            next_prefix = prefix + [key]
            if key in getattr(node, '_subconfig_meta', {}):
                paths.append('.'.join(next_prefix))
            if isinstance(value, Config):
                stack.append((next_prefix, value))
    return paths


def config_to_nested_dict(cfg, include_class=True):
    """
    Convert a realized config tree to a nested dictionary.

    Example:
        >>> import scriptconfig as scfg
        >>> class Inner(scfg.Config):
        ...     __default__ = {'x': 1}
        >>> class Outer(scfg.Config):
        ...     __default__ = {'inner': scfg.SubConfig(Inner)}
        >>> cfg = Outer(_dont_call_post_init=True)
        >>> wrap_subconfig_defaults(cfg, _dont_call_post_init=True)
        >>> data = config_to_nested_dict(cfg)
        >>> assert 'inner' in data
    """
    def unwrap(val):
        if isinstance(val, Value):
            return val.value
        return val

    result = {}
    meta_map = getattr(cfg, '_subconfig_meta', {})
    for key, value in cfg._data.items():
        meta = meta_map.get(key)
        if isinstance(value, Config):
            child = config_to_nested_dict(value, include_class=include_class)
            selector = None
            if meta is not None and meta.choices:
                for name, cls in meta.choices.items():
                    if isinstance(value, cls):
                        selector = name
                        break
            if selector is None:
                selector = _class_identifier(value.__class__)
            # Always record the selected implementation for SubConfig nodes.
            if meta is not None or include_class:
                child['__class__'] = selector
            result[key] = child
        else:
            result[key] = unwrap(value)
    return result
