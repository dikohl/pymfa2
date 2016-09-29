#!/usr/bin/python3
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
import math

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
            return 0.0
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
        sum_rate = 0
        if len(par) == 2:   # loc = 0
            c = par[0]
            scale = par[1]
            for j in range (2,30):  #calculate sum over weibull function except for service lifetime = 1
                frozenWeib = st.exponweib(1, c, 0, scale)
                weib_rate = 0.5*(frozenWeib.pdf(j-0.5)-frozenWeib.pdf(j))+frozenWeib.pdf(j)
                sum_rate += weib_rate
                
            if period ==0:  # weibull function should not become infinite if c<1
                   rate = 0

            elif period ==1: 
                   rate = 1-sum_rate #sum over weibull function should equal 1, all material gets released in the end
            else:
                frozenWeib = st.exponweib(1, c, 0, scale)
                rate = 0.5*(frozenWeib.pdf(period-0.5)-frozenWeib.pdf(period))+frozenWeib.pdf(period)
            return rate
            
        elif len(par) == 3: # loc defined by user
            c = par[0]
            scale = par[1]
            loc = par[2]
            ceil = math.ceil(loc)
            for j in range (ceil+1,30): #calculate sum over weibull function except for service lifetime <=loc
                frozenWeib = st.exponweib(1, c, loc, scale)
                weib_rate = 0.5*(frozenWeib.pdf(j-0.5)-frozenWeib.pdf(j))+frozenWeib.pdf(j)
                sum_rate += weib_rate
                
            if period < ceil: # weibull function should not become infinite if c<1
                   rate = 0
                   
            elif period == ceil:
                   rate = 1-sum_rate #sum over weibull function should equal 1, all material gets released in the end
            else:
                frozenWeib = st.exponweib(1, c, loc, scale)
                rate = 0.5*(frozenWeib.pdf(period-0.5)-frozenWeib.pdf(period))+frozenWeib.pdf(period)
            return rate
        else:
            print('ERROR:')
            print('Too few or too many arguments for weibull release function.')
            print('Enter two or three arguments for weibull release function.')
