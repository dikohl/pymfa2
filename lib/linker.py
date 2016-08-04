#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created in February 2016

@author: RoBa

The linker module serves as link to the dpmfa_simulator. It takes the imported
data and generates the needed compartments, transfers, and release strategies.
Then it sets the dpmfa model and runs the simulator.
"""



from copy import copy, deepcopy
import numpy as np
from .dpmfa_simulator import simulator as sim
from .dpmfa_simulator import model as model
from .dpmfa_simulator import components as cp
from . import adjusted_functions_ExtDiskret as af



class NodeData(object):
  def __init__(self, nodeName, material, unit):
    self.name = copy(nodeName)
    self.material = copy(material)
    self.unit = copy(unit)
    self.type = "no type"


class InflowData(NodeData):
  def __init__(self, nodeName, dstName, material, unit, inflows = [],
               description = ''):
    super(InflowData, self).__init__(nodeName, material, unit)
    self.target = deepcopy(dstName + '_' + material + '_' + unit)
    self.inflows = deepcopy(inflows)
    self.description = copy(description)
    self.type = "inflow"
  
  
class RateData(NodeData):
  def __init__(self, nodeName, material, unit, nodeType = "no type",
               transfers = {}, descriptions = {}):
    super(RateData, self).__init__(nodeName, material, unit)
    self.name = deepcopy(nodeName + '_' + material + '_' + unit)
    self.category = copy(nodeName)
    self.transfers = deepcopy(transfers)
    self.descriptions = copy(descriptions)
    self.type = nodeType  # later defined as 'conversion', 'fraction' or 'rate'


class DelayData(NodeData):
  def __init__(self, nodeName, material, unit, transfers = {},
               releases = {}, descriptions = {}):
    super(DelayData, self).__init__(nodeName, material, unit)
    self.name = deepcopy(nodeName + '_' + material + '_' + unit)
    self.category = copy(nodeName)
    self.transfers = deepcopy(transfers)
    self.releases = deepcopy(releases)
    self.descriptions = copy(descriptions)
    self.type = "delay"


class SinkData(NodeData):
  def __init__(self, nodeName, material, unit):
    super(SinkData, self).__init__(nodeName, material, unit)
    self.name = deepcopy(nodeName + '_' + material + '_' + unit)
    self.category = copy(nodeName)

class System(object):
  def __init__(self):
    self.runs = -99
    self.periods = -99
    self.median = False
    self.percentiles = []
    self.timeSpanPlots = []
    self.timeIndices = []
    self.nodes = {}
    self.inflows = {}
    self.rates = {}
    self.delays = {}
    self.sinks = {}
    self.links = []
    self.entropy = False

    self.Hmax = -99
    self.metadataMatrix = []
    self.entropyInflows = []
    

  def run(self):
    """Runs the dpmfa simulator with the gathered data."""
    
    print('\n               creating model...')
    print('0%                                              100%')
    
    # create dpmfa model
    dpmfaModel = model.Model("Model 1")
    
    self.dpmfaCompartments = {}
    self.dpmfaSinglePeriodInflows = {}
    self.dpmfaListInflows = []
    self.functionsDict = {}
    self.parametersDict = {}
    self.prioritiesDict = {}

    # create flow compartments, stocks and sinks out of the gathered data
    for node in list(self.rates.keys()):
      if self.rates[node].type in ["rate", "fraction"]:
        newCompartment = \
        cp.FlowCompartment(node, logInflows=True, logOutflows=True,
                adjustOutgoingTCs=True, categories=[self.rates[node].category])
        self.dpmfaCompartments[node] = deepcopy(newCompartment)
      elif self.rates[node].type == "conversion":
        newCompartment = \
        cp.FlowCompartment(node, logInflows=True, logOutflows=True,
               adjustOutgoingTCs=False, categories=[self.rates[node].category])
        self.dpmfaCompartments[node] = deepcopy(newCompartment)
      else:
        raise RunException(
              ("\n--------------------\n" +
               "ERROR:\nUnexpected node type in core.rates, got '%s'. Only " +
               "the types 'rate', 'fraction' and 'conversion' are allowed.")
               % (self.rates[node].type))

    print("|", end="")  # displays progress step 1
    for node in list(self.delays.keys()):
      if self.delays[node].type == "delay":
        newStock = \
        cp.TDRStock(node, logInflows=True, logOutflows=True,
                    categories=[self.delays[node].category])
        self.dpmfaCompartments[node] = deepcopy(newStock)
      else:
        raise RunException(
              ("\n--------------------\n" +
               "ERROR:\nUnexpected node type in core.delays, got '%s'. " +
               "Only type 'delay' is allowed.")
               % (self.delays[node].type))

    for node in list(self.sinks.keys()):
      newSink = \
      cp.Sink(node, logInflows=True, categories=[self.sinks[node].category])
      self.dpmfaCompartments[node] = deepcopy(newSink)
      
    # create and log external inflows to the system
    for node in list(self.inflows.keys()):
      srcNode = self.inflows[node]
      targ = srcNode.target
      if targ not in list(self.dpmfaCompartments.keys()):
        raise RunException(
              ("\n--------------------\n" +
               "ERROR:\nTarget node for inflow not found.\ninflow: %s\n" +
               "target node: %s")
               % (self.inflows[node].nodeName, targ))
      self.dpmfaSinglePeriodInflows[node] = []
      for i in range(len(srcNode.inflows)):
        if srcNode.inflows[i][0] == "fix":
          self.dpmfaSinglePeriodInflows[node].append(
                                    cp.FixedValueInflow(srcNode.inflows[i][1]))
        elif srcNode.inflows[i][0] == "stoch":
          if srcNode.inflows[i][1] == "normal":
            self.dpmfaSinglePeriodInflows[node].append(
                            cp.StochasticFunctionInflow(np.random.normal,
                                                        srcNode.inflows[i][2]))
          elif srcNode.inflows[i][1] == "triangular":
            self.dpmfaSinglePeriodInflows[node].append(
                            cp.StochasticFunctionInflow(np.random.triangular,
                                                        srcNode.inflows[i][2]))
          elif srcNode.inflows[i][1] == "uniform":
            self.dpmfaSinglePeriodInflows[node].append(
                            cp.StochasticFunctionInflow(np.random.uniform,
                                                        srcNode.inflows[i][2]))
          else:
            raise RunException(
                  ("\n--------------------\n" +
                   "ERROR:\nUnexpected probability distribution function " +
                   "for '%s', got '%s'.") % (node, srcNode.inflows[i][1]))
        elif srcNode.inflows[i][0] == "rand":
          self.dpmfaSinglePeriodInflows[node].append(
                                  cp.RandomChoiceInflow(srcNode.inflows[i][1]))
        else:
          raise RunException(
                ("\n--------------------\n" +
                 "ERROR:\nUnexpected inflow value type for '%s', got '%s'.")
                 % (node, srcNode.inflows[i][0]))
        
      self.dpmfaListInflows.append(cp.ExternalListInflow(
                    self.dpmfaCompartments[targ],
                    list(inf for inf in self.dpmfaSinglePeriodInflows[node])))


    # create transfers for 'rate' nodes (incl. 'conversion' + 'fraction' nodes)
    print("|", end="")  # displays progress step 2
    for node in list(self.rates.keys()):
      srcNode = self.rates[node]
      for n, targ in enumerate(srcNode.transfers.keys()):
        self.functionsDict[node, targ] = []
        self.parametersDict[node, targ] = []
        self.prioritiesDict[node, targ] = []
        if targ in list(self.dpmfaCompartments.keys()):
            
          for i in range(len(srcNode.transfers[targ])):
            if srcNode.transfers[targ][i][0] == "fix":
              self.functionsDict[node, targ].append(af.fixedRate)
              self.parametersDict[node, targ].append(
                                                 srcNode.transfers[targ][i][1])
              self.prioritiesDict[node, targ].append(
                                                 srcNode.transfers[targ][i][2])
            elif srcNode.transfers[targ][i][0] == "stoch":
              if srcNode.transfers[targ][i][1] == "normal":
                self.functionsDict[node, targ].append(np.random.normal)
              elif srcNode.transfers[targ][i][1] == "triangular":
                self.functionsDict[node, targ].append(np.random.triangular)
              elif srcNode.transfers[targ][i][1] == "uniform":
                self.functionsDict[node, targ].append(np.random.uniform)
              else:
                raise RunException(
                      ("\n--------------------\n" +
                       "ERROR:\nUnexpected probability distribution function" +
                       ", got '%s'.\nlink: '%s' -> '%s'")
                       % (srcNode.transfers[targ][i][1], node, targ))

              self.parametersDict[node, targ].append(
                                                 srcNode.transfers[targ][i][2])
              self.prioritiesDict[node, targ].append(
                                                 srcNode.transfers[targ][i][3])
            elif srcNode.transfers[targ][i][0] == "rand":
              self.functionsDict[node, targ].append(np.random.choice)
              self.parametersDict[node, targ].append(
                                                 srcNode.transfers[targ][i][1])
              self.prioritiesDict[node, targ].append(
                                                 srcNode.transfers[targ][i][2])
            else:
              raise RunException(
                    ("\n--------------------\n" +
                     "ERROR:\nUnexpected transfer value type, got '%s'.\n" +
                     "link: '%s' -> '%s'")
                     % (srcNode.transfers[targ][i][0], node, targ))
                               
        else:
          raise RunException(
                ("\n--------------------\n" +
                 "ERROR:\nTarget node not found.\nsource node: %s\n" +
                 "target node: %s")
                 % (node, targ))
                 
        # append the transfers to the dpmfa compartments
        newTransfer = \
        cp.PeriodDefinedTransfer(self.dpmfaCompartments[targ],
                                 self.functionsDict[node, targ],
                                 self.parametersDict[node, targ],
                                 self.prioritiesDict[node, targ])
        
        self.dpmfaCompartments[node].transfers.append(newTransfer)
        newTransfer = None
        del newTransfer

    # preparations for displaying the remaining progress steps
    currentStep = 0
    lastIncrease = 0
    signsToPrint = 47  # actually 50 but 3 are already printed / will be printed
    totalSteps = 0
    for node in list(self.delays.keys()):  # calculation of the number of steps
      srcNode = self.delays[node]
      for targ in list(srcNode.transfers.keys()):
        if targ in list(self.dpmfaCompartments.keys()):
          totalSteps += 2
          
    # create transfers and release strategies for 'delay' nodes
    for node in list(self.delays.keys()):
      srcNode = self.delays[node]
      for targ in list(srcNode.transfers.keys()):
        if targ in list(self.dpmfaCompartments.keys()):
            
          if len(srcNode.transfers[targ]) != len(srcNode.releases[targ]):
            raise RunException(
                  ("\n--------------------\n" +
                   "ERROR:\nNot the same number of transfers and releases " +
                   "for the following delayed transfer:\n'%s' -> '%s'")
                   % (node, targ))
          functionList = []
          parameterList = []
          priorityList = []
          releaseFunctionList = []
          delayList = []

          # create and log transfers and releases for every period
          for i in range(len(srcNode.transfers[targ])):
            # create and log transfers
            if srcNode.transfers[targ][i][0] == "fix":
              functionList.append(af.fixedRate)
              parameterList.append(srcNode.transfers[targ][i][1])
              priorityList.append(srcNode.transfers[targ][i][2])
            elif srcNode.transfers[targ][i][0] == "stoch":
              if srcNode.transfers[targ][i][1] == "normal":
                functionList.append(np.random.normal)
              elif srcNode.transfers[targ][i][1] == "triangular":
                functionList.append(np.random.triangular)
              elif srcNode.transfers[targ][i][1] == "uniform":
                functionList.append(np.random.uniform)
              else:
                raise RunException(
                      ("\n--------------------\n" +
                       "ERROR:\nUnexpected probability distribution function" +
                       ", got '%s'.\nlink: '%s' -> '%s'")
                       % (srcNode.transfers[targ][i][1], node, targ))
              parameterList.append(srcNode.transfers[targ][i][2])
              priorityList.append(srcNode.transfers[targ][i][3])
            elif srcNode.transfers[targ][i][0] == "rand":
              functionList.append(np.random.choice)
              parameterList.append(srcNode.transfers[targ][i][1])
              priorityList.append(srcNode.transfers[targ][i][2])
            else:
              raise RunException(
                    ("\n--------------------\n" +
                     "ERROR:\nUnexpected transfer value type, got '%s'.\n" +
                     "link: '%s' -> '%s'")
                     % (srcNode.transfers[targ][i][0], node, targ))

            # create and log releases      
            releaseParameters = srcNode.releases[targ][i][1]
            if srcNode.releases[targ][i][0] == "fix":
              releaseFunctionList.append(
                      af.ReleaseFunction(releaseParameters).fixedRateRelease)
            elif srcNode.releases[targ][i][0] == "list":
              releaseFunctionList.append(
                      af.ReleaseFunction(releaseParameters).listRelease)
            elif srcNode.releases[targ][i][0] == "rand":
              releaseFunctionList.append(
                      af.ReleaseFunction(releaseParameters).randomRateRelease)
            elif srcNode.releases[targ][i][0] == "weibull":
              releaseFunctionList.append(
                          af.ReleaseFunction(releaseParameters).weibullRelease)
            else:
              raise RunException(
                    ("\n--------------------\n" +
                     "ERROR:\nUnexpected release function, got '%s'.\n" +
                     "link: '%s' -> '%s'")
                     % (srcNode.releases[targ][i][0], node, targ))
            # log delay
            delayList.append(srcNode.releases[targ][i][2])


          # append the transfers to the compartments
          self.dpmfaCompartments[node].transfers.append(
                         cp.PeriodDefinedTransfer(self.dpmfaCompartments[targ],
                         functionList, parameterList, priorityList))

          # print progress
          if signsToPrint != 0 and currentStep+1-lastIncrease >= float(totalSteps)/signsToPrint:
            progress = int((currentStep+1-lastIncrease)/(float(totalSteps)/signsToPrint))
            totalSteps -= 1
            signsToPrint -= progress
            lastIncrease += 1
            currentStep += 1
            print("|" * progress, end="")
            
          # append the releases to the compartments
          self.dpmfaCompartments[node].localReleaseList.append(
                          cp.PeriodDefinedRelease(self.dpmfaCompartments[targ],
                          releaseFunctionList, delayList))
                          
          # print progress
          if signsToPrint != 0 and currentStep+1-lastIncrease >= float(totalSteps)/signsToPrint:
            progress = int((currentStep+1-lastIncrease)/(float(totalSteps)/signsToPrint))
            totalSteps -= 1
            signsToPrint -= progress
            lastIncrease += 1
            currentStep += 1
            print("|" * progress, end="")
            
            
        else:
          raise RunException(
                ("\n--------------------\n" +
                 "ERROR:\nTarget node not found.\nsource node: %s\n" +
                 "target node: %s")
                 % (node, targ))


    print("|\n")  # prints the last progress step

    # add compartments and inflows to the model
    compartmentList = []
    for n in list(self.dpmfaCompartments.keys()):
      compartmentList.append(self.dpmfaCompartments[n])

    dpmfaModel.setCompartments(compartmentList)  

    dpmfaModel.setInflows(self.dpmfaListInflows)

    dpmfaModel.checkModelValidity()
    
    # create the dpmfa simulator
    simulator = sim.Simulator(self.runs, self.periods, 1, False, True)
    
    # connect the dpmfa model to the simulator
    simulator.setModel(dpmfaModel)
    
    # run Monte-Carlo simulation process
    simulator.runSimulation()

    self.entropyInflows = dpmfaModel.getInflows()
    
    return simulator



class RunException(Exception):
  pass

