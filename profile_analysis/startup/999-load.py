import os
import sys

# expected code
# 0 -> beamline
# 1 -> test
# 2 -> simulation
os.environ['XPDAN_SETUP'] = str(0)

# setup glbl
from xpdan.glbl import an_glbl
from xpdan.data_reduction import *

db = an_glbl.exp_db # alias


# patch to separate xpdan and xpdacq
class AnMD:
    pass
try:
    f = open(os.path.join(an_glbl.yaml_dir,
                          'bt_bt.yml'))
    an_dict = yaml.load(f)
    an = AnMD()
    an.md = an_dict
except:
    pass
