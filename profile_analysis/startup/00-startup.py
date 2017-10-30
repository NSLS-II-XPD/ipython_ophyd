# Set up a Broker.
from databroker import Broker
import copy
db = Broker.named('xpd')
db.prepare_hook = lambda x, y: copy.deepcopy(y)

import subprocess


def show_env():
    # this is not guaranteed to work as you can start IPython without hacking
    # the path via activate
    proc = subprocess.Popen(["conda", "list"], stdout=subprocess.PIPE)
    out, err = proc.communicate()
    a = out.decode('utf-8')
    b = a.split('\n')
    print(b[0].split('/')[-1][:-1])
