#!/bin/bash

#make directory on a68 for this to go in, and set as output directory in pathnames
out_dir=/nfs/a68/eelk/FlexPart/test_juloct_maxpartfrac_partnumfix_ageon_5moutput_5mheight_onerun
mkdir -p "${out_dir}/"
sed -i "2s@.*@${out_dir}/@" /scratch/eelk/fwd_gfs_test/pathnames

#days to start and end and run length are inputted. Currently start and end day in same month.
start_day=1
start_month=07
start_year=2015
end_day=01
end_month=07
run_length=123

start_day_j=$(date --date="${start_year}-${start_month}-${start_day}" +"%j")
end_day_j=$(date --date="${start_year}-${end_month}-${end_day}" +"%j")


for (( i=$start_day_j; i<=$end_day_j; i++)); do #loop through all days as day of year
  run_day_j=$i   										 #day of year  start day of run
  run_end_day_j=$(($run_day_j+$run_length))						 #day of year  end day of run
  run_day=$(date -d "$((${run_day_j}-1)) days ${start_year}-01-01" +"%d")			#date day start of run
  run_end_day=$(date -d "$((${run_end_day_j}-1)) days ${start_year}-01-01" +"%d")		#date day end of run
  run_month=$(date -d "$((${run_day_j}-1)) days ${start_year}-01-01" +"%m")		#date month start of run
  run_end_month=$(date -d "$((${run_end_day_j}-1)) days ${start_year}-01-01" +"%m")	#date month end of run
  echo  $start_year, $(printf ${run_month}), $(printf ${run_day}) ,  $(printf ${run_end_day})   #$(printf %02d ${run_day})
  echo $run_day_j, $run_end_day_j, $end_day_j


  #copy over met files and make available file. If there aren't 8 files a day for GFS4, then use GFS3, then use fnl
  rm /scratch/eelk/data/gfs*
  rm /scratch/eelk/data/fnl*
  for (( j=$run_day_j; j<=$run_end_day_j; j++)) do #loop through run days
    j_day=$(date -d "$((${j}-1)) days ${start_year}-01-01" +"%d")
    j_month=$(date -d "$((${j}-1)) days ${start_year}-01-01" +"%m")
    for file in /nfs/a68/eelk/FlexPart/gfs_data/gfsanl_4_${start_year}$(printf ${j_month})$(printf ${j_day})*;  do
      cp "$file" "/scratch/eelk/data/"
    done
  done
  check_size=$(find /scratch/eelk/data/gfsanl_4* -size -40M| wc -l )
  if [ $check_size != 0 ]; then
    rm /scratch/eelk/data/gfsanl_4*
  fi
  check=$(ls /scratch/eelk/data/gfsanl_4_${start_year}* | wc -l)

  if [ $check != $((8*$(($run_length+1)) )) ]; then
    echo $check, 'getting gfs 3'
    rm /scratch/eelk/data/gfsanl_4*
    for (( j=$run_day_j; j<=$run_end_day_j; j++)) do #loop through run days
      j_day=$(date -d "$((${j}-1)) days ${start_year}-01-01" +"%d")
      j_month=$(date -d "$((${j}-1)) days ${start_year}-01-01" +"%m")
      for file in /nfs/a68/eelk/FlexPart/gfs_data/gfsanl_3_${start_year}$(printf ${j_month})$(printf ${j_day})*;  do
        cp "$file" "/scratch/eelk/data/"
      done
    done
    check_size=$(find /scratch/eelk/data/gfsanl_3* -size -20M| wc -l )
    if [ $check_size > 0 ]; then
      rm /scratch/eelk/data/gfsanl_3*
    fi
    check= $(ls /scratch/eelk/data/gfsanl_3_${start_year}* | wc -l)
  fi

  if [ $check != $((8*$(($run_length+1)) )) ]; then
    echo $check, 'getting fnl'
    rm /scratch/eelk/data/gfsanl_3*
    for (( j=$run_day_j; j<=$run_end_day_j; j++)) do #loop through run days
      j_day=$(date -d "$((${j}-1)) days ${start_year}-01-01" +"%d")
      j_month=$(date -d "$((${j}-1)) days ${start_year}-01-01" +"%m")
      for file in /nfs/a68/eelk/FlexPart/gfs_data/fnl_${start_year}$(printf ${j_month})$(printf ${j_day})*;  do
        cp "$file" "/scratch/eelk/data/"
      done
    done
  fi

  cd ../data/
  ./make_available
  cd ../fwd_gfs_test/


  #remove any previous releases file and make a new file for fires on this day
  rm /scratch/eelk/fwd_gfs_test/options/RELEASES*
  cp "/nfs/a68/eelk/FlexPart/releases_files/releases_${start_year}$(printf ${run_month})$(printf ${run_day})_maxpartsfrac_5mHeight.txt" "/scratch/eelk/fwd_gfs_test/options/RELEASES"

  #update lines in COMMAND file to have start date of this day and end date of this day+run length
  sed -i "9s/.*/ IBDATE=         $start_year$(printf ${run_month})$(printf ${run_day}), ! Start date of the simulation   ; YYYYMMDD: YYYY=year, MM=month, DD=day /" /scratch/eelk/fwd_gfs_test/options/COMMAND
  sed -i "11s/.*/ IEDATE=         ${start_year}$(printf ${run_end_month})$(printf ${run_end_day}),! End date of the simulation     ; same format as IBDATE  /" /scratch/eelk/fwd_gfs_test/options/COMMAND
  sed -i '25s/.*/ IPIN=                  0, ! Warm start from particle dump (needs previous partposit_end file); [0]no 1]yes  /' /scratch/eelk/fwd_gfs_test/options/COMMAND

  #if its not the first day then want to use a warm start
  #remove partposit_end file and replace it with partposit_file from run before
  #update line in COMMAND file to have a warm start
  if [ $run_day_j != $start_day_j ]; then
    echo 'warm start'
    rm ${out_dir}/partposit_end
    cp "${out_dir}/partposit_${start_year}$(printf ${run_month})$(printf ${run_day})000000" "${out_dir}/partposit_end"
    sed -i '25s/.*/ IPIN=                  1, ! Warm start from particle dump (needs previous partposit_end file); [0]no 1]yes  /' /scratch/eelk/fwd_gfs_test/options/COMMAND
    rm ${out_dir}/partposit_${start_year}*
  fi

  #run flexpart for this day
  FLEXPART

  #put partposit files and header in folder
  mkdir "${out_dir}/${start_year}$(printf ${run_month})$(printf ${run_day})"
  for file in ${out_dir}/partposit_*000000; do
    cp $file "${out_dir}/${start_year}$(printf ${run_month})$(printf ${run_day})/"
  done
  cp "${out_dir}/header" "${out_dir}/${start_year}$(printf ${run_month})$(printf ${run_day})/"

  #mv "/scratch/eelk/fwd_gfs_test/output/grid_conc_${start_year}$(printf ${run_month})$(printf ${run_day})000000.nc" "${out_dir}/"

  old_run_day=$run_day

done
