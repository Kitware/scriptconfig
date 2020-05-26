def convert_argparse(parser):
    """
    Helper for converting an existing argparse object to scriptconfig
    definition.
    """
    import argparse
    import ubelt as ub
    value_template1 = '{dest!r}: scfg.Value({default!r}, help={help!r})'
    value_template2 = '{dest!r}: scfg.Value({default!r})'

    lines = []
    for action in parser._actions:
        if action.default == argparse.SUPPRESS:
            continue
        if action.help is None:
            value_text = value_template2.format(
                dest=action.dest,
                default=action.default,
            )
        else:
            value_text = value_template1.format(
                dest=action.dest,
                default=action.default,
                help=ub.paragraph(action.help))
        lines.append(value_text + ',')

    class_template = ub.codeblock(
        '''
        import scriptconfig as scfg
        class MyConfig(scfg.Config):
            """{desc}"""
            default = {{
        {body}
            }}
        ''')

    body = ub.indent('\n'.join(lines), ' ' * 8)
    text = class_template.format(body=body, desc=parser.description)
    print(text)
