#!/bin/bash
#
# set -e
# for starting stress-ng
# define the prefix of the log name
HOME_OF_ALL='/tmp/sysperftest'
cd ${HOME_OF_ALL} || exit -1
log_prefix="${HOME_OF_ALL}/sysperftest_$(date +%y%m%d_%H%M)_$(hostname)_stream"
pkg_prefix="STREAM-master"

echo "stream pid: " $$

# unpack the package
# 'make clean && make SET=TRUE N=90000000 MTIMES=100 && sync'
find . -type f -name "${pkg_prefix}*.zip" -exec unzip {} \;
_HOME=$(find . -maxdepth 2 -type d -name "${pkg_prefix}*" -print | head -1)
cd $_HOME
# todo must test ARM-based machine
if [[ ! -f 'stream_c.exe' ]]; then
  make clean && make SET=TRUE N=90000000 MTIMES=100 && sync
fi

no_cpus=$(lscpu | grep "^CPU...:" | awk -F':' '{print $2}' | sed 's/  //g')
total_mem_mib=$(free -m | grep "Mem" | awk '{print $2}')
total_swap_mib=$(free -m | grep "Swap" | awk '{print $2}')
no_disks=$(lsblk | grep -vE "├|─|NAME" | wc -l)

./stream_c.exe | tee -a ${log_prefix}.log
exit 0

