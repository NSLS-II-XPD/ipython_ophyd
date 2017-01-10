from ophyd import (Device, PVPositioner, EpicsSignal, EpicsSignalRO)
from ophyd.mixins import EpicsSignalPositioner
from ophyd import Component as Cpt
from ophyd.device import DeviceStatus


class CS700TemperatureController(PVPositioner):
    readback = Cpt(EpicsSignalRO, 'T-I')
    setpoint = Cpt(EpicsSignal, 'T-SP')
    done = Cpt(EpicsSignalRO, 'Cmd-Busy')
    stop_signal = Cpt(EpicsSignal, 'Cmd-Cmd')
    
    def set(self, *args, timeout=None, **kwargs):
        return super().set(*args, timeout=timeout, **kwargs)

    def trigger(self):
        # There is nothing to do. Just report that we are done.
        # Note: This really should not necessary to do --
        # future changes to PVPositioner may obviate this code.
        status = DeviceStatus(self)
        status._finished()
        return status

# To allow for sample temperature equilibration time, increase
# the `settle_time` parameter (units: seconds).
cs700 = CS700TemperatureController('XF:28IDC-ES:1{Env:01}', name='cs700',
                                   settle_time=0)
cs700.done_value = 0
cs700.read_attrs = ['setpoint', 'readback']
cs700.readback.name = 'temperature'
cs700.setpoint.name = 'temperature_setpoint'


class Eurotherm(Device):
    temp = Cpt(EpicsSignalPositioner, 'T-I', write_pv='T-SP',
               tolerance=10, timeout=600)

    ramp_rate = Cpt(EpicsSignal, 'Rate:Ramp-RB', write_pv='Rate:Ramp-SP')


eurotherm = Eurotherm('XF:28IDC-ES:1{Env:04}', name='eurotherm')
