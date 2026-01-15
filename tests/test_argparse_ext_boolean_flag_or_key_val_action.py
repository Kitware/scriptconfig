import argparse
import pytest

from scriptconfig.argparse_ext import BooleanFlagOrKeyValAction


def make_parser(default=None, type_=None, with_short=True, help_text=None, formatter=None):
    kwargs = {}
    if formatter is not None:
        kwargs["formatter_class"] = formatter
    parser = argparse.ArgumentParser(**kwargs)

    optnames = []
    if with_short:
        optnames.append("-f")
    optnames.append("--flag")

    parser.add_argument(
        *optnames,
        action=BooleanFlagOrKeyValAction,
        default=default,
        type=type_,
        help=help_text,
    )
    return parser


def test_default_none_no_args():
    parser = make_parser(default=None)
    ns = parser.parse_args([])
    assert ns.flag is None


def test_default_true_no_args():
    parser = make_parser(default=True)
    ns = parser.parse_args([])
    assert ns.flag is True


def test_default_false_no_args():
    parser = make_parser(default=False)
    ns = parser.parse_args([])
    assert ns.flag is False


def test_positive_flag_sets_true_from_default_none():
    parser = make_parser(default=None)
    ns = parser.parse_args(["--flag"])
    assert ns.flag is True


def test_positive_flag_sets_true_from_default_false():
    parser = make_parser(default=False)
    ns = parser.parse_args(["--flag"])
    assert ns.flag is True


def test_negative_flag_sets_false_from_default_true():
    parser = make_parser(default=True)
    ns = parser.parse_args(["--no-flag"])
    assert ns.flag is False


def test_negative_flag_sets_false_from_default_none():
    parser = make_parser(default=None)
    ns = parser.parse_args(["--no-flag"])
    assert ns.flag is False


def test_keyval_equals_true_variants():
    parser = make_parser(default=None)
    assert parser.parse_args(["--flag=1"]).flag == 1
    assert parser.parse_args(["--flag=true"]).flag is True
    assert parser.parse_args(["--flag=True"]).flag is True
    assert parser.parse_args(["--flag=yes"]).flag == 'yes'


def test_keyval_equals_false_variants():
    parser = make_parser(default=None)
    assert parser.parse_args(["--flag=0"]).flag == 0
    assert parser.parse_args(["--flag=false"]).flag is False
    assert parser.parse_args(["--flag=False"]).flag is False
    assert parser.parse_args(["--flag=no"]).flag == 'no', 'note: string should win'


def test_keyval_space_true_variants():
    parser = make_parser(default=None)
    assert parser.parse_args(["--flag", "1"]).flag == 1
    assert parser.parse_args(["--flag", "true"]).flag is True
    assert parser.parse_args(["--flag", "True"]).flag is True
    assert parser.parse_args(["--flag", "yes"]).flag == 'yes'


def test_keyval_space_false_variants():
    parser = make_parser(default=None)
    assert parser.parse_args(["--flag", "0"]).flag == 0
    assert parser.parse_args(["--flag", "false"]).flag is False
    assert parser.parse_args(["--flag", "False"]).flag is False
    assert parser.parse_args(["--flag", "no"]).flag == 'no', 'note: string should win'


def test_negated_keyval_is_flipped_current_behavior():
    """
    Current implementation flips the parsed value when using --no-flag=<val>.
    Docstring calls this a "probably shouldn't" feature; this test documents it.

    If you later decide to forbid values on --no-flag, change this to expect SystemExit.
    """
    parser = make_parser(default=None)
    assert parser.parse_args(["--no-flag=0"]).flag is True
    assert parser.parse_args(["--no-flag=1"]).flag is False
    assert parser.parse_args(["--no-flag=false"]).flag is True
    assert parser.parse_args(["--no-flag=true"]).flag is False


def test_short_flag_works_but_no_auto_no_short():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--flag', '-f', action=BooleanFlagOrKeyValAction)
    assert parser.parse_args(["-f"]).flag is True
    # '--no-f' is not generated: should error (SystemExit: 2)
    with pytest.raises(SystemExit) as ex:
        parser.parse_args(["--no-f"])
    assert ex.value.code == 2


