"""
Created 2024

@author: B.J.Hensen

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2024, Hensen Lab

All rights reserved.

"""

import numpy as np
import time, os
import h5py

import matplotlib
from matplotlib import pyplot as plt
from matplotlib.widgets import CheckButtons

from .measurement import Measurement

class LoggerMeasurement(Measurement):

    """
    Measurment class to plot and log parameters over time. Currently only handles floating point data. 
    Provide a gettable function to log, using the add_log_parameter fucntion

    """

    def __init__(self,name, log_parameters = None, **kw):
        """
        log_parameters: list of dicts {name:str, get_func:function, plot_factor:float, plot_label:str} to log.
        """
        super().__init__(__class__.__name__+ '_' + name,**kw)
        self.params['update_time'] = 1  #s
        self.params['do_plot'] = True
        self.params['pause_plot'] = False
        self.params['autoscale_plot_x'] = True
        self.params['autoscale_plot_y'] = True
        self.params['MAX_DATA_LEN'] = int(100e6)
        self.params['interactive_plot_settings'] = True
        self.params['interactive_plot_settings_keys'] = ['pause_plot','autoscale_plot_x','autoscale_plot_y']

        if log_parameters is not None:
            self.log_parameters = log_parameters
        else:
            self.log_parameters = []

        self.running=False 

    def add_log_parameter(self, name, get_func,plot_factor,plot_label):
        self.log_parameters.append(dict(name=name,get_func=get_func,plot_factor=plot_factor,plot_label=plot_label)) 

    def start_measurement_process(self):
        self.running = True

    def measurement_process_running(self):
        return self.running

    def stop_measurement_process(self, *args):
        self.running = False

    def print_measurement_progress(self):
        pass

    def callback(self,key):
        print(key)
        self.params[key] = not self.params[key]

    def run(self, setup=True,  rawdata_idx=1):
            
        if setup:
            self.setup()

        g = self.h5data

        dset_time = g.create_dataset(f'timestamps-{rawdata_idx:d}', (0,),maxshape=(None,), dtype=np.float64)
        dset_delta_time = g.create_dataset(f'delta_time-{rawdata_idx:d}', (0,),maxshape=(None,))

        dsets = []
        for d in self.log_parameters:
            dset = g.create_dataset(f'{d["name"]}-{rawdata_idx:d}', (0,),maxshape=(None,), dtype=np.float64)
            dsets.append(dset)

        if self.params['do_plot']:
            matplotlib.use('Qt5Agg')
            plt.close('all')
            self.fig,self.axs=plt.subplots(nrows=len(self.log_parameters), sharex=True, squeeze=False, figsize=(10,5*len(self.log_parameters)), num=self.name)
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
            self.axs[-1,0].set_xlabel('Time (s)')

            self.plot_lines = []
            for i,d in enumerate(self.log_parameters):
                self.axs[i,0].set_ylabel(d['plot_label'])
                self.axs[i,0].grid()
                self.plot_lines.append(self.axs[i,0].plot([0,1],[1,2],'.-')[0])
                self.axs[i,0].get_yaxis().get_major_formatter().set_useOffset(False)
            self.fig.canvas.mpl_connect('close_event', self.stop_measurement_process)
            if self.params['interactive_plot_settings']:
                #self.inset_ax = self.axs[0,0].inset_axes([0.9,0.9,0.1,0.4])
                fig,inset_ax = plt.subplots(1, num='logging_buttons')
                keys = self.params['interactive_plot_settings_keys']
                check = CheckButtons(inset_ax, keys, actives=[self.params[k] for k in keys])
                check.on_clicked(self.callback)
            fig_title, fig_save_fp = self.get_figure_title_and_path()
            self.fig.suptitle(fig_title)    
            self.fig.tight_layout()

        self.start_measurement_process()

        t=time.time()
        t0 = time.time()
        
        ii=0
        current_dset_length = 0
        
        while self.measurement_process_running():
    
            t=time.time()
            ii+=1
            current_dset_length+=1
         
            dset_time.resize((current_dset_length,))
            dset_time[-1] = t
            dset_delta_time.resize((current_dset_length,))
            dset_delta_time[-1] = t-t0

            for i,d in enumerate(self.log_parameters):
                dsets[i].resize((current_dset_length,))
                dsets[i][-1] = d['get_func']()
        
            self.h5data.flush()

            if self.params['do_plot'] and ii>2:
                if not(self.params['pause_plot']):
                    for i,d in enumerate(self.log_parameters):
                        self.plot_lines[i].set_data(dset_delta_time[:],dsets[i][:]*d['plot_factor'])
                        if self.params['autoscale_plot_x'] or ii<5:
                            self.axs[i,0].set(xlim=(np.nanmin(dset_delta_time[:]),np.nanmax(dset_delta_time[:])))
                        if self.params['autoscale_plot_y'] or ii<5:                                  
                            self.axs[i,0].set(ylim=(np.nanmin(dsets[i][:]*d['plot_factor']),np.nanmax(dsets[i][:]*d['plot_factor'])))
                            #self.axs[i,0].autoscale()
                    self.fig.canvas.draw()
                
                while time.time() < (t + self.params['update_time']):
                    self.fig.canvas.flush_events()
                    time.sleep(0.001)
                # plt.pause(self.params['update_time'])
                
            else:
                time.sleep(self.params['update_time'])


            if current_dset_length > self.params['MAX_DATA_LEN']:
                rawdata_idx += 1
                dset_time = g.create_dataset(f'timestamps-{rawdata_idx:d}', (0,),maxshape=(None,), dtype=np.float64)
                dset_delta_time = g.create_dataset(f'delta_time-{rawdata_idx:d}', (0,),maxshape=(None,))

                dsets = []
                for name, get_func in self.log_parameters:
                    dset = g.create_dataset(f'{name}-{rawdata_idx:d}', (0,),maxshape=(None,), dtype=np.float64)
                    dsets.append(dset)

                current_dset_length = 0
                self.h5data.flush()
        
        
        print('total datasets, items last database, last iteration:', rawdata_idx, current_dset_length, ii)
        self.h5data.flush()
        self.stop_measurement_process()

        
        self.fig.savefig(fig_save_fp, bbox_inches='tight')
