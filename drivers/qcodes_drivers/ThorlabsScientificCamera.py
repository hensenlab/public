# -*- coding: utf-8 -*-
"""
Created on Dec 2024

@author: B.J.Hensen

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2024, Hensen Lab

All rights reserved.

To install the Thorlabs SDK:

- Install ThorCam™ software https://www.thorlabs.com/software_pages/ViewSoftwarePage.cfm?Code=ThorCam 
- Find SDK install instructions in e.g. # C:/Program Files/Thorlabs/Scientific Imaging/Scientific Camera Support/Scientific_Camera_Interfaces.zip/Scientific Camera Interfaces/Python_README.txt
- Copy the SDK dll's into the folder from where the calling script is run, see thorlabs_camera_example.py

"""

import time
from qcodes.utils.helpers import create_on_off_val_mapping
from qcodes.instrument.base import Instrument

from qcodes.utils.validators import Numbers, Ints

from thorlabs_tsi_sdk.tl_camera import TLCameraSDK, ROI


class ThorlabsScientificCamera(Instrument):
    """
    This is a qcodes driver for Thorlabs Scientific cameras. 
    """
    
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

        self.sdk = TLCameraSDK()
        

        available_cameras = self.sdk.discover_available_cameras()
        if len(available_cameras) < 1:
            print("no cameras detected")

        self.camera = self.sdk.open_camera(available_cameras[0])     
        self.camera.name = name

        exposure_time_range = self.camera.exposure_time_range_us
        self.add_parameter(name = 'exposure_time',
                           unit = 's',
                           get_cmd = lambda: self.camera.exposure_time_us,
                           set_cmd = lambda x: setattr(self.camera,'exposure_time_us',x),
                           set_parser = lambda x: int(x*1e6),
                           get_parser = lambda x: x*1e-6,
                           vals=Numbers(min_value=exposure_time_range[0]*1e-6,
                                        max_value= exposure_time_range[1]*1e-6))
                               
        self.add_parameter(name = 'image_poll_timeout',
                           unit = 's',
                           docstring = 'get_pending_frame_or_null() will block up to this time before returning',
                           get_cmd = lambda: self.camera.image_poll_timeout_ms,
                           set_cmd = lambda x: setattr(self.camera,'image_poll_timeout_ms',x),
                           set_parser = lambda x: int(x*1e3),
                           get_parser = lambda x: x*1e-3)

        self.add_parameter(name = 'frame_time',
                           unit = 's',
                           docstring = 'Time required for a frame to be exposed and read out from the sensor.',
                           get_cmd = lambda: self.camera.frame_time_us,
                           get_parser = lambda x: x*1e-6)

        self.add_parameter(name = 'measured_frame_rate',
                           unit = 'fps',
                           docstring = 'Gets the current rate of frames that are delivered to the host computer. The frame rate can be affected by the\
                                        performance capabilities of the host computer and the communication interface.',
                           get_cmd = self.camera.get_measured_frame_rate_fps)

        self.add_parameter(name = 'readout_time',
                           unit = 's',
                           docstring = 'Time required to readout data from image sensor.',
                           get_cmd = lambda: self.camera.sensor_readout_time_ns,
                           get_parser = lambda x: x*1e-9)

        

        self.add_parameter(name = 'trigger_polarity',
                           get_cmd = lambda: self.camera.trigger_polarity,
                           set_cmd = lambda x: setattr(self.camera,'trigger_polarity',x),
                           val_mapping = {'rising':0,'falling':1})
        if False:
            self.add_parameter(name = 'data_rate',
                               docstring = 'This property sets or gets the sensor-level data rate. Scientific-CCD cameras offer data rates of 20MHz or\
                                             40MHz. Compact-scientific cameras offer FPS30 or FPS50, which are frame rates supported by the camera when\
                                             doing full-frame readout. The actual rate can vary if a region of interest (ROI) or binning is set or if the\
                                             host computer cannot keep up with the camera.',
                               get_cmd = lambda: self.camera.data_rate,
                               set_cmd = lambda x: setattr(self.camera,'data_rate',x),
                               val_mapping = {'FPS_30':2,'FPS_50':3})

        self.add_parameter(name = 'sensor_pixel_width',
                           unit = 'm',
                           docstring = 'This property provides the physical width of a single light-sensitive photo site on the sensor.',
                           get_cmd = lambda: self.camera.sensor_pixel_width_um,
                           get_parser = lambda x: x*1e-6)
        self.add_parameter(name = 'sensor_pixel_height',
                           unit = 'm',
                           docstring = 'This property provides the physical width of a single light-sensitive photo site on the sensor.',
                           get_cmd = lambda: self.camera.sensor_pixel_height_um,
                           get_parser = lambda x: x*1e-6)

        self.add_parameter(name = 'bit_depth',
                           docstring = 'The number of bits to which a pixel value is digitized on a camera.\
                                         In the image data that is delivered to the host application, the bit depth indicates how many of the lower bits\
                                         of each 16-bit ushort value are relevant.\
                                         While most cameras operate at a fixed bit depth, some are reduced when data bandwidth limitations would\
                                         otherwise restrict the frame rate. Please consult the camera manual and specification for details about a\
                                         specific model.',
                           get_cmd = lambda: self.camera.bit_depth,
                           vals=Ints())

        frame_rate_control_value_range = self.camera.frame_rate_control_value_range
        self.add_parameter(name = 'frame_rate_control_value',
                           docstring= 'The frame rate control adjusts the frame rate of the camera independent of exposure time, within certain\
                                        constraints. For short exposure times, the maximum frame rate is limited by the readout time of the sensor.\
                                        For long exposure times, the frame rate is limited by the exposure time.',
                           unit = 'fps',
                           get_cmd = lambda: self.camera.frame_rate_control_value,
                           set_cmd = lambda x: setattr(self.camera,'frame_rate_control_value',x),
                           vals=Numbers(min_value=frame_rate_control_value_range[0],
                                        max_value= frame_rate_control_value_range[1]))

        self.add_parameter(name = 'frame_rate_control_enabled',
                   docstring= 'The frame rate control adjusts the frame rate of the camera independent of exposure time, within certain\
                                constraints. For short exposure times, the maximum frame rate is limited by the readout time of the sensor.\
                                For long exposure times, the frame rate is limited by the exposure time.',
                   get_cmd = lambda: self.camera.is_frame_rate_control_enabled,
                   set_cmd = lambda x: setattr(self.camera,'is_frame_rate_control_enabled',x),
                   val_mapping=create_on_off_val_mapping())


        self.add_parameter(name = 'usb_port_type',
                           docstring = 'Return wether the device is connected to\
                            a USB 1.0/1.1 port (1.5 Mbits/sec or 12 Mbits/sec),\
                            a USB 2.0 port (480 Mbits/sec),\
                            or a USB 3.0 port (5000 Mbits/sec).',
                           get_cmd = lambda: self.camera.usb_port_type,
                           val_mapping = {'USB 1.0':0,'USB2.0':1,'USB 3.0':2,})
            
        self.add_parameter(name = 'communication_interface',
                           docstring = 'Returns the computer interface type, such as USB, GigE, or CameraLink.',
                           get_cmd = lambda: self.camera.communication_interface,
                           val_mapping = {'GIG_E':0,'LINK':1,'USB':2,})

        self.add_parameter(name = 'camera_sensor_type',
                           docstring = '',
                           get_cmd = lambda: self.camera.camera_sensor_type,
                           val_mapping = {'MONOCHROME':0,'BAYER':1,'MONOCHROME_POLARIZED':2,})
        
        if self.camera_sensor_type() == 'BAYER':

            self.add_parameter(name = 'color_filter_array_phase',
                               docstring = """
                               The FILTER_ARRAY_PHASE enumeration lists all the possible values that a pixel in a Bayer pattern color arrangement 
                               could assume.
    
                               The classic Bayer pattern is::
    
                                   -----------------------
                                   |          |          |
                                   |    R     |    GR    |
                                   |          |          |
                                   -----------------------
                                   |          |          |
                                   |    GB    |    B     |
                                   |          |          |
                                   -----------------------
    
                               where:
                               
                               - R = a red pixel
                               - GR = a green pixel next to a red pixel
                               - B = a blue pixel
                               - GB = a green pixel next to a blue pixel
                              
                               The primitive pattern shown above represents the fundamental color pixel arrangement in a Bayer pattern
                               color sensor.  The basic pattern would extend in the X and Y directions in a real color sensor containing
                               millions of pixels.
                              
                               Notice that the color of the origin (0, 0) pixel logically determines the color of every other pixel.
                              
                               It is for this reason that the color of this origin pixel is termed the color "phase" because it represents
                               the reference point for the color determination of all other pixels.
                              
                               Every TSI color camera provides the sensor specific color phase of the full frame origin pixel as a discoverable
                               parameter.
    
                               """,
                               get_cmd = lambda: self.camera.color_filter_array_phase,
                               val_mapping = {'BAYER_RED':0,'BAYER_BLUE':1,'GREEN_LEFT_OF_RED':2,'GREEN_LEFT_OF_BLUE':3})
                
    
            self.add_parameter(name = 'camera_color_correction_matrix_output_color_space',
                               get_cmd = lambda: self.camera.camera_color_correction_matrix_output_color_space)


       
        
        if self.camera_sensor_type() == 'MONOCHROME_POLARIZED':

            self.add_parameter(name = 'polar_phase',
                               docstring = """
                                            The possible polarization angle values (in degrees) for a pixel in a polarization sensor. The polarization phase
                                            pattern of the sensor is::
    
                                                -------------
                                                | + 0 | -45 |
                                                -------------
                                                | +45 | +90 |
                                                -------------
    
                                            The primitive pattern shown above represents the fundamental polarization phase arrangement in a polarization
                                            sensor. The basic pattern would extend in the X and Y directions in a real polarization sensor containing millions
                                            of pixels. Notice that the phase of the origin (0, 0) pixel logically determines the phase of every other pixel.
                                            It is for this reason that the phase of this origin pixel is termed the polarization "phase" because it represents
                                            the reference point for the phase determination of all other pixels.
                                            """,
                               get_cmd = lambda: self.camera.polar_phase,
                               val_mapping = {'PolarPhase0':0,'PolarPhase45':1,'PolarPhase90':2,'PolarPhase135':3})


        if self.camera.is_eep_supported:
            self.add_parameter(name = 'eep_status',
                               docstring = """
                                            Equal Exposure Pulse (EEP) mode is an LVTTL-level signal that is active during the time when all rows have been\
                                            reset during rolling reset, and the end of the exposure time (and the beginning of rolling readout). The signal\
                                            can be used to control an external light source that will be on only during the equal exposure period,\
                                            providing the same amount of exposure for all pixels in the ROI.\
                                            When EEP mode is disabled, the status will always be EEP_STATUS.OFF.\
                                            EEP mode can be enabled, but, depending on the exposure value, active or inactive.\
                                            If EEP is enabled in bulb mode, it will always give a status of BULB.',
                                            """,
                               get_cmd = lambda: self.camera.eep_status,
                               val_mapping = {'DISABLED':0,'ENABLED_ACTIVE':1,'ENABLED_INACTIVE':2,'ENABLED_BULB':3})
    
            self.add_parameter(name = 'eep_enabled',
                               docstring= 'Equal Exposure Pulse (EEP) mode is an LVTTL-level signal that is active between the time when all rows have\
                                            been reset during rolling reset, and the end of the exposure time (and the beginning of rolling readout). The\
                                            signal can be used to control an external light source that will be triggered on only during the equal exposure\
                                            period, providing the same amount of exposure for all pixels in the ROI.\
                                            Please see the camera specification for details on EEP mode.',
                               get_cmd = lambda: self.camera.is_eep_enabled,
                               set_cmd = lambda x: setattr(self.camera,'is_eep_enabled',x),
                               val_mapping=create_on_off_val_mapping())


        self.add_parameter(name = 'operation_mode',
                           docstring = 'Thorlabs scientific cameras can be software- or hardware-triggered.\n \
                                         - To run continuous-video mode, set frames_per_trigger to zero and operation_mode to SOFTWARE_TRIGGERED.\n\
                                         - To trigger frames using the hardware trigger input, set operation_mode to HARDWARE_TRIGGERED. In this mode, \
                                         the exposure_time is used to determine the length of the exposure.\n\
                                         - To trigger frames using the hardware trigger input and to determine the exposure length with that signal, set\
                                         operation_mode to BULB.',
                           get_cmd = lambda: self.camera.operation_mode,
                           set_cmd = lambda x: setattr(self.camera,'operation_mode',x),
                           val_mapping = {'SOFTWARE_TRIGGERED':0,'HARDWARE_TRIGGERED':1, 'BULB':2})

        gain_range = self.camera.gain_range
        self.add_parameter(name = 'gain',
                           unit = 'dB',
                           get_cmd = lambda: self.camera.gain,
                           set_cmd = lambda x: setattr(self.camera,'gain',x),
                           get_parser = self.camera.convert_gain_to_decibels,
                           set_parser = self.camera.convert_decibels_to_gain,
                           vals = Numbers(min_value=self.camera.convert_gain_to_decibels(gain_range[0]),
                                          max_value= self.camera.convert_gain_to_decibels(gain_range[1])))


        black_level_range = self.camera.black_level_range
        self.add_parameter(name = 'black_level',
                           docstring = 'Black level adds an offset to pixel values.',
                           unit = 'camera_dependent',
                           get_cmd = lambda: self.camera.black_level,
                           set_cmd = lambda x: setattr(self.camera,'black_level',x),
                           vals=Ints(min_value=black_level_range[0],
                                     max_value= black_level_range[1]))



        binx_range = self.camera.binx_range
        self.add_parameter(name = 'binx',
                           unit = 'pixels',
                           get_cmd = lambda: self.camera.binx,
                           set_cmd = lambda x: setattr(self.camera,'binx',x),
                           vals=Ints(min_value=binx_range[0],
                                     max_value= binx_range[1]))
        biny_range = self.camera.biny_range
        self.add_parameter(name = 'biny',
                           unit = 'pixels',
                           get_cmd = lambda: self.camera.biny,
                           set_cmd = lambda x: setattr(self.camera,'biny',x),
                           vals=Ints(min_value=biny_range[0],
                                     max_value= biny_range[1]))

        self.add_parameter(name = 'hot_pixel_correction',
                           docstring= 'Due to variability in manufacturing, some pixels have inherently higher dark current\
                                    which manifests as abnormally bright pixels in images, typically visible with longer exposures.\
                                    Hot-pixel correction identifies hot pixels and then substitutes a calculated value based\
                                    on the values of neighboring pixels in place of hot pixels. This property enables or disables\
                                    hot-pixel correction. If the connected camera supports hot-pixel correction,\
                                    the threshold-range maximum will be greater than zero.',
                           unit = 'pixels',
                           get_cmd = lambda: self.camera.is_hot_pixel_correction_enabled,
                           set_cmd = lambda x: setattr(self.camera,'is_hot_pixel_correction_enabled',x),
                           val_mapping=create_on_off_val_mapping())

        hot_pixel_correction_threshold_range = self.camera.hot_pixel_correction_threshold_range
        self.add_parameter(name = 'hot_pixel_correction_threshold',
                           get_cmd = lambda: self.camera.hot_pixel_correction_threshold,
                           set_cmd = lambda x: setattr(self.camera,'hot_pixel_correction_threshold',x),
                           vals=Ints(min_value=hot_pixel_correction_threshold_range[0],
                                     max_value= hot_pixel_correction_threshold_range[1]))

        self.add_parameter(name = 'sensor_width',
                           unit = 'pixels',
                           get_cmd = lambda: self.camera.sensor_width_pixels)
        self.add_parameter(name = 'sensor_height',
                           unit = 'pixels',
                           get_cmd = lambda: self.camera.sensor_height_pixels)

        self.add_parameter(name = 'armed',
                           get_cmd = lambda: self.camera.is_armed)
        

        if self.camera.is_led_supported:
            self.add_parameter(name = 'led_on',
                               get_cmd = lambda: self.camera.is_led_on,
                               set_cmd = lambda x: setattr(self.camera,'is_led_on',x),
                               val_mapping=create_on_off_val_mapping())
        
        if self.camera.is_cooling_supported:
            self.add_parameter(name = 'cooling_enabled',
                               get_cmd = lambda: self.camera.is_cooling_enabled)
            
        self.add_parameter(name = 'nir_boost_supported',
                           get_cmd = lambda: self.camera.is_nir_boost_supported)
        
        self.add_parameter(name = 'image_width',
                           unit = 'pixels',
                           get_cmd = lambda: self.camera.image_width_pixels)
        self.add_parameter(name = 'image_height',
                           unit = 'pixels',
                           get_cmd = lambda: self.camera.image_height_pixels)




        frames_per_trigger_range = self.camera.frames_per_trigger_range
        self.add_parameter(name = 'frames_per_trigger',
                           docstring = 'The number of frames generated per software or hardware trigger can be unlimited or finite.\
                                        If set to zero, the camera will self-trigger indefinitely, allowing a continuous video feed.\
                                        If set to one or higher, a single software or hardware trigger will generate only the prescribed number of\
                                        frames and then stop.',
                           get_cmd = lambda: self.camera.frames_per_trigger_zero_for_unlimited,
                           set_cmd = lambda x: setattr(self.camera,'frames_per_trigger_zero_for_unlimited',x),
                           vals=Ints(min_value=frames_per_trigger_range[0],
                                     max_value= frames_per_trigger_range[1]))


        


        self.add_parameter(name = 'camera_model',
                           get_cmd = lambda: self.camera.model)
        
        self.add_parameter(name = 'firmware_version',
                           get_cmd = lambda: self.camera.firmware_version)

        self.add_parameter(name = 'serial_number',
                           get_cmd = lambda: self.camera.serial_number)


        roi_range = self.camera.roi_range
        self.add_parameter('roi_upper_left_x',
                            unit = 'pixels',
                            get_cmd = lambda: self.get_roi()[0],
                            set_cmd = lambda x: self.set_roi(roi_upper_left_x=x),
                           vals=Ints(min_value=roi_range.upper_left_x_pixels_min,
                                     max_value= roi_range.upper_left_x_pixels_max))
        self.add_parameter('roi_upper_left_y',
                            unit = 'pixels',
                            get_cmd = lambda: self.get_roi()[1],
                            set_cmd = lambda x: self.set_roi(roi_upper_left_y=x),
                           vals=Ints(min_value=roi_range.upper_left_y_pixels_min,
                                     max_value= roi_range.upper_left_y_pixels_max))
        self.add_parameter('roi_lower_right_x',
                            unit = 'pixels',
                            get_cmd = lambda: self.get_roi()[2],
                            set_cmd = lambda x: self.set_roi(roi_lower_right_x=x),
                            vals=Ints(min_value=roi_range.lower_right_x_pixels_min,
                                     max_value= roi_range.lower_right_x_pixels_max))
        self.add_parameter('roi_lower_right_y',
                            unit = 'pixels',
                            get_cmd = lambda: self.get_roi()[3],
                            set_cmd = lambda x: self.set_roi(roi_lower_right_y=x),
                            vals=Ints(min_value=roi_range.lower_right_y_pixels_min,
                                     max_value= roi_range.lower_right_y_pixels_max))

                           
                           
    def __enter__(self):
        """ Method to allow the use of the with-as statement
        """
        return self
        
    def __exit__(self, type, value, traceback):
        """ Method to allow the use of the with-as statement
        """
        self.close()
        
    def get_idn(self):
        return self.camera_model() + '_' + self.serial_number()
        


    def get_roi(self):
        roi = self.camera.roi
        return [roi.upper_left_x_pixels, roi.upper_left_y_pixels, roi.lower_right_x_pixels, roi.lower_right_y_pixels]

    def set_roi(self, roi_upper_left_x = None, roi_upper_left_y = None, roi_lower_right_x = None, roi_lower_right_y = None):
        if roi_upper_left_x is None:
            roi_upper_left_x = self.roi_upper_left_x.cache.get()
        if roi_upper_left_y is None:
            roi_upper_left_y = self.roi_upper_left_y.cache.get()
        if roi_lower_right_x is None:
            roi_lower_right_x = self.roi_lower_right_x.cache.get()
        if roi_lower_right_y is None:
            roi_lower_right_y = self.roi_lower_right_y.cache.get()
        roi = ROI(roi_upper_left_x, roi_upper_left_y, roi_lower_right_x, roi_lower_right_y)
        print(roi)
        self.camera.roi = roi


    def arm(self,frames_to_buffer = 2):
        """
        Before issuing software or hardware triggers to get images from a camera, prepare it for imaging by calling
        arm(). 
        
        A good choice for frames_to_buffer seems to be 100. Minimum is 2.

        """
        self.camera.arm(frames_to_buffer)


    def disarm(self):
        """
        When finished issuing software or hardware triggers, call disarm(). This allows
        setting parameters that are not available in armed mode such as roi or
        operation_mode.
        
        Disarming the camera does not clear the image queue – polling can continue until the queue is empty. When
        calling arm again, the queue will be automatically cleared.

        """
        self.camera.disarm()

    def get_frame(self):
        return self.camera.get_pending_frame_or_null()

    def issue_software_trigger(self):
        self.camera.issue_software_trigger()
        
    def live_view(self):
        import pyqtgraph as pg
        from pyqtgraph.Qt import QtCore
        
        self.image_poll_timeout(self.exposure_time()+1)
        self.arm(100)
        self.issue_software_trigger()
        time.sleep(1)
        
        frame = self.get_frame()
        p = pg.image(frame.image_buffer.T)
        
        def update():
            frame = self.get_frame()
            if frame:
                p.setImage(frame.image_buffer.T, autoRange=False,autoLevels=False,autoHistogramRange=False)
        
        timer = QtCore.QTimer()
        timer.timeout.connect(update)
        timer.start(0)
        pg.exec()
        self.disarm()

    def close(self):
        self.camera.dispose()
        self.sdk.dispose()
        super().close()
        
