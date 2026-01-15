import textwrap

import pytest

import scriptconfig as scfg


class SGDConfig(scfg.DataConfig):
    lr = scfg.Value(0.01, type=float)
    momentum = scfg.Value(0.9, type=float)


class AdamConfig(scfg.DataConfig):
    lr = scfg.Value(0.001, type=float)
    beta1 = scfg.Value(0.9, type=float)


class BackboneConfig(scfg.DataConfig):
    patch = scfg.Value(4, type=int)


class SegformerConfig(scfg.DataConfig):
    backbone = scfg.SubConfig(BackboneConfig, choices={'vit': BackboneConfig})
    heads = 1


class ModelConfig(scfg.DataConfig):
    name = 'base'


class TrainConfig(scfg.DataConfig):
    optim = scfg.SubConfig(AdamConfig, choices={'adam': AdamConfig, 'sgd': SGDConfig})
    model = scfg.SubConfig(ModelConfig, choices={'base': ModelConfig, 'seg': SegformerConfig})
    epochs = scfg.Value(10, type=int)


def test_flat_fastpath():
    class FlatConfig(scfg.DataConfig):
        foo = 1

    cfg = FlatConfig.cli(argv=['--foo', '3'])
    assert cfg.foo == 3
    assert not cfg._has_subconfigs


def test_nested_leaf_override_via_cli():
    cfg = TrainConfig.cli(argv=['--optim.lr=0.02'], allow_subconfig_overrides=True)
    assert cfg.optim.lr == pytest.approx(0.02)


def test_selector_via_dunder_class_and_sugar():
    cfg = TrainConfig.cli(
        argv=['--optim.__class__=sgd', '--optim.momentum=0.7'],
        allow_subconfig_overrides=True,
    )
    assert isinstance(cfg.optim, SGDConfig)
    assert cfg.optim.momentum == pytest.approx(0.7)

    cfg2 = TrainConfig.cli(argv=['--optim=sgd', '--optim.momentum=0.5'], allow_subconfig_overrides=True)
    assert isinstance(cfg2.optim, SGDConfig)
    assert cfg2.optim.momentum == pytest.approx(0.5)


def test_nested_selector_and_deep_leaves():
    cfg = TrainConfig.cli(argv=[
        '--model=seg',
        '--model.backbone=vit',
        '--model.backbone.patch=16',
    ], allow_subconfig_overrides=True)
    assert isinstance(cfg.model, SegformerConfig)
    assert isinstance(cfg.model.backbone, BackboneConfig)
    assert cfg.model.backbone.patch == 16


def test_variant_aware_help(capsys):
    with pytest.raises(SystemExit):
        TrainConfig.cli(argv=['--model=seg', '--help'], allow_subconfig_overrides=True)
    out = capsys.readouterr().out
    assert 'model.backbone.patch' in out


def test_precedence_default_file_kwargs_cli(tmp_path):
    cfg_path = tmp_path / 'train.yaml'
    cfg_text = textwrap.dedent(
        '''
        optim:
            __class__: sgd
            lr: 0.2
        epochs: 5
        '''
    )
    cfg_path.write_text(cfg_text)
    kw_overrides = {'epochs': 8}
    cli_overrides = ['--epochs=12']
    cfg = TrainConfig.cli(
        data=kw_overrides,
        argv=['--config', str(cfg_path), *cli_overrides],
        allow_subconfig_overrides=True,
    )
    assert isinstance(cfg.optim, SGDConfig)
    assert cfg.optim.lr == pytest.approx(0.2)
    assert cfg.epochs == 12


def test_unknown_key_error():
    with pytest.raises(SystemExit):
        TrainConfig.cli(argv=['--optim.unknown=1'], allow_subconfig_overrides=True)


def test_reserved_class_name_error():
    with pytest.raises(ValueError):
        class BadConfig(scfg.DataConfig):
            __default__ = {'__class__': 1}


def test_dotted_access_for_config_and_dataconfig():
    class Inner(scfg.Config):
        __default__ = {'leaf': 1}

    class Outer(scfg.Config):
        __default__ = {'inner': Inner()}

    cfg = Outer()
    cfg['inner.leaf'] = 5
    assert cfg['inner.leaf'] == 5
    assert cfg['inner']['leaf'] == 5

    class InnerDC(scfg.DataConfig):
        leaf = 1

    class OuterDC(scfg.DataConfig):
        inner = InnerDC()

    dcfg = OuterDC()
    dcfg['inner.leaf'] = 9
    assert dcfg['inner.leaf'] == 9
    assert dcfg.inner.leaf == 9


