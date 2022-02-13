#!/bin/bash
#
# set -e
# for starting lmbench
# define the prefix of the log name
HOME_OF_ALL='/tmp/sysperftest'
cd ${HOME_OF_ALL} || exit 127
log_prefix="${HOME_OF_ALL}/sysperftest_$(date +%y%m%d_%H%M)_$(hostname)_lmbench"
pkg_prefix="lmbench-3"

echo "lmbench pid: " $$

# unpack the package
# opts='chmod +x scripts/config-run && make || make LDFLAGS=-ltirpc'
find ${HOME_OF_ALL} -type f -name "${pkg_prefix}*.tgz" -exec tar -xvf {} \;
_HOME=$(find ${HOME_OF_ALL} -maxdepth 2 -type d -name "${pkg_prefix}*" -print | head -1)
# shellcheck disable=SC2164
cd ${_HOME} || exit 127
# test ARM-based machine
chmod +x ${_HOME}/scripts/config-run && make || make LDFLAGS=-ltirpc

no_cpus=$(lscpu | grep "^CPU...:" | awk -F':' '{print $2}' | sed 's/  //g')
total_mem_mib=$(free -m | grep "Mem" | awk '{print $2}')
total_swap_mib=$(free -m | grep "Swap" | awk '{print $2}')
no_disks=$(lsblk | grep -vE "├|─|NAME" | wc -l)
first_disk=$(lsblk | grep -vE "├|─|NAME" | head -1)

# The file need to be modified to make the process automatically.
# otherwise, options should be input though system stdin
FILE=$HOME/scripts/config-run

#
# start SINGLE copy lmbench test
#
# define how many multiple copies of lmbench in parallel
# 1 or num_of_cpus
SYNC_MAX=1

# Options to control job placement
LMBENCH_SCHED='1'

# 3. Memory used by lmbench
# recommend cache[s]*4, <=80%*memory, more bigger, more accurate.
# 1/10 is used for test on VM, MODIFY on product system.
# shellcheck disable=SC2004
TMP=$((${total_mem_mib} * 1 / 10))

# lmbench measures a wide variety of system performance
subset='all'

# Answering yes means that we measure memory latency with a 127 byte stride.
fast='yes'

# If you want to skip the file system latency tests, answer "yes" below.
slow='yes'

# Define which disk need to be test
disks=${first_disk}

REMOTE=''

# modify args in file 'lmbench*/script/config-run
sed -i 's/read SYNC_MAX/SYNC_MAX='"$SYNC_MAX"'/' ${FILE}
sed -i 's/read LMBENCH_SCHED/LMBENCH_SCHED='$LMBENCH_SCHED'/' ${FILE}
sed -i 's/read TMP/TMP='$TMP'/' ${FILE}
sed -i 's/read subset/subset='$subset'/' ${FILE}
sed -i 's/read fast/fast='$fast'/' ${FILE}
sed -i 's/read slow/slow='$slow'/' ${FILE}
sed -i 's/read disks/disks='"$disks"'/' ${FILE}
sed -i 's/read REMOTE/REMOTE='"$REMOTE"'/' ${FILE}

# for test
echo "dummy run lmbench" | tee  -a ${log_prefix}_single.log && exit 0
# for test

# uncommitted after finished test.
# cd "$HOME" && nohup make results see &
# make results see on rhel7 based system, if error occurred, add additional options
make results see | tee -a ${log_prefix}_single.log || make results LDFLAGS=-ltirpc see | tee -a ${log_prefix}_single.log


# committed line to start multiple copies lmbench test
exit 0
#
# start MULTIPLE copies lmbench test
#
# define how many multiple copies of lmbench in parallel
# 1 or num_of_cpus
SYNC_MAX=${no_cpus}

# Options to control job placement
LMBENCH_SCHED='1'

# 3. Memory used by lmbench
# recommend cache[s]*4, <=80%*memory, more bigger, more accurate.
# 1/10 is used for test on VM, MODIFY on product system.
# shellcheck disable=SC2004
TMP=$(($total_mem_mib * 8 / 10))

# lmbench measures a wide variety of system performance
subset='all'

# Answering yes means that we measure memory latency with a 127 byte stride.
fast='no'

# If you want to skip the file system latency tests, answer "yes" below.
slow='no'

# Define which disk need to be test
disks=${first_disk}

REMOTE=''

# modify args in file 'lmbench*/script/config-run
sed -i 's/read SYNC_MAX/SYNC_MAX='"$SYNC_MAX"'/' ${FILE}
sed -i 's/read LMBENCH_SCHED/LMBENCH_SCHED='$LMBENCH_SCHED'/' ${FILE}
sed -i 's/read TMP/TMP='$TMP'/' ${FILE}
sed -i 's/read subset/subset='$subset'/' ${FILE}
sed -i 's/read fast/fast='$fast'/' ${FILE}
sed -i 's/read slow/slow='$slow'/' ${FILE}
sed -i 's/read disks/disks='"$disks"'/' ${FILE}
sed -i 's/read REMOTE/REMOTE='"$REMOTE"'/' ${FILE}

# uncommitted after finished test.
# cd "$HOME" && nohup make results see &
# make results see on rhel7 based system, if error occurred, add additional options
make results see | tee -a ${log_prefix}_single.log || make results LDFLAGS=-ltirpc see | tee -a ${log_prefix}_multiple.log

