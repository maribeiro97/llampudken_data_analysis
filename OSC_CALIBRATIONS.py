OSCS = {
    'dpo4104': {
        'channels': ['dR1', 'ICCD QE', 'Laser 1.0[J]', 'ICCD andor'],
        'axes_labels': ['Time [s]', 'Voltage [V]'],
        'times': [56.8, 84.5, 66.5, 95.5]
    },
    'dpo5054':{
        'channels': [
            'Line Switch Norte Óptico',
            'Line Switch Sur Óptico',
            'Pin 1 Norte',
            'Pin 1 Sur'
        ],
        'axes_labels': ['Time [s]', 'Voltage [V]'],
        'times': [0.0, 0.0, 387.0, 388.0]
    },
    'tds684b':{
        'channels': [
            'Clock',
            'Corriente Inyector',
            'BD Pin',
            'Laser 1 Trigger'
        ],
        'axes_labels': ['Time [s]', 'Voltage [V]'],
        'times': [0.0, 83.5, 184.0, 0.0],
    },
    'tds3054':{
        'channels': ['Pin 3 Norte', 'Pin 3 Sur', 'LGT Light', 'Trigger P400'],
        'axes_labels': ['Time [s]', 'Voltage [V]'],
    },
    'tds5054':{
        'channels': ['dR2', 'dVtln', 'dVtlc', 'dVtls'],
        'axes_labels': ['Time [s]', 'Voltage [V]'],
        'times': [57.0, 62.0, 60.0, 62.0]
    },
    'tds5104':{
        'channels': ['dR3', 'V Norte Eléctrico', 'V Sur Eléctrico', 'PCD 12.5μm Ti'],
        'axes_labels': ['Time [s]', 'Voltage [V]'],
        'times': [61.0, 101.6, 101.0, 63.0]
    },
    'tds7104':{
        'channels': [
            'Rogowski Principal, Factor 0.5',
            'Rogowski Principal Integrada, Factor 0.5, 1494 [kA/(mVns)]',
            'AXUV 2 25um Be',
            'MCP 1'
        ],
        'axes_labels': ['Time [s]', 'Voltage [V]'],
        'calibration_factors': [1.0, 1400.0 * 2, 1.0, 1.0],
        'times': [69.5, 71.0, 61.0, 67.5]
    },
}