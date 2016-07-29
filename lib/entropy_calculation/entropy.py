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
from lib.entropy_calculation.result import Result


class Entropy:
    def __init__(self, system, simulator, substanceConcentration):
        self.periods = []
        self.conversions = []
        self.flowValues = {}
        self.concentrationValues = substanceConcentration
        self.Hmax = system.Hmax
        self.inflows = simulator.inflows

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
        for period in self.periods:
            for key in period.stages.keys():
                print(period.year)
                print(period.stages[key])

    def fillPeriods(self):
        for i in range(len(self.metadataMatrix)):
                transferType = self.metadataMatrix[i][0]
                if transferType.lower() == "inflow" or transferType.lower() == "concentration":
                    continue
                srcName = self.metadataMatrix[i][1]
                srcUnit = self.metadataMatrix[i][3]
                destName = self.metadataMatrix[i][4]
                destUnit = self.metadataMatrix[i][6]
                stages = self.metadataMatrix[i][7]

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
            self.periods[i].setStockValues()
            self.periods[i].convertUnits(self.conversions,i)

class EntropyCalc(object):
    #initiate EntropyCalc with the values of all the material flows, substance flows and concentrations
    def __init__(self, entropy):
        self.entropy = entropy

    def computeEntropy(self, materialFlows, stage):
        stageResults = dict()
        # get all necessary values for the calculation of the stage
        materialFlowMatrix, substanceFlowMatrix, concentrationMatrix = self.getCalcValues(materialFlows)
        sumSubstanceFlows = []

        for i in range(len(substanceFlowMatrix[0])):
            allMi = dict()
            allHIIi = dict()
            # sum all the substanceFloas in this stage and period
            substanceFlowPeriod = [sub[i] for sub in substanceFlowMatrix]
            if self.timeIndices[i] == 2012 and stage == 2:
                print(stage)
                print(materialFlowMatrix)
                print("_______")
                print(concentrationMatrix)
            sumSubstanceFlowsPeriod = np.sum(substanceFlowPeriod)

            # calculate the mi of the calculation
            for flow in materialFlowMatrix:
                mi = np.true_divide(flow[i + 2], sumSubstanceFlowsPeriod + self.addedSubstanceFlows[i])
                allMi[flow[0], flow[1]] = mi
                # if self.timeIndices[i] == 2012 and stage == 2:
                # print(allMi)

            # calculate HIIi
            for flow in materialFlowMatrix:
                concentration = float(concentrationMatrix[flow[0], flow[1]][i + 2])
                mi = allMi[flow[0], flow[1]]
                if concentration != 0:
                    tmp = np.multiply(-mi, concentration)
                    HIIi = np.multiply(tmp, np.log2(concentration))
                else:
                    HIIi = 0
                allHIIi[flow[0], flow[1]] = HIIi
                # if self.timeIndices[i] == 2012 and stage == 2:
                # print(concentration)
                # print(allHIIi)

            periodStageEntropy = np.true_divide(sum(list(allHIIi.values())), self.Hmax)
            stageResults[self.timeIndices[i]] = periodStageEntropy
            sumSubstanceFlows.append(sumSubstanceFlowsPeriod)
        # add the total substance flows of the previous stages to the substance flows of the current stage
        # for every period
        self.addedSubstanceFlows = [x + y for x, y in zip(self.addedSubstanceFlows, sumSubstanceFlows)]
        return stageResults


class EntropyException(Exception):
    def __init__(self, error):
        self.error = error
        # pass