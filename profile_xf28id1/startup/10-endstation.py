from ophyd.controls import EpicsMotor, PVPositioner
from ophyd.controls.positioner import MoveStatus,Positioner


class NullPositioner(Positioner):

    def __init__(self, name=None):
        Positioner.__init__(self)
        self._egu = 'a.u.'
        self._position = 0

    def move(self, position, wait=False,
              moved_cb=None, timeout=30.0):

        self._position = position
        status = MoveStatus(self, position, done=True)
        self.subscribe(status._finished,
                       event_type=self._SUB_REQ_DONE, run=True)

        return status

tth = EpicsMotor('XF:28IDC-ES:1{Dif-Ax:2ThI}Mtr', name='tth')

cs700 = PVPositioner('XF:28IDC-ES:1{Env:01}T-SP',
                     readback='XF:28IDC-ES:1{Env:01}T-I',
                     stop='XF:28IDC-ES:1{Env:01}Cmd-Cmd', stop_val=13,
                     put_complete=True)

nullmtr = NullPositioner(name='nullmtr')
