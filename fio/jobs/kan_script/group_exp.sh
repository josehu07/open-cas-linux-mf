
fio_name="./fio_jobs/randread_optane_ssd_flash_80_hit.fio"

for QD in 1 3 5 6
do
	 bash ./run_with_pure.sh wa $fio_name $QD 
done
