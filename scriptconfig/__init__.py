"""
ScriptConfig
============

The goal of ``scriptconfig`` is to make it easy to be able to define a CLI by
**simply defining a dictionary**. Thie enables you to write simple configs and
update from CLI, kwargs, and/or json.

The pattern is simple:

    1. Create a class that inherits from :class:`scriptconfig.Config`

    2. Create a class variable dictionary named ``default``

    3. The keys are the names of your arguments, and the values are the defaults.

    4. Create an instance of your config object. If you pass ``cmdline=True`` as an argument, it will autopopulate itself from the command line.

Here is an example for a simple calculator program:

.. code:: python

    import scriptconfig as scfg


    class MyConfig(scfg.Config):
        'The docstring becomes the CLI description!'
        default = {
            'num1': 0,
            'num2': 1,
            'outfile': './result.txt',
        }


    def main():
        config = MyConfig(cmdline=True)
        result = config['num1'] + config['num2']
        with open(config['outfile'], 'w') as file:
            file.write(str(result))


    if __name__ == '__main__':
        main()

If the above is written to a file `calc.py`, it can be be called like this.

.. code:: bash

    python calc.py --num1=3 --num2=4 --outfile=/dev/stdout

It is possible to gain finer control over the CLI by specifying the values in
``default`` as a :class:`scriptconfig.Value`, where you can specify a help
message, the expected variable type, if it is a positional variable, alias
parameters for the command line, and more.

The important thing that gives scriptconfig an edge over things like
:mod:`argparse` is that it is trivial to disable the ``cmdline`` flag and pass
explicit arguments into your function as a dictionary. Thus you can write you
scripts in such a way that they are callable from Python or from a CLI via with
an API that corresponds 1-to-1!

A more complex example version of the above code might look like this

.. code:: python

    import scriptconfig as scfg


    class MyConfig(scfg.Config):
        '''
        The docstring becomes the CLI description!
        '''
        default = {
            'num1': scfg.Value(0, type=float, help='first number to add', position=1),
            'num2': scfg.Value(1, type=float, help='second number to add', position=2),
            'outfile': scfg.Value('./result.txt', help='where to store the result', position=3),
        }


    def main(cmdline=1, **kwargs):
        '''
        Example:
            >>> # This is much easier to test than argparse code
            >>> kwargs = {'num1': 42, 'num2': 23, 'outfile': 'foo.out'}
            >>> cmdline = 0
            >>> main(cmdline=cmdline, **kwargs)
            >>> with open('foo.out') as file:
            >>>     assert file.read() == '65'
        '''
        config = MyConfig(cmdline=True, data=kwargs)
        result = config['num1'] + config['num2']
        with open(config['outfile'], 'w') as file:
            file.write(str(result))


    if __name__ == '__main__':
        main()

This code can be called with positional arguments:

.. code:: bash

    python calc.py 33 44 /dev/stdout


The help text for this program (via ``python calc.py --help``) looks like this:

.. code::

    usage: MyConfig [-h] [--num1 NUM1] [--num2 NUM2] [--outfile OUTFILE] [--config CONFIG] [--dump DUMP] [--dumps] num1 num2 outfile

    The docstring becomes the CLI description!

    positional arguments:
      num1               first number to add
      num2               second number to add
      outfile            where to store the result

    optional arguments:
      -h, --help         show this help message and exit
      --num1 NUM1        first number to add (default: 0)
      --num2 NUM2        second number to add (default: 1)
      --outfile OUTFILE  where to store the result (default: ./result.txt)
      --config CONFIG    special scriptconfig option that accepts the path to a on-disk configuration file, and loads that into this 'MyConfig' object. (default: None)
      --dump DUMP        If specified, dump this config to disk. (default: None)
      --dumps            If specified, dump this config stdout (default: False)


Note that keyword arguments are always available, even if the argument is
marked as positional. This is because a scriptconfig object always reduces to
key/value pairs --- i.e. a dictionary.


See the :mod:`scriptconfig.config` module docs for details and examples on
getting started.
"""

__autogen__ = """
Ignore:
    mkinit ~/code/scriptconfig/scriptconfig/__init__.py --nomods --relative --diff
    mkinit ~/code/scriptconfig/scriptconfig/__init__.py --nomods --relative -w
"""

__version__ = '0.7.5'

__submodules__ = {
    'config': None,
    'value': None,
    'cli': None,
    'dataconfig': None,
}

from .config import (Config, define,)
from .value import (Path, PathList, Value,)
from .cli import (quick_cli,)
from .dataconfig import (DataConfig, dataconf,)

__all__ = ['Config', 'DataConfig', 'Path', 'PathList', 'Value', 'dataconf',
           'define', 'quick_cli']
