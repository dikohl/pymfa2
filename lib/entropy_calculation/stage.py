class Stage:
    def __init__(self, stage):
        self.stage = stage
        self.flows = []

    def append(self,flow):
        self.flows.append(flow)

    def getSubstanceFlowSum(self):
        sum = 0.0
        for flow in self.flows:
            sum += float(flow.substanceFlow)
        return sum

    def getMiSum(self):
        sum = 0.0
        for flow in self.flows:
            sum = sum + float(flow.Mi)
        return sum

    def getHIIiSum(self):
        sum = 0.0
        for flow in self.flows:
            sum = sum + float(flow.HIIi)
        return sum

    def updateStockValue(self, searchFlow, value):
        for flow in self.flows:
            if searchFlow == flow:
                flow.setFlowValue(value)
