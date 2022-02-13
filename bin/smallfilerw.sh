#!/bin/bash
#
# Huge number of small files write & read performance test

HOME_OF_ALL='/tmp/sysperftest'
cd ${HOME_OF_ALL} || exit 1
log_prefix="${HOME_OF_ALL}/sysperftest_$(date +%y%m%d_%H%M)_$(hostname)_smallfilerw"
pkg_prefix="smallfilerw"


# print PID of script
echo "smallfilerw pid: " $$

# unpack the package
find ${HOME_OF_ALL} -type f -name "${pkg_prefix}*.tar" -exec tar -xvf {} \;
_HOME=$(find ${HOME_OF_ALL} -maxdepth 2 -type d -name "${pkg_prefix}*" -print | head -1)
cd ${_HOME}/src/current || exit 127

dir_depth=5
file_num_per_dir=5
file_size=1K

#

