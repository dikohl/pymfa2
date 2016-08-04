from lib.entropy_calculation.node import Node


class Flow:

    def __init__(self, type, srcName, srcUnit, destName, destUnit, stages, value, concentration):
        self.stages = stages
        self.transferType = type
        self.sourceNode = Node(srcUnit,srcName)
        self.destinationNode = Node(destUnit,destName)
        self.concentration = concentration
        self.Mi = 0.0
        self.HIIi = 0.0

        if float(self.concentration) == 0:
            self.materialFlow = 0.0
            self.substanceFlow = 0.0
        else:
            if "x" in self.stages:
                self.substanceFlow = value
                self.materialFlow = float(self.substanceFlow)/float(self.concentration)
                #print(str(self.sourceNode)+" --> "+str(self.destinationNode)+": "+str(self.materialFlow))
            else:
                self.materialFlow = value
                self.substanceFlow = float(self.materialFlow)*float(self.concentration)

    def setFlowValue(self, value):
        self.materialFlow = value
        self.substanceFlow = float(self.materialFlow)*float(self.concentration)

    def getSourceUnit(self):
        return self.sourceNode.unit

    def getDestinationUnit(self):
        return self.destinationNode.unit

    def convertUnits(self, conversion):
        self.materialFlow = self.materialFlow*conversion
        self.substanceFlow = self.substanceFlow*conversion

    def __eq__(self, other):
        return (self.sourceNode.name == other.sourceNode.name and
                self.destinationNode.name == other.destinationNode.name)

    def __str__(self):
        return str(self.sourceNode)+" --> "+str(self.destinationNode)+" (Mat: "+str(self.materialFlow)+" Sub: "+str(self.substanceFlow)

    def __repr__(self):
        return str(self.sourceNode)+" --> "+str(self.destinationNode)+" (Mat: "+str(self.materialFlow)+" Sub: "+str(self.substanceFlow)