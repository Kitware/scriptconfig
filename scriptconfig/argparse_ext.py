"""
Argparse Extensions
"""
import argparse


__docstubs__ = """
import argparse
_Base = argparse._StoreAction
"""

# Inherit from StoreAction to make configargparse happy.  Hopefully python
# doesn't change the behavior of this private class.
# If we ditch support for configargparse in the future, then we can more
# reasonably just inherit from Action
_Base = argparse._StoreAction
# _Base = argparse.Action


class BooleanFlagOrKeyValAction(_Base):
    """
    An action that allows you to specify a boolean via a flag as per usual
    or a key/value pair.

    This helps allow for a flexible specification of boolean values:

        --flag        > {'flag': True}
        --flag=1      > {'flag': True}
        --flag True   > {'flag': True}
        --flag True   > {'flag': True}
        --flag False  > {'flag': False}
        --flag 0      > {'flag': False}
        --no-flag     > {'flag': False}
        --no-flag=0   > {'flag': True}
        --no-flag=1   > {'flag': False}

    Example:
        >>> from scriptconfig.argparse_ext import *  # NOQA
        >>> import argparse
        >>> parser = argparse.ArgumentParser()
        >>> parser.add_argument('--flag', action=BooleanFlagOrKeyValAction)
        >>> print(parser.format_usage())
        >>> print(parser.format_help())
        >>> import shlex
        >>> # Map the CLI arg string to what value we would expect to get
        >>> variants = {
        >>>     # Case1: you either specify the flag, or you don't
        >>>     '': None,
        >>>     '--flag': True,
        >>>     '--no-flag': False,
        >>>     # Case1: You specify the flag as a key/value pair
        >>>     '--flag=0': False,
        >>>     '--flag=1': True,
        >>>     '--flag True': True,
        >>>     '--flag False': False,
        >>>     # Case1: You specify the negated flag as a key/value pair
        >>>     # (you probably shouldn't do this)
        >>>     '--no-flag 0': True,
        >>>     '--no-flag 1': False,
        >>>     '--no-flag=True': False,
        >>>     '--no-flag=False': True,
        >>> }
        >>> for args, want in variants.items():
        >>>     args = shlex.split(args)
        >>>     ns = parser.parse_known_args(args=args)[0].__dict__
        >>>     print(f'args={args} -> {ns}')
        >>>     assert ns['flag'] == want

    Example:
        >>> # Does this play nice with other complex cases?
        >>> from scriptconfig.argparse_ext import *  # NOQA
        >>> import argparse
        >>> parser = argparse.ArgumentParser()
        >>> parser.add_argument('--flag', action=BooleanFlagOrKeyValAction)
        >>> print(parser.format_usage())
        >>> print(parser.format_help())
        >>> import shlex
        >>> # Map the CLI arg string to what value we would expect to get
        >>> variants = {
        >>>     # Case1: you either specify the flag, or you don't
        >>>     '': None,
        >>>     '--flag': True,
        >>>     '--no-flag': False,
        >>>     # Case1: You specify the flag as a key/value pair
        >>>     '--flag=0': False,
        >>>     '--flag=1': True,
        >>>     '--flag True': True,
        >>>     '--flag False': False,
        >>>     # Case1: You specify the negated flag as a key/value pair
        >>>     # (you probably shouldn't do this)
        >>>     '--no-flag 0': True,
        >>>     '--no-flag 1': False,
        >>>     '--no-flag=True': False,
        >>>     '--no-flag=False': True,
        >>> }
        >>> for args, want in variants.items():
        >>>     args = shlex.split(args)
        >>>     ns = parser.parse_known_args(args=args)[0].__dict__
        >>>     print(f'args={args} -> {ns}')
        >>>     assert ns['flag'] == want
    """
    def __init__(self, option_strings, dest, default=None, required=False,
                 help=None):

        _option_strings = []
        for option_string in option_strings:
            _option_strings.append(option_string)
            if option_string.startswith('--'):
                option_string = '--no-' + option_string[2:]
                _option_strings.append(option_string)
        if help is not None and default is not None and default is not argparse.SUPPRESS:
            help += " (default: %(default)s)"

        actionkw = dict(
            option_strings=_option_strings, dest=dest, default=default,
            type=None, choices=None, required=required, help=help,
            metavar=None)
        # Either the zero arg flag form or the 1 arg key/value form.
        actionkw['nargs'] = '?'

        # Hack because of the Store Base for configargparse support
        argparse.Action.__init__(self, **actionkw)
        # super().__init__(**actionkw)

    def format_usage(self):
        # I thought this was used in formatting the help, but it seems like
        # we dont have much control over that here.
        if self.default is False:
            # If the default is false, don't show the negative variants
            _option_strings = []
            for option_string in self.option_strings:
                if not option_string.startswith('--no'):
                    _option_strings.append(option_string)
        else:
            _option_strings = self.option_strings
        return ' | '.join(_option_strings)

    def _mark_parsed_argument(action, parser):
        if not hasattr(parser, '_explicitly_given'):
            # We might be given a subparser / parent parser
            # and not the original one we created.
            parser._explicitly_given = set()
        parser._explicitly_given.add(action.dest)

    def __call__(action, parser, namespace, values, option_string=None):
        if option_string in action.option_strings:
            # Was the positive or negated key given?
            key_default = not option_string.startswith('--no-')
        # Was there a value or was the flag specified by itself?
        if values is None:
            value = key_default
        else:
            # Allow for non-boolean values (i.e. auto) to be passed
            from scriptconfig import smartcast as smartcast_mod
            value = smartcast_mod.smartcast(values)
            # value = smartcast_mod._smartcast_bool(values)
            if not key_default:
                value = not value
        setattr(namespace, action.dest, value)
        action._mark_parsed_argument(parser)


