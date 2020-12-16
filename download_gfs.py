#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
NAME
    download_gfs
KEYWORD ARGUMENTS
    Start and End date (Format: YYYY-MM-DD)
    Output directory path
    Earliest date 1st January 2007 (20200515),
    there are no weather data before that date to download (status June2020)
DESCRIPTION
    download_gfs downloads weather data (analysis 0.5 degree grid) from nomads.ncdc.noaa.gov
    linux os is required
NOTE
    The files will not be renamed and not be checked if the download succeded!

    Comments / improvements are welcome.

CONTACT
    c.c.symonds@leeds.ac.uk
    Version 2, June 2020

DISCLAIMER
    This software is based heavily on code written by florian.geyer@zamg.ac.at for the
        FLEXPART workshop 2019 @ ZAMG, with changes to:
        a) bring up to python3
        b) allow parsing of arguments and dates
        c) make use of new block of data available from FTP at NOAA

"""

import os
import datetime
import urllib.request
import time
from bs4 import BeautifulSoup
import requests
import re

def getargs():

    import argparse
    import dateutil.parser as dateparse

    '''
    Retrieve the required date of data from command line arguments
    aas well as the output directory.

    In : None
    Out: Dates of data in datetime object format and data destination path
    '''

    parser = argparse.ArgumentParser(description=(
        'Retrieve data from NOAA in either grib or grib2 format.\n'+
        'Requires start and end dates for GFS data in YYYY-MM-DD format and'+
        ' output directory as input arguments.'
        ))

    parser.add_argument('startdate',
                        type=str,
                        help='[REQUIRED]\nFirst date for which data is required. Should be in format "YYYY-MM-DD"\n')

    parser.add_argument('enddate',
                        type=str,
                        help='Last date for which data is required. Should be in format "YYYY-MM-DD"\n')

    parser.add_argument('outdir',
                         type=str,
                         help='Output directory for grib files from GFS')

    args = parser.parse_args()

    # Validate the date

    startdate=dateparse.parse(args.startdate).date()

    if ( startdate.year != int(args.startdate[:4]) and startdate.month <= 12 and startdate.day <= 12 ):
        raise ArgumentsError("Start date was not in ISO 8601 format (YYYY-MM-DD), and date "+
        "parser cannot infer true date as both month and day are below 12 and "+
        "could be month-first or day-first format.\n"+
        "Please retry using the recommended ISO 8601 format (YYYY-MM-DD)")

    enddate=dateparse.parse(args.enddate).date()

    if ( enddate.year != int(args.enddate[:4]) and enddate.month <= 12 and enddate.day <= 12 ):
        raise ArgumentsError("End date was not in ISO 8601 format (YYYY-MM-DD), and date "+
        "parser cannot infer true date as both month and day are below 12 and "+
        "could be month-first or day-first format.\n"+
        "Please retry using the recommended ISO 8601 format (YYYY-MM-DD)")

    # Validate the output path, or generate it from default value

    path_out = args.outdir

    if not os.path.exists(path_out):
        print('Directory to write gfs files to'
              + ' does not exist\nAttempting to create:')
        try:
            os.makedirs(path_out)
        except:
            raise FatalError('Could not create directory '+ path_out +'\n')
        else:
            print ("Success!\n")

    if path_out and not os.path.isdir(path_out):
        raise FatalError(path_out + ' exists but is not a directory\n')

    return (startdate,enddate,path_out)


def create_filenames(d,variant):
    """
        creates filenames for givn date,
        from the runs at 0, 6, 12 and 18 UTC
        only t=0 and t=3 will be downloaded
    """
    ext = ".grb2"
    filelist = list()
    for t in ["0000", "0600", "1200", "1800"]:
        for t2 in ["000", "003"]:
            filelist.append("gfs_"+variant+"_"+d.strftime('%Y%m%d')+"_"+t+"_"+t2+ext)
    return filelist

def geturl(d,variant):
    if variant=="3":
        grid = "grid-003-1.0-degree"
    else:
        grid = "grid-004-0.5-degree"
    return "https://www.ncei.noaa.gov/data/global-forecast-system/access/"+grid+"/forecast/"+d.strftime('%Y%m')+"/"+d.strftime('%Y%m%d')+"/"

def getfilelist(d,variant):
    url = geturl(d, variant)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    alllinks = [x['href'] for x in soup.findAll('a')[5:]]
    return [x for x in alllinks if re.search("_00(0|3).grb2?$",x)]

def create_lastfilenames(d,variant):
    """
        creates filenames for final date,
        from the runs at 0, 6, 12 and 18 UTC
        only t=0 and t=3 will be downloaded
    """
    ext = ".grb2"
    filelist = list()
    for t in ["0000"]:
        for t2 in ["000", "003"]:
            filelist.append("gfs_"+variant+"_"+d.strftime('%Y%m%d')+"_"+t+"_"+t2+ext)
    return filelist

def getlastfilelist(d,variant):
    url = geturl(d, variant)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    alllinks = [x['href'] for x in soup.findAll('a')[5:]]
    return [x for x in alllinks if re.search("0000_00(0|3).grb2?$",x)]

def download_file(path, link, destination):
    """
        downloads files from path and saves to destination
    """

    download_url = path + link

    urllib.request.urlretrieve(download_url,os.path.join(destination,link))

    time.sleep(1)

def startFtpDate():
    """
        from this date 0.5 degree grid data exists on http
    """
    return datetime.date(2020,5,15)

def get_gfs(start_date,end_date,destination,variant="4"):
    """
        Retrieves gfs data between supplied dates
    """

    print ("Retrieving GFS data for selected dates:")

    # print input arguments
    print ("Start: {}\n".format(start_date.strftime("%Y-%m-%d")))
    print ("End:   {}\n\n".format(end_date.strftime("%Y-%m-%d")))

    if not (variant == "3" or variant == "4"):
        raise ArgumentsError ("Only GFS 3 or GFS 4 are valid.\n"+
               "Variant chosen was {}\n".format(variant))

    start_ftp_date = startFtpDate()

    # check if dates are in correct order
    if (start_date>end_date):
        print ("Your start date was after the end date, I will turn it around!\n\n")
        start_date, end_date = end_date, start_date

    if (start_date<start_ftp_date):
        raise ArgumentsError("The HTTPS-Server only provides data after the 15th May 2020, please choose another date!\n\n")

    print ("start downloading from "+start_date.strftime("%Y-%m-%d")+" to "+end_date.strftime("%Y-%m-%d"))

    # create date list
    date_list = [start_date + datetime.timedelta(days=x) for x in range(0, (end_date-start_date).days+1)]

    # iter through date_list and download

    for d in date_list:
        baseurl = geturl(d,variant)
        try:
            file_list_http = getfilelist(d, variant)
        except:
            print (d.strftime('%Y-%m-%d') + " Directory not found")
        try:
            file_list = create_filenames(d,variant)
        except:
            print ("Could not construct the file list")
        for f in file_list:
            if f in file_list_http:
                print ("  "+f+ " found, download as "+os.path.join(destination,f))
                download_file(baseurl, f, destination)
            else:
                print ("  "+ f + "not found")

    last = date_list[-1] + datetime.timedelta(days=1)
    baseurl = geturl(last,variant)
    try:
        file_list_http = getlastfilelist(last, variant)
    except:
        print (last.strftime('%Y-%m-%d') + " Directory not found")
    try:
        file_list = create_lastfilenames(last,variant)
    except:
        print ("Could not construct the file list")
    for f in file_list:
        if f in file_list_http:
            newfile = os.path.join(destination,f)
            if not os.path.exists(newfile):
                print ("  "+f+ " found, download as "+newfile)
                download_file(baseurl, f, destination)
            else:
                print ("  "+f+ " found on disk - already downloaded")
        else:
            print ("  "+ f + "not found")

    print ("")

def main():

    (start,end,out_dir) = getargs()
    get_gfs(start,end,out_dir)

if __name__=="__main__":
    main()
