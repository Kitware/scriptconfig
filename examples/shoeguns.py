import ubelt as ub
import scriptconfig as scfg


class ShoeGunConfig(scfg.DataConfig):
    src = scfg.Value(None, position=1)
    option1 = scfg.Value(None)
    option2 = scfg.Value(None)
    sub_config = scfg.Value(None)


# This is a correct invocation of the CLI with an argv string It works as you
# expect, but if you make a small typo you will get encounter a shoegun.
config_good = ShoeGunConfig.cli(argv=[
    '--src', 'input_data',
    '--option1', 'my_value',
    '--sub_config', ub.codeblock(
        '''
        - subkey1
        - subkey2
        ''')
])


# In `config_typo` we will "forget" a comma after specifying the value for
# 'option1'. This causes the predictable bug that the "value" for "option1"
# will be set as "preference--sub_config" because of Python's implicit string
# concatenation. However, what is not intuitive is that the unhandled value
# will not be treated as a positional argument and overwrite the value of
# "src".
config_typo = ShoeGunConfig.cli(argv=[
    '--src', 'srcfile',
    '--option1', 'preference'
    '--sub_config', ub.codeblock(
        '''
        - subkey1
        - subkey2
        ''')
])


print('config_good = {}'.format(ub.urepr(config_good, nl=1)))
print('config_typo = {}'.format(ub.urepr(config_typo, nl=1)))


# TODO: can we determine that an argument was "eaten"?
