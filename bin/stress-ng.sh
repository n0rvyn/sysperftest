#!/bin/bash
#
# set -e
# for starting stress-ng
# define the prefix of the log name
HOME_OF_ALL='/tmp/sysperftest'
cd ${HOME_OF_ALL} || exit -1
log_prefix="${HOME_OF_ALL}/sysperftest_$(date +%y%m%d_%H%M)_$(hostname)_stress-ng"
pkg_prefix="stress-ng-0"

echo "stress-ng pid: " $$

# unpack the package
# opts='make clean && make && make install'
find . -type f -name "${pkg_prefix}*.gz" -exec tar -xvf {} \;
_HOME=$(find . -maxdepth 2 -type d -name "${pkg_prefix}*" -print | head -1)
cd $_HOME
# todo must test ARM-based machine
if [[ ! `which stress-ng` ]]; then
  make clean && make && make install
fi

no_cpus=$(lscpu | grep "^CPU...:" | awk -F':' '{print $2}' | sed 's/  //g')
total_mem_mib=$(free -m | grep "Mem" | awk '{print $2}')
total_swap_mib=$(free -m | grep "Swap" | awk '{print $2}')
no_disks=$(lsblk | grep -vE "├|─|NAME" | wc -l)


# Run 4 CPU, 2 virtual memory, 1 disk and 8 fork stressors for 2 minutes and print measurements:
stress-ng --cpu 1 --vm 1 --vm-bytes 5% --vm-method all --io 1 --hdd 1 --fork 1 --timeout 6s --metrics --log-file ${log_prefix}.log

# Run matrix stressor on all online CPUs for 60 seconds and measure temperature:
# stress-ng --matrix -1 --tz -t 60 &> ${resultsDir} &

echo "END OF STRESS-NG"
exit 0

