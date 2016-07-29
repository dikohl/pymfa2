from lib.entropy_calculation.node import Node
import numpy as np


class Flow:

    def __init__(self, type, srcName, srcUnit, destName, destUnit, stages, value, concentration):
        self.stages = stages
        self.transferType = type
        self.sourceNode = Node(srcUnit,srcName)
        self.destinationNode = Node(destUnit,destName)
        self.concentration = concentration
        if type.lower() == "fraction":
            self.substanceFlow = value
            if self.concentration == 0:
                self.materialFlow = 0
            else:
                self.materialFlow = 100*(float(self.substanceFlow)/float(self.concentration))
        else:
            self.materialFlow = value
            print(str(self.materialFlow)+" "+str(self.concentration))
            self.substanceFlow = float(self.materialFlow)*float(self.concentration)

    def setFlowValue(self, value):
        self.materialFlow = value
        self.substanceFlow = self.materialFlow*self.concentration

    def getSourceUnit(self):
        return self.sourceNode.unit

    def getDestinationUnit(self):
        return self.destinationNode.unit

    def convertUnits(self, conversion):
        self.materialFlow = self.materialFlow*conversion
        self.substanceFlow = self.substanceFlow*conversion

    def __str__(self):
        return self.sourceNode+" --> "+self.destinationNode+": "+str(self.materialFlow)

    def __repr__(self):
        return str(self.sourceNode)+" --> "+str(self.destinationNode)+": "+str(self.materialFlow)