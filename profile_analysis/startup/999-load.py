import os
import sys
from mock import MagicMock
from PyQt4 import QtGui
app = QtGui.QApplication(sys.argv)

# expected code
# 0 -> beamline
# 1 -> test
# 2 -> simulation
os.environ['XPDAN_SETUP'] = str(0)

# setup glbl
from xpdan.glbl import an_glbl
an_glbl.exp_db = db

# import functionality
from xpdan.qt_gui import XpdanSearch, an
from xpdan.data_reduction import *
from xpdan.utils import start_xpdan
an = start_xpdan()

#db = an_glbl.exp_db # alias
