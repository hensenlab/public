# -*- coding: utf-8 -*-
"""
Created 2020

@author: B.J.Hensen

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2022, Hensen Lab

All rights reserved.

# Transcribed for python from matlab FMINSEARCHBND
# Author: John D'Errico
# E-mail: woodchips@rochester.rr.com
# Release: 4
# Release date: 7/23/06

"""

import numpy as np
import scipy.optimize
import logging

def minimize_bound(fun,x0,fun_args=(),LB=None,UB=None,**kwargs):
    """
    minimize_bound,: scipy.optimize.minimize but with bound constraints by transformation


    args: fun, x0: see help for scipy.optimize.minimize
    kwargs:
     LB - lower bound vector or array, must be the same size as x0

           If no lower bounds exist for one of the variables, then
           supply -inf for that variable.

           If no lower bounds at all, then LB may be left empty.

           Variables may be fixed in value by setting the corresponding
           lower and upper bounds to exactly the same value.

      UB - upper bound vector or array, must be the same size as x0

           If no upper bounds exist for one of the variables, then
           supply +inf for that variable.

           If no upper bounds at all, then UB may be left empty.

           Variables may be fixed in value by setting the corresponding
           lower and upper bounds to exactly the same value.

    **kwargs are passed on to scipy.optimize.minimize

     Variables which are constrained by both a lower and an upper
     bound will use a sin transformation. Those constrained by
     only a lower or an upper bound will use a quadratic
     transformation, and unconstrained variables will be left alone.

     Variables may be fixed by setting their respective bounds equal.
     In this case, the problem will be reduced in size for FMINSEARCH.

     The bounds are inclusive inequalities, which admit the
     boundary values themselves, but will not permit ANY function
     evaluations outside the bounds. These constraints are strictly
     followed.

     If your problem has an EXCLUSIVE (strict) constraint which will
     not admit evaluation at the bound itself, then you must provide
     a slightly offset bound. An example of this is a function which
     contains the log of one of its parameters. If you constrain the
     variable to have a lower bound of zero, then FMINSEARCHBND may
     try to evaluate the function exactly at zero.

     Example usage:
     rosen = lambda x: (1-x[0])**2 + 105*(x[1]-x[0])**2)**2

     minimize_bound(rosen,[3,3], method  = 'Nelder-Mead')     % unconstrained
     ans =
        1.0000    1.0000

     fminsearchbnd(rosen,[3,3],LB=[2,2],method  = 'Nelder-Mead')  % constrained
     ans =
        2.0000    4.0000

     """
    x0 = np.array(x0)

    n = len(x0)
    if LB is None:
        LB = np.full(x0.shape,-np.inf)
    else:
    	LB = np.array(LB)
    if UB is None:
        UB = np.full(x0.shape,np.inf)
    else:
    	UB=np.array(UB)

    assert x0.shape == LB.shape
    assert x0.shape == UB.shape

    bound_params = {}
    bound_params['LB'] = LB
    bound_params['UB'] = UB
    bound_params['fun'] = fun
    bound_params['n'] = n


    # type of bound:
    # 0 --> unconstrained variable
    # 1 --> lower bound only
    # 2 --> upper bound only
    # 3 --> dual finite bounds
    # 4 --> fixed variable
    types = 1*np.isfinite(LB) + 2*np.isfinite(UB)
    types = types + 1*((types==3) & (LB==UB))
    bound_params['types'] = types
    # transform starting values into their unconstrained
    # surrogates. Check for infeasible starting guesses.
    x0u = x0.copy();
    k=0;

    for i in range(n):
        #check for infeasible starting values. Use bound.
        if types[i] == 0:   # unconstrained variable. x0u(i) is set.
            x0u[k] = x0[i]
        elif types[i] == 1: # lower bound only
            x0u[k] = np.sqrt(x0[i] - LB[i]) if x0[i]>LB[i] else 0  
        elif types[i] == 2: # upper bound only
            x0u[k] = np.sqrt(UB[i] - x0[i]) if x0[i]<UB[i] else 0 
        elif types[i] == 3: # lower and upper bounds
            if x0[i]<=LB[i]:
                # infeasible starting value
                x0u[k] = -np.pi/2
            elif x0[i]>=UB[i]:
                # infeasible starting value
                x0u[k] = np.pi/2
            else:
                x0u[k] = 2*(x0[i] - LB[i])/(UB[i]-LB[i]) - 1;
                # shift by 2*pi to avoid problems at zero in fminsearch
                # otherwise, the initial simplex is vanishingly small
                x0u[k] = 2*np.pi+np.arcsin(np.max([-1,np.min([1,x0u[k]])]))
        elif types[i] == 4:  # fixed variable. drop it before fminsearch sees it.
                             # k is not incremented for this variable.
            continue
        # increment k
        k+=1
    # if any of the unknowns were fixed, then we need to shorten
    # x0u now.
    x0u = x0u[:k]
    # were all the variables fixed?
    if k == 0:
        logging.warning('All variables were held fixed by the applied bounds')
        return
    fun_args = list(fun_args)
    fun_args.insert(0,bound_params)
    res = scipy.optimize.minimize(intrafun,x0u,args=tuple(fun_args),**kwargs)
    xt = xtransform(res['x'],bound_params)
    return xt,res

def intrafun(x,*args):
    # transform variables, then call original function
    # transform
    bound_params = args[0]
    xtrans = xtransform(x,bound_params)
    # and call fun
    return bound_params['fun'](xtrans,*args[1:])

def xtransform(x,bound_params):
    # converts unconstrained variables into their original domains
    xtrans = np.zeros(bound_params['n'])
    # k allows some variables to be fixed, thus dropped from the
    # optimization.
    
    types = bound_params['types']
    LB = bound_params['LB']
    UB = bound_params['UB']
    k=0
    for i in range(bound_params['n']):
        if types[i] == 0:   # unconstrained variable. x0u(i) is set.
            xtrans[i] = x[k]
        elif types[i] == 1: # lower bound only
            xtrans[i] = LB[i] + x[k]**2
        elif types[i] == 2: # upper bound only
            xtrans[i] = UB[i] - x[k]**2
        elif types[i] == 3: # lower and upper bounds
            xtrans[i] = (np.sin(x[k])+1)/2
            xtrans[i] = xtrans[i]*(UB[i] - LB[i]) + LB[i]
            # just in case of any floating point problems
            xtrans[i] = np.max([LB[i],np.min([UB[i],xtrans[i]])]);
        elif types[i] == 4:  # fixed variable. drop it before fminsearch sees it.
                             # k is not incremented for this variable.
            xtrans[i] = LB[i]
            continue
        k+=1
    return xtrans

if __name__=='__main__':
    rosen = lambda x: (1-x[0])**2 + 105*(x[1]-x[0]**2)**2
    xt,res=minimize_bound(rosen,[3,3], method  = 'Nelder-Mead') 
    print(xt,res)
    
    xt,res = minimize_bound(rosen,[3,3],LB=[2,2],method  = 'Nelder-Mead') 
    print(xt,res)
    xt,res = minimize_bound(rosen,[3,3],LB=[2,2],UB=[4,4],method  = 'Nelder-Mead') 
    print(xt,res)