import six
# DBA
import os
import time
import tifffile
from dataportal import StepScan as ss, DataBroker as db
import matplotlib.pyplot as plt
import traceback

def show_last():
    data = ss[-1]
    if len(data) > 1:
        raise NotImplementedError("This scan contains multiple images. "
                                  "I don't know how to handle that.")
    subtracted = data['pe1_image_lightfield'] - data['pe1_image_darkfield']
    img = subtracted.values[0]
    options = dict(cmap='gray', interpolation='nearest')
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    ax1, ax2, ax3 = axes
    ax1.imshow(data['pe1_image_lightfield'].values[0], **options)
    ax2.imshow(data['pe1_image_darkfield'].values[0], **options)
    ax3.imshow(subtracted.values[0], **options)
    ax1.set(title='light')
    ax2.set(title='dark')
    ax3.set(title='subtracted')


def show(light_id, dark_id=None):
    """Show light/dark/difference based on two scan ids
    if no dark_id is provided, it is assumed that the dark_id 
    was collected first
    """
    light = ss[light_id]['pe1_image_lightfield'][0].astype(float)
    if not dark_id:
        dark_id = light_id-1
    dark = ss[dark_id]['pe1_image_lightfield'][0].astype(float)
    _show_subtracted(light, dark)

def show_id(scan_id, subtract_dark=True):
    data = ss[scan_id]
    if len(data) > 1:
        raise NotImplementedError("This scan contains multiple images. "
                                  "I don't know how to handle that.")
    light = data['pe1_image_lightfield'][0].astype(float)
    if subtract_dark:
        try:
            dark = data['pe1_image_darkfield'][0].astype(float)
        except KeyError:
            print('No dark field found. Just showing the light field')
            dark = None
            subtract_dark = False
    if subtract_dark:
        _show_subtracted(light, dark)
    else:
        _show_image(light, 'pe1_image_lightfield')

from xray_vision.backend.mpl.cross_section_2d import CrossSection


def _show_image(light, title):
    options = dict(cmap='gray', interpolation='nearest')
    fig = plt.figure()
    cs = CrossSection(fig)
    cs.update_image(light)
#    fig, axes = plt.subplots(1, 1, figsize=(4, 4))
#    axes.imshow(light, **options)
    cs._ax_h.set_title(title)


def _show_subtracted(light, dark):
    _show_image(light,'pe1_image_lightfield' )
    _show_image(dark, 'pe1_image_darkfield')
    subtracted = light - dark 
    _show_image(subtracted, 'light - dark')

def save_tiff_temporary(light_id, filepath, fields):
    light = ss[light_id]['pe1_image_lightfield']
    dark = ss[light_id-1]['pe1_image_lightfield']
    
    _save_tiff_helper(light, dark, filepath, fields, '%d&%d' % (light_id-1,
        light_id))


def save_tiff(scan_ids, filepath, fields):
    """
    Parameters
    ----------
    scan_id : int, list
        List of scan ids you wish to output to tiffs
    filepath : str
        directory to save TIFF files in
    fields : list
        List of fields in the run header to include in the 
        file name

    Example
    -------

    >>> save_tiff(187, '~/my_folder/', ['mood', 'sample_flavor'])
    '~/my_folder/scan-187_mood-excited_sample_flavor-orange-0.tif'


    """
    try:
        iter(scan_ids)
    except TypeError:
        # scan_id is not iterable and therefore not a list
        scan_ids = [scan_ids]
    for scan_id in scan_ids:
        filepath = os.path.expanduser(filepath)
        df = ss[scan_id]
        header = db[scan_id]
        light = df['pe1_image_lightfield']
        try:
            dark = df['pe1_image_darkfield']
        except KeyError:
            print("No dark frame available for scan %d. Only outputting the light"
                "field" % scan_id)
        try:
            _save_tiff_helper(light, dark, header, filepath, fields, scan_id)
        except:
            print("There was a problem with scan %s. Traceback: " % scan_id)
            print(traceback.format_exc())


