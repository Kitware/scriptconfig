import glob
import ubelt as ub
import copy
from . import smartcast
import re


long_prefix_pat = re.compile('--[^-].*')
short_prefix_pat = re.compile('-[^-].*')


def normalize_option_str(s):
    return s.lstrip('-').replace('-', '_')


__note__ = """
TODO:
    After we remove 3.6 support, deprecate position and add the ispositional
    argument. Or maybe just "positional"?

    ispositional (bool):
        if True the argument will be treated as a positional argument with
        its order determined by its location in the config.

"""


class Value(ub.NiceRepr):
    """
    You may set any item in the config's default to an instance of this class.
    Using this class allows you to declare the desired default value as well as
    the type that the value should be (Used when parsing sys.argv).

    Attributes:
        value (Any):
            A float, int, etc...

        type (type | None):
            the "type" of the value. This is usually used if the value
            specified is not the type that `self.value` would usually be set
            to.

        parsekw (dict):
            kwargs for to argparse add_argument

        position (None | int):
            if an integer, then we allow this value to be a positional argument
            in the argparse CLI. Note, that values with the same position index
            will cause conflicts. Also note: positions indexes should start
            from 1.

        isflag (bool): if True, args will be parsed as booleans.
            Default to False.

        alias (List[str] | None):
            other long names (that will be prefixed with '--') that will be
            accepted by the argparse CLI.

        short_alias (List[str] | None):
            other short names (that will be prefixed with '-') that will be
            accepted by the argparse CLI.

        group (str | None):
            Impacts display of underlying argparse object by grouping values
            with the same type together. There is no other impact.

        mutex_group (str | None):
            Indicates that only one of the values in a group should be given on
            the command line. This has no impact on python usage.

    Example:
        >>> self = Value(None, type=float)
        >>> print('self.value = {!r}'.format(self.value))
        self.value = None
        >>> self.update('3.3')
        >>> print('self.value = {!r}'.format(self.value))
        self.value = 3.3
    """

    # hack to work around isinstance with IPython %autoreload magic
    __scfg_class__ = 'Value'

    def __init__(self, value=None, type=None, help=None, choices=None,
                 position=None, isflag=False, nargs=None, alias=None,
                 required=False, short_alias=None, group=None,
                 mutex_group=None):
        self.value = None
        self.type = type
        self.alias = alias
        self.position = position
        self.isflag = isflag
        self.parsekw = {
            'help': help,
            'type': type,
            'choices': choices,
            'nargs': nargs,
        }
        self.group = group
        self.mutex_group = mutex_group
        self.required = required
        self.short_alias = short_alias
        self.update(value)

    def __nice__(self):
        return '{!r}: {!r}'.format(self.type, self.value)

    def update(self, value):
        self.value = self.cast(value)
        return self

    def cast(self, value):
        if isinstance(value, str):
            value = smartcast.smartcast(value, self.type)
        return value

    def copy(self):
        return copy.copy(self)

    def _to_value_kw(self):
        value = self
        orig_help = self.parsekw['help']
        orig_type = self.parsekw['type']
        value_kw = {k: str(v) for k, v in self.__dict__.items() if v}
        value_kw.pop('parsekw')
        value_kw.update(value.parsekw)
        value_kw['help'] = repr(orig_help)
        value_kw['nargs'] = repr(value.parsekw['nargs'])
        if orig_type is not None:
            if isinstance(orig_type, str):
                value_kw['type'] = repr(orig_type)
            else:
                value_kw['type'] = orig_type.__name__

        value_kw = ub.udict(value_kw)
        order = value_kw & ['value', 'nargs', 'type', 'isflag', 'position', 'required',
                            'choices', 'alias', 'short_alias', 'group', 'mutex_group',
                            'help']
        value_kw = order | (value_kw - order)
        if value_kw.get('nargs', None) in {None, 'None'}:
            value_kw.pop('nargs', None)

        HACKS = 1
        if HACKS:
            if value_kw['type'] == 'smartcast':
                value_kw.pop('type')
            if orig_help and len(orig_help) > 40:
                import textwrap
                wrapped = ub.indent('\n'.join(textwrap.wrap(orig_help, width=60)), ' ' * 4)
                block = ub.codeblock(
                    """
                    ub.paragraph(
                        '''
                    {}
                        ''')
                    """
                ).format(wrapped)
                value_kw['help'] = ub.indent(block, ' ' * 8).lstrip()
                # "ub.paragraph(\n'''\n{}\n''')".format(ub.indent(value.help, ' ' * 16))
        value_kw['default'] = value.value
        value_kw.pop('value', None)
        return value_kw

    @classmethod
    def _from_action(cls, action, actionid_to_groupkey, actionid_to_mgroupkey,
                     pos_counter):
        key = action.dest

        long_option_strings = [
            s for s in action.option_strings
            if long_prefix_pat.match(s)
        ]
        short_option_strings = [
            s for s in action.option_strings
            if short_prefix_pat.match(s)
        ]

        alias = ub.oset(normalize_option_str(s)
                        for s in long_option_strings)
        alias = list(alias - {key})

        short_alias = ub.oset(normalize_option_str(s)
                              for s in short_option_strings)
        short_alias = list(short_alias - {key})

        real_value_kw = {
            'value': action.default,
            'type': action.type,
            'alias': alias,
            'short_alias': short_alias,
            'required': action.required,
            'choices': action.choices,
            'help': action.help,
        }
        if action.nargs == 0 and action.const is True:
            # This is a boolean flag
            real_value_kw['isflag'] = True
        else:
            real_value_kw.pop('isflag', None)
            if action.nargs is not None:
                real_value_kw['nargs'] = action.nargs
        action_id = id(action)
        if action_id in actionid_to_groupkey:
            real_value_kw['group'] = repr(actionid_to_groupkey[action_id])
        if action_id in actionid_to_mgroupkey:
            real_value_kw['mutex_group'] = repr(actionid_to_mgroupkey[action_id])
        if len(action.option_strings) == 0:
            real_value_kw['position'] = next(pos_counter)
        value = Value(**real_value_kw)
        return value


