from ophyd.controls import EpicsMotor, PVPositioner


tth = EpicsMotor('XF:28IDC-ES:1{Dif-Ax:2ThI}Mtr', name='tth')

cs700 = PVPositioner('XF:28IDC-ES:1{Env:01}T-SP',
                     readback='XF:28IDC-ES:1{Env:01}T-I',
                     put_complete=True)

