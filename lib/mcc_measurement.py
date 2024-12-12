"""
Created 2024

@author: B.J.Hensen

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2024, Hensen Lab

All rights reserved.
"""

import numpy as np
import scipy.signal
import time


from mcculw.enums import Status

import matplotlib
from matplotlib import pyplot as plt

from .measurement import Measurement

class MCCMeasurement(Measurement):


    def __init__(self, name, mcc_ins, **kw):
        """
        log_parameters: list of dicts {name:str, get_func:function, plot_factor:float, plot_label:str} to log.
        """
        super().__init__(__class__.__name__+ '_' + name,**kw)

        self.mcc_ins = mcc_ins

        self.params['update_time'] = 0.5  #s
        self.params['do_plot'] = True
        self.average_idx = -1

    def setup(self):

        self.num_chans, \
        self.total_samples, \
        self.memhandle, \
        self.ctypes_array, \
        self.scan_options = self.mcc_ins.prepare_ai_scan(self.params['low_chan'], 
                                                         self.params['high_chan'],
                                                         self.params['samples'],
                                                         background=True)
        self.ai_range = self.mcc_ins.ai_info.supported_ranges[self.params['ai_range_idx']]

        if self.params['do_plot']:
            matplotlib.use('Qt5Agg')

            self.fig = plt.figure(num = self.name)
            self.fig.clf()
            self.ax = self.fig.add_subplot(1,1,1)

            fig_b,ax_b = plt.subplots(1, num='meas_stop',figsize=(3.2,1))
            ax_b.set_title('close me to stop the measurement')
            fig_b.tight_layout()

    def run(self, setup=True, raw_data_idx=0):
        print('                                     ',end='')
        
        self.mcc_ins.start_ai_scan(self.params['low_chan'], 
                                   self.params['high_chan'], 
                                   self.total_samples, 
                                   self.params['rate'],
                                   self.ai_range, 
                                   self.memhandle, 
                                   self.scan_options)

        
        while 1: 
            if self.params['do_plot']:
                t=time.time()
                while time.time() < (t + self.params['update_time']):
                    self.fig.canvas.flush_events()
                    time.sleep(0.001)
            else:
                time.sleep(self.params['update_time'])
            status, curr_count, curr_index = self.mcc_ins.get_ai_status()
            # print(f'{curr_count}/{total_count}', end='\r')
            print('\r', f'{raw_data_idx}: {curr_count/self.total_samples*100:.0f}%', end='')

            if status == Status.IDLE or (self.params['do_plot'] and not(plt.fignum_exists('meas_stop'))):
                self.mcc_ins.stop_ai_background()
                break
        
        self.cur_data = self.mcc_ins.reshape_ai_array(self.ctypes_array, 
                                                      self.num_chans, 
                                                      self.total_samples)

        data_dict = {f'raw_timetrace-{raw_data_idx:d}': self.cur_data}
        self.add_data(**data_dict)
        self.h5data.flush()
        if self.params['do_plot']:
            self.update_plot(raw_data_idx)
        

    def update_plot(self, raw_data_idx):
        if self.params['plot_type'] not in ['timetrace', 'psd']:
                raise Exception(f'Unknown plot_type {self.params["plot_type"]}, choose timetrace or psd')
        fig_title, fig_fp = self.get_figure_title_and_path()
        if self.average_idx < 1:
            if raw_data_idx != 0:
                 fig_title += f' {raw_data_idx}'
            self.lines = []
            if self.params['plot_type'] == 'timetrace':
                self.sum_data = self.cur_data
                self.t = np.linspace(0, self.params['samples']/self.params['rate'], self.params['samples'])
                for ch in range(self.num_chans):
                    self.lines.append(self.ax.plot(self.t,self.cur_data[:,ch], label = f'ch {ch:d}')[0])
                self.ax.set(xlabel = 'Time (s)', ylabel = 'Signal (V)', title = fig_title)
                self.ax.legend()
            elif self.params['plot_type'] == 'psd':
                self.f,Pxx = scipy.signal.periodogram(self.cur_data, fs = self.params['rate'], axis=0, window = self.params['fft_window'])
                self.sum_Pxx = Pxx
                for ch in range(self.num_chans):
                    self.lines.append(self.ax.loglog(self.f[1:],np.sqrt(Pxx[1:,ch]), label = f'ch {ch:d}')[0])
                self.ax.set(xlabel = 'Frequency (Hz)', ylabel = 'PSD (V/sqrtHz)', title = fig_title)
                self.ax.legend()
        else:
            if self.params['plot_type'] == 'timetrace':
                self.sum_data += self.cur_data
                for ch in range(self.num_chans):
                    self.lines[ch].set_ydata(self.sum_data[:,ch]/(self.average_idx+1))
            elif self.params['plot_type'] == 'psd':
                f,Pxx = scipy.signal.periodogram(self.cur_data, fs = self.params['rate'], axis=0, window = self.params['fft_window'])
                self.sum_Pxx += Pxx
                for ch in range(self.num_chans):
                    self.lines[ch].set_ydata(np.sqrt(self.sum_Pxx[1:,ch]/(self.average_idx+1)))

        self.fig.tight_layout()
        self.fig.canvas.draw()
        plt.pause(0.001)
        self.fig.savefig(fig_fp, bbox_inches='tight')

    def run_averaged(self):

        while 1:
            self.average_idx+=1
            self.run(setup=False, raw_data_idx=self.average_idx)
            if self.average_idx==self.params['averages']-1 or not(plt.fignum_exists('meas_stop')):
                break

    def finish(self, **kw):
        if self.params['do_plot'] and self.average_idx > 0:
            if self.params['plot_type'] == 'timetrace':
                self.add_data(t=self.t,sum_data = self.sum_data)
            elif self.params['plot_type'] == 'psd':
                self.add_data(f=self.f,sum_Pxx = self.sum_Pxx)
        super().finish(**kw)
        if self.params['do_plot']:
            plt.close('meas_stop')