class Path(Value):
    """
    Note this is mean to be used only with scriptconfig.Config.
    It does NOT represent a pathlib object.
    """
    def __init__(self, value=None, help=None, alias=None):
        super(Path, self).__init__(value, str, help=help, alias=alias)

    def cast(self, value):
        if isinstance(value, str):
            value = ub.expandpath(value)
        return value


class PathList(Value):
    """
    Can be specified as a list or as a globstr

    FIXME:
        will fail if there are any commas in the path name

    Example:
        >>> from os.path import join
        >>> path = ub.modname_to_modpath('scriptconfig', hide_init=True)
        >>> globstr = join(path, '*.py')
        >>> # Passing in a globstr is accepted
        >>> assert len(PathList(globstr).value) > 0
        >>> # Smartcast should separate these
        >>> assert len(PathList('/a,/b').value) == 2
        >>> # Passing in a list is accepted
        >>> assert len(PathList(['/a', '/b']).value) == 2
    """

    def cast(self, value=None):
        if isinstance(value, str):
            paths1 = sorted(glob.glob(ub.expandpath(value)))
            paths2 = smartcast.smartcast(value)
            if paths1:
                value = paths1
            else:
                value = paths2
        return value


def _value_add_argument_to_parser(value, _value, self, parser, key, fuzzy_hyphens=0):
    """
    POC for a new simplified way for a value to add itself as an argument to a
    parser.
    """
    # import argparse
    from scriptconfig import argparse_ext

    # value: Any | Value
    name = key
    argkw = {}
    argkw['help'] = ''
    positional = None
    isflag = False
    required = False

    group_lut = getattr(parser, '_sc_group_lut', {})
    mutex_group_lut = getattr(parser, '_sc_mutex_group_lut', {})
    parser._sc_mutex_group_lut = mutex_group_lut
    parser._sc_group_lut = group_lut

    parent = parser
    if _value is not None:
        # Use the metadata in the Value class to enhance argparse
        # _value = _metadata[name]
        argkw.update(_value.parsekw)
        required = _value.required
        value = _value.value
        isflag = _value.isflag
        positional = _value.position

        # If the args are flagged as belonging to a group, resepct that.
        if _value.group is not None:
            if _value.group not in group_lut:
                groupkw = {}
                if isinstance(_value.group, str):
                    groupkw['title'] = _value.group
                group_lut[_value.group] = parent.add_argument_group(**groupkw)
            parent = group_lut[_value.group]

        if _value.mutex_group is not None:
            if _value.mutex_group not in mutex_group_lut:
                mutex_group_lut[_value.mutex_group] = parent.add_mutually_exclusive_group()
            parent = mutex_group_lut[_value.mutex_group]

    if not argkw['help']:
        argkw['help'] = '<undocumented>'

    argkw['default'] = value
    argkw['action'] = _maker_smart_parse_action(self)

    if positional:
        parent.add_argument(name, **argkw)

    argkw['dest'] = name

    option_strings = _resolve_alias(name, _value, fuzzy_hyphens)

    if isflag:
        # Can we support both flag and setitem methods of cli
        # parsing?
        argkw.pop('type', None)
        argkw.pop('choices', None)
        argkw.pop('action', None)
        argkw.pop('nargs', None)
        argkw['dest'] = name

        argkw['action'] = argparse_ext.BooleanFlagOrKeyValAction
        parent.add_argument(*option_strings, required=required, **argkw)
    else:
        parent.add_argument(*option_strings, required=required, **argkw)


