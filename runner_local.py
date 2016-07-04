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
"""



import sys
from os.path import splitext
from lib.importer import CSVImporter
from lib.exporter import CSVExporter
from lib.entropy import EntropyCalc

inFileName = sys.argv[1]
outFileName = sys.argv[2]

def usage():
  return ("usage: runner_local.py source.csv results.csv\n" +
          "source.csv: path to the source file of an analysis.\n" +
          "results.csv: path to where the results should be stored.\n")

if not inFileName or not outFileName:
  print("ERROR: This script requires two arguments")
  print(usage())
  sys.exit(1)

print("using input file: %s" % inFileName)
print("using output file: %s" % outFileName)

exporter = None
if splitext(outFileName)[1].lower() == ".csv":
  exporter = CSVExporter()
if not exporter:
  print("ERROR: The second argument should end in '.csv'.")
  print(usage())
  sys.exit(1)

importer = CSVImporter()

print("loading input file...")
system,concentration = importer.load(inFileName)
print("running analysis...")
simulator = system.run()
print("calculating entropy (if Hmax was specified)...")
entropyResult = EntropyCalc(system, simulator, concentration).run()
print("writing results...")
doPlot = 0
if '--plot' in sys.argv [1:]:
    doPlot = 1
exporter.export(outFileName, system, simulator, entropyResult, doPlot)

print("All done.")