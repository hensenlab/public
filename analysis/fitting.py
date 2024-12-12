# -*- coding: utf-8 -*-
"""
Created 2022

@author: B.J.Hensen, Rob Stockill

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2022, Hensen Lab

All rights reserved.
"""

from scipy.optimize import curve_fit
import numpy as np
from analysis.data_tools import max_abs_fft


def fit(x,y,fitfunc,p0, plot_pts = 1000, plot_initial_guess=False, ignore_y_nans=True,**kwargs):
    """
    Use scipy.curvefit to fit x,y with fitfunc, using initial guess p0.
    kwargs are passed on to scipy.curve_fit
    returns optimal parameters popt, with standard errors perr = np.sqrt(np.diag(pcov)),
    as well as xp,yp, plottable arrays of the fitresult with plot_pts points.
    """
   
    xp = np.linspace(np.min(x),np.max(x),plot_pts)
    if plot_initial_guess:
        yp = fitfunc(xp,*p0)
        popt = np.array(p0)
        perr = popt*np.inf
    else:
        if ignore_y_nans:
            x = x[~np.isnan(y)]
            y = y[~np.isnan(y)]
        popt, pcov = curve_fit(fitfunc, x, y, p0 =p0, **kwargs)
        perr = np.sqrt(np.diag(pcov))
        yp = fitfunc(xp,*popt)

    return popt, perr, xp, yp

def guess_gauss(x,y):
    return [np.nanmax(y)-np.nanmin(y),x[np.nanargmax(np.abs(y))],(np.nanmax(x)-np.nanmin(x))/4,np.nanmean(y)-(np.nanmax(y)-np.nanmin(y))/2]  

def gauss_function(x, a, x0, sigma, offset):
    """
    return a*np.exp(-(x-x0)**2/(2*sigma**2))+offset
    """
    return a*np.exp(-(x-x0)**2/(2*sigma**2))+offset

def lorentz_function(x, a, x0, w, offset):
    """
    return offset + 2*a/np.pi*w/(4*(x-x0)**2+w**2)
    """
    return offset + a*((w/2)**2)/((x-x0)**2+(w/2)**2)

def lorentz_function_linoff(x, a, x0, w, offset,boff):
    """
    return offset + 2*a/np.pi*w/(4*(x-x0)**2+w**2)
    """
    return offset + boff*(x - x0) + a*((w/2)**2)/((x-x0)**2+(w/2)**2)

def double_lorentz_function_linoff(x, a1, a2, x01, x02, w1, w2, offset, boff):
    return offset + boff*(x - x01) + a1*((w1/2)**2)/((x-x01)**2+(w1/2)**2) + a2*((w2/2)**2)/((x-x02)**2+(w2/2)**2)

def triple_lorentz_function_linoff(x, a1, a2, a3, x01, x02, x03, w1, w2, w3, offset, boff):
    return offset + boff*(x - x01) + a1*((w1/2)**2)/((x-x01)**2+(w1/2)**2) + a2*((w2/2)**2)/((x-x02)**2+(w2/2)**2) + a3*((w3/2)**2)/((x-x03)**2+(w3/2)**2)

def root_lorentz_function(x, a, x0, w, offset):
    """
    return offset + np.sqrt(a*((w/2)**2)/((x-x0)**2+(w/2)**2))
    """
    return offset + a*np.sqrt(np.abs(((w/2)**2)/((x-x0)**2+(w/2)**2)))

def root_lorentz_function_linoff(x, a, x0, w, offset, boff):
    """
    return offset + np.sqrt(a*((w/2)**2)/((x-x0)**2+(w/2)**2))
    """
    return offset + boff*(x - x0) + a*np.sqrt(np.abs(((w/2)**2)/((x-x0)**2+(w/2)**2)))

def root_function(x,a,offset):
    return offset + a*np.sqrt(x)

def coop_fun(x,a,b,c):
    return a*(x/b)/(1 + c + (x/b))**2

def guess_exp(x,y):
    return [y[0]-y[-1],(np.max(x)-np.min(x))/6,y[-1]]

