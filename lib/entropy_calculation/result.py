class Result:
    def __init__(self):
        self.timeIndices = []
        self.entropy = []

    def __repr__(self):
        return self.entropy

    def __str__(self):
        return self.entropy

class PeriodResults:
    def __init__(self):
        self.stages = dict()

    def __repr__(self):
        out = []
        for key in self.stages.keys():
            out.append(["Stage " + key]+[self.stages[key]])
        return out