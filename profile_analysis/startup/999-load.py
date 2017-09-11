import os
from shed.event_streams import istar

# expected code
# 0 -> beamline
# 1 -> test
# 2 -> simulation
os.environ['XPDAN_SETUP'] = str(0)

# setup glbl
from xpdan.glbl import an_glbl
from xpdan.pipelines.main import conf_main_pipeline

an_glbl['exp_db'] = db  # alias

s = conf_main_pipeline(db, an_glbl['tiff_base'],
                       calibration_md_folder=an_glbl['config_base'],
                       write_to_disk=True,
                       vis=True,
                       verbose=False, pdf_kwargs={'Qmax':25})

d.subscribe(istar(s.emit))

d.start()
