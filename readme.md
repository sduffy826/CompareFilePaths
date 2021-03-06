## Class: CompPaths 
### Example usage in class also
This class was built to compare files in different paths.  It will generate a csv file that has different sections, one for matches, one for differences and one for missing.  The records in the csv are in two columns, column1 is for path1 and column2 is path2.  If you don't see a value in the column (for missing section) then it means it's missing from there.

**Note**: The match is done by filename, you could have the same file in several subdirectories that's why you may see 'MULTIPLE' for a given column, it means a given file was found in the other path but it didn't match, and the other path has same filename in multiple locations.  

The program can also identify the delta's between files (not MULTIPLE), if you want to see that just pass a 'true' as the fourth arg (shows in example mainline), it will generate an html file that shows deltas.

**Also note**: I removed the 'starting' search path from the files in the output, it was easier to read, down the road if you don't want that just make another flag and change the program to strip the path based on the flag state.

Typical usage of the class can be seen in the example mainline.  At a high level you:
1. Instantiate (pass in path1, path2, filepattern, &lt;flagToWriteDeltas&gt;, &lt;debugFlag&gt;)
2. **Optionally:** You can set the delta output file (method setDeltaOutputFile), and the csv output file (method setCSVOutputFile).  Note: the deltaOutputFile is appended to by default, if you don't want that, then delete it first :)
3. Call the performCompare method
4. Analyze the output file(s) 