# -*- coding: utf-8 -*-
"""
Created 2023, based on earlier work in the Groeblacher lab, https://github.com/GroeblacherLab

@author: B.J.Hensen

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2023, Hensen Lab

All rights reserved.

"""

import numpy as np
import time

from qcodes import Instrument

from drivers import ZNB
from lib.vna_measurement_rs import VNAMeasurement, VNACurrentMeasurement
import config
data_folder = config.get('data_folder')

# %%
try:
    vna = Instrument.find_instrument('vna')
    vna.close()
except KeyError:
    pass

vna = ZNB.ZNB('vna','TCPIP0::192.168.0.4::inst0::INSTR')


################################################################
#%% simplest example, take a vna snapshot using the current vna settings

name = 'test'
params = {}

params['device'] = ''  
meas = VNAMeasurement(name, vna, params=params, base_folder=data_folder)
# meas.params['vna_opc_update_time'] = 10# optional longer time (default 0.5) between checking if the trace is complete: this allows you to do stuff on the vna for longer before it hops back to remote

meas.run(run_identifier=str(0),run_params={})
#meas.run(run_identifier=str(1),run_params={})

meas.finish()     

################################################################
# %% take a vna trace, without updating it, essentially saving the current trace.
name = 'full_scan_'
params = {}

params['device'] = '' 

meas = VNAMeasurement(name, vna, params=params, base_folder=data_folder)
meas.run(run_identifier=str(0),run_params={}, skip_update_channels=[1], stop_cont_meas=False) # if you do not want to restart the trace, but just take the current one, add the trace channel to the updatred channels kw
meas.finish() 

################################################################
# %% continuous scans
name = 'warmup-to-4K'
params = {}

params['device'] = ''  
params['max_scans'] = 20000

params['wait_time'] = 0.01

meas = VNAMeasurement(name, vna, params=params, base_folder=data_folder)
meas.setup()
meas.params['do_plot'] = False

trace = vna.traces[0]
trace.update_lin_traces()

for i in range(params['max_scans']):
    t0=time.time()
    meas.run(run_identifier=str(i),setup=False,run_params={'timestamp': time.time(), 'timestring': time.strftime('%Y-%m-%d %H:%M:%S')}) # skip_update_channels=[1],stop_cont_meas=False
    t1 = time.time()
    time.sleep(params['wait_time'])
    
    print(i, t1-t0)

meas.finish()     

################################################################
# %% set VNA parameters before measuerment
name = 'full_scan_0dBm'
params = {}

params['device'] = ''  

trace = vna.traces[0]
trace.start(4e9)
trace.stop(8e9)
trace.npts(10001)
trace.bandwidth(5)
trace.avg(1)
trace.power(-0)


meas = VNAMeasurement(name,vna,params=params, base_folder = data_folder)

meas.run(run_identifier=str(0),run_params={})
#meas.run(run_identifier=str(0),run_params={}, skip_update_channels=[0]) # if you do not want to restart the trace, but just take the current one, add the trace channel to the updatred channels kw

meas.finish() 
#############################################################

# %% stepped scans
name = '18mK_0_5_GHz_range'
params = {}

params['device'] = ''   
params['center_frequencies'] = np.arange(0.5e9, 5e9+1e8, 1e8)  #  [0.5e9,1.5e9,2.5e9,3.5e9,4.5e9]
trace = vna.traces[0]
trace.span(1e8)
freq_stepsize = 1e3
trace.npts(int(trace.span()/freq_stepsize)+1)
trace.bandwidth(100)
trace.avg(1)
trace.power(5)

meas = VNAMeasurement(name, vna, params=params, base_folder = data_folder)
meas.setup()


for i,cf in enumerate(params['center_frequencies']):
    #meas.run(run_identifier=str(0),run_params={})
    trace.center(cf)
    meas.run(run_identifier=str(i),setup=False,run_params={'center_frequency':cf}) # if you do not want to restart the trace, but just take the current one, add the trace channel to the updatred channels kw
    

meas.finish()    
#############################################################

# %% Zoom in on resonances
name = 'zooms'
params = {}

params['device'] = ''  

params['center_frequencies'] = np.array([4.2776, 4.536911, 5.38022, 5.40760, 5.5751,  5.59237, 5.59380183, 5.6647, 5.692451, 5.77382])*1e9
trace = vna.traces[0]
trace.span(5e6)
#freq_stepsize = 1e3
#trace.npts(int(trace.span()/freq_stepsize)+1)
trace.npts(10001)
trace.bandwidth(5)
trace.avg(1)
trace.power(-50)

meas = VNAMeasurement(name, vna, params=params, base_folder = data_folder)
meas.setup()


for i,cf in enumerate(params['center_frequencies']):
    #meas.run(run_identifier=str(0),run_params={})
    trace.center(cf)
    meas.run(run_identifier=str(i),setup=False,run_params={'center_frequency':cf}) # if you do not want to restart the trace, but just take the current one, add the trace channel to the updatred channels kw
    
meas.finish() 
#############################################################   
    
# %% Power sweep
name = 'power_sweep'
params = {}

params['device'] = 'Steele-01'  
params['center_frequencies'] = [5.75e9]  #[5.122e9,5.556e9,6.13e9]
params['powers'] = [-50, -40, -30, -20, -10, 0, 8]

trace = vna.traces[0]
trace.span(900e6)
# freq_stepsize = 40e3
# trace.npts(int(trace.span()/freq_stepsize)+1)
trace.npts(100001)
trace.bandwidth(1e2)
trace.avg(1)

meas = VNAMeasurement(name,vna, params=params, base_folder = data_folder)
meas.setup()

for j,p in enumerate(params['powers']):
    trace.power.set(p)
    for i,cf in enumerate(params['center_frequencies']):
        #meas.run(run_identifier=str(0),run_params={})
        trace.center.set(cf)
        meas.run(run_identifier=f'{i}_{j}',setup=False,run_params={'center_frequency':cf, 'power':p}) # 

meas.finish()    
#############################################################   

# %% Current sweep
from drivers.Keithley_2400 import Keithley2400

source_meter = Keithley2400('source_meter','ASRL7::INSTR',terminator="\r")

#vna = ZNB.ZNB('VNA',ZNB20_add)

# %%
# Full sweep measurements at different flux and powers
name = 'flux_power_sweep'
params = {}

params['device'] = ''   

params['center_frequencies'] = np.array([4.53])*1e9 # 5.38022, 5.40760, 5.5751,  5.59237, 5.59380183, 5.6647, 5.692451, 5.77382])*1e9 #4.2776, 
trace = vna.traces[0]
trace.span(20e6)
#freq_stepsize = 1e3
#trace.npts(int(trace.span()/freq_stepsize)+1)
trace.npts(1001)
trace.bandwidth(100)
trace.avg(1)
trace.power(0)
params['powers'] = [0]

source_meter.output(False)
source_meter.write('SENS:RES:MODE MAN')
source_meter.mode('CURR')
 
source_meter.compliancev.set(0.4)
source_meter.rangei.set(0.1)

params['currents'] = np.linspace(0, 50e-3, 50)  

source_meter.curr.set(params['currents'][0])
source_meter.output(True)

meas = VNACurrentMeasurement(name,vna, source_meter,params=params, base_folder = data_folder)
meas.setup()

for k,p in enumerate(params['powers']):
    trace.power.set(p)
    print('Power:', p)
    for j,c in enumerate(params['currents']):
        if j>0: source_meter.ramp_to(c)
    
        for i,cf in enumerate(params['center_frequencies']):
            trace.center(cf)
            source_meter.curr.set(c)
            print(source_meter.curr.get())
            meas.run(run_identifier=f'{k}_{i}_{j}',setup=False,run_params={'power':p,'center_frequency':cf,'current':source_meter.curr.get()})
   

source_meter.curr.set(0)
source_meter.output(False)
meas.finish()    
#############################################################   

# %% Full sweep measurements at different flux for dirffernet freqa
name = 'full_sweep_vs_flux'
params = {}

params['device'] = ''  
params['center_frequencies'] =  [5.53e9]
trace = vna.traces[0]
trace.span(50e6)
freq_stepsize = 200e3
trace.npts(int(trace.span()/freq_stepsize)+1)
trace.bandwidth(1e2)
trace.avg(1)
trace.power(-50)

source_meter.write('SENS:RES:MODE MAN')
source_meter.mode('CURR')

source_meter.compliancev.set(6)
source_meter.rangev.set(6)
source_meter.rangei.set(0.21)

params['currents'] = np.linspace(0, 20e-3, 201) #np.linspace(0, 0.15, 50)

source_meter.curr.set(params['currents'][0])
source_meter.output(True)

meas = VNACurrentMeasurement(name, vna, source_meter, params=params, base_folder = data_folder)
meas.setup()


for j,c in enumerate(params['currents']):
    source_meter.curr.set(c)
    print(j,'\n','I (A):', c)
    print('R (ohm):', source_meter.resistance.get())
    print('P (W):',  source_meter.resistance.get()*source_meter.curr.get()**2)

    for i,cf in enumerate(params['center_frequencies']):
        trace.center.set(cf)
        meas.run(run_identifier=f'{i}_{j}', setup=False, run_params={'current': source_meter.curr.get(), 'resistance': source_meter.resistance.get()}) # if you do not want to restart the trace, but just take the current one, add the trace channel to the updatred channels kw


source_meter.curr.set(0)
source_meter.output(False)
meas.finish()    
