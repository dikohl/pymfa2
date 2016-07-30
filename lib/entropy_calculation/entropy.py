#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created April 2016

@author: dikohl

The entropy module contains the class EntropyCalc to compute the statistical entropy of a material flow system.

The class gets the necessary data to calculate the statistical entropy directly from the simulation
and where needed the concentration of a substance from the source file.
"""

import numpy as np

from lib.entropy_calculation.flow import Flow
from lib.entropy_calculation.period import Period
from lib.entropy_calculation.conversion import Conversion
from lib.entropy_calculation.result import Result, StageResult


class Entropy:
    def __init__(self, system, simulator, substanceConcentration):
        self.periods = []
        self.conversions = []
        self.flowValues = {}
        self.concentrationValues = substanceConcentration
        self.Hmax = system.Hmax

        self.shouldCalculate = system.entropy

        self.timeIndices = system.timeIndices
        for timeIndex in self.timeIndices:
            period = Period(timeIndex)
            self.periods.append(period)

        self.addedSubstanceFlows = [0] * len(self.timeIndices)

        # get the mean of every flow in the simulation
        for comp in simulator.flowCompartments:
            for key in list(comp.outflowRecord.keys()):
                self.flowValues[comp.name, key] = []
                self.flowValues[comp.name, key].append(np.mean(comp.outflowRecord[key], axis=0).tolist())

        self.metadataMatrix = system.metadataMatrix
        self.fillPeriods()

    def fillPeriods(self):
        for i in range(len(self.metadataMatrix)):
                transferType = self.metadataMatrix[i][0]
                if transferType.lower() == "concentration" or transferType.lower() == "inflow":
                    continue
                stages = self.metadataMatrix[i][7].split("|")
                if '' in stages:
                    continue
                srcName = self.metadataMatrix[i][1]
                srcUnit = self.metadataMatrix[i][3]
                destName = self.metadataMatrix[i][4]
                destUnit = self.metadataMatrix[i][6]

                sourceName = (self.metadataMatrix[i][1] + "_" +
                           self.metadataMatrix[i][2] + "_" +
                           self.metadataMatrix[i][3]).lower()
                targName = (self.metadataMatrix[i][4] + "_" +
                            self.metadataMatrix[i][5] + "_" +
                            self.metadataMatrix[i][6]).lower()
                values = self.flowValues[sourceName, targName][0]
                concentrations = self.concentrationValues.get((sourceName, targName),[0] * (len(self.periods)))
                if transferType.lower() == "conversion":
                    self.conversions.append(Conversion(srcUnit, destUnit, values))
                else:
                    for j in range(len(self.periods)):
                        flow = Flow(transferType,srcName,srcUnit,destName,destUnit,stages,values[j],concentrations[j])
                        self.periods[j].addFlow(flow)

        for i in range(len(self.periods)):
            #see in export if we should use "stock" form stockValues or "delay" from flowValues
            #self.periods[i].setStockValues()
            self.periods[i].convertUnits(self.conversions,i)

class EntropyCalc(object):
    #initiate EntropyCalc with the values of all the material flows, substance flows and concentrations
    def __init__(self, entropy):
        self.entropy = entropy

    def computeEntropy(self):
        result = Result()
        for period in self.entropy.periods:
            for stage in period.stages.keys():
                stageObj = period.stages[stage]
                stageSum = stageObj.getSubstanceFlowSum()
                for flow in stageObj.flows:
                    if stageSum == 0:
                        flow.Mi = 0
                    else:
                        flow.Mi = flow.materialFlow/stageSum
                    if flow.concentration == 0:
                        flow.HIIi = 0
                    else:
                        flow.HIIi = float(flow.concentration)*(-flow.Mi)*np.log2(float(flow.concentration))
                    #if period.year == 2012 and stage == "6" and flow.transferType.lower() == "delay":
                    #    print(flow)
                stageEntropy = stageObj.getHIIiSum()/self.entropy.Hmax
                result.append(StageResult(period.year,stage,stageEntropy))
        return result

class EntropyException(Exception):
    def __init__(self, error):
        self.error = error
        # pass