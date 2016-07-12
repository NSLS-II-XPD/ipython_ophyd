import time
import os
import numpy as np
from bluesky.plans import (scan, subs_wrapper, abs_set, pchain,
                           reset_positions_wrapper, count, list_scan,
                           open_run, close_run, stage, unstage,
                           trigger_and_read, checkpoint, sleep)
from bluesky.callbacks.broker import post_run, LiveTiffExporter
from bluesky.callbacks import LiveTable, LivePlot
from bluesky.plan_tools import print_summary
from uuid import uuid4

d_spacings = np.loadtxt(os.path.join(
    '/nfs/xf28id1/ipython_ophyd/profile_collection/startup/../../data/LaB6_d.txt'))

def ramp_from_temp_and_time(temp, time):
    ramp = np.abs(temp - eurotherm.get())/time
    if ramp > 5.:
        raise ValueError("Ramp greater than the eurotherm's temp rate")
    return ramp

def Ecal(start=-4, stop=-1.5, step_size=0.01):
    """
    Energy calibration scan

    Example
    -------

    Execute an energy calibration scan with default steps.
    >>> RE(Ecal())
    """
    plan = scan([sc], tth_cal, start, stop, (stop - start) / step_size)
    # plan = pchain(abs_set(x_cal, 0), abs_set(y_cal, 0), plan) 
    # plan = reset_positions_wrapper(plan)

    # Send data documnets to cw, LiveTable, LivePlot.
    cw = ComputeWavelength('tth_cal', 'sc_chan1', d_spacings)
    subs = [cw, LiveTable(['tth_cal', 'sc_chan1']),
            LivePlot('sc_chan1', 'tth_cal')]
    plan = subs_wrapper(plan, subs)

    yield from plan


def timed_count(detectors, total_time, *, md=None, sleep_time=None):
    if md is None:
        md = {}
    md = ChainMap(
        md,
        {'detectors': [det.name for det in detectors],
         'total_time': total_time,
         'plan_args': {'detectors': list(map(repr, detectors)),
                       'total_time': total_time},
         'plan_name': 'timed_count'})

    for det in detectors:
        yield from stage(det)
    yield from open_run(md=md)

    end_time = total_time + time.time()

    yield from timed_count_guts(detectors, total_time, md=md,
                                sleep_time=sleep_time)

    for det in detectors:
        yield from unstage(det)
    yield from close_run()


def timed_count_guts(detectors, total_time, *, md=None, sleep_time=None):
    end_time = total_time + time.time()
    while True:
        if time.time() > end_time:
            break
        yield from checkpoint()
        yield from trigger_and_read(detectors)
        if sleep_time is not None:
            yield from sleep(sleep_time)


def MED(gasses, minT, maxT, num_steps, cycle_time):
    """
    Modulated Excitation Diffraction plan

    1. Start flowing the initial gas.
    2. Scan the temperature from minT to maxT in `num_steps` evenly-spaced steps.
    3. Hold temperature at maxT and take  `num_steady` images.
    4. Switch the gas, still holding at maxT and take `num_steady` images.
    5. Repeat.

    Parameters
    ----------
    gasses : list
        e.g., ['N', Ar']
        These gasses must be in `gas.gas_list` but they may be in any order.
    minT : number
        minimum temp in whatever units the temp controller uses
    maxT : number
        minimum temp in whatever units the temp controller uses
    num_steps : integer
        number of points to sample between minT and maxT inclusive
    cycle_time : number
        time per gas cycle to take a time series; units are seconds

    Example
    -------
    Set the gasses. They can be in any other, nothing to do with
    the order they are used in the plan.
    >>> gas.gas_list = ['O2', 'CO2']

    Optionally, preview the plan.
    >>> print_summary(MED(["N", "Ar"], 30, 50, 3, 10))

    Execute it.
    >>> RE(MED(["N", "Ar"], 30, 50, 3, 10))
    """
    eurotherm = cs700

    template = "/home/xf28id1/xpdUser/med_tiffs/{start.scan_id}_{event.seq_num:04d}.tiff"
    exporter = LiveTiffExporter('pe1_image', template)
    export_at_end = post_run(exporter)

    # These are commented out that the pe1c can be configured interactively.
    # pe1c.images_per_set.put(1)
    # pe1c.number_of_sets.put(1)

    dets = [pe1c, rga, gas.current_gas, eurotherm]
    # Step 1
    yield from abs_set(gas, gasses[0])
    # Steps 2

    # optional darkframe -- for emergencies :-)
    # yield from abs_set(shctl1, 0)
    # yield from count(dets, md={'role': 'dark'})
    # yield from abs_set(shctl1, 1)

    yield from subs_wrapper(scan(dets, eurotherm, minT, maxT, num_steps),
                            [LiveTable(dets), export_at_end])
    # Alternate between gasses forever.
    for gas_name in itertools.cycle(gasses):
        yield from abs_set(gas, gas_name)
        yield from subs_wrapper(timed_count(dets, total_time=cycle_time),
                                [LiveTable(dets), export_at_end])


