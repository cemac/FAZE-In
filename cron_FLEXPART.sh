# @Author: Christopher Symonds
# @Date:   2020-11-18T10:07:25+00:00
# @Email:  C.C.Symonds@leeds.ac.uk
# @Project: FAZE-In
# @Filename: cron_FLEXPART.sh
# @Last modified by:   Christopher Symonds
# @Last modified time: 2020-11-18T13:00:14+00:00
# @License: MIT
# @Copyright: University of Leeds



#!/bin/bash

#Replace with own conda path
. /nfs/earcemac/chmcsy/anaconda3/etc/profile.d/conda.sh

. /scratch/cemac/cemac.sh

module purge
module load user
module load gnu/4.8.1
module load flexpart

# Dir paths
rundir=$PWD
scratchdir="/scratch/chmcsy/data"
flexdir="/scratch/chmcsy/FlexPart"
testdir="/scratch/chmcsy/fwd_gfs_test"
out_dir_base="${flexdir}/cronflex"
flextractdir="/scratch/chmcsy/flex_extract/"
spritedir="/nfs/see-fs-02_users/chmcsy/Git_Repos/Faze-In_App/Applications/static/sprites"

#Looks at day before yesterday to yesterday. UTC to account for any daylight savings effects.
day=$(TZ=":UTC" date -d '-3 days' +"%Y%m%d" )

#make directory on a68 for this to go in, and set as output directory in pathnames

out_dir=${out_dir_base}/daily

mkdir -p ${out_dir}

if [ -f "${out_dir}/partposit_$( date -d $day +'%Y%m%d%H%M%S' )" ];
  warm_strt = TRUE
else
  warm_strt = FALSE
fi

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
  datechunk=27 # 20 days, plus five days of output data and one day either side
  endday=$day
  strtday=$( date -d "$day -$datechunk days" +"%Y%m%d" )
fi

echo "Data to be retrieved between $strtday and $endday"

#Retrieve ERA5 data using flex_extract tool and make AVAILABLE file

conda activate flex_extract
#${flextractdir}/Source/Python/submit.py --controlfile CONTROL_EA5.0.5.6h --date_chunk $datechunk --start_date $strtday --end_date $endday --outputdir ${scratchdir}

echo "Conda env activated for flex_extract"

python $rundir/download_gfs.py ${strtday} ${endday} ${scratchdir}

cp make_available ${scratchdir}
cd ${scratchdir}
./make_available
cd ${testdir}

echo "AVAILABLE file made"

#Retrieve GFAS data and make RELEASES file

conda activate fazein

echo "Fazein conda activated"

rm ${testdir}/options/RELEASES*
cp -f $rundir/get_fire_RELEASES_GFAS_daily.py ${testdir}
cd ${testdir}
python get_fire_RELEASES_GFAS_daily.py $( date -d $strtday +'%F' ) --enddate $( date -d $endday +'%F' )

echo "GFAS files retrieved"

# Add combo for releases

#update lines in COMMAND file to have start date of this day and end date of this day+run length
sed -i "9s/.*/ IBDATE=         ${strtday}, ! Start date of the simulation   ; YYYYMMDD: YYYY=year, MM=month, DD=day /" ${testdir}/options/COMMAND
sed -i "11s/.*/ IEDATE=         $( date -d "${endday} +1 days" +"%Y%m%d" ),! End date of the simulation     ; same format as IBDATE  /" ${testdir}/options/COMMAND
sed -i '25s/.*/ IPIN=                  0, ! Warm start from particle dump (needs previous partposit_end file); [0]no 1]yes  /' ${testdir}/options/COMMAND

#if its not the first day then want to use a warm start
#remove partposit_end file and replace it with partposit_file from run before
#update line in COMMAND file to have a warm start
if [ "$warm_strt" == TRUE ]; then
  #if [ -d ${out_dir_base}/backup_data ]; then rm -rf ${out_dir_base}/backup_data; fi
  #cp -r ${out_dir} ${out_dir_base}/backup_data
  echo 'warm start'
  if [ -f ${out_dir}/partposit_end ]; then rm ${out_dir}/partposit_end; fi
  cp -f "${out_dir}/partposit_$( date -d $day +'%Y%m%d%H%M%S' )" "${out_dir}/partposit_end"
  sed -i '25s/.*/ IPIN=                  1, ! Warm start from particle dump (needs previous partposit_end file); [0]no 1]yes  /' ${testdir}/options/COMMAND
  start_year=$( date -d $day +'%Y' )
  rm ${out_dir}/partposit_$( date -d $day +'%Y%m%d' )*
fi

#if [ -f ${flexdir}/FlexOut.out ]; then rm ${flexdir}/FlexOut.out; fi
#run flexpart for this day
FLEXPART #> ${flexdir}/FlexOut.out

#plot the output files
conda activate flex_extract

python ${rundir}/plot_flexpart.py ${strtday} ${out_dir} -v BC

echo "Plots created"

cd ${out_dir}
spritedays=5
mkdir -p ${out_dir}/spritebuild
plotday=$( date -d "${day} +1 days" +"%Y%m%d" )
cp 20m-${plotday}* spritebuild
for i in `seq 0 $spritedays`; do
  plotday=$( date -d "${day} -${i} days" +"%Y%m%d" )
  cp 20m-${plotday}* spritebuild
done

cd ${out_dir}/spritebuild
rm 20m-${plotday}0000.png

montage -background transparent -tile 8x -geometry 675x600+0+0 *.png ${spritedir}/spritesheet.png
cd ..
rm -rf spritebuild

#put partposit files and header in folder
mkdir -p "${out_dir}/${day}"
for file in ${out_dir}/partposit_*000000; do
  cp $file "${out_dir}/${day}/"
done
cp "${out_dir}/header" "${out_dir}/${day}/"
