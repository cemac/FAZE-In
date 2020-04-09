#!/usr/bin/env python
from ecmwfapi import ECMWFDataServer
server = ECMWFDataServer()
server.retrieve({
    "class": "mc",
    "dataset": "cams_gfas",
    "date": "2015-01-01/to/2015-01-31",
    "expver": "0001",
    "levtype": "sfc",
    "param": "81.210/87.210",
    "step": "0-24",
    "stream": "gfas",
    "time": "00:00:00",
    "type": "ga",
    "target": "GFAS_2015_01_auto.nc",
    "format": "netcdf",
})
