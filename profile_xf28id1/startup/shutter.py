from __future__ import print_function

import logging

from ophyd.controls import EpicsSignal
from ophyd.controls.signal import SignalGroup


class Shutter(SignalGroup):
    '''Base class for shutters or valves'''

    def __init__(self, *args, **kwargs):
        super(Shutter, self).__init__(*args, **kwargs)

    def open(self):
        pass

    def close(close):
        pass


class Nsls2Shutter(Shutter):
    def __init__(self, open=None, open_status=None,
                 close=None, close_status=None):
       Shutter.__init__(self)
       signals = [EpicsSignal(open_status, write_pv=open, alias='_open'),
                  EpicsSignal(close_status, write_pv=close, alias='_close'),
                  ] 

       for sig in signals:
           self.add_signal(sig)

    @property
    def open(self):
        return self._open.value == 0

    @open.setter
    def open(self, val):
        self._open.value = val

    @property
    def close(self):
        return self._close.value == 0

    @close.setter
    def close(self, val):
        self._close.value = val


sh1 = Nsls2Shutter(open='XF:28IDC-ES:1{Sh:Exp}Cmd:Opn-Cmd',
                    open_status='XF:28IDC-ES:1{Sh:Exp}Sw:Opn1-Sts',
                    close='XF:28IDC-ES:1{Sh:Exp}Cmd:Cls-Cmd',
                    close_status='XF:28IDC-ES:1{Sh:Exp}Sw:Cls1-Sts')

