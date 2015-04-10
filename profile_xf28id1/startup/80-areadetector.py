from ophyd.controls.area_detector import (AreaDetectorFileStoreHDF5,
                                          AreaDetectorFileStoreTIFF)

shctl1 = EpicsSignal('XF:28IDC-ES:1{Det:PE1}cam1:ShutterMode', name='shctl1')
shctl2 = EpicsSignal('XF:28IDC-ES:1{Det:PE2}cam1:ShutterMode', name='shctl2')

pe1 = AreaDetectorFileStoreTIFF('XF:28IDC-ES:1{Det:PE1}', name='pe1',
                                stats=[],
                                ioc_file_path = 'G:/pe1_data',
                                file_path = '/home/xf28id1/pe1_data',
                                shutter=shctl1,
                                shutter_val=(1,0))


pe2 = AreaDetectorFileStoreTIFF('XF:28IDC-ES:1{Det:PE2}', name='pe2',
                                stats=[],
                                ioc_file_path = 'Z:/pe2_data',
                                file_path = '/home/xf28id1/pe2_data',
                                shutter=shctl2,
                                shutter_val=(1,0))

