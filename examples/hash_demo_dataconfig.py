"""
This is the same example as hash_demo, but with a DataConfig instead.

If this script is in a module ``hash_demo_dataconfig.py``, it can be invoked in these
following ways.

Purely from the command line:

.. code-block:: bash

    # Get help
    python hash_demo_dataconfig.py --help

    # Using key-val pairs
    python hash_demo_dataconfig.py --fpath=$HOME/.bashrc --hasher=sha1

    # Using a positional arguments and other defaults
    python hash_demo_dataconfig.py $HOME/.bashrc

From the command line using a yaml config:

.. code-block:: bash

    # Write out a config file
    echo '{"fpath": "hashconfig.json", "hasher": "sha512"}' > hashconfig.json

    # Use the special `--config` cli arg provided by scriptconfig
    python hash_demo_dataconfig.py --config=hashconfig.json

    # You can also mix and match, this overrides the hasher in the config with sha1
    python hash_demo_dataconfig.py --config=hashconfig.json --hasher=sha1


Lastly you can call it from good ol' Python.

.. code-block:: bash

    python -c "import hash_demo_dataconfig; hash_demo_dataconfig.main(fpath=hash_demo_dataconfig.__file__, hasher='sha512')"
"""
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
