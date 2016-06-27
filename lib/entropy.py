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

class EntropyCalc(object):
    #initiate EntropyCalc with the values of all the material flows, substance flows and concentrations
    def __init__(self, system, simulator, substanceConcentration):

        self.Hmax = system.Hmax

        self.shouldCalculate = system.entropy

        self.timeIndices = system.timeIndices
        self.conversions = dict()
        self.addedSubstanceFlows = [0]*len(self.timeIndices)

        #str(timeIndex) + str(simulator.model.getInflows())

        self.inflows = simulator.inflows

        #get the mean of every flow in the simulation
        self.flowValues = {}
        for comp in simulator.flowCompartments:
          for key in list(comp.outflowRecord.keys()):
            self.flowValues[comp.name, key] = []
            self.flowValues[comp.name, key].append(np.mean(comp.outflowRecord[key], axis=0).tolist())

        self.concentrationValues = substanceConcentration
        self.metadataMatrix = system.metadataMatrix

    # sort the metadata according to it's stages
    def run(self):

        results = dict()
        stages = dict()

        if not self.shouldCalculate:
            return results
        # get the conversion from one unit to another
        for i in range(len(self.metadataMatrix)):
            if self.metadataMatrix[i][0].lower() == 'conversion' and self.metadataMatrix[i][2] == \
                    self.metadataMatrix[i][5]:
                srcName = (self.metadataMatrix[i][1] + "_" +
                            self.metadataMatrix[i][2] + "_" +
                            self.metadataMatrix[i][3]).lower()
                targName = (self.metadataMatrix[i][4] + "_" +
                            self.metadataMatrix[i][5] + "_" +
                            self.metadataMatrix[i][6]).lower()
                self.conversions[self.metadataMatrix[i][3], self.metadataMatrix[i][6]] = \
                self.flowValues[srcName, targName][0]
                self.metadataMatrix.remove(self.metadataMatrix[i])

        # order flows by stages
        for metadata in self.metadataMatrix:
            metadataStages = [x for x in metadata[-2].split('|') if x]
            # every other flow is added to the correct stage
            for mStage in metadataStages:
                stages.setdefault(int(mStage),[]).append(metadata)
        # for every stage of stages calculate entropy
        for key in range(len(stages)):
            stageResult = self.computeSingleStage(stages[int(key) + 1],int(key)+1)
            results[int(key) + 1] = stageResult
        return results

    def computeSingleStage(self, materialFlows, stage):
        stageResults = dict()
        #get all necessary values for the calculation of the stage
        materialFlowMatrix, substanceFlowMatrix, concentrationMatrix = self.getCalcValues(materialFlows)
        sumSubstanceFlows = []
        
        for i in range(len(substanceFlowMatrix[0])):
            allMi = dict()
            allHIIi = dict()
            #sum all the substanceFloas in this stage and period
            substanceFlowPeriod = [sub[i] for sub in substanceFlowMatrix]
            #if self.timeIndices[i] == 2012 and stage == 2:
                #print(stage)
                #print(substanceFlowMatrix)
            sumSubstanceFlowsPeriod = np.sum(substanceFlowPeriod)

            #calculate the mi of the calculation
            for flow in materialFlowMatrix:
                mi = np.true_divide(flow[i+2], sumSubstanceFlowsPeriod+self.addedSubstanceFlows[i])
                allMi[flow[0], flow[1]] = mi
                #if self.timeIndices[i] == 2012 and stage == 2:
                    #print(allMi)

            #calculate HIIi
            for flow in materialFlowMatrix:
                concentration = float(concentrationMatrix[flow[0], flow[1]][i+2])
                mi = allMi[flow[0], flow[1]]
                if concentration != 0:
                    tmp = np.multiply(-mi,concentration)
                    HIIi = np.multiply(tmp,np.log2(concentration))
                else:
                    HIIi = 0
                allHIIi[flow[0],flow[1]] = HIIi
                #if self.timeIndices[i] == 2012 and stage == 2:
                    #print(concentration)
                    #print(allHIIi)
                    
            periodStageEntropy = np.true_divide(sum(list(allHIIi.values())), self.Hmax)
            stageResults[self.timeIndices[i]] = periodStageEntropy
            sumSubstanceFlows.append(sumSubstanceFlowsPeriod)
        #add the total substance flows of the previous stages to the substance flows of the current stage
        #for every period
        self.addedSubstanceFlows = [x + y for x, y in zip(self.addedSubstanceFlows, sumSubstanceFlows)]
        return stageResults

    def getCalcValues(self, materialFlows):
        concentrationMatrix = dict()
        substanceFlowMatrix = []
        materialFlowMatrix = []
        
        #generate the keys for every flow
        for flow in materialFlows:
            srcName = (flow[1] + "_" +
                        flow[2] + "_" +
                        flow[3]).lower()
            targName = (flow[4] + "_" +
                        flow[5] + "_" +
                        flow[6]).lower()
            #if the flow is not an inflow get the material flow and the concentration
            #if no concentration was in the input file generate a list with all zeros
            if flow[0].lower() == 'inflow' and srcName == '__':
                #get the inflows material flows and get their respective concentrations
                for infl in self.inflows:
                    materialFlowValue = self.convertUnits(
                        [srcName] + [targName] + [infl.getCurrentInflow(j) for j in range(len(self.timeIndices))])
                    concentrationValue = [srcName] + [targName] + self.concentrationValues.get((srcName, targName),
                                                                      [0] * (len(materialFlowValue) - 2))
            elif flow[0].lower() == 'concentration':
                continue
            else:
                materialFlowValue = self.convertUnits([srcName] + [targName] + self.flowValues[srcName, targName][0])
                concentrationValue = [srcName] + [targName] + self.concentrationValues.get((srcName, targName),
                                                                      [0] * (len(materialFlowValue) - 2))
                
                
            substanceFlowValue = []
            for i in range(len(materialFlowValue) - 2):
                #calculate substanceFlow by multiplying materialFlow and concentration
                substanceFlowValue.append(np.multiply(materialFlowValue[i + 2], float(concentrationValue[i+2])))
                
                #if i == len(materialFlowValue)-3:
                    #print('__________________')
                    #print(materialFlowValue[i+2])
                    #print(concentrationValue[i+2])
                    #print(substanceFlowValue)
                    #print('__________________')

            substanceFlowMatrix.append(substanceFlowValue)
            materialFlowMatrix.append(materialFlowValue)
            concentrationMatrix[srcName, targName] = concentrationValue
        return materialFlowMatrix, substanceFlowMatrix, concentrationMatrix

    def convertUnits(self, flowValue):
        #find the units of the source node and target node
        nodeUnit = flowValue[0].split('_')[2]
        targUnit = flowValue[1].split('_')[2]
        #if there is a conversion for the units defined in the source file
        #convert values and return the converted values
        if (nodeUnit, targUnit) in self.conversions:
            conversion = self.conversions[nodeUnit, targUnit]
            for i in range(len(conversion)):
                flowValue[i + 2] = np.multiply(conversion[i], flowValue[i + 2])
        return flowValue
        
class EntropyException(Exception):
    def __init__(self, error):
        self.error = error
        # pass