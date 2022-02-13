#!/bin/bash
#

# set -e
# for starting iozone3
# define the prefix of the log name
HOME_OF_ALL='/tmp/sysperftest'
cd ${HOME_OF_ALL} || exit 127
log_prefix="${HOME_OF_ALL}/sysperftest_$(date +%y%m%d_%H%M)_$(hostname)_iozone3"
pkg_prefix="iozone3"

# opts='cd src/current/ && make linux-AMD64'
echo "iozone3 pid: " $$

# unpack the package
find ${HOME_OF_ALL} -type f -name "${pkg_prefix}*.tgz" -exec tar -xvf {} \;
_HOME=$(find ${HOME_OF_ALL} -maxdepth 2 -type d -name "${pkg_prefix}*" -print | head -1)
cd ${_HOME}/src/current || exit 127

# ARM-based machine
[ -f 'iozone' ] || make linux-AMD64

no_cpus=$(lscpu | grep "^CPU...:" | awk -F':' '{print $2}' | sed 's/  //g')
total_mem_mib=$(free -m | grep "Mem" | awk '{print $2}')
total_swap_mib=$(free -m | grep "Swap" | awk '{print $2}')
no_disks=$(lsblk | grep -vE "├|─|NAME" | wc -l)

doubleMemMib=$((${total_mem_mib}*2))
halfMemMib=$((${total_mem_mib}/2))

./iozone -a -s ${total_mem_mib} -i 0 -i 1 -i 2 -f /tmp/iozone3_data | tee -a ${log_prefix}_full_mem.log
./iozone -a -s ${doubleMemMib} -i 0 -i 1 -i 2 -f /tmp/iozone3_data | tee -a ${log_prefix}_double_mem.log
./iozone -a -s ${halfMemMib} -i 0 -i 1 -i 2 -f /tmp/iozone3_data | tee -a ${log_prefix}_half_mem.log

# ./iozone -a -s ${total_mem_mib} -i 0 -i 1 -i 2 -f /tmp/iozone3_data -Rb ${log_prefix}_full_mem.xls
# ./iozone -a -s ${doubleMemMib} -i 0 -i 1 -i 2 -f /tmp/iozone3_data -Rb ${log_prefix}_double_mem.xls
# ./iozone -a -s ${halfMemMib} -i 0 -i 1 -i 2 -f /tmp/iozone3_data -Rb ${log_prefix}_half_mem.xls

echo "END OF IOZONE3"
exit 0