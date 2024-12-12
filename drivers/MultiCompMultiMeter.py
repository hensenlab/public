"""
Created 2024

@author: B.J.Hensen

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2024, Hensen Lab

All rights reserved.
"""

import hid # pip install hidapi
import numpy as np

MODES = {
    0: ['ACV','Vrms'],
    2: ['DCV','V'],
    1: ['ACmV','mVrms'],
    6: ['RES',{'0':'Ohm','1':'kOhm','2':'kOhm','3':'kOhm','4':'MOhm','5':'MOhm'}],
    8: ['DIODE','V'],
    3: ['DCmV','mV'],
    7: ['Short-Circuit','Ohm'],
    9: ['CAP',{'0':'nF','1':'nF','2':'uF','3':'uF','4':'uF','6':'mF','7':'mF','8':'mF'}],
    4: ['FREQ','Hz'],
    5: ['Duty Cycle','%'],
    12: ['DCuA','uA'],
    13: ['ACuA','uArms'],
    14: ['DCmA','mA'],
    15: ['ACmA','mArms'],
    16: ['DCA','A'],
    17: ['ACA','Arms'],
    20: ['NCV',''],
    }

#Id	Type	Time	Length	Hex	Ascii	
#6	W	0.003354	65	00 06 ab cd 03 5e 01 d9 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00	.....^...........................................................	
# read single value
FUNCTIONS = dict(
                read_single = r'00 06 ab cd 03 5e 01 d9 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00', 
                select = r'00 06 ab cd 03 4c 01 c7 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00',
                manual_range = r'00 06 ab cd 03 46 01 c1 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00',
                auto_range = r'00 06 ab cd 03 47 01 c2 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00',
                rel = r'00 06 ab cd 03 48 01 c3 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00',
                hz_usb = r'00 06 ab cd 03 49 01 c4 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00',
                hold = r'00 06 ab cd 03 4a 01 c5 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00',
                light = r'00 06 ab cd 03 4b 01 c6 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00',
                max_min = r'00 06 ab cd 03 41 01 bc 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00',
                min_max_exit = r'00 06 ab cd 03 42 01 bd 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00',
                )

class MultiCompMultiMeter:
    """
    This is the qcodes driver for our MULTICOMP MP730561 multimeter with optical to usb converter cable D-09A.
    
    Usefull tip: To disable the auto-off function, press and hold the SELECT buttingh in the off state, and then turn on the meter.
    
    """


    def __init__(self, name, vendor_id=6790, product_id=58409, **kwargs):
        #super().__init__(name, **kwargs)
        
        # -*- coding: utf-8 -*-
        """
        Created on Fri Nov 22 15:40:01 2024

        @author: lion
        """
        self.name = name
        self.dev = hid.device()
        
        self.dev.open(vendor_id,product_id)
        
        self.timeout_ms = 1000
        self.bytes_to_read = 1000

    def enumerate_hid_devices(self):
       return hid.enumerate()
   
    def clear_buffer(self):
        ls=[]
        while 1:
            l = self.dev.read(self.bytes_to_read,self.timeout_ms)
            if len(l)==0:
                break
            ls.append(l)
        print(len(ls))
        
    def _write_read_command(self,hex_str):
        hsl = hex_str.split(' ')
        #hsl.insert(0,'')
        #hsls = r'\x'.join(hslhs)

        isl = [int(x,16) for x in hsl]
        self.dev.write(isl)
        return self.dev.read(self.bytes_to_read,self.timeout_ms)
        
        
    def read_single(self):
        l = self._write_read_command(FUNCTIONS['read_single'])
        
        if len(l)==0:
            print('No answer')
            return
        la = np.array(l)
        laf = la[4]
        lar = la[5]
        
        lad = la[[8,9,10,11,12]]
        
        #print('function:',laf, 'data:',''.join([chr(x) for x in lad]),'range:',chr(lar))
        
        mode_str = MODES[laf][0]
        
        range_str = chr(lar)
        
        unit_str = MODES[laf][1] if type(MODES[laf][1])==str else MODES[laf][1][range_str]
        
        data_str = ''.join([chr(x) for x in lad])
        
        
        if laf==20:
            data=data_str
        elif 'L' in data_str:
            data = np.inf
        else:
            data = float(data_str)
        
        print(f'{mode_str}: {data} {unit_str}')
        return mode_str, range_str, data, unit_str
        
        
    def backlight(self):
        self._write_read_command(FUNCTIONS['light'])
    def select(self):
        self._write_read_command(FUNCTIONS['select']) 
    def manual_range(self):
        self._write_read_command(FUNCTIONS['manual_range'])        
    def auto_range(self):
        self._write_read_command(FUNCTIONS['auto_range'])
    def relative(self):
        self._write_read_command(FUNCTIONS['rel'])       
    def hz_percent_usb(self):
        self._write_read_command(FUNCTIONS['hz_percent_usb'])
    def hold(self):
        self._write_read_command(FUNCTIONS['hold'])
    def max_min(self):
        self._write_read_command(FUNCTIONS['max_min'])   
    def min_max_exit(self):
        self._write_read_command(FUNCTIONS['min_max_exit'])           

