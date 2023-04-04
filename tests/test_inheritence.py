

def test_inheritence():
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
        c1 = Config1({
            'arg1': 1,
            'arg2': 2,
            'arg3': 3,
        })
        ''')
    assert text2 == ub.codeblock(
        '''
        c2 = Config2({
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
        c3 = Config3({
            'arg1': 1,
            'arg2': 22,
            'arg3': 33,
            'arg4': 4,
            'arg5': 55,
            'arg6': 6,
        })
        ''')
