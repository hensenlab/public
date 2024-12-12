# -*- coding: utf-8 -*-
"""
Created 2024

@author: B.J.Hensen

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2024, Hensen Lab

All rights reserved.

First install zhinst python api at 

# pip install zhinst 
# pip install zhinst-qcodes

"""
# %%
import time
import logging
import numpy as np

lib import zi_measurement
import config
data_folder = config.get('data_folder')

logging.getLogger().setLevel(logging.INFO)

from zhinst.qcodes import MFLI

device = MFLI("DEV7700", "192.168.0.10", name="our_mfli")


# %% Scope measurement
name = 'test'

params = {}
params['do_plot'] = True
params['check_scope_record_flags'] = True
params['scope_fft_mode'] = False  # True
params['scope_averager_weigth'] = 0
params['scope_history_length'] = 1
params['scope_averager_method'] = 0
params['fft_window'] = 0

meas = zi_measurement.ZIScopeMeasurement(name, device, params=params, base_folder=data_folder)

print('Running meas')
meas.run()
meas.finish()

# %% Sweeper measurement
params = {}
params['do_plot'] = True
params['autoscale_plot'] = True
params['update_time'] = 1  # s
params['save_data_keys'] = ['grid', 'x', 'xpwr', 'xstddev', 'y', 'ypwr', 'ystddev']
params['start'] = 0  # Hz
params['stop'] = 500  # Hz
params['samplecount'] = 250
params['xmapping'] = 0  # linear (=0) or logarithmic (=1)
params[
    'bandwidthcontrol'] = 0  # manually (=0), fixed bandwidth (=1), automatically (=2) https://docs.zhinst.com/labone_api_user_manual/modules/sweeper/index.html#controlling-how-the-sweeper-sets-the-demodulators-time-constant
params[
    'bandwidthoverlap'] = 0  # https://docs.zhinst.com/labone_api_user_manual/modules/sweeper/index.html#bandwidthoverlap
params[
    'scan'] = 0  # sequential scan mode (=0), binary scan mode (=1), bidirectional scan mode (=2), reverse scan mode (=3), https://docs.zhinst.com/labone_api_user_manual/modules/sweeper/index.html#controlling-the-scan-mode-the-selection-of-range-values
params['loopcount'] = 1
params[
    'settling_time'] = 0  # https://docs.zhinst.com/labone_api_user_manual/modules/sweeper/index.html#specifying-the-sweepers-settling-time
params['settling_inaccuracy'] = 0.001
params[
    'averaging_tc'] = 0  # https://docs.zhinst.com/labone_api_user_manual/modules/sweeper/index.html#specifying-how-the-measurement-data-is-averaged
params['averaging_sample'] = 1

params['gridnode'] = device.oscs[0].freq.zi_node
params['sample_nodes'] = [device.demods[0].sample.zi_node]

meas = zi_measurement.ZISweeperMeasurement('spectrum_paper_lib', device, params=params, base_folder=data_folder)

print('Running sweeper meas')
meas.run(run_identifier=str(0), setup=True)
meas.finish()

# %% Looped sweeper measurement

params = {}
params['do_plot'] = True
params['autoscale_plot'] = True
params['update_time'] = 1  # s
params['save_data_keys'] = ['grid', 'r', 'rpwr', 'rstddev', 'phase', 'phasepwr', 'phasestddev']

params['start'] = 1  # Hz
params['stop'] = 500  # Hz
params['samplecount'] = 250
params['xmapping'] = 0  # linear (=0) or logarithmic (=1)
params[
    'bandwidthcontrol'] = 0  # manually (=0), fixed bandwidth (=1), automatically (=2) https://docs.zhinst.com/labone_api_user_manual/modules/sweeper/index.html#controlling-how-the-sweeper-sets-the-demodulators-time-constant
params[
    'bandwidthoverlap'] = 0  # https://docs.zhinst.com/labone_api_user_manual/modules/sweeper/nodedoc.html?h=bandwidthoverlap#bandwidthoverlap