if __name__ == '__main__':
    mm = MultiCompMultiMeter(name = 'multimeter')    

        # %%

        # hid.enumerate()

        # # %%
        # dev = hid.device()


        # # %%

        # dev.open(vendor_id,product_id)

        # # %%

        # ls = []

        # ranges = [6,60,600,6000]
        # while 1:
        #     l = dev.read(1000,1100)
        #     if len(l)==0:
        #         break
        #     la = np.array(l)
        #     laf = la[4]
        #     lar = la[5]
            
        #     lad = la[[8,9,10,11,12]]
        #     print('function:',laf,'range:',chr(lar), 'data:',''.join([chr(x) for x in lad]))
            
        #     #print(lar,lad)
        #     ls.append(l)
            
            

        # print(len(ls))
        # %%

        






        # # %%
        # lsa = np.array(ls)
        # print(lsa.shape)
        # lsad = lsa[:,(8,9,10,11,12)] - 48

        # print(np.min(lsad,axis=0))
        # print(np.max(lsad,axis=0))


        # # %%

        # lch=[chr(x) for x in l]
        # print(lch)

        # lun=[str(x).encode('utf-8').decode('utf-8') for x in l]
        # print(lun)
        # # %%

        # import numpy as np

        # l1 = np.array([19, 171, 205, 16, 6, 53, 32, 32, 32, 79, 46, 76, 32, 3, 0, 48, 52, 48, 3, 163, 91, 213, 105, 87, 237, 109, 187, 95, 39, 223, 53, 83, 245, 251, 247, 127, 170, 119, 237, 249, 217, 251, 246, 123, 117, 109, 139, 239, 245, 221, 231, 245, 87, 187, 95, 171, 171, 95, 255, 111, 215, 191, 187, 219]
        #               )
        # l2 = np.array([19, 171, 205, 16, 2, 48, 32, 32, 48, 46, 48, 48, 48, 0, 0, 48, 48, 48, 3, 120, 91, 213, 105, 87, 237, 109, 187, 95, 39, 223, 53, 83, 245, 251, 247, 127, 170, 119, 237, 249, 217, 251, 246, 123, 117, 109, 139, 239, 245, 221, 231, 245, 87, 187, 95, 171, 171, 95, 255, 111, 215, 191, 187, 219]
        #               )

        # print(l1-l2)

        # # %% 

       
        # # %%

        # hsl = hex_str.split(' ')
        # #hsl.insert(0,'')
        # #hsls = r'\x'.join(hslhs)

        # isl = [int(x,16) for x in hsl]
        # dev.write(isl)


        # l = dev.read(1000,1000)

        # print(l)
        
        
        
        
        
        
        
#         self.visa_handle.read_termination = '\n'
#         self.connect_message()
#         self.add_parameter(name='current_setpoint',
#                          label='Sets the output current.',
#                          unit='A',
#                          get_cmd='ISET1?',
#                          set_cmd='ISET1:{}',
#                          get_parser=float,
#                          vals=Numbers(min_value=0,
#                                       max_value=max_current))
#         self.add_parameter(name='actual_current',
#                          label='Returns the actual output current.',
#                          unit='A',
#                          get_cmd='IOUT1?',
#                          get_parser=float)
        
#         self.add_parameter(name='voltage_setpoint',
#                          label='Sets the output voltage.',
#                          unit='V',
#                          get_cmd='VSET1?',
#                          set_cmd='VSET1:{}',
#                          get_parser=float,
#                          vals=Numbers(min_value=0,
#                                       max_value=max_voltage))
#         self.add_parameter(name='actual_voltage',
#                          label='Returns the actual output voltage.',
#                          unit='V',
#                          get_cmd='VOUT1?',
#                          get_parser=float)
        
#         self.add_parameter('output',
#                             label='Turn on/off output',
#                             set_cmd='OUT{}',
#                             val_mapping=create_on_off_val_mapping(on_val='1',
#                                                                   off_val='0'))
#         self.add_parameter('ocp',
#                             label='Turn on/off over-current protection',
#                             set_cmd='OCP{}',
#                             val_mapping=create_on_off_val_mapping(on_val='1',
#                                                                   off_val='0'))
#         self.add_parameter('ovp',
#                             label='Turn on/off over-voltage protection',
#                             set_cmd='OVP{}',
#                             val_mapping=create_on_off_val_mapping(on_val='1',
#                                                                   off_val='0'))
        
#     def __enter__(self):
#         """ Method to allow the use of the with-as statement
#         """
#         return self
        
#     def __exit__(self, type, value, traceback):
#         """ Method to allow the use of the with-as statement
#         """
#         self.close()
        
#     def get_status(self):
#         s = self.visa_handle.query('STATUS?')
#         si=ord(s)
#         ch1_mode = 'CV mode' if si & 2**0 else 'CC mode'
#         ch2_mode = 'CV mode' if si & 2**1 else 'CC mode'
#         beep = si & 2**4 > 0
#         lock = si & 2**5 > 0
#         output = si & 2**6 > 0
#         return dict(status_integer = si,ch1_mode=ch1_mode,ch2_mode=ch2_mode, beep=beep, lock=lock ,output=output )
    
#     def output_on(self):
#         self.output(True)
        
#     def output_off(self):
#         self.output(False)


# if __name__ == '__main__':
#     # with TenmaPowerSupply(name = 'tenma', address  = 'ASRL17::INSTR', ) as ten:
#     #     print(ten.get_status())
#     ten = TenmaPowerSupply(name = 'tenma', address  = 'ASRL17::INSTR', )
