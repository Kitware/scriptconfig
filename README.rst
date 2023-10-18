ScriptConfig
============

.. # TODO Get CI services running on gitlab
.. #|CircleCI| |Travis| |Codecov| |ReadTheDocs|

|GitlabCIPipeline| |GitlabCICoverage| |Appveyor| |Pypi| |Downloads|


+------------------+--------------------------------------------------+
| Read the docs    | https://scriptconfig.readthedocs.io              |
+------------------+--------------------------------------------------+
| Gitlab (main)    | https://gitlab.kitware.com/utils/scriptconfig    |
+------------------+--------------------------------------------------+
| Github (mirror)  | https://github.com/Kitware/scriptconfig          |
+------------------+--------------------------------------------------+
| Pypi             | https://pypi.org/project/scriptconfig            |
+------------------+--------------------------------------------------+

The main webpage for this project is: https://gitlab.kitware.com/utils/scriptconfig

The goal of ``scriptconfig`` is to make it easy to be able to define a CLI by
**simply defining a dictionary**. This enables you to write simple configs and
update from CLI, kwargs, and/or json.

The ``scriptconfig`` module provides a simple way to make configurable scripts
using a combination of config files, command line arguments, and simple Python
keyword arguments.

A script config object is defined by creating a subclass of ``Config`` with a
``__default__`` dict class attribute. An instance of a custom ``Config`` object
will behave similar a dictionary, but with a few conveniences.

.. code-block:: python

    import scriptconfig as scfg

    class ExampleConfig(scfg.DataConfig):
        """
        The docstring will be the description in the CLI help
        """
        option1 = scfg.Value('default1', help='option1 help')
        option2 = scfg.Value('default2', help='option2 help')
        option3 = scfg.Value('default3', help='option3 help')

    # Use as a dictionary with defaults
    config = ExampleConfig(option1=123)
    print(config)

    # Use as a argparse CLI
    config = ExampleConfig.cli(argv=['--option2=overruled'])
    print(config)

    # Can always fallback to pure-argparse
    print(ExampleConfig().port_to_argparse())


Installation
------------

The `scriptconfig <https://pypi.org/project/scriptconfig/>`_.  package can be installed via pip:

.. code-block:: bash

    pip install scriptconfig

Example Script
--------------

Scriptconfig is used to define a flat configuration dictionary with values that
can be specified via Python keyword arguments, command line parameters, or a
yaml config file. Consider the following script that prints its config, opens a
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

From the command line using a yaml config:

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
    >>> # The `load` method can also be passed a json/yaml file/path.
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
attributes are memebers of a ``__default__`` dictionary. The ``DataConfig``
class should be favored moving forward past version 0.6.2. However,
the ``__default__`` attribute is always available if you have an existing
dictionary you want to wrap with scriptconfig.


Features
--------

- Serializes to json

- Dict-like interface. By default a ``Config`` object operates independent of config files or the command line.

- Can create command line interfaces

  - Can directly create an independent argparse object

  - Can use special command line loading using ``self.load(cmdline=True)``. This extends the basic argparse interface with:

      - Can specify options as either ``--option value`` or ``--option=value``

      - Default config options allow for "smartcasting" values like lists and paths

      - Automatically add ``--config``, ``--dumps``, and ``--dump`` CLI options
        when reading cmdline via ``load``.

- Inheritence unions configs.

- Modal configs (see scriptconfig.modal)


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

Question: How do I override the default values for a scriptconfig object using json file?

Answer:  This depends if you want to pass the path to that json file via the command line or if you have that file in memory already.  There are ways to do either. In the first case you can pass ``--config=<path-to-your-file>`` (assuming you have set the ``cmdline=True`` keyword arg when creating your config object e.g.: ``config = MyConfig(cmdline=True)``. In the second case when you create an instance of the scriptconfig object pass the ``default=<your dict>`` when creating the object: e.g. ``config = MyConfig(default=json.load(open(fpath, 'r')))``.  But the special ``--config`` ``--dump`` and ``--dumps`` CLI arg is baked into script config to make this easier.


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


.. |GitlabCIPipeline| image:: https://gitlab.kitware.com/utils/scriptconfig/badges/master/pipeline.svg
   :target: https://gitlab.kitware.com/utils/scriptconfig/-/jobs

.. |GitlabCICoverage| image:: https://gitlab.kitware.com/utils/scriptconfig/badges/master/coverage.svg?job=coverage
    :target: https://gitlab.kitware.com/utils/scriptconfig/commits/master

.. # See: https://ci.appveyor.com/project/jon.crall/scriptconfig/settings/badges
.. |Appveyor| image:: https://ci.appveyor.com/api/projects/status/br3p8lkuvol2vas4/branch/master?svg=true
   :target: https://ci.appveyor.com/project/jon.crall/scriptconfig/branch/master

.. |Codecov| image:: https://codecov.io/github/Erotemic/scriptconfig/badge.svg?branch=master&service=github
   :target: https://codecov.io/github/Erotemic/scriptconfig?branch=master

.. |Pypi| image:: https://img.shields.io/pypi/v/scriptconfig.svg
   :target: https://pypi.python.org/pypi/scriptconfig

.. |Downloads| image:: https://img.shields.io/pypi/dm/scriptconfig.svg
   :target: https://pypistats.org/packages/scriptconfig

.. |ReadTheDocs| image:: https://readthedocs.org/projects/scriptconfig/badge/?version=latest
    :target: http://scriptconfig.readthedocs.io/en/latest/
