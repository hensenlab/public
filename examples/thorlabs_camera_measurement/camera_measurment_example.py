# -*- coding: utf-8 -*-
"""
Created 2024

@author: B.J.Hensen

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2024, Hensen Lab

All rights reserved.
"""
import sys
import os
import numpy as np
import time

from windows_setup import configure_path
configure_path()

# if you get the error that windows_setup cannot be found, make sure you are excecuting this scrip in the current directory.
# the Thorlabs dlls need to be in the same directory as the script you are excecuring this script from!
# If you put them elsewhere and add that location to os.ENVIRON['path'], it will STILL NOT WORK!

from lib import camera_measurement

import config
data_folder = config.get('data_folder')

# %%

from drivers.ThorlabsScientificCamera import ThorlabsScientificCamera

cam = ThorlabsScientificCamera('Sid_cam')

# %%
# #
# from drivers.ThorlabsScientificCamera_with_threaded_liveview import ThorlabsScientificCameraThreadedLiveview
#
# cam = ThorlabsScientificCameraThreadedLiveview('Sid_cam')

# you can now use cam.start_threaded_live_view() and cam.stop_threaded_live_view(), 
# these work when excecuted in the console. Not when excecuted as a run_cell evaluation
  
# %%
# cam.live_view()

# %% single measurement

params = {}
params['do_plot'] = True
params['plot_update_frames'] = 5
params['max_frames'] = 10000
params['max_duration'] = 1000 #s
params['frames_to_buffer'] = 100

name='ringdown_after_trapping'

m = camera_measurement.CameraMeasurement(name, cam, params=params, base_folder=data_folder, cached=True)
m.setup()
m.run(run_identifier=str(0),run_params={})
m.finish()
print(m.f_id)

# %% q measuremnt

params = {}

delay_time = 2 #s
frame_count_update = int(delay_time/cam.exposure_time())


params['do_plot'] = True
params['plot_update_frames'] = 5
params['max_frames'] = 50000
params['max_duration'] = 1000 #s
params['frames_to_buffer'] = 100

params['amplitude'] = 1
params['frequency'] = 45

name = 'q_meas'

# turn_on_coherent_drive()

def callback(frame_count):
    if frame_count>frame_count_update: 
        #turn_off_coherent_drive()
        return 0.      
    return 1.

m = camera_measurement.CameraMeasurement(name, cam,  params=params, base_folder=data_folder)
m.setup()
m.run(run_identifier=str(0),run_params={},update_callback=callback)
m.finish()

# %% frequency sweep - works for typical framerates less than 100 Hz

data_folder = config.get('data_folder')

params = {}

delay_time = 1 #s
frame_count_update = int(delay_time/cam.exposure_time())
pts = 130
freqs = np.linspace(1, 130, pts)

params['do_plot'] = True
params['plot_update_frames'] = 5
params['max_frames'] = int(frame_count_update*pts)
params['max_duration'] = 1000 #s
params['frames_to_buffer'] = 100
name = 'freq_sweep'


#prepare_function_generator()

def callback(frame_count):
    step = min([int(np.floor(frame_count/frame_count_update)),pts-1])
    f = freqs[step]
    if frame_count%frame_count_update ==0 and step<pts: 
        print(step, f)
        #change_function_generator_frequency()
    return f


m = camera_measurement.CameraMeasurement(name, cam,  params=params, base_folder=data_folder)
m.setup()
m.run(run_identifier=str(0),run_params={},update_callback=callback)
m.finish()

