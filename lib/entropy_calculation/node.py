class Node:
    def __init__(self, unit, name):
        self.unit = unit
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name