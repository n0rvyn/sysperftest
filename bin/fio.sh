#!/bin/bash
#
# for starting fio test
# fio has been installed via Yum

HOME_OF_ALL='/tmp/sysperftest'
cd ${HOME_OF_ALL} || exit 1
log_prefix="${HOME_OF_ALL}/sysperftest_$(date +%y%m%d_%H%M)_$(hostname)_fio"
pkg_name_prefix="fio*"

# print PID of script
echo "fio pid: " $$

no_cpus=$(lscpu | grep "^CPU...:" | awk -F':' '{print $2}' | sed 's/  //g')
total_mem_mib=$(free -m | grep "Mem" | awk '{print $2}')
total_swap_mib=$(free -m | grep "Swap" | awk '{print $2}')
no_disks=$(lsblk | grep -vE "├|─|NAME" | wc -l)

fio --filename=/tmp/fio_test --size=16M --direct=1 --rw=write --bs=4M --ioengine=libaio --iodepth=1 \
  --runtime=3 --numjobs=1 --time_based --group_reporting --name=throughput-test-job --eta-newline=1 \
  --output=${log_prefix}_write.log

fio --filename=/tmp/fio_test --size=16M --direct=1 --rw=read --bs=4M --ioengine=libaio --iodepth=1 \
  --runtime=3 --numjobs=1 --time_based --group_reporting --name=throughput-test-job --eta-newline=1 --readonly \
  --output=${log_prefix}_read.log

echo "fio pid done."

exit 0
