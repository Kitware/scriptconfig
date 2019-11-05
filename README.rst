ScriptConfig
============

.. # TODO Get CI services running on gitlab 
.. #|CircleCI| |Travis| |Appveyor| |Codecov| |Pypi| |Downloads| |ReadTheDocs|


Write simple configs and update from CLI, kwargs, and/or json.

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


.. |CircleCI| image:: https://circleci.com/gh/Erotemic/scriptconfig.svg?style=svg
    :target: https://circleci.com/gh/Erotemic/scriptconfig
    
.. |Travis| image:: https://img.shields.io/travis/Erotemic/scriptconfig/master.svg?label=Travis%20CI
   :target: https://travis-ci.org/Erotemic/scriptconfig?branch=master

.. |Appveyor| image:: https://ci.appveyor.com/api/projects/status/github/Erotemic/scriptconfig?branch=master&svg=True
   :target: https://ci.appveyor.com/project/Erotemic/scriptconfig/branch/master

.. |Codecov| image:: https://codecov.io/github/Erotemic/scriptconfig/badge.svg?branch=master&service=github
   :target: https://codecov.io/github/Erotemic/scriptconfig?branch=master

.. |Pypi| image:: https://img.shields.io/pypi/v/scriptconfig.svg
   :target: https://pypi.python.org/pypi/scriptconfig

.. |Downloads| image:: https://img.shields.io/pypi/dm/scriptconfig.svg
   :target: https://pypistats.org/packages/scriptconfig

.. |ReadTheDocs| image:: https://readthedocs.org/projects/scriptconfig/badge/?version=latest
    :target: http://scriptconfig.readthedocs.io/en/latest/
