

def test_inheritence():
    """
    Test that a inheriting from a dataconfig unions existing config options
    with new ones.
    """
    from scriptconfig import DataConfig
    import ubelt as ub

    class Config1(DataConfig):
        arg1 = 1
        arg2 = 2
        arg3 = 3

    class Config2(Config1):
        arg4 = 4
        arg5 = 5
        arg6 = 6

    class Config3(Config2):
        arg2 = 22
        arg3 = 33
        arg5 = 55

    c1 = Config1()
    c2 = Config2()
    c3 = Config3()
    text1 = ('c1 = {}'.format(ub.urepr(c1, nl=1)))
    text2 = ('c2 = {}'.format(ub.urepr(c2, nl=1)))
    text3 = ('c3 = {}'.format(ub.urepr(c3, nl=1)))

    print(text1)
    print(text2)
    print(text3)
    assert text1 == ub.codeblock(
        '''
        c1 = Config1(**{
            'arg1': 1,
            'arg2': 2,
            'arg3': 3,
        })
        ''')
    assert text2 == ub.codeblock(
        '''
        c2 = Config2(**{
            'arg1': 1,
            'arg2': 2,
            'arg3': 3,
            'arg4': 4,
            'arg5': 5,
            'arg6': 6,
        })
        ''')
    assert text3 == ub.codeblock(
        '''
        c3 = Config3(**{
            'arg1': 1,
            'arg2': 22,
            'arg3': 33,
            'arg4': 4,
            'arg5': 55,
            'arg6': 6,
        })
        ''')


def test_multiple_inheritence():
    """
    Ensure that a class can inherit from multiple DataConfigs and become the
    union of them.
    """
    from scriptconfig import DataConfig

    class Fooable(DataConfig):
        foo_arg1 = 1
        foo_arg2 = 2
        foobarg1 = 3
        foobarg2 = 4

    class Barable(DataConfig):
        bar_arg1 = 'a'
        bar_arg2 = 'b'
        foobarg1 = 'c'
        foobarg2 = 'd'

    class Foobarable(Fooable, Barable):
        foo_arg2 = ...
        bar_arg2 = ...
        foobarg2 = ...
        new_arg = 'NEW'

    config = Foobarable()
    import ubelt as ub
    text = ub.urepr(config, nl=1)
    print(text)
    assert text == ub.codeblock(
        '''
        Foobarable(**{
            'bar_arg1': 'a',
            'bar_arg2': Ellipsis,
            'foobarg1': 3,
            'foobarg2': Ellipsis,
            'foo_arg1': 1,
            'foo_arg2': Ellipsis,
            'new_arg': 'NEW',
        })
        ''')


def test_multiple_inheritence_diamond():
    """
    Test that diamond inheritence diagrams union options correctly.
    """
    from scriptconfig import DataConfig

    class Base(DataConfig):
        base_arg1 = 'B1'
        base_arg2 = 'B2'
        base_arg3 = 'B3'
        base_arg4 = 'B4'

    class Left(Base):
        left_arg1 = 'L1'
        left_arg2 = 'L2'
        base_arg2 = 'L_B2'

    class Right(Base):
        right_arg1 = 'R1'
        right_arg2 = 'R2'
        base_arg3 = 'R_B3'

    class Joined(Left, Right):
        left_arg2 = 'J1'
        right_arg2 = 'J2'
        base_arg4 = 'J3'

    config = Joined()
    import ubelt as ub
    text = ub.urepr(config, nl=1)
    print(text)
    assert text == ub.codeblock(
        '''
        Joined(**{
            'base_arg1': 'B1',
            'base_arg2': 'L_B2',
            'base_arg3': 'B3',
            'base_arg4': 'J3',
            'right_arg1': 'R1',
            'right_arg2': 'J2',
            'left_arg1': 'L1',
            'left_arg2': 'J1',
        })
        ''')
