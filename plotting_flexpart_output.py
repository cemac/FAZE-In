"""
Created on Mon Feb 17 10:59:06 2020

@author: eelk
"""


from netCDF4 import Dataset
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from mpl_toolkits.basemap import Basemap


filename = '_juloct_maxpartfrac_partnumfix_ageon_multiheightoutput_750mheight_ecmwf'
c = 'green'
lab = 'ECMWF & emissions up to 750m'



av_PM25_all_days = []
av_CO_all_days = []
av_trace_all_days = []
av_PM25_area = np.ones((400,400))*np.nan
year = '2015'
days_in_month = [31,28,31,30,31,30,31,31,30,31,30,31]
monthcount = 0
for month in ['07' ,'08','09','10']:
    print month
    daycount=0
    for day in range(1,days_in_month[int(month)-1]+1):
        day = str(day)
        if int(day)<10:
            day = '0'+day 
        date = year+month+day
        #print date
        flex_file = Dataset('/nfs/see-fs-01_users/eelk/a68/FlexPart/test'+filename+'/grid_conc_'+date+'000000.nc','r',format="NETCDF4")
        lat = flex_file.variables['latitude'][:]
        lon = flex_file.variables['longitude'][:]
        time = flex_file.variables['time'][:]  ##in seconds from start date
        height = flex_file.variables['height'][:]
        trace = flex_file.variables['spec002_mr'][0,0,:,:,:,:]/1000  #ug/m3
        CO = flex_file.variables['spec001_mr'][0,0,:,:,:,:]/1000 #ug/m3
        PM25 = flex_file.variables['spec003_mr'][0,0,:,:,:,:]/1000 #ug/m3
  
  
        ##average up to 20m###   
        for l in range(0,2):
            if l ==0:
                h = height[l]   
            else:
                h = height[l]- height[l-1]
            PM25[:,l,:,:] = PM25[:,l,:,:]*h  #multiply by meters in each height level to get it in ug/m2
            CO[:,l,:,:] = CO[:,l,:,:]*h
            trace[:,l,:,:] = trace[:,l,:,:]*h
        PM25 = np.sum(PM25[:,0:l+1,:,:],axis = 1)/height[l]  ##add up heights up to 20m, then divide by 20 to get it back in ug/m3
        CO = np.sum(CO[:,0:l+1,:,:],axis = 1)/height[l] 


        i = 0
        for i in range(0,8):
            #print (daycount*8)+i, str(monthcount+(daycount*8)+i)
            ###Map plot of each 3 hour timestep - labelled as time from start date ###
            ###To make video from plots use:  ffmpeg -r 2 -f image2 -s 1920x1080 -i PM25_map_%d.png -vcodec libx264 -crf 25  -pix_fmt yuv420p PM25_2015.mp4             
            ax = plt.figure(figsize = (14,7))        
            plt.rcParams.update({'font.size': 13})
            vals = np.array([25,50,100,150,200,250,300,350,400,450,500,600,700,800,900,1000,1500,2000,2500,3000,3500,4000,4500,5000,6000,7000,8000,10000,15000,20000])
            vals = vals/200          
            cmap = plt.get_cmap('RdYlBu_r', 100)
            newcolors = cmap(np.linspace(0, 1, 100))    
            newcmp = mpl.colors.ListedColormap(newcolors)
            norm = mpl.colors.BoundaryNorm(vals,newcmp.N)           
            m = Basemap(projection='merc',llcrnrlon=88.,llcrnrlat=-17.,urcrnrlon=132.,urcrnrlat=27.,resolution='i') 
            m.drawcoastlines(linewidth=2)
            m.drawmapboundary(linewidth=0.5)
            #m.drawparallels(np.arange(-10,11,5),labels=[1,0,0,0], linewidth=0.0)
            xx, yy = np.meshgrid(lon, lat )
            x , y = m(xx,yy)            
            m.pcolormesh(x,y,PM25[i,:,:],shading='flat',cmap=newcmp, norm = norm)
            plt.title('PM2.5 20m (ug/m3)')
            plt.text(1,1,year+' '+month+' '+day+' 00 +'+str(time[i]/(60*60))+' hours')
            cbar_ax = plt.axes([0.02, 0.05, 0.95, 0.03])
            plt.colorbar(cax=cbar_ax, orientation='horizontal', extend = 'both') #, label = 'ug/m3')           
            plt.savefig('/nfs/see-fs-01_users/eelk/a68/FlexPart/test'+filename+'/PM25_above20_gfs_ecmwf_map_'+str(monthcount+(daycount*8)+i)+'.png')
            plt.close()    



        PM25_av = np.mean(PM25[:,:,:],axis = (1,2))  ##ug/m3
        CO_av = np.mean(CO[:,:,:],axis = (1,2))  ##ug/m3
        trace_av = np.mean(trace[:,:,:],axis = (1,2))  ##ug/m3
        
        av_PM25_all_days = np.append(av_PM25_all_days, PM25_av)
        av_trace_all_days = np.append(av_trace_all_days, trace_av)
        
        av_PM25_area = np.dstack((av_PM25_area,np.nanmean(PM25,axis=0)) )      
        
        
        daycount=daycount+1
        #print daycount
    monthcount = monthcount+(daycount*8)
    #print monthcount


fig =plt.figure(num=14, figsize=(12,5))
plt.rcParams.update({'font.size': 10})
plt.plot(av_PM25_all_days, c, label = lab)    
plt.xticks((np.arange(0,123,4)*8), np.concatenate((np.concatenate((np.arange(1,32).astype(str),np.arange(1,32).astype(str))), np.concatenate((np.arange(1,31).astype(str),np.arange(1,32).astype(str)))))[0:123:4] )
plt.ylabel('Average PM2.5 (ug/m3) ')
plt.xlabel('Day')  
legend = plt.legend(loc=(0.1,0.6))    
plt.savefig('/nfs/see-fs-01_users/eelk/a68/FlexPart/PM2.5_all_runs.png')   



###Map of average for entire run ###
ax = plt.figure(figsize = (6,8))
plt.rcParams.update({'font.size': 15})
m = Basemap(projection='merc',llcrnrlon=88.,llcrnrlat=-17.,urcrnrlon=132.,urcrnrlat=27.,resolution='i') 
m.drawcoastlines(linewidth=2)
m.drawmapboundary(linewidth=0.5)
xx, yy = np.meshgrid(lon, lat )
x , y = m(xx,yy)
vals = np.arange(0,100,5)    
cmap = plt.get_cmap('RdYlBu_r', 100)
#newcolors = cmap(np.linspace(0, 1, 100))    
#newcmp = mpl.colors.ListedColormaplormap(newcolors)
norm = mpl.colors.BoundaryNorm(vals,cmap.N)
m.pcolormesh(x,y,np.mean(av_PM25_area[:,:,1:],axis = 2),shading='flat',cmap=cmap, norm = norm)
plt.title('PM2.5')
plt.colorbar(orientation='horizontal', extend = 'both', label = 'ug/m3')
plt.savefig('/nfs/see-fs-01_users/eelk/a68/FlexPart/test'+filename+'/PM25_map_JulOct.png')


