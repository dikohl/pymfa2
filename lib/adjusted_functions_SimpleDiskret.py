# -*- coding: utf-8 -*-
"""
Created in January 2016

@author: RoBa

The adjusted_functions module contains the 'fixedRate' function (which can be
used as transfer function) and the class 'ReleaseFunction'.
This class' functions can be used as release functions for local releases and
so for their stock components. Once the parameters are set by instantiating
the class, the release functions only depend on the current period.
"""

import scipy.stats as st
import numpy as np


def fixedRate(rate):
    return rate
    

class ReleaseFunction(object):
    """
    A ReleaseFunction determines a release rate for a specific period via
    the chosen function. The functions are determined by the
    instance's parameters.
    """
    
    def __init__(self, parameters = []):
        self.parameters = parameters

 
    def fixedRateRelease(self, period):
        """
        Returns always the first/only value from the parameter list,
        independently of the current period.
        """
        return self.parameters[0]

                
    def listRelease(self, period):
        """
        Returns a rate from the parameter list determined by the period.
        """
        if len(self.parameters) < 1:
            print('ERROR:')
            print('No arguments for list release function.')
        elif len(self.parameters) <= period:
            print('ERROR:')
            print('More periods than rates for list release.')
        else:
            return self.parameters[period]


    def randomRateRelease(self, period):
        """
        Returns a random rate from the parameter list.
        """
        rate = np.random.choice(self.parameters)
        return rate


        
    def weibullRelease(self, period):
        """
        Returns the rate from a user-shaped weibull distribution function 
        at a specific period.  
        """
        par = self.parameters
        if len(par) == 2:   # loc = 0
            c = par[0]
            scale = par[1]
            frozenWeib = st.exponweib(1, c, 0, scale)
            rate = frozenWeib.pdf(period)
            return rate
        elif len(self.parameters) == 3: # loc defined by user
            c = par[0]
            scale = par[1]
            loc = par[2]
            frozenWeib = st.exponweib(1, c, loc, scale)
            rate = frozenWeib.pdf(period)
            return rate
        else:
            print('ERROR:')
            print('Too few or too many arguments for weibull release function.')
            print('Enter two or three arguments for weibull release function.')
