'''create a class, similar to exporter
It should get the needed values from the simulation and calculate the entropy for every marked flow in every year
THEN change the exporter so it also adds a row for the entropy'''

#conversion??
#delay??

from lib.dpmfa_simulator.components import ExternalListInflow as exinf
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

        
    def computeSingleStage(self, materialFlows, stageNum):

        stageResults = dict()
        concentrationMatrix = dict()
        substanceFlowMatrix = []
        materialFlowMatrix = []

        for flow in materialFlows:
            nodeName = (flow[1] + "_" +
                        flow[2] + "_" +
                        flow[3]).lower()
            targName = (flow[4] + "_" +
                        flow[5] + "_" +
                        flow[6]).lower()

            if '' not in flow[1:3]:
                materialFlowValue = self.convertUnits([nodeName] + [targName] + self.flowValues[nodeName, targName][0])
                concentrationValue = self.concentrationValues.get((nodeName, targName),[nodeName] + [targName] +
                                                                  [0]*(len(materialFlowValue)-2))

            else:
                for infl in self.inflows:
                    materialFlowValue = self.convertUnits([nodeName] + [targName] + [infl.getCurrentInflow(j) for j in range(len(self.timeIndices))])
                    concentrationValue = self.concentrationValues.get((nodeName, targName), [nodeName] + [targName] +
                                                                      [0] * (len(materialFlowValue)-2))
            substanceFlowValue = []

            for i in range(len(materialFlowValue)-2):
                # find substanceFlow by multiplying materialFlow and concentration
                substanceFlowValue.append(np.multiply(materialFlowValue[i+2], float(concentrationValue[i])))
            substanceFlowMatrix.append(substanceFlowValue)
            materialFlowMatrix.append(materialFlowValue)
            concentrationMatrix[nodeName, targName] = concentrationValue

        sumSubstanceFlows = []
        for i in range(len(substanceFlowMatrix[0])):
            allMi = dict()
            allHIIi = dict()
            substanceFlowPeriod = [sub[i] for sub in substanceFlowMatrix]
            sumSubstanceFlowsPeriod = np.sum(substanceFlowPeriod)
            for flow in materialFlowMatrix:
                mi = np.true_divide(flow[i+2], sumSubstanceFlowsPeriod+self.addedSubstanceFlows[i])
                allMi[flow[0], flow[1]] = mi
            for flow in materialFlowMatrix:
                #throw error if concentration is not known
                if (flow[0], flow[1]) not in concentrationMatrix:
                    raise EntropyException("Concentration for ... is missing")
                concentration = float(concentrationMatrix[flow[0], flow[1]][i])
                mi = allMi[flow[0], flow[1]]
                tmp = np.multiply(-mi,concentration)
                HIIi = np.multiply(tmp, np.log2(concentration))
                allHIIi[flow[0],flow[1]] = HIIi
            periodStageEntropy = np.true_divide(sum(list(allHIIi.values())), self.Hmax)
            stageResults[self.timeIndices[i]] = periodStageEntropy
            sumSubstanceFlows.append(sumSubstanceFlowsPeriod)
        self.addedSubstanceFlows = [x + y for x, y in zip(self.addedSubstanceFlows, sumSubstanceFlows)]
        return stageResults
    
    #sort the metadata according to it's stages
    def run(self):
        results = dict()
        if not self.shouldCalculate:
            return results
        #get the conversion from one unit to another
        for i in range(len(self.metadataMatrix)):
            if self.metadataMatrix[i][0].lower() == 'conversion' and self.metadataMatrix[i][2] == self.metadataMatrix[i][5]:
                if '' not in self.metadataMatrix[i][1:3]:
                    nodeName = (self.metadataMatrix[i][1] + "_" +
                                self.metadataMatrix[i][2] + "_" +
                                self.metadataMatrix[i][3]).lower()
                    targName = (self.metadataMatrix[i][4] + "_" +
                                self.metadataMatrix[i][5] + "_" +
                                self.metadataMatrix[i][6]).lower()
                    self.conversions[self.metadataMatrix[i][3], self.metadataMatrix[i][6]] = self.flowValues[nodeName, targName][0]
                    self.metadataMatrix.remove(self.metadataMatrix[i])
        
        #order flows by stages
        stages = dict()
        for metadata in self.metadataMatrix:
            metadataStages = [x for x in metadata[-2].split('|') if x]
            #every other flow is added to the correct stage
            for mStage in metadataStages:
                if mStage in stages.keys():
                    stages[int(mStage)].append(metadata)
                else:
                    stages[int(mStage)] = [metadata]

        #for every stage of stages calculate entropy
        for key in range(len(stages)):
            stageResult = self.computeSingleStage(stages[int(key)+1], int(key)+1)
            results[int(key)+1] = stageResult
        print(results)
        return results
                
    def convertUnits(self,flowValue):
        nodeUnit = flowValue[0].split('_')[2]
        targUnit = flowValue[1].split('_')[2]
        if (nodeUnit, targUnit) in self.conversions:
            conversion = self.conversions[nodeUnit, targUnit]
            for i in range(len(conversion)):
                flowValue[i+2] = np.multiply(conversion[i],flowValue[i+2])
        return flowValue
        
class EntropyException(Exception):
    def __init__(self, error):
        self.error = error
        # pass