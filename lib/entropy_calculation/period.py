class Period():
    def __init__(self,year):
        self.year = year
        self.stages = dict()
        self.stocks = []

    def addFlow(self, flow):
        if flow.transferType.lower() == "delay":
            self.stocks.append(flow)
        for stage in flow.stages:
            self.stages.setdefault(stage, []).append(flow)

    def setStockValues(self):
        for stock in self.stocks:
            inflow = self.getNodeInflows(stock)
            outflow = self.getNodeOutflows(stock)
            self.updateStockValue(stock, inflow-outflow)

    def getNodeInflows(self,stockFlow):
        inflow = 0
        for key in self.stages.keys():
            for flow in self.stages[key]:
                if flow.destinationNode == stockFlow.sourceNode:
                    inflow = inflow+flow.materialFlow
        return inflow

    def getNodeOutflows(self,stockFlow):
        outflow = 0
        for key in self.stages.keys():
            for flow in self.stages[key]:
                if flow.sourceNode == stockFlow.destinationNode:
                    outflow = outflow+flow.materialFlow
        return outflow

    def updateStockValue(self,flow,value):
        flow.setFlowValue(value)

    def convertUnits(self, conversions, index):
        for key in self.stages.keys():
            for flow in self.stages[key]:
                for conv in conversions:
                    if flow.getSourceUnit() == conv.fromUnit and flow.getDestinationUnit() == conv.toUnit:
                        flow.convertUnits(conv[index])

    def getSubstanceFlowSum(self):
        return 0

    def __str__(self):
        return str(self.year) + ": " + str(self.stages)

    def __repr__(self):
        return str(self.year) + ": " + str(self.stages)