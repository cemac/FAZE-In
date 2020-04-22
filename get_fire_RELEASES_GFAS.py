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
#from mpl_toolkits.basemap import Basemap
from calendar import monthrange
from ecmwfapi import ECMWFDataServer
import os

server = ECMWFDataServer(url="https://api.ecmwf.int/v1",key="cd85b3670e9c314f617d7b36f50b032f",email="C.C.Symonds@leeds.ac.uk")

year = '2015'

latmin = -20
latmax = 20
lonmin = 90
lonmax = 150

processdir = os.getcwd()

GFAS_path = os.path.join(processdir,"GFAS")
RELEASES_dir = os.path.join(processdir,"RELEASES")

try:
    os.makedirs(GFAS_path)
except FileExistsError:
    # directory already exists
    pass

try:
    os.makedirs(RELEASES_dir)
except FileExistsError:
    # directory already exists
    pass

for months in ['02']:

    daynum = monthrange(int(year),int(months))[1]
    daystr = "{:02d}".format(daynum)

    daterange = '-'.join([year,months,'01'])+'/to/'+'-'.join([year,months,daystr])

    os.chdir(GFAS_path)

    GFAS_target = 'GFAS_2015_'+months+'_auto.nc'

    server.retrieve({
        "class": "mc",
        "dataset": "cams_gfas",
        "date": daterange,
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

    print ('Retrieved file '+GFAS_target+'.\n\nProcessing....')

    os.chdir(processdir)

    GFAS_file = Dataset(os.path.join(GFAS_path,GFAS_target))

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

    for days in range(1,daynum+1):
        day_mass2 = 0
        month = months #'09'

        day = "{:02d}".format(days)

        releasesfile=os.path.join(RELEASES_dir, 'releases_GFAS_'+year+month+day+'_maxpartsfrac_750mHeight.txt')

        print ('Processing releases file for day '+ day+' of '+str(daynum))

        day_mass = np.sum(PM25_kg_area[days-1,:,:])
        fact = day_mass/450000

        ###check GFAS and FINN are similar
        juldays = [range(1,32), range(32,32+28), range(60,60+31), range(91,91+30),range(121,121+31), range(152,152+30), range(182,182+31), range(213,213+31),range(244, 244+30), range(274, 274+31), range(305,305+30), range(335,335+31) ]
        julday = juldays[int(month)-1][int(day)-1]

        with open(releasesfile,'w') as f_new:

            f_new.write('&RELEASES_CTRL \n')
            f_new.write(' NSPEC      =           3, ! Total number of species \n')
            f_new.write(' SPECNUM_REL=      22, 24, 40, ! Species numbers in directory SPECIES  \n')
            f_new.write(' / \n')

            count =0
            for i in np.arange(0,400):   ### for all gridcells
                for j in np.arange(0,600):
                    if PM25_kg_area[days-1,i,j]>1:  ## if there are emissions from gridcell
                        ##day_mass2 = day_mass2 + float(FINN_PM25[i])
                        num_parts = PM25_kg_area[days-1,i,j]/fact
                        if num_parts < 5:
                            num_parts =5
                        if num_parts > 300:
                            num_parts = 300
                        #print num_parts
                        count = count +1
                        startday = year+month+day
                        starttime = '000000'
                        endday = year+month+day
                        endtime = '230000'
                        lon1 = lonmin+(j/10.)
                        lon2 = lonmin+(j/10.)+0.1
                        lat1 = latmin+(i/10.)
                        lat2 =   latmin+(i/10.)+0.1
                        height1 = 0
                        height2 = 750
                        heightkind = 1
                        mass2 = str(PM25_kg_area[days-1,i,j])
                        mass1 = str(CO_kg_area[days-1,i,j])
                        parts = int(num_parts) # int(FINN_PM25[i])/4  #
                        comment = '"Fire '+str(count)+'"'

                        ### Write to new file ###
                        f_new.write('&RELEASE                   ! For each release \n')
                        f_new.write(' IDATE1  =       '+ str(startday)+', ! Release start date, YYYYMMDD: YYYY=year, MM=month, DD=day \n' )
                        f_new.write(' ITIME1  =         '+ str(starttime)+ ', ! Release start time in UTC HHMISS: HH hours, MI=minutes, SS=seconds \n' )
                        f_new.write(' IDATE2  =       '+ str(endday)+ ', ! Release end date, same as IDATE1 \n' )
                        f_new.write(' ITIME2  =         '+ str(endtime)+ ', ! Release end time, same as ITIME1 \n' )
                        f_new.write(' LON1    =         '+ str(lon1)+ ', ! Left longitude of release box -180 < LON1 <180 \n' )
                        f_new.write(' LON2    =         '+ str(lon2)+ ', ! Right longitude of release box, same as LON1 \n' )
                        f_new.write(' LAT1    =          '+ str(lat1)+ ', ! Lower latitude of release box, -90 < LAT1 < 90 \n' )
                        f_new.write(' LAT2    =          '+ str(lat2)+ ', ! Upper latitude of release box same format as LAT1 \n' )
                        f_new.write(' Z1      =             '+ str(height1)+ ', ! Lower height of release box meters/hPa above reference level \n' )
                        f_new.write(' Z2      =             '+ str(height2)+ ', ! Upper height of release box meters/hPa above reference level \n' )
                        f_new.write(' ZKIND   =              '+ str(heightkind)+ ', ! Reference level 1=above ground, 2=above sea level, 3 for pressure in hPa \n' )
                        f_new.write(' MASS    =        '+ str(mass1)+ ', '+str(mass2) + ', '+str(mass2) + ', ! Total mass emitted, only relevant for fwd simulations \n' )
                        f_new.write(' PARTS   =         '+ str(parts)+ ', ! Total number of particles to be released \n' )
                        f_new.write(' COMMENT =   '+ str(comment)+ ', ! Comment, written in the outputfile \n' )
                        f_new.write(' / \n')
