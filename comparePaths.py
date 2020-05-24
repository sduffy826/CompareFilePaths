# Has class and example mainline to compare file paths, wrote because I had code that
# I suspected was duplicated in multiple workspaces and I wanted to dedupe/cleanup/consolidate
# the workspaces.  Take a look at the description below
# 
# SDuffy 2020-05-23

import sys
import os
import time
import glob
import datetime
import math
import filecmp
import difflib
# import regex module
import re 

# This class was built to compare files in different paths.  It will generate a csv file that
# has different sections, one for matches, one for differences and one for missing.  The records
# in the csv are in two columns, column1 is for path1 and column2 is path2.  If you don't see 
# a value in the columne (for missing section) then it means it's missing from there.
# Note: The match is done by filename, you could have save the same file in several subdirectories
#       that's why you may see 'MULTIPLE' for a given column, it means a given file was found
#       in the other path but it didn't match, and the other path has same filename in multiple
#       locations.  
# The program can also identify the delta's between files (not MULTIPLE), if you want to see that just
#   pass a 'true' as the fourth arg (shows in example mainline), it will generate an html file
# Also note: I removed the 'starting' search path from the files in the output, it was easier to 
#   read, down the road if you don't want that just make another flag and change the program to 
#   strip the path based on the flag state.
# Typical usage of this can be seen in the example mainline, but at a high level you:
#  1) Instantiate (pass in path1, path2, filepattern, <flagToWriteDeltas>, <debugFlag>)
#  2) <Can set the delta output file with method setDeltaOutputFile, and the csv output file
#     with setCSVOutputFile (both just pass the name of the file), note the deltaOutputFile is
#     appended to, so if you don't want that then delete before running this :)
#  3) Call the performCompare method
#  4) Analyze the output file(s) :)
class ComparePaths:
  MULTITAG = "MULTIPLE"

  def __init__(self, path1, path2, filePattern="*", writeDeltas=False, debugFlag=False):
    self.path1           = path1
    self.path2           = path2
    self.filePattern     = filePattern
    self.flagWriteDeltas = writeDeltas
    self.debugFlag       = debugFlag
    self.deltaOutputFile = "fileDeltas.html"
    self.csvOutputFile   = "pathComparison.csv"
    
  # Compare two sets of files, you pass
  #   dictOfAttributes1 - A dictionary that has the file attributes for a given path
  #   dictOfFileToPath1 - Dictionary that has the filename (only) and a list of all the paths it exists in
  #   dictOfAttributes2 - Same as (1) above, but for second set of paths
  #   dictOfFileToPath2 - Same as (2) above, also for second set of filenames
  # It Returns three lists:
  #   matches - each record has the paths that match i.e. (pathFromFirstList, matchedPathFromSecondList)
  #   missing - each record is a tuple in form of (filename1, filename2), you'll only have the
  #               existing of one filename, the other tuple value will be '', if you had
  #               ('testfile.txt','') it means 'testfile.txt' is in the first argument passed
  #               in but does not exist in the second.
  #   deltas  - records have paths where attributes don't match i.e. (firstListPath, secListPath)
  #               Note: it (should be) unlikely that the same filename exists under the tree for
  #                     a given path; if it does you may see 'MULTIPLE' as the filepath designation
  #                     that means the path didn't match and the other list has multiple paths to the
  #                     same file.
  def compareFiles(self, dictOfAttributes1, dictOfFileToPath1, \
                         dictOfAttributes2, dictOfFileToPath2):

    missing   = []
    matches   = []
    different = []

    if self.debugFlag:
      print("dictOfAttributes1 len: {0} dictOfFileToPath1 len: {1} \
            dictOfAttributes2 len: {2} dictOfFileToPath2 len: {3}".format(
              len(dictOfAttributes1), len(dictOfFileToPath1),
              len(dictOfAttributes2), len(dictOfFileToPath2)
            ))
      print("dictOfAttributes1: {0}".format(dictOfAttributes1))
      print("\ndictOfFileToPath1: {0}".format(dictOfFileToPath1))
      print("\ndictOfAttributes2: {0}".format(dictOfAttributes2))
      print("\ndictOfFileToPath2: {0}".format(dictOfFileToPath2))

    # Check all the files in dictOfFileToPath1, we check for matches, missing and deltas 
    for fName in dictOfFileToPath1:
      if self.debugFlag: 
        print("File: {0}".format(fName))
      if fName not in dictOfFileToPath2:
        for aPath in dictOfFileToPath1[fName]:
          missing.append(tuple((aPath,"")))  # Add tuple where first position is the path of missing file
      else:     
        otherFilePaths = dictOfFileToPath2[fName]  # Get list of other paths
        for aPath in dictOfFileToPath1[fName]:
          # getMatch... you pass the attributes of this file, the array of other
          # paths and the dictionary that has the other path and it's attributes
          matchingOtherPath = self.getMatchingPathInOther(aPath, dictOfAttributes1[aPath], 
                                                          otherFilePaths, dictOfAttributes2)
          if len(matchingOtherPath) > 0:
            matches.append(tuple((aPath,matchingOtherPath)))
          else:
            # It's different... if multiple paths exist in other then just output indicator, they
            # can be reviewed manually... should be very few
            if len(otherFilePaths) > 1:
              different.append(tuple((aPath, ComparePaths.MULTITAG)))
            else:
              different.append(tuple((aPath,otherFilePaths[0])))

    # Check all the files in dictOfFileToPath2, we only need to identify the missing
    # records
    for fName in dictOfFileToPath2:
      if self.debugFlag:
        print("File(2): {0}".format(fName))
      if fName not in dictOfFileToPath1:
        for aPath in dictOfFileToPath2[fName]:
          missing.append(tuple(("",aPath))) # Write out each missing path
      else:     
        otherFilePaths = dictOfFileToPath1[fName]  # Get list of other paths
        for aPath in dictOfFileToPath2[fName]:     # Check each location where fName exists
          matchingOtherPath = self.getMatchingPathInOther(aPath, dictOfAttributes2[aPath], 
                                                          otherFilePaths, dictOfAttributes1)
          if len(matchingOtherPath) == 0:
            # It's different... if this file only exists once we don't need to report it, it
            # would have been reported in loop above.
            if len(dictOfFileToPath2[fName]) > 1:
              different.append(tuple((ComparePaths.MULTITAG,aPath)))
            
    return matches, missing, different

  # Delete file (only does if existing)
  def deleteFile(self, path):
    if os.path.exists(path):
      os.remove(path)

  # Return the file last modified time and size of a file
  def getFileDateAndSize(self, pathForFile):
    return (os.path.getmtime(pathForFile), os.path.getsize(pathForFile))

  # Return a list of files for the given path and file pattern
  def getFilesForPathAndPattern(self, pathToSearch, patternToMatch):
    pattern = pathToSearch.strip()
    if pattern[-1] != os.sep:
      pattern += os.sep
    pattern += "**" + os.sep + patternToMatch
    return glob.glob(pattern, recursive = True)

  # Return the file time in format YY-MM-DD HH:MM:SS
  def getFileTime(self, fileTime):
    return time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(fileTime))

  # This will return the path in the 'other' set of paths that matches the
  # attributes in the first argument.  The args are:
  #    Attr1 - tuple with (file timestamp, file size)
  #    otherFilePaths - A list that has all the paths of files to be checked
  #    otherAttributes - A dictionary where the path is the key, the value for it is a tuple
  #                      that matches format of Attr1
  # If a match isn't found then '' is returned.
  def getMatchingPathInOther(self, path1, attr1, otherFilePaths, otherAttributes):  
    for theOtherPath in otherFilePaths:
      if filecmp.cmp(path1,theOtherPath,False):
        return theOtherPath
      # Old way was checking attributes          
      # if Attr1[0] == otherAttributes[theOtherPath][0] and \
      #   Attr1[1] == otherAttributes[theOtherPath][1]:
      # return theOtherPath
    return ""    

  # This does the work of performing the comparison and handles generating the output
  def performCompare(self):   
    listOfFiles1 = self.getFilesForPathAndPattern(self.path1, self.filePattern)
    listOfFiles2 = self.getFilesForPathAndPattern(self.path2, self.filePattern)
    
    dictOfAttributes1, dictOfFileToPath1 = self.returnDictOfAttributesAndDictMappingName(listOfFiles1)
    dictOfAttributes2, dictOfFileToPath2 = self.returnDictOfAttributesAndDictMappingName(listOfFiles2)
    
    fileMatches, fileMissing, fileDelta = self.compareFiles(dictOfAttributes1, dictOfFileToPath1, \
                                                            dictOfAttributes2, dictOfFileToPath2)

    self.writeCSV(list((self.path1,self.path2,"Pattern: {0}".format(self.filePattern))), \
                  self.path1, self.path2, fileMatches, fileDelta, fileMissing)
    
    if self.flagWriteDeltas == True:  # Want to write out the deltas
      for aTuple in fileDelta:
        if ComparePaths.MULTITAG not in aTuple:  # Ignore files with MULTITAG set
          self.writeDelta(aTuple[0], aTuple[1])

  # Returns two dictionaries related to file (path) attributes, more below
  #  First has a dictionary where the pathWithName is key and it contains a tuple with
  #    (the file date/time, the file size)
  #  Second dictionary has filename as key (no path) and each record is a list of 
  #    pathsWithNames.  It is expected that you probably only have one record in the list
  #    but I did it this way so it would support duplicate files in nested subdirectories.
  def returnDictOfAttributesAndDictMappingName(self, listOfPaths):
    dictOfAttributes = {}
    dictMappingNames = {}

    for aPath in listOfPaths:
      dictOfAttributes[aPath] = self.getFileDateAndSize(aPath)
      fNameOnly = os.path.basename(aPath)
      if fNameOnly not in dictMappingNames:
        dictMappingNames[fNameOnly] = [] # Create empty list
      dictMappingNames[fNameOnly].append(aPath) # Append path
    return dictOfAttributes, dictMappingNames

  # Set the name of the csv file that has the output of the comparison (matches, diff, missing files)
  def setCSVOutputFile(self, outputFileName):
    self.csvOutputFile = outputFileName

  # Set the output file for the deltas
  def setDeltaOutputFile(self, outputFileName):
    self.deltaOutputFile = outputFileName

  # This function removes the startPath1 from tuple element[0] and startPath2 from
  # tuple element[1].  
  def trimStartPathFromTuples(self, startPath1, startPath2, tupleList2Fix):
    newTupleList = []
    if self.debugFlag:
      print("Tuple before: {0}".format(str(tupleList2Fix)))
    for aTuple in tupleList2Fix:
      newTupleList.append( (re.sub(startPath1,'',aTuple[0]),re.sub(startPath2,'',aTuple[1])) )
    return newTupleList

  # Write the match, differences and missing data to a csv file (easier to manage there).  fyi: The 
  # first argument should be paths that we started looking at, they will be used for labels
  # for a 'header' type of line, we'll also use them to string off of the individual filePaths
  def writeCSV(self, headerLine, startPath1, startPath2, matches, differences, missing):
    with open(self.csvOutputFile, 'w') as csv_file:
      csv_file.write(str(headerLine).strip('[]')+'\n')
      
      csv_file.write('\n\nMatches\n')
      for aLine in self.trimStartPathFromTuples(startPath1, startPath2, matches):
        csv_file.write(str(aLine).strip('()')+'\n')

      csv_file.write('\n\nDifferences\n')
      for aLine in self.trimStartPathFromTuples(startPath1, startPath2, differences):
        csv_file.write(str(aLine).strip('()')+'\n')

      csv_file.write('\n\nMissing\n')
      for aLine in self.trimStartPathFromTuples(startPath1, startPath2, missing):
        csv_file.write(str(aLine).strip('()')+"\n")

  # Write the deltas between the two files to the deltaFileName
  def writeDelta(self, path1, path2):
    with open(path1, 'U') as f:
      path1Lines = f.readlines()
    with open(path2, 'U') as f:
      path2Lines = f.readlines()

    outLines = difflib.HtmlDiff().make_table(path1Lines, path2Lines, path1, path2, context=True, numlines=3)
    with open(self.deltaOutputFile,"a") as htmlFile:
      htmlFile.writelines(outLines)
      htmlFile.write("<br /><hr /><br />")

