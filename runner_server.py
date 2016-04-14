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



import sys
import os
from os.path import splitext
from lib.importer import CSVImporter, CSVParserException
from lib.exporter import CSVExporter
from lib.entropy import EntropyCalc

class Runner(object):
    def __init__(self, inputFile, outputFile):
        self.inFileName = inputFile
        self.outFileName = outputFile

    def run(self):
        exporter = CSVExporter()
        importer = CSVImporter()
        try:
            system = importer.load(self.inFileName)
            simulator = system.run()
            #entropy = EntropyCalc(system, simulator)
            #simulator??system?? = entropy.run
            exporter.export(self.outFileName, system, simulator)
        except CSVParserException as e:
            return e.error
        return ''
        