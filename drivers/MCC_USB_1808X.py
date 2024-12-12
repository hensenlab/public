# -*- coding: utf-8 -*-
"""
Created 2024

@author: B.J.Hensen

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2024, Hensen Lab
All rights reserved.

Instrument wrapper for Digilent MCC_USB_1808X ADC

https://digilent.com/shop/mcc-usb-1808x-high-speed-high-precision-simultaneous-usb-daq-device

see https://pypi.org/project/mcculw for installation instructions.
basically: first install https://digilent.com/shop/software/mcc-software/daqami/
then pip install mcculw
Also, see python examples at https://github.com/mccdaq/mcculw/raw/master/examples.zip

"""

from ctypes import cast, POINTER, c_double, c_ushort, c_ulong
import numpy as np

from mcculw import ul
from mcculw.enums import InterfaceType, ScanOptions, FunctionType, Status, AnalogInputMode
from mcculw.device_info import DaqDeviceInfo


class MCC_USB_1808X():

    def __init__(self, name, device_id=None, board_num=0):
        """
            use device_id to select a particular device. 
            If more than one devices are being used at the same time, 
            the devices can be kept apart using board_num.

            board_num : int
                The number you wish to associate with the board when created with
                :func:`.create_daq_device`. board_num may be 0 to 99, and must not be associated with any
                other installed device.
        """
        self.name = name
        self.board_num = board_num
        ul.ignore_instacal()
        devices = ul.get_daq_device_inventory(InterfaceType.ANY)

        for device in devices:
            print('  ', device.product_name, ' (', device.unique_id, ') - ',
                  'Device ID = ', device.product_id, sep='')
            if device_id is not None:
                if device.product_id == device_id:
                    self.device = device
        if device_id is None:
            self.device = devices[0]

        ul.create_daq_device(self.board_num, device)

        self.daq_dev_info = DaqDeviceInfo(self.board_num)
        self.ai_info = self.daq_dev_info.get_ai_info()
        self.ao_info = self.daq_dev_info.get_ao_info()

    def set_ai_channel_differential(self, channel, differential = True):
        if differential:
            ul.a_chan_input_mode(self.board_num, channel, AnalogInputMode.DIFFERENTIAL)
        else:
            ul.a_chan_input_mode(self.board_num, channel, AnalogInputMode.SINGLE_ENDED)

    def prepare_and_do_ai_scan(self,low_chan, high_chan, samples, rate):
        """ convienience function to perform a simple analog input scan"""
        num_chans, total_samples, memhandle, ctypes_array, scan_options = self.prepare_ai_scan(low_chan, high_chan, samples)

        self.start_ai_scan(low_chan, high_chan, total_samples, rate, self.ai_info.supported_ranges[0], memhandle, scan_options)

        return self.reshape_ai_array(ctypes_array, num_chans, total_samples)

    def reshape_ai_array(self, ctypes_array, num_chans, total_samples):
        return np.reshape(ctypes_array[0:total_samples],(-1,num_chans))

    def prepare_ai_scan(self, low_chan, high_chan, samples,  background=False, continuous= False):
        num_chans = high_chan - low_chan + 1
        total_samples = samples * num_chans

        if background:
            scan_options = ScanOptions.BACKGROUND
        else:
            scan_options = ScanOptions.FOREGROUND

        if continuous:
            scan_options |=ScanOptions.CONTINUOUS

        # we always want to scale to enegneering units eg volts. there are of course other options.
        scan_options |= ScanOptions.SCALEDATA 

        memhandle = ul.scaled_win_buf_alloc(total_samples)
        ctypes_array = cast(memhandle, POINTER(c_double))

        return num_chans, total_samples, memhandle, ctypes_array, scan_options

    def start_ai_scan(self, low_chan, high_chan, total_samples, rate, ai_range, memhandle, scan_options):
        # print(low_chan, high_chan, total_samples, rate, ai_range, memhandle, scan_options)
        ul.a_in_scan(self.board_num, low_chan, high_chan, total_samples,
                            rate, ai_range, memhandle, scan_options)

    def get_ai_status(self):
        status, curr_count, curr_index = ul.get_status(
                self.board_num, FunctionType.AIFUNCTION)
        return status, curr_count, curr_index

    def stop_ai_background(self):
        ul.stop_background(self.board_num, FunctionType.AIFUNCTION)

    def output_voltage(self, channel, voltage):
        ul.v_out(self.board_num, channel, self.ao_info.supported_ranges[0], voltage)




