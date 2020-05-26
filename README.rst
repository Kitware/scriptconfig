ScriptConfig
============

.. # TODO Get CI services running on gitlab 
.. #|CircleCI| |Travis| |Codecov| |ReadTheDocs|

|GitlabCIPipeline| |GitlabCICoverage| |Appveyor| |Pypi| |Downloads| 

The main webpage for this project is: https://gitlab.kitware.com/utils/scriptconfig

The goal of ``scriptconfig`` is to make it easy to be able to define a CLI by
**simply defining a dictionary**. Thie enables you to write simple configs and
update from CLI, kwargs, and/or json.

The ``scriptconfig`` provides a simple way to make configurable scripts using a
combination of config files, command line arguments, and simple Python keyword
arguments. A script config object is defined by creating a subclass of
``Config`` with a ``default`` dict class attribute. An instance of a custom
``Config`` object will behave similar a dictionary, but with a few
conveniences.

To get started lets consider some example usage:

.. code-block:: python

    >>> import scriptconfig as scfg
    >>> # In its simplest incarnation, the config class specifies default values.
    >>> # For each configuration parameter.
    >>> class ExampleConfig(scfg.Config):
    >>>     default = {
    >>>         'num': 1,
    >>>         'mode': 'bar',
    >>>         'ignore': ['baz', 'biz'],
    >>>     }
    >>> # Creating an instance, starts using the defaults
    >>> config = ExampleConfig()
    >>> # Typically you will want to update default from a dict or file.  By
    >>> # specifying cmdline=True you denote that it is ok for the contents of
    >>> # `sys.argv` to override config values. Here we pass a dict to `load`.
    >>> kwargs = {'num': 2}
    >>> config.load(kwargs, cmdline=False)
    >>> assert config['num'] == 2
    >>> # The `load` method can also be passed a json/yaml file/path.
    >>> config_fpath = '/tmp/foo'
    >>> open(config_fpath, 'w').write('{"num": 3}')
    >>> config.load(config_fpath, cmdline=False)
    >>> assert config['num'] == 3
    >>> # It is possbile to load only from CLI by setting cmdline=True
    >>> # or by setting it to a custom sys.argv
    >>> config.load(cmdline=['--num=4'])
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
    >>>     default = {
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



FAQ
---

Question: How do I override the default values for a scriptconfig object using json file?

Answer:  This depends if you want to pass the path to that json file via the command line or if you have that file in memory already.  There are ways to do either. In the first case you can pass ``--config=<path-to-your-file>`` (assuming you have set the ``cmdline=True`` keyword arg when creating your config object e.g.: ``config = MyConfig(cmdline=True)``. In the second case when you create an instance of the scriptconfig object pass the ``default=<your dict>`` when creating the object: e.g. ``config = MyConfig(default=json.load(open(fpath, 'r')))``.  But the special ``--config`` ``--dump`` and ``--dumps`` CLI arg is baked into script config to make this easier.  


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
