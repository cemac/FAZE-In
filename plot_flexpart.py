#!/usr/bin/env python

# e.g.:
#   ./plot_flexpart.py file.nc NO2

import matplotlib
matplotlib.use('Agg')

import datetime
import sys

from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import iris
import iris.quickplot as qplt
import matplotlib.pyplot as plt
import numpy as np

iris.FUTURE.netcdf_promote = True

if len(sys.argv) != 3:
    sys.stderr.write('usage: {0} NC_FILE VAR_NAME\n'.format(sys.argv[0]))
    sys.exit()

NC_FILE = sys.argv[1]
VAR_NAME = sys.argv[2]

constrain_at = iris.Constraint(name=VAR_NAME)
cube = iris.load_cube(NC_FILE, constrain_at)

cube_lat = cube.coord('grid_latitude')
cube_lon = cube.coord('grid_longitude')

lats = cube_lat.points
lons = cube_lon.points

lat_min = int(np.ceil(lats.min()))
lat_max = int(np.floor(lats.max()))
lon_min = int(np.ceil(lons.min()))
lon_max = int(np.floor(lons.max()))

xx, yy = np.meshgrid(lons, lats)

cube_height = cube.coord('height')
heights = cube_height.points

minmax_data = cube.data
minmax_data[minmax_data == 0] = np.nan
data_min = np.nanmin(minmax_data)
data_max = np.nanmax(minmax_data)
data_range = data_max - data_min

col_bound_min = data_min
#col_bound_max = data_min + (0.05 * data_range)
col_bound_max = 0.01
col_bound_range = col_bound_max - col_bound_min
col_bounds = np.arange(col_bound_min, col_bound_max, col_bound_range / 15)

for i in enumerate(heights):

  index = i[0]
  height = i[1]
  i_height = int(round(height))
  h_cube = cube[0, 0, :, index, :, :]

  for t in range(h_cube.shape[0]):

    t_cube = h_cube[t]

    t_data = t_cube.data
    t_data[t_data == 0] = np.nan

    if np.where(np.isnan(t_data) == False)[0].shape[0] < 5:
        continue

    cube_time = t_cube.coord('time')
    cube_datetime = cube_time.units.num2date(cube_time.points)[0]
    filename_time = cube_datetime.strftime('%Y%m%d%H%M')
    title_time = cube_datetime.strftime('%Y-%m-%d %H:%M')

    plot_ax = plt.axes(projection=ccrs.PlateCarree())

    plot_ax.set_ylim(bottom=lat_min, top=lat_max)
    plot_ax.set_xlim(left=lon_min, right=lon_max)
    plot_ax.set_xticks(range(lon_min + 4, lon_max, 10), crs=ccrs.PlateCarree())
    plot_ax.set_yticks(range(lat_min + 4, lat_max, 10), crs=ccrs.PlateCarree())
    lon_formatter = LongitudeFormatter(number_format='.1f', degree_symbol='')
    lat_formatter = LatitudeFormatter(number_format='.1f', degree_symbol='')
    plot_ax.xaxis.set_major_formatter(lon_formatter)
    plot_ax.yaxis.set_major_formatter(lat_formatter)

    plot_ax.add_feature(cfeature.LAND)
    plot_ax.add_feature(cfeature.OCEAN)
    plot_ax.add_feature(cfeature.COASTLINE)

    plt.contourf(xx, yy, t_data, col_bounds,
                 cmap=plt.cm.jet,
                 vmin=data_min, vmax=data_max, zorder=10, extend='both')

    plt.clim(col_bound_min, col_bound_max)
    plt.colorbar()

    title = '{:,}m {}'.format(i_height, title_time)
    plot_ax.set_title(title)

    filename = '{}m-{}.png'.format(i_height, filename_time)
    plt.savefig(filename, dpi=300, format='png')

    plt.close('all')
