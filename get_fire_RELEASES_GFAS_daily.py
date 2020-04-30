# -*- coding: utf-8 -*-
"""
Created on Wed Apr  1 09:46:52 2020

@author: eelk
"""

###Code to read WRF file and write FlexPart RELEASES file ###
import numpy as np
import matplotlib.pyplot as plt
from netCDF4 import Dataset
import matplotlib as mpl
from calendar import monthrange
from ecmwfapi import ECMWFDataServer
from os import path, getcwd, makedirs, chdir
import argparse
import dateutil.parser as dateparse
from sys import stderr, exit


latmin = -20
latmax = 20
lonmin = 90
lonmax = 150


class ArgumentsError(Exception):
    '''
    Exception raised when there is an error detected in the argument list.
    '''
    def __init__(self, msg):
        stderr.write('[FATAL ERROR] : %s' % msg )
        exit(9)


class FatalError(Exception):
    '''
    Exception raised when there is an unrecoverable error encountered.
    '''
    def __init__(self, msg):
        stderr.write('[FATAL ERROR] : %s' % msg )
        exit(9)


class FileError(Exception):
    '''
    Exception raised when contents of files are not as expected
    '''
    def __init__(self,msg):
        stderr.write('[FILE ERROR] : %s' % msg )
        exit(9)