def test_last_one_wins_mixed_forms():
    parser = make_parser(default=None)

    assert parser.parse_args(["--flag", "--no-flag"]).flag is False
    assert parser.parse_args(["--no-flag", "--flag"]).flag is True
    assert parser.parse_args(["--flag=0", "--flag=1"]).flag == 1
    assert parser.parse_args(["--flag=1", "--flag=0"]).flag == 0
    assert parser.parse_args(["--no-flag", "--flag=0"]).flag == 0
    assert parser.parse_args(["--flag=1", "--no-flag"]).flag is False


def test_explicitly_given_tracking_is_set():
    parser = make_parser(default=None)
    assert not hasattr(parser, "_explicitly_given")

    ns = parser.parse_args(["--flag"])
    assert ns.flag is True
    assert hasattr(parser, "_explicitly_given")
    assert "flag" in parser._explicitly_given


def test_type_cast_str_positive_value():
    parser = make_parser(default=None, type_=str)
    assert parser.parse_args(["--flag=auto"]).flag == "auto"
    assert parser.parse_args(["--flag", "auto"]).flag == "auto"


def test_type_cast_str_negated_value_is_truthiness_flip_footgun():
    """
    With type=str, '--no-flag=auto' parses to "auto" then flips to False because not "auto" is False.
    """
    parser = make_parser(default=None, type_=str)
    assert parser.parse_args(["--no-flag=auto"]).flag is False


def test_positional_boolean_option():
    """
    This is not typical usage, but in this case, error if the user tries do to
    this.
    """
    import argparse
    from scriptconfig.argparse_ext import BooleanFlagOrKeyValAction
    parser = argparse.ArgumentParser()
    parser.add_argument("flag", action=BooleanFlagOrKeyValAction)
    with pytest.raises(Exception):
        ns = parser.parse_args([])
    with pytest.raises(Exception):
        ns = parser.parse_args(["true"])



def test_help_default_duplication_can_happen_with_argumentdefaults_formatter():
    """
    This documents a potential help-text duplication if the action appends default text
    and the formatter also appends defaults.
    """
    parser = make_parser(
        default=True,
        help_text="enable flag",
        formatter=argparse.ArgumentDefaultsHelpFormatter,
    )
    text = parser.format_help().lower()
    assert "default" in text


def test_bool_as_positional():
    import scriptconfig as scfg
    class MyConfig(scfg.DataConfig):
        my_key = scfg.Value(False, isflag=True, position=1)
    parser = MyConfig().argparse()
    assert not parser.parse_args([]).my_key, 'empty args should keep default'
    assert parser.parse_args(['1']).my_key, 'positional truthy boolean should be true'
    assert not parser.parse_args(['0']).my_key, 'positional falsy boolean should be false'
    assert parser.parse_args(['true']).my_key, 'positional truthy is truthy'
    assert not parser.parse_args(['1', '--my_key=0']).my_key, 'second position should win'
    assert parser.parse_args(['0', '--my_key=1']).my_key, 'second position should win'
    assert parser.parse_args(['--my_key=0', '1']).my_key, 'second position should win'
    assert not parser.parse_args(['--my_key=1', '0']).my_key, 'second position should win'


def test_smartcast_boolean_option():
    """
    This is not typical usage, but in this case, error if the user tries do to
    this.
    """
    import argparse
    from scriptconfig.argparse_ext import BooleanFlagOrKeyValAction
    parser = argparse.ArgumentParser()
    parser.add_argument("--flag", action=BooleanFlagOrKeyValAction)
    ns = parser.parse_args(["--flag=fo,o"])
    assert ns.flag == ['fo', 'o'], 'Note: this behavior will change in 2.x to return the regular string. This test will change in that case'

    from scriptconfig import smartcast as smartcast_mod
    parser = argparse.ArgumentParser()
    parser.add_argument("--flag", type=lambda x: smartcast_mod.smartcast(x, 'smartcast:v1'), action=BooleanFlagOrKeyValAction)
    ns = parser.parse_args(["--flag=fo,o"])
    assert ns.flag == 'fo,o'

def test_boolean_action_with_type():
    # You should likely not use type with this action,
    from scriptconfig import smartcast as smartcast_mod
    parser = argparse.ArgumentParser()
    parser.add_argument("--flag", type=float, action=BooleanFlagOrKeyValAction)
    ns = parser.parse_args(["--flag=1."])
    assert type(ns.flag) == float
    ns = parser.parse_args(["--flag"])
    assert ns.flag is True, 'positional flag ignores the type, not sure if this is good behavior'
