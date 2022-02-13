#!/bin/bash
#
# set -e
# for starting UnixBench
# define the prefix of the log name
HOME_OF_ALL='/tmp/sysperftest'
cd ${HOME_OF_ALL} || exit -1
log_prefix="${HOME_OF_ALL}/sysperftest_$(date +%y%m%d_%H%M)_$(hostname)_unixbench"
pkg_prefix="UnixBench_5.1.3"

# opts='cd src/current/ && make linux-AMD64'
echo "unixbench pid: " $$

# unpack the package
find ${HOME_OF_ALL} -type f -name "${pkg_prefix}*.zip" -exec unzip {} \;
_HOME=$(find ${HOME_OF_ALL} -maxdepth 2 -type d -name "${pkg_prefix}*" -print | head -1)
cd $_HOME
[ -f 'Run' ] || make
# todo must test ARM-based machine

no_cpus=$(lscpu | grep "^CPU...:" | awk -F':' '{print $2}' | sed 's/  //g')
total_mem_mib=$(free -m | grep "Mem" | awk '{print $2}')
total_swap_mib=$(free -m | grep "Swap" | awk '{print $2}')
no_disks=$(lsblk | grep -vE "├|─|NAME" | wc -l)
# end of test

echo 'dummy test unixbench.' | tee -a ${log_prefix}.log && exit 0

# run system bench with UnixBench tool
./Run -q -c 1 -c ${no_cpus} | tee -a ${log_prefix}.log

echo "END OF UNIXBENCH"
exit 0