def _resolve_alias(name, _value, fuzzy_hyphens):
    if _value is None:
        aliases = None
        short_aliases = None
    else:
        aliases = _value.alias
        short_aliases = _value.short_alias
    if isinstance(aliases, str):
        aliases = [aliases]
    if isinstance(short_aliases, str):
        short_aliases = [short_aliases]
    long_names = [name] + list((aliases or []))
    short_names = list(short_aliases or [])
    if fuzzy_hyphens:
        # Do we want to allow for people to use hyphens on the CLI?
        # Maybe, we can make it optional.
        unique_long_names = set(long_names)
        modified_long_names = {n.replace('_', '-') for n in unique_long_names}
        extra_long_names = modified_long_names - unique_long_names
        long_names += sorted(extra_long_names)
    short_option_strings = ['-' + n for n in short_names]
    long_option_strings = ['--' + n for n in long_names]
    option_strings = short_option_strings + long_option_strings
    return option_strings


def scfg_isinstance(item, cls):
    """
    use instead isinstance for scfg types when reloading

    Args:
        item (object): instance to check
        cls (type): class to check against

    Returns:
        bool
    """
    # Note: it is safe to simply use isinstance(item, cls) when
    # not reloading
    if hasattr(item, '__scfg_class__')  and hasattr(cls, '__scfg_class__'):
        return item.__scfg_class__ == cls.__scfg_class__
    else:
        return isinstance(item, cls)


def _maker_smart_parse_action(self):
    import argparse
    from itertools import chain

    scfg_object = self

    ### TODO: be slightly less smart
    class ParseAction(argparse._StoreAction):
        def __init__(self, *args, **kwargs):
            # required/= kwargs.pop('required', False)
            super().__init__(*args, **kwargs)
            # with script config nothing should be required by default
            # (unless specified) all positional arguments should have
            # keyword arg variants Setting required=False here will prevent
            # positional args from erroring if they are not specified. I
            # dont think there are other side effects, but we should make
            # sure that is actually the case.
            self.required = False  # hack

            if self.type is None:
                # If a type isn't explicitly declared, we will either use
                # the template (if it exists) or try using a smartcast.
                def _smart_type(value):
                    key = self.dest
                    template = scfg_object.default[key]
                    if not isinstance(template, Value):
                        # smartcast non-valued params from commandline
                        value = smartcast.smartcast(value)
                    else:
                        value = template.cast(value)
                    return value

                self.type = _smart_type

        def __call__(action, parser, namespace, values, option_string=None):
            # print('CALL action = {!r}'.format(action))
            # print('option_string = {!r}'.format(option_string))
            # print('values = {!r}'.format(values))

            if isinstance(values, list) and len(values):
                # We got a list of lists, which we hack into a flat list
                if isinstance(values[0], list):
                    values = list(chain(*values))

            setattr(namespace, action.dest, values)
            if not hasattr(parser, '_explicitly_given'):
                # We might be given a subparser / parent parser
                # and not the original one we created.
                parser._explicitly_given = set()
            parser._explicitly_given.add(action.dest)

    return ParseAction
