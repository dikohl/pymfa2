#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 12 14:56:22 2014

@author: bni

The components module contains model elements that are necessary to implement a
Probabilistic Material Flow Model. To represent the system, the model elements
need to be parametrized to fit the specific system behavior.
"""
import numpy as np
from functools import reduce



class Compartment(object):
    """ A compartment is a distinct area of the investigated system. 
    Depending on the scientific question to be aswered with the model a 
    compartment can be an environmental media, a geographic region or a logical
    partition in the fate of a material.
    
    To use a Compartment, please instantiate its subclasses FlowComp, Sink, and
    Stock. 
    """
    def __init__(self, name, logInflows, categories):
        self.compNumber = 'not defined'
        self.name = name
        self.logInflows = logInflows
        self.categories = categories
        
    """
    inits a matrix to log the material inflows for all simulation runs and
    periods
    """
    def initFlowLog(self, runs, periods):
        """
        if flow record is set, a matrix is initialized to log all flows to the 
        compartment        
        """
        if self.logInflows:
            self.inflowRecord = np.zeros((runs, periods))
    
    
    def logFlow(self, run, period, amt):    
        """
        logs the inflow to the compartment
        """    
        if self.logInflows:            
            self.inflowRecord[run, period]= amt

# modified by RoBa, January 2016: function determineTCs(...)
class FlowCompartment(Compartment):
    """ A FlowComp represents a system Compartment without residence time of
    observed material. The further transfer of material to subsequent 
    compartments is defined using Transfer objects. 
    
    Parameters:        
    ----------------
    name: string 
        compartment name
    transfers: list<components.Transfer>
        all outgoing transfers from the Flow Compartment
        for every target Compartment
    logInflows: Boolean
        defines if incoming flows are logged for later evaluation
    logOutflows: Boolean
        defines if outgoing flows are logged for later evaluation         
    categories: list
        defined a list of categories the stock is part of(for later evaluation)
    """
    
    def __init__(self, name, transfers= [], logInflows = False, 
                 logOutflows = False, adjustOutgoingTCs = True, 
                 categories = []):
        super(FlowCompartment, self).__init__(name, logInflows, categories)        
        self.transfers = transfers        
        self.adjustOutTCs = adjustOutgoingTCs
        self.logOutflows = logOutflows
        self.immediateReleaseRate = 1
    
    def determineTCs(self, useGlobalTCsettings, globalSettingsAdjust, period):   
        """
        Samples transfer from the underlying probability distribution, may \
        adjust to a sum of one over all outgoing transfers.
        """

        # modified by RoBa, October 2015: parameter 'period' in
        # sampleTC(period) is used for transfers of class 'PeriodDefinedTransfer'   
        for t in self.transfers:
            if isinstance(t, PeriodDefinedTransfer):
                t.sampleTC(period)
            else:
                t.sampleTC()
        
        if (not useGlobalTCsettings) & self.adjustOutTCs:
            self.adjustTCs()

        elif useGlobalTCsettings & globalSettingsAdjust:
            self.adjustTCs()                


    def initFlowLog(self, runs, periods):
        """
        if flow record is set, a matrix is initialized to log all flows to the 
        compartment
        if outFlows are logged a dictionary is initialized to log the outflows        
        """
        if self.logInflows:
            self.inflowRecord = np.zeros((runs, periods))
            
        if self.logOutflows:
            self.outflowRecord = {}
            for t in self.transfers:
                self.outflowRecord[t.target.name] = np.zeros((runs, periods))

    # annotation RoBa, January 2016: never run
    def initInventory(self, runs, periods):
        self.inventory = np.zeros((runs, periods))
        self.releaseList = np.zeros((runs, periods))
        self.localRelease.releaseList = np.zeros((runs, periods))


    def logFlow(self, run, period, amt):    
        """
        logs the inflow to the compartment
        """    
        if self.logInflows:            
            self.inflowRecord[run, period]= amt
            
        if self.logOutflows:
            for t in self.transfers:
                self.outflowRecord[t.target.name][run, period] = \
                t.getCurrentTC()*amt            
 
    # modified by RoBa, March 2016:
    # - problem of occuring ERROR if currentAdjustSum==0 solved
    # - rounding problem solved (some floats never rounded to 1)
    def adjustTCs(self):
        """ Adjusts TCs outgoing from one compartment to sum up to one.      
        Applies adjustment factor on TCs with the lowest priority first. \
        If that is insufficient (negativ TCs are not allowed), adjustment of \
        the TC with next higher priority and so on...
        """
        tcSum = sum(t.currentTC for t in self.transfers)
        currentPriority = min(t.priority for t in self.transfers)
       
        while tcSum!=1:

            adjustableTransfers = [t for t in self.transfers if t.priority == 
                                   currentPriority]
            adjustableTCs = [t.currentTC for t in adjustableTransfers]          
            currentAdjustSum = sum(adjustableTCs)             
            normToValue = max(currentAdjustSum - (tcSum - 1), 0)
            
            if tcSum == 0:
                changedTCs = [1.0/len(self.transfers)] * len(self.transfers)
                for i in range(len(self.transfers)):
                    self.transfers[i].currentTC = changedTCs[i]
            elif currentAdjustSum == 0 and tcSum < 1:
                changedTCs = [(1.0-tcSum)/len(adjustableTCs)]*len(adjustableTCs)
                for i in range(len(changedTCs)):
                    adjustableTransfers[i].currentTC = changedTCs[i]
            elif currentAdjustSum != 0:
                changedTCs = self.__normListSumTo(adjustableTCs, normToValue)
                for i in range(len(changedTCs)):
                    adjustableTransfers[i].currentTC = changedTCs[i]
            else:
                pass
                           
            tcSum = sum(t.currentTC for t in self.transfers)
            tcSum = round(tcSum, 12)
            if int(tcSum*100000000000) == int(100000000000):
                tcSum = 1  # round to 11 digits after the decimal point
            currentPriority = currentPriority + 1
            

    def __normListSumTo(self, L, sumTo=1):  
        '''normalize values of a list to a certain value''' 
        sum = reduce(lambda x,y:x+y, L)
        return [ x/(sum*1.0)*sumTo for x in L]

        
class Sink(Compartment):
    """ A model compartment where inflowing material accumulates 
    
    Parameters:        
    ----------------
    name: string 
        compartment name
    logInflows: Boolean
        defines if incoming flows are logged for later evaluation
    categories: list
        defined a list of categories the stock is part of(for later evaluation)          
    
    """

    def __init__(self, name, logInflows = False, categories = []):
        super(Sink, self).__init__(name, logInflows, categories)
                        
    def initInventory(self, runs, periods):
        self.inventory = np.zeros((runs, periods))
            
    def updateInventory(self, run, period):
        """ transfers the stored amount from the end of a period to the 
        beginning of the next one.
        """
        if (period != 0):
            self.inventory[run, period] = self.inventory[run, period -1]
        
    def storeMaterial(self, run, period, amount):
        """ increases the stored amount by an accumulated inflow"""
        self.inventory[run, period] = self.inventory[run, period] + amount
            


class Stock(FlowCompartment, Sink):
    """ A Stock is a Sink that releases a part of the stored material in later
    periods.
    
    Parameters:        
    ----------------
    name: string 
        compartment name
    transfers: list<components.Transfer>
        transfers of the material released from stock to other compartments
    localRelease: components.LocalRelease
        definition which proportions of the amount of material stored in a \
        period are released in which of the subsequent periods          
    logInflows: Boolean
        defines if incoming flows are logged for later evaluation   
    logOutflows: Boolean
        defines if outgoing flows are logged for later evaluation
    categories: list
        defined a list of categories the stock is part of(for later evaluation)
    
    """
    def __init__(self, name, transfers=[], localRelease = 0, 
                 logInflows = False, logOutflows = False, 
                 logImmediateFlows = False, categories = []):
        super(Stock, self).__init__(name, transfers, logInflows, categories)
        self.localRelease = localRelease
        self.logOutflows = logOutflows
        self.logImmediateFlows = logImmediateFlows
        self.immediateReleaseRate = 1
        self.categories = categories

    
    def initInventory(self, runs, periods):
        self.inventory = np.zeros((runs, periods))
        self.releaseList = np.zeros((runs, periods))
        # annotation RoBa, December 2015: 'self.releaseList' is never used
        self.localRelease.releaseList = np.zeros((runs, periods))      
        if self.logImmediateFlows:
            self.immediateFlowRecord = {}
            for t in self.transfers:
                self.immediateFlowRecord[t.target.name] = np.zeros((runs, 
                                                                    periods))
        
        
    def updateImmediateReleaseRate(self):
        self.immediateReleaseRate = self.localRelease.getImmediateReleaseRate()


    def logFlow(self, run, period, amt):    
        """
        logs the inflow to the compartment
        """    
        if self.logInflows:            
            self.inflowRecord[run, period]= amt
                       
        if self.logOutflows:
            for t in self.transfers:
                self.outflowRecord[t.target.name][run, period] = \
                self.outflowRecord[t.target.name][run, period] + \
                t.getCurrentTC()*amt * self.immediateReleaseRate    
                                
        if self.logImmediateFlows:
            for t in self.transfers:
                self.immediateFlowRecord[t.target.name][run, period] = \
                t.getCurrentTC()*amt * self.immediateReleaseRate 
            

    def storeMaterial(self, run, period, amount):
        """ stores material and schedules future release according to the 
        release strategy of the stock
        """

        self.inventory[run, period] = self.inventory[run, period] + \
        amount*(1-self.immediateReleaseRate)
        self.localRelease.scheduleFutureRelease(run, period, amount)


    def releaseMaterial(self, run, period):
        """ takes the release scheduled for the current period distributes it 
        to the different target Compartments
        
        ------------
        returns: Dict {Compartment: amt}
        """        

        releaseAmt = self.localRelease.releaseList[run, period]
        self.inventory[run, period] = self.inventory[run, period] - releaseAmt
        releases = {}
        for trans in self.transfers:            
            releases[trans.target]=trans.getCurrentTC()*releaseAmt
            if self.logOutflows:
                self.outflowRecord[trans.target.name][run, period] = \
                releases[trans.target]
                
        return releases



# added by RoBa, November 2015
class TDRStock(Stock):
    """ A Stock is a Sink that releases a part of the stored material in later
    periods. In contrast to the Stock class, the TDRStock's release strategie
    can be defined for every period and every target individually.
    (TDR means "target defined release".)
    
    Parameters:        
    ----------------
    name: string 
        compartment name
    transfers: list<components.PeriodDefinedTransfer>
        transfers of the material released from stock to other compartments
    localRelease: List<components.LocalRelease>
        definition which proportions of the amount of material stored in a
        period are released in which of the subsequent periods          
    logInflows: Boolean
        defines if incoming flows are logged for later evaluation   
    logOutflows: Boolean
        defines if outgoing flows are logged for later evaluation
    categories: list
        defined a list of categories the stock is part of(for later evaluation)
    
    """
    def __init__(self, name, transfers = [], localRelease = [], 
                 logInflows = False, logOutflows = False, 
                 logImmediateFlows = False, categories = []):
        super(TDRStock, self).__init__(name)
        self.transfers = transfers
        self.logInflows = logInflows
        self.logOutflows = logOutflows
        self.logImmediateFlows = logImmediateFlows
        self.categories = categories
        self.localReleaseList = localRelease
        self.localRelease = {}  # Dict {Compartment.name: LocalRelease}
        self.immediateReleaseRate = {}

    
    def initInventory(self, runs, periods):
        self.inventory = np.zeros((runs, periods))
        self.releaseList = np.zeros((runs, periods))
        # annotation RoBa, November 2015: 'self.releaseList' is never used
        
        for locRel in self.localReleaseList:
            self.localRelease[locRel.target.name] = locRel
            self.localRelease[locRel.target.name].releaseList = \
            np.zeros((runs, periods))
        
        if self.logImmediateFlows:
            self.immediateFlowRecord = {}
            for t in self.transfers:
                self.immediateFlowRecord[t.target.name] = np.zeros((runs, 
                                                                    periods))
                                                                    
                                                                            
    def updateImmediateReleaseRate(self):
        for t in self.transfers:
            self.immediateReleaseRate[t.target.name] = \
            self.localRelease[t.target.name].getImmediateReleaseRate()


    def logFlow(self, run, period, amt):    
        """
        logs the inflow to the compartment
        """    
        if self.logInflows:            
            self.inflowRecord[run, period]= amt
                       
        if self.logOutflows:
            for t in self.transfers:
                self.outflowRecord[t.target.name][run, period] = \
                self.outflowRecord[t.target.name][run, period] + \
                t.getCurrentTC()*amt * \
                self.immediateReleaseRate[t.target.name][period]    
                                
        if self.logImmediateFlows:
            for t in self.transfers:
                self.immediateFlowRecord[t.target.name][run, period] = \
                t.getCurrentTC()*amt * \
                self.immediateReleaseRate[t.target.name][period]
            

    def storeMaterial(self, run, period, amount):
        """ stores material and schedules future release according to the 
        release strategy of the stock
        """

        for t in self.transfers:
            amountForTarget = amount * t.getCurrentTC()
            self.inventory[run, period] = \
            self.inventory[run, period] + amountForTarget * \
            (1-self.immediateReleaseRate[t.target.name][period])
            self.localRelease[t.target.name].scheduleFutureRelease(run, period,
                                                               amountForTarget)


    def releaseMaterial(self, run, period):
        """ takes the release scheduled for the current period distributes it 
        to the different target Compartments
        
        ------------
        returns: Dict {Compartment: amt}
        """        

        releases = {}
        for trans in self.transfers:
            releaseAmt = \
            self.localRelease[trans.target.name].releaseList[run, period]
            self.inventory[run, period] -= releaseAmt
            releases[trans.target] = releaseAmt
            if self.logOutflows:
                self.outflowRecord[trans.target.name][run, period] = \
                releases[trans.target]
                
        return releases


     
class LocalRelease(object):
    """ Describes after what period how much of the material stored is released
    from stock. To use, implement subclasses. 
    """
    def __init__(self):  
        self.releaseList = 0


    def getImmediateReleaseRate(self):
            return self.releaseRatesList[0]
            
    def scheduleFutureRelease(self, currentRun, currentPeriod, storedAmt):
        remainder = 1- self.releaseRatesList[0]
        per = currentPeriod + 1
        i = 1     
        while per < len(self.releaseList[currentRun]) and \
        i < len(self.releaseRatesList):
            self.releaseList[currentRun, per] = \
            self.releaseList[currentRun, per] + \
            storedAmt*min(self.releaseRatesList[i], remainder)
            remainder = remainder - min(self.releaseRatesList[i], remainder)
            i+=1
            per+=1

 
 
class FixedRateRelease(LocalRelease):
    """ A material release plan with constant rate after a delay period. \
    Values are rounded to full periods.  
    
    Parameters:        
    ----------------
    releaseRate: float 
        periodic release rate 
    delay: Integer 
        delay time in periods, befor the release starts. 
    
    """
    
    def __init__(self, releaseRate = 1, delay = 0):
        super(FixedRateRelease, self).__init__()
        self.releaseRatesList = []
        remainder = 1
        
        while (remainder > 0):
            if releaseRate < remainder:
                self.releaseRatesList.append(releaseRate)
            else:
                self.releaseRatesList.append(remainder)
            remainder = remainder - releaseRate    
        delayArray = np.zeros(delay)        
        self.releaseRatesList = np.concatenate((delayArray, 
                                                self.releaseRatesList)) 


           
class ListRelease(LocalRelease):
    """ A material release plan with a defined list of partial release rates 
    after a delay period
    
    Parameters:        
    ----------------
    releaseRatesList: list<float>
        list of release rates of a stored material in future periods. 
    delay: Integer 
        delay time in periods, befor the release starts. 

    """
    
    def __init__(self, releaseRatesList = [1], delay = 0):
        super(ListRelease, self).__init__()
        delayArray = np.zeros(delay)
        
        self.releaseRatesList = np.concatenate((delayArray, releaseRatesList))
        
        

class FunctionRelease(LocalRelease):
    """ A material release plan based on a distribution function that returns
    a release rate for every period. The time instant of the release is
    relative to the time of material storage in the stock. 
    
    Parameters:        
    ----------------
    releaseFunction: function 
        function that returns the relative release rate for a period        
    delay: Integer 
        delay time in periods, befor the release starts.  
    """
    def __init__(self, releaseFunction, delay = 0):        
        super(FunctionRelease, self).__init__()        
        self.releaseRatesList = []        
        self.totRelease = 0
        self.currentPeriod = 0
        self.lastNonZero = 0 
        
        delayArray = np.zeros(delay)
                                          # MAX period if no total release      
        while self.totRelease < 1 and self.currentPeriod < 500:
            currentRelease = releaseFunction(self.currentPeriod)            
            self.releaseRatesList.append(currentRelease)
            if currentRelease != 0:
                self.lastNonZero = self.currentPeriod
            self.totRelease += currentRelease
            self.currentPeriod +=1
    
        
        if self.currentPeriod-1 != self.lastNonZero:
            self.releaseRatesList = self.releaseRatesList[:self.lastNonZero+1]            
        
        if self.totRelease > 1: 
            self.releaseRatesList[-1] += 1-self.totRelease
            
        # modified by RoBa, January 2016:
        # before: self.releaseList = np.concatenate(...)
        self.releaseRatesList = np.concatenate((delayArray, self.releaseRatesList))
            


# added by RoBa, December 2015
class PeriodDefinedRelease(LocalRelease):
    """ A material release plan based on a distribution function that returns
    a release rate for every period. The time instant of the release is
    relative to the time of material storage in the stock.
    In contrast to other LocalRelease subclasses, the PeriodDefinedRelease
    class offers the possibility to choose different distribution functions
    for every target and every period.
    
    Parameters:        
    ----------------
    target: components.Compartment
        the release's target Compartment
    releaseFunctionList: list<function> 
        for every period a function that returns the relative release rate
        for a period    
    delayList: list<Integer> 
        a delay time (in periods) for every period, befor the release starts.  
    """
        
    def __init__(self, target, releaseFunctionList, delayList = []):
        super(PeriodDefinedRelease, self).__init__()
        self.target = target
        self.releaseFunctions = releaseFunctionList
        self.releaseRatesList = []
        self.delays = delayList
        self.releaseList = []
                
        if len(self.releaseFunctions) == len(self.delays):
            self.numPeriods = len(self.delays)            
            self.delayArrays = []
                        
            for p in range(self.numPeriods):
                tempDelayArray = np.zeros((self.delays[p]))
                self.delayArrays.append(tempDelayArray)
                self.tempRatesArray = []
                self.totRelease = 0
                self.currentPeriod = 0
                self.lastNonZero = 0
                
                                          # MAX period if no total release      
                while self.totRelease < 1 and self.currentPeriod < 500:
                    currentRelease = \
                    self.releaseFunctions[p](self.currentPeriod)
                    self.tempRatesArray.append(currentRelease)
                    if currentRelease != 0:
                        self.lastNonZero = self.currentPeriod
                    self.totRelease += currentRelease
                    self.currentPeriod +=1

                if self.currentPeriod-1 != self.lastNonZero:
                    self.tempRatesArray = \
                    self.tempRatesArray[:self.lastNonZero+1]            
        
                if self.totRelease > 1: 
                    self.tempRatesArray[-1] += 1-self.totRelease

                if len(self.delayArrays[p]) != 0:
                    tempArray = []
                    tempArray.extend(self.delayArrays[p])
                    tempArray.extend(self.tempRatesArray)
                    self.releaseRatesList.append(tempArray)
                else:
                    self.releaseRatesList.append(self.tempRatesArray)

        
    def getImmediateReleaseRate(self):
        """ in contrary to 'getImmediateReleaserate(self)' of other subclasses of
        the class LocalRelease, returns a list of immediate rates instead of
        a single rate
        """
        immediateRates = []
        for p in range(self.numPeriods):
            immediateRates.append(self.releaseRatesList[p][0])
            
        return immediateRates

    
    def scheduleFutureRelease(self, currentRun, currentPeriod, storedAmt):
        remainder = 1 - self.releaseRatesList[currentPeriod][0]
        per = currentPeriod + 1
        i = 1     
        while per < len(self.releaseList[currentRun]) and \
        i < len(self.releaseRatesList[currentPeriod]):
            self.releaseList[currentRun, per] = \
            self.releaseList[currentRun, per] + \
            storedAmt*min(self.releaseRatesList[currentPeriod][i], remainder)
            remainder = \
            remainder - min(self.releaseRatesList[currentPeriod][i], remainder)
            i+=1
            per+=1
      
        

class Transfer(object):
    """ A transfer object determines the relative rate of a total material flow
    that is transfered from one Compartment to another. The priority denotes
    the relative credibility of the assumed values and can be used for the 
    adjustment of contradictory dependent TCs. 
    
    To implement, use subclass. 
    """
    def __init__(self, target, priority):
        self.target = target
        self.priority = priority
        self.currentTC = 0
    def sampleTC(self):
         print('To be implemented in Subclass')
    def getCurrentTC(self):
         return self.currentTC
         

class ConstTransfer(Transfer):
    """ A Transfer with a deterministic TC. 
    
    Parameters:        
    ----------------    
    value: float
        determinstic value for the transfer coefficient
    target: components.Compartment
        specifies the target compartment of the transfer
    priority: integer
        if the sum of the transfer coefficients from a compartment are \
        normalized, a higher priority excludes the value from adjustment         
    
    """

    def __init__(self, value, target, priority=1):
        super(ConstTransfer, self).__init__(target, priority)
        self.value = value        
        self.currentTC = value     
    def sampleTC(self):
        """ assign the constant value as current TC """
        self.currentTC = self.value
        

class StochasticTransfer(Transfer):
    """ A Transfer Coefficient determined by an underlying probability \
    distribution 
    
    Parameters:        
    ----------------
    function: probability density function 
        probability distribution function (e.g. from scipy.stats) to sample \
        random values for the transfer coefficient
    parameters: list<float>
        parameter list of the probability distribution function     
    target: components.Compartment
        specifies the target compartment of the transfer
    priority: integer
        if the sum of the transfer coefficients from a compartment are \
        normalized, a higher priority excludes the value from adjustment  
     
    """
    def __init__(self, function, parameters, target,  priority=1):
        super(StochasticTransfer, self).__init__(target, priority)
        self.function = function 
        self.parameters = parameters
    def sampleTC(self):
        """ samples a random value from the probability distribution as current 
        TC
        """
        self.currentTC = self.function(*self.parameters)


class RandomChoiceTransfer(Transfer):
    """ A Transfer Coefficient determined by a given sample. 
    
        Parameters:        
        ----------------
        sample: list<float>
            a given sample of values from which is randomly drawn
        target: components.Compartment
            specifies the target compartment of the transfer
        priority: integer
            if random values for the transfer coefficients are normalized, \
            a higher priority excludes the value from adjustment 
    
    """
    def __init__(self, sample, target, priority=1):
        super(RandomChoiceTransfer, self).__init__(target, priority)
        self.sample = sample
    def sampleTC(self):
        """ Randomly assigns one value from the sample as current TC"""
        self.currentTC = np.random.choice(self.sample)
  
              
class AggregatedTransfer(Transfer):
    """ A Transfer Coefficient from a combined set of several given samples \
    and or probability distributin functions. A weighting factor for the \
    partial samples can be defined. 

    Parameters:        
    ----------------
    partialDistributions: list<Transfer>
        a list of SochasticTransfers and/or RandomChoiceTransfers to be \
        considered in the combined distribution
    weightingFactors: list<float>
        list of weighting factors
    target: components.Compartment
        specifies the target compartment of the transfer
    priority: integer
        if random values for the transfer coefficients are normalized, \
        a higher priority excludes the value from adjustment 
    """
    
    def __init__(self, target, singleTransfers, weights = None, priority=1):
        super(AggregatedTransfer, self).__init__(target, priority)        
        self.singleTransfers = singleTransfers
        if weights != None:
            self.weights = weights
        else:
            self.weights = [1]*len(singleTransfers)
        
    def sampleTC(self):
        #An array of the weights, cumulatively summed.
        cs = np.cumsum(self.weights)
        total = sum(self.weights)  
        #Find the index of the first weight over a random value.
        ind = sum(cs < np.random.uniform(0, total))
        transfer = self.singleTransfers[ind]
        transfer.sampleTC()
        self.currentTC = transfer.getCurrentTC()



# added by RoBa, November 2015
class PeriodDefinedTransfer(Transfer):
    """ A PeriodDefinedTransfer object determines the relative rates of a
    total material flow that is transfered from one Compartment to another for
    every single period. A single rate can be determined deterministic,
    stochastic or by draw from a list of TCs. The priorities denote the
    relative credibilities of the assumed values and can be used for the
    adjustment of contradictory dependent TCs for each period. 
    
    Parameters:
    ----------------
    target: components.Compartment
        specifies the target compartment of the transfer
    functionList: list<function> 
        functions for every single period to generate a value for the
        transfer coefficient
    parameterList: list<list<float>>
        parameters for the functions in functionList for each period.
    priorityList: list<integer>
        the list consists of every period's priority.
        The sum of the transfer coefficients from a compartment is normalized,
        a higher priority excludes the value from adjustment
    priority: integer
        has no meaning within this subclass, each period's priority is set by
        the priorityList
    """
    
    def __init__(self, target, functionList = [], parameterList = [], 
                 priorityList = [], priority = 1):
        super(PeriodDefinedTransfer, self).__init__(target, priority)
        self.functions = functionList
        self.parameters = parameterList
        self.priorities = priorityList
        
    def sampleTC(self, period):
        
        listLength = len(self.priorities)
        
        if listLength == len(self.functions) and \
           listLength == len(self.parameters):
            if period < listLength:
                self.priority = self.priorities[period]
                tempList = []
                x=0
                # workaround for random choice function
                while x < len(self.parameters[period]):
                    tempList.append(x)
                    x += 1
                if self.functions[period] == np.random.choice:
                    i = np.random.choice(tempList)
                    self.currentTC = self.parameters[period][i]
                else:
                    self.currentTC = \
                    self.functions[period](*self.parameters[period])
                
            else:
                print('too many periods or too few transfers')
        else:
            print ('missing some functions,  parameters or priorities')
            

    
class SinglePeriodInflow(object):
    """ A single inflow represents the inflow of material to the model in one \
    single period. To implement material inflows to the system over the entire\
    simulated time implement ExternalListInflow or ExternalFunctionInflow
    
    To implement use subclass
    
    """
    def __init__(self):
        self.currentValue = None
    
    def sampleValue(self):
        pass
    
    def getValue(self):
        return self.currentValue



class StochasticFunctionInflow(SinglePeriodInflow):
    """ External inflow to a compartment of one Period. Uncertatinty about\
    the true value of this inflow is represented as probability distribution\
    function.
    
    Parameters:
    ----------------
    ProbabilityDistribution: probability density function
        probability distribution (e.g. from scipy.stats) to represent uncertain
        knowledge about the true value of the inflow 
    values: list<float>
        parameter list of the distribution function.   
    
    """    
    def __init__(self, probabilityDistribution, parameters):
        super(StochasticFunctionInflow, self).__init__()
        self.pdf = probabilityDistribution
        self.parameterValues = parameters       
        
    def sampleValue(self): 
        self.currentValue = self.pdf(*self.parameterValues)
    
    
    
class RandomChoiceInflow(SinglePeriodInflow):
    """ External inflow to a compartment in one Period. Uncertatinty about\
    the true value of this inflow is represented as a sample representing the\
    the assumptions about the true value. 
    
    Parameter:
    ----------------
    sample: list<float>
        sample to draw random value from        
    """    
    def __init__(self, sample):
        super(RandomChoiceInflow, self).__init__()
        self.sample = sample  

    def sampleValue(self):
        self.currentValue = np.random.choice(self.sample)
        
        
    
class FixedValueInflow(SinglePeriodInflow):
    """ External inflow amount to a compartment in one Period. 
    
    Parameter:
    ----------------
    value: float
        the inflow value  
    """    
    def __init__(self, value):
        super(FixedValueInflow, self).__init__()
        self.currentValue = value

    def getValue(self):
        return self.currentValue




class ExternalInflow(object):
    """ Represents the external material inflow to the observed system. 
        
    To implement, please use subclass     
    """   
    def __init__(self, target, derivationDistribution, derivationParameters, 
                 startDelay):
        self.target = target
        self.startDelay = startDelay
        self.derivationDistribution = derivationDistribution
        self.derivationParameters = derivationParameters
        self.derivationFactor = 1
        
    def getCurrentInflow(self, period):  
        pass


class ExternalListInflow(ExternalInflow):
    """ Source of external inflows as a list of material amounts for each \
    period considered in the model. 

        Parameters:        
        ----------------
        target: components.Compartment
            target compartment of the external inflow.
        inflowList: list<SingleInflow>
            list of Single Inflow elements for each period
        derivationDistribution: probability density function
            probability distribution (e.g. from scipy.stats) to represent \
            uncertain knowledge about the true value of the model inflows. \
            The derivation is calculated once per simulation run and applied \
            to the whole inflow list
        derivationParameters: list<float>
            parameter list of the probability distribution function of the \
            derivation             
        startDelay: integer
            time lag between the simulation start and the first release from \
            the source.           
    """  
 
    def __init__(self, target, inflowList, derivationDistribution= None, 
                 derivationParameters=[], startDelay = 0):
        super(ExternalListInflow, self).__init__(target, 
                derivationDistribution, derivationParameters, startDelay)
        self.inflowList = inflowList
        
        for i in range(len(self.inflowList)):            
            if isinstance(self.inflowList[i], (int, float, list)):
#                self.inflowList[i] = SinglePeriodInflow(self.inflowList[i])
                self.inflowList[i] = FixedValueInflow(self.inflowList[i])

    def __repr__(self):
        return(str(self.inflowList[0].currentValue))

        
    def getCurrentInflow(self, period = 0):
        """ determines the inflow for a given period"""

        if period - self.startDelay < 0:
            return 0         
        else:
            if (period-self.startDelay) < len(self.inflowList):
                returnValue = \
                self.inflowList[(period-self.startDelay)].getValue()*\
                self.derivationFactor                
                if returnValue >=0:
                    return returnValue
                else: 
                    return 0               
            else:
                return 0


    def sampleValues(self):
        for inf in self.inflowList:
            inf.sampleValue()
        if self.derivationDistribution != None: 
            self.derivationFactor = \
            self.derivationDistribution(*self.derivationParameters)


class ExternalFunctionInflow(ExternalInflow):

    """ External source; mean inflow amounts as function of time, relative \
    derivation from stochastic distribution. delay function. 
        
    Parameters:
    --------------
    target: components.Compartment
        target compartment of the external inflow.
    basicInflow: components.SingleInflow
        initial inflow to the system in the first period
    inflowFunction: function
        returns a material amount as inflow for a specific period; gets basic\ 
        Value and period number as input. If no input function is defined, \
        the basic value is used for all periods. 
    derivationDistribution: probability density function
        probability distribution (e.g. from scipy.stats) to represent \
        uncertain knowledge about the true value of the model inflows. The \
        derivation is calculated once per simulation run and applied to the \
        whole inflow list
    derivationParameters: list<float>
        parameter list of the probability distribution function of the \
        derivation               
    startDelay: integer
        time lag between the simulation start and the first release from the \
        source.    
        
    """
    def __init__(self, target, basicInflow, inflowFunction = None, 
                 defaultInflowFunction= 0, derivationDistribution = None,
        derivationParameters=[], startDelay=0):
        super(ExternalFunctionInflow, self).__init__(target, 
                derivationDistribution, derivationParameters, startDelay) 
        if inflowFunction == None:
            self.inflowFunction = self.defaultInflowFunction
        else:
            self.inflowFunction = inflowFunction
        
        if isinstance(basicInflow, (int, float, list)):        
            self.basicInflow = SinglePeriodInflow(basicInflow)
        else:
            self.basicInflow = basicInflow


    def getCurrentInflow(self, period= 0):
        if period - self.startDelay < 0:
            return 0
        else:
            #return self.inflowFunction(self.baseValue, 
            #                   period-self.startDelay)*self.derivationFactor
            returnValue = self.inflowFunction(self.baseValue, 
                            period-self.startDelay)*self.derivationFactor
            print(self.inflowFunction(self.baseValue,period-self.startDelay))
            print(self.derivationFactor)
            if returnValue >= 0:
                return returnValue
            else:
                return 0
    
    def sampleValues(self):    
        self.basicInflow.sampleValue()
        self.baseValue = self.basicInflow.getValue()
        if self.derivationDistribution != None:  
            self.derivationFactor = \
            self.derivationDistribution(*self.derivationParameters)


    def defaultInflowFunction(self, base, period):
        return base
       
              