def exp_function(x, a, t, offset):
    """
    return a*np.exp(-x/t)+offset 
    """
    return a*np.exp(-x/t)+offset 

def linear_function(x, a, b):
    """ 
    return a*x + b
    """
    return a*x + b

def guess_sin(x,y):
    return [(np.max(y)-np.min(y))/2,2*np.pi*max_abs_fft(x,y),0,np.mean(y)]

def sin_function(x, amplitude, omega, phase , offset):
    """
    return amplitude*np.sin(omega*x + phase) + offset
    """
    return amplitude*np.sin(omega*x + phase) + offset

def decaying_sin_function(x, amplitude, omega, phase , offset,decay_constant):
    """
    return np.exp(-x/decay_constant)*amplitude*np.sin(omega*x + phase) + offset
    """
    return np.exp(-x/decay_constant)*amplitude*np.sin(omega*x + phase) + offset

def sin_sq_function(x, a, b, c , d):
    """
    return a*(np.sin(b*x + c))**2 + d
    """
    return a*(np.sin(b*x + c))**2 + d

def thermalization_curve(x, offset, a, b, gamma_rise, gamma_fall):
    return offset - a*np.exp(-x/gamma_rise) + b*np.exp(-x/gamma_fall)

def rising_pulse_transduction(x,offset,xoffset,amp,gamma,detuning):
    """
    offset + np.heaviside(x-xoffset,0)*amp*(1 + np.exp(-(x - xoffset)/gamma) - 2*np.cos(detuning*(x-xoffset))*np.exp(-(x - xoffset)/gamma/2))
    Fitting function for saturating photon level from pulsed transduction, taken from supp of https://doi.org/10.1038/s41467-020-17053-3
    """
    return offset + np.heaviside(x-xoffset,0)*amp*(1 + np.exp(-(x - xoffset)/gamma) - 2*np.cos(detuning*(x-xoffset))*np.exp(-(x - xoffset)/gamma/2))

def rising_pulse_transduction_no_detuning(x,offset,xoffset,amp,gamma):
    """
    offset + np.heaviside(x-xoffset,0)*amp*(1 - np.exp(-(x-xoffset)/gamma/2))**2# + np.exp(-kappa*(x)) - 2*1*np.exp(-kappa*(x)/2))
    
    Fitting function for saturating photon level from pulsed transduction, taken from supp of https://doi.org/10.1038/s41467-020-17053-3
    """
    return offset + np.heaviside(x-xoffset,0)*amp*(1 - np.exp(-(x-xoffset)/gamma/2))**2# + np.exp(-kappa*(x)) - 2*1*np.exp(-kappa*(x)/2))
    

def over_under_function(x,amp,ke,ki,det):
    """
    

    Parameters
    ----------
    x : array
        VNA Frequency
    amp : array
        S21 linear amplitude multiplier (nb if dB needs 10**(S21_dB/20))
        also note that if the VNA is properly calibrated this number should be 1.
    ke : float
        External coupling rate (linear frequency)
    ki : float
        Internal loss rate (linear frequency)
    det : float
        Carrier detuning from resonance (linear frequency)

    Returns
    -------
    function for total reflected light oscillating at the drive frequency
    - including the interference between
    the carrier and each of the sidebands. 

    """
    def E0_r(x,ke,ki,det):
        return (1 - ke/(((ke + ki)/2)  - 1j*(-det)))
    def Eres_r(x,ke,ki,det):
        return (1 - ke/(((ke + ki)/2)  - 1j*(x - det)))
    def Eoff_r(x,ke,ki,det):
        return (1 - ke/(((ke + ki)/2)  - 1j*(-x - det)))
    
    return amp*0.25*np.abs(E0_r(x,ke,ki,det)*np.conj(Eres_r(x,ke,ki,det)) 
                           + np.conj(E0_r(x,ke,ki,det))*Eres_r(x,ke,ki,det) 
                           + E0_r(x,ke,ki,det)*np.conj(Eoff_r(x,ke,ki,det)) 
                           + np.conj(E0_r(x,ke,ki,det))*Eoff_r(x,ke,ki,det))