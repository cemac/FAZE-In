# -*- coding: utf-8 -*-
"""
Created on Wed Feb 12 13:38:15 2020

@author: eelk
"""

###Code to read WRF file and write FlexPart RELEASES file ###
import numpy as np
import matplotlib.pyplot as plt
#import datetime
from netCDF4 import Dataset
#import os.path
import matplotlib as mpl
from mpl_toolkits.basemap import Basemap

for months in ['10']: 
    
    for days in range(1,32):
        day_mass2 = 0
        year = '2015'
        month = months #'09'
        day =  str(days) #'01'
        if days<10:
            day = '0'+day
        juldays = [range(1,32), range(32,32+28), range(60,60+31), range(91,91+30),range(121,121+31), range(152,152+30), range(182,182+31), range(213,213+31),range(244, 244+30), range(274, 274+31), range(305,305+30), range(335,335+31) ]
        julday = juldays[int(month)-1][int(day)-1]
        
        FINN_lat = []
        FINN_lon = []
        FINN_day = []
        FINN_PM25 = []
        FINN_CO = []
    
        with open('/nfs/a68/eelk/FINN/FINNv16_new/other_years/FINNv1.6_SEAS_scaledPEAT04_sm_'+year+'_09012018_MOZ4.txt','r') as f:
            read_it = f.read()
            all_lines= read_it.splitlines()
            
            for line in all_lines:   
#                print line
#                header =  line.split(',') 
#                stop                  
                line_data = line.split(',')
                if line_data[0] != 'DAY':
                    FINN_lat.append(float(line_data[3]))
                    FINN_lon.append(float(line_data[4]))
                    FINN_day.append(int(line_data[0]))
                    FINN_PM25.append(line_data[40])  
                    FINN_CO.append(line_data[7])             
        		     
               
        FINN_lat = np.array(FINN_lat)
        FINN_lon = np.array(FINN_lon)
        FINN_day = np.array(FINN_day)
        FINN_PM25 = np.array(FINN_PM25)
        FINN_CO = np.array(FINN_CO)
        FINN_day_ind = np.where(FINN_day == julday)      
        
        #num_fires = np.size(FINN_day_ind)
        #num_parts = 450000/num_fires
        #print num_parts, int(np.sum(FINN_PM25[FINN_day_ind].astype(float))*0.5)/num_fires
        
        day_mass = np.sum(FINN_PM25[FINN_day_ind].astype(float))        
        fact = day_mass/450000  
      
        with open('/nfs/a68/eelk/FlexPart/releases_files/releases_'+year+month+day+'_maxpartsfrac_5mHeight.txt','w') as f_new:
            f_new.write('&RELEASES_CTRL \n')
            f_new.write(' NSPEC      =           3, ! Total number of species \n')
            f_new.write(' SPECNUM_REL=      22, 24, 40, ! Species numbers in directory SPECIES  \n')
            f_new.write(' / \n')    
	    
            count =0
            for i in FINN_day_ind[0]:
                day_mass2 = day_mass2 + float(FINN_PM25[i])
                num_parts = float(FINN_PM25[i])/fact
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
                lon1 = FINN_lon[i]
                lon2 = FINN_lon[i]+0.01
                lat1 = FINN_lat[i]
                lat2 = FINN_lat[i]+0.01    
                height1 = 0
                height2 = 5
                heightkind = 1
                mass2 = FINN_PM25[i]
                mass1 = str(float(FINN_CO[i])*0.028)
                parts = int(num_parts) # int(FINN_PM25[i])/4  # 
                comment = '"Fire '+str(count)+'"'
                
                #print   float(FINN_PM25[i]), mass2               
                
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
		  

        #print days, day_mass, day_mass2