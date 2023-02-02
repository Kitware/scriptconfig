"""
If this script is in a module ``hash_demo.py``, it can be invoked in these
following ways.

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

.. code-block:: bash

    python -c "import hash_demo; hash_demo.main(fpath=hash_demo.__file__, hasher='sha512')"
"""
import scriptconfig as scfg
import hashlib
import ubelt as ub


class FileHashConfig(scfg.Config):
    """
    The docstring will be the description in the CLI help
    """
    default = {
        'fpath': scfg.Value(None, position=1, help=ub.paragraph(
            '''
            a path to a file to hash
            ''')),
        'hasher': scfg.Value('sha1', choices=['sha1', 'sha512'], help=ub.paragraph(
            '''
            a name of a hashlib hasher
            ''')),
    }


def main(**kwargs):
    config = FileHashConfig(default=kwargs, cmdline=True)
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