params[
    'scan'] = 0  # sequential scan mode (=0), binary scan mode (=1), bidirectional scan mode (=2), reverse scan mode (=3), https://docs.zhinst.com/labone_api_user_manual/modules/sweeper/index.html#controlling-the-scan-mode-the-selection-of-range-values
params['loopcount'] = 1  # works now!
params[
    'settling_time'] = 0  # https://docs.zhinst.com/labone_api_user_manual/modules/sweeper/index.html#specifying-the-sweepers-settling-time
params['settling_inaccuracy'] = 0.001
params[
    'averaging_tc'] = 0  # https://docs.zhinst.com/labone_api_user_manual/modules/sweeper/index.html#specifying-how-the-measurement-data-is-averaged
params['averaging_sample'] = 1

params['gridnode'] = device.oscs[0].freq.zi_node
params['sample_nodes'] = [device.demods[0].sample.zi_node]

#Frequency sweep
# params['sweep_parameter'] = np.linspace(2500, 3500, 20)
# params['sweep_pts'] = len(params['sweep_parameter'])

#Current sweep
# params['sweep_parameter'] = np.linspace(0.15, 0.55, 20)
# params['sweep_pts'] = len(params['sweep_parameter'])

#Tenma sweep
params['sweep_parameter'] = np.linspace(0.15, 0.35, 20)
params['sweep_pts'] = len(params['sweep_parameter'])

#Xi sweep
# params['sweep_parameter'] = np.linspace(2.0, 5.0, 20)
# params['sweep_pts'] = len(params['sweep_parameter'])

# driving_amps = np.linspace(2.5,5.5,len(params['voltages']))

meas = zi_measurement.ZISweeperMeasurement('MPT_LI_sweep', device, params=params,
                                           base_folder=data_folder)  ##sweeper measurement

meas.setup()
print('Running sweeper meas')

# std_floating = get_std_time_signal() #Get the std of the time domain signal when magnet is levitated
drop_change = 0.2  # The ratio between std of measured signal and std of signal when magnet is levitated
max_change = 1.5  # The max ratio between std of measured signal and std of signal when magnet is levitated

for j, parameter in enumerate(params['sweep_parameter']):
    if j > 0:
        meas.params['autoscale_plot'] = False

    # Frequency sweep
    # frequency = parameter
    # inner_coil_channel.frequency(frequency)
    # outer_coil_channel.frequency(frequency)
    # inner_coil_channel.phase(0)
    # outer_coil_channel.phase(180)
    # waveform_generator.sync_channel_phases()
    # print(f"Set frequency to {frequency}Hz.")

    # #Current sweep
    # current = parameter
    # inner_coil_current = current
    # outer_coil_current = inner_coil_current * current_ratio
    # print(f"Set inner coil current to {inner_coil_current}A and outer coil current to {outer_coil_current}A.")
    # inner_coil_voltage = inner_coil_current / 0.299
    # outer_coil_voltage = outer_coil_current / 0.308
    # inner_coil_channel.amplitude(inner_coil_voltage)
    # outer_coil_channel.amplitude(outer_coil_voltage)

    # Xi sweep
    # inner_coil_current = 0.2
    # outer_coil_current = min(parameter * inner_coil_current, 1)  # Limit to 1A for safety.
    # print(f"Set inner coil current to {inner_coil_current}A and outer coil current to {outer_coil_current}A.")
    # inner_coil_voltage = inner_coil_current / 0.299
    # outer_coil_voltage = outer_coil_current / 0.308
    # inner_coil_channel.amplitude(inner_coil_voltage)
    # outer_coil_channel.amplitude(outer_coil_voltage)

    # B0-field sweep
    #ramp_tenma(parameter)

    meas.run(run_identifier=str(j), setup=False, run_params={'parameter': parameter})

meas.finish()

