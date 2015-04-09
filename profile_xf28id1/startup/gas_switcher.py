from __future__ import print_function

import logging

from ophyd.controls import EpicsSignal
from ophyd.controls.signal import SignalGroup


class GasSwitcher(SignalGroup):
    '''Base class for Gas Switcher'''

    def __init__(self, *args, **kwargs):
        super(GasSwitcher, self).__init__(*args, **kwargs)

    def current_pos(self):
        pass

    def requested_pos(self):
        pass


class XPDGasSwitcher(GasSwitcher):
    def __init__(self, requested_pos=None, current_pos=None):
       GasSwitcher.__init__(self)
       signals = [EpicsSignal(current_pos, rw=False, alias='_current_pos'),
                  EpicsSignal(requested_pos, alias='_requested_pos'),
                  ] 

       for sig in signals:
           self.add_signal(sig)

    @property
    def current_pos(self):
        return self._current_pos.value

    @property
    def requested_pos(self):
        return self._requested_pos.value

    @requested_pos.setter
    def requested_pos(self, val):
        self._requested_pos.value = val


gas1 = XPDGasSwitcher(requested_pos='XF:28IDC-ES:1{Env:02}Pos-SP',
        current_pos='XF:28IDC-ES:1{Env:02}Pos-I')