def test_dump_and_load_roundtrip(tmp_path):
    class ChoiceA(scfg.DataConfig):
        x = 1

    class ChoiceB(scfg.DataConfig):
        x = 2

    class Outer(scfg.Config):
        __default__ = {
            'inner': scfg.SubConfig(ChoiceA, choices={'a': ChoiceA, 'b': ChoiceB}),
            'root': 3,
        }

    cfg = Outer.cli(argv=['--inner=b', '--inner.x=10'], allow_subconfig_overrides=True)
    out_path = tmp_path / 'cfg.yaml'
    with open(out_path, 'w') as file:
        cfg.dump(stream=file)

    cfg2 = Outer()
    cfg2.load(out_path, cmdline=False)
    assert isinstance(cfg2['inner'], ChoiceB)
    assert cfg2['inner'].x == 10
    assert cfg2['root'] == 3


def test_subconfig_overrides_disabled(capsys):
    cfg = TrainConfig.cli(argv=['--optim.beta1=0.3'], allow_subconfig_overrides=False)
    assert cfg.optim.beta1 == pytest.approx(0.3)

    with pytest.raises(SystemExit):
        TrainConfig.cli(argv=['--optim=sgd'], allow_subconfig_overrides=False)
    err = capsys.readouterr().err
    assert 'allow_subconfig_overrides=True' in err
    with pytest.raises(SystemExit):
        TrainConfig.cli(argv=['--optim.__class__=sgd'], allow_subconfig_overrides=False)


def test_subconfig_class_in_dict():
    cfg = TrainConfig.cli(argv=[], allow_subconfig_overrides=False)
    data = cfg.to_dict()
    assert data['optim']['__class__'] == 'adam'


def test_subconfig_stacklevel_localns_resolution():
    class LocalOpt(scfg.Config):
        __default__ = {'lr': 0.2}

    class TrainLocal(scfg.Config):
        __default__ = {
            'optim': scfg.SubConfig(AdamConfig, choices={'adam': AdamConfig}),
        }

    def wrapper_cli():
        return TrainLocal.cli(
            argv=['--optim=LocalOpt'],
            allow_subconfig_overrides=True,
            stacklevel=1,
        )

    cfg = wrapper_cli()
    assert isinstance(cfg['optim'], LocalOpt)

    def wrapper_load():
        cfg = TrainLocal()
        cfg.load(
            cmdline=['--optim=LocalOpt'],
            allow_subconfig_overrides=True,
            stacklevel=1,
        )
        return cfg

    cfg2 = wrapper_load()
    assert isinstance(cfg2['optim'], LocalOpt)


def test_config_attribute_lookup_is_disallowed():
    class SimpleConfig(scfg.Config):
        __default__ = {'value': 3}

    cfg = SimpleConfig()
    with pytest.raises(AttributeError):
        _ = cfg.value


def test_subconfig_nested_class_scope_resolution():
    class Container:
        class LocalOpt(scfg.Config):
            __default__ = {'lr': 0.3}

    class ContainerTrain(scfg.Config):
        __default__ = {
            'optim': scfg.SubConfig(
                Container.LocalOpt,
                choices={'local': Container.LocalOpt},
            ),
        }

    cfg = ContainerTrain.cli(
        argv=['--optim=local'],
        allow_subconfig_overrides=True,
        stacklevel=0,
    )
    assert isinstance(cfg['optim'], Container.LocalOpt)


def test_subconfig_local_scope_resolution_in_function():
    def build_cfg():
        class LocalOpt(scfg.Config):
            __default__ = {'lr': 0.4}

        class TrainLocal(scfg.Config):
            __default__ = {
                'optim': scfg.SubConfig(
                    LocalOpt,
                    choices={'local': LocalOpt},
                ),
            }

        cfg = TrainLocal.cli(
            argv=['--optim=local'],
            allow_subconfig_overrides=True,
            stacklevel=1,
        )
        return cfg, LocalOpt

    cfg, local_cls = build_cfg()
    assert isinstance(cfg['optim'], local_cls)