class RawDescriptionDefaultsHelpFormatter(
        argparse.RawDescriptionHelpFormatter,
        argparse.ArgumentDefaultsHelpFormatter):
    ...


class CompatArgumentParser(argparse.ArgumentParser):
    """
    For Python 3.6-3.8 compatibility where the exit_on_error flag does not
    exist.
    """

    def __init__(self, *args, **kwargs):
        self.exit_on_error = kwargs.pop('exit_on_error', True)
        super().__init__(*args, **kwargs)

    # def error(self, message):
    #     if self.exit_on_error:
    #         super().error(message)

    def parse_known_args(self, args=None, namespace=None):
        # This is the version from Python 3.10
        from argparse import _sys, Namespace, SUPPRESS, ArgumentError
        from argparse import _UNRECOGNIZED_ARGS_ATTR
        import os
        if args is None:
            # args default to the system args
            args = _sys.argv[1:]
        else:
            # make sure that args are mutable
            args = list(args)
            # Allow Paths objects
            args = [os.fspath(a) if isinstance(a, os.PathLike) else a for a in args]

        # default Namespace built from parser defaults
        if namespace is None:
            namespace = Namespace()

        # add any action defaults that aren't present
        for action in self._actions:
            if action.dest is not SUPPRESS:
                if not hasattr(namespace, action.dest):
                    if action.default is not SUPPRESS:
                        setattr(namespace, action.dest, action.default)

        # add any parser defaults that aren't present
        for dest in self._defaults:
            if not hasattr(namespace, dest):
                setattr(namespace, dest, self._defaults[dest])

        # parse the arguments and exit if there are any errors
        if self.exit_on_error:
            try:
                namespace, args = self._parse_known_args(args, namespace)
            except ArgumentError:
                err = _sys.exc_info()[1]
                self.error(str(err))
        else:
            namespace, args = self._parse_known_args(args, namespace)

        if hasattr(namespace, _UNRECOGNIZED_ARGS_ATTR):
            args.extend(getattr(namespace, _UNRECOGNIZED_ARGS_ATTR))
            delattr(namespace, _UNRECOGNIZED_ARGS_ATTR)
        return namespace, args

    def _parse_optional(self, arg_string):
        """
        Allow "_" or "-" on the CLI.

        https://stackoverflow.com/questions/53527387/make-argparse-treat-dashes-and-underscore-identically
        """
        from gettext import gettext as gettext_fn

        # if it's an empty string, it was meant to be a positional
        if not arg_string:
            return None

        # if it doesn't start with a prefix, it was meant to be positional
        if not arg_string[0] in self.prefix_chars:
            return None

        # if it's just a single character, it was meant to be positional
        if len(arg_string) == 1:
            return None

        option_tuples = self._get_option_tuples(arg_string)

        # if multiple actions match, the option string was ambiguous
        if len(option_tuples) > 1:
            options = ', '.join([option_string
                                 for action, option_string, explicit_arg in option_tuples])
            args = {'option': arg_string, 'matches': options}
            msg = gettext_fn('ambiguous option: %(option)s could match %(matches)s')
            self.error(msg % args)

        # if exactly one action matched, this segmentation is good,
        # so return the parsed action
        elif len(option_tuples) == 1:
            option_tuple, = option_tuples
            return option_tuple

        # if it was not found as an option, but it looks like a negative
        # number, it was meant to be positional
        # unless there are negative-number-like options
        if self._negative_number_matcher.match(arg_string):
            if not self._has_negative_number_optionals:
                return None

        # if it contains a space, it was meant to be a positional
        if ' ' in arg_string:
            return None

        # it was meant to be an optional but there is no such option
        # in this parser (though it might be a valid option in a subparser)
        return None, arg_string, None

    def _get_option_tuples(self, option_string):
        result = []

        if '=' in option_string:
            option_prefix, explicit_arg = option_string.split('=', 1)
        else:
            option_prefix = option_string
            explicit_arg = None
        if option_prefix in self._option_string_actions:
            action = self._option_string_actions[option_prefix]
            tup = action, option_prefix, explicit_arg
            result.append(tup)
        else:  # imperfect match
            chars = self.prefix_chars
            if option_string[0] in chars and option_string[1] not in chars:
                # short option: if single character, can be concatenated with arguments
                short_option_prefix = option_string[:2]
                short_explicit_arg = option_string[2:]
                if short_option_prefix in self._option_string_actions:
                    action = self._option_string_actions[short_option_prefix]
                    tup = action, short_option_prefix, short_explicit_arg
                    result.append(tup)

            underscored = {k.replace('-', '_'): k for k in self._option_string_actions}
            option_prefix = option_prefix.replace('-', '_')
            if option_prefix in underscored:
                action = self._option_string_actions[underscored[option_prefix]]
                tup = action, underscored[option_prefix], explicit_arg
                result.append(tup)
            elif self.allow_abbrev:
                for option_string in underscored:
                    if option_string.startswith(option_prefix):
                        action = self._option_string_actions[underscored[option_string]]
                        tup = action, underscored[option_string], explicit_arg
                        result.append(tup)

        # return the collected option tuples
        return result
