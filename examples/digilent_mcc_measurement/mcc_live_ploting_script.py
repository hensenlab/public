# -*- coding: utf-8 -*-
"""
Created 2024

@author: B.J.Hensen

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2024, Hensen Lab

All rights reserved.

https://www.pyqtgraph.org/
conda install -c conda-forge pyqtgraph
"""
import time
import os
import numpy as np

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore

from drivers.MCC_USB_1808X import MCC_USB_1808X


# %%

mcc_ins = MCC_USB_1808X('our_mcc')



# %% basic timetrace block plot
plot_channels = [0]
low_chan = 0
high_chan = 3
rate = 1000
duration = 0.5 #trace length
samples = int(duration*rate)

for ch in range(low_chan,high_chan+1):
    mcc_ins.set_ai_channel_differential(ch,False)

num_chans, total_samples, memhandle, ctypes_array, scan_options = mcc_ins.prepare_ai_scan(low_chan, high_chan, samples)
t = np.linspace(0, samples/rate, samples)

win = pg.GraphicsLayoutWidget(show=True, title="Basic block plot")
win.resize(1000,600)
win.setWindowTitle('pyqtgraph example: Plotting')
pg.setConfigOptions(antialias=True)

p1 = win.addPlot(title="Basic array plotting")
p1.getAxis('bottom').setLabel('Time')
p1.getAxis('left').setLabel('Voltage')
p1.addLegend()
def update():
    mcc_ins.start_ai_scan(low_chan, high_chan, total_samples, rate, mcc_ins.ai_info.supported_ranges[0], memhandle, scan_options)
    data = mcc_ins.reshape_ai_array(ctypes_array, num_chans, total_samples)

    for ii,ch in enumerate(plot_channels):
        p1.plot(x = t,y = data[:,ch], clear=(ii==0), pen = (ch,len(plot_channels)), name=f'ch {ch:d}')

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(0)
pg.exec()

# %% basic x/y block plot


low_chan = 0
high_chan = 3

for ch in range(low_chan,high_chan+1):
    mcc_ins.set_ai_channel_differential(ch,False)

rate = 1000
duration = 0.2 #trace length
samples = int(duration*rate)

x_channel = 0
y_channels = [1]

num_chans, total_samples, memhandle, ctypes_array, scan_options = mcc_ins.prepare_ai_scan(low_chan, high_chan, samples)

win = pg.GraphicsLayoutWidget(show=True, title="Basic block plot")
win.resize(1000,600)
win.setWindowTitle('pyqtgraph example: Plotting')
pg.setConfigOptions(antialias=True)

p1 = win.addPlot(title="Basic array plotting")
p1.getAxis('bottom').setLabel('Voltage')
p1.getAxis('left').setLabel('Voltage')
p1.addLegend()

def update():
    mcc_ins.start_ai_scan(low_chan, high_chan, total_samples, rate, mcc_ins.ai_info.supported_ranges[0], memhandle, scan_options)
    data = mcc_ins.reshape_ai_array(ctypes_array, num_chans, total_samples)
    for ii,ch in enumerate(y_channels):
        p1.plot(x = data[:,x_channel],y = data[:,ch], clear=(ii==0), pen = (ch,len(y_channels)), name=f'ch {ch:d}')


timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(0)
pg.exec()

timer.stop()
mcc_ins.stop_ai_background()

# %% Continuous streaming plot

# %%
from mcculw.enums import Status

plotsize = 1000 # show last 1000 points only
plot_update_time = 0.05#s
plot_channels = [0]


low_chan = 0
high_chan = 3
rate = 1000
samples = int(10*plotsize)

for ch in range(low_chan,high_chan+1):
    mcc_ins.set_ai_channel_differential(ch,False)

num_chans, total_samples, memhandle, ctypes_array, scan_options = mcc_ins.prepare_ai_scan(low_chan, high_chan, samples, background=True, continuous= True)

win = pg.GraphicsLayoutWidget(show=True, title="Basic block plot")
win.resize(1000,600)
win.setWindowTitle('pyqtgraph example: Plotting')
pg.setConfigOptions(antialias=True)

