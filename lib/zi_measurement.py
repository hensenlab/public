# -*- coding: utf-8 -*-
"""
Created 2024

@author: B.J.Hensen

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2024, Hensen Lab

All rights reserved.
"""

import time
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

import logging

from lib.measurement import Measurement
from analysis.data_tools import phase_unwrapped_and_offset, magnitude_dB

class ZIMeasurement(Measurement):

    """
    See also https://docs.zhinst.com/zhinst-toolkit/en/latest/ and https://docs.zhinst.com/zhinst-qcodes/en/latest/

    """

    def __init__(self, name, device, **kwargs):
        super().__init__(__class__.__name__+ '_' + name,**kwargs)
        self.device = device

    def finish(self,save_zi_snapshot=True,**kwargs):
        if save_zi_snapshot:
             self.save_dict(self.device.snapshot(update=True),'zi_snapshot/')
        super().finish(**kwargs)
        

class ZISweeperMeasurement(ZIMeasurement):

    """
    See https://docs.zhinst.com/labone_api_user_manual/modules/sweeper/index.html
    """

    def setup(self):
        try:
            getattr(self,'sweeper')
            logging.warning('SETUP ALREADY  RAN, only runsetup once!')
            return
        except:
            pass
        
        super().setup()
       
        self.sweeper = self.device.session.modules.sweeper
        self.params['gridnode'] = self.params['gridnode'].lower()
        self.sweeper.gridnode(self.params['gridnode'])
        self.sweeper.start(self.params['start'])
        self.sweeper.stop(self.params['stop'])
        self.sweeper.samplecount(self.params['samplecount'])
        self.sweeper.xmapping(self.params['xmapping'])
        self.sweeper.bandwidthcontrol(self.params['bandwidthcontrol'])
        self.sweeper.bandwidthoverlap(self.params['bandwidthoverlap'])
        self.sweeper.scan(self.params['scan'])
        self.sweeper.loopcount(self.params['loopcount'])
        self.sweeper.settling.time(self.params['settling_time'])
        self.sweeper.settling.inaccuracy(self.params['settling_inaccuracy'])
        self.sweeper.averaging.tc(self.params['averaging_tc'])
        self.sweeper.averaging.sample(self.params['averaging_sample'])
        self.params['sample_nodes'] = [s.lower() for s in self.params['sample_nodes']]
        for sample_node in self.params['sample_nodes']:
            self.sweeper.subscribe(sample_node)
            
        if self.params['do_plot']:
            matplotlib.use('Qt5Agg')
            plt.close('all')
            ncols=len(self.params['sample_nodes'])
            self.fig = plt.figure(figsize=(4*ncols,6), num='ZI Sweeper Measurement')
            self.fig.clf()
            self.axs = self.fig.subplots(nrows=2,ncols=ncols,squeeze=False, sharex=True)

    def run(self, setup=True, run_identifier=None , run_params={}):
        
        if setup:
            self.setup()
        
        if run_identifier is not None:
            run_h5_group = self.h5data.create_group('{}'.format(run_identifier))
            self.save_dict(run_params,run_h5_group.name+'/')
            plot_label  = run_identifier
        else:
            run_h5_group = self.h5data
            plot_label = ''

        if self.params['do_plot']:
            
            self.plot_lines = []
            for i,sample_node in enumerate(self.params['sample_nodes']): 
                self.plot_lines.append([self.axs[0,i].plot([0,1],[1,2],'.-', label=f'run-{plot_label}-loop-0')[0],self.axs[1,i].plot([0,1],[1,2],'.-',label='loop-0')[0]])
                self.axs[0,i].legend()
                self.axs[1,i].set_xlabel(self.params['gridnode'])

            self.axs[0,0].set_ylabel('Amplitude (V)')
            self.axs[1,0].set_ylabel('Phase (rad)')

            fig_title, fig_save_fp = self.get_figure_title_and_path()
            self.fig.suptitle(fig_title)    
            self.fig.tight_layout()
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()


        for i,sample_node in enumerate(self.params['sample_nodes']): 
            for save_key in self.params['save_data_keys']:
                y_data = run_h5_group.create_dataset(f'data_node-{i:d}-{save_key}',(self.sweeper.samplecount(),self.sweeper.loopcount()),dtype=np.float64)
                y_data.attrs['sample_node'] = sample_node
                y_data.attrs['grid_node'] = self.params['gridnode']

        self.sweeper.execute()
        time.sleep(self.params['update_time'])
        self.device.session.sync()

        cur_loop = 0
        finished = False
        while 1:
            
            data = self.sweeper.read()
            #print(data.keys())
            logging.info(f'{self.name}: loop: {cur_loop+1}/{self.sweeper.loopcount()}, sweep progress: {self.sweeper.progress()}')#, remaining time: {self.sweeper.remaining()}')
            for i,sample_node in enumerate(self.params['sample_nodes']):
                if sample_node in data:
                    s_data = data[sample_node]
                    for loop_idx, loop_data in enumerate(s_data):
                        if loop_idx > 0:
                            cur_loop+=1
                            self.plot_lines[i] = [self.axs[0,i].plot([0,1],[1,2],'.-', label=f'run-{plot_label}-loop-{cur_loop}')[0],self.axs[1,i].plot([0,1],[1,2],'.-',label=f'loop-{cur_loop}')[0]]
                            self.axs[0,i].legend()
                        if len(loop_data)>0:
                            for save_key in self.params['save_data_keys']:
                                run_h5_group[f'data_node-{i:d}-{save_key}'][:,cur_loop] = loop_data[0][save_key]
                            if self.params['do_plot']:
                                self.update_plot_line(i,loop_data[0]['grid'],loop_data[0]['r'],loop_data[0]['phase'],cur_loop)
                                self.fig.canvas.draw()
                                self.fig.canvas.flush_events()
                        
            self.h5data.flush()
            if finished:
                break
            finished = self.sweeper.raw_module.finished()
            if self.params['do_plot']:
                plt.pause(self.params['update_time'])
            else:
                time.sleep(self.params['update_time'])

        if self.params['do_plot']:
            self.fig.savefig(fig_save_fp, bbox_inches='tight')
   
        self.sweeper.finish()

    def update_plot_line(self,i,x,r,phase, cur_loop):
        self.plot_lines[i][0].set_data(x,r)
        self.plot_lines[i][1].set_data(x,phase)
        if self.params['autoscale_plot'] and len(x)>2 and cur_loop==0:
            self.axs[0,i].set(xlim=(np.nanmin(x),np.nanmax(x)),ylim=(np.nanmin(r),np.nanmax(r)))
            self.axs[1,i].set(xlim=(np.nanmin(x),np.nanmax(x)),ylim=(np.nanmin(phase),np.nanmax(phase)))


