ScriptConfig
============

.. # TODO Get CI services running on gitlab
.. #|CircleCI| |Travis| |Codecov| |ReadTheDocs|

|GitlabCIPipeline| |GitlabCICoverage| |Appveyor| |Pypi| |PypiDownloads|


+------------------+--------------------------------------------------+
| Read the docs    | https://scriptconfig.readthedocs.io              |
+------------------+--------------------------------------------------+
| Gitlab (main)    | https://gitlab.kitware.com/utils/scriptconfig    |
+------------------+--------------------------------------------------+
| Github (mirror)  | https://github.com/Kitware/scriptconfig          |
+------------------+--------------------------------------------------+
| Pypi             | https://pypi.org/project/scriptconfig            |
+------------------+--------------------------------------------------+

The goal of ``scriptconfig`` is to make it easy to be able to define a default
configuration by **simply defining a dictionary**, and then allow that
configuration to be modified by either:

1. Updating it with another Python dictionary (e.g. ``kwargs``)
2. Reading a YAML/JSON configuration file, or
3. Inspecting values on ``sys.argv``, in which case we provide a powerful
   command line interface (CLI).

The simplest way to create a script config is to create a class that inherits
from ``scriptconfig.DataConfig``.  Then, use class variables to define the
expected keys and default values.

.. code-block:: python

    import scriptconfig as scfg

    class ExampleConfig(scfg.DataConfig):
        """
        The docstring will be the description in the CLI help
        """

        # Wrap defaults with `Value` to provide metadata

        option1 = scfg.Value('default1', help='option1 help')
        option2 = scfg.Value('default2', help='option2 help')
        option3 = scfg.Value('default3', help='option3 help')

        # Wrapping a default with `Value` is optional

        option4 = 'default4'


An instance of a config object will work similarly to a dataclass, but it also
implements methods to duck-type a dictionary. Thus a scriptconfig object can be
dropped into code that uses an existing dictionary configuration or an existing
argparse namespace configuration.


.. code-block:: python

    # Use as a dictionary with defaults
    config = ExampleConfig(option1=123)
    print(config)

    # Can access items like a dictionary
    print(config['option1'])

    # OR Can access items like a namespace
    print(config.option1)


Use the ``.cli`` classmethod to create an extended argparse command line
interface. Options to the ``cli`` method are similar to
``argparse.ArgumentParser.parse_args``.

.. code-block:: python

    # Use as a argparse CLI
    config = ExampleConfig.cli(argv=['--option2=overruled'])
    print(config)


After all that, if you still aren't loving scriptconfig, or you can't use it as
a dependency in production, you can ask it to convert itself to pure-argparse:


