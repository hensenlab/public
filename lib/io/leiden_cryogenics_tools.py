"""
Created 2023

@author: B.J.Hensen

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2023, Hensen Lab

All rights reserved.

"""


import os
import numpy as np
import pandas as pd

from lib.io import tools


def get_first_last_timestamps(fp, first_data_row):
    first_lines=[]
    with open(fp, 'r') as f:
        for i in range(first_data_row+1):
            first_lines.append(f.readline())
    first_timestamp = np.datetime64(first_lines[first_data_row].strip().split('\t')[0])
    last_line = tools.get_last_line_from_file(fp)
    last_timestamp = np.datetime64(last_line.strip().split('\t')[0])
    return first_timestamp, last_timestamp

def get_latest_readings(folder,log_type):   
    if log_type == 'avs':
        fn_contains = 'AVS'
        names_row = 2
    elif log_type == 'frontpanel':
        fn_contains = 'FP'
        names_row = 0
    else:
        raise ValueError(f"unknown log_type {log_type}, only 'avs' and 'frontpanel' supported")

    fp = tools.get_latest_file_from_folder(folder, fn_contains, '.dat')
    first_lines = []
    with open(fp, 'r') as f:
        for i in range(names_row+1):
            first_lines.append(f.readline())
    col_names =   first_lines[names_row].strip().split('\t')
    last_line = tools.get_last_line_from_file(fp)
    last_readings = last_line.strip().replace(',','.').split('\t')
    values = dict()
    for i,n in enumerate(col_names):
        if i==0:
            values[n] = np.datetime64(last_readings[i])
        else:
            values[n] = float(last_readings[i])
    return values


def load_data_from_timestamps(folder,start_datetime,end_datetime,log_type):
    if log_type == 'avs':
        fn_contains = 'AVS'
        first_data_row=5
        skiprows = [0,1,3,4]
    elif log_type == 'frontpanel':
        fn_contains = 'FP'
        first_data_row=1
        skiprows = []
    else:
        raise ValueError(f"unknown log_type {log_type}, only 'avs' and 'frontpanel' supported")

    fps = [] 
    timestamps = []
    for fn in os.listdir(folder):
        fp = os.path.join(folder,fn)
        if os.path.isfile(fp) and os.path.splitext(fp)[1]=='.dat' and fn_contains in fn:
            
           fts,lts = get_first_last_timestamps(fp, first_data_row)
           if np.isnan(fts) or np.isnan(lts):
               continue
           fps.append(fp)
           timestamps.append((fts,lts))
    timestamps = np.array(timestamps)
    fps = np.array(fps)
    
    start_in_fps = (timestamps[:,0]<=start_datetime) & (timestamps[:,1]>=start_datetime)
    end_in_fps = (timestamps[:,0]<=end_datetime) & (timestamps[:,1]>=end_datetime)
    fps_in_range = (timestamps[:,0]>start_datetime) & (timestamps[:,1]<end_datetime)
    load_fps = fps[start_in_fps | end_in_fps | fps_in_range]
    
    dfs = [pd.read_csv(fp, delimiter = '\t', skiprows=skiprows, header=0, decimal = ',', parse_dates=[0]) for fp in load_fps]
    df = pd.concat(dfs)
    return df