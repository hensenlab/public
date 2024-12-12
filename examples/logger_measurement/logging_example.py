# -*- coding: utf-8 -*-
"""
Created 2022

@author: B.J.Hensen

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2022, Hensen Lab

All rights reserved.
"""

import config
data_folder = config.get('data_folder')
    
from lib.logger_measurement import LoggerMeasurement

from drivers.Keithley_2400 import Keithley2400
source_meter = Keithley2400('source_meter','ASRL11::INSTR',terminator="\r")

source_meter.output(False)
source_meter.write('SENS:RES:MODE MAN')
source_meter.mode('CURR')
source_meter.compliancev.set(0.5)
source_meter.rangei.set(0.001)
source_meter.curr.set(0.001)
source_meter.output(True)

# %%
from drivers.Lakeshore import LakeshoreModel335
temperature_controller = LakeshoreModel335(57600,com_port='COM13')

get_temperature_func = lambda: temperature_controller.get_kelvin_reading('A')


name = 'test_meas'

m= LoggerMeasurement(name,base_folder = data_folder)

m.add_log_parameter('resistance_1', source_meter.resistance.get, 1, 'Top Resistance (Ohm)')
m.add_log_parameter('temperature_cage_lens', get_temperature_func, 1, r'$T_{cage}$ (K)')


m.params['do_plot'] = True
m.params['autoscale_plot_x'] = True
m.params['autoscale_plot_y'] = True
m.params['update_time'] = 2

m.run()

m.finish()