class MCCLoggingMeasurement(Measurement):

    def __init__(self, name, mcc_ins, **kw):
        """
        log_parameters: list of dicts {name:str, get_func:function, plot_factor:float, plot_label:str} to log.
        """
        super().__init__(name,**kw)

        self.mcc_ins = mcc_ins

        self.params['do_plot'] = True
        self.params['write_chunk_size'] = 2**12
        self.params['MAX_DATA_LEN'] = 2**63 #max size is 2**64, stay below that

    def setup(self):
        
        self.params['samples'] = 4*self.params['write_chunk_size'] 
        self.params['update_time'] = np.min([self.params['rate']*self.params['samples'],1])  #s

        self.num_chans, \
        self.total_samples, \
        self.memhandle, \
        self.ctypes_array, \
        self.scan_options = self.mcc_ins.prepare_ai_scan(self.params['low_chan'], 
                                                         self.params['high_chan'],
                                                         self.params['samples'],
                                                         background=True,
                                                         continuous = True)
        
        # assert self.total_samples > 10*self.params['write_chunk_size']
        # assert self.params['update_time']*self.params['rate'] < self.params['samples']

        self.ai_range = self.mcc_ins.ai_info.supported_ranges[self.params['ai_range_idx']]
        
        if self.params['do_plot']:
            matplotlib.use('Qt5Agg')
    
            self.fig,ax = plt.subplots(1, num='cont_meas_stop',figsize=(3.2,1))
            ax.set_title('close me to stop the measurement')
            self.fig.tight_layout()

    def run(self, setup=True):

        self.mcc_ins.start_ai_scan(self.params['low_chan'], 
                                   self.params['high_chan'], 
                                   self.total_samples, 
                                   self.params['rate'],
                                   self.ai_range, 
                                   self.memhandle, 
                                   self.scan_options)


        rawdata_idx = 0
        cur_dset = self.h5data.create_dataset(f'data-{rawdata_idx:d}', (0,self.num_chans),maxshape=(None,self.num_chans), dtype=np.float64)
        self.h5data.swmr_mode = True # https://docs.h5py.org/en/stable/swmr.html
        status = Status.IDLE
        # Wait for the scan to start fully
        while status == Status.IDLE:
            status, _, _ = self.mcc_ins.get_ai_status()

        prev_count = 0
        prev_index = 0
        current_dset_length = 0
        while 1:
            # Get the latest counts
            status, curr_count, curr_index = self.mcc_ins.get_ai_status()
            new_data_count = curr_count - prev_count
            if new_data_count > self.params['write_chunk_size']:
                if status == Status.IDLE or new_data_count > self.total_samples:
                    #buffer overrun: print an error and stop writing
                    self.mcc_ins.stop_ai_background()
                    raise Exception('A buffer overrun occurred')
                if prev_index + new_data_count > self.total_samples - 1:
                    first_chunk_size = self.total_samples - prev_index
                    second_chunk_size = new_data_count - first_chunk_size
                    new_data_0 = np.reshape(self.ctypes_array[prev_index:self.total_samples],(-1,self.num_chans))
                    new_data_1 = np.reshape(self.ctypes_array[0:second_chunk_size],(-1,self.num_chans))
                    new_data = np.concatenate((new_data_0, new_data_1),axis=0)
                else:
                    new_data = np.reshape(self.ctypes_array[prev_index:prev_index+new_data_count],(-1,self.num_chans))
                
                new_data_samples = new_data.shape[0]
                
                cur_dset.resize((current_dset_length+new_data_samples,self.num_chans))
                cur_dset[current_dset_length:,:] = new_data
                current_dset_length += new_data_samples
                self.h5data.flush()

                if current_dset_length > self.params['MAX_DATA_LEN']:
                    rawdata_idx += 1
                    cur_dset = self.h5data.create_dataset(f'data-{rawdata_idx:d}', (0,self.num_chans),maxshape=(None,self.num_chans), dtype=np.float64)
                    current_dset_length = 0
                    self.h5data.flush()
                
                prev_count = curr_count
                prev_index += new_data_count
                prev_index %= self.total_samples
                
                
            if self.params['do_plot'] and not(plt.fignum_exists('cont_meas_stop')):
                self.mcc_ins.stop_ai_background()
                break
            
            if self.params['do_plot']:
                t=time.time()
                while time.time() < (t + self.params['update_time']):
                    self.fig.canvas.flush_events()
                    time.sleep(0.001)
            else:
                time.sleep(self.params['update_time'])
            
            


    def finish(self, **kw):
        super().finish(**kw)
        if self.params['do_plot']:
            plt.close('meas_stop')