"""
Is it significantly slower / faster to use scriptconfig than some other similar
method?


Current Observations Conclusions:

    * It is 40x faster to define a scriptconfig DataConfig than a dataclass

    * It is 20x slower to create a DataConfig instance than a dataclass instance

    * It is 5x slower to access a DataConfig attribute than a dataclass attribute
"""
import scriptconfig as scfg
from dataclasses import dataclass


def define_dataconfig_v1():
    class MyDataconfig(scfg.DataConfig):
        thresh = 0.0
        morph_kernel = 3
        key = 'salient'
        bg_key = None
        time_thresh = 1
        response_thresh = None
        use_boundaries = False
        norm_ord = 1
        agg_fn = 'probs'
        moving_window_size = None
        min_area_square_meters = None
        max_area_square_meters = None
        max_area_behavior = 'drop'
        thresh_hysteresis = None
        polygon_simplify_tolerance = None
        resolution = None
        inner_window_size = None
        inner_agg_fn = None
        poly_merge_method = None
    return MyDataconfig


def define_dataconfig_v2():
    class MyDataconfig(scfg.DataConfig):
        thresh = scfg.Value(0.0)
        morph_kernel = scfg.Value(3)
        key = scfg.Value('salient')
        bg_key = scfg.Value(None)
        time_thresh = scfg.Value(1)
        response_thresh = scfg.Value(None)
        use_boundaries = scfg.Value(False)
        norm_ord = scfg.Value(1)
        agg_fn = scfg.Value('probs')
        moving_window_size = scfg.Value(None)
        min_area_square_meters = scfg.Value(None)
        max_area_square_meters = scfg.Value(None)
        max_area_behavior = scfg.Value('drop')
        thresh_hysteresis = scfg.Value(None)
        polygon_simplify_tolerance = scfg.Value(None)
        resolution = scfg.Value(None)
        inner_window_size = scfg.Value(None)
        inner_agg_fn = scfg.Value(None)
        poly_merge_method = scfg.Value(None)
    return MyDataconfig


def define_dataclass():
    @dataclass
    class MyDataclass:
        thresh: object = 0.0
        morph_kernel: object = 3
        key: object = 'salient'
        bg_key: object = None
        time_thresh: object = 1
        response_thresh: object = None
        use_boundaries: object = False
        norm_ord: object = 1
        agg_fn: object = 'probs'
        moving_window_size: object = None
        min_area_square_meters: object = None
        max_area_square_meters: object = None
        max_area_behavior: object = 'drop'
        thresh_hysteresis: object = None
        polygon_simplify_tolerance: object = None
        resolution: object = None
        inner_window_size: object = None
        inner_agg_fn: object = None
        poly_merge_method: object = None
    return MyDataclass


def main():
    import timerit
    import pandas as pd
    import rich

    define_ti = timerit.Timerit(100, bestof=10, verbose=2)
    create_ti = timerit.Timerit(100, bestof=10, verbose=2)
    access_ti = timerit.Timerit(100, bestof=10, verbose=2)

    ##
    # Time class definition

    for timer in define_ti.reset('define_scriptconfig v1'):
        with timer:
            DataconfigV1 = define_dataconfig_v1()

    for timer in define_ti.reset('define_scriptconfig v2'):
        with timer:
            DataconfigV2 = define_dataconfig_v2()

    for timer in define_ti.reset('define_dataclass'):
        with timer:
            Dataclass = define_dataclass()

    ##
    # Time instance creation

    for timer in create_ti.reset('define_scriptconfig v1'):
        with timer:
            config_v1 = DataconfigV1()

    for timer in create_ti.reset('define_scriptconfig v2'):
        with timer:
            config_v2 = DataconfigV2()

    for timer in create_ti.reset('define_dataclass'):
        with timer:
            dclsinst = Dataclass()

    ##
    # Time attribute access

    for timer in access_ti.reset('access dataconfig v1'):
        with timer:
            config_v1.agg_fn

    for timer in access_ti.reset('access dataconfig v2'):
        with timer:
            config_v2.agg_fn

    for timer in access_ti.reset('access dataclass'):
        with timer:
            dclsinst.agg_fn

    define_times = pd.DataFrame(define_ti.measures)
    create_times = pd.DataFrame(create_ti.measures)
    access_times = pd.DataFrame(access_ti.measures)

    print('Absolute Times')
    print('Define:')
    rich.print(define_times.to_string())
    print('Create:')
    rich.print(create_times.to_string())
    print('Access:')
    rich.print(access_times.to_string())

    print('Relative Times')
    print('Define:')
    rich.print(define_times / define_times.min())
    print('Create:')
    rich.print(create_times / create_times.min())
    print('Access:')
    rich.print(access_times / access_times.min())


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/scriptconfig/dev/bench/bench_dataconfig_versus_alternatives.py
    """
    main()
