import os
if os.environ.get('DISPLAY', 0):
    from matplotlib.pyplot import *

from uiophyd.tiffsaver import TiffSaver
from uiophyd.brokerutils import blank_events
from uiophyd.brokerutils import ui_imagearray, ui_nonzerofraction

# create a default TiffSaver object ts:
ts = TiffSaver()