def next_path(path_pattern):
    """
    Finds the next free path in an sequentially named list of files

    e.g. path_pattern = 'file-%s.txt':

    file-1.txt
    file-2.txt
    file-3.txt

    In: path_pattern;
    example: 'file-%s.txt'
    Out: Path with next available sequentially numbered entry;
    example:
    file-1.txt
    file-2.txt
    file-3.txt
    """
    i = 1

    # First do an exponential search
    while path.exists(path_pattern % i):
        i = i * 2

    # Result lies somewhere in the interval (i/2..i]
    # We call this interval (a..b] and narrow it down until a + 1 = b
    a, b = (i // 2, i)
    while a + 1 < b:
        c = (a + b) // 2 # interval midpoint
        a, b = (c, b) if path.exists(path_pattern % c) else (a, c)

    return path_pattern % b


def getargs():
    '''
    Retrieve the required date of data from command line arguments
    and convert it to FLEXPART releases format.

    In : None
    Out: Date of data in "YYYY-MM-DD" format
    '''

    parser = argparse.ArgumentParser(description=(
        'Retrieve data from ECMWF and convert to RELEASES text format.\n'+
        'Requires date for GFAS data in YYYY-MM-DD format as input argument.'
        ))

    parser.add_argument('date', #'-i',
                        type=str,
                        help='Date for which data is required. Should be in format "YYYY-MM-DD"')


    args = parser.parse_args()

    # Validate the date

    date=dateparse.parse(args.date).date()

    if ( date.year != args.date[:4] and date.month <= 12 and date.day <= 12 ):
        raise ArgumentsError("Date was not in ISO 8601 format (YYYY-MM-DD), and date "+
        "parser cannot infer true date as both month and day are below 12 and "+
        "could be month-first or day-first format.\n"+
        "Please retry using the recommended ISO 8601 format (YYYY-MM-DD)")
        return "0000-00-00"
    else:
        return date.strftime("%Y-%m-%d")


def retrieve_GFAS(processdir, gfasdate):
    '''
    Retrieve GFAS fire data from ECMWF using ECMWF api

    In : processdir - working directory path
         gfasdate   - date for data to be retrieved

    Out : Path to downloaded GFAS data file (in netCDF format)
    '''

    server = ECMWFDataServer(url="https://api.ecmwf.int/v1",key="cd85b3670e9c314f617d7b36f50b032f",email="C.C.Symonds@leeds.ac.uk")

    GFAS_path = path.join(processdir,"GFAS")

    try:
        makedirs(GFAS_path)
    except FileExistsError:
        # directory already exists
        pass

    chdir(GFAS_path)

    GFAS_target = 'GFAS_2015_'+gfasdate+'_auto.nc'

    server.retrieve({
        "class": "mc",
        "dataset": "cams_gfas",
        "date": gfasdate,
        "expver": "0001",
        "levtype": "sfc",
        "param": "81.210/87.210",
        "step": "0-24",
        "stream": "gfas",
        "time": "00:00:00",
        "type": "ga",
        "target": GFAS_target,
        "format": "netcdf",
    })

    print ('Retrieved file '+GFAS_target+'.\n')

    return path.join(GFAS_path,GFAS_target)

def process_gfas(gfaspath, processdir, gfasdate):
    '''
    Process GFAS netCDF file into a FlexPart RELEASES file, listing
    each emission-containing gridpoint separately for use in FlexPart
    simulation

    In: gfaspath   - path to GFAS netCDF file
        processdir - working directory
        gfasdate   - date of GFAS data (only single day)

    Out: Status code
    '''

    chdir(processdir)

    GFAS_file = Dataset(gfaspath)

    lat = GFAS_file.variables['latitude'][:]    #90 to -90
    lon = GFAS_file.variables['longitude'][:]   # 0 to 360
    PM25 = GFAS_file.variables['pm2p5fire'][:]    ##kg/m2/s
    CO = GFAS_file.variables['cofire'][:]     ##kg/m2/s

    lat = np.flip(lat, axis = 0)     #-90 to 90
    PM25 = np.flip(PM25,axis = 1 )
    CO = np.flip(CO,axis = 1 )

    PM25_kg = PM25*(110567*0.1)*(110567*0.1)*(60*60*24)    ### kg/m2/s * m2 in gridcell * s in day
    CO_kg = CO*(110567*0.1)*(110567*0.1)*(60*60*24)

    lats_area =  np.array(np.where((lat>latmin) & (lat<latmax))[0])
    lons_area =  np.array(np.where((lon>lonmin) & (lon<lonmax))[0])
    PM25_kg_area = PM25_kg[:,lats_area,:][:,:, lons_area]
    CO_kg_area = CO_kg[:,lats_area, :][:,:,lons_area]

    RELEASES_dir = path.join(processdir,"RELEASES")

    try:
        makedirs(RELEASES_dir)
    except FileExistsError:
        # directory already exists
        pass

    fname = 'releases_GFAS_'+gfasdate.replace('-','')+'_maxpartsfrac_750mHeight.txt'

    releasesfile=path.join(RELEASES_dir, fname)

    if path.exists(releasesfile):
        releasesfile = next_path(path.join(RELEASES_dir, fname[:-4]+'-%s.txt'))

    print ('Processing releases file for  '+ gfasdate)

    day_mass = np.sum(PM25_kg_area[0,:,:])
    fact = day_mass/450000

    with open(releasesfile,'w') as f_new:

        f_new.write('&RELEASES_CTRL \n')
        f_new.write(' NSPEC      =           3, ! Total number of species \n')
        f_new.write(' SPECNUM_REL=  22, 24, 40, ! Species numbers in directory SPECIES  \n')
        f_new.write(' / \n')

        count =0
        for i in np.arange(0,400):   ### for all gridcells
            for j in np.arange(0,600):
                if PM25_kg_area[0,i,j]>1:  ## if there are emissions from gridcell
                    num_parts = PM25_kg_area[0,i,j]/fact
                    if num_parts < 5:
                        num_parts = 5
                    if num_parts > 300:
                        num_parts = 300
                    count = count +1
                    startday = gfasdate.replace('-','')
                    starttime = '000000'
                    endday = gfasdate.replace('-','')
                    endtime = '230000'
                    lon1 = lonmin+(j/10.)
                    lon2 = lonmin+(j/10.)+0.1
                    lat1 = latmin+(i/10.)
                    lat2 = latmin+(i/10.)+0.1
                    height1 = 0
                    height2 = 750
                    heightkind = 1
                    mass1 = CO_kg_area[0,i,j]
                    mass2 = PM25_kg_area[0,i,j]
                    parts = int(num_parts)
                    comment = '"Fire {:05d}"'.format(count)

                    ### Write to new file ###
                    f_new.write('&RELEASE                   ! For each release \n')
                    f_new.write(' IDATE1  = {:>14s}, ! Release start date, YYYYMMDD: YYYY=year, MM=month, DD=day \n'.format(startday))
                    f_new.write(' ITIME1  = {:>14s}, ! Release start time in UTC HHMISS: HH hours, MI=minutes, SS=seconds \n'.format(starttime))
                    f_new.write(' IDATE2  = {:>14s}, ! Release end date, same as IDATE1 \n'.format(endday) )
                    f_new.write(' ITIME2  = {:>14s}, ! Release end time, same as ITIME1 \n'.format(endtime) )
                    f_new.write(' LON1    = {:>14.2f}, ! Left longitude of release box -180 < LON1 <180 \n'.format(lon1) )
                    f_new.write(' LON2    = {:>14.2f}, ! Right longitude of release box, same as LON1 \n'.format(lon2) )
                    f_new.write(' LAT1    = {:>14.2f}, ! Lower latitude of release box, -90 < LAT1 < 90 \n'.format(lat1) )
                    f_new.write(' LAT2    = {:>14.2f}, ! Upper latitude of release box same format as LAT1 \n'.format(lat2) )
                    f_new.write(' Z1      = {:>14d}, ! Lower height of release box meters/hPa above reference level \n'.format(height1) )
                    f_new.write(' Z2      = {:>14d}, ! Upper height of release box meters/hPa above reference level \n'.format(height2) )
                    f_new.write(' ZKIND   = {:>14d}, ! Reference level 1=above ground, 2=above sea level, 3 for pressure in hPa \n'.format(heightkind) )
                    f_new.write(' MASS    =   {0:.12f}, {1:.12f}, {1:.12f}, ! Total mass emitted, only relevant for fwd simulations \n'.format(mass1, mass2) )
                    f_new.write(' PARTS   = {:>14d}, ! Total number of particles to be released \n'.format(parts) )
                    f_new.write(' COMMENT = {:>14s}, ! Comment, written in the outputfile \n'.format(comment) )
                    f_new.write(' / \n')

    return 0


def main():

    processdir = getcwd()

    gfasdate = getargs()

    gfaspath = retrieve_GFAS(processdir, gfasdate)

    stat = process_gfas(gfaspath, processdir, gfasdate)

    if stat == 0:
        print('RELEASES file written successfully')
    else:
        print('RELEASES file not written successfully')


if __name__ == "__main__":

    main()