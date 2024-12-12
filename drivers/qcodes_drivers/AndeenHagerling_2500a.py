# -*- coding: utf-8 -*-
"""
Created 2024

@author: Loek van Everdignen

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2024, Hensen Lab

All rights reserved.
"""
import re
import time
import datetime
from qcodes import VisaInstrument, validators as vals
from qcodes.utils.helpers import create_on_off_val_mapping
from qcodes.instrument.base import Instrument, InstrumentBase
from qcodes.logger.instrument_logger import get_instrument_logger
from qcodes.utils.validators import Numbers,Enum,MultiType, OnOff


class AndeenHagerling2500a(VisaInstrument):
    """
    This is the qcodes driver for Andeen-Hagerling 2500a and 2550a capacitance bridges
    """
    
    def __init__(self, name, address, timeout = 5000, **kwargs):
        super().__init__(name, address, terminator='\n', **kwargs)
        
        self.visa_handle.read_termination = '\n'

        self.connect_message()
        
        # set timeout
        self.visa_handle.timeout = timeout  
        
        
        self.add_parameter(name = 'notation',
                           label = 'determines the type of notation of returned values \n 0 = floating point, 1 = scientific, 2 = engineering',
                           set_cmd = 'FO SP {}',
                           vals=Numbers(min_value=0,
                                        max_value= 2))
                               
        self.add_parameter(name = 'cap_digits',
                           label = 'amount of significant digits measured in a capacitance measurement',
                           set_cmd = 'PL C {}',
                           vals = Numbers(min_value = 1,
                                         max_value = 9))
        
        self.add_parameter(name = 'reference_mode',
                           set_cmd = 'REF {}',
                           val_mapping = {'on': 'C SINGLE', 'off': 'HALT'},
                           vals = OnOff())
            
        self.add_parameter(name = 'cap_Reference',
                           label = 'Value of  capacitance reference in reference mode',
                           unit = 'pF',
                           set_cmd = 'REF C {}')
        
        self.add_parameter(name = 'high_voltage',
                           label = 'sets the maximum voltage used during a measurement',
                           set_cmd = 'V {}',
                           #get_cmd = self.get_param('V'),
                           vals = Numbers(min_value = 0,
                                          max_value = 15))
                           
                           
    def __enter__(self):
        """ Method to allow the use of the with-as statement
        """
        return self
        
    def __exit__(self, type, value, traceback):
        """ Method to allow the use of the with-as statement
        """
        self.close()
        
        
    def connect_message(self, begin_time: float | None = None ) -> None:
        """
        Print a message on initial connection to the ELD driver. 
        This function is adapted as the ELD driver does not support the  "IDN" command

        """
        t = time.time() - (begin_time or self._t0)
              
        #print a message
        con_msg =  f"Connected to: AH2500a in {t:.2f}s "      
        print(con_msg)

        self.log.info(f"Connected to instrument: ELD piezodriver")
        
    def get_status(self):
        rep = self.visa_handle.query('SHOW STATUS')
        print(rep)
        
        
    def parse_response(self, rep):
        """ Parse the response from a single measurement and return as floats
        """ 
        print(rep)
        cap, loss, voltage = re.findall( r'[-+]?[0-9]*\.?[0-9]+', rep)
        return float(cap), float(loss), float(voltage)                                           
                

    def single(self):
        """ Perform a single capacitance measurement and return value
        """
        #perform a single measurement
        self.visa_handle.write('SINGLE')
        time.sleep(5)
        rep = self.visa_handle.read()
    
        #extract floats from string using a regex
        cap, ___, voltage = self.parse_response(rep)
        
        #convert cap and loss to floating point number
        cap = float(cap)
        voltage = float(voltage)
        
        return cap, voltage
        
                        
    def continuous(self, N_measurements = 100000, period = 100000000, interval = 1):
        """ Perform continuous capacitance measurement for a specified amount of time
        can also run until interrupted. Interval defines the amount of time between subsequent measurements. 
        
        Also stops the measurement after N_measurements are completed
        """
        #perform a single measurement
        self.visa_handle.write(f'CONTINUOUS {interval}')
        
        timeStart = datetime.datetime.now()
        
        #define arrays for storing measured capacitance and voltage arrays
        cap_arr = []
        voltage_arr = []
        time_arr = []
        
        #set an index to 
        index = 0
        
        try:
            while index < N_measurements:
    
                rep = self.visa_handle.read()
                
                #repeat measurement if response is EXCESS NOISE

                if rep == 'EXCESS NOISE':
                    print('WARNING: AH2500a measurement contains excess  noise')
                    #wait 3 seconds before repeating measurement
                    time.sleep(5)
                    rep = self.visa_handle.read()
            
                #extract floats from string using a regex
                cap, ___, voltage = self.parse_response(rep)
                    
                
                #add the measured capacitance and voltage to array
                cap_arr.append(cap)
                voltage_arr.append(voltage)
                time_arr.append(datetime.datetime.now())
                
                
                #check if supplied period has ellapsed
                timeDif = datetime.datetime.now() - timeStart
                
                if timeDif.total_seconds() > period:
                    print(f'Measurement interrupted after {period} seconds')
                    break
                
                #increase the index by one 
                index += 1
                
            
            #stop the measurement after N measurements ar done
            self.visa_handle.write('SINGLE')
                
        except KeyboardInterrupt:
            self.visa_handle.write('SINGLE')
            print('Keyboard Interrupt by user.')

        return cap_arr, voltage_arr, time_arr

    def toggle_ref_mode(self,ref_val):
        """ Toggle capacitance reference mode on/off. Sets a new reference value if turned on
        """
        mode = self.reference_mode.get()
        
        if  mode  == 'on':
            self.reference_mode.set('off')

        elif mode == 'off':
            self.reference_mode.set('on')
            


    def get_param(self, ParamName):
        """Ask the instrument for a parameter value
        """        
        self.visa_handle.write(f'SHOW {ParamName}')
        
        rep = self.visa_handle.read()
        value = re.findall(r'[-+]?[0-9]*\.?[0-9]+', rep)
        
        return float(value[0])