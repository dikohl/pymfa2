'''create a class, similar to exporter
It should get the needed values from the simulation and calculate the entropy for every marked flow in every year
THEN change the exporter so it also adds a row for the entropy'''

#conversion??
#delay??


import numpy as np

class EntropyCalc(object):
    #initiate EntropyCalc with the values of all the material flows, substance flows and concentrations
    def __init__(self, system, simulator):
        #self.Hmax = ld(1/earthcrust concentration)
        
        #get the mean of every flow in the simulation
        self.flowValues = {}
        for comp in simulator.flowCompartments:
          for key in list(comp.outflowRecord.keys()):
            self.flowValues[comp.name, key] = []
            self.flowValues[comp.name, key].append(np.mean(comp.outflowRecord[key], axis=0).tolist())
            
        self.metadataMatrix = system.metadataMatrix
        
    def computeSingleStage(self, materialFlows, concentrations, firstValue):
        
        #convert units so that all are the same
        #!!!!!!flowValue = self.convertUnits(conversions, flowValue, firstValue)!!!!!!

        substanceFlowValues = dict()
        for flow in MaterialFlows:
            nodeName = (flow[1] + "_" +
                        flow[2] + "_" +
                        flow[3]).lower()
            targName = (flow[4] + "_" +
                        flow[5] + "_" +
                        flow[6]).lower()
            flowValue = self.flowValues[nodeName, targName][0]
            concentrationValue = self.concentrationValues[nodeName, targName]
            substanceFlowValue = []
            for i in range(len(flowValue)):
                # find substanceFlow by materialFlow * concentration
                substanceFlowValue[i] = np.multiply(flowValue[i], concentrationValue[i])
            substanceFlowValues[nodeName, targName] =  substanceFlowValue

        allMi = dict()
        allHIIi = dict()
        for material, flow in materialFlows.items():
            mi = np.true_divide(flow, np.sum(list(substanceFlow.values())))
            allMi[material] = mi
            
        for material, mi in allMi.items():
            #concentration needs to be converted from 1% to 0.01
            c = concentrations[material]
            mi = allMi[material]
            tmp = np.multiply(-mi,c)
            HIIi = np.multiply(tmp,np.log2(c))
            allHIIi[material] = HIIi
        
        entropy = np.true_divide(sum(list(allHIIi.values())), self.Hmax)
        return entropy
    
    #sort the metadata according to it's stages
    def run(self):
        #get the conversion from one unit to another
        conversions = dict()
        for i in range(len(system.metadataMatrix)):
            if self.metadataMatrix[i][0].lower() == 'conversion' and flowValue[2] == flowValue[5]:
                nodeName = (self.metadataMatrix[i][1] + "_" +
                            self.metadataMatrix[i][2] + "_" +
                            self.metadataMatrix[i][3]).lower()
                targName = (self.metadataMatrix[i][4] + "_" +
                            self.metadataMatrix[i][5] + "_" +
                            self.metadataMatrix[i][6]).lower()
                conversion[self.flowValue[3]] = self.flowValues[nodeName, targName][0]
                self.metadataMatrix.remove(self.metadataMatrix[i])
        
        #order flows by stages
        stages = dict()
        concStages = dict()
        for metadata in metadataMatrix:
            flowStages = metadata[-2].split('|')

            #every other flow is added to the correct stage
            else:
                for fstage in flowStages:
                    if stages[fstage]:
                        stages[fstage].append(flowValue)
                    else:
                        stages[fstage] = [flowValue]
        #for every stage of stages calculate entropy
        results = dict()
        for key in stages.keys():
            stageResult = self.computeSingleStage(stages[key], concStages[key])
            results[key] = stageResult
        return results
                
    def convertUnits(self, conversions, flowValue, firstValue):
        if flowValue[3] in conversions.keys():
            conversion = conversions[flowValue[3]]
            for i in range(len(conversion)):
                flowValue[i+firstValue] = np.multiply(conversion[i],flowValue[i+firstValue])
        return flowValue
        
        