from ophyd.controls import EpicsMotor


slt_mb2_xg = EpicsMotor('XF:28IDC-OP:1{Slt:MB2-Ax:XGap}Mtr', name='slt_mb2_xg')
slt_mb2_xc = EpicsMotor('XF:28IDC-OP:1{Slt:MB2-Ax:XCtr}Mtr', name='slt_mb2_xc')
slt_mb2_yg = EpicsMotor('XF:28IDC-OP:1{Slt:MB2-Ax:YGap}Mtr', name='slt_mb2_yg')
slt_mb2_yc = EpicsMotor('XF:28IDC-OP:1{Slt:MB2-Ax:YCtr}Mtr', name='slt_mb2_yc')

slt_mb2_t = EpicsMotor('XF:28IDC-OP:1{Slt:MB2-Ax:T}Mtr', name='slt_mb2_t')
slt_mb2_b = EpicsMotor('XF:28IDC-OP:1{Slt:MB2-Ax:B}Mtr', name='slt_mb2_b')
slt_mb2_i = EpicsMotor('XF:28IDC-OP:1{Slt:MB2-Ax:I}Mtr', name='slt_mb2_i')
slt_mb2_o = EpicsMotor('XF:28IDC-OP:1{Slt:MB2-Ax:O}Mtr', name='slt_mb2_o')