def temp_gas_run(gasses, Tlist, time_list, calibration_uid, background_uid,
                 is_background, md=None):
    """
    Modulated Excitation Diffraction plan

    1. Start flowing the initial gas.
    2. Scan the temperature from minT to maxT in `num_steps` evenly-spaced steps.
    3. Hold temperature at maxT and take  `num_steady` images.
    4. Switch the gas, still holding at maxT and take `num_steady` images.
    5. Repeat.

    Parameters
    ----------
    gasses : list
        e.g., ['N', Ar']
        These gasses must be in `gas.gas_list` but they may be in any order.
    minT : number
        minimum temp in whatever units the temp controller uses
    maxT : number
        minimum temp in whatever units the temp controller uses
    num_steps : integer
        number of points to sample between minT and maxT inclusive
    cycle_time : number
        time per gas cycle to take a time series; units are seconds

    Example
    -------
    Set the gasses. They can be in any other, nothing to do with
    the order they are used in the plan.
    >>> gas.gas_list = ['O2', 'CO2']

    Optionally, preview the plan.
    >>> print_summary(MED(["N", "Ar"], 30, 50, 3, 10))

    Execute it.
    >>> RE(MED(["N", "Ar"], 30, 50, 3, 10))
    """

    cal_bg_asoc = {'is_calibration': False,
                   'calibration_uid': calibration_uid,
                   'is_background': is_background,
                   'background_uid': background_uid}

    template = "/home/xf28id1/xpdUser/tiff_base/{start.scan_id}_{event.seq_num:04d}_{eurotherm.get()}.tiff"
    exporter = LiveTiffExporter('pe1_image', template)
    export_at_end = post_run(exporter)

    # These are commented out that the pe1c can be configured interactively.
    # yield from abs_set(glbl.frame_acq_time, .1)
    # yield from abs_set(pe1c.images_per_set, 1)
    # yield from abs_set(pe1c.number_of_sets, 1)

    dets = [pe1c, gas.current_gas, eurotherm]
    # optional darkframe -- for emergencies :-)
    print('taking dark')
    dark_uid = str(uuid4())
    yield from abs_set(shctl1, 0)
    yield from count(dets, md={'role': 'dark', 'dark_uid':dark_uid})
    yield from abs_set(shctl1, 1)
    if md is None:
        md = {}
    md = ChainMap(
        md,
        {'detectors': [det.name for det in dets],
         'time_list': time_list,
         'temp_list': Tlist,
         'plan_args': {'detectors': list(map(repr, dets)),
                       'time_list': time_list},
         'plan_name': 'temp_gas_run'},
        cal_bg_asoc,
        {'dark_uid':dark_uid, 'role':'light'}
    )

    def inner():
        # Step 1
        # setup detector
        for det in dets:
            yield from stage(det)
        open_rtn = (yield from open_run(md=md))
        yield from abs_set(gas, gasses[0])
        # Steps 2

        # Go to temperature, taking images all the way

        # Set ramprate in C/s

        # Set the temperature, we now start ramping.
        # Note:the rate is calculated from the set temps and times
        yield from abs_set(euro_ramp_rate, np.abs(Tlist[0] - eurotherm.get())/time_list[0], wait=False)
        yield from abs_set(eurotherm, Tlist[0], wait=False)
        print('ramp_rate', euro_ramp_rate.get())

        # Run shots until we hit the time specified
        yield from timed_count_guts(dets, total_time=time_list[0],
                                    md=cal_bg_asoc)

        # Hold the temperature, still taking shots
        yield from timed_count_guts(dets, total_time=time_list[1],
                                    md=cal_bg_asoc)

        # ramp to rt
        yield from abs_set(euro_ramp_rate, np.abs(Tlist[1] - eurotherm.get())/time_list[-1], wait=False)
        yield from abs_set(eurotherm, Tlist[1], wait=False)
        print('ramp_rate', euro_ramp_rate.get())

        # Switch gas
        yield from abs_set(gas, gasses[1])

        # Now cool , taking images all the way
        yield from timed_count_guts(dets, total_time=time_list[2],
                                    md=cal_bg_asoc)

        yield from abs_set(gas, gasses[0])
        yield from abs_set(shctl1, 0)
        for det in dets:
            yield from unstage(det)
        yield from close_run()
        return open_rtn

    return (yield from subs_wrapper(inner(), [LiveTable(dets), export_at_end]))

def bkground_temp_gas_run(Tlist, time_list, calibration_uid, background_uid,
    is_background=True, md = None):
    """
    Modulated Excitation Diffraction plan

    1. Start flowing the initial gas.
    2. Scan the temperature from minT to maxT in `num_steps` evenly-spaced steps.
    3. Hold temperature at maxT and take  `num_steady` images.
    4. Switch the gas, still holding at maxT and take `num_steady` images.
    5. Repeat.

    Parameters
    ----------
    gasses : list
        e.g., ['N', Ar']
        These gasses must be in `gas.gas_list` but they may be in any order.
    minT : number
        minimum temp in whatever units the temp controller uses
    maxT : number
        minimum temp in whatever units the temp controller uses
    num_steps : integer
        number of points to sample between minT and maxT inclusive
    cycle_time : number
        time per gas cycle to take a time series; units are seconds

    Example
    -------
    Set the gasses. They can be in any other, nothing to do with
    the order they are used in the plan.
    >>> gas.gas_list = ['O2', 'CO2']

    Optionally, preview the plan.
    >>> print_summary(MED(["N", "Ar"], 30, 50, 3, 10))

    Execute it.
    >>> RE(MED(["N", "Ar"], 30, 50, 3, 10))
    """

    cal_bg_asoc = {'is_calibration': False,
    'calibration_uid': calibration_uid,
    'is_background': is_background,
    'background_uid': background_uid}

    template = "/home/xf28id1/xpdUser/tiff_base/{start.scan_id}_{event.seq_num:04d}_{eurotherm.get()}.tiff"
    exporter = LiveTiffExporter('pe1_image', template)
    export_at_end = post_run(exporter)

    # These are commented out that the pe1c can be configured interactively.
    # yield from abs_set(glbl.frame_acq_time, .1)
    # yield from abs_set(pe1c.images_per_set, 1)
    # yield from abs_set(pe1c.number_of_sets, 1)

    dets = [pe1c, eurotherm]
    # optional darkframe -- for emergencies :-)
    print('taking dark')
    dark_uid = str(uuid4())
    yield from abs_set(shctl1, 0)
    yield from count(dets, md={'role': 'dark', 'dark_uid': dark_uid})
    yield from abs_set(shctl1, 1)
    if md is None:
        md = {}
    md = ChainMap(md,
    {'detectors': [det.name for det in dets],
     'time_list': time_list,
     'temp_list': Tlist,
     'plan_args': {'detectors': list(map(repr, dets)),
                   'time_list': time_list},
     'plan_name': 'temp_gas_run'},
    cal_bg_asoc,
    {'dark_uid': dark_uid, 'role': 'light'}
    )

    def inner():
        # Step 1
        # setup detector
        for det in dets:
            yield from stage(det)
        open_rtn = (yield from open_run(md=md))
        # Steps 2

        # Go to temperature, taking images all the way

        # Set ramprate in C/s

        # Set the temperature, we now start ramping.
        # Note:the rate is calculated from the set temps and times
        yield from abs_set(euro_ramp_rate, np.abs(Tlist[0] - eurotherm.get()) / time_list[0], wait=False)
        yield from abs_set(eurotherm, Tlist[0], wait=False)
        print('ramp_rate', euro_ramp_rate.get())

        # Run shots until we hit the time specified
        yield from timed_count_guts(dets, total_time=time_list[0],
                                    md=cal_bg_asoc)

        # Hold the temperature, still taking shots
        yield from timed_count_guts(dets, total_time=time_list[1],
                                    md=cal_bg_asoc)

        # ramp to rt
        yield from abs_set(euro_ramp_rate, np.abs(Tlist[1] - eurotherm.get()) / time_list[-1], wait=False)
        yield from abs_set(eurotherm, Tlist[1], wait=False)
        print('ramp_rate', euro_ramp_rate.get())

        # Switch gas

        # Now cool , taking images all the way
        yield from timed_count_guts(dets, total_time=time_list[2],
                                    md=cal_bg_asoc)

        yield from abs_set(shctl1, 0)
        for det in dets:
            yield from unstage(det)
        yield from close_run()
        return open_rtn


    return (yield from subs_wrapper(inner(), [LiveTable(dets), export_at_end]))


def single_shot(is_calibration, calibration_uid, is_background, background_uid, md=None):
    template = "/home/xf28id1/xpdUser/tiff_base/{start.scan_id}_{event.seq_num:04d}.tiff"
    exporter = LiveTiffExporter('pe1_image', template)
    export_at_end = post_run(exporter)

    # These are commented out that the pe1c can be configured interactively.
    # yield from abs_set(glbl.frame_acq_time, .1)
    # yield from abs_set(pe1c.images_per_set, 1)
    # yield from abs_set(pe1c.number_of_sets, 1)

    cal_bg_asoc = {'is_calibration': is_calibration,
                   'calibration_uid': calibration_uid,
                   'is_background': is_background,
                   'background_uid': background_uid}
    dets = [pe1c]
    # optional darkframe -- for emergencies :-)
    print('taking dark')
    dark_uid = str(uuid4())
    if md is None:
        md = {}
    md = ChainMap(md,
                  {'detectors': [det.name for det in dets],
                   'plan_args': {'detectors': list(map(repr, dets)),},
                   'plan_name': 'temp_gas_run'},
                  cal_bg_asoc,
                  {'dark_uid': dark_uid, 'role': 'light'}
                  )
    yield from abs_set(shctl1, 0)
    dark_md = md.copy()
    dark_md.update({'role': 'dark', 'dark_uid': dark_uid})
    yield from count(dets, md=dark_md)
    yield from abs_set(shctl1, 1)

    light_md = md.copy()
    light_md.update({'role': 'light', 'dark_uid': dark_uid})
    yield from count(dets, md=light_md)
    yield from abs_set(shctl1, 0)
