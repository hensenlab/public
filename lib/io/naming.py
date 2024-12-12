"""
Created 2022

@author: B.J.Hensen

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2022, Hensen Lab

All rights reserved.
"""


import os
import datetime
import logging
import numpy as np

BASE = os.curdir
EXT = 'hdf5'
SEP = '_'
DATE_FMT = '%Y%m%d'
TIME_FMT = '%H%M%S'
MAX_ID = 9999
USE_DATE_SUBDIRS = True
USE_TIME_SUBDIRS = False



def name_from_filepath(fp,separator = SEP):
    """
    From a filepath with filename structure id_datestring_timestring_measurmentname.extention, 
    return measurmentname only
    """
    fn = os.path.split(fp)[-1]
    fn_no_ext = os.path.splitext(fn)[0]
    fn_split = fn_no_ext.split(separator)
    return separator.join(fn_split[3:])

def filepath_from_id(target_id, **kwargs):
    """
    return filepath of valid measurment file in base_folder with given target_id. Valid measurement files
    are identified by having the right extention "ext", and the filename starting with a number <= "max_id", 
    followed by at least one "separator". 
    """
    return filepaths_from_ids([target_id],**kwargs)[0]

def filepaths_from_ids(target_ids, base_folder = BASE, ext=EXT,separator=SEP, max_id=MAX_ID):
    """
    return filepaths of valid measurment files in base_folder with given target_ids. Valid measurement files
    are identified by having the right extention "ext", and the filename starting with a number <= "max_id", 
    followed by at least one "separator". 
    """

    ids,fps = _get_ids_fps(base_folder,ext,separator, max_id)
    target_fps = []
    for target_id in target_ids:
        idxs = np.where(np.array(ids) == target_id)[0]
        if len(idxs) == 0:
            logging.warning('meas id {:d} not found in basefolder {:s}'.format(target_id,base_folder))
            target_fps.append(None)
        elif len(idxs) > 1:
            logging.warning(' Multiple meas id {:d} found in basefolder {:s}, returing last'.format(target_id,base_folder))
            target_fps.append(fps[idxs[-1]])
        else:
            target_fps.append(fps[idxs[0]])
    return target_fps

def latest(base_folder = BASE, ext=EXT, separator=SEP, max_id = MAX_ID, contains=None, return_all = False):
    """
    Returns the measurement id and filepath of with the largest id contained in base_folder. Valid measurement files
    are identified by having the right extention "ext", and the filename starting with a number <= "max_id", 
    followed by at least one "separator".
    - optionally, if "contains" is not None, filters the list on "contains" being in the filename

    """

    ids,fps = _get_ids_fps(base_folder,ext,separator, max_id,contains)
    if return_all:
        return ids, fps
    if len(ids) == 0:
        return 0, None
    idx = np.argmax(np.array(ids))
    return ids[idx], fps[idx]

def generate_filepath(name, **kw):
    """
    Convienience function to quickly generate a filepath, with filename structure id_datestring_timestring_measurmentname.extention

    see docstring for MeasurementFilepathGenerator for details.
    """

    mfpg = MeasurementFilepathGenerator(**kw)
    return mfpg.generate(name)

def get_figure_title_and_path(fp, appendix=None, fig_ext = '.png'):

    if appendix is not None:
        fig_fp = os.path.splitext(fp)[0] + '_' + appendix + fig_ext
        fn = os.path.split(fp)[1]
        fig_title = os.path.splitext(fn)[0] + ' ' + appendix
    else:
        fig_fp = os.path.splitext(fp)[0] + fig_ext
        fn = os.path.split(fp)[1]
        fig_title = os.path.splitext(fn)[0]
    return fig_title, fig_fp

class MeasurementFilepathGenerator:
    """
    Class to generate measurement filepaths, with filename structure id_datestring_timestring_measurmentname.extention 
    - Optinally generates datestring and timestring subdirectories.
    "extention", "datestring" and "timestring" format can be specified as keyword arguments on instantiation, defaulting to module defaults.
    
    Usage:
    Instantiate and repeatedly call generate(measurmentname) for more filepaths.


    """
    def __init__(self,base_folder = BASE, use_date_subfolders = USE_DATE_SUBDIRS, use_time_subfolders=USE_TIME_SUBDIRS, ext=EXT,date_format=DATE_FMT, time_format=TIME_FMT, separator = SEP):
        self.base_folder = base_folder
        self.use_date_subfolders = use_date_subfolders
        self.use_time_subfolders = use_time_subfolders
        self.date_format = date_format
        self.time_format  = time_format
        self.separator = separator
        self.ext=ext

        self.last_filepath = None

    def update_id(self):
        last_id, _ = latest(base_folder = self.base_folder,ext = self.ext, separator = self.separator)
        self.current_id = last_id+1

    def generate(self, name, force_update_id = False):
        now = datetime.datetime.now()
        if force_update_id or self.last_filepath is None:
            self.update_id()
        else:
            if os.path.exists(self.last_filepath):
                self.current_id += 1
        fn = _generate_filename(name, self.current_id, ext=self.ext, separator=self.separator, date_format=self.date_format, time_format=self.time_format, now = now)
        folder = _generate_folder(base_folder=self.base_folder,use_date_subfolders = self.use_date_subfolders, date_format=self.date_format,use_time_subfolders=self.use_time_subfolders, time_format=self.time_format , now = now)
        fp = os.path.join(folder,fn)
        self.last_filepath = fp
        return fp 

        

def _generate_filename(name, id, ext=EXT, separator=SEP, date_format=DATE_FMT, time_format=TIME_FMT, now = None):
    if now is None:
        now = datetime.datetime.now()

    return '{:d}'.format(id) + separator + now.strftime(date_format) + separator + now.strftime(time_format)+ separator + name + os.extsep + ext

def _generate_folder(base_folder=BASE,use_date_subfolders = USE_DATE_SUBDIRS, date_format=DATE_FMT,use_time_subfolders=USE_TIME_SUBDIRS, time_format=TIME_FMT, now = None):
    if now is None:
        now = datetime.datetime.now()
    folder = base_folder
    if use_date_subfolders:
        folder = os.path.join(folder,now.strftime(date_format))
    if use_time_subfolders:
        folder = os.path.join(folder,now.strftime(time_format))
    return folder
  


def _get_ids_fps(base_folder = BASE, ext=EXT, separator=SEP, max_id = MAX_ID, contains=None):
    """
    Returns a list of measurement id's and corresponding filepaths in base_folder. Valid measurement files
    are identified by having the right extention "ext", and the filename starting with a number <= "max_id", 
    followed by at least one "separator".
    - optionally, if "contains" is not None, filters the list on "contains" being in the filename

    """

    ids = []
    fps = []
    for folder, dns, fns in os.walk(base_folder):
        for fn in fns:
            fn_split_ext = os.path.splitext(fn)
            if fn_split_ext[1] == os.path.extsep+ext:
                if (contains is not None) and (not contains in fn_split_ext[0]):
                    continue
                fn_split = fn_split_ext[0].split(separator)
                try: 
                    cur_id = int(fn_split[0])
                    if cur_id <= max_id:
                        ids.append(cur_id)
                        fps.append(os.path.join(folder,fn))
                except ValueError:
                    continue
    return ids,fps

        