.. code-block:: python

    import argparse
    parser = argparse.ArgumentParser(
        prog='ExampleConfig',
        description='The docstring will be the description in the CLI help',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--option1', help='option1 help', default='default1', dest='option1', required=False)
    parser.add_argument('--option2', help='option2 help', default='default2', dest='option2', required=False)
    parser.add_argument('--option3', help='option3 help', default='default3', dest='option3', required=False)
    parser.add_argument('--option4', help='', default='default4', dest='option4', required=False)


Of course, the above also removes extra features of scriptconfig - so its not
exactly 1-to-1, but it's close. It's also a good tool for transferring any
existing intuition about ``argparse`` to ``scriptconfig``.


Goal
----

The idea is we want to be able to start writing a simple program with a simple
configuration and allow it to evolve with minimal refactoring. In the early
stages we will insist that there be little-to-no boilerplate, but as a program
evolves we will add boilerplate to enhance the featurefull-ness of our program.


When we start coding we should aim for something like this:

.. code-block:: python


   def my_function():

       config = {
           'simple_option1': 1,
           'simple_option2': 2,
       }

       # Early algorithmic and debugging logic
       ...


As we evolve our code, we can plug scriptconfig in like this:

.. code-block:: python


   def my_function():

       default_config = {
           'simple_option1': 1,
           'simple_option2': 2,
       }

       import scriptconfig
       class MyConfig(scriptconfig.DataConfig):
           __default__ = default_config

       config = MyConfig()

       # Transition algorithmic and debugging logic
       ...


It's not pretty, but it gives us the ability to a fairly advanced CLI right
away (i.e by calling the ``.cli`` classmethod) without any major sacrifice to
code simplicity. However, as a project evolves we may eventually want to
refactor our CLI to gain full control over the metadata in our configuration an
CLI. Scriptconfig has a tool to help with this too. Given this janky definition,
we can port to a more ellegant style. We can run
``print(config.port_to_dataconf())`` which prints:


.. code-block:: python

    import ubelt as ub
    import scriptconfig as scfg

    class MyConfig(scfg.DataConfig):
        """
        argparse CLI generated by scriptconfig 0.7.12
        """
        simple_option1 = scfg.Value(1, help=None)
        simple_option2 = scfg.Value(2, help=None)


And then use that to make the refactor much easier.
The final state of a scriptconfig program might look something like this:

.. code-block:: python

    import ubelt as ub
    import scriptconfig as scfg

    class MyConfig(scfg.DataConfig):
        """
        This is my CLI description
        """
        simple_option1 = scfg.Value(1, help=ub.paragraph(
            '''
            A reasonably detailed but concise description of an argument.
            About one paragraph is reasonable.
            ''')
        simple_option2 = scfg.Value(2, help='more help is better')

        @classmethod
        def main(cls, cmdline=1, **kwargs):
            config = cls.cli(cmdline=cmdline, data=kwargs)
            my_function(config)

    def my_function(config):
        # Continued algorithmic and debugging logic
        ...

Note that the fundamental impact on the ``...`` -- i.e. the intereting part of
the function -- remain completely unchanged! From it's point of view, you never
did anything to the original ``config`` dictionary, because scriptconfig
duck-typed it at every stage.


Installation
------------

The `scriptconfig <https://pypi.org/project/scriptconfig/>`_  package can be installed via pip:

.. code-block:: bash

    pip install scriptconfig


To install with argcomplete and rich-argparse support, either install these
packages separately or use:


.. code-block:: bash

    pip install scriptconfig[optional]


Features
--------

- Serializes to JSON

- Dict-like interface. By default a ``Config`` object operates independent of config files or the command line.

- Can create command line interfaces

  - Can directly create an independent argparse object

  - Can use special command line loading using ``self.load(cmdline=True)``. This extends the basic argparse interface with:

      - Can specify options as either ``--option value`` or ``--option=value``

      - Default config options allow for "smartcasting" values like lists and paths

      - Automatically add ``--config``, ``--dumps``, and ``--dump`` CLI options
        when reading cmdline via ``load``.

- Fuzzy hyphen matching: e.g. ``--foo-bar=2`` and ``--foo_bar=2`` are treated the same for argparse options (note: modal commands do not have this option yet)

- Inheritance unions configs.

- Modal configs (see scriptconfig.modal)

- Integration with `argcomplete <https://pypi.org/project/argcomplete/>`_ for shell autocomplete.

- Integration with `rich_argparse <https://pypi.org/project/rich_argparse/>`_ for colorful CLI help pages.


Example Script
--------------

Scriptconfig is used to define a flat configuration dictionary with values that
can be specified via Python keyword arguments, command line parameters, or a
YAML config file. Consider the following script that prints its config, opens a
file, computes its hash, and then prints it to stdout.


.. code-block:: python

    import scriptconfig as scfg
    import hashlib


    class FileHashConfig(scfg.DataConfig):
        """
        The docstring will be the description in the CLI help
        """
        fpath = scfg.Value(None, position=1, help='a path to a file to hash')
        hasher = scfg.Value('sha1', choices=['sha1', 'sha512'], help='a name of a hashlib hasher')


    def main(**kwargs):
        config = FileHashConfig.cli(data=kwargs)
        print('config = {!r}'.format(config))
        fpath = config['fpath']
        hasher = getattr(hashlib, config['hasher'])()

        with open(fpath, 'rb') as file:
            hasher.update(file.read())

        hashstr = hasher.hexdigest()
        print('The {hasher} hash of {fpath} is {hashstr}'.format(
            hashstr=hashstr, **config))


    if __name__ == '__main__':
        main()

If this script is in a module ``hash_demo.py`` (e.g. in the examples folder of
this repo), it can be invoked in these following ways.

Purely from the command line:

.. code-block:: bash

    # Get help
    python hash_demo.py --help

    # Using key-val pairs
    python hash_demo.py --fpath=$HOME/.bashrc --hasher=sha1

    # Using a positional arguments and other defaults
    python hash_demo.py $HOME/.bashrc

From the command line using a YAML config:

.. code-block:: bash

    # Write out a config file
    echo '{"fpath": "hashconfig.json", "hasher": "sha512"}' > hashconfig.json

    # Use the special `--config` cli arg provided by scriptconfig
    python hash_demo.py --config=hashconfig.json

    # You can also mix and match, this overrides the hasher in the config with sha1
    python hash_demo.py --config=hashconfig.json --hasher=sha1


Lastly you can call it from good ol' Python.

.. code-block:: python

    import hash_demo
    hash_demo.main(fpath=hash_demo.__file__, hasher='sha512')

Modal CLIs
----------

A ModalCLI defines a way to group several smaller scriptconfig CLIs into a
single parent CLI that chooses between them "modally". E.g. if we define two
configs: do_foo and do_bar, we use ModalCLI to define a parent program that can
run one or the other. Let's make this more concrete.

Consider the code in ``examples/demo_modal.py``:

.. code-block:: python

    import scriptconfig as scfg

    class DoFooCLI(scfg.DataConfig):
        __command__ = 'do_foo'
        option1 = scfg.Value(None, help='option1')

        @classmethod
        def main(cls, cmdline=1, **kwargs):
            self = cls.cli(cmdline=cmdline, data=kwargs)
            print('Called Foo with: ' + str(self))

    class DoBarCLI(scfg.DataConfig):
        __command__ = 'do_bar'
        option1 = scfg.Value(None, help='option1')

        @classmethod
        def main(cls, cmdline=1, **kwargs):
            self = cls.cli(cmdline=cmdline, data=kwargs)
            print('Called Bar with: ' + str(self))

    class MyModalCLI(scfg.ModalCLI):
        __version__ = '1.2.3'
        foo = DoFooCLI
        bar = DoBarCLI

    if __name__ == '__main__':
        MyModalCLI().main()


Running: ``python examples/demo_modal.py  --help``, results in:


.. code-block::

    usage: demo_modal.py [-h] [--version] {do_foo,do_bar} ...

    options:
      -h, --help       show this help message and exit
      --version        show version number and exit (default: False)

    commands:
      {do_foo,do_bar}  specify a command to run
        do_foo         argparse CLI generated by scriptconfig 0.7.12
        do_bar         argparse CLI generated by scriptconfig 0.7.12


And if you specify a command, ``python examples/demo_modal.py do_bar --help``, you get the help for that subcommand:


.. code-block::

    usage: DoBarCLI [-h] [--option1 OPTION1]

    argparse CLI generated by scriptconfig 0.7.12

    options:
      -h, --help         show this help message and exit
      --option1 OPTION1  option1 (default: None)


Autocomplete
------------

If you installed the optional `argcomplete <https://pypi.org/project/argcomplete/>`_ package you will find that pressing
tab will autocomplete registered arguments for scriptconfig CLIs. See project instructions for details, but on standard Linux
distributions you can enable global completion via:


.. code:: bash

    pip install argcomplete
    mkdir -p ~/.bash_completion.d
    activate-global-python-argcomplete --dest ~/.bash_completion.d
    source ~/.bash_completion.d/python-argcomplete

And then add these lines to your ``.bashrc``:

.. code:: bash

    if [ -f "$HOME/.bash_completion.d/python-argcomplete" ]; then
        source ~/.bash_completion.d/python-argcomplete
    fi


Lastly, ensure your Python script has the following two comments at the top:

.. code:: python

    #!/usr/bin/env python
    # PYTHON_ARGCOMPLETE_OK

Project Design Goals
--------------------

    * Write Python programs that can be invoked either through the commandline
      or via Python itself.

    * Drop in replacement for any dictionary-based configuration system.

    * Intuitive parsing (currently working on this), ideally improve on
      argparse if possible. This means being able to easily specify simple
      lists, numbers, strings, and paths.

To get started lets consider some example usage:

.. code-block:: python

    >>> import scriptconfig as scfg
    >>> # In its simplest incarnation, the config class specifies default values.
    >>> # For each configuration parameter.
    >>> class ExampleConfig(scfg.DataConfig):
    >>>     num = 1
    >>>     mode = 'bar'
    >>>     ignore = ['baz', 'biz']
    >>> # Creating an instance, starts using the defaults
    >>> config = ExampleConfig()
    >>> assert config['num'] == 1
    >>> # Or pass in known data. (load as shown in the original example still works)
    >>> kwargs = {'num': 2}
    >>> config = ExampleConfig.cli(default=kwargs, cmdline=False)
    >>> assert config['num'] == 2
    >>> # The `load` method can also be passed a JSON/YAML file/path.
    >>> config_fpath = '/tmp/foo'
    >>> open(config_fpath, 'w').write('{"mode": "foo"}')
    >>> config.load(config_fpath, cmdline=False)
    >>> assert config['num'] == 2
    >>> assert config['mode'] == "foo"
    >>> # It is possbile to load only from CLI by setting cmdline=True
    >>> # or by setting it to a custom sys.argv
    >>> config = ExampleConfig.cli(argv=['--num=4'])
    >>> assert config['num'] == 4
    >>> # Note that using `config.load(cmdline=True)` will just use the
    >>> # contents of sys.argv


Notice in the above example the keys in your default dictionary are command
line arguments and values are their defaults.  You can augment default values
by wrapping them in ``scriptconfig.Value`` objects to encapsulate information
like help documentation or type information.


.. code-block:: python

    >>> import scriptconfig as scfg
    >>> class ExampleConfig(scfg.Config):
    >>>     __default__ = {
    >>>         'num': scfg.Value(1, help='a number'),
    >>>         'mode': scfg.Value('bar', help='mode1 help'),
    >>>         'mode2': scfg.Value('bar', type=str, help='mode2 help'),
    >>>         'ignore': scfg.Value(['baz', 'biz'], help='list of ignore vals'),
    >>>     }
    >>> config = ExampleConfig()
    >>> # smartcast can handle lists as long as there are no spaces
    >>> config.load(cmdline=['--ignore=spam,eggs'])
    >>> assert config['ignore'] == ['spam', 'eggs']
    >>> # Note that the Value type can influence how data is parsed
    >>> config.load(cmdline=['--mode=spam,eggs', '--mode2=spam,eggs'])

(Note the above example uses the older ``Config`` usage pattern where
attributes are members of a ``__default__`` dictionary. The ``DataConfig``
class should be favored moving forward past version 0.6.2. However,
the ``__default__`` attribute is always available if you have an existing
dictionary you want to wrap with scriptconfig.


Gotchas
-------

**CLI Values with commas:**

When using ``scriptconfig`` to generate a command line interface, it uses a
function called ``smartcast`` to try to determine input type when it is not
explicitly given. If you've ever used a program that tries to be "smart" you'll
know this can end up with some weird behavior. The case where that happens here
is when you pass a value that contains commas on the command line. If you don't
specify the default value as a ``scriptconfig.Value`` with a specified
``type``, if will interpret your input as a list of values. In the future we
may change the behavior of ``smartcast``, or prevent it from being used as a
default.

**Boolean flags and positional arguments:**

``scriptconfig`` always provides a key/value way to express arguments. However, it also
recognizes that sometimes you want to just type ``--flag`` and not ``--flag=1``.
We allow for this for ``Values`` with ``isflag=1``, but this causes a
corner-case ambituity with positional arguments. For the following example:


.. code:: python

    class MyConfig(scfg.DataConfig):
        arg1 = scfg.Value(None, position=1)
        flag1 = scfg.Value(False, isflag=True, position=1)


For ``--flag 1`` We cannot determine if you wanted
``{'arg1': 1, 'flag1': False}`` or ``{'arg1': None, 'flag1': True}``.

This is fixable by either using strict key/value arguments, expressing all
positional arguments before using flag arguments, or using the `` -- ``
construct and putting all positional arguments at the end. In the future we may
raise an AmbiguityError when specifying arguments like this, but for now we
leave the behavior undefined.


FAQ
---

Question: How do I override the default values for a scriptconfig object using JSON file?

Answer:  This depends if you want to pass the path to that JSON file via the command line or if you have that file in memory already.  There are ways to do either. In the first case you can pass ``--config=<path-to-your-file>`` (assuming you have set the ``cmdline=True`` keyword arg when creating your config object e.g.: ``config = MyConfig(cmdline=True)``. In the second case when you create an instance of the scriptconfig object pass the ``default=<your dict>`` when creating the object: e.g. ``config = MyConfig(default=json.load(open(fpath, 'r')))``.  But the special ``--config`` ``--dump`` and ``--dumps`` CLI arg is baked into script config to make this easier.


Related Software
----------------

I've never been completely happy with existing config / argument parser
software. I prefer to not use decorators, so click and to some extend hydra are
no-gos. Fire is nice when you want a really quick CLI, but is not so nice if
you ever go to deploy the program in the real world.

The builtin argparse in Python is pretty good, but I with it was easier to do
things like allowing arguments to be flags or key/value pairs. This library
uses argparse under the hood because of its stable and standard backend, but
that does mean we inherit some of its quirks.

The configargparse library - like this one - augments argparse with the ability
to read defaults from config files, but it has some major usage limitations due
to its implementation and there are better options (like jsonargparse). It also
does not support the use case of calling the CLI as a Python function very
well.

The jsonargparse library is newer than this one, and looks very compelling.  I
feel like the definition of CLIs in this library are complementary and I'm
considering adding support in this library for jsonargparse because it solves
the problem of nested configurations and I would like to inherit from that.
Keep an eye out for this feature in future work.


Hydra - https://hydra.cc/docs/intro/

OmegaConf - https://omegaconf.readthedocs.io/en/latest/index.html

Argparse - https://docs.python.org/3/library/argparse.html

JsonArgparse - https://jsonargparse.readthedocs.io/en/stable/index.html

Fire - https://pypi.org/project/fire/

Click - https://pypi.org/project/click/

ConfigArgparse - https://pypi.org/project/ConfigArgParse/


TODO
----

- [ ] Nested Modal CLI's

- [ ] Fuzzy hyphens in ModelCLIs

- [X] Policy on nested heirachies (currently disallowed) - jsonargparse will be the solution here.

  - [ ] How to best integrate with jsonargparse

- [ ] Policy on smartcast (currently enabled)

  - [ ] Find a way to gracefully way to make smartcast do less. (e.g. no list parsing, but int is ok, we may think about accepting YAML)

- [X] Policy on positional arguments (currently experimental) - we have implemented them permissively with one undefined corner case.

    - [X] Fixed length - nope

    - [X] Variable length

    - [X] Can argparse be modified to always allow for them to appear at the beginning or end? - Probably not.

    - [x] Can we get argparse to allow a positional arg change the value of a prefixed arg and still have a sane help menu?

- [x] Policy on boolean flags - See the ``isflag`` argument of ``scriptconfig.Value``

- [x] Improve over argparse's default autogenerated help docs (needs exploration on what is possible with argparse and where extensions are feasible)


.. |GitlabCIPipeline| image:: https://gitlab.kitware.com/utils/scriptconfig/badges/main/pipeline.svg
   :target: https://gitlab.kitware.com/utils/scriptconfig/-/jobs

.. |GitlabCICoverage| image:: https://gitlab.kitware.com/utils/scriptconfig/badges/main/coverage.svg
    :target: https://gitlab.kitware.com/utils/scriptconfig/commits/main

.. # See: https://ci.appveyor.com/project/jon.crall/scriptconfig/settings/badges
.. |Appveyor| image:: https://ci.appveyor.com/api/projects/status/br3p8lkuvol2vas4/branch/main?svg=true
   :target: https://ci.appveyor.com/project/jon.crall/scriptconfig/branch/main

.. |Codecov| image:: https://codecov.io/github/Erotemic/scriptconfig/badge.svg?branch=main&service=github
   :target: https://codecov.io/github/Erotemic/scriptconfig?branch=main

.. |Pypi| image:: https://img.shields.io/pypi/v/scriptconfig.svg
   :target: https://pypi.python.org/pypi/scriptconfig

.. |PypiDownloads| image:: https://img.shields.io/pypi/dm/scriptconfig.svg
   :target: https://pypistats.org/packages/scriptconfig

.. |ReadTheDocs| image:: https://readthedocs.org/projects/scriptconfig/badge/?version=latest
    :target: http://scriptconfig.readthedocs.io/en/latest/
