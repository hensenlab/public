"""
Created 2022

@author: Many

This work is licensed under the GNU Affero General Public License v3.0

"""

import os

import shutil
import json
import numpy as np
import logging

import re
import traceback

def get_config_folder():
    if 'APPDATA' in os.environ:
        confighome = os.environ['APPDATA']
    elif 'XDG_CONFIG_HOME' in os.environ:
        confighome = os.environ['XDG_CONFIG_HOME']
    else:
        confighome = os.path.join(os.environ['HOME'], '.config')
    config_folder = os.path.join(confighome, 'hensenlab')
    return config_folder


def find_all_by_regex(basefolder, regex, condition=None, **kw):
        foundlist = list()
        for folder, dns, fns in os.walk(basefolder):
            for fn in fns:
                fp = os.path.join(folder,fn)
                if re.match(regex,fn) and (not(condition) or (condition and condition(fp))):
                    foundlist.append(fp)
        return foundlist
    
    
def save_analysis_script(save_fp, analysis_script_fp=None):
    import zipfile
    import inspect
    from modulefinder import ModuleFinder
    
    if analysis_script_fp is None:
        analysis_script_fp = inspect.stack()[1][1]
    print(f'Saving stack for {analysis_script_fp}')
    
    #retrieve all qphoxlab modules that are used by the analysis script
    if 'ipynb' in os.path.splitext(analysis_script_fp)[1]:
        # we can't search an ipynb, so first convert to py
        module_search_fp = os.path.splitext(analysis_script_fp)[0] + '_converted_.py'
        convertNotebook(analysis_script_fp,module_search_fp)
    else:
        module_search_fp = analysis_script_fp
    finder = ModuleFinder(path=[get_hensenlab_folder()])
    finder.run_script(module_search_fp)
    fps_to_save = []
    for name, mod in finder.modules.items():
        mod_fp = str(mod.__file__)
        if os.path.isfile(mod_fp):
            fps_to_save.append(mod_fp)
    
    #let's save the analysis script, but let's comment the lines of code that call this function, if present.            
    s = open(analysis_script_fp,'r').read()
    s = s.replace('tools.save_analysis_script(','#tools.save_analysis_script(')
    s = s.replace('from lib.io import tools','#from lib.io import tools')
    
    save_fp = os.path.splitext(save_fp)[0] + '.zip'        
    with zipfile.ZipFile(save_fp,'w') as zf:
        #zf.write(calling_script_fp, os.path.split(calling_script_fp)[1])
        zf.writestr(os.path.split(analysis_script_fp)[1], s) # write analysis script to zip root folder
        for fp in fps_to_save:
            zf.write(fp,os.path.relpath(fp, get_hensenlab_folder())) # write the modules used to their relative paths
                  
def convertNotebook(notebookPath, modulePath):
    import nbformat
    from nbconvert import PythonExporter
    with open(notebookPath) as fh:
        nb = nbformat.reads(fh.read(), nbformat.NO_CONVERT)

    exporter = PythonExporter()
    source, meta = exporter.from_notebook_node(nb)

    with open(modulePath, 'w+') as fh:
        fh.writelines(source)#.encode('utf-8'))        


def get_hensenlab_folder():
    import hensenlab
    return os.path.split(os.path.split(hensenlab.__file__)[0])[0]
    
    
def save_stack(save_fp,source):
    save_fp = os.path.splitext(save_fp)[0]
    if os.path.isfile(source):
        folder,fn = os.path.split(source)
    elif os.path.isdir(source):
        folder = source
    else:
        raise ValueError(f'save_stack source {source} not understood')
    shutil.make_archive(save_fp, 'zip', root_dir = folder)

def save_hensenlab_stack(save_fp):
    save_stack(save_fp,get_hensenlab_folder())
   
# from https://stackoverflow.com/questions/26646362/numpy-array-is-not-json-serializable
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)
    
def save_dict_to_json(save_fp,dct):
    ext = '.json'
    save_fp = os.path.splitext(save_fp)[0] + ext
    
    with open(save_fp,'w') as f:
        json.dump(dct,f, cls=NumpyEncoder, indent=4)

def load_dict_from_json(fp):
    with open(fp,'r') as f:
        dct = json.load(f)
    return dct

def get_latest_file_from_folder(folder, pattern, ext):
    fns = os.listdir(folder)
    fps = [os.path.join(folder, basename) for basename in fns]
    fps = list(filter(lambda x: os.path.isfile(x) and os.path.splitext(x)[1] == ext and pattern in os.path.split(x)[1],fps))
    fps.sort(key=lambda x: os.path.getmtime(x))
    return fps[-1]

def get_last_line_from_file(fp):
    # https://stackoverflow.com/questions/46258499/how-to-read-the-last-line-of-a-file-in-python
    with open(fp, 'rb') as f:
        try:  # catch OSError in case of a one line file 
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b'\n':
                f.seek(-2, os.SEEK_CUR)
        except OSError:
            f.seek(0)
        last_line = f.readline().decode()
    return last_line

def get_notebook_name():


    import re
    import ipykernel
    import requests

    from requests.compat import urljoin


    from notebook.notebookapp import list_running_servers
    """
    Return the full path of the jupyter notebook.
    """
    kernel_id = re.search('kernel-(.*).json',
                          ipykernel.connect.get_connection_file()).group(1)
    servers = list_running_servers()
    for ss in servers:
        response = requests.get(urljoin(ss['url'], 'api/sessions'),
                                params={'token': ss.get('token', '')})
        print(response.text)
        for nn in json.loads(response.text):
            if nn['kernel']['id'] == kernel_id:
                relative_path = nn['notebook']['path']
                return os.path.join(ss['notebook_dir'], relative_path)