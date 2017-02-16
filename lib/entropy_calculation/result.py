import numpy as np

class Result:
    def __init__(self):
        self.stageResults = dict()

    def append(self,stageResult):
        self.stageResults.setdefault(stageResult.stage, stageResult).append(stageResult)

    def __repr__(self):
        table = []
        for key in self.stageResults.keys():
            table.append(["Stage " + key] + self.stageResults[key])
        return table

class StageResult:
    def __init__(self,year,stage,entropyResult):
        self.stage = stage
        self.entropyResults = dict()
        self.entropyResults[year] = np.float64(entropyResult)

    def append(self, stageResult):
        for key in stageResult.entropyResults.keys():
            #print("stage: " + str(self.stage) + " res: " + str(key) +" : "+ str(stageResult.entropyResults[key]))
            self.entropyResults[key] = stageResult.entropyResults[key]

    def __repr__(self):
        return [str(np.float64(self.enropyResults[key])) for key in self.entropyResults.keys()]
