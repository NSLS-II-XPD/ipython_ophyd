from bluesky.callbacks.zmq import RemoteDispatcher
from bluesky.utils import install_qt_kicker


d = RemoteDispatcher('localhost:5578')
install_qt_kicker(loop=d.loop)  # This may need to be d._loop depending on tag

