# -*- coding: utf-8 -*-
"""
Created 2022

@author: B.J.Hensen

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2022, Hensen Lab

All rights reserved.
"""

import numpy as np

def phase_unwrapped_and_offset(Z):
    phase = np.angle(Z)
    x=np.arange(len(phase))
    y = np.unwrap(phase)/np.pi*180
    p = np.polyfit(x,y,1)
    
    return y - p[0]*x

def magnitude_dB(Z):
    return 20*np.log10(np.abs(Z))

def get_data_shape(f):
    valid_keys = []
    for k in f.keys():
        k_split = k.split('_')
        idxs = np.zeros(len(k_split),dtype=int)
        is_valid = True
        for i,ks in enumerate(k_split):
            try:
                idxs[i] = int(ks)
            except:
                is_valid = False
                break
        if is_valid:
            valid_keys.append(idxs)
    all_keys = np.array(valid_keys,dtype=int)
    return np.max(all_keys,axis=0)+1
    # # return all_keys
    # ndims = len(all_keys[0,:])
    # dim_max_idxs = np.zeros(ndims,dtype=int)
    
    # for dim in range(ndims):
    #     if dim+1 < ndims:
    #         if dim == 0:
    #             fltr = np.all(all_keys[:,1:] == 0,axis=1)
    #         else:
    #             fltr = np.all(all_keys[:,dim+1:] == 0,axis=1) & np.all(all_keys[:,:dim] == dim_max_idxs[:dim],axis=1)
    #     else:
    #         fltr = True
    #     dim_idxs = all_keys[fltr,dim]
    #     print(dim_idxs)
    #     dim_idxs_sorted = np.sort(dim_idxs)
    #     if all(np.diff(dim_idxs_sorted)) == 1:
    #         dim_max_idxs[dim] = dim_idxs_sorted[-1]
    #     else:
    #         #print(dim, dim_idxs_sorted)
    #         raise Exception('Inconsistent keys: missing indices, check file.')
    
    # return dim_max_idxs + 1
        
def fft(x,y):
    xfft = np.fft.fftfreq(x.shape[-1],x[1]-x[0])[1:int(len(y)/2)]
    yfft = np.fft.fft(y)[1:int(len(y)/2)]
    return xfft,yfft

def max_abs_fft(x,y):
    xfft,yfft = fft(x,y)
    return xfft[np.argmax(np.abs(yfft))]

def average_array(arr, averages):
    remainder = len(arr)%averages
    return np.mean(np.reshape(arr[:len(arr)-remainder],(-1,averages)),1)

def rebin_array(arr, averages):
    remainder = len(arr)%averages
    return np.sum(np.reshape(arr[:len(arr)-remainder],(-1,averages)),1)