def test_value_wrapped_config_upgrades_to_subconfig():
    class InnerConfig(scfg.Config):
        __default__ = {'x': 1}

    class InnerDataConfig(scfg.DataConfig):
        x = 2

    class OuterConfig(scfg.Config):
        __default__ = {
            'inner_cfg': scfg.Value(InnerConfig()),
            'inner_dc': scfg.Value(InnerDataConfig()),
        }

    cfg = OuterConfig()
    assert cfg._has_subconfigs
    assert isinstance(cfg._subconfig_meta['inner_cfg'], scfg.SubConfig)
    assert isinstance(cfg._subconfig_meta['inner_dc'], scfg.SubConfig)
    assert isinstance(cfg['inner_cfg'], InnerConfig)
    assert isinstance(cfg['inner_dc'], InnerDataConfig)


def test_dataconfig_class_default_selector_by_classname():
    class OptimizerConfig(scfg.DataConfig):
        lr = 1e-3

    class Adam(OptimizerConfig):
        beta1 = 0.9

    class Sgd(OptimizerConfig):
        momentum = 0.9

    class TrainCfg(scfg.DataConfig):
        optim = Adam
        epochs = scfg.Value(10, type=int)

    cfg = TrainCfg.cli(
        argv='--optim=Sgd --optim.momentum=0.8 --epochs=20',
        allow_subconfig_overrides=True,
    )
    assert isinstance(cfg._subconfig_meta['optim'], scfg.SubConfig)
    assert isinstance(cfg.optim, Sgd)
    assert cfg.optim.momentum == pytest.approx(0.8)
    assert cfg.epochs == 20


def test_dataconfig_value_wrapped_subconfig():
    class OptimizerConfig(scfg.DataConfig):
        lr = 1e-3

    class Adam(OptimizerConfig):
        beta1 = 0.9

    class TrainCfg(scfg.DataConfig):
        optim = scfg.Value(Adam)

    cfg = TrainCfg()
    assert isinstance(cfg._subconfig_meta['optim'], scfg.SubConfig)
    assert isinstance(cfg.optim, Adam)


def test_subconfig_config_string_cases():
    class OptimizerConfig(scfg.DataConfig):
        lr = scfg.Value(0.01, type=float)

    class SGDLocal(OptimizerConfig):
        momentum = scfg.Value(0.9, type=float)

    class AdamLocal(OptimizerConfig):
        beta1 = scfg.Value(0.9, type=float)

    class TrainLocal(scfg.DataConfig):
        optim = scfg.SubConfig(SGDLocal, choices={'adam': AdamLocal, 'sgd': SGDLocal})
        model = scfg.Value('vit', choices=['vit', 'resnet50'])
        epochs = scfg.Value(10, type=int)

    cases = [
        {'argv': '--config "{model: resnet50, optim.momentum: 0.88}"', 'optim': SGDLocal},
        {'argv': '--config "{model: resnet50, optim: {momentum: 0.88}}"', 'optim': SGDLocal},
        {'argv': '--config "{model: resnet50, optim: adam, optim.beta1: 0.88}"', 'optim': AdamLocal},
        {'argv': '--config "{model: resnet50, optim.__class__: adam, optim.beta1: 0.88}"', 'optim': AdamLocal},
        {'argv': '--config "{model: resnet50, optim: {__class__: adam, beta1: 0.88}}"', 'optim': AdamLocal},
    ]

    for case in cases:
        cfg = TrainLocal.cli(argv=case['argv'], allow_import=True, allow_subconfig_overrides=True)
        assert cfg.model == 'resnet50'
        assert isinstance(cfg.optim, case['optim'])
        if isinstance(cfg.optim, SGDLocal):
            assert cfg.optim.momentum == pytest.approx(0.88)
        else:
            assert cfg.optim.beta1 == pytest.approx(0.88)


def test_subconfig_class_identifier_module_path():
    class Inner(scfg.Config):
        __default__ = {'x': 1}

    class Outer(scfg.Config):
        __default__ = {'inner': scfg.SubConfig(Inner)}

    cfg = Outer()
    data = cfg.to_dict()
    assert data['inner']['__class__'] == f'{Inner.__module__}.{Inner.__name__}'
