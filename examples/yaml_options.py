import scriptconfig as scfg
import ubelt as ub


class FooConfig(scfg.DataConfig):
    options = scfg.Value(None, help='A dictionary with blah... Can be yaml-coerced')

    def __post_init__(self):
        from watch.utils.util_yaml import Yaml
        self.options = Yaml.coerce(self.options)

config = FooConfig()
print('config.options = {}'.format(ub.urepr(config.options, nl=1)))

config = FooConfig(options=(
    '''
    a: 1.0
    b: 2.0
    c: yaml-is-easy-to-write
    '''))
print('config.options = {}'.format(ub.urepr(config.options, nl=1)))

config = FooConfig(options={
    'a': 'works',
    'b': 'as a raw input too',
    'c': 3,
})
print('config.options = {}'.format(ub.urepr(config.options, nl=1)))
