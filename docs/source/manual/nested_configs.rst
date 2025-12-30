Nested Configs with SubConfig
=============================

Scriptconfig supports nested configuration trees via :class:`scriptconfig.SubConfig`.
This lets a config contain other Config/DataConfig nodes while still supporting
selector-based swapping and dotted CLI overrides.

Overview
--------

Use :class:`scriptconfig.SubConfig` for any nested node that can be selected or
configured independently. Leaf values remain regular ``Value`` entries or raw
defaults.

.. code:: python

    import scriptconfig as scfg


    class Adam(scfg.Config):
        __default__ = {
            'lr': 1e-3,
            'beta1': 0.9,
        }


    class Sgd(scfg.Config):
        __default__ = {
            'lr': 1e-2,
            'momentum': 0.9,
        }


    class TrainCfg(scfg.DataConfig):
        optim = scfg.SubConfig(
            Adam,
            choices={'adam': Adam, 'sgd': Sgd},
        )
        epochs = scfg.Value(10, type=int)


Selector overrides
------------------

Selectors choose the implementation for a SubConfig node. There are two forms:

* Canonical: ``--optim.__class__=sgd``
* Sugar: ``--optim=sgd`` (only when ``optim`` is a SubConfig)

The selector is applied before leaf parsing so the realized tree is correct:

.. code:: bash

    python train.py --optim=sgd --optim.momentum=0.8

Dotted leaf overrides
---------------------

Leaf values use dotted paths:

.. code:: bash

    python train.py --optim.lr=0.02 --epochs=20

In Python, you can apply the same updates by passing dotted keys via kwargs or
``data``:

.. code:: python

    cfg = TrainCfg.cli(argv=False, data={
        'optim.__class__': 'sgd',
        'optim.momentum': 0.95,
    })

Config files
------------

YAML/JSON config files support nested mappings and selector keys. The merge
order remains: defaults < config file < kwargs < CLI.

.. code:: yaml

    optim:
      __class__: sgd
      momentum: 0.88
    epochs: 12

Or using dotted keys:

.. code:: yaml

    optim.__class__: sgd
    optim.momentum: 0.88

Limitations and notes
---------------------

* ``__class__`` is reserved for SubConfig selector metadata.
* ``Config`` objects are dict-like and do not allow attribute access; use
  ``cfg['key']`` for plain ``Config`` instances.
* ``DataConfig`` supports both attribute and dict-style access.

For additional details, see the API docs for :class:`scriptconfig.SubConfig`.
