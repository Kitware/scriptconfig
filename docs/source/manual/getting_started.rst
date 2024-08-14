Getting Started
---------------

scriptconfig its very simple at its core. Just define a class, and then make
class variables corresponding to your arguments. It works almost exactly like a
dataclass.


.. code:: python

    class YourConfig(scriptconfig.DataConfig):
        argname1 = default1
        argname2 = default2

using ``config = YourConfig()`` creates an instance, which behaves like a
dictionary and like parsed args. I.e. you ``config.argname1`` or
``config['argname1']``

Using ``YourConfig.cli()`` does the same thing but creates a parser and overloads
the defaults based on sys.argv.

saying ``YourConfig.cli(data=kwargs)`` will set new defaults, but sys.argv will
overwrite anything that is specified on the command line

Otherwise it behaves exactly like ``YourConfig(**kwargs)``

Using ``YourConfig.cli(cmdline=False, ...)``  disables CLI parsing so you can force
it to use the exact passed parameters (very useful when you want to invoke the
CLI programatically from python, and not make an argparse object under the
hood)

The main limitation of scriptconfig over argparse is that you are forced to
always have a default and always use key/value argument pairs. I view this as a
benefit because I want a 1-to-1 mapping between calling a script via a CLI and
calling it with a kwargs configuration.

There are lots of other little things and tricks you can do, but that's the
core principle. Define a dataclass that describes your parameters and their
defaults.

The other thing of note is that it does "smart" parsing by default, which I'm
strongly reconsidering. So if you have  the above config and run prog
``--argname=1`` or prog ``--argname=foobar``  in the first case it will automatically
figure out that you want a integer 1 and in the second case you want a string
foobar.

Also ``--argname=True`` will be a boolean.
I think this level of smartness is great, but what I regret adding as a feature is 
``--argname=a,b,1,c`` will load as ``['a', 'b', 1, 'c']``, which is far too
smart. A lot of time people do have commas in their arguments and they expect
it to be a string by default.

Of course you can disable smart parsing by doing something like:


.. code:: python

    argname1 = scfg.Value('default1', type=str)

Specifying the type forces the argument into a standardized type, but the
default under the hood is actually:
``argname1 = scfg.Value('default1', type=scfg.smartcast)``
