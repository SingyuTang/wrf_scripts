#!/usr/bin/env python
""" 
Python script to download selected files from rda.ucar.edu.
After you save the file, don't forget to make it executable
i.e. - "chmod 755 <name_of_script>"
"""
import sys, os
from urllib.request import build_opener

opener = build_opener()

filelist = [
  'https://data.rda.ucar.edu/d083002/grib1/2006/2006.01/fnl_20060101_00_00.grib1',
  'https://data.rda.ucar.edu/d083002/grib1/2006/2006.01/fnl_20060101_06_00.grib1',
  'https://data.rda.ucar.edu/d083002/grib1/2006/2006.01/fnl_20060101_12_00.grib1',
  'https://data.rda.ucar.edu/d083002/grib1/2006/2006.01/fnl_20060101_18_00.grib1'
]

for file in filelist:
    ofile = os.path.basename(file)
    sys.stdout.write("downloading " + ofile + " ... ")
    sys.stdout.flush()
    infile = opener.open(file)
    outfile = open(ofile, "wb")
    outfile.write(infile.read())
    outfile.close()
    sys.stdout.write("done\n")
