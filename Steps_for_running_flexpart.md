# <ins>**Steps for running FLEXPART:**</ins> #

* Each run needs to be a warm start, reading in the particles from the end of the previous run, or it needs to have ~30 days warm up before the day you are interested in.
* For looking at NRT concentrations, FLEXPART will be run using the latest available fire emissions, probably for only one or two days, so a 30 day warm up may be impractical.
* Ideally FLEXPART would be run every day, using the particle position file from the day before so that no warm up is needed.


For each run:

1. **Get meteorology data**\
 Download GFS data for the period the run is covering (1day). If GFS is not available use FNL (all files need to be the same for each run).

1. **Make AVAILABLE file with all met files**
1. **Create RELEASES file from fire emissions for each day (or multiple days).**\
 I have Python code which does this for FINN emissions which is what I am currently using, but this will be slightly different for GFAS. FINN emissions are a text file with a line for each fire, GFAS files are gridded emissions, so the code will have to be changed.\
 The releases file specifies the latitude, longitude and time of each release (in this case fires), and the number of particles released. It also contains the mass of each species emitted. The behaviour of each species (deposition, scavenging rate etc.) is given in the SPECIES files. A SPECIES file is needed for each species specified in the RELEASES file (currently the AIRTRACER, PM2.5 and CO).
4.  **Update COMMAND file with the setup wanted e.g. to use a warm start.**\
 The COMMAND file contains most of the set up options for the model, and the date to run to and from. Between runs the only things which should change are these dates.
5. **Get particle position file for warm start**\
 If using a warm start need to get the file from the end of the previous run to start this run with. This file is outputted every three hours as ‘partposit_DATE&TIME’, but the file to be read in at the start of a run is ‘partposit_end’, so the correct partposit file needs to be renamed.
6. **Run Flexpart**
