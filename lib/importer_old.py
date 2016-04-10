#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created in February 2016

@author: RoBa

The importer module imports, checks, and saves the data from a csv file.
"""


import csv
from .linker import System, InflowData, RateData, DelayData, SinkData



class CSVImporter(object):
  def colString(self, n):
    n+=1
    s = ""
    while n != 0:
      s += chr((n - 1) % 26 + 65)
      n //= 27
    return s[::-1]


  def load(self, fileName):
    """read a csv file and build the flow model"""

    system = System()

    # open the file
    with open(fileName, 'r') as f:
      try:
        dialect = csv.Sniffer().sniff(f.read(), ',;: \t')
      except (UnicodeDecodeError, csv.Error):
        raise CSVParserException(
              "Invalid CSV file: The uploaded file could not be " +
              "recognized as a CSV file.")
      f.seek(0)
      reader = csv.reader(f, dialect)
      
      haveRuns = False
      havePeriods = False
      haveMedian = False
      havePercentiles = False
      haveTimeSpanPlots = False
      haveTimeIndex = False
      haveInflow = False
      rowNumber = 1
      
      supportedTransferTypes = \
          ['inflow', 'delay', 'rate', 'conversion', 'fraction']
      supportedProbabilityDistributions = ['uniform','normal', 'triangular']
      supportedReleaseFunctions = ['fix', 'list', 'rand', 'weibull']
      
      
      # go through every line of the input file and make sanity checks
      for row in reader:
          
        # ignore empty lines and lines where the first column is empty
        if not row or len(row[0]) == 0:
          rowNumber += 1
          continue

        # check and log input for 'runs'
        if not haveRuns:
          if row[0].lower() == "runs:":
            if len(row[1]) == 0:
              raise CSVParserException(
                    ("row %d, col %s: is empty.\n" +
                     "Please enter an integer > 0.")
                     % (rowNumber, self.colString(1)))
            else:
              try:
                system.runs = int(row[1])
                if system.runs < 1:
                  raise CSVParserException(
                        ("row %d, col %s:\nThe input for the number of runs " +
                         "is smaller than 1.\nPlease enter an integer > 0.")
                         % (rowNumber, self.colString(1)))
              except ValueError:
                raise CSVParserException(
                      ("row %d, col %s:\nCould not convert string '%s' to " +
                       "an integer.\nUse an integer > 0 representing the " +
                       "number of runs for the model to calculate.")
                       % (rowNumber, self.colString(1), row[1]))
          else:
            raise CSVParserException(
                  ("row %d:\nFirst non-comment row not containing information " + 
                   "about the number of runs.\nPlease enter 'runs:' into " +
                   "column %s and an integer > 0 representing the number of " +
                   "runs relevant for the calculations into column %s.")
                   % (rowNumber, self.colString(0), self.colString(1)))
                   
          rowNumber += 1
          haveRuns = True
          continue

        # check and log input for 'periods'
        if not havePeriods:
          if row[0].lower() == "periods:":
            if len(row[1].replace(" ", "")) == 0:
              system.periods = 0
            else:
              try:
                system.periods = int(row[1])
                if system.periods < 0 or system.periods == 1:
                  raise CSVParserException(
                        ("row %d, col %s:\nThe value '1' or negative values " +
                         "for the numbers of periods are not allowed.\nEither " +
                         "use '0' or leave the cell empty if the number of " +
                         "periods shall be the number of time indices,\nor " +
                         "use an integer > 1 representing the number of " +
                         "periods relevant for the calculations.")
                         % (rowNumber, self.colString(1)))
              except ValueError:
                raise CSVParserException(
                      ("row %d, col %s:\nCould not convert string '%s' to " +
                       "an integer.\nEither use '0' or leave the cell empty " +
                       "if the number of periods shall be the number of " +
                       "time indices,\nor use an integer > 1 representing " +
                       "the number of periods relevant for the calculations.")
                       % (rowNumber, self.colString(1), row[1]))
          else:
            raise CSVParserException(
                  ("row %d:\nSecond non-comment row not containing " +
                   "information about the number of periods.\nPlease enter " +
                   "'periods:' into column %s and an integer representing " +
                   "the number of periods relevant for the calculations into " +
                   "column %s. If the number of periods shall be equal to " +
                   "the number of time indices, insert '0' or leave the cell " +
                   "empty.")
                   % (rowNumber, self.colString(0), self.colString(1)))
          
          rowNumber += 1
          havePeriods = True
          continue

        # check and log input for 'median'
        if not haveMedian:
          if row[0].lower() == "median:":
            if len(row[1]) == 0:
              pass
            elif row[1].lower().replace(" ", "") in ["0", "n", "no", "none"]:
              pass
            elif row[1].lower().replace(" ", "") in ["1", "y", "yes"]:
              system.median = True
            else:
             raise CSVParserException(
                   ("row %d, col %s:\nWrong input for 'median:', got '%s'. " +
                    "\nHere, you can choose, if you want to display the " +
                    "median values in the result file.\nFor the inputs " +
                    "'0', 'n', 'no', 'none' or an empty cell no medians "
                    "will be displayed. For the inputs '1', 'y' or 'yes' " +
                    "the median values will be displayed.")
                    % (rowNumber, self.colString(1), row[1]))
          else:
            raise CSVParserException(
                  ("row %d: Third non-comment row not containing " +
                   "information about the median values.\nPlease enter " +
                   "'median:' into column %s. With an input in column %s " +
                   "you can choose, if you want to display the " +
                   "median values in the result file.\nFor the inputs " +
                   "'0', 'n', 'no', 'none' or an empty cell no medians "
                   "will be displayed. For the inputs '1', 'y' or 'yes' " +
                   "the median values will be displayed.")
                   % (rowNumber, self.colString(0), self.colString(1)))

          rowNumber += 1
          haveMedian = True
          continue
       
        # check and log input for 'percentiles'
        if not havePercentiles:
          if row[0].lower() == "percentiles:":
            if len(row[1]) == 0:
              pass
            else:
              try:
                system.percentiles = list(map(int, str.split(row[1], "|")))
              except ValueError:
                raise CSVParserException(
                      ("row %d, col %s:\nCould not convert string '%s' to " +
                       "integers.\nPlease, use integers between 0 and 100 " +
                       "separated by '|'.\nThe integers represent the " +
                       "percentiles to be calculated.\nExample: '20|80' " +
                       "represents the percentiles at 20%% and 80%%.\nIf you " +
                       "leave the cell empty, no percentiles will be " +
                       "calculated.")% (rowNumber, self.colString(1), row[1]))
              else:
                properInput = True
                for i in range(len(system.percentiles)):
                  if system.percentiles[i] >= 0 and system.percentiles[i] <= 100:
                    pass
                  else:
                    properInput = False
                    break
                if properInput == False:
                  raise CSVParserException(
                          ("row %d, col %s:\nThe input '%s' is not as " +
                           "expected.\nPlease, use integers between 0 and 100 " +
                           "separated by '|'.\nThe integers represent the " +
                           "percentiles to be calculated.\nExample: '20|80' " +
                           "represents the percentiles at 20%% and 80%%.\nIf " +
                           "you leave the cell empty, no percentiles will be " +
                           "calculated.")
                           % (rowNumber, self.colString(1), row[1]))
          else:
            raise CSVParserException(
                  ("row %d:\nFourth non-comment row not containing " + 
                   "information about the percentiles.\nPlease enter " +
                   "'percentiles:' into column %s and integers between 0 and " +
                   "100 separated by '|' into column %s.\nThe integers " +
                   "represent the percentiles to be calculated.\nExample: " +
                   "'20|80' represents the percentiles at 20%% and 80%%.\nIf " +
                   "you leave the cell empty, no percentiles will be " +
                   "calculated.")
                   % (rowNumber, self.colString(0), self.colString(1)))
                   
          rowNumber += 1
          havePercentiles = True
          continue
      
        # check and log input for 'plots'     
        if not haveTimeSpanPlots:
          if row[0].lower().replace(" ", "") == "plots:":
            if len(row[1]) == 0 or row[1].replace(" ", "") == "0":
              system.timeSpanPlots = None
            elif row[1].replace(" ", "") == "1":
              pass
            else:
              try:
                system.timeSpanPlots = list(map(str, str.split(row[1], "|")))
                system.timeSpanPlots = \
                list(p.strip() for p in system.timeSpanPlots)
              except ValueError:
                raise CSVParserException(
                      ("row %d, col %s: Could not convert string '%s' to " +
                       "string. Something with the input is wrong.\nEnter " +
                       "the nodes for which you want a plot over the whole " +
                       "time span here. Use '|' to separate the names of the " +
                       "nodes. You can also enter '0' or leave the cell " +
                       "empty if no plots shall be printed or '1' if all the " +
                       "time span plots shall be printed.\ninput examples:" +
                       " 'Decommissioning|Recycling|Dumping', '0', '1'")
                       % (rowNumber, self.colString(1), row[1]))
          else:
            raise CSVParserException(
                  ("row %d: Fifth non-comment row not containing " +
                   "information about the plots.\nPlease enter 'plots:' " +
                   "into column %s and the nodes for which you want a plot " +
                   "over the whole time span into column %s. Use '|' to " +
                   "separate the names of the nodes. You can also enter '0' " +
                   "or leave the cell empty if no plots shall be printed or " +
                   "'1' if all the time span plots shall be printed.\ninput " +
                   "examples: 'Decommissioning|Recycling|Dumping', '0', '1'")
                   % (rowNumber, self.colString(0), self.colString(1)))
                   
          rowNumber += 1
          haveTimeSpanPlots = True
          continue


        # check if enough columns in the file
        if not system.timeIndices and len(row) < 10:
          raise CSVParserException(
                ("row %d:\nSixth non-comment row not containing enough " + 
                 "columns,\nExpecting 8 metadata columns and at least 2 data " +
                 "columns, got %d.") % (rowNumber, len(row)))
        if system.timeIndices and len(row) != 8 + len(system.timeIndices):
          raise CSVParserException(
                ("row %d:\nNon-comment row containing wrong number of " + 
                 "columns,\nExpecting 8 metadata columns and %d data columns," +
                 "got %d.") % (rowNumber, len(system.timeIndices), len(row)))

        valuesOffset = 8           # index of the first column that has values
        metadata = row[0:7]         # the columns containing type, nodes etc.
        description = row[7]        # the 'free text' description column
        values = row[valuesOffset:] # contains the values of the current row
                     
        if metadata[0].lower().replace(" ", "") == "transfertype":
          if haveTimeIndex:
            raise CSVParserException(
                  
                  "row %d:\nDuplicate header row" % (rowNumber))
          previous = None
          for n, timeIndex in enumerate(values):
            # sanity check if the value is an integer
            try:
              int(timeIndex)
            except ValueError:
              raise CSVParserException(
                    ("row %d, col %s:\nExpected integer time index, got '%s'") %
                    (rowNumber, self.colString(valuesOffset+n), timeIndex))
            # sanity check if the values are in sequence, separated by 1
            if previous != None and (previous + 1) != int(timeIndex):
              raise CSVParserException(
                    ("row %d, col %s:\nExpected next time index %d, got '%s'") %
                    (rowNumber, self.colString(valuesOffset+n), previous + 1, 
                     timeIndex))
            else:
              previous = int(timeIndex)

          # store the time indices in the system
          system.timeIndices = [int(y) for y in values]
          
          # adjust number of periods to number of time indices
          # (if requested or necessary)
          if system.periods == 0 or system.periods > len(system.timeIndices):
            system.periods = len(system.timeIndices)
                        
          haveTimeIndex = True

        # the other rows contain data (but we ignore empty rows)
        else:
          if not haveTimeIndex:
            raise CSVParserException(
                ("row %d:\nExpected header row with time index or empty " +
                  "row or a row with an empty first column, got row %s")
                  % (rowNumber, row))
                  
          # extract the metadata
          (transferType, src, srcMaterial, srcUnit,
           dst, dstMaterial, dstUnit) = [x.lower() for x in metadata]
           
          # assign column numbers to the column headers
          (colTransferType, colSrc, colSrcMaterial, colSrcUnit, colDst,
           colDstMaterial, colDstUnit) = [0, 1, 2, 3, 4, 5, 6]
           
          if not dstMaterial:
            dstMaterial = srcMaterial
          if not dstUnit:
            dstUnit = srcUnit
            
          if metadata[5] == "":
            metadata[5] = metadata[2]
            
          if metadata[6] == "":
            metadata[6] = metadata[3]
            
          system.metadataMatrix.append(metadata + [description])


          tempArg = []
          splittedValues = []
            
          # sanity check if supported transfer type is used
          if transferType not in supportedTransferTypes:
            raise CSVParserException(
                  ("row %d, col %s:\nUnexpected transfer type, got '%s' " +
                   "Please use the following transfer types:\n%s")
                   % (rowNumber, self.colString(colTransferType), 
                      transferType, str(supportedTransferTypes)\
                      .replace("[", "").replace("]", "").replace(",", "\n")))
                      
          # sanity check if first transfer type in source file is an inflow
          if not haveInflow:
            if transferType == "inflow":
              haveInflow = True
            else:
              raise CSVParserException(
                    ("row %d, col %s:\nFirst transfer type is not an inflow. " +
                     "Please use 'inflow' as the first transfer type to " +
                     "generate an inflow to a target node.")
                     % (rowNumber, self.colString(colTransferType)))
        
          # sanity check if there is a name for the source compartment and
          # if it is not a number
          if transferType != "inflow":  # no src for inflow types
            if src.replace(" ", "") == "":
              raise CSVParserException(
                    ("row %d, col %s:\nNo name for the source node.") 
                     % (rowNumber, self.colString(colSrc)))
            else:
              try:
                float(src.replace(" ", "").replace(",", ""))
              except:
                pass
              else:
                raise CSVParserException(
                      ("row %d, col %s:\nNumber as a compartment name. A " +
                       "number is not allowed as compartment name, got '%s'.") 
                       % (rowNumber, self.colString(colSrc), src))
                       
          # sanity check if there is a name for the target compartment and
          # if it is not a number
          if dst.replace(" ", "") == "":
            raise CSVParserException(
                  ("row %d, col %s:\nNo name for the target node.") 
                   % (rowNumber, self.colString(colDst)))
          else:
            try:
              float(dst.replace(" ", "").replace(",", ""))
            except:
              pass
            else:
              raise CSVParserException(
                    ("row %d, col %s:\nNumber as a compartment name. A number " +
                     "is not allowed as compartment name, got '%s'.") 
                     % (rowNumber, self.colString(colDst), dst))
                   
          # sanity check if source unit is different from target unit 
          # if transfer type is 'conversion'      
          if transferType == "conversion":
            if srcUnit == dstUnit:
              raise CSVParserException(
                    ("row %d, col %s and %s:\nSame source unit and target " +
                     "unit. When using a conversion as transfer type, the " +
                     "source unit has to be different from the target unit.") 
                     % (rowNumber, self.colString(colSrcUnit), 
                        self.colString(colDstUnit)))
                        
          # sanity check if source and target unit are the same if
          # transfer type is neither 'conversion' nor 'inflow'
          if transferType != "conversion" and \
              transferType != "inflow":
            if srcUnit != dstUnit:
              raise CSVParserException(
                    ("row %d, col %s and %s:\nSource unit is different from " +
                     "target unit. When not using a conversion as a transfer " +
                     "type, the source unit and the target unit have to be " +
                     "the same.") 
                     % (rowNumber, self.colString(colSrcUnit), 
                        self.colString(colDstUnit)))
                                                                         
          # sanity check if we have the correct number of non-empty values
          if (not all(values) or (len(values) != len(system.timeIndices))):
            raise CSVParserException("row %d, col %s to %s:\nExpected %d values, got %s" %
                  (rowNumber, self.colString(valuesOffset), 
                   self.colString(valuesOffset+len(system.timeIndices)),
                   len(system.timeIndices), sum([bool(v) for v in values])))

          # sanity checks for values when using type 'inflow'
          if transferType == "inflow":
            for c, v in enumerate(values):
              if v.replace(" ", "") == "":
                raise CSVParserException(
                      ("row %d, col %s:\nMissing input. Please choose an " +
                       "inflow value type (fix, stoch or rand) and enter " +
                       "the respective arguments separated by '|'.\n" +
                       "Examples: 'fix|30000'\n" +
                       "          'stoch|normal|30000, 1500'\n" +
                       "          'rand|28000, 29000, 30000, 31000, 32000'")
                       % (rowNumber, self.colString(valuesOffset+c)))
              else:
                try:
                  tempArg = list(str.split(v.replace(" ", ""), "|"))
                except:
                  raise CSVParserException(
                        ("row %d, col %s:\nNot able to parse the input, " +
                         "got '%s'. Please choose an inflow value type " +
                         "(fix, stoch or rand) and enter the respective " +
                         "arguments separated by '|'.\n" +
                         "Examples: 'fix|30000'\n" +
                         "          'stoch|normal|30000, 1500'\n" +
                         "          'rand|28000, 29000, 30000, 31000, 32000'")
                         % (rowNumber, self.colString(valuesOffset+c), v))
              if tempArg[0] == "fix":
                if len(tempArg) != 2:
                  raise CSVParserException(
                        ("row %d, col %s:\nWrong number of arguments for " +
                         "inflow value type 'fix', got input '%s'. Please, " +
                         "enter the inflow value type and the respective " +
                         "value as the two arguments separated by '|'.\n" +
                         "-> example input: 'fix|30000'")
                         % (rowNumber, self.colString(valuesOffset+c), v))
                try:
                  tempArg[1] = float(tempArg[1])
                except ValueError:
                  raise CSVParserException(
                        ("row %d, col %s:\nCould not parse second argument " +
                         "to float, got '%s'. Please choose one float value " +
                         "as second argument.\nExamples: '30000', '30000.0', " +
                         "'30000.45'")
                         % (rowNumber, self.colString(valuesOffset+c), 
                            tempArg[1]))
              elif tempArg[0] == "stoch":
                if len(tempArg) != 3:
                  raise CSVParserException(
                        ("row %d, col %s:\nWrong number of arguments for " +
                         "inflow value type 'stoch', got input '%s'. " +
                         "Please, enter the inflow value type, the function " +
                         "and the respective parameters as the three " +
                         "arguments separated by '|'.\n" +
                         "-> example input: 'stoch|normal|30000, 1500.5'")
                         % (rowNumber, self.colString(valuesOffset+c), v))
                if tempArg[1] not in supportedProbabilityDistributions:
                  raise CSVParserException(
                        ("row %d, col %s:\nSecond argument is not a supported " +
                         "probability distribution function, got '%s'. " +
                         "Please, use one of the following functions:\n%s") %
                         (rowNumber, self.colString(valuesOffset+c),tempArg[1],
                          str(supportedProbabilityDistributions).replace(
                          "[", "").replace("]", "").replace(" ", "").replace(
                          ",", "\n")))
                try:
                  tempArg[2] = \
                  list(float(p) for p in str.split(tempArg[2], ","))
                except ValueError:
                  raise CSVParserException(
                        ("row %d, col %s:\nCould not parse the function " +
                         "parameters into float, got '%s'. Please choose " +
                         "float values as parameters for the chosen function.")
                         % (rowNumber, self.colString(valuesOffset+c), 
                            tempArg[2]))
                if tempArg[1] == "normal" and len(tempArg[2]) != 2:
                  raise CSVParserException(
                        ("row %d, col %s:\nWrong number of function " +
                         "parameters for function 'normal', got input '%s'. " +
                         "Please choose exactly two floats as parameters, " +
                         "got %d parameters.\n" +
                         "-> example input: 'stoch|normal|3000, 120'")
                         % (rowNumber, self.colString(valuesOffset+c),
                            tempArg[2], len(tempArg[2])))
                if tempArg[1] == "triangular" and len(tempArg[2]) != 3:
                  raise CSVParserException(
                        ("row %d, col %s:\nWrong number of function " +
                         "parameters for function 'triangular', got input " +
                         "'%s'. Please choose exactly three floats as " +
                         "parameters, got %d parameters.\n-> example input: " +
                         "'stoch|triangular|2880, 3000, 3120'")
                         % (rowNumber, self.colString(valuesOffset+c),
                            tempArg[2], len(tempArg[2])))
                if tempArg[1] == "uniform" and len(tempArg[2]) != 2:
                  raise CSVParserException(
                        ("row %d, col %s:\nWrong number of function " +
                         "parameters for function 'uniform', got input '%s'. " +
                         "Please choose exactly two floats as parameters, " +
                         "got %d parameters.\n" +
                         "-> example input: 'stoch|uniform|2880, 3120'")
                         % (rowNumber, self.colString(valuesOffset+c),
                            tempArg[2], len(tempArg[2])))
              elif tempArg[0] == "rand":
                if len(tempArg) > 2:
                  raise CSVParserException(
                        ("row %d, col %s:\nWrong number of arguments for " +
                         "inflow value type 'rand', got input '%s'. Please, " +
                         "enter the inflow value type and the respective " +
                         "values as the two arguments, separated by '|'.\n" +
                         "-> example input: 'rand||28000, 29000, 30000, " +
                         "31000, 32000'")
                         % (rowNumber, self.colString(valuesOffset+c), v))
                try:
                  tempArg[1] = \
                  list(float(p) for p in str.split(tempArg[1], ","))
                except ValueError:
                  raise CSVParserException(
                        ("row %d, col %s:\nCould not parse the values to " +
                         "floats, got '%s'. Please choose floats as list " +
                         "items.\nExample: '30000, 31000.5, 29750.7'")
                         % (rowNumber, self.colString(valuesOffset+c), 
                            tempArg[1]))
              else:
                raise CSVParserException(
                      ("row %d, col %s:\nWrong inflow value type input, got " +
                       "'%s'. Please choose an inflow value type (fix, " +
                       "stoch or rand) and enter the respective arguments " +
                       "separated by '|'.\n" +
                       "Examples: 'fix|30000'\n" +
                       "          'stoch|normal|30000, 2000.5'\n" +
                       "          'rand|28000, 29000, 30000, 31000, 32000'")
                       % (rowNumber, self.colString(valuesOffset+c), v))
                       
              splittedValues.append(tempArg)
                       
          # sanity checks for the values when using 'rate', 'conversion' or
          #'fraction' as transfer type
          if transferType in supportedTransferTypes and \
              transferType != 'inflow' and transferType != 'delay':
            for c, v in enumerate(values):
              if v.replace(" ", "") == "":
                raise CSVParserException(
                      ("row %d, col %s:\nMissing input. Please choose a " +
                       "transfer value type (fix, stoch or rand) and " +
                       "enter the respective arguments separated by '|'.\n" +
                       "Examples: 'fix|0.8|1'\n" +
                       "          'stoch|normal|0.5, 0.15|1'\n" +
                       "          'rand|0.65, 0.7, 0.71, 0.75, 0.8|1'")
                       % (rowNumber, self.colString(valuesOffset+c)))
              else:
                try:
                  tempArg = list(str.split(v.replace(" ", ""), "|"))
                except:
                  raise CSVParserException(
                        ("row %d, col %s:\nNot able to parse the input, " +
                         "got '%s'. Please choose a transfer value type " +
                         "(fix, stoch or rand) and enter the respective " +
                         "arguments separated by '|'.\n" +
                         "Examples: 'fix|0.8|1'\n" +
                         "          'stoch|normal|0.5, 0.15|1'\n" +
                         "          'rand|0.65, 0.7, 0.71, 0.75, 0.8|1'") %
                         (rowNumber, self.colString(valuesOffset+c), v))
              if tempArg[0] == "fix":
                if len(tempArg) != 3:
                  raise CSVParserException(
                        ("row %d, col %s:\nWrong input for 'fix' " +
                         "transfer value type, got '%s'. Please enter the " +
                         "following three arguments separated by '|':\n" +
                         "1. transfer value type,\n2. value,\n3. priority\n" +
                         "-> example input: 'fix|0.8|1'")
                         % (rowNumber, self.colString(valuesOffset+c), v))
                try:
                  tempArg[1] = [float(tempArg[1])]
                except ValueError:
                  raise CSVParserException(
                        ("row %d, col %s:\nCould not parse second argument " +
                         "to float, got '%s'. Please choose a float value " +
                         "as the second argument.\nExample: '0.8'")
                         % (rowNumber, self.colString(valuesOffset+c), 
                            tempArg[1]))
                try:
                  tempArg[2] = int(tempArg[2])
                except ValueError:
                  raise CSVParserException(
                        ("row %d, col %s:\nCould not parse third argument " +
                         "to integer, got '%s'. Please choose an integer as " +
                         "the third argument.")
                         % (rowNumber, self.colString(valuesOffset+c), 
                            tempArg[2]))
              elif tempArg[0] == "stoch":
                if len(tempArg) != 4:
                  raise CSVParserException(
                        ("row %d, col %s:\nWrong input for 'stoch' transfer " +
                         "value type, got '%s'. Please enter the following " +
                         "four arguments separated by '|':\n" +
                         "1. transfer value type,\n2. function,\n3. function " +
                         "parameters,\n4. priority\n" +
                         "-> example input: 'stoch|normal|0.5, 0.15|1'")
                         % (rowNumber, self.colString(valuesOffset+c), v))
                if tempArg[1] not in supportedProbabilityDistributions:
                  raise CSVParserException(
                        ("row %d, col %s:\nSecond argument is not a supported " +
                         "probability distribution function, got '%s'. " +
                         "Please, use one of the following functions:\n%s") %
                         (rowNumber, self.colString(valuesOffset+c), tempArg[1],
                          str(supportedProbabilityDistributions).replace(
                          "[", "").replace("]", "").replace(" ", "").replace(
                          ",", "\n")))
                try:
                  tempArg[2] = \
                  list(float(p) for p in str.split(tempArg[2], ","))
                except ValueError:
                  raise CSVParserException(
                        ("row %d, col %s:\nCould not parse the function " +
                         "parameters to float, got '%s'. Please choose " +
                         "float values as parameters for the chosen function.")
                         % (rowNumber, self.colString(valuesOffset+c), 
                            tempArg[2]))
                try:
                  tempArg[3] = int(tempArg[3])
                except ValueError:
                  raise CSVParserException(
                        ("row %d, col %s:\nCould not parse fourth argument " +
                         "to integer, got '%s'. Please choose an integer as " +
                         "the fourth argument.")
                         % (rowNumber, self.colString(valuesOffset+c), 
                            tempArg[3]))
              elif tempArg[0] == "rand":
                if len(tempArg) != 3:
                  raise CSVParserException(
                        ("row %d, col %s:\nWrong input for 'rand' " +
                         "transfer value type, got '%s'. Please enter the " +
                         "following three arguments separated by '|':\n" +
                         "1. transfer value type,\n2. values,\n3. priority\n" +
                         "-> example input: 'rand|0.65, 0.7, 0.71, 0.75, " +
                         "0.8|1'")
                         % (rowNumber, self.colString(valuesOffset+c), v))
                try:
                  tempArg[1] = \
                  list(float(p) for p in str.split(tempArg[1], ","))
                except ValueError:
                  raise CSVParserException(
                        ("row %d, col %s:\nCould not parse the list to " +
                         "floats, got '%s'. Please choose floats as list " +
                         "items.\nExample: '0.7, 0.69, 0.71, 0.74'")
                         % (rowNumber, self.colString(valuesOffset+c), 
                            tempArg[1]))
                try:
                  tempArg[2] = int(tempArg[2])
                except ValueError:
                  raise CSVParserException(
                        ("row %d, col %s:\nCould not parse third argument " +
                         "to integer, got '%s'. Please choose an integer as " +
                         "the third argument.")
                         % (rowNumber, self.colString(valuesOffset+c), 
                            tempArg[2]))
              else:
                raise CSVParserException(
                      ("row %d, col %s:\nWrong transfer value type input, " +
                       "got '%s'. Please choose a transfer value type " +
                       "(fix, stoch or rand) and enter the respective " +
                       "arguments separated by '|'.\n" +
                       "Examples: 'fix|0.8|1'\n" +
                       "          'stoch|normal|0.5, 0.15|1'\n" +
                       "          'rand|0.65, 0.7, 0.71, 0.75, 0.8|1'")
                       % (rowNumber, self.colString(valuesOffset+c), v))
                       
              splittedValues.append(tempArg)

          # sanity checks for the values when using 'delay' as transfer type
          if transferType == 'delay':
            for c, v in enumerate(values):
              if v.replace(" ", "") == "":
                raise CSVParserException(
                      ("row %d, col %s:\nMissing input. Please choose a " +
                       "transfer value type (fix, stoch or rand) and " +
                       "enter the respective arguments separated by '|'.\n" +
                       "Please add a release function for the delayed " +
                       "releases and the respective parameters and the delay " +
                       "as well.\n"
                       "Examples: 'fix|0.8|1|list|0.5, 0.3, 0.2|0'\n       " +
                       "   'stoch|normal|0.5, 0.15|1|weibull|1, 3, 1|0'\n  " +
                       "        'rand|0.65, 0.7, 0.71, 0.75|1|weibull|1, 3|0'")
                       % (rowNumber, self.colString(valuesOffset+c)))
              else:
                try:
                  tempArg = list(str.split(v.replace(" ", ""), "|"))
                except:
                  raise CSVParserException(
                        ("row %d, col %s:\nNot able to parse the input, " +
                         "got '%s'. Please choose a transfer value type " +
                         "(fix, stoch or rand) and enter the respective " +
                         "arguments separated by '|'.\nPlease add a release " +
                         "function for the delayed releases and the " +
                         "respective parameters and the delay as well.\n" +
                         "Examples: 'fix|0.8|1|list|0.5, 0.3, 0.2|0'\n        " +
                         "  'stoch|normal|0.5, 0.15|1|weibull|1, 3, 1|0'\n    " +
                         "      'rand|0.65, 0.7, 0.71, 0.75|1|weibull|1, 3|0'")
                         % (rowNumber, self.colString(valuesOffset+c), v))
              if tempArg[0] == "fix":
                if len(tempArg) != 6:
                  raise CSVParserException(
                        ("row %d, col %s:\nWrong input for 'fix' " +
                         "transfer value type, got '%s'. Please enter the " +
                         "following three arguments separated by '|'.\n" +
                         "Please add a release function for the delayed " +
                         "releases and the respective parameters as well.\n" +
                         "1. transfer value type,\n2. value,\n3. priority,\n" +
                         "4. release function,\n5. parameters for release " +
                         "function,\n6. delay\n" +
                         "-> example input: 'fix|0.8|1|list|0.5, 0.3, 0.2|0'")
                         % (rowNumber, self.colString(valuesOffset+c), v))
                try:
                  tempArg[1] = [float(tempArg[1])]
                except ValueError:
                  raise CSVParserException(
                        ("row %d, col %s:\nCould not parse second argument " +
                         "to float, got '%s'. Please choose a float value " +
                         "as the second argument.\nExample: '0.8'")
                         % (rowNumber, self.colString(valuesOffset+c), 
                            tempArg[1]))
                try:
                  tempArg[2] = int(tempArg[2])
                except ValueError:
                  raise CSVParserException(
                        ("row %d, col %s:\nCould not parse third argument " +
                         "to integer, got '%s'. Please choose an integer as " +
                         "the third argument.")
                         % (rowNumber, self.colString(valuesOffset+c), 
                            tempArg[2]))
                if tempArg[3] not in supportedReleaseFunctions:
                  raise CSVParserException(
                        ("row %d, col %s:\nFourth argument is not a " +
                         "supported release function, got '%s'. Please " +
                         "choose a supported release function as the " +
                         "fourth argument.")
                         % (rowNumber, self.colString(valuesOffset+c), 
                            tempArg[3]))
                try:
                  tempArg[4] = \
                  list(float(p) for p in str.split(tempArg[4], ","))
                except ValueError:
                  raise CSVParserException(
                        ("row %d, col %s:\nCould not parse the values to " +
                         "floats, got '%s'. Please choose floats as " +
                         "fifth argument.")
                         % (rowNumber, self.colString(valuesOffset+c), 
                            tempArg[4]))
                try:
                  tempArg[5] = int(tempArg[5])
                except ValueError:
                  raise CSVParserException(
                        ("row %d, col %s:\nCould not parse sixth argument " +
                         "to integer, got '%s'. Please choose an integer as " +
                         "the sixth argument.")
                         % (rowNumber, self.colString(valuesOffset+c), 
                            tempArg[5]))
              elif tempArg[0] == "stoch":
                if len(tempArg) != 7:
                  raise CSVParserException(
                        ("row %d, col %s:\nWrong input for 'stoch' transfer " +
                         "value type, got '%s'. Please enter the following " +
                         "four arguments separated by '|'.\nPlease add a " +
                         "release function for the delayed releases and the " +
                         "respective parameters as well.\n" +
                         "1. transfer value type,\n2. function,\n3. function " +
                         "parameters,\n4. priority,\n5. release function,\n" +
                         "6. parameters for release function,\n7. delay\n" +
                         "-> example input: 'stoch|normal|0.5, 0.15|1|list|" +
                         "0.5, 0.3, 0.2|0'")
                         % (rowNumber, self.colString(valuesOffset+c), v))
                if tempArg[1] not in supportedProbabilityDistributions:
                  raise CSVParserException(
                        ("row %d, col %s:\nSecond argument is not a supported " +
                         "probability distribution function, got '%s'. " +
                         "Please, use one of the following functions:\n%s") %
                         (rowNumber, self.colString(valuesOffset+c), tempArg[1],
                          str(supportedProbabilityDistributions).replace(
                          "[", "").replace("]", "").replace(" ", "").replace(
                          ",", "\n")))
                try:
                  tempArg[2] = \
                  list(float(p) for p in str.split(tempArg[2], ","))
                except ValueError:
                  raise CSVParserException(
                        ("row %d, col %s:\nCould not parse the function " +
                         "parameters to float, got '%s'. Please choose " +
                         "float values as parameters for the chosen function.")
                         % (rowNumber, self.colString(valuesOffset+c), 
                            tempArg[2]))
                try:
                  tempArg[3] = int(tempArg[3])
                except ValueError:
                  raise CSVParserException(
                        ("row %d, col %s:\nCould not parse fourth argument " +
                         "to integer, got '%s'. Please choose an integer as " +
                         "the fourth argument.")
                         % (rowNumber, self.colString(valuesOffset+c), 
                            tempArg[3]))
                if tempArg[4] not in supportedReleaseFunctions:
                  raise CSVParserException(
                        ("row %d, col %s:\nFifth argument is not a " +
                         "supported release function, got '%s'. Please " +
                         "choose a supported release function as the " +
                         "fifth argument.")
                         % (rowNumber, self.colString(valuesOffset+c), 
                            tempArg[4]))
                try:
                  tempArg[5] = \
                  list(float(p) for p in str.split(tempArg[5], ","))
                except ValueError:
                  raise CSVParserException(
                        ("row %d, col %s:\nCould not parse the values to " +
                         "floats, got '%s'. Please choose floats as " +
                         "sixth argument.")
                         % (rowNumber, self.colString(valuesOffset+c), 
                            tempArg[5]))
                try:
                  tempArg[6] = int(tempArg[6])
                except ValueError:
                  raise CSVParserException(
                        ("row %d, col %s:\nCould not parse seventh argument " +
                         "to integer, got '%s'. Please choose an integer as " +
                         "the seventh argument.")
                         % (rowNumber, self.colString(valuesOffset+c), 
                            tempArg[6]))
              elif tempArg[0] == "rand":
                if len(tempArg) != 6:
                  raise CSVParserException(
                        ("row %d, col %s:\nWrong input for 'rand' " +
                         "transfer value type, got '%s'. Please enter the " +
                         "following three arguments separated by '|'.\n" +
                         "Please add a release function for the delayed " +
                         "releases and the respective parameters as well.\n" +
                         "1. transfer value type,\n2. values,\n3. priority,\n" +
                         "4. release function,\n5. parameters for release " +
                         "function,\n6. delay\n-> example input: " +
                         "'rand|0.7, 0.71, 0.75|1|list|0.5, 0.3, 0.2|0'")
                         % (rowNumber, self.colString(valuesOffset+c), v))
                try:
                  tempArg[1] = \
                  list(float(p) for p in str.split(tempArg[1], ","))
                except ValueError:
                  raise CSVParserException(
                        ("row %d, col %s:\nCould not parse the list to " +
                         "floats, got '%s'. Please choose floats as list " +
                         "items.\nExample: '0.7, 0.69, 0.71, 0.74'")
                         % (rowNumber, self.colString(valuesOffset+c), 
                            tempArg[1]))
                try:
                  tempArg[2] = int(tempArg[2])
                except ValueError:
                  raise CSVParserException(
                        ("row %d, col %s:\nCould not parse third argument " +
                         "to integer, got '%s'. Please choose an integer as " +
                         "the third argument.")
                         % (rowNumber, self.colString(valuesOffset+c), 
                            tempArg[2]))
                if tempArg[3] not in supportedReleaseFunctions:
                    raise CSVParserException(
                          ("row %d, col %s:\nFourth argument is not a " +
                           "supported release function, got '%s'. Please " +
                           "choose a supported release function as the " +
                           "fourth argument.")
                           % (rowNumber, self.colString(valuesOffset+c), 
                              tempArg[3]))
                try:
                  tempArg[4] = \
                  list(float(p) for p in str.split(tempArg[4], ","))
                except ValueError:
                  raise CSVParserException(
                        ("row %d, col %s:\nCould not parse the values to " +
                         "floats, got '%s'. Please choose floats as " +
                         "fifth argument.")
                         % (rowNumber, self.colString(valuesOffset+c), 
                            tempArg[4]))
                try:
                  tempArg[5] = int(tempArg[5])
                except ValueError:
                  raise CSVParserException(
                        ("row %d, col %s:\nCould not parse sixth argument " +
                         "to integer, got '%s'. Please choose an integer as " +
                         "the sixth argument.")
                         % (rowNumber, self.colString(valuesOffset+c), 
                            tempArg[5]))
              else:
                raise CSVParserException(
                      ("row %d, col %s:\nWrong transfer value type input, " +
                       "got '%s'. Please choose a transfer value type " +
                       "(fix, stoch or rand) and enter the respective " +
                       "arguments separated by '|'. Please add a release " +
                       "function for the delayed releases and the respective " +
                       "parameters and the delay as well.\n" +
                       "Examples: 'fix|0.8|1|list|0.5, 0.3, 0.2|0'\n       " +
                       "   'stoch|normal|0.5, 0.15|1|weibull|1, 1, 3|0'\n  " +
                       "        'rand|0.65, 0.7, 0.71, 0.75|1|weibull|1, 3|0'")
                       % (rowNumber, self.colString(valuesOffset+c), v))
                       
              splittedValues.append(tempArg)

          nodeName = src + '_' + srcMaterial + '_' + srcUnit
          targetName = dst + '_' + dstMaterial + '_' + dstUnit
          
          # creating target node if it doesn't exist yet
          # (as we don't know the target node's outgoing links yet, we create
          #  the node as 'delay'and will change it later, if necessary.)
          if targetName not in system.nodes:
            system.nodes[targetName] = "delay"
            system.delays[targetName] = DelayData(dst, dstMaterial, dstUnit)
            
          # creating source node if it doesn't exist yet or
          # extending/changing it if it already exists
          if transferType == "inflow":
            nodeName = "inflow " + str(len(system.inflows)+1)
            system.nodes[nodeName] = "inflow"
            system.inflows[nodeName] = InflowData(nodeName, dst, dstMaterial,
                                                  dstUnit, splittedValues,
                                                  description)
          elif transferType == "delay":
            if nodeName not in system.nodes:
              system.nodes[nodeName] = "delay"
              system.delays[nodeName] = DelayData(src, srcMaterial, srcUnit)
              system.delays[nodeName].descriptions[targetName] = description
              system.delays[nodeName].transfers[targetName] = []
              system.delays[nodeName].releases[targetName] = []
              for i in range(len(splittedValues)):
                system.delays[nodeName].transfers[targetName].append(
                                                        splittedValues[i][:-3])
                system.delays[nodeName].releases[targetName].append(
                                                        splittedValues[i][-3:])
            else:
              if system.nodes[nodeName] == "delay":
                if (targetName in system.delays[nodeName].descriptions or
                    targetName in system.delays[nodeName].transfers):
                  raise CSVParserException(
                        ("row %d:\nOnly one link between a source node and " +
                         "a target node allowed. The following link already " +
                         "exists:\n%s -> %s")
                         % (rowNumber, src, dst))
                else:
                  system.delays[nodeName].descriptions[targetName] = \
                  description
                  system.delays[nodeName].transfers[targetName] = []
                  system.delays[nodeName].releases[targetName] = []
                for i in range(len(splittedValues)):
                  system.delays[nodeName].transfers[targetName].append(
                                                      splittedValues[i][:-3])
                  system.delays[nodeName].releases[targetName].append(
                                                      splittedValues[i][-3:])
              else:                
                raise CSVParserException(
                      ("row %d:\nNo 'rate' or 'delay' link allowed for nodes " +
                       "which are already source node of a 'conversion' or " +
                       "'fraction' link.") % (rowNumber))
          elif transferType == "rate":
            if nodeName not in system.nodes:
              # create a 'delay' node (src node could still have 'delay' links)
              system.nodes[nodeName] = "delay"
              system.delays[nodeName] = DelayData(src, srcMaterial, srcUnit)
              system.delays[nodeName].descriptions[targetName] = description
              system.delays[nodeName].transfers[targetName] = splittedValues
            else:
              if system.nodes[nodeName] == "delay":
                if (targetName in system.delays[nodeName].descriptions or
                    targetName in system.delays[nodeName].transfers):
                  raise CSVParserException(
                        ("row %d:\nOnly one link between a source node and " +
                         "a target node allowed. The following link already " +
                         "exists:\n%s -> %s") % (rowNumber, src, dst))
                else:
                  system.delays[nodeName].descriptions[targetName] = \
                  description
                  system.delays[nodeName].transfers[targetName] = \
                  splittedValues
              else:
                raise CSVParserException(
                      ("row %d:\nNo 'rate' or 'delay' link allowed for nodes " +
                       "which are already source node of a 'conversion' or " +
                       "'fraction' link.\n source node: %s")
                       % (rowNumber, src))
          elif transferType == "conversion":
            if nodeName not in system.nodes:
              system.nodes[nodeName] = "conversion"
              system.rates[nodeName] = RateData(src, srcMaterial, srcUnit,
                                                                "conversion")
              system.rates[nodeName].descriptions[targetName] = description
              system.rates[nodeName].transfers[targetName] = splittedValues
            else:
              if system.nodes[nodeName] == "delay":
                if (system.delays[nodeName].transfers or
                    system.delays[nodeName].releases or
                    system.delays[nodeName].descriptions):
                  raise CSVParserException(
                        ("row %d:\nSource node of a 'conversion' link " +
                         "already exists as a source node of a different " +
                         "link.\nsource node: %s") % (rowNumber, src))
                else:
                  system.nodes[nodeName] = "conversion"
                  system.delays[nodeName] = None
                  del system.delays[nodeName]
                  system.rates[nodeName] = RateData(src, srcMaterial, srcUnit,
                                                                  "conversion")
                  system.rates[nodeName].descriptions[targetName] = description
                  system.rates[nodeName].transfers[targetName] = splittedValues
              else:
                raise CSVParserException(
                      ("row %d:\nSource node of a 'conversion' link already " +
                       "exists as a source node of a different link.\n" +
                       "source node: %s") % (rowNumber, src))
          elif transferType == "fraction":
            if nodeName not in system.nodes:
              system.nodes[nodeName] = "fraction"
              system.rates[nodeName] = RateData(src, srcMaterial, srcUnit,
                                                                    "fraction")
              system.rates[nodeName].descriptions[targetName] = description
              system.rates[nodeName].transfers[targetName] = splittedValues
            elif system.nodes[nodeName] == "delay":
              if (system.delays[nodeName].transfers or
                  system.delays[nodeName].releases or
                  system.delays[nodeName].descriptions):
                raise CSVParserException(
                      ("row %d:\nSource node of a 'fraction' link " +
                       "already exists as a source node of a different " +
                       "link.\nsource node: %s") % (rowNumber, src))
              else:
                system.nodes[nodeName] = "fraction"
                system.delays[nodeName] = None
                del system.delays[nodeName]
                system.rates[nodeName] = RateData(src, srcMaterial, srcUnit,
                                                                    "fraction")
                system.rates[nodeName].descriptions[targetName] = description
                system.rates[nodeName].transfers[targetName] = splittedValues
            elif system.nodes[nodeName] == "fraction":
              if (targetName in system.rates[nodeName].descriptions or
                  targetName in system.rates[nodeName].transfers):
                raise CSVParserException(
                      ("row %d:\nOnly one link between a source node and a " +
                       "target node allowed. The following link already " +
                       "exists:\n%s -> %s") % (rowNumber, src, dst))
              else:
                system.rates[nodeName].descriptions[targetName] = description
                system.rates[nodeName].transfers[targetName] = splittedValues
            else:
              raise CSVParserException(
                    ("row %d:\nSource node of a 'fraction' link " +
                     "already exists as a source node of a different " +
                     "link.\nsource node: %s") % (rowNumber, src))
          else:
            raise CSVParserException(
                  ("row %d:\nUnexpected transfer type, got '%s'.")
                   % (rowNumber, transferType))

        if metadata[5] == "":
          metadata[5] = metadata[2]
        if metadata[6] == "":
          metadata[6] = metadata[3]
        rowNumber += 1
        
      # - changing 'delay' nodes to 'rate' and 'sink' nodes if they have no
      #   delayed releases or neither delayed releases nor transfers.
      # - adding release strategies to the delay nodes which haven't 
      #   a release strategy for all transfers (because these are not delayed)
      for node in list(system.nodes.keys()):
        if (system.nodes[node] == "delay" and
            (not system.delays[node].releases) and
            (not system.delays[node].transfers)):
          system.nodes[node] = "sink"
          tempNode = system.delays[node]
          system.sinks[node] = \
          SinkData(tempNode.category, tempNode.material, tempNode.unit)
          system.delays[node] = None
          del system.delays[node]
        elif (system.nodes[node] == "delay" and
              (not system.delays[node].releases)):
          system.nodes[node] = "rate"
          tempNode = system.delays[node]
          system.rates[node] = \
          RateData(tempNode.category, tempNode.material, tempNode.unit,
                          "rate", tempNode.transfers, tempNode.descriptions)
          system.delays[node] = None
          del system.delays[node]
        elif system.nodes[node] == "delay":
          for target in list(system.delays[node].transfers.keys()):
            if (target not in system.delays[node].releases):
              tempLength = len(system.delays[node].transfers[target])
              system.delays[node].releases[target] = []
              for i in range(tempLength):
                system.delays[node].releases[target].append(['fix', [1.0], 0])
        else:
          pass

      return system

class CSVParserException(Exception):
    def __init__(self, error):
        self.error = error
  #pass


