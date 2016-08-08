#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created in February 2016

@author: RoBa

The runner module runs the whole material flow analysis tool.

It takes two arguments:
1. the path to the csv source file
   (incl. file name and '.csv' ending)
2. the path to where the results csv file shall be written
   (incl. file name and '.csv' ending)
   
modified by dikohl
This runner is used serverside and was changed to be called after a new file was uploaded.
"""

import sys, argparse

from lib.entropy_calculation.entropy import Entropy, EntropyCalc
from lib.exporter import CSVExporter
from lib.importer import CSVImporter, CSVParserException


class Runner(object):
    def __init__(self, inputFile, outputFile):
        self.inFileName = inputFile
        self.outFileName = outputFile
        parser = argparse.ArgumentParser()
        parser.add_argument('--plot',action='store_true')
        parser.add_argument('--entropy',action='store_true')
        args = parser.parse_args()

        self.doPlot = 0
        self.showDetail = 0
        if args.plot:
            self.doPlot = 1
        if args.entropy:
            self.showDetail = 1

    def run(self):
        exporter = CSVExporter()
        importer = CSVImporter()
        try:
            system, concentration, conversion = importer.load(self.inFileName)
            simulator = system.run()
            entropyResult = EntropyCalc(Entropy(system, simulator, concentration, conversion)).computeEntropy(self.showDetail)
            exporter.export(self.outFileName, system, simulator, entropyResult, self.doPlot)
            #exporter.export(self.outFileName, system, simulator, self.doPlot)
        except CSVParserException as e:
            return e.error
        return ''
        