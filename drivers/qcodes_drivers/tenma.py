"""
Created 2024

@author: B.J.Hensen

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2024, Hensen Lab

All rights reserved.
"""

from qcodes import VisaInstrument, validators as vals
from qcodes.utils.helpers import create_on_off_val_mapping
from qcodes.instrument.base import Instrument, InstrumentBase
from qcodes.logger.instrument_logger import get_instrument_logger
from qcodes.utils.validators import Numbers,Enum,MultiType

class TenmaPowerSupply(VisaInstrument):
    """
    This is the qcodes driver for our Tenma 72-2535 power supply
    """


    def __init__(self, name, address,max_voltage=30,max_current=3, **kwargs):
        super().__init__(name, address, terminator='\r\n', **kwargs)
        self.visa_handle.read_termination = '\n'
        self.connect_message()
        self.add_parameter(name='current_setpoint',
                         label='Sets the output current.',
                         unit='A',
                         get_cmd='ISET1?',
                         set_cmd='ISET1:{}',
                         get_parser=float,
                         vals=Numbers(min_value=0,
                                      max_value=max_current))
        self.add_parameter(name='actual_current',
                         label='Returns the actual output current.',
                         unit='A',
                         get_cmd='IOUT1?',
                         get_parser=float)
        
        self.add_parameter(name='voltage_setpoint',
                         label='Sets the output voltage.',
                         unit='V',
                         get_cmd='VSET1?',
                         set_cmd='VSET1:{}',
                         get_parser=float,
                         vals=Numbers(min_value=0,
                                      max_value=max_voltage))
        self.add_parameter(name='actual_voltage',
                         label='Returns the actual output voltage.',
                         unit='V',
                         get_cmd='VOUT1?',
                         get_parser=float)
        
        self.add_parameter('output',
                            label='Turn on/off output',
                            set_cmd='OUT{}',
                            val_mapping=create_on_off_val_mapping(on_val='1',
                                                                  off_val='0'))
        self.add_parameter('ocp',
                            label='Turn on/off over-current protection',
                            set_cmd='OCP{}',
                            val_mapping=create_on_off_val_mapping(on_val='1',
                                                                  off_val='0'))
        self.add_parameter('ovp',
                            label='Turn on/off over-voltage protection',
                            set_cmd='OVP{}',
                            val_mapping=create_on_off_val_mapping(on_val='1',
                                                                  off_val='0'))
        
    def __enter__(self):
        """ Method to allow the use of the with-as statement
        """
        return self
        
    def __exit__(self, type, value, traceback):
        """ Method to allow the use of the with-as statement
        """
        self.close()
        
    def get_status(self):
        s = self.visa_handle.query('STATUS?')
        si=ord(s)
        ch1_mode = 'CV mode' if si & 2**0 else 'CC mode'
        ch2_mode = 'CV mode' if si & 2**1 else 'CC mode'
        beep = si & 2**4 > 0
        lock = si & 2**5 > 0
        output = si & 2**6 > 0
        return dict(status_integer = si,ch1_mode=ch1_mode,ch2_mode=ch2_mode, beep=beep, lock=lock ,output=output )
    
    def output_on(self):
        self.output(True)
        
    def output_off(self):
        self.output(False)


if __name__ == '__main__':
    # with TenmaPowerSupply(name = 'tenma', address  = 'ASRL17::INSTR', ) as ten:
    #     print(ten.get_status())
    ten = TenmaPowerSupply(name = 'tenma', address  = 'ASRL17::INSTR', )
