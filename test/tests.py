import unittest
import sys
from lib.exporter import CSVExporter


class TestExporterMethod(unittest.TestCase):
    def setUp(self):
        entropyResult = {1: {1995: 23, 1996: 34, 1997: 45, 1998: 46, 1999: 56},
                         2: {1995: 23, 1996: 34, 1997: 45, 1998: 46, 1999: 56},
                         3: {1995: 23, 1996: 34, 1997: 45, 1998: 46, 1999: 56},
                         4: {1995: 23, 1996: 34, 1997: 45, 1998: 46, 1999: 56},
                         5: {1995: 23, 1996: 34, 1997: 45, 1998: 46, 1999: 56},
                         6: {1995: 23, 1996: 34, 1997: 45, 1998: 46, 1999: 56}}

        timeIndices = [1995, 1996, 1997, 1998, 1999]
        self.result = [['Entropy'],
                  ['Period', 1995], ['Stage 1', 23], ['Stage 2', 23], ['Stage 3', 23], ['Stage 4', 23], ['Stage 5', 23],
                       ['Stage 6', 23],
                  ['Period', 1996], ['Stage 1', 34], ['Stage 2', 34], ['Stage 3', 34], ['Stage 4', 34], ['Stage 5', 34],
                       ['Stage 6', 34],
                  ['Period', 1997], ['Stage 1', 45], ['Stage 2', 45], ['Stage 3', 45], ['Stage 4', 45], ['Stage 5', 45],
                       ['Stage 6', 45],
                  ['Period', 1998], ['Stage 1', 46], ['Stage 2', 46], ['Stage 3', 46], ['Stage 4', 46], ['Stage 5', 46],
                       ['Stage 6', 46],
                  ['Period', 1999], ['Stage 1', 56], ['Stage 2', 56], ['Stage 3', 56], ['Stage 4', 56], ['Stage 5', 56],
                       ['Stage 6', 56],
                  ]
        self.table = []
        exporter = CSVExporter()
        self.table = exporter.exportEntropy(self.table, timeIndices, entropyResult)

    def test_fillTable(self):
        self.assertEqual(self.table,self.result)