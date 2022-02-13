#!/bin/bash
#
# set -e
# for starting iozone3
# define the prefix of the log name
HOME_OF_ALL='/tmp/sysperftest'
cd ${HOME_OF_ALL} || exit -1
log_prefix="${HOME_OF_ALL}/sysperftest_$(date +%y%m%d_%H%M)_$(hostname)_nmon"
pkg_prefix="nmon"

# opts='cd src/current/ && make linux-AMD64'
echo "nmon pid: " $$

# unpack the package
# find ${HOME_OF_ALL} -type f -name "${pkg_prefix}*.tgz" -exec tar -xvf {} \;
_HOME=$(find ${HOME_OF_ALL} -maxdepth 2 -type d -name "${pkg_prefix}*" -print | head -1)
cd ${_HOME}

no_cpus=$(lscpu | grep "^CPU...:" | awk -F':' '{print $2}' | sed 's/  //g')
total_mem_mib=$(free -m | grep "Mem" | awk '{print $2}')
total_swap_mib=$(free -m | grep "Swap" | awk '{print $2}')
no_disks=$(lsblk | grep -vE "├|─|NAME" | wc -l)

os_mark=$(echo $(cat /etc/os-release | grep -Ew "ID=|VERSION_ID=" | awk -F'"' '{print $2}') | sed 's/ //g' | awk -F'.' '{print $1}')
cp nmon_$(uname -p)_${os_mark} /usr/local/bin/nmon
chmod +x /usr/local/bin/nmon
mkdir -p /tmp/nmon

nmon_cron='0 * * * *  /usr/local/bin/nmon -s5 -c720 -ft -m /tmp/nmon/'
# add nmon crontab

echo "END OF NMON SETUP"
exit 0