#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created in February 2016

@author: RoBa

The importer module imports, checks, and saves the data from a csv file.

modified by kodi in February 2016
"""

import csv
from .linker import System, InflowData, RateData, DelayData, SinkData
from lib.entropy_calculation.conversion import Conversion


class CSVImporter(object):
    def __init__(self):
        self.system = System()

        self.haveRuns = False
        self.havePeriods = False
        self.haveMedian = False
        self.havePercentiles = False
        self.haveTimeSpanPlots = False
        self.haveTimeIndex = False
        self.haveInflow = False
        self.haveEntropy = False

        self.rowNumber = 1

        self.valuesOffset = 9  # index of the first column that has values

        self.supportedTransferTypes = \
            ['inflow', 'delay', 'rate', 'conversion', 'fraction', 'concentration']
        self.supportedProbabilityDistributions = ['uniform', 'normal', 'triangular']
        self.supportedReleaseFunctions = ['fix', 'list', 'rand', 'weibull']

        self.concentrationEntropy = dict()

    def load(self, fileName):
        # read a csv file and build the flow model

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

            # go through every line of the input file and make sanity checks and get data
            for row in reader:

                # ignore empty lines and lines where the first column is empty
                if not row or len(row[0]) == 0:
                    self.rowNumber += 1
                    continue
                # get header data with these checks
                if self.checkForRuns(row):
                    continue
                if self.checkForPeriods(row):
                    continue
                if self.checkForMedian(row):
                    continue
                if self.checkForPercentiles(row):
                    continue
                if self.checkAndLogPlotData(row):
                    continue
                if self.checkForEntropyHmax(row):
                    continue

                metadata, description, values = self.checkNumberOfColumns(row)

                # if we are in the description row, we can count the years (periods) if we didn't define them in the header
                if metadata[0].lower().replace(" ", "") == "transfertype":
                    self.checkForTimeIndex(values)
                # the other rows contain data (but we ignore empty rows) relevant for the Matflow calculation
                else:
                    self.checkAndHandleEntropyData(metadata, values)
                    self.checkAndHandleData(row, metadata, description, values)

                # if metadata is missing information (TargetMaterial and TargetUnit) get it from the sourceMaterial and sourceUnit
                if metadata[5] == "":
                    metadata[5] = metadata[2]
                if metadata[6] == "":
                    metadata[6] = metadata[3]

                self.rowNumber += 1

            # changing 'delay' nodes to 'rate' and 'sink' nodes if they have no
            # delayed releases or neither delayed releases nor transfers.
            self.delayToRateSink()

            return self.system, self.concentrationEntropy

    # check and log input for 'runs'
    def checkForRuns(self, row):
        if not self.haveRuns:
            if row[0].lower() == "runs:":
                if len(row[1]) == 0:
                    raise CSVParserException(
                        ("row %d, col %s: is empty.\n" +
                         "Please enter an integer > 0.")
                        % (self.rowNumber, self.colString(1)))
                else:
                    try:
                        self.system.runs = int(row[1])
                        if self.system.runs < 1:
                            raise CSVParserException(
                                ("row %d, col %s:\nThe input for the number of runs " +
                                 "is smaller than 1.\nPlease enter an integer > 0.")
                                % (self.rowNumber, self.colString(1)))
                    except ValueError:
                        raise CSVParserException(
                            ("row %d, col %s:\nCould not convert string '%s' to " +
                             "an integer.\nUse an integer > 0 representing the " +
                             "number of runs for the model to calculate.")
                            % (self.rowNumber, self.colString(1), row[1]))
            else:
                raise CSVParserException(
                    ("row %d:\nFirst non-comment row not containing information " +
                     "about the number of runs.\nPlease enter 'runs:' into " +
                     "column %s and an integer > 0 representing the number of " +
                     "runs relevant for the calculations into column %s.")
                    % (self.rowNumber, self.colString(0), self.colString(1)))

            self.rowNumber += 1
            self.haveRuns = True
            return True
        return False

    # check and log input for 'periods'
    def checkForPeriods(self, row):
        if not self.havePeriods:
            if row[0].lower() == "periods:":
                if len(row[1].replace(" ", "")) == 0:
                    self.system.periods = 0
                else:
                    try:
                        self.system.periods = int(row[1])
                        if self.system.periods < 0 or self.system.periods == 1:
                            raise CSVParserException(
                                ("row %d, col %s:\nThe value '1' or negative values " +
                                 "for the numbers of periods are not allowed.\nEither " +
                                 "use '0' or leave the cell empty if the number of " +
                                 "periods shall be the number of time indices,\nor " +
                                 "use an integer > 1 representing the number of " +
                                 "periods relevant for the calculations.")
                                % (self.rowNumber, self.colString(1)))
                    except ValueError:
                        raise CSVParserException(
                            ("row %d, col %s:\nCould not convert string '%s' to " +
                             "an integer.\nEither use '0' or leave the cell empty " +
                             "if the number of periods shall be the number of " +
                             "time indices,\nor use an integer > 1 representing " +
                             "the number of periods relevant for the calculations.")
                            % (self.rowNumber, self.colString(1), row[1]))
            else:
                raise CSVParserException(
                    ("row %d:\nSecond non-comment row not containing " +
                     "information about the number of periods.\nPlease enter " +
                     "'periods:' into column %s and an integer representing " +
                     "the number of periods relevant for the calculations into " +
                     "column %s. If the number of periods shall be equal to " +
                     "the number of time indices, insert '0' or leave the cell " +
                     "empty.")
                    % (self.rowNumber, self.colString(0), self.colString(1)))
            self.rowNumber += 1
            self.havePeriods = True
            return True
        return False

    # check and log input for 'median'
    def checkForMedian(self, row):
        if not self.haveMedian:
            if row[0].lower() == "median:":
                if len(row[1]) == 0:
                    pass
                elif row[1].lower().replace(" ", "") in ["0", "n", "no", "none"]:
                    pass
                elif row[1].lower().replace(" ", "") in ["1", "y", "yes"]:
                    self.system.median = True
                else:
                    raise CSVParserException(
                        ("row %d, col %s:\nWrong input for 'median:', got '%s'. " +
                         "\nHere, you can choose, if you want to display the " +
                         "median values in the result file.\nFor the inputs " +
                         "'0', 'n', 'no', 'none' or an empty cell no medians "
                         "will be displayed. For the inputs '1', 'y' or 'yes' " +
                         "the median values will be displayed.")
                        % (self.rowNumber, self.colString(1), row[1]))


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
                    % (self.rowNumber, self.colString(0), self.colString(1)))

            self.rowNumber += 1
            self.haveMedian = True
            return True
        return False

    # check and log input for 'percentiles'
    def checkForPercentiles(self, row):
        if not self.havePercentiles:
            if row[0].lower() == "percentiles:":
                if len(row[1]) == 0:
                    pass
                else:
                    try:
                        self.system.percentiles = list(map(int, str.split(row[1], "|")))
                    except ValueError:
                        raise CSVParserException(
                            ("row %d, col %s:\nCould not convert string '%s' to " +
                             "integers.\nPlease, use integers between 0 and 100 " +
                             "separated by '|'.\nThe integers represent the " +
                             "percentiles to be calculated.\nExample: '20|80' " +
                             "represents the percentiles at 20%% and 80%%.\nIf you " +
                             "leave the cell empty, no percentiles will be " +
                             "calculated.")
                            % (self.rowNumber, self.colString(1), row[1]))
                    else:
                        properInput = True
                        for i in range(len(self.system.percentiles)):
                            if self.system.percentiles[i] >= 0 and self.system.percentiles[i] <= 100:
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
                                % (self.rowNumber, self.colString(1), row[1]))
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
                    % (self.rowNumber, self.colString(0), self.colString(1)))

            self.rowNumber += 1
            self.havePercentiles = True
            return True
        return False

    # check and log input for 'plots'
    def checkAndLogPlotData(self, row):
        if not self.haveTimeSpanPlots:
            if row[0].lower().replace(" ", "") == "plots:":
                if len(row[1]) == 0 or row[1].replace(" ", "") == "0":
                    self.system.timeSpanPlots = None
                elif row[1].replace(" ", "") == "1":
                    pass
                else:
                    try:
                        self.system.timeSpanPlots = list(map(str, str.split(row[1], "|")))
                        self.system.timeSpanPlots = \
                            list(p.strip() for p in self.system.timeSpanPlots)
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
                            % (self.rowNumber, self.colString(1), row[1]))
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
                    % (self.rowNumber, self.colString(0), self.colString(1)))

            self.rowNumber += 1
            self.haveTimeSpanPlots = True
            return True
        return False

    # check if enough columns in the file
    def checkNumberOfColumns(self, row):
        if not self.system.timeIndices and len(row) < 11:
            raise CSVParserException(
                ("row %d:\nSixth non-comment row not containing enough " +
                 "columns,\nExpecting 9 metadata columns and at least 2 data " +
                 "columns, got %d.") % (self.rowNumber, len(row)))
        if self.system.timeIndices and len(row) != 9 + len(self.system.timeIndices):
            raise CSVParserException(
                ("row %d:\nNon-comment row containing wrong number of " +
                 "columns,\nExpecting 9 metadata columns and %d data columns," +
                 "got %d.") % (self.rowNumber, len(self.system.timeIndices), len(row)))

        metadata = row[0:8]  # the columns containing type, nodes etc.
        description = row[self.valuesOffset - 1]  # the 'free text' description column
        values = row[self.valuesOffset:]  # contains the values of the current row
        return metadata, description, values

    # get data from the columns and create nodes from the data
    def checkAndHandleData(self, row, metadata, description, values):
        if not self.haveTimeIndex:
            raise CSVParserException(
                ("row %d:\nExpected header row with time index or empty " +
                 "row or a row with an empty first column, got row %s")
                % (self.rowNumber, row))

        # extract the metadata
        (transferType, src, srcMaterial, srcUnit, dst, dstMaterial, dstUnit, entropyStages) = [x.lower() for x in metadata]
        # assign column numbers to the column headers
        (colTransferType, colSrc, colSrcMaterial, colSrcUnit, colDst, colDstMaterial, colDstUnit, entropyStages) = [0, 1, 2, 3, 4, 5,
                                                                                                     6, 7]

        if not dstMaterial:
            dstMaterial = srcMaterial
        if not dstUnit:
            dstUnit = srcUnit

        if metadata[5] == "":
            metadata[5] = metadata[2]

        if metadata[6] == "":
            metadata[6] = metadata[3]

        self.system.metadataMatrix.append(metadata + [description])

        # get values from data columns
        splittedValues = self.transferTypeSanityChecks(transferType, src, srcMaterial, srcUnit, dst, dstMaterial,
                                                       dstUnit,
                                                       colTransferType, colSrc, colSrcMaterial, colSrcUnit, colDst,
                                                       colDstMaterial, colDstUnit, metadata, description, values)

        nodeName = src + '_' + srcMaterial + '_' + srcUnit
        targetName = dst + '_' + dstMaterial + '_' + dstUnit

        # create nodes from metadata and data
        self.createNodes(transferType, src, srcMaterial, srcUnit, dst, dstMaterial, dstUnit,
                         colTransferType, colSrc, colSrcMaterial, colSrcUnit, colDst, colDstMaterial, colDstUnit,
                         splittedValues, nodeName, targetName, metadata, description, values)
        return

    def checkForTimeIndex(self, values):
        if self.haveTimeIndex:
            raise CSVParserException(
                "row %d:\nDuplicate header row" % (self.rowNumber))
        previous = None
        for n, timeIndex in enumerate(values):
            # sanity check if the value is an integer
            try:
                int(timeIndex)
            except ValueError:
                raise CSVParserException(
                    ("row %d, col %s:\nExpected integer time index, got '%s'")
                    % (self.rowNumber, self.colString(self.valuesOffset + n), timeIndex))
            # sanity check if the values are in sequence, separated by 1
            if previous != None and (previous + 1) != int(timeIndex):
                raise CSVParserException(
                    ("row %d, col %s:\nExpected next time index %d, got '%s'")
                    % (self.rowNumber, self.colString(self.valuesOffset + n), previous + 1, timeIndex))
            else:
                previous = int(timeIndex)

        # store the time indices in the system
        self.system.timeIndices = [int(y) for y in values]

        # adjust number of periods to number of time indices
        # (if requested or necessary)
        if self.system.periods == 0 or self.system.periods > len(self.system.timeIndices):
            self.system.periods = len(self.system.timeIndices)

        self.haveTimeIndex = True
        return

    # sanity check if supported transfer type is used
    # also we get the data from the columns if the sanity check is passed
    def transferTypeSanityChecks(self, transferType, src, srcMaterial, srcUnit, dst, dstMaterial, dstUnit,
                                 colTransferType, colSrc, colSrcMaterial, colSrcUnit, colDst, colDstMaterial,
                                 colDstUnit, metadata, description, values):
        tempArg = []
        splittedValues = []

        # sanity check if supported transfer type is used
        if transferType not in self.supportedTransferTypes:
            raise CSVParserException(
                ("row %d, col %s:\nUnexpected transfer type, got '%s' " +
                 "Please use the following transfer types:\n%s")
                % (self.rowNumber, self.colString(colTransferType),
                   transferType, str(self.supportedTransferTypes) \
                   .replace("[", "").replace("]", "").replace(",", "\n")))

        # sanity check if first transfer type in source file is an inflow
        if not self.haveInflow:
            if transferType == "inflow":
                self.haveInflow = True
            else:
                raise CSVParserException(
                    ("row %d, col %s:\nFirst transfer type is not an inflow. " +
                     "Please use 'inflow' as the first transfer type to " +
                     "generate an inflow to a target node.")
                    % (self.rowNumber, self.colString(colTransferType)))

        # sanity check if there is a name for the source compartment and
        # if it is not a number
        if transferType != "inflow" and transferType != "concentration":  # no src for inflow types
            if src.replace(" ", "") == "":
                raise CSVParserException(
                    ("row %d, col %s:\nNo name for the source node.")
                    % (self.rowNumber, self.colString(colSrc)))
            else:
                try:
                    float(src.replace(" ", "").replace(",", ""))
                except:
                    pass
                else:
                    raise CSVParserException(
                        ("row %d, col %s:\nNumber as a compartment name. A " +
                         "number is not allowed as compartment name, got '%s'.")
                        % (self.rowNumber, self.colString(colSrc), src))

        # sanity check if there is a name for the target compartment and
        # if it is not a number
        if dst.replace(" ", "") == "":
            raise CSVParserException(
                ("row %d, col %s:\nNo name for the target node.")
                % (self.rowNumber, self.colString(colDst)))
        else:
            try:
                float(dst.replace(" ", "").replace(",", ""))
            except:
                pass
            else:
                raise CSVParserException(
                    ("row %d, col %s:\nNumber as a compartment name. A number " +
                     "is not allowed as compartment name, got '%s'.")
                    % (self.rowNumber, self.colString(colDst), dst))

        # sanity check if source unit is different from target unit 
        # if transfer type is 'conversion'      
        if transferType == "conversion":
            if srcUnit == dstUnit:
                raise CSVParserException(
                    ("row %d, col %s and %s:\nSame source unit and target " +
                     "unit. When using a conversion as transfer type, the " +
                     "source unit has to be different from the target unit.")
                    % (self.rowNumber, self.colString(colSrcUnit),
                       self.colString(colDstUnit)))

        # sanity check if source and target unit are the same if
        # transfer type is neither 'conversion' nor 'inflow'
        if transferType != "conversion" and \
                        transferType != "inflow" and transferType != 'concentration':
            if srcUnit != dstUnit:
                raise CSVParserException(
                    ("row %d, col %s and %s:\nSource unit is different from " +
                     "target unit. When not using a conversion as a transfer " +
                     "type, the source unit and the target unit have to be " +
                     "the same.")
                    % (self.rowNumber, self.colString(colSrcUnit),
                       self.colString(colDstUnit)))

        # sanity check if we have the correct number of non-empty values
        if (not all(values) or (len(values) != len(self.system.timeIndices))):
            raise CSVParserException("row %d, col %s to %s:\nExpected %d values, got %s" %
                                     (self.rowNumber, self.colString(self.valuesOffset),
                                      self.colString(self.valuesOffset + len(self.system.timeIndices)),
                                      len(self.system.timeIndices), sum([bool(v) for v in values])))

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
                        % (self.rowNumber, self.colString(self.valuesOffset + c)))
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
                            % (self.rowNumber, self.colString(self.valuesOffset + c), v))
                if tempArg[0] == "fix":
                    if len(tempArg) != 2:
                        raise CSVParserException(
                            ("row %d, col %s:\nWrong number of arguments for " +
                             "inflow value type 'fix', got input '%s'. Please, " +
                             "enter the inflow value type and the respective " +
                             "value as the two arguments separated by '|'.\n" +
                             "-> example input: 'fix|30000'")
                            % (self.rowNumber, self.colString(self.valuesOffset + c), v))
                    try:
                        tempArg[1] = float(tempArg[1])
                    except ValueError:
                        raise CSVParserException(
                            ("row %d, col %s:\nCould not parse second argument " +
                             "to float, got '%s'. Please choose one float value " +
                             "as second argument.\nExamples: '30000', '30000.0', " +
                             "'30000.45'")
                            % (self.rowNumber, self.colString(self.valuesOffset + c),
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
                            % (self.rowNumber, self.colString(self.valuesOffset + c), v))
                    if tempArg[1] not in self.supportedProbabilityDistributions:
                        raise CSVParserException(
                            ("row %d, col %s:\nSecond argument is not a supported " +
                             "probability distribution function, got '%s'. " +
                             "Please, use one of the following functions:\n%s") %
                            (self.rowNumber, self.colString(self.valuesOffset + c), tempArg[1],
                             str(self.supportedProbabilityDistributions).replace(
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
                            % (self.rowNumber, self.colString(self.valuesOffset + c),
                               tempArg[2]))
                    if tempArg[1] == "normal" and len(tempArg[2]) != 2:
                        raise CSVParserException(
                            ("row %d, col %s:\nWrong number of function " +
                             "parameters for function 'normal', got input '%s'. " +
                             "Please choose exactly two floats as parameters, " +
                             "got %d parameters.\n" +
                             "-> example input: 'stoch|normal|3000, 120'")
                            % (self.rowNumber, self.colString(self.valuesOffset + c),
                               tempArg[2], len(tempArg[2])))
                    if tempArg[1] == "triangular" and len(tempArg[2]) != 3:
                        raise CSVParserException(
                            ("row %d, col %s:\nWrong number of function " +
                             "parameters for function 'triangular', got input " +
                             "'%s'. Please choose exactly three floats as " +
                             "parameters, got %d parameters.\n-> example input: " +
                             "'stoch|triangular|2880, 3000, 3120'")
                            % (self.rowNumber, self.colString(self.valuesOffset + c),
                               tempArg[2], len(tempArg[2])))
                    if tempArg[1] == "uniform" and len(tempArg[2]) != 2:
                        raise CSVParserException(
                            ("row %d, col %s:\nWrong number of function " +
                             "parameters for function 'uniform', got input '%s'. " +
                             "Please choose exactly two floats as parameters, " +
                             "got %d parameters.\n" +
                             "-> example input: 'stoch|uniform|2880, 3120'")
                            % (self.rowNumber, self.colString(self.valuesOffset + c),
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
                            % (self.rowNumber, self.colString(self.valuesOffset + c), v))
                    try:
                        tempArg[1] = \
                            list(float(p) for p in str.split(tempArg[1], ","))
                    except ValueError:
                        raise CSVParserException(
                            ("row %d, col %s:\nCould not parse the values to " +
                             "floats, got '%s'. Please choose floats as list " +
                             "items.\nExample: '30000, 31000.5, 29750.7'")
                            % (self.rowNumber, self.colString(self.valuesOffset + c),
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
                        % (self.rowNumber, self.colString(self.valuesOffset + c), v))

                splittedValues.append(tempArg)

        # sanity checks for the values when using 'rate', 'conversion' or
        # 'fraction' as transfer type
        if transferType in self.supportedTransferTypes and \
                        transferType != 'inflow' and transferType != 'delay' \
                        and transferType != 'concentration':
            valuesConv = []
            for c, v in enumerate(values):
                if v.replace(" ", "") == "":
                    raise CSVParserException(
                        ("row %d, col %s:\nMissing input. Please choose a " +
                         "transfer value type (fix, stoch or rand) and " +
                         "enter the respective arguments separated by '|'.\n" +
                         "Examples: 'fix|0.8|1'\n" +
                         "          'stoch|normal|0.5, 0.15|1'\n" +
                         "          'rand|0.65, 0.7, 0.71, 0.75, 0.8|1'")
                        % (self.rowNumber, self.colString(self.valuesOffset + c)))
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
                            (self.rowNumber, self.colString(self.valuesOffset + c), v))
                if tempArg[0] == "fix":
                    if len(tempArg) != 3:
                        raise CSVParserException(
                            ("row %d, col %s:\nWrong input for 'fix' " +
                             "transfer value type, got '%s'. Please enter the " +
                             "following three arguments separated by '|':\n" +
                             "1. transfer value type,\n2. value,\n3. priority\n" +
                             "-> example input: 'fix|0.8|1'")
                            % (self.rowNumber, self.colString(self.valuesOffset + c), v))
                    try:
                        tempArg[1] = [float(tempArg[1])]
                    except ValueError:
                        raise CSVParserException(
                            ("row %d, col %s:\nCould not parse second argument " +
                             "to float, got '%s'. Please choose a float value " +
                             "as the second argument.\nExample: '0.8'")
                            % (self.rowNumber, self.colString(self.valuesOffset + c),
                               tempArg[1]))
                    if transferType == "fraction" or transferType == "rate":
                        if tempArg[1][0] > 1.0 or tempArg[1][0] < 0:
                            raise CSVParserException(
                                ("\n--------------------\n" +
                                 "row %d, col %s:\nRate is bigger than 1 or negative. " +
                                 "Only positive rates <= 1.0 are allowed, got '%s'")
                                % (self.rowNumber, self.colString(self.valuesOffset + c),
                                   tempArg[1][0]))
                    if transferType == "conversion":
                        if tempArg[1][0] < 0:
                            raise CSVParserException(
                                ("\n--------------------\n" +
                                 "row %d, col %s:\nRate is negative. " +
                                 "Only positive rates are allowed, got '%s'")
                                % (self.rowNumber, self.colString(self.valuesOffset + c),
                                   tempArg[1][0]))
                    try:
                        tempArg[2] = int(tempArg[2])
                    except ValueError:
                        raise CSVParserException(
                            ("row %d, col %s:\nCould not parse third argument " +
                             "to integer, got '%s'. Please choose an integer as " +
                             "the third argument.")
                            % (self.rowNumber, self.colString(self.valuesOffset + c),
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
                            % (self.rowNumber, self.colString(self.valuesOffset + c), v))
                    if tempArg[1] not in self.supportedProbabilityDistributions:
                        raise CSVParserException(
                            ("row %d, col %s:\nSecond argument is not a supported " +
                             "probability distribution function, got '%s'. " +
                             "Please, use one of the following functions:\n%s") %
                            (self.rowNumber, self.colString(self.valuesOffset + c), tempArg[1],
                             str(self.supportedProbabilityDistributions).replace(
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
                            % (self.rowNumber, self.colString(self.valuesOffset + c),
                               tempArg[2]))
                    if transferType == "fraction" or transferType == "rate":
                        for i in range(len(tempArg[2])):
                            if tempArg[2][i] > 1.0 or tempArg[2][i] < 0:
                                raise CSVParserException(
                                    ("\n--------------------\n" +
                                     "row %d, col %s:\nRates or parameters are bigger " +
                                     "than 1 or negative. Only positive rates and " +
                                     "parameters <= 1.0 are allowed, got '%s'")
                                    % (self.rowNumber, self.colString(self.valuesOffset + c),
                                       tempArg[2]))
                    if transferType == "conversion":
                        for i in range(len(tempArg[2])):
                            if tempArg[2][i] < 0:
                                raise CSVParserException(
                                    ("\n--------------------\n" +
                                     "row %d, col %s:\nRates or parameters are " +
                                     "negative. Only positive rates and " +
                                     "parameters are allowed, got '%s'")
                                    % (self.rowNumber, self.colString(self.valuesOffset + c),
                                       tempArg[2]))
                    try:
                        tempArg[3] = int(tempArg[3])
                    except ValueError:
                        raise CSVParserException(
                            ("row %d, col %s:\nCould not parse fourth argument " +
                             "to integer, got '%s'. Please choose an integer as " +
                             "the fourth argument.")
                            % (self.rowNumber, self.colString(self.valuesOffset + c),
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
                            % (self.rowNumber, self.colString(self.valuesOffset + c), v))
                    try:
                        tempArg[1] = \
                            list(float(p) for p in str.split(tempArg[1], ","))
                    except ValueError:
                        raise CSVParserException(
                            ("row %d, col %s:\nCould not parse the list to " +
                             "floats, got '%s'. Please choose floats as list " +
                             "items.\nExample: '0.7, 0.69, 0.71, 0.74'")
                            % (self.rowNumber, self.colString(self.valuesOffset + c),
                               tempArg[1]))
                    if transferType == "fraction" or transferType == "rate":
                        for i in range(len(tempArg[1])):
                            if tempArg[1][i] > 1.0 or tempArg[1][i] < 0:
                                raise CSVParserException(
                                    ("\n--------------------\n" +
                                     "row %d, col %s:\nAt least one rate is bigger " +
                                     "than 1 or negative. Only positive rates <= " +
                                     "1.0 are allowed, got '%s'")
                                    % (self.rowNumber, self.colString(self.valuesOffset + c),
                                       tempArg[1]))
                    if transferType == "conversion":
                        for i in range(len(tempArg[1])):
                            if tempArg[1][i] < 0:
                                raise CSVParserException(
                                    ("\n--------------------\n" +
                                     "row %d, col %s:\nAt least one rate is " +
                                     "negative. Only positive rates are allowed, " +
                                     "got '%s'")
                                    % (self.rowNumber, self.colString(self.valuesOffset + c),
                                       tempArg[1]))
                    try:
                        tempArg[2] = int(tempArg[2])
                    except ValueError:
                        raise CSVParserException(
                            ("row %d, col %s:\nCould not parse third argument " +
                             "to integer, got '%s'. Please choose an integer as " +
                             "the third argument.")
                            % (self.rowNumber, self.colString(self.valuesOffset + c),
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
                        % (self.rowNumber, self.colString(self.valuesOffset + c), v))
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
                        % (self.rowNumber, self.colString(self.valuesOffset + c)))
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
                            % (self.rowNumber, self.colString(self.valuesOffset + c), v))
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
                            % (self.rowNumber, self.colString(self.valuesOffset + c), v))
                    try:
                        tempArg[1] = [float(tempArg[1])]
                    except ValueError:
                        raise CSVParserException(
                            ("row %d, col %s:\nCould not parse second argument " +
                             "to float, got '%s'. Please choose a float value " +
                             "as the second argument.\nExample: '0.8'")
                            % (self.rowNumber, self.colString(self.valuesOffset + c),
                               tempArg[1]))
                    if tempArg[1][0] > 1.0 or tempArg[1][0] < 0:
                        raise CSVParserException(
                            ("\n--------------------\n" +
                             "row %d, col %s:\nRate is bigger than 1 or " +
                             "negative. Only positive rates <= 1.0 are allowed" +
                             ", got '%s'")
                            % (self.rowNumber, self.colString(self.valuesOffset + c),
                               tempArg[1][0]))
                    try:
                        tempArg[2] = int(tempArg[2])
                    except ValueError:
                        raise CSVParserException(
                            ("row %d, col %s:\nCould not parse third argument " +
                             "to integer, got '%s'. Please choose an integer as " +
                             "the third argument.")
                            % (self.rowNumber, self.colString(self.valuesOffset + c),
                               tempArg[2]))
                    if tempArg[3] not in self.supportedReleaseFunctions:
                        raise CSVParserException(
                            ("row %d, col %s:\nFourth argument is not a " +
                             "supported release function, got '%s'. Please " +
                             "choose a supported release function as the " +
                             "fourth argument.")
                            % (self.rowNumber, self.colString(self.valuesOffset + c),
                               tempArg[3]))
                    try:
                        tempArg[4] = \
                            list(float(p) for p in str.split(tempArg[4], ","))
                    except ValueError:
                        raise CSVParserException(
                            ("row %d, col %s:\nCould not parse the values to " +
                             "floats, got '%s'. Please choose floats as " +
                             "fifth argument.")
                            % (self.rowNumber, self.colString(self.valuesOffset + c),
                               tempArg[4]))
                    if tempArg[3] == "fix" or tempArg[3] == "rand" or \
                                    tempArg[3] == "list":
                        for i in range(len(tempArg[4])):
                            if tempArg[4][i] > 1.0 or tempArg[4][i] < 0:
                                raise CSVParserException(
                                    ("\n--------------------\n" +
                                     "row %d, col %s:\nRates or parameters are bigger " +
                                     "than 1 or negative. Only positive rates and " +
                                     "parameters <= 1.0 are allowed, got '%s'")
                                    % (self.rowNumber, self.colString(self.valuesOffset + c),
                                       tempArg[4]))
                    try:
                        tempArg[5] = int(tempArg[5])
                    except ValueError:
                        raise CSVParserException(
                            ("row %d, col %s:\nCould not parse sixth argument " +
                             "to integer, got '%s'. Please choose an integer as " +
                             "the sixth argument.")
                            % (self.rowNumber, self.colString(self.valuesOffset + c),
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
                            % (self.rowNumber, self.colString(self.valuesOffset + c), v))
                    if tempArg[1] not in self.supportedProbabilityDistributions:
                        raise CSVParserException(
                            ("row %d, col %s:\nSecond argument is not a supported " +
                             "probability distribution function, got '%s'. " +
                             "Please, use one of the following functions:\n%s") %
                            (self.rowNumber, self.colString(self.valuesOffset + c), tempArg[1],
                             str(self.supportedProbabilityDistributions).replace(
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
                            % (self.rowNumber, self.colString(self.valuesOffset + c),
                               tempArg[2]))
                    for i in range(len(tempArg[2])):
                        if tempArg[2][i] > 1.0 or tempArg[2][i] < 0:
                            raise CSVParserException(
                                ("\n--------------------\n" +
                                 "row %d, col %s:\nRates or parameters are bigger " +
                                 "than 1 or negative. Only positive rates and " +
                                 "parameters <= 1.0 are allowed, got '%s'")
                                % (self.rowNumber, self.colString(self.valuesOffset + c),
                                   tempArg[2]))
                    try:
                        tempArg[3] = int(tempArg[3])
                    except ValueError:
                        raise CSVParserException(
                            ("row %d, col %s:\nCould not parse fourth argument " +
                             "to integer, got '%s'. Please choose an integer as " +
                             "the fourth argument.")
                            % (self.rowNumber, self.colString(self.valuesOffset + c),
                               tempArg[3]))
                    if tempArg[4] not in self.supportedReleaseFunctions:
                        raise CSVParserException(
                            ("row %d, col %s:\nFifth argument is not a " +
                             "supported release function, got '%s'. Please " +
                             "choose a supported release function as the " +
                             "fifth argument.")
                            % (self.rowNumber, self.colString(self.valuesOffset + c),
                               tempArg[4]))
                    try:
                        tempArg[5] = \
                            list(float(p) for p in str.split(tempArg[5], ","))
                    except ValueError:
                        raise CSVParserException(
                            ("row %d, col %s:\nCould not parse the values to " +
                             "floats, got '%s'. Please choose floats as " +
                             "sixth argument.")
                            % (self.rowNumber, self.colString(self.valuesOffset + c),
                               tempArg[5]))
                    if tempArg[4] == "fix" or tempArg[4] == "rand" or \
                                    tempArg[4] == "list":
                        for i in range(len(tempArg[5])):
                            if tempArg[5][i] > 1.0 or tempArg[5][i] < 0:
                                raise CSVParserException(
                                    ("\n--------------------\n" +
                                     "row %d, col %s:\nRates or parameters are bigger " +
                                     "than 1 or negative. Only positive rates and " +
                                     "parameters <= 1.0 are allowed, got '%s'")
                                    % (self.rowNumber, self.colString(self.valuesOffset + c),
                                       tempArg[5]))
                    try:
                        tempArg[6] = int(tempArg[6])
                    except ValueError:
                        raise CSVParserException(
                            ("row %d, col %s:\nCould not parse seventh argument " +
                             "to integer, got '%s'. Please choose an integer as " +
                             "the seventh argument.")
                            % (self.rowNumber, self.colString(self.valuesOffset + c),
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
                            % (self.rowNumber, self.colString(self.valuesOffset + c), v))
                    try:
                        tempArg[1] = \
                            list(float(p) for p in str.split(tempArg[1], ","))
                    except ValueError:
                        raise CSVParserException(
                            ("row %d, col %s:\nCould not parse the list to " +
                             "floats, got '%s'. Please choose floats as list " +
                             "items.\nExample: '0.7, 0.69, 0.71, 0.74'")
                            % (self.rowNumber, self.colString(self.valuesOffset + c),
                               tempArg[1]))
                    for i in range(len(tempArg[1])):
                        if tempArg[1][i] > 1.0 or tempArg[1][i] < 0:
                            raise CSVParserException(
                                ("\n--------------------\n" +
                                 "row %d, col %s:\nRates are bigger than 1 or " +
                                 "negative. Only positive rates <= 1.0 are " +
                                 "allowed, got '%s'")
                                % (self.rowNumber, self.colString(self.valuesOffset + c),
                                   tempArg[1]))
                    try:
                        tempArg[2] = int(tempArg[2])
                    except ValueError:
                        raise CSVParserException(
                            ("row %d, col %s:\nCould not parse third argument " +
                             "to integer, got '%s'. Please choose an integer as " +
                             "the third argument.")
                            % (self.rowNumber, self.colString(self.valuesOffset + c),
                               tempArg[2]))
                    if tempArg[3] not in self.supportedReleaseFunctions:
                        raise CSVParserException(
                            ("row %d, col %s:\nFourth argument is not a " +
                             "supported release function, got '%s'. Please " +
                             "choose a supported release function as the " +
                             "fourth argument.")
                            % (self.rowNumber, self.colString(self.valuesOffset + c),
                               tempArg[3]))
                    try:
                        tempArg[4] = \
                            list(float(p) for p in str.split(tempArg[4], ","))
                    except ValueError:
                        raise CSVParserException(
                            ("row %d, col %s:\nCould not parse the values to " +
                             "floats, got '%s'. Please choose floats as " +
                             "fifth argument.")
                            % (self.rowNumber, self.colString(self.valuesOffset + c),
                               tempArg[4]))
                    if tempArg[3] == "fix" or tempArg[3] == "rand" or \
                                    tempArg[3] == "list":
                        for i in range(len(tempArg[4])):
                            if tempArg[4][i] > 1.0 or tempArg[4][i] < 0:
                                raise CSVParserException(
                                    ("\n--------------------\n" +
                                     "row %d, col %s:\nRates or parameters are bigger " +
                                     "than 1 or negative. Only positive rates and " +
                                     "parameters <= 1.0 are allowed, got '%s'")
                                    % (self.rowNumber, self.colString(self.valuesOffset + c),
                                       tempArg[4]))
                    try:
                        tempArg[5] = int(tempArg[5])
                    except ValueError:
                        raise CSVParserException(
                            ("row %d, col %s:\nCould not parse sixth argument " +
                             "to integer, got '%s'. Please choose an integer as " +
                             "the sixth argument.")
                            % (self.rowNumber, self.colString(self.valuesOffset + c),
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
                        % (self.rowNumber, self.colString(self.valuesOffset + c), v))

                splittedValues.append(tempArg)

        return splittedValues


    # create nodes from metadata and read data
    def createNodes(self, transferType, src, srcMaterial, srcUnit, dst, dstMaterial, dstUnit, colTransferType, colSrc,
                    colSrcMaterial, colSrcUnit, colDst, colDstMaterial, colDstUnit, splittedValues, nodeName,
                    targetName, metadata, description, values):
        # creating target node if it doesn't exist yet
        # (as we don't know the target node's outgoing links yet, we create
        #  the node as 'delay'and will change it later, if necessary.)
        if targetName not in self.system.nodes:
            self.system.nodes[targetName] = "delay"
            self.system.delays[targetName] = DelayData(dst, dstMaterial, dstUnit)

        # creating source node if it doesn't exist yet or
        # extending/changing it if it already exists
        if transferType == "inflow":
            nodeName = "inflow " + str(len(self.system.inflows) + 1)
            self.system.nodes[nodeName] = "inflow"
            self.system.inflows[nodeName] = InflowData(nodeName, dst, dstMaterial,
                                                       dstUnit, splittedValues,
                                                       description)
        elif transferType == "delay":
            if nodeName not in self.system.nodes:
                self.system.nodes[nodeName] = "delay"
                self.system.delays[nodeName] = DelayData(src, srcMaterial, srcUnit)
                self.system.delays[nodeName].descriptions[targetName] = description
                self.system.delays[nodeName].transfers[targetName] = []
                self.system.delays[nodeName].releases[targetName] = []
                for i in range(len(splittedValues)):
                    self.system.delays[nodeName].transfers[targetName].append(splittedValues[i][:-3])
                    self.system.delays[nodeName].releases[targetName].append(splittedValues[i][-3:])
            else:
                if self.system.nodes[nodeName] == "delay":
                    if (targetName in self.system.delays[nodeName].descriptions or
                                targetName in self.system.delays[nodeName].transfers):
                        raise CSVParserException(
                            ("row %d:\nOnly one link between a source node and " +
                             "a target node allowed. The following link already " +
                             "exists:\n%s -> %s")
                            % (self.rowNumber, src, dst))
                    else:
                        self.system.delays[nodeName].descriptions[targetName] = description
                        self.system.delays[nodeName].transfers[targetName] = []
                        self.system.delays[nodeName].releases[targetName] = []
                    for i in range(len(splittedValues)):
                        self.system.delays[nodeName].transfers[targetName].append(splittedValues[i][:-3])
                        self.system.delays[nodeName].releases[targetName].append(splittedValues[i][-3:])
                else:
                    raise CSVParserException(
                        ("row %d:\nNo 'rate' or 'delay' link allowed for nodes " +
                         "which are already source node of a 'conversion' or " +
                         "'fraction' link.") % (self.rowNumber))
        elif transferType == "rate":
            if nodeName not in self.system.nodes:
                # create a 'delay' node (src node could still have 'delay' links)
                self.system.nodes[nodeName] = "delay"
                self.system.delays[nodeName] = DelayData(src, srcMaterial, srcUnit)
                self.system.delays[nodeName].descriptions[targetName] = description
                self.system.delays[nodeName].transfers[targetName] = splittedValues
            else:
                if self.system.nodes[nodeName] == "delay":
                    if (targetName in self.system.delays[nodeName].descriptions or
                                targetName in self.system.delays[nodeName].transfers):
                        raise CSVParserException(
                            ("row %d:\nOnly one link between a source node and " +
                             "a target node allowed. The following link already " +
                             "exists:\n%s -> %s") % (self.rowNumber, src, dst))
                    else:
                        self.system.delays[nodeName].descriptions[targetName] = description
                        self.system.delays[nodeName].transfers[targetName] = splittedValues
                else:
                    raise CSVParserException(
                        ("row %d:\nNo 'rate' or 'delay' link allowed for nodes " +
                         "which are already source node of a 'conversion' or " +
                         "'fraction' link.\n source node: %s")
                        % (self.rowNumber, src))
        elif transferType == "conversion":
            if nodeName not in self.system.nodes:
                self.system.nodes[nodeName] = "conversion"
                self.system.rates[nodeName] = RateData(src, srcMaterial, srcUnit, "conversion")
                self.system.rates[nodeName].descriptions[targetName] = description
                self.system.rates[nodeName].transfers[targetName] = splittedValues
            else:
                if self.system.nodes[nodeName] == "delay":
                    if (self.system.delays[nodeName].transfers or
                            self.system.delays[nodeName].releases or
                            self.system.delays[nodeName].descriptions):
                        raise CSVParserException(
                            ("row %d:\nSource node of a 'conversion' link "+
                             "already exists as a source node of a different "+
                             "link.\nsource node: %s") % (self.rowNumber, src))
                    else:
                        self.system.nodes[nodeName] = "conversion"
                        self.system.delays[nodeName] = None
                        del self.system.delays[nodeName]
                        self.system.rates[nodeName] = RateData(src, srcMaterial, srcUnit, "conversion")
                        self.system.rates[nodeName].descriptions[targetName] = description
                        self.system.rates[nodeName].transfers[targetName] = splittedValues
                else:
                    raise CSVParserException(
                        ("row %d:\nSource node of a 'conversion' link already " +
                         "exists as a source node of a different link.\n" +
                         "source node: %s") % (self.rowNumber, src))
        elif transferType == "fraction":
            if nodeName not in self.system.nodes:
                self.system.nodes[nodeName] = "fraction"
                self.system.rates[nodeName] = RateData(src, srcMaterial, srcUnit, "fraction")
                self.system.rates[nodeName].descriptions[targetName] = description
                self.system.rates[nodeName].transfers[targetName] = splittedValues
            elif self.system.nodes[nodeName] == "delay":
                if (self.system.delays[nodeName].transfers or
                        self.system.delays[nodeName].releases or
                        self.system.delays[nodeName].descriptions):
                    raise CSVParserException(
                        ("row %d:\nSource node of a 'fraction' link " +
                         "already exists as a source node of a different " +
                         "link.\nsource node: %s") % (self.rowNumber, src))
                else:
                    self.system.nodes[nodeName] = "fraction"
                    self.system.delays[nodeName] = None
                    del self.system.delays[nodeName]
                    self.system.rates[nodeName] = RateData(src, srcMaterial, srcUnit, "fraction")
                    self.system.rates[nodeName].descriptions[targetName] = description
                    self.system.rates[nodeName].transfers[targetName] = splittedValues
            elif self.system.nodes[nodeName] == "fraction":
                if (targetName in self.system.rates[nodeName].descriptions or targetName in self.system.rates[
                    nodeName].transfers):
                    raise CSVParserException(
                        ("row %d:\nOnly one link between a source node and a " +
                         "target node allowed. The following link already " +
                         "exists:\n%s -> %s") % (self.rowNumber, src, dst))
                else:
                    self.system.rates[nodeName].descriptions[targetName] = description
                    self.system.rates[nodeName].transfers[targetName] = splittedValues
            else:
                raise CSVParserException(
                    ("row %d:\nSource node of a 'fraction' link " +
                     "already exists as a source node of a different " +
                     "link.\nsource node: %s") % (self.rowNumber, src))
        elif transferType == 'concentration':
            return
        else:
            raise CSVParserException(
                ("row %d:\nUnexpected transfer type, got '%s'.")
                % (self.rowNumber, transferType))
        return

    # - changing 'delay' nodes to 'rate' and 'sink' nodes if they have no
    #   delayed releases or neither delayed releases nor transfers.
    # - adding release strategies to the delay nodes which haven't
    #   a release strategy for all transfers (because these are not delayed)
    def delayToRateSink(self):
        for node in list(self.system.nodes.keys()):
            if (self.system.nodes[node] == "delay" and
                    (not self.system.delays[node].releases) and
                    (not self.system.delays[node].transfers)):
                self.system.nodes[node] = "sink"
                tempNode = self.system.delays[node]
                self.system.sinks[node] = \
                    SinkData(tempNode.category, tempNode.material, tempNode.unit)
                self.system.delays[node] = None
                del self.system.delays[node]
            elif (self.system.nodes[node] == "delay" and (not self.system.delays[node].releases)):
                self.system.nodes[node] = "rate"
                tempNode = self.system.delays[node]
                self.system.rates[node] = \
                    RateData(tempNode.category, tempNode.material, tempNode.unit,
                             "rate", tempNode.transfers, tempNode.descriptions)
                self.system.delays[node] = None
                del self.system.delays[node]
            elif self.system.nodes[node] == "delay":
                for target in list(self.system.delays[node].transfers.keys()):
                    if (target not in self.system.delays[node].releases):
                        tempLength = len(self.system.delays[node].transfers[target])
                        self.system.delays[node].releases[target] = []
                        for i in range(tempLength):
                            self.system.delays[node].releases[target].append(['fix', [1.0], 0])
            else:
                pass
        return

    # is used for the column number in the exception
    def colString(self, n):
        n += 1
        s = ""
        while n != 0:
            s += chr((n - 1) % 26 + 65)
            n //= 27
        return s[::-1]


    def checkAndHandleEntropyData(self, metadata, values):
        # if the value is for entropy calculation add it to the concentrations
        if metadata[0].lower() == "concentration":
            for c, v in enumerate(values):
                if float(v) > 1 or float(v) < 0:
                    raise CSVParserException(
                        ("row %d, col %s:\nThe concentration value for the entropy calculation " +
                         "got '%s'. Please enter a concentration between 1 and 0")
                        % (self.rowNumber, self.colString(self.valuesOffset + c), v))
            srcName = (metadata[1] + "_" +
                        metadata[2] + "_" +
                        metadata[3]).lower()
            targName = (metadata[4] + "_" +
                        metadata[5] + "_" +
                        metadata[6]).lower()

            self.concentrationEntropy[srcName, targName] = values

    # check and log input for 'entropyHmax'
    def checkForEntropyHmax(self, row):
        if not self.haveEntropy:
            #if Hmax is equal to 0, don't calculate the entropy
            if row[0].lower().replace(" ", "") == "entropyhmax:":
                if len(row[1]) == 0 or float(row[1]) == 0:
                    pass
                elif float(row[1]) >= 0:
                    #if Hmax is a value > 0 calculate the entropy and set Hmax in the system
                    self.system.entropy = True
                    self.system.Hmax = float(row[1])
                else:
                    raise CSVParserException(
                        ("row %d, col %s:\nWrong input for 'entropy:', got '%s'. " +
                         "\nHere, you can choose, if you want to display the " +
                         "entropy values in the result file.\nFor the inputs " +
                         "'0', 'n', 'no', 'none' or an empty cell no entropy "
                         "will be displayed. For the inputs '1', 'y' or 'yes' " +
                         "the entropy values will be displayed.")
                        % (self.rowNumber, self.colString(1), row[1]))


            else:
                raise CSVParserException(
                    ("row %d: Sixth non-comment row not containing " +
                     "information about the entropy values.\nPlease enter " +
                     "'entropy:' into column %s. With an input in column %s " +
                     "you can choose, if you want to display the " +
                     "entropy values in the result file.\nFor the inputs " +
                     "'0', 'n', 'no', 'none' or an empty cell no entropy "
                     "will be displayed. For the inputs '1', 'y' or 'yes' " +
                     "the entropy values will be displayed.")
                    % (self.rowNumber, self.colString(0), self.colString(1)))

            self.rowNumber += 1
            self.haveEntropy = True
            return True
        return False


class CSVParserException(Exception):
    def __init__(self, error):
        self.error = error
        # pass