# Mainline program just to demonstrate usage
def mainMethod():
  print("In mainline with arg length of {0}".format(len(sys.argv)))

  if len(sys.argv) < 4:
    print("Usage: {0} <path1> <path2> <filepattern> [flagWriteDeltas=False] [debugFlag=False]".format(sys.argv[0]))
    print("  i.e. {0} /eclipse/workspace /eclipse/backupworkspace \"*.java\" true true".format(sys.argv[0]))
    exit(99)

  path1           = sys.argv[1]
  path2           = sys.argv[2]
  filePattern     = sys.argv[3]
  flagWriteDeltas = False
  debugIt         = False

  if len(sys.argv) > 4:  # Passed a 5th arg use it for the flag to write the delta file
    flagWriteDeltas = (sys.argv[4].upper() == "TRUE")
  
  if len(sys.argv) > 5:  # Debug flag
    debugIt = (sys.argv[5].upper() == "TRUE")

  if debugIt:
    print("path1: {0} path2: {1} filePattern:{2}".format(path1, path2, filePattern))

  # Just for testing we'll make our output files have iso date/time (for uniqueness)
  isoDateTime = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

  # Sample: create object, set csv output filename and call the performCompare method
  # If you don't set csv/delta file they'll default to values in the constructor
  # (pathComparison.csv and fileDeltas.html)
  compFiles = ComparePaths(path1, path2, filePattern, flagWriteDeltas, debugIt)
  compFiles.setCSVOutputFile("testCSV_{0}.csv".format(isoDateTime))
  compFiles.setDeltaOutputFile("testDelta_{0}.html".format(isoDateTime))
  compFiles.performCompare()

  print("Done, do your analysis")
  
if __name__ == "__main__":
  mainMethod()