def _save_tiff_helper(light, dark, header, filepath, fields, scan_id):
    data = {'light': light, 'dark': dark, 'subtracted': light-dark} 
    full_filepaths = []
    for img_name, images in data.items():
        for i, img in enumerate(images):
            filename = "scan-%s" % scan_id
            for field in fields:
                # Look up each field in the Header.
                try:
                    value = header[field]
                except KeyError:
                    raise KeyError("The field %s was not in the Header "
                                   "for scan %d. It has fields: %s " % (field, scan_id,
                                       fields))
                filename += "_%s-%s" % (field, value)
            if img_name != 'subtracted':
                filename += "_%s" % img_name
            filename += "_%05d.tif" % i
            full_filepath = os.path.join(filepath, filename)
            print('Writing to %s' % full_filepath), 
            tifffile.imsave(full_filepath, img)
            print(' ...written')
            full_filepaths.append(full_filepath)
    return full_filepaths


#def save_jon_tiff(scan_id, filepath, fields=None):
#    if fields is None:
#        fields = [...]  # <-- your defaults here
#    return save_tiff(scan_id, filepath, fields)

def gas_macro(gas, ct, old_gas, new_gas, duration, *args, **kwargs):
    """For Jon

    gas:
        gas Ophyd object
    ct:
        ct Ophyd object
    old gas: str
        e.g., 'N2'
    new gas: str
        e.g., 'O2'
    duration: number
        seconds after gas switch to collect data

    Example
    -------
    >>> pe1.num_images = 10
    >>> pe1.darkframe_interval = 1
    >>> ct.user_detectors.extend([pe1, gas])
    >>> gas_macro('N2', 'O2', 600)
    # Additional keyword arguments will be passed on to ct()
    # such as metadata.
    >>> gas_macro('N2', 'O2', 600, my_meta_field='blah')
    """
    # Make sure we are starting for the right state.
    gas.switch(old_gas)
    while gas.requested_pos != gas.current_pos:
        time.sleep(0.5)
    # Switch to the new state.
    gas.switch(new_gas)
    while gas.requested_pos != gas.current_pos:
        time.sleep(delay)
    # The gas has switched. Take data.
    start_time = time.time()
    while time.time() < start_time + duration:
        kwargs['gasses'] = gas.lookup
        ct(*args, **kwargs)
    return

def gas_macro2(gas, ct, old_gas, new_gas, duration, *args, **kwargs):
    """For Jon

    gas:
        gas Ophyd object
    ct:
        ct Ophyd object
    old gas: str
        e.g., 'N2'
    new gas: str
        e.g., 'O2'
    duration: number
        seconds after gas switch to collect data

    Example
    -------
    >>> pe1.num_images = 10
    >>> pe1.darkframe_interval = 1
    >>> ct.user_detectors.extend([pe1, gas])
    >>> gas_macro('N2', 'O2', 600)
    # Additional keyword arguments will be passed on to ct()
    # such as metadata.
    >>> gas_macro('N2', 'O2', 600, my_meta_field='blah')
    """
    # start with first gas 
    gas.switch(old_gas)
    while gas.requested_pos != gas.current_pos:
        time.sleep(0.5)
    # Take dark image and then data
    pe1.darkframe_interval = 1
    kwargs['gasses'] = gas.lookup
    ct(*args, **kwargs)
    # Take only data for the duration of first gas on
    pe1.darkframe_interval = 0
    start_time = time.time()
    while time.time() < start_time + duration:
        kwargs['gasses'] = gas.lookup
        ct(*args, **kwargs)

    # Switch to the second gas
    gas.switch(new_gas)
    while gas.requested_pos != gas.current_pos:
        time.sleep(0.5)
    # Take dark image and then data
    pe1.darkframe_interval = 1
    kwargs['gasses'] = gas.lookup
    ct(*args, **kwargs)
    # Take only data for the duration of second gas on
    pe1.darkframe_interval = 0
    start_time = time.time()
    while time.time() < start_time + duration:
        kwargs['gasses'] = gas.lookup
        ct(*args, **kwargs)
    return

