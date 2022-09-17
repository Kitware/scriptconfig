

def test_paths_with_commas():
    from scriptconfig.value import Value, Path

    self = Value('key')
    self.update('/path/with,commas')
    print('self.value = {!r}'.format(self.value))
    assert isinstance(self.value, list), 'without specifying types a string with commas will be smartcast'

    self = Value('key', type=str)
    self.update('/path/with,commas')
    print('self.value = {!r}'.format(self.value))
    assert isinstance(self.value, str), 'specifying a type should prevent smartcast'

    self = Path('key')
    self.update('/path/with,commas')
    print('self.value = {!r}'.format(self.value))
    assert isinstance(self.value, str), 'specifying a type should prevent smartcast'


def test_paths_with_commas_in_config():
    import scriptconfig as scfg
    class TestConfig(scfg.Config):
        default = {
            'key': scfg.Value(None, type=str),
        }

    kw = {
        'key': '/path/with,commas',
    }
    config = TestConfig(default=kw, cmdline=False)
    print(config['key'])
    assert isinstance(config['key'], str), 'specifying a type should prevent smartcast'

    # In the past setting cmdline=True did cause an error
    config = TestConfig(default=kw, cmdline=True)
    print(config['key'])
    assert isinstance(config['key'], str), 'specifying a type should prevent smartcast'


def test_globstr_with_nargs():
    from os.path import join
    import ubelt as ub
    import scriptconfig as scfg
    dpath = ub.Path.appdir('scriptconfig', 'tests', 'files').ensuredir()
    ub.touch(join(dpath, 'file1.txt'))
    ub.touch(join(dpath, 'file2.txt'))
    ub.touch(join(dpath, 'file3.txt'))

    class TestConfig(scfg.Config):
        default = {
            'paths': scfg.Value(None, nargs='+'),
        }

    cmdline = '--paths {dpath}/*'.format(dpath=dpath)
    config = TestConfig(cmdline=cmdline)

    # ub.cmd(f'echo {dpath}/*', shell=True)

    import glob
    cmdline = '--paths ' + ' '.join(list(glob.glob(join(dpath, '*'))))
    config = TestConfig(cmdline=cmdline)

    cmdline = '--paths=' + ','.join(list(glob.glob(join(dpath, '*'))))
    config = TestConfig(cmdline=cmdline)  # NOQA
