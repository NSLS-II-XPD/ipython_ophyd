from bluesky.callbacks.zmq import RemoteDispatcher
from bluesky.utils import install_qt_kicker


d = RemoteDispatcher('10.28.0.202:5578')
install_qt_kicker(loop=d.loop)  # This may need to be d._loop depending on tag

