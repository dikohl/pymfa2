import numpy as np

from lib.entropy_calculation.flow import Flow

class Conversion(Flow):
    def __init__(self,transferType,srcName,srcUnit,destName,destUnit,stages,values,concentration):
        Flow.__init__(self,transferType,srcName,srcUnit,destName,destUnit,stages,values,concentration)

    def calculate(self, infl):
        if infl != 0:
            self.conversion = np.divide(np.float64(self.conversion), np.float64(infl))
