'''create a class, similar to exporter
It should get the needed values from the simulation and calculate the entropy for every marked flow in every year
THEN change the exporter so it also adds a row for the entropy'''
    #StagesMaterialFlows = dict()
    #StagesSubstanceFlows = dict()
    #StagesConcentrations = dict()
    #dicts within dicts!!!!


import numpy as np

class EntropyCalc(object):
    #initiate EntropyCalc with the values of all the material and substance flows and concentrations
    def __init__(self, system, simulator):
        #self.Hmax = ld(1/earthcrust concentration)
        
        #get the mean of every flow in the simulation
        flowValues = {}
        linkedFlowValues = []
        for comp in simulator.flowCompartments:
          for key in list(comp.outflowRecord.keys()):
            flowValues[comp.name, key] = []
            flowValues[comp.name, key].append(np.mean(comp.outflowRecord[key], axis=0).tolist())
        
        print(flowValues)
        
        for i in range(len(system.metadataMatrix)):
            if system.metadataMatrix[i][0].lower() == "inflow":
                print(system.metadataMatrix[i])
                #linkedFlowValues.append(system.metadataMatrix[])
            else:
                nodeName = (system.metadataMatrix[i][1] + "_" +
                            system.metadataMatrix[i][2] + "_" +
                            system.metadataMatrix[i][3]).lower()
                targName = (system.metadataMatrix[i][4] + "_" +
                            system.metadataMatrix[i][5] + "_" +
                            system.metadataMatrix[i][6]).lower()
                flowValues[nodeName, targName][0]
        firstValue = len(system.metadataMatrix[0])+1
        
        self.computeStages(linkedFlowValues, firstValue)
        
        #dict with all materialFlows
        #dict with all substanceFlows
        #dict with all concentrations
        
    def calculateStage(self, materialFlows, substanceFlows, concentrations):
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
    
    #sort the values according to their TransferType
    def computeStages(self, linkedFV, firstValue):
        #get the conversion from one unit to another
        conversions = dict()
        for flowValue in linkedFV:
            if flowValue[0].lower() == 'conversion' and flowValue[2] == flowValue[5]:
                conversions[flowValue[3]] = flowValue[firstValue:]
                linkedFV.remove(flowValue)
        
        #get flows from single nodes
        stages = dict()
        for flowValue in linkedFV:
            print(flowValue)
            flowValue = self.convertUnits(conversions, flowValue, firstValue)
            print(flowValue)
            if (flowValue[0],flowValue[1]) in stages.keys():
                flows = stages[(flowValue[0],flowValue[1])]
                flows[flowValue[4]] = flowValue[firstValue:]
                stages[(flowValue[0],flowValue[1])] = flows
            else:
                stages[(flowValue[0],flowValue[1])] = {flowValue[4]:flowValue[firstValue:]}
                
    def convertUnits(self, conversions, flowValue, firstValue):
        if flowValue[3] in conversions.keys():
            conversion = conversions[flowValue[3]]
            for i in range(len(conversion)):
                flowValue[i+firstValue] = np.multiply(conversion[i],flowValue[i+firstValue])
        return flowValue
        
        