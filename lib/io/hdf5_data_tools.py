
"""
Created on 2022

@author: B.J.Hensen

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2022, Hensen Lab

All rights reserved.

Module providing handling of HDF5 data.

"""

import os
import time
import h5py
import logging
import numpy as np
import types

def recursively_load_dict(h5file, path='/'):
    """
    ....
    """
    ans = {}
    for k,v in h5file[path].attrs.items():
                ans[k] = v
    for key, item in h5file[path].items():
        if isinstance(item, h5py._hl.dataset.Dataset):
            ans[key] = item.value
        elif isinstance(item, h5py._hl.group.Group):
            ans[key] = recursively_load_dict(h5file, path + key + '/')
    return ans

def recursively_save_dict(dic, h5file, path='/'):
    """
    ....
    """
    for key, item in dic.items():
        save_object(str(key),item,h5file,path)


def save_object(name, obj, h5file, path = '/'):
    name=str(name)
    std_types = (float, int, np.int64, np.float64, str, type(None))
    list_types = (tuple, list)
    if isinstance(obj, std_types):
        #print(path)
        if not path in h5file:
            h5file.create_group(path)
        if isinstance(obj,type(None)):
            obj = 'none'
        if isinstance(obj, str) and '\x00' in obj:
            obj = 'none'
        h5file[path].attrs[name] = obj
    elif isinstance(obj, (tuple, list)):
        if all([isinstance(obj_i,std_types) for obj_i in obj]):
            if not path in h5file:
                h5file.create_group(path)
            if any([obj_i is None for obj_i in obj ]):
                obj = [obj_i if obj_i is not None else 'none' for obj_i in obj]
            h5file[path].attrs[name] = obj
        else:
            for i,obj_i in enumerate(obj):
                save_object(name + '_' + str(i),obj_i, h5file, path)
    elif isinstance(obj, np.ndarray):
        h5file[path + name] = obj
    elif isinstance(obj, dict):
        for key, item in obj.items():
            save_object(str(key),item,h5file,path + name + '/' )
    else:
        logging.warning('Cannot save object ', name, ' of type', type(obj))

def print_object(h5file, pre='', max_depth=10):
    if pre.count('\t') > max_depth:
        print(pre,'...at max depth')
    else:
        if hasattr(h5file,'attrs') and len(h5file.attrs)>0:
            print(pre,'Attrs:')
            for at in h5file.attrs:
                print(pre,'\t',at)
            print('')
        if hasattr(h5file,'keys'):
            for k in h5file.keys():
                print(pre,k,':')
                print_object(h5file[k], pre=pre+'\t', max_depth=max_depth)
        else:
            print(pre,h5file)