# -*- coding: utf-8 -*-
"""

Created on Dec 2024

@author: B.J.Hensen

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2024, Hensen Lab

All rights reserved.
"""
from drivers.ThorlabsScientificCamera import ThorlabsScientificCamera

# for live plotting:
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
# for threaded live plotting:
from multiprocessing import Process, Queue
import threading

def display(name, queue):

    frame = queue.get()
    p = pg.image(frame.image_buffer.T)
    
    def update():
        if not(queue.empty()):
            frame = queue.get()
            p.setImage(frame.image_buffer.T, autoRange=False,autoLevels=False,autoHistogramRange=False)
    
    timer = QtCore.QTimer()
    timer.timeout.connect(update)
    timer.start(0)
    pg.QtGui.QGuiApplication.exec_()


class ThorlabsScientificCameraThreadedLiveview(ThorlabsScientificCamera):
    """
    This is the qcodes driver for Thorlabs cameras. 
    """

    def _put_frame_in_queue(self,running,queue):
        while running.is_set():
            queue.put(self.get_frame())
        self.disarm()
        
    def stop_threaded_live_view(self):
        
        if hasattr(self, '_live_view_running'):
            self._live_view_running.clear()
            print('Live view stopped')
        else:
            print('Live view not running')
            
    def is_threaded_live_view_running(self):
        return hasattr(self, '_live_view_running') and self._live_view_running.is_set()
        
    def start_threaded_live_view(self):
        """
        Note: cannot be called using spyder cell magic, only by direct call in the console
        """
        
        if hasattr(self, '_live_view_running'):
            if self._live_view_running.is_set():
                print('Live view already running, call self.stop_live_view_threaded() first')
                return
            else:
                self._live_view_io_thread.join()
                self._live_view_running.set()
        else:
            self._live_view_running = threading.Event()
            self._live_view_running.set()
            
            self._live_view_queue = Queue()
            
        self.arm(100)
        self.issue_software_trigger()
        
        self._live_view_io_thread = threading.Thread(target=self._put_frame_in_queue, args=(self._live_view_running,self._live_view_queue))
        self._live_view_io_thread.start()
        
        if hasattr(self,'_live_view_plot_process'):
            if self._live_view_plot_process.is_alive():
                return
            else:
                self._live_view_plot_process.join()
        
        self._live_view_plot_process = Process(target=display, args=('bob',self._live_view_queue))
        self._live_view_plot_process.start()
        print('process started')

