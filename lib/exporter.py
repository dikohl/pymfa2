#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created in February 2016

@author: RoBa
modified by Dimitri Kohler in March 2016

The exporter module exports the results of the calculations as a table to a
csv file and creates plots of the material flows and stocks.
"""

from io import BytesIO as StringIO
import os
import zipfile
import shutil
import csv
import numpy as np



class CSVExporter(object):
  def export(self,outFileName,system,simulator,entropyResult,doPlot):
    """Returns a list (rows) of lists (row contents) containing all data."""

    runs = system.runs
    periods = system.periods
    categories = simulator.getCategories()
    timeIndices = system.timeIndices
    if periods < len(timeIndices):
      timeIndices = timeIndices[:periods]

    # x stands for the number of rows per node
    # minus the number of percentile rows
    x = None
    if system.median:   # 2 rows (mean and median)
      x = 2
    else:               # 1 row (only mean)
      x = 1
    
    flowValues = {}
    stockValues = {}
    
    linkMeanRows = []
    linkMedianRows = []
    linkPercentileRows = []
    
    stockMeanRows = []
    stockMedianRows = []
    stockPercentileRows = []


    # prepare header rows:
    padding = ["","","","",""]
    startPadding = ["", "", "", "", "", "", "", "", ""]
    stockHeader = (["Node Type", "Node Name", "Material", "Unit"] +
                        padding + [""] + timeIndices)
    linkHeader = (["Transfer Type", "SourceNode", "SourceMaterial",
                        "SourceUnit", "DestinationNode", "DestinationMaterial",
                        "DestinationUnit", "Stages","Description", ""] + timeIndices)


    # log flow data from flow compartments
    for comp in simulator.flowCompartments:
      for key in list(comp.outflowRecord.keys()):
        flowValues[comp.name, key] = []
        flowValues[comp.name, key].append(np.mean(comp.outflowRecord[key],
                                                    axis=0).tolist())
        if system.median and runs != 1:
          flowValues[comp.name, key].append(np.median(comp.outflowRecord[key],
                                                      axis=0).tolist())
        if len(system.percentiles) != 0 and runs != 1:
          for i in range(len(system.percentiles)):
            flowValues[comp.name, key].append(np.percentile(
                                                    comp.outflowRecord[key],
                                                    system.percentiles[i],
                                                    axis=0).tolist())


    # log stock data from stocks and sinks
    for sink in simulator.sinks:
      stockValues[sink.name] = []
      stockValues[sink.name].append(np.mean(sink.inventory, axis=0).tolist())
      if system.median and runs != 1:
        stockValues[sink.name].append(np.median(sink.inventory,
                                                axis=0).tolist())
      if len(system.percentiles) != 0 and runs != 1:
        for i in range(len(system.percentiles)):
          stockValues[sink.name].append(np.percentile(sink.inventory,
                                                       system.percentiles[i],
                                                       axis=0).tolist())


    # creating data rows for links
    for i in range(len(system.metadataMatrix)):
      if system.metadataMatrix[i][0].lower() == "inflow" or system.metadataMatrix[i][0].lower() == "concentration":
        continue
      else:
        nodeName = (system.metadataMatrix[i][1] + "_" +
                    system.metadataMatrix[i][2] + "_" +
                    system.metadataMatrix[i][3]).lower()
        targName = (system.metadataMatrix[i][4] + "_" +
                    system.metadataMatrix[i][5] + "_" +
                    system.metadataMatrix[i][6]).lower()
        linkMeanRows.append(system.metadataMatrix[i] + ["mean:"] +
                              flowValues[nodeName, targName][0])
        if system.median and runs != 1:
          linkMedianRows.append(startPadding + ["median:"] +
                                flowValues[nodeName, targName][1])
        if len(system.percentiles) != 0 and runs != 1:
          for j in range(len(system.percentiles)):
            linkPercentileRows.append(startPadding +
                                    [str(system.percentiles[j])+"th perc.:"] +
                                    flowValues[nodeName, targName][j+x])


    # find and mark sinks as 'Sink' (used for the csv output)                             
    typeTracker = {}  # keeps track of the type 'sink' for sinks
    for i in range(len(system.metadataMatrix)):
      if system.metadataMatrix[i][1].lower() in list(typeTracker.keys()):
        typeTracker[system.metadataMatrix[i][1].lower()] = "Stock"
      typeTracker[system.metadataMatrix[i][4].lower()] = "Sink"


    # creating data rows for stocks
    takenCareOf = []
    for cat in categories:
      for i in range(len(system.metadataMatrix)):
        nodeName = (system.metadataMatrix[i][1] + "_" +
                      system.metadataMatrix[i][2] + "_" +
                      system.metadataMatrix[i][3]).lower()
        targName = (system.metadataMatrix[i][4] + "_" +
                      system.metadataMatrix[i][5] + "_" +
                      system.metadataMatrix[i][6]).lower()
        if system.metadataMatrix[i][1].lower() == cat and \
                              nodeName in list(stockValues.keys()):
          if nodeName in takenCareOf:
            pass
          else:
            takenCareOf.append(nodeName)
            typeName = "Stock"
            if typeTracker[system.metadataMatrix[i][1].lower()] == "Sink":
              typeName = "Sink"
            stockMeanRows.append([typeName] + system.metadataMatrix[i][1:4] +
                          padding + ["mean:"] + stockValues[nodeName][0])
            if system.median and runs != 1:
              stockMedianRows.append(startPadding + ["median:"] +
                                     stockValues[nodeName][1])
            if len(system.percentiles) != 0 and runs != 1:
              for j in range(len(system.percentiles)):
                stockPercentileRows.append(startPadding +
                                    [str(system.percentiles[j])+"th perc."] +
                                    stockValues[nodeName][j+x])
        if system.metadataMatrix[i][4].lower() == cat and \
                              targName in list(stockValues.keys()):
          if targName in takenCareOf:
            pass
          else:
            takenCareOf.append(targName)
            typeName = "Stock"
            if typeTracker[system.metadataMatrix[i][4].lower()] == "Sink":
              typeName = "Sink"
            stockMeanRows.append([typeName] + system.metadataMatrix[i][4:7] +
                          padding + ["mean:"] + stockValues[targName][0])
            if system.median and runs != 1:
              stockMedianRows.append(startPadding + ["median:"] +
                                     stockValues[targName][1])
            if len(system.percentiles) != 0 and runs != 1:
              for j in range(len(system.percentiles)):
                stockPercentileRows.append(startPadding +
                                    [str(system.percentiles[j])+"th perc."] +
                                    stockValues[targName][j+x])

                                      
    # create result table
    table = []
    table.append(["Runs:", runs])
    table.append(["Periods:", periods])
    table.append([])
    table.append(linkHeader)
    for i in range(len(linkMeanRows)):
      table.append(linkMeanRows[i])
      if system.median and runs != 1:
        table.append(linkMedianRows[i])
      if len(system.percentiles) != 0 and runs != 1:
        for j in range(len(system.percentiles)):
          table.append(linkPercentileRows[(i*len(system.percentiles))+j])
    table.append([])
    table.append(stockHeader)
    for i in range(len(stockMeanRows)):
      table.append(stockMeanRows[i])
      if system.median and runs != 1:
        table.append(stockMedianRows[i])
      if len(system.percentiles) != 0 and runs != 1:
        for j in range(len(system.percentiles)):
          table.append(stockPercentileRows[(i*len(system.percentiles))+j])

    if system.entropy:
        table = self.exportEntropy(table,timeIndices,entropyResult)

    if doPlot:
        import matplotlib.pyplot as plt
        root, file = os.path.split(outFileName)
        date, out = os.path.split(root)
        path = os.path.join(date,"plots")
        # save time span plots
        timeIDs = np.array(timeIndices)
        categories = simulator.getCategories()
    
        # fill system.timeSpanPlots with capitalized node names if it's empty
        if system.timeSpanPlots != None and len(system.timeSpanPlots) == 0:
          for node in categories:
            splittedNode = str.split(node, " ")
            capNode = (str.capitalize(split) for split in splittedNode)
            capNode = " ".join(capNode)
            system.timeSpanPlots.append(capNode)
        
        if system.timeSpanPlots != None and len(system.timeSpanPlots) != 0:

          # create directory for saving the plots
          if not os.path.exists(path):
            os.makedirs(path)
        
          # calculate number of total plots (used for printing the progress)
          lowerTimeSpanPlots = list(node.lower() for node in system.timeSpanPlots)
          plotCounter = 0
          for comp in simulator.compartments:
            if comp.categories[0] in lowerTimeSpanPlots:
              if comp.name in system.rates.keys():
                if system.rates[comp.name].type != "conversion":
                  plotCounter += 1
              elif comp.name in system.delays.keys():
                plotCounter += 3
              elif comp.name in system.sinks.keys():
                plotCounter += 2
              else:
                plotCounter += 1
              
          plotNumber = 0  # used for printing the progress
          lastIncrease = 0  # used for printing the progress
          signsToPrint = 50  # used for printing the progress
          if plotCounter == 1:
            print("\n               creating " + str(plotCounter) + " plot...")
          else:
            print("\n               creating " + str(plotCounter) + " plots...")
          print("0%                                              100%")

          #save plots for nodes in system.timeSpanPlots (except conversions)
          for comp in simulator.compartments:
            if comp.categories[0] in lowerTimeSpanPlots and \
                    system.nodes[comp.name] != "conversion":
                    
              # capitalize the node category
              splittedName = str.split(comp.categories[0], " ")
              splittedName = (str.capitalize(n) for n in splittedName)
              capitalizedName = " ".join(splittedName)
          
              # create plot for the node's inflows
              plotNumber += 1
              if signsToPrint != 0 and plotNumber-lastIncrease >= \
                 float(plotCounter)/signsToPrint:  # display progress
                progress = \
                int((plotNumber-lastIncrease)/(float(plotCounter)/signsToPrint))
                plotCounter -= 1
                signsToPrint -= progress
                lastIncrease += 1
                print("|" * progress, end="")
              xTicks = []
              for i in range(len(timeIDs)):
                if i % (int(len(timeIDs)/12)+1) == 0:
                  xTicks.append(str(timeIDs[i]))
                else:
                  xTicks.append("")
              plt.xticks(timeIDs, xTicks)
              plt.xlabel('years')
              material = ''
              unit = ''
              isDelay = False
              isSink = False
              if comp.name in system.rates.keys():
                material = system.rates[comp.name].material
                unit = system.rates[comp.name].unit
              elif comp.name in system.delays.keys():
                material = system.delays[comp.name].material
                unit = system.delays[comp.name].unit
                isDelay = True
              elif comp.name in system.sinks.keys():
                material = system.sinks[comp.name].material
                unit = system.sinks[comp.name].unit
                isSink = True
              else:
                print("could not generate plot for node '" +
                      capitalizedName + "': node name not found.")
                plt.close()
                continue
              plt.ylabel(material+' in '+unit)
              plt.title(capitalizedName+'\nInflows')
              for row in comp.inflowRecord:
                if runs == 1:
                  plt.plot(timeIDs, row, color='0.3', lw=1)
                else:
                  plt.plot(timeIDs, row, color='0.7', lw=0.1)
              if runs != 1:
                plt.plot(timeIDs, np.mean(comp.inflowRecord, axis=0), color='r',
                         lw=1, label = "mean")
                if system.median:
                  plt.plot(timeIDs, np.median(comp.inflowRecord, axis=0),
                           color='b', lw=1, label="median")
                if len(system.percentiles) != 0:
                  for i in range(len(system.percentiles)):
                    plt.plot(timeIDs, np.percentile(comp.inflowRecord,
                             system.percentiles[i], axis=0), color='g', lw=1,
                             label=str(system.percentiles[i])+"th perc.")
                plt.legend(loc=2, fontsize='x-small')
              plt.savefig(path + "/" + comp.name + " - inflows.png", dpi=300)
              plt.close()
            
              # create plot for the node's inventory
              if isDelay or isSink:
                plotNumber += 1
                if signsToPrint != 0 and plotNumber-lastIncrease >= \
                   float(plotCounter)/signsToPrint:  # display progress
                  progress = \
                  int((plotNumber-lastIncrease)/(float(plotCounter)/signsToPrint))
                  plotCounter -= 1
                  signsToPrint -= progress
                  lastIncrease += 1
                  print("|" * progress, end="")
                plt.xticks(timeIDs, xTicks)
                plt.xlabel('years')
                plt.ylabel(material+' in '+unit)
                plt.title(capitalizedName+'\nInventory')
                for row in comp.inventory:
                  if runs == 1:
                    plt.plot(timeIDs, row, color='0.3', lw=1)
                  else:
                    plt.plot(timeIDs, row, color='0.7', lw=0.1)
                if runs != 1:
                  plt.plot(timeIDs, np.mean(comp.inventory, axis=0), color='r',
                           lw=1, label = "mean")
                  if system.median:
                    plt.plot(timeIDs, np.median(comp.inventory, axis=0),
                             color='b', lw=1, label="median")
                  if len(system.percentiles) != 0:
                    for i in range(len(system.percentiles)):
                      plt.plot(timeIDs, np.percentile(comp.inventory,
                               system.percentiles[i], axis=0), color='g', lw=1,
                               label=str(system.percentiles[i])+"th perc.")
                  plt.legend(loc=2, fontsize='x-small')
                plt.savefig(path + "/" + comp.name + " - inventory.png", dpi=300)
                plt.close()
              
              # create plot for the node's outflows
              if isDelay:
                plotNumber += 1
                if signsToPrint != 0 and plotNumber-lastIncrease >= \
                   float(plotCounter)/signsToPrint:  # display progress
                  progress = \
                  int((plotNumber-lastIncrease)/(float(plotCounter)/signsToPrint))
                  plotCounter -= 1
                  signsToPrint -= progress
                  lastIncrease += 1
                  print("|" * progress, end="")
                plt.xticks(timeIDs, xTicks)
                plt.xlabel('years')
                plt.ylabel(material+' in '+unit)
                plt.title(capitalizedName+'\nOutflows')
                totalOutflows = np.zeros((runs, periods))
                for i in range(runs):
                  for targ in comp.outflowRecord.keys():
                    totalOutflows[i] += comp.outflowRecord[targ][i]
                if runs > 1:
                  for row in totalOutflows:
                    plt.plot(timeIDs, row, color='0.7', lw=0.1)
                  plt.plot(timeIDs, np.mean(totalOutflows, axis=0), color='r',
                           lw=1, label = "mean")
                  if system.median and runs != 1:
                    plt.plot(timeIDs, np.median(totalOutflows, axis=0),
                             color='b', lw=1, label="median")
                  if len(system.percentiles) != 0 and runs != 1:
                    for i in range(len(system.percentiles)):
                      plt.plot(timeIDs, np.percentile(totalOutflows,
                               system.percentiles[i], axis=0), color='g', lw=1,
                               label=str(system.percentiles[i])+"th perc.")
                  plt.legend(loc=2, fontsize='x-small')
                else:
                  plt.plot(timeIDs, totalOutflows[0], color='0.3', lw=1)
                plt.savefig(path + "/" + comp.name + " - outflows.png", dpi=300)
                plt.close()

            ziph = zipfile.ZipFile('plots.zip', 'w', zipfile.ZIP_DEFLATED)
            for root, dirs, files in os.walk(path):
              for file in files:
                ziph.write(os.path.join(root, file))
            shutil.rmtree(path)
            
          print("\n")
    

    with open(outFileName, 'w') as f:
        w = csv.writer(f, delimiter=';', lineterminator='\n',
                       quotechar='"', quoting=csv.QUOTE_MINIMAL)
        w.writerows(table)
    return

#adds the entropy results to the table that is later printed to the output file
  def exportEntropy(self, table, timeIndices, entropyResult):
    table.append(["Entropy"] + timeIndices)
    keys = entropyResult.stageResults.keys()
    for key in sorted(keys):
      values = [entropyResult.stageResults[key].entropyResults[year] for year in sorted(entropyResult.stageResults[key].entropyResults.keys())]
      table.append(["Stage " + key] + values)
    return table
    
    