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

def getargs():
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

    parser.add_argumment('outdir',
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

    path_out = args.output

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

    if variant == "3":
        ext = ".grb"
    else:
        ext = ".grb2"

    filelist = list()
    for t in ["0000", "0600", "1200", "1800"]:
        for t2 in ["000", "003"]:
            filelist.append("gfsanl_"+variant+"_"+d.strftime('%Y%m%d')+"_"+t+"_"+t2+ext)
    return filelist

def download_file(path, filename, destination):
    """
        downloads files from path and saves to destination
    """
    import os
    command = "wget -q -O "+destination+"/"+filename+" ftp://nomads.ncdc.noaa.gov/"+path+"/"+filename
    os.system(command)

def startFtpDate():
    """
        from this date 0.5 degree grid data exists on ftp
    """
    return datetime.date(2020,05,15)

def get_gfs(start_date,end_date,destination,variant="4"):
    """
        Retrieves gfs data between supplied dates
    """

    import sys
    from ftplib import FTP
    import datetime

    print ("Retrieving GFS data for selected dates:")

    # print input arguments
    print ("Start: {}\n".format(start_date.strftime("%Y-%m-%d")))
    print ("End:   {}\n\n".format(end_date.strftime("%Y-%m-%d")))

    check_path(destination)

    if not (variant == "3" or variant == "4"):
        print ("Only GFS 3 or GFS 4 are valid.\n"+
               "Variant chosen was {}\n".format(variant))
        sys.exit()

    start_ftp_date = startFtpDate()

    # check if dates are in correct order
    if (start_date>end_date):
        print ("Your start date was after the end date, I will turn it around!\n\n")
        start_date, end_date = end_date, start_date

    if (start_date<start_ftp_date):
        raise ArgumentsError("The FTP-Server only provides data after the 15th May 2020, please choose another date!\n\n")

    print ("start downloading from "+start_date.strftime("%Y-%m-%d")+" to "+end_date.strftime("%Y-%m-%d"))

    # create date list
    date_list = [start_date + datetime.timedelta(days=x) for x in range(0, (end_date-start_date).days+1)]

    # connect to ftp
    ftp = FTP('nomads.ncdc.noaa.gov')
    ftp.login()

    # iter through date_list and download
    for d in date_list:
        path = "GFS/analysis_only/"+d.strftime('%Y%m')+"/"+d.strftime('%Y%m%d')+"/"
        try:
            ftp.cwd(path)
            print ("{} found".format(path))
            file_list_ftp = ftp.nlst()
            file_list = create_filenames(d,variant)
            for f in file_list:
                if f in file_list_ftp:
                    print ("  "+f+ " found, download as "+destination+f)
                    download_file(path, f, destination)
                else:
                    print ("  "+ f + "not found")
            ftp.cwd("../../../../")
        except:
            print (d.strftime('%Y-%m-%d') + " Directory not found")

    ftp.quit()
    print ("")

def main():

    (start,end,out_dir) = getargs()
    get_gfs(start,end,out_dir)

if __name__=="__main__":
    main()
