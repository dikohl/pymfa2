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
            system, concentration = importer.load(self.inFileName)
            simulator = system.run()
            entropyResult = EntropyCalc(system, simulator, concentration).run()
            #entropyResult = {1:{1995:23,1996:34,1997:45,1998:46,1999:56,2000:20,2001:21,2002:21,2003:21,2004:21,2005:21,2006:21,2007:21,2008:21,2009:21,2010:21,2011:21,2012:21},2:{1995:23,1996:34,1997:45,1998:46,1999:56,2000:20,2001:21,2002:21,2003:21,2004:21,2005:21,2006:21,2007:21,2008:21,2009:21,2010:21,2011:21,2012:21},3:{1995:23,1996:34,1997:45,1998:46,1999:56,2000:20,2001:21,2002:21,2003:21,2004:21,2005:21,2006:21,2007:21,2008:21,2009:21,2010:21,2011:21,2012:21},4:{1995:23,1996:34,1997:45,1998:46,1999:56,2000:20,2001:21,2002:21,2003:21,2004:21,2005:21,2006:21,2007:21,2008:21,2009:21,2010:21,2011:21,2012:21},5:{1995:23,1996:34,1997:45,1998:46,1999:56,2000:20,2001:21,2002:21,2003:21,2004:21,2005:21,2006:21,2007:21,2008:21,2009:21,2010:21,2011:21,2012:21},6:{1995:23,1996:34,1997:45,1998:46,1999:56,2000:20,2001:21,2002:21,2003:21,2004:21,2005:21,2006:21,2007:21,2008:21,2009:21,2010:21,2011:21,2012:21}}
            exporter.export(self.outFileName, system, simulator, entropyResult)
        except CSVParserException as e:
            return e.error
        return ''
        