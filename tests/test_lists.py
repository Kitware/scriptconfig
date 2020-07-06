import ubelt as ub


def test_list_parsing():
    """

    References:
        .. [1] https://stackoverflow.com/questions/15753701/how-can-i-pass-a-list-as-a-command-line-argument-with-argparse

        .. [2] https://www.gnu.org/prep/standards/html_node/Command_002dLine-Interfaces.html

        .. [3] http://www.catb.org/~esr/writings/taoup/html/ch10s05.html

        .. [4] https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/V1_chap12.html

         https://stackoverflow.com/questions/8957222/are-there-standards-for-linux-command-line-switches-and-arguments

         https://www.gnu.org/software/libc/manual/html_node/Getopt-Long-Options.html

    Ideal Spec:
        The input is a list of lexed argv tokens: e.g. sys.argv[1:]

        For boolean flag options `--{name}` is equivalent to `--{name}=True`

        A single valued argument should be able to be specified as either
        `--{name} {value}` OR `--{name}={value}`

        A multi-valued argument should be specifiable as
            `--{name} {parsable_delimited_values}` OR
            `--{name} {value1} {value2} ... {valueN}` OR
            `--{name}={parsable_delimited_values}` OR

            Note: the above may have ambuguities and we need to look into that
            and potentiall restrict the spec.

        The following is NOT acceptable due because it would cause ambiguities.
            `--{name}={value1} {value2} ... {valueN}`

        Positional arguments can occur:
            (1) at the beginning of the lexed-argv tokens,
            (2) after any single-valued argument

        Positional cannot arguments can occur:
            (3) after a multi-valued space delimited argument.

    TODO:

        - [ ] There is almost no situation where the argparse type should be
          able to be passed as "list", See[1]. Therefore if a Value has a type
          of "list" we should do special handling of it.


        - [ ] A list Value should be able to accept either multiple traditional
          nargs space-separated values, or a comma delimited list of values.
    """
    import scriptconfig as scfg

    # FIXME: We need make parsing lists a bit more intuitive
    # FIXME: Parsing lists is currently very fragile

    class ExampleConfig(scfg.Config):
        default = {
            'item1': [],
            'item2': scfg.Value([], type=list),
            'item3': scfg.Value([]),
            'item4': scfg.Value([], nargs='*'),
        }
    config = ExampleConfig()
    print('config._default = {}'.format(ub.repr2(config._default, nl=1)))
    print('config._data = {}'.format(ub.repr2(config._data, nl=1)))

    parser = config.argparse()
    print('parser._actions = {}'.format(ub.repr2(parser._actions, nl=1)))

    # IDEALLY BOTH CASES SHOULD WORK
    config.load(cmdline=[
        '--item1', 'spam', 'eggs',
        '--item2', 'spam', 'eggs',
        '--item3', 'spam', 'eggs',
        '--item4', 'spam', 'eggs',
    ])
    print('loaded = ' + ub.repr2(config.asdict(), nl=1))
    # ub.map_vals(len, config)

    config.load(cmdline=[
        '--item1=spam,eggs',
        '--item2=spam,eggs',
        '--item3=spam,eggs',
        '--item4=spam,eggs',
    ])
    print('loaded = ' + ub.repr2(config.asdict(), nl=1))
