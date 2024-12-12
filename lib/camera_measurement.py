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
import pyqtgraph as pg
import logging

from lib.measurement import Measurement
from lib.io import naming


MAX_FRAMES_PER_DATASET = 1000 #20000 does not work

class CameraMeasurement(Measurement):
     
    def __init__(self, name, camera, **kwargs):
        super().__init__(__class__.__name__+ '_' + name,**kwargs)
        self.camera = camera
        
    def setup(self):
        pass
            
    def create_datasets(self,run_h5_group,dataset_idx,cur_dset_size):
        cur_dset_timestamp  = time.time()
        cur_dset_time_str = time.strftime(naming.DATE_FMT + '_' + naming.TIME_FMT)
        cur_frame_image_data = run_h5_group.create_dataset(f'frame_image-{dataset_idx:d}',
                                                                (self.camera.image_height(),self.camera.image_width(), cur_dset_size),
                                                                dtype=np.uint16, chunks=True)#, 
                                                               # compression='gzip')
        cur_frame_image_data.attrs['timestamp'] = cur_dset_timestamp
        cur_frame_image_data.attrs['time'] = cur_dset_time_str
        cur_frame_timestamp_data  = run_h5_group.create_dataset(f'frame_timestamp-{dataset_idx:d}',(cur_dset_size,),dtype=np.int64)
        cur_frame_count_data = run_h5_group.create_dataset(f'frame_counter-{dataset_idx:d}',(cur_dset_size,),dtype=np.int64)
        cur_aux_data = run_h5_group.create_dataset(f'aux_data-{dataset_idx:d}',(cur_dset_size,),dtype=np.float64)
        return cur_frame_image_data, cur_frame_timestamp_data, cur_frame_count_data, cur_aux_data

    def run(self, setup=True, run_identifier=None, update_callback=None, run_params={}):
        
        if setup:
            self.setup()
            
        if run_identifier is not None:
            run_h5_group = self.h5data.create_group('{}'.format(run_identifier))
            self.save_dict(run_params,run_h5_group.name+'/')
        else:
            run_h5_group = self.h5data
        
        frame_idx = 0
        dataset_frame_idx = 0
        dataset_idx = 0
        
        cur_dset_size = min([MAX_FRAMES_PER_DATASET, self.params['max_frames']])
        cur_frame_image_data, cur_frame_timestamp_data, cur_frame_count_data, cur_aux_data = self.create_datasets(run_h5_group, dataset_idx, cur_dset_size)
                
        self.camera.arm(self.params['frames_to_buffer'] )
        self.camera.issue_software_trigger()
        
        try:
            t0 = time.time()
            while 1:
                frame = self.camera.get_frame()
                if frame is None:
                    logging.warn('Camera returned empty frame, is image_poll_timout set correctly?')
                else:
                    cur_frame_image_data[:,:,dataset_frame_idx] = frame.image_buffer
                    cur_frame_timestamp_data[dataset_frame_idx] = frame.time_stamp_relative_ns_or_null
                    cur_frame_count_data[dataset_frame_idx] = frame.frame_count
                    
                    if self.params['do_plot'] and frame_idx % self.params['plot_update_frames'] ==0:
                        if frame_idx ==0:
                            self.p = pg.image(frame.image_buffer.T)
                        else:
                            self.p.setImage(frame.image_buffer.T, autoRange=False,autoLevels=False,autoHistogramRange=False)
                        pg.QtGui.QGuiApplication.processEvents()
                        
                    if frame_idx % 100 ==0 and frame_idx>0:
                        print('\r', f'{frame_idx/self.params["max_frames"]*100:.0f}%', end='')
                        self.h5data.flush()
                    if update_callback is not None:
                        cur_aux_data[dataset_frame_idx] = update_callback(cur_frame_count_data[dataset_frame_idx])
                    # self.h5data.flush()
                    frame_idx += 1
                    dataset_frame_idx += 1
                
                if (frame_idx >= self.params['max_frames']) or\
                        (time.time()-t0 >= self.params['max_duration']) or\
                            (self.params['do_plot'] and not(self.p.isVisible())):
                    break
                    
                if dataset_frame_idx >= MAX_FRAMES_PER_DATASET:
                    dataset_idx+=1
                    dataset_frame_idx = 0
                    cur_dset_size = min([MAX_FRAMES_PER_DATASET, self.params['max_frames']-dataset_idx*MAX_FRAMES_PER_DATASET])
                    cur_frame_image_data, cur_frame_timestamp_data, cur_frame_count_data, cur_aux_data = self.create_datasets(run_h5_group, dataset_idx, cur_dset_size)
                    
                
            print('Measurment finished')
            print(f'Percentage dropped frames: {(1-((frame_idx-1)/(cur_frame_count_data[dataset_frame_idx-1]-1)))*100:.2f}')
            
            if self.params['do_plot']:
                self.p.close()
                pg.QtGui.QGuiApplication.processEvents()
                
        finally:        
            self.camera.disarm()
            self.h5data.flush()
            
            
    def finish(self,save_camera_snapshot=True,update_camera_snapshot=True,**kwargs):
        if save_camera_snapshot:
             self.save_dict(self.camera.snapshot(update=update_camera_snapshot),'camera_snapshot/')
        super().finish(**kwargs)
        
