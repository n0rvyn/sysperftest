#!/bin/bash
#
# set -e
# for starting ltp
# define the prefix of the log name
HOME_OF_ALL='/tmp/sysperftest'
cd ${HOME_OF_ALL} || exit -1
log_prefix="${HOME_OF_ALL}/sysperftest_$(date +%y%m%d_%H%M)_$(hostname)_ltp"
pkg_prefix="ltp-full"

echo "ltp pid: " $$

# unpack the package
# opts='chmod +x scripts/config-run && make || make LDFLAGS=-ltirpc'
find ${HOME_OF_ALL} -type f -name "${pkg_prefix}*.bz2" -exec tar -xvf {} \;
_HOME=$(find ${HOME_OF_ALL} -maxdepth 2 -type d -name "${pkg_prefix}*" -print | head -1)
cd $_HOME
# todo must test ARM-based machine
if [[ ! -d /opt/ltp/testscripts ]]; then
  make autotools && ./configure && make && make install
  # make autotools && ./configure && make all && make install
fi

no_cpus=$(lscpu | grep "^CPU...:" | awk -F':' '{print $2}' | sed 's/  //g')
total_mem_mib=$(free -m | grep "Mem" | awk '{print $2}')
total_swap_mib=$(free -m | grep "Swap" | awk '{print $2}')
no_disks=$(lsblk | grep -vE "├|─|NAME" | wc -l)

# run system bench with UnixBench tool
# /opt/ltp/runltp -c ${no_cpus} -i ${no_cpus} \
/opt/ltp/runltp \
  -m 2,4,10240,1 -D 2,10,10240,1 -p -q \
  -l ${log_prefix}.log \
  -o ${log_prefix}_result.log \
  -C ${log_prefix}_failed.log \
  -d /tmp \
  -t 5s
# -c NUM_PROCS    Run LTP under additional background CPU load
# -i NUM_PROCS    Run LTP under additional background Load on IO Bus
# -t 60s = 60 seconds; -t 45m = 45 minutes; -t 24h = 24 hours; -t 2d  = 2 days

# after 48H, system resources release normally, test pass.
echo "END OF LTP."
exit 0