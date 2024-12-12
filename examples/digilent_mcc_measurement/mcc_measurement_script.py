# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
Created 2024

@author: B.J.Hensen

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2024, Hensen Lab

All rights reserved.
"""


import time
import os
import numpy as np

from matplotlib import pyplot as plt

from drivers.MCC_USB_1808X import MCC_USB_1808X

from lib.mcc_measurement import MCCMeasurement, MCCLoggingMeasurement

import config
data_folder = config.get('data_folder')

# %%

mcc_ins = MCC_USB_1808X('our_mcc')

# %% normal measurement

params = {}

params['low_chan'] = 0
params['high_chan'] = 1

for ch in range(params['low_chan'],params['high_chan']+1):
    mcc_ins.set_ai_channel_differential(ch,False) # setup channels to measure Singel ended or differential

params['rate'] = 1000
duration = 5 #trace length
params['samples'] = int(duration*params['rate'])
print(mcc_ins.ai_info.supported_ranges)
params['ai_range_idx'] = 0
params['averages'] = 20
params['plot_type'] = 'psd' # psd or timetrace
params['fft_window'] = 'hann' #see scipy.signal.periodogram
# %% 
meas = MCCMeasurement('test', mcc_ins, base_folder = data_folder, params = params, cached=True)
meas.setup()
if params['averages'] > 1:
	meas.run_averaged()
else:
	meas.run(setup=False)
meas.finish()


# %% continuous logging measuremnt
params = {}
params['low_chan'] = 0
params['high_chan'] = 1
for ch in range(params['low_chan'],params['high_chan']+1):
    mcc_ins.set_ai_channel_differential(ch,False) # setup channels to measure Singel ended or differential
params['rate'] = 1000
params['ai_range_idx'] = 0
meas = MCCLoggingMeasurement('test', mcc_ins, base_folder = data_folder, params = params)
meas.setup()
meas.run(setup=False)
meas.finish()
