#!/bin/bash

#Replace with own conda path
. /nfs/earcemac/chmcsy/anaconda3/etc/profile.d/conda.sh

. /scratch/cemac/cemac.sh

module purge
module load user
module load gnu/4.8.1
module load flexpart

# Need a test here to see if a warm start is possible.
warm_strt=FALSE

# Dir paths
rundir=$PWD
scratchdir="/scratch/chmcsy/data"
flexdir="/nfs/earcemac/chmcsy/FlexPart"
testdir="/scratch/chmcsy/fwd_gfs_test"
out_dir="${flexdir}/test_cronflex"
flextractdir="/scratch/chmcsy/flex_extract/"

#Looks at day before yesterday to yesterday. 13:00 to account for any daylight savings effects.
day=$(TZ=":UTC" date -d '-16 days' +"%Y%m%d" )

#make directory on a68 for this to go in, and set as outpuexitt directory in pathnames
#out_dir=${flexdir}/daily/$( date -d $day +"%Y%m%d" )/

mkdir -p ${out_dir}

# Make pathnames file
cat > ${testdir}/pathnames <<-EOF
$testdir/options
$out_dir
$scratchdir
$scratchdir/AVAILABLE
EOF

if [ "$warm_strt" = TRUE ]; then
  datechunk=3 # 1 day, plus one on either side
  strtday=$day
  endday=$day
else
  datechunk=22 # 20 days, plus one on either side
  endday=$day
  strtday=$( date -d "$day -$datechunk days" +"%Y%m%d" )
fi

echo "Data to be retrieved between $strtday and $endday"

#Retrieve ERA5 data using flex_extract tool and make AVAILABLE file

conda activate flex_extract
#${flextractdir}/Source/Python/submit.py --controlfile CONTROL_EA5.0.5.6h --date_chunk $datechunk --start_date $strtday --end_date $endday --outputdir ${scratchdir}

echo "Conda env activated for flex_extract"

python $rundir/download_gfs.py ${strtday} ${endday} ${scratchdir}

cd ${scratchdir}
./make_available
cd ${testdir}

echo "AVAILABLE file made" 

#Retrieve GFAS data and make RELEASES file

conda activate fazein

echo "Fazein conda activated"

rm ${testdir}/options/RELEASES*
cp $rundir/get_fire_RELEASES_GFAS_daily.py ${testdir}/options/
cd ${testdir}/options
python get_fire_RELEASES_GFAS_daily.py $( date -d $strtday +'%F' ) --enddate $( date -d $endday +'%F' )
cd ..

echo "GFAS files retrieved"

# Add combo for releases

#update lines in COMMAND file to have start date of this day and end date of this day+run length
sed -i "9s/.*/ IBDATE=         ${strtday}, ! Start date of the simulation   ; YYYYMMDD: YYYY=year, MM=month, DD=day /" ${testdir}/options/COMMAND
sed -i "11s/.*/ IEDATE=         ${endday},! End date of the simulation     ; same format as IBDATE  /" ${testdir}/options/COMMAND
sed -i '25s/.*/ IPIN=                  0, ! Warm start from particle dump (needs previous partposit_end file); [0]no 1]yes  /' ${testdir}/options/COMMAND

#if its not the first day then want to use a warm start
#remove partposit_end file and replace it with partposit_file from run before
#update line in COMMAND file to have a warm start
if [ "$warm_strt" == TRUE ]; then
  echo 'warm start'
  rm ${out_dir}/partposit_end
  cp "${out_dir}/partposit_$( date -d $day +'%Y%m%d%H%M%S' )" "${out_dir}/partposit_end"
  sed -i '25s/.*/ IPIN=                  1, ! Warm start from particle dump (needs previous partposit_end file); [0]no 1]yes  /' ${testdir}/options/COMMAND
  rm ${out_dir}/partposit_${start_year}*
fi

#run flexpart for this day
FLEXPART

#plot the output files
python plotting_flexpart_output.py ${strtday} ${out_dir}

echo "Plots created"

#put partposit files and header in folder
mkdir "${out_dir}/${day}"
for file in ${out_dir}/partposit_*000000; do
  cp $file "${out_dir}/${day}/"
done
cp "${out_dir}/header" "${out_dir}/${day}/"
