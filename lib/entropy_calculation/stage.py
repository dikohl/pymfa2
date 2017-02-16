import numpy as np

class Stage:
    def __init__(self, stage):
        self.stage = stage
        self.flows = []

    def append(self,flow):
        self.flows.append(flow)

    def getSubstanceFlowSum(self):
        sum = np.float64(0.0)
        for flow in self.flows:
            sum = np.float64(np.add(np.float64(sum), np.float64(flow.substanceFlow)))
        return sum

    def getMiSum(self):
        sum = np.float64(0.0)
        for flow in self.flows:
            sum = np.float64(np.add(np.float64(sum), np.float64(flow.Mi)))
        return sum

    def getHIIiSum(self):
        sum = np.float64(0.0)
        for flow in self.flows:
            sum = np.float64(np.add(np.float64(sum), np.float64(flow.HIIi)))
        return sum

    def updateStockValue(self, searchFlow, value):
        for flow in self.flows:
            if searchFlow == flow:
                flow.setFlowValue(np.float64(value))