p1 = win.addPlot(title="Streaming array plotting")
p1.getAxis('bottom').setLabel('Time')
p1.getAxis('left').setLabel('Voltage')
p1.addLegend()
mcc_ins.start_ai_scan(low_chan, 
                       high_chan, 
                       total_samples, 
                       rate,
                       mcc_ins.ai_info.supported_ranges[0],
                       memhandle, 
                       scan_options)

status = Status.IDLE
# Wait for the scan to start fully
while status == Status.IDLE:
    status, _, _ = mcc_ins.get_ai_status()


prev_count = 0
prev_index = 0
total_data_samples = 0
plot_data = np.full((plotsize, num_chans), np.nan)

def update():
    global prev_count, prev_index, total_data_samples, plot_data
    # Get the latest counts
    status, curr_count, curr_index = mcc_ins.get_ai_status()
    new_data_count = curr_count - prev_count
    if new_data_count>2:
        if status == Status.IDLE or new_data_count > total_samples:
            #buffer overrun: print an error and stop writing
            mcc_ins.stop_ai_background()
            raise Exception('A buffer overrun occurred')
        if prev_index + new_data_count > total_samples - 1:
            first_chunk_size = total_samples - prev_index
            second_chunk_size = new_data_count - first_chunk_size
            new_data_0 = np.reshape(ctypes_array[prev_index:total_samples],(-1,num_chans))
            new_data_1 = np.reshape(ctypes_array[0:second_chunk_size],(-1,num_chans))
            new_data = np.concatenate((new_data_0, new_data_1),axis=0)
        else:
            new_data = np.reshape(ctypes_array[prev_index:prev_index+new_data_count],(-1,num_chans))
        
        new_data_samples = new_data.shape[0]
        
        plot_data = np.roll(plot_data,-new_data_samples,axis=0)
        plot_data[-new_data_samples:,:] = new_data
        total_data_samples += new_data_samples
        prev_count = curr_count
        prev_index += new_data_count
        prev_index %= total_samples
        
        t = np.linspace(total_data_samples/rate-plotsize/rate,total_data_samples/rate,plotsize)
        for ch in plot_channels:
            p1.plot(x = t,y = plot_data[:,ch], pen=(ch,len(plot_channels)), clear=(ch==0), name=f'ch {ch:d}')
            
            ax.setTicks([[(t[0],f'{t[0]:.3f}'),(t[-1],f'{t[-1]:.3f}')]])
            # ax.setWidth(100)
            
            #ax.setTickSpacing(major=(t[-1]-t[0])*0.9)

timer = QtCore.QTimer()
#timer.setSingleShot(True)
timer.timeout.connect(update)
timer.start(int(plot_update_time*1000))
pg.exec()

timer.stop()
mcc_ins.stop_ai_background()


# %% dual xy plot



low_chan = 0
high_chan = 2
rate = 1000
duration = 0.1 #trace length
samples = int(duration*rate)

x_channel = 0
y1_channel = 1
y2_channel = 2


for ch in range(low_chan,high_chan+1):
    mcc_ins.set_ai_channel_differential(ch,False)

num_chans, total_samples, memhandle, ctypes_array, scan_options = mcc_ins.prepare_ai_scan(low_chan, high_chan, samples)

win = pg.GraphicsLayoutWidget(show=True, title="Basic block plot")
win.resize(1000,600)
win.setWindowTitle('pyqtgraph example: Plotting')
pg.setConfigOptions(antialias=True)

p1 = win.addPlot(title="Basic array plotting")
p1.addLegend()
def update():
    mcc_ins.start_ai_scan(low_chan, high_chan, total_samples, rate, mcc_ins.ai_info.supported_ranges[0], memhandle, scan_options)
    data = mcc_ins.reshape_ai_array(ctypes_array, num_chans, total_samples)
    p1.plot(x = data[:,x_channel],y = data[:,y1_channel], pen='blue', clear=True)
    p1.plot(x = data[:,x_channel],y = data[:,y2_channel], pen='red', clear=False)

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(0)
pg.exec()

timer.stop()
mcc_ins.stop_ai_background()
    