# -*- coding: utf-8 -*-
"""
Created 2023, based on earlier work in the Groeblacher lab, https://github.com/GroeblacherLab

@author: B.J.Hensen

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2023, Hensen Lab

All rights reserved.

"""

import time
import numpy as np
import matplotlib.pyplot as plt

from lib.measurement import Measurement

from analysis.data_tools import phase_unwrapped_and_offset, magnitude_dB


class VNAMeasurement(Measurement):
    def __init__(self, name, vna, **kwargs):
        super().__init__(__class__.__name__+ '_' + name,**kwargs)
        self.vna = vna
        
        self.params['do_plot'] = True
        self.params['vna_opc_update_time'] = 0.5
        
    def run(self, setup=True, run_identifier=None , run_params={},skip_update_channels = [], stop_cont_meas=True):
        
        if setup:
            self.setup()
            
        if run_identifier is not None:
            run_h5_group = self.h5data.create_group('{}'.format(run_identifier))
            self.save_dict(run_params,run_h5_group.name+'/')
        else:
            run_h5_group = self.h5data

        if self.params['do_plot']:
            n_traces = len(self.vna.traces)
            figname = 'VNA Measurement' if run_identifier is None else f'VNA Measurement {run_identifier}'
            fig = plt.figure(figsize=(4*n_traces,5), num=figname)
            fig.clf()
            axs = fig.subplots(nrows=2,ncols = n_traces,squeeze=False, sharex=True)


        updated_channels = skip_update_channels.copy()
        try:
            if stop_cont_meas:
                self.vna.cont_meas.set(False)

            for i,trace in enumerate(self.vna.traces):
                do_update = trace._ch not in updated_channels
                
                trace.update_lin_traces()
                freq = np.array(trace.trace_mag_phase.setpoints[0][0])
                
                ###new does not work quite well
                # if do_update:
                #     trace.start_sweep()
                #     print(f'taking {trace.avg():d} averages')
                #     for j in range(trace.avg()):
                #         if j>0: print(i, end=' ')
                #         trace.init_single()
                #         while not self.vna.operation_complete():
                #             if self.params['do_plot']:
                #                 t0 = time.time()
                #                 while time.time()-t0 < self.params['vna_opc_update_time']:
                #                     fig.canvas.flush_events()
                #                     time.sleep(0.001)
                #             else:
                #                 time.sleep(self.params['vna_opc_update_time'])
                # data = trace._get_sweep_data(force_polar=True, update=False)   
                ###
                
                ###old
                data = trace._get_sweep_data(force_polar=True, update=do_update)
                ###
                
                updated_channels.append(trace._ch)
                
                g = run_h5_group.create_group(trace.name)
                g.create_dataset('frequency', data = freq)
                vna_parameter = trace.vna_parameter.get()
                g.create_dataset(vna_parameter, data = data)
                if self.params['do_plot']:
                    axs[0,i].set_title(vna_parameter)
                    axs[0,i].plot(freq/1e9,magnitude_dB(data), label = vna_parameter)
                    axs[1,i].plot(freq/1e9,phase_unwrapped_and_offset(data), label = vna_parameter)
                    axs[1,i].set_xlabel('Frequency (GHz)')
                self.h5data.flush()
        finally:
            if stop_cont_meas:
                self.vna.cont_meas.set(True)
        
        if self.params['do_plot']:
            axs[0,0].set_ylabel('Power (dB)')
            axs[1,0].set_ylabel('phase (degrees)')
            
            fig_title, fig_save_fp = self.get_figure_title_and_path(appendix = run_identifier)
            fig.suptitle(fig_title)    
            fig.tight_layout()
            fig.savefig(fig_save_fp, bbox_inches='tight')
            fig.canvas.draw()
            fig.canvas.flush_events()
            
            
    def finish(self,save_vna_snapshot=True,update_vna_snapshot=True,**kwargs):
        if save_vna_snapshot:
             self.save_dict(self.vna.snapshot(update=update_vna_snapshot),'vna_snapshot/')
        super().finish(**kwargs)
        

class VNACurrentMeasurement(VNAMeasurement):
    def __init__(self, name, vna, current_source, **kwargs):
        super().__init__(name, vna, **kwargs)
        self.current_source = current_source
        
    def finish(self, save_current_source_snapshot=True, **kwargs):
        if save_current_source_snapshot:
             self.save_dict(self.current_source.snapshot(update=True),'current_source_snapshot/')
        super().finish(**kwargs)
        