"""
Created 2022

@author: B.J.Hensen

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2022, Hensen Lab

All rights reserved.

Based on earlier work by many authors, such as W. Pfaff, R. Heeres.

This module contains the abstract class Measurement.
The goal is that other measurements are classes based on
this one. This can provide benefits, because measurements
usually have common features, like saving and plotting data,
which then do not have to be written explicitly if implemented
in a common parent class.

Furthermore, measurements can be based on other measurements,
e.g. by just introducing another outer parameter sweep, which can
also be facilitated by an OO approach like this one.
"""

### imports
import sys,os,time,shutil,inspect
from stat import S_IREAD, S_IRGRP, S_IROTH
import logging
import numpy as np
import h5py

from .io import naming, hdf5_data_tools, tools

class Measurement:
    """
    Implements some common tasks such as data creation, so they need not be 
    implemented explicitly by all measurements
    """
       
    STACK_DIR = 'stack'
    FILES_DIR = 'files'

    def __init__(self, name, params=None,  save=True, cached=False, **kwargs):
        self.name = name
        self.cached = cached
        self.params = {}

        if params!=None:
            for k,v in params.items():
                self.params[k] = v  
        
        if save:
            self.dataset_idx = 0
            self.h5datapath = naming.MeasurementFilepathGenerator(**kwargs).generate(name)
            self.datafolder,self.filename = os.path.split(self.h5datapath)
            self.f_id = int(self.filename.split(naming.SEP)[0])
            if not os.path.isdir(self.datafolder):
                os.makedirs(self.datafolder)
            
            self.h5data = h5py.File(self.h5datapath, 'w', libver='latest')
            self.h5base = '/'
            self.h5data.attrs['name'] = self.name
            
            if self.cached:
                local_cache_folder = tools.get_config_folder()
                if not(os.path.exists(local_cache_folder)):
                    os.makedirs(local_cache_folder)
                self.cache_datapath = os.path.join(local_cache_folder,self.filename)
                self.h5data.attrs['cached_filepath'] = self.cache_datapath
                self.h5data.close()
                self.h5data = h5py.File(self.cache_datapath, 'w', libver='latest')
                
                self.h5base = '/'
                self.h5data.attrs['name'] = self.name
            
            self.save_params('params/')
                
            
            
        

    def __enter__(self):
        """ Method to allow the use of the with-as statement
        """
        return self
        
    def __exit__(self, type, value, traceback):
        """ Method to allow the use of the with-as statement
        """
        self.finish()
        
    def get_filename(self):
        return self.filename

    def get_f_id(self):
        return self.f_id

    def get_figure_title_and_path(self, appendix = None):

        return naming.get_figure_title_and_path(self.h5datapath, appendix = appendix)

    def save_stack(self, depth=2):
        '''
        save stack files, i.e. exectuted scripts, classes and so forth,
        into the subfolder specified by STACK_DIR.
        '''
        sdir = os.path.join(self.datafolder, self.STACK_DIR)
        if not os.path.isdir(sdir):
            os.makedirs(sdir)
        
        # pprint.pprint(inspect.stack())
        
        stack = inspect.stack()
        i = 0
        while stack[i][1][-3:] == '.py':
            shutil.copy(inspect.stack()[i][1], sdir)
            i+=1

    def save_dict(self,dic,path='/'):
        hdf5_data_tools.recursively_save_dict(dic,self.h5data,path)

    def add_file(self, filepath):
        '''
        save a file along the data. will be put into FILES_DIR
        '''
        fdir = os.path.join(self.datafolder, self.FILES_DIR)
        if not os.path.isdir(fdir):
            os.makedirs(fdir)
        
        shutil.copy(filepath, fdir+'/')

    def save_params(self, params_base):
        '''
        adds all measurement params contained in self.params as attributes
        to the basis data group of the hdf5 data object or any other
        specified object.
        '''
        self.save_dict(self.params,params_base)
        self.h5data.flush()

    def setup(self, save_params = False):
        if save_params:
            self.save_params('params-setup/')

    def run(self):
        pass
                
    
    def finish(self, save_params=False, save_stack=False, 
            stack_depth=4):
        '''
        Optionally saves params dictionary, cfg files, instrument settings and script stack, then closes the hd5 data object
        '''
        if save_params:
            self.save_params('params-post/')
            
        if save_stack:
            self.save_stack(depth=stack_depth)
      
        self.h5data.close()
        
        if self.cached:
            os.remove(self.h5datapath)
            shutil.move(self.cache_datapath,self.h5datapath)
        
        os.chmod(self.h5datapath, S_IREAD|S_IRGRP|S_IROTH) #make file read only

    def add_data(self, **kwargs):
        for k in kwargs:
            self.h5data.create_dataset(k, data = kwargs[k])

    def add_datapoints(self, **kwargs):
        for k,v in kwargs.items():
            v = np.array(v)
            if v.ndim > 1:
                raise ValueError('Only 1-dimensional data can be added')
            if v.ndim == 0:
                v = v.reshape((1,))
            if k in self.h5data.keys():
                ds = self.h5data[k]
                cur_len = ds.shape[0]
                ds.resize(cur_len+len(v), axis=0)
                ds[cur_len:] = v
            else:
                self.h5data.create_dataset(k, data = v, maxshape=(None,))


 
