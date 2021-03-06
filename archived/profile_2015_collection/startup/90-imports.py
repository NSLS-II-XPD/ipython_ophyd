#!/usr/bin/env python

from dataportal import DataBroker as db, get_events, get_table, get_images


from uiophyd.tiffsaver import TiffSaver
from uiophyd.brokerutils import blank_events
from uiophyd.brokerutils import ui_imagearray, ui_nonzerofraction

# create a default TiffSaver object ts:
ts = TiffSaver()

# Import pyplot after the dataportal implied in brokerutils.
import os
if os.environ.get('DISPLAY', 0):
    from matplotlib.pyplot import *