class ZIScopeMeasurement(ZIMeasurement):

    """

        Take 1 or more records from the scope, does not support segmented data taking yet.
        You can call the run function multiple times.

        See https://docs.zhinst.com/labone_api_user_manual/modules/scope/index.html

    """

    def setup(self):
        try:
            getattr(self,'scope')
            logging.warning('SETUP ALREADY  RAN, only runsetup once!')
            return
        except:
            pass
        self.scope = self.device.scopes[0] #the device scope node, where you set everything like input source, timebase, trace length.
        self.scope_module = self.device.session.modules.scope #scope module is a convienience module from ZI for easy scope data transfer
        
        scope_mode = 3 if self.params['scope_fft_mode'] else 1
        self.scope_module.mode(scope_mode)
        self.scope_module.averager.weight(self.params['scope_averager_weigth'])
        self.scope_module.historylength(self.params['scope_history_length'])
        self.scope_module.fft.window(self.params['fft_window'])
        self.scope_module.subscribe(self.scope.wave)


        self.scope.enable(0) #stop running the scope
        if self.params['scope_history_length'] ==1:
            self.scope.single(1)
        else:
            self.scope.single(0)

        self.sampling_rate = self.device.clockbase()/2**self.scope.time()
        
        scope_channel = self.scope.channel()
        if scope_channel == 1:
            self.scope_channels = [1]
        elif scope_channel == 2:
            self.scope_channels = [2]
        else:
            self.scope_channels = [1,2]
            
        self.device.session.sync()
        


    def run(self, setup=True, run_identifier=None , run_params={}):
        
        if setup:
            self.setup()
            
        if run_identifier is not None:
            run_h5_group = self.h5data.create_group('{}'.format(run_identifier))
            self.save_dict(run_params,run_h5_group.name+'/')
        else:
            run_h5_group = self.h5data

        if self.params['do_plot']:
            nrows = 1#2 if self.params['scope_fft_mode'] else 1
            ncols=len(self.scope_channels)
            fig = plt.figure(figsize=(4*ncols,3*nrows), num='VNA Measurement')
            fig.clf()
            axs = fig.subplots(nrows=nrows,ncols=ncols,squeeze=False, sharex=True)



        self.scope_module.execute()
        self.scope.enable(1)
        self.device.session.sync()

        while 1:
            progress= self.scope_module.progress()
            records = self.scope_module.records()
            if progress < 1. or  records < self.params['scope_history_length']:
                logging.info(f'{self.name}: scope progress: {progress}, scope records: {records}/{self.params["scope_history_length"]}')
                time.sleep(0.3)
            else:
                break

        data = self.scope_module.read()[self.scope.wave]
        self.data_tmp=data

        self.scope.enable(0)

        if self.params['check_scope_record_flags']:
            self.check_scope_record_flags(data)

        totalsamples = data[0][0]['totalsamples']
        if self.params['scope_fft_mode']:
            x_axis = np.linspace(0, self.sampling_rate / 2, totalsamples)
        else:
            x_axis = 1/self.sampling_rate*np.arange(totalsamples)

        run_h5_group.create_dataset('x_axis', data = x_axis)

        for i, record in enumerate(data):
            run_h5_group.create_dataset(f'trace_{i:d}', data = record[0]['wave'])
            if self.params['do_plot']:
                for j,ch in enumerate(self.scope_channels):
                    y = record[0]['wave'][j,:]
                    if self.params['scope_fft_mode']:  
                            axs[0,j].plot(x_axis,magnitude_dB(np.abs(y)), label = f'trace {i:d}')
                            #axs[1,j].plot(x_axis,phase_unwrapped_and_offset(np.angle(y)), label = f'trace {i:d}')
                    else:
                            axs[0,j].plot(x_axis,y, label = f'trace {i:d}')                    
          
        self.h5data.flush()
        
        if self.params['do_plot']:
            for j,ch in enumerate(self.scope_channels):
                axs[0,j].set_title(f'Channel {ch:d}')
            if self.params['scope_fft_mode']: 
                axs[0,0].set_ylabel('Power (dB)')
                #axs[1,0].set_ylabel('phase (degrees)')
                for j,ch in enumerate(self.scope_channels):
                    #axs[1,j].set_xlabel('Frequency (Hz)')
                    axs[0,j].set_xlabel('Frequency (Hz)')
            else:
                axs[0,0].set_ylabel('Voltage (V)')
                for j,ch in enumerate(self.scope_channels):
                    axs[0,j].set_xlabel('Time (s)')
            
            fig_title, fig_save_fp = self.get_figure_title_and_path(appendix = run_identifier)
            fig.suptitle(fig_title)    
            fig.tight_layout()
            fig.savefig(fig_save_fp, bbox_inches='tight')
            fig.canvas.draw()
            fig.canvas.flush_events()  
        self.scope_module.close()


    def check_scope_record_flags(self,scope_records):
        """
        From https://docs.zhinst.com/zhinst-qcodes/en/latest/examples/scope_module.html
        Loop over all records and print a warning if an error bit in
        flags has been set.
        """
        num_records = len(scope_records)
        for index, record in enumerate(scope_records):
            record_idx = f"{index}/{num_records}"
            record_flags = record[0]["flags"]
            if record_flags & 1:
                logging.warning(f"Warning: Scope record {record_idx} flag indicates dataloss.")
            if record_flags & 2:
                logging.warning(f"Warning: Scope record {record_idx} indicates missed trigger.")
            if record_flags & 4:
                logging.warning(f"Warning: Scope record {record_idx} indicates transfer failure" \
                    "(corrupt data).")

            totalsamples = record[0]["totalsamples"]
            for wave in record[0]["wave"]:
                # Check that the wave in each scope channel contains
                # the expected number of samples.
                if len(wave) != totalsamples:
                    logging.warning(f"Scope record {index}/{num_records} size does not match totalsamples.")
          
        
        
if __name__=='__main__':
    
    logging.getLogger().setLevel(logging.INFO)
    
    from zhinst.qcodes import MFLI

    device = MFLI("DEV7700", "192.168.0.10", name="our_mfli")

    #device.sigins[0].range(0.1)

    s=device.scopes[0]
    #s.time(0)
    #s.length(20000)

    name = 'test'
 
    params = {}
    params['do_plot'] = True
    params['check_scope_record_flags'] = True
    params['scope_fft_mode'] = False
    params['scope_averager_weigth'] = 1
    params['scope_history_length'] = 1
    params['fft_window'] = 0

    meas = ZIScopeMeasurement(name,device, params=params) 
    
    print('Running scope meas')
    meas.run()
    meas.finish() 


    params = {}
    params['do_plot'] = True
    params['autoscale_plot'] = True
    params['update_time'] = 1 #s
    params['save_data_keys'] = ['grid','x', 'xpwr', 'xstddev', 'y', 'ypwr', 'ystddev']
    params['start'] = 6 #Hz
    params['stop'] = 20  #Hz
    params['samplecount'] = 100
    params['xmapping'] = 1 # linear (=0) or logarithmic (=1) 
    params['bandwidthcontrol'] = 0  # manually (=0), fixed bandwidth (=1), automatically (=2) https://docs.zhinst.com/labone_api_user_manual/modules/sweeper/index.html#controlling-how-the-sweeper-sets-the-demodulators-time-constant
    params['bandwidthoverlap'] = 0 # https://docs.zhinst.com/labone_api_user_manual/modules/sweeper/nodedoc.html?h=bandwidthoverlap#bandwidthoverlap
    params['scan'] = 0   # sequential scan mode (=0), binary scan mode (=1), bidirectional scan mode (=2), reverse scan mode (=3), https://docs.zhinst.com/labone_api_user_manual/modules/sweeper/index.html#controlling-the-scan-mode-the-selection-of-range-values
    params['loopcount'] = 1
    params['settling_time'] = 0 # https://docs.zhinst.com/labone_api_user_manual/modules/sweeper/index.html#specifying-the-sweepers-settling-time
    params['settling_inaccuracy'] = 0.001 
    params['averaging_tc'] = 0 #https://docs.zhinst.com/labone_api_user_manual/modules/sweeper/index.html#specifying-how-the-measurement-data-is-averaged
    params['averaging_sample'] = 1

    meas = ZISweeperMeasurement(name,device, params=params) 
    
    print('Running sweeper meas')
    meas.run(gridnode = device.oscs[0].freq, sample_nodes = [device.demods[0].sample])
    meas.finish() 

        