import os

# expected code
# 0 -> beamline
# 1 -> test
# 2 -> simulation
os.environ['XPDAN_SETUP'] = str(0)

# setup glbl
from xpdan.glbl import an_glbl
from xpdan.pipelines.callback import MainCallback

an_glbl['exp_db'] = db  # alias

s = MainCallback(db, an_glbl['tiff_base'],
                 calibration_md_folder=an_glbl['config_base'],
                 write_to_disk=True,
                 vis=True)

d.subscribe(s)

d